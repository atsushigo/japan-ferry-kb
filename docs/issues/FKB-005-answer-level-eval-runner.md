# FKB-005：建立回答層自動評測腳本（run_chat.py）

| Field | Value |
|---|---|
| Type / Priority / Status | Story / High / Open |
| Component | evaluation |
| Related | FKB-002、FKB-003、FKB-006 |

## Description
目前只有檢索層（召回）自動評測（`run_recall.py`、`score_run.py`）。回答層（模型最後說了什麼）只能在 Dify 預覽手動測，無法重現、無法比較不同模型或提示詞版本。FKB-002、FKB-003 都是在回答層才發現的。

## Scope
1. `evaluation/run_chat.py`：讀 `chatbot/test-conversations.csv`，呼叫 Dify 應用 API（`/chat-messages`，blocking 模式），每題一個獨立對話，存回答、引用段落、token 與延遲。
2. 輸出放進與召回相同結構的不可變 run 資料夾（`config.json` 記錄模型名稱、提示詞版本、Dify 應用 DSL 雜湊）。
3. 限速：預設每題間隔 5 秒（免費層每分鐘上限 5～15 次，見 FKB-001）。
4. 規則式自動檢查：`must_not` 關鍵字（例如「加價」「超過 3 個月」）、是否含來源網址與確認日期、庫外題是否為固定拒答文字。
5. 規則檢查不到的（語意是否忠於來源），先輸出給人工逐題判讀的欄位，不宣稱自動化。

## Acceptance criteria
- 一個指令跑完全部測試題，產生 `results.csv`、`config.json`、`summary.md`。
- 同一批題目可用不同模型各跑一輪並排比較。
- 金鑰只從 `.env` 讀（`DIFY_APP_API_KEY`），不寫入任何輸出檔。

## Dependencies
- 應用已發布，並由使用者在 `.env` 設定應用金鑰（不同於知識庫金鑰）。
