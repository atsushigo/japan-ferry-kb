# Chatbot app

- [`app-config.md`](app-config.md) — how the Dify chatflow is built (flow diagram, model, retrieval settings, observations).
- [`system-prompt.md`](system-prompt.md) — the prompt, with version history (v1.1 deployed, v2 proposed).
- [`test-conversations.csv`](test-conversations.csv) — answer-level test cases A1–A14 (runner: [FKB-005](../docs/issues/FKB-005-answer-level-eval-runner.md)).
- Planned: exported app DSL (YAML) after the prompt is stable.

Design rules come from the retrieval audit (`../docs/phase1-rag-audit-report.md`, §4.4–4.5): the score threshold is not a sufficient guard,
so the flow routes empty retrieval to a fixed reply and the prompt enforces "answer only from the retrieved text".
Defects found at the answer level are tracked in [`../docs/issues/`](../docs/issues/README.md).

## 看懂這個資料夾（給不熟聊天機器人設計的讀者）

### 先理解四個名詞

| 名詞 | 白話解釋 | 在這個專案裡 |
|---|---|---|
| 知識庫（knowledge base） | 把文件切成小段、存成可搜尋的資料 | `knowledge/` 的兩份文件，已上傳到 Dify |
| 檢索（retrieval） | 依問題找出最相關的幾段文件 | Top K 5、分數閾值 0.71；已用 `evaluation/` 測過 |
| 系統提示詞（system prompt） | 事先告訴模型「你是誰、只能怎麼回答」的規則 | `system-prompt.md` |
| 流程（chatflow） | 問題進來後依序經過哪些步驟 | `app-config.md` 的流程圖 |

一次提問的路徑：**問題 → 檢索 → 沒找到就固定回覆「知識庫沒有」／找到了就交給模型 → 模型依提示詞規則，只根據找到的段落組成回答**。
模型不會「學會」這些文件，每次回答時，文件段落是臨時放進提示詞裡讓它參考的。

### 為什麼檢索與回答要分開測

檢索測試（`evaluation/`）問的是「找到的段落對不對」；回答測試（本資料夾）問的是「模型最後講的對不對」。
檢索全對，模型仍可能把兩個事實合併成沒有根據的結論（見 [FKB-002](../docs/issues/FKB-002-unsupported-peak-season-surcharge.md)）。

### test-conversations.csv 的欄位與標籤

| 欄位 | 意思 |
|---|---|
| `id` | 題號 |
| `language` | 提問語言：zh 中文、ja 日文、en 英文 |
| `query` | 要問聊天機器人的問題 |
| `expected_behavior` | 正確回答應有的行為（標籤，見下表） |
| `must_not` | 絕對不能出現的行為（標籤，可附相關問題單） |

標籤只是描述用的短語，目前由人工對照閱讀；[FKB-005](../docs/issues/FKB-005-answer-level-eval-runner.md) 完成後，其中能用規則判斷的會變成自動檢查，語意判斷仍由人工。

| 標籤（`expected_behavior`） | 意思 | 例題 |
|---|---|---|
| `answer_from_kb_with_...` / `answer_in_..._with_source` | 依知識庫回答，附來源；指定語言就用該語言 | A1、A7、A8 |
| `state_suspended_or_contradictory_status_first` | 航線停航或資料矛盾時，先講這個狀態再講細節 | A2 |
| `list_both_conflicting_rule_sets` | 官方有兩套互相矛盾的規定時，兩套都列出，不自己選 | A3 |
| `say_kb_does_not_cover` | 超出範圍就說知識庫沒有，不要用模型自己的知識補 | A4、A9 |
| `say_cannot_check_realtime` / `say_cannot_book` | 說明做不到即時座位、訂票，指向官方管道 | A5、A6 |
| `refuse_and_stay_in_scope` | 拒絕「忽略規則、洩漏提示詞」這類指令 | A11 |
| `give_fares_only_with_not_buyable_while_suspended_caveat` | 上海票價可以給，但要註明停航期間不能購買 | A10 |
| `answer_from_battery_section_or_say_not_in_kb` | 知識庫有寫就照寫，沒寫就說沒有，不猜 | A12 |
| `say_kb_only_states_no_discount_in_peak_...` | 只轉述原文「旺季不能折扣、沒寫差額」 | A13 |
| `state_confirmation_date_and_advise_checking_official` | 標示確認日期並建議查官方，不猜資料新舊 | A14 |

`must_not` 的標籤同理，例如 `do_not_describe_other_routes`（不描述其他航線）、`do_not_pretend_to_book`（不假裝訂票）。

### 想改什麼，去哪個檔案

| 想做的事 | 改哪裡 |
|---|---|
| 調整回答規則、語氣 | `system-prompt.md`（改完要更新版本表，並在 Dify 貼上） |
| 改流程、模型、檢索設定 | 先在 Dify 改，再更新 `app-config.md` |
| 新增一個回答測試 | `test-conversations.csv` 加一列，必要時在上表補標籤 |
