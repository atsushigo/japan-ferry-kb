# FKB-001：Gemini 免費層每日額度用完，錯誤顯示為「high demand」

| Field | Value |
|---|---|
| Type / Priority / Status | Incident / High / Mitigated |
| Component | infra（模型供應商）、chatbot-flow |
| Found in | Dify Cloud 聊天流 v0；LLM = Gemini 3.8 Flash（免費層）；「失敗時重試 3 次」已開啟 |
| Reported | 2026-11-21 21:43 JST（根因確認 22:08 JST） |
| Related | FKB-006 |

## Description
聊天流的 LLM 節點在預覽中持續失敗。錯誤訊息一開始是：

> `[gemini] This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.`

我們把它當成暫時性過載，開啟「失敗時重試 3 次」並反覆重試，結果相同；約 25 分鐘後改看單步測試，才得到真正的錯誤：

> `Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3.8-flash ... Please retry in 18h52m`

## Steps to reproduce
1. 聊天流 LLM 節點使用 Gemini 3.8 Flash（Gemini 免費 API 金鑰）。
2. 在預覽與單步測試中累計超過 20 次 LLM 請求（含失敗與自動重試）。
3. 之後所有請求被拒絕，直到額度重置。

## Expected / Actual
- Expected：額度用完時，錯誤訊息應清楚指出是額度（quota），而不是「需求過高」。
- Actual：同一情境先後出現兩種訊息，第一種誤導了判斷；兩者的 HTTP 層級原因不同，Dify 前端沒有說明。

## Root cause（Confirmed）
- 免費層對 `gemini-3.8-flash` 的限制為每天 20 次請求、每分鐘 5 次（AI Studio「速率限制」頁，2026-11-21 截圖）。
- 「失敗時重試 3 次」讓每個失敗的提問最多消耗 4 次請求，加速耗盡額度。
- 額度以模型為單位分開計算，每天太平洋時間午夜重置（約 17:00 JST）。Embedding（gemini-embedding-2）有獨立額度，所以知識檢索仍正常。

## Resolution / Workaround
- 開發階段改用 Gemini 3.5 Flash-Lite（免費層每天 500 次、每分鐘 15 次），並將重試降低或關閉。
- 評測腳本需限速（見 FKB-005）：免費層每分鐘 5～15 次。
- 長期方案見 FKB-006（是否開啟計費）。

## Verification
- 換成 3.5 Flash-Lite 後，完整流程預覽成功（2026-11-21 22:30 JST），知識檢索 → 條件分支 → LLM → 回覆皆通過。

## Lessons learned
1. 錯誤訊息的字面意思不一定是真正原因。「暫時過載」要在單步測試或供應商後台確認額度，再決定重試或換模型。
2. 額度緊的時候，自動重試是反效果；重試前先確認錯誤是否真的暫時性。
3. 每次改動模型，都要在 run 的設定檔記錄實際使用的模型名稱（Dify 的 `model_name` 欄位可驗證，這次就用它發現選到的是 3.1 而不是 3.5 Flash-Lite）。
4. 官方文件沒有公布各模型免費層的每日上限，只能看自己帳號的額度頁，且可能隨時調整。
