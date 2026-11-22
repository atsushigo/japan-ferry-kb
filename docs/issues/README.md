# Issue log（問題與改善紀錄）

用 Jira 的欄位格式記錄專案中發現的問題與改善項目，讓每個問題都有：現象、重現步驟、根因、修正、驗證與教訓。
這是 repo 內的文字紀錄，不是 Jira 系統；編號 `FKB-nnn`（Ferry Knowledge Base）依發現順序遞增，不重用。

## 索引

| Key | Type | Priority | Status | Summary | 概要（日本語） |
|---|---|---|---|---|---|
| [FKB-001](FKB-001-gemini-free-tier-quota.md) | Incident | High | Mitigated | Gemini 免費層每日額度用完，錯誤訊息顯示為「high demand」，且自動重試加速耗盡額度 | Gemini 無料枠の日次上限を使い切ると「high demand」と表示され、自動リトライが枠の消費を早めた |
| [FKB-002](FKB-002-unsupported-peak-season-surcharge.md) | Bug | High | Done | 回答把「旺季不可折扣」延伸成知識庫沒有的「旺季加價」 | 回答が「繁忙期は割引不可」を、ナレッジベースにない「繁忙期は割増」に拡大解釈した |
| [FKB-003](FKB-003-stale-date-rule-not-answerable.md) | Bug | Medium | Done | 「超過 3 個月提醒過期」規則無法執行，模型自相矛盾 | 「3 か月超で期限切れ注意」というルールは今日の日付を知らないため実行不能で、モデルが自己矛盾した |
| [FKB-004](FKB-004-unused-files-variable.md) | Task | Low | Done | LLM 節點的使用者訊息帶了用不到的 `files` 變數 | LLM ノードのユーザーメッセージに使わない `files` 変数が入っていた |
| [FKB-005](FKB-005-answer-level-eval-runner.md) | Story | High | In Progress | 回答層自動評測腳本（run_chat.py、score_chat.py）；第一輪 chat-001 已跑 | 回答レベルの自動評価スクリプト（run_chat.py、score_chat.py）。chat-001 から実施中 |
| [FKB-006](FKB-006-llm-model-comparison-and-billing.md) | Story | Medium | Open | 比較 Gemini 3.5 Flash-Lite 與 3.8 Flash，並決定是否開啟計費 | Gemini 3.5 Flash-Lite と 3.8 Flash の比較、および課金の要否の判断 |
| [FKB-007](FKB-007-nondeterministic-price-hallucination.md) | Bug | High | Mitigated | 回答偶爾輸出知識庫沒有的價格數字；4 次都在「陽台套房」那一列（預覽 ₩2/人、API ₩2,500,000 ×2、₩2,000；提示詞 v3 後 A1 ×20 無錯價） | ナレッジベースにない金額を稀に出力（4 回ともバルコニースイートの行）。プロンプト v3 後は A1 ×20 で誤金額なし |
| [FKB-008](FKB-008-glued-two-generations.md) | Bug | High | Mitigated | 回答中出現兩段輸出拼接（A1、A3 共 26 次中 4 次；日誌確認為 Gemini「high demand」串流中斷後節點重試，殘缺前半段被保留；重試關閉並發布後 chat-003 20 次無拼接） | 回答に 2 回分の出力が連結される現象。原因は Gemini の途中切断後のノード再試行。再試行オフで公開後は 20 回中 0 件 |
| [FKB-009](FKB-009-answer-language-mismatch.md) | Bug | Medium | Open（部分改善） | 日文、英文提問得到中文內容（A7 3/3、A8 2/3；chat-006 日英 8 題 15/15 次不一致，幾乎全面；v5.1 後日英單語題正文正確 8/20） | 日本語・英語の質問に中国語で回答する。v5.1 で単一言語の質問は一部改善（本文 8/20）。多言語対応は延期 |
| [FKB-010](FKB-010-suspension-not-stated-first.md) | Bug | High | Mitigated | 問上海票價時，客運暫停狀態被放最後且沒說明不能購買（3 次中 2 次；v4 後 A10 ×10 全部先說明） | 上海航路の質問で、旅客輸送の中断という状況の説明が末尾に回り、「この運賃は今購入できることを意味しない」という注意もなかった。v4 後は A10 ×10 で先頭に記載 |
| [FKB-011](FKB-011-eval-harness-limitations.md) | Task | Medium | Open | 回答層測試的限制：A14 單輪無效、A11 沒測到提示詞、拒答帶假來源、評分誤判 | 回答レベルのテストの限界：A14 は単発では無効、A11 はプロンプトを検証できていない、根拠なしの出典付き拒否、採点の誤判定 |
| [FKB-012](FKB-012-overview-questions-miss-threshold.md) | Story | Medium | Done | 概括性問題（「大阪からどこまでいけますか」）被閾值擋掉；需要開場問題按鈕與總覽段落 ；總覽段落已上傳，最模糊的日文問法由固定訊息引導 | 概括的な質問（「大阪からどこまでいけますか」）が閾値で除外される。概要チャンクと開始時の質問ボタンで対応 |
| [FKB-013](FKB-013-output-amount-guardrail.md) | Story | High | Mitigated | 輸出後驗證：回答中的金額不在檢索結果就不顯示；已接進 Dify 並發布；離線 524 個注入全擋、線上 43 次正確回答 0 誤擋（擋下分支尚未線上觸發） | 出力後検証：回答中の金額が検索結果になければ表示しない。Dify に組み込み公開済み。オフライン 524 件の注入を全て遮断、公開版での 43 回の正しい回答で誤遮断 0 件（遮断分岐は公開版でまだ作動していない） |

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
