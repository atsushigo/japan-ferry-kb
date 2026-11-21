# FKB-013：輸出後驗證——金額不在檢索結果裡就不顯示

| Field | Value |
|---|---|
| Type / Priority / Status | Story / High / In Progress（程式與離線驗證完成；Dify 接線待使用者操作） |
| Component | chatbot-flow、evaluation |
| Found in | FKB-007 的後續處理（層級 3，見 `docs/hallucination-mitigation-options.md`） |
| Reported | 2026-11-22 JST |
| Related | FKB-007、`evaluation/score_chat.py` |

## Description
提示詞（層級 1）只能降低錯價機率，不能保證為零（FKB-007：約 4/33 次出錯，v3 後 20/20 正確但樣本小）。需要一個不靠模型的把關：LLM 回答後，用程式檢查每個金額是否出現在檢索結果，不符就不顯示。

## Implementation
- `chatbot/guardrail/amount_check.py`：Dify「程式碼」節點的 Python，輸出 `verdict`（pass／block）與 `bad`。
- `chatbot/guardrail/README.md`：Dify 接線步驟、固定訊息（三語）、單步測試輸入。
- `evaluation/test_guardrail.py`：離線重播與注入測試。
- `evaluation/score_chat.py`：被擋的回答會被標成 `guardrail_blocked`，在測試結果中看得到。

## Verification
離線（2026-11-22）：
- 重播 230 則回答（93 則含金額）：會擋 3 則，正好是已知的 3 個錯價；其餘 90 則 0 誤擋。
- 注入 524 個錯誤金額變體：524/524 被擋。
線上：**未做**。接好後用 API 跑 A1 ×20、A3 ×10、A10 ×10、A25 ×3，確認沒有誤擋。

## Limits
- 金額是真的但配錯艙等（例如陽台套房寫成 ₩700,000）不會被擋；只檢查貨幣符號或貨幣單位旁的數字。
- 被擋時使用者要自己再問一次；不處理錯價的原因。
- 串流行為未驗證：結構是 LLM → 程式碼 → 回覆，推測使用者不會看到未驗證的逐字輸出，需在預覽觀察。

## Lessons learned
- 同一套規則先在離線測試跑通（重播＋注入），再搬進線上流程，可以在不動線上設定的情況下先知道誤擋率。
