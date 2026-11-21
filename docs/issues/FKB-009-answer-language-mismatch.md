# FKB-009：回答沒有使用提問的語言（日文、英文提問得到中文內容）

| Field | Value |
|---|---|
| Type / Priority / Status | Bug / Medium / Open |
| Component | chatbot-prompt |
| Found in | chat-001、提示詞 v2、gemini-3.5-flash-lite |
| Reported | 2026-11-21 JST |

## Description
提示詞規則 8 要求用提問的語言回答。實測：

| 題 | 提問語言 | 結果（3 次） |
|---|---|---|
| A7 荷物制限 | 日文 | 3/3 只有開頭一句日文，其餘條列為繁體中文 |
| A8 What documents do I need... | 英文 | 2/3 全中文，1/3 英文 |

## Root cause（Suspected）
檢索回來的段落是繁體中文，模型傾向直接沿用原文；規則 8 在提示詞中排在第 8 位，沒有明確要求「資料是中文時也要翻成提問語言」。

## Resolution（提案，未驗證）
把語言規則移到最前面並寫明：「先判斷使用者提問的語言，整個回答（含條列與結尾句）都用該語言；檢索結果是中文時也要翻譯成該語言，專有名詞（船名、艙等名稱、網址）保留原文。」

## Verification
A7、A8 各重跑 10 次，`score_chat.py` 的 language 檢查零違規，再人工確認譯文沒有改變金額與規則。

## Lessons learned
目標族群包含日本面試官，語言一致是展示重點；規則放在提示詞後段，模型遵守度較低。
