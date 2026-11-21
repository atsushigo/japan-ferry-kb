# Issue log（問題與改善紀錄）

用 Jira 的欄位格式記錄專案中發現的問題與改善項目，讓每個問題都有：現象、重現步驟、根因、修正、驗證與教訓。
這是 repo 內的文字紀錄，不是 Jira 系統；編號 `FKB-nnn`（Ferry Knowledge Base）依發現順序遞增，不重用。

## 索引

| Key | Type | Priority | Status | Summary |
|---|---|---|---|---|
| [FKB-001](FKB-001-gemini-free-tier-quota.md) | Incident | High | Mitigated | Gemini 免費層每日額度用完，錯誤訊息顯示為「high demand」，且自動重試加速耗盡額度 |
| [FKB-002](FKB-002-unsupported-peak-season-surcharge.md) | Bug | High | Done | 回答把「旺季不可折扣」延伸成知識庫沒有的「旺季加價」 |
| [FKB-003](FKB-003-stale-date-rule-not-answerable.md) | Bug | Medium | Done | 「超過 3 個月提醒過期」規則無法執行，模型自相矛盾 |
| [FKB-004](FKB-004-unused-files-variable.md) | Task | Low | Done | LLM 節點的使用者訊息帶了用不到的 `files` 變數 |
| [FKB-005](FKB-005-answer-level-eval-runner.md) | Story | High | In Progress | 回答層自動評測腳本（run_chat.py、score_chat.py）；第一輪 chat-001 已跑 |
| [FKB-006](FKB-006-llm-model-comparison-and-billing.md) | Story | Medium | Open | 比較 Gemini 3.5 Flash-Lite 與 3.8 Flash，並決定是否開啟計費 |
| [FKB-007](FKB-007-nondeterministic-price-hallucination.md) | Bug | High | Mitigated | 回答偶爾輸出知識庫沒有的價格數字；4 次都在「陽台套房」那一列（預覽 ₩2/人、API ₩2,500,000 ×2、₩2,000；提示詞 v3 後 A1 ×20 無錯價） |
| [FKB-008](FKB-008-glued-two-generations.md) | Bug | High | Mitigated | 回答中出現兩段輸出拼接（A1、A3 共 26 次中 4 次；日誌確認為 Gemini「high demand」串流中斷後節點重試，殘缺前半段被保留；重試關閉並發布後 chat-003 20 次無拼接） |
| [FKB-009](FKB-009-answer-language-mismatch.md) | Bug | Medium | Open | 日文、英文提問得到中文內容（A7 3/3、A8 2/3；chat-006 日英 8 題 15/15 次不一致，幾乎全面） |
| [FKB-010](FKB-010-suspension-not-stated-first.md) | Bug | High | Mitigated | 問上海票價時，客運暫停狀態被放最後且沒說明不能購買（3 次中 2 次；v4 後 A10 ×10 全部先說明） |
| [FKB-011](FKB-011-eval-harness-limitations.md) | Task | Medium | Open | 回答層測試的限制：A14 單輪無效、A11 沒測到提示詞、拒答帶假來源、評分誤判 |
| [FKB-012](FKB-012-overview-questions-miss-threshold.md) | Story | Medium | In Progress | 概括性問題（「大阪からどこまでいけますか」）被閾值擋掉；需要開場問題按鈕與總覽段落 |

## 欄位與規範

| 欄位 | 說明 |
|---|---|
| Type | Bug（行為與預期不符）／Incident（服務中斷或異常，含處置）／Story（新功能或改善）／Task（設定或雜項） |
| Priority | High（影響「不編造」或「可用性」這兩個核心要求）／Medium／Low |
| Status | Open → In Progress → Mitigated（已有暫時處置）→ Done（已修正且驗證過）／Won't fix |
| Component | knowledge-base／retrieval／chatbot-prompt／chatbot-flow／evaluation／infra |
| Found in | 發現時的版本：知識文件版本、提示詞版本、模型、Dify 流程 |
| 日期 | 一律日本時間（JST） |

撰寫原則：
1. **只寫有觀察到的事實。** 根因未驗證時標 `Suspected`，不要寫成確定。
2. **Status 要誠實。** 修法只是「提案」、尚未重跑測試，就維持 Open，不寫 Done。
3. **記錄驗證方式。** 每張單要寫清楚用哪個測試題、什麼結果算通過。
4. **不放秘密。** 不寫金鑰、知識庫 ID、個人資訊。
5. 修好之後，在原檔補上 Resolution 與驗證結果，不另開新檔；Status 更新並在索引同步。

## 單檔範本

```markdown
# FKB-nnn：標題
| Field | Value |
|---|---|
| Type / Priority / Status | |
| Component | |
| Found in | |
| Reported | YYYY-MM-DD HH:MM JST |
| Related | FKB-xxx |

## Description
## Steps to reproduce
## Expected / Actual
## Root cause（Confirmed／Suspected）
## Resolution / Workaround
## Verification（測試題與通過條件）
## Lessons learned
```
