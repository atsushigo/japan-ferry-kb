# FKB-006：比較 Gemini 3.5 Flash-Lite 與 3.8 Flash，並決定是否開啟計費

| Field | Value |
|---|---|
| Type / Priority / Status | Story / Medium / Open |
| Component | infra、chatbot-prompt |
| Related | FKB-001、FKB-005 |

## Description
目前為了繞過免費額度，開發用 Gemini 3.5 Flash-Lite。Flash-Lite 較小，遵守複雜提示詞（不編造、矛盾並列）的能力可能不如 3.8 Flash。需要用同一批測試題做對照，才能決定正式使用哪個模型。

## 已查到的事實（2026-11-21，官方定價頁；頁面無更新日期，使用前應再確認）
| 模型 | 付費輸入／輸出（每百萬 token，USD） | 免費層（本帳號額度頁） |
|---|---|---|
| Gemini 3.8 Flash | 0.75／3.75（2027-01-01 起 1.50／7.50） | 每天 20 次、每分鐘 5 次 |
| Gemini 3.5 Flash-Lite | 0.30／2.50 | 每天 500 次、每分鐘 15 次 |
| Gemini 3.1 Flash-Lite | 0.25／1.50 | 未確認 |
| gemini-embedding-2 | 0.20（僅輸入） | 每分鐘 100 次；每日未確認 |

Tier 1 需綁定計費帳戶，通常立即生效；每 10 分鐘花費上限 10 美元。各模型 Tier 1 的 RPM／RPD 頁面未載明。
實測成本：一次含檢索的提問約 0.0003～0.002 美元（Dify 回傳的 `total_price` 為依據）。

## Tasks
1. 用 FKB-005 的腳本，對同一批題目各跑一輪 3.5 Flash-Lite 與 3.8 Flash（額度重置後，或開計費後）。
2. 並排比較：忠實度（FKB-002 類錯誤次數）、拒答正確率、語言一致性、延遲、成本。
3. 把結果寫進報告，並決定正式模型與是否開啟計費。

## Acceptance criteria
- 兩個模型在相同提示詞版本、相同知識文件版本下各有一個完整 run。
- 報告中有對照表與結論；決策理由寫明，包含成本。
