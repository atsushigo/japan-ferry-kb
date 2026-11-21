# FKB-008：回答中出現兩段輸出拼接（截斷的前半＋完整的後半）

| Field | Value |
|---|---|
| Type / Priority / Status | Bug / High / Mitigated（重試關閉並發布後 20 次無拼接；樣本小） |
| Component | chatbot-flow、model |
| Found in | chat-001（42 次請求中 3 次）；chat-002 再 1 次；Dify 日誌追蹤已確認機制 |
| Reported | 2026-11-21 JST |
| Related | FKB-007、FKB-001 |

## Description
同一則回答裡，前一段在句子中間被截斷，後面緊接一整份新的回答：

- A1 #1：「…內側房 INSIDE CABIN」後面直接接「大阪到釜山（パンスターミラクル号）的單程票價依艙等而定…」。此次前半段含錯誤金額（FKB-007）。
- A1 #3：「…稅金與燃油附加費」後面直接接「大阪到釜山（パンスターミラクル号）的單程票價依房型而定…」。
- A3 #2：「…扣 30%」後面直接接另一份完整的取消規定。
3 次都發生在長回答（表格／清單）。使用者會看到重複且不完整的內容。

## Test of the retry hypothesis（chat-002，2026-11-21 JST）
A1、A3 各重跑 10 次（20 次請求，當時認為重試已關閉）：仍出現 1 次拼接（A3 #4）。合併 chat-001（3 次）與 chat-002（1 次）：A1、A3 共 26 次請求中 4 次拼接，全是長回答；其他題的 36 次沒有發現。樣本小。
**這個實驗的前提後來被推翻**：見下一節，同一筆請求的追蹤顯示 LLM 節點有「1 重試」，所以「關閉重試後仍拼接」不能用來否定重試假說。

## Evidence from the Dify log（2026-11-22 JST，chat-002 A3 #4，23:45:31）
- 日誌狀態 **Partial Success**，訊息「有 1 個節點運行異常」；其餘 A3 請求為 Success。同樣的對照：chat-001 的 A3 #2、A1 #1／#3 在日誌也是 Partial Success，與 `glued_output` 標記一致。
- 追蹤：LLM 節點底下有 **「1 重試」**。重試的錯誤訊息：`[gemini] This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.`（Google 端暫時過載，不是額度錯誤）。
- LLM 節點總耗時 6.354 秒，最終成功那次生成的 `latency` 只有 2.075 秒、輸出 483 token、`finish_reason: STOP`；節點輸出 `text` 是**乾淨的一份**答案。多出的約 4 秒是失敗的第一次嘗試。
- 最終回答仍是拼接版：第一次嘗試在串流中途失敗，已輸出的前半段被直接回覆節點收下，重試成功的完整答案接在後面。

## Root cause
- **Confirmed（機制）**：Gemini 在串流中途回傳「high demand」錯誤 → LLM 節點重試 → 已串流出去的殘缺文字留在回答裡，後面接重試的完整答案。
- **Suspected（為什麼會過載）**：免費層優先順序低，尖峰時較容易遇到；尚未驗證。請求量遠低於 RPM／RPD 上限，錯誤文字也不是 quota 的文字，所以不像額度問題，但沒有證明。
- **Confirmed**：chat-002 時重試其實是開著的。編排頁顯示「已發布 3 小時前」（約 22:30），早於 chat-002（23:43–23:46）；關閉重試只改了草稿，沒有發布。API 用的是已發布版本。

## Resolution / Workaround（提案）
1. ~~確認重試設定與是否已發布~~：已發布（版本 #2），見 Verification。關閉重試後，過載錯誤會變成明確的失敗，而不是殘缺文字加完整答案（失敗比拼接更容易被發現與處理）。
2. 錯誤處理改成「失敗分支」，失敗時回固定訊息，避免殘缺文字。
3. 用 Gemini 3.8 Flash 或付費層對照（FKB-006），看過載頻率是否下降。
4. 評分腳本已能標出 `glued_output`；Dify 日誌的 Partial Success 可作為第二個佐證。

## Verification
**chat-003（2026-11-22 JST，LLM 節點重試關閉並已發布為版本 #2，A1、A3 各 10 次）**：20/20 請求成功，**沒有拼接**，也沒有請求失敗；單次耗時 2.6–4.5 秒，沒有 chat-002 那種 7 秒的長尾。對照：重試開啟時 A1、A3 為 4/26 次拼接，若比率不變，20 次一次都沒有的機率約 4%，支持但不能證明；樣本小，且 Google 過載本身是間歇性的。Dify 日誌的 Partial Success 狀態尚未對照 chat-003 的時段（待使用者查）。
補充（chat-006，v4，retry 關閉）：A20 #1 遇到同樣的「high demand」錯誤，這次 API 直接回 HTTP 400、沒有任何殘缺文字，符合「過載變成明確失敗」的預期。另 A19 #1 被拼接檢查標記：回答含兩段各自完整的上海航線說明（第二段較詳細），retry 已關閉，原因不明，待人工複核與觀察。
未完成的部分：`glued_output` 是啟發式，已用 Dify 日誌的 Partial Success 狀態對照：chat-001 A3 #2、chat-002 A3 #4 一致；chat-001 A1 日誌有 3 筆 Partial，我們只標了 2 筆拼接，另 1 筆未查；chat-001 A13 第一次也是 Partial 但未被標記，待查。

## Lessons learned
- 猜測要用實驗檢驗，但實驗的前提也要檢驗：我們以為重試已關閉，日誌卻顯示有重試。設定改完要確認「已發布」，並用日誌核對。
- 「Partial Success」是比文字比對更直接的訊號，之後測試要一併看日誌狀態。
- 一個錯誤訊息（high demand）可能出現在不同成因下（本專案早先的額度問題 FKB-001 也曾被顯示成類似文字），要看完整錯誤與節點層級的證據再下結論。
