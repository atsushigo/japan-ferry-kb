# FKB-005：建立回答層自動評測腳本（run_chat.py）

| Field | Value |
|---|---|
| Type / Priority / Status | Story / High / In Progress（腳本已寫並以合成資料自測，尚未跑真實回答） |
| Component | evaluation |
| Related | FKB-002、FKB-003、FKB-006 |

## Description
目前只有檢索層（召回）自動評測（`run_recall.py`、`score_run.py`）。回答層（模型最後說了什麼）只能在 Dify 預覽手動測，無法重現、無法比較不同模型或提示詞版本。FKB-002、FKB-003 都是在回答層才發現的。

## Scope
1. `evaluation/run_chat.py`：讀 `chatbot/test-conversations.csv`，呼叫 Dify 應用 API（`/chat-messages`，blocking 模式），每題一個獨立對話，存回答、引用段落、token 與延遲。
2. 輸出放進與召回相同結構的不可變 run 資料夾（`config.json` 記錄模型名稱、提示詞版本、Dify 應用 DSL 雜湊）。
3. 限速：預設每題間隔 5 秒（免費層每分鐘上限 5～15 次，見 FKB-001）。
4. 規則式自動檢查：`must_not` 關鍵字（例如「加價」「超過 3 個月」）、是否含來源網址與確認日期、庫外題是否為固定拒答文字。
5. **數字溯源檢查**：回答中出現的每個金額（₩、¥、RMB 數字）都必須出現在該題檢索到的段落文字中，否則標記為疑似編造（FKB-007 的 ₩2/人 就是這類錯誤，可被此規則抓到）。
6. 每題重複多次（預設 3 次），因為 Gemini 3 系列不能調溫度，回答有非確定性。
7. 規則檢查不到的（語意是否忠於來源），先輸出給人工逐題判讀的欄位，不宣稱自動化。

## Progress（2026-11-21 JST）
- `evaluation/run_chat.py`（呼叫應用 API、重複、限速、遇額度錯誤即停並保留已完成的結果）與 `evaluation/score_chat.py`（規則檢查）已完成。
- `score_chat.py` 已用合成回答自測：能抓出不在檢索段落中的金額（「₩2/人」）、A13 的「旺季加價」、A14 的「超過 3 個月」，且不誤判正確回答與拒答。
- 尚未做：用真實應用跑一輪（需 `.env` 的 `DIFY_APP_API_KEY`）；金額偵測只認 ₩／¥ 符號或貨幣單位旁的數字。

## Acceptance criteria
- 一個指令跑完全部測試題，產生 `results.csv`、`config.json`、`summary.md`。
- 同一批題目可用不同模型各跑一輪並排比較。
- 金鑰只從 `.env` 讀（`DIFY_APP_API_KEY`），不寫入任何輸出檔。

## Dependencies
- 應用已發布，並由使用者在 `.env` 設定應用金鑰（不同於知識庫金鑰）。
