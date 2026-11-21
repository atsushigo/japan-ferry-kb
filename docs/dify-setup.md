# Dify 設定與重現步驟

> 記錄實際使用的設定。**不要把 API key 提交到版本庫。**
> 介面名稱依 Dify Cloud 繁體中文版（2026-11 當時）；不同版本的位置可能略有不同。

## 1. 前置

| 項目 | 內容 |
|---|---|
| Dify 方案 | Cloud Sandbox（免費）：200 點額度、5 個 app、1 位成員、50 份知識庫文件（以訂閱頁為準，來源之間數字有出入） |
| 模型 API | Google AI Studio 申請的 Gemini API key（與 Gemini 聊天 App 的額度無關） |

免費方案**一次只能上傳一個檔案**；但同一個知識庫可分次加入多份文件。

## 2. 模型供應商

1. 入口：左側選單「集成」（或工作區設定），安裝 Gemini 外掛。
2. 新增授權：
   - 授權名稱：自訂（僅供辨識）
   - API Key：貼上 AI Studio 的 key
   - Base URL、Files URL：**留空**（使用 Google 官方預設）
   - Enable request metadata：Disabled
3. 系統模型設定：

| 項目 | 設定 |
|---|---|
| 系統推理模型 | Gemini 3.8 Flash |
| Embedding 模型 | gemini-embedding-2 |
| Rerank 模型 | 不設定 |
| 語音轉文字／文字轉語音 | 不設定 |

模型選擇原則：推理用標準 Flash（避開 Lite：遵守「查不到就說不知道」的能力較弱；避開 Pro：免費額度較緊）；嵌入模型須支援多語言（資料含日文、韓文、中文），且建庫後換模型需重建索引，所以第一次就選對。

## 3. 建立知識庫

- 名稱：`japan-ferry-kansai`
- 資料來源：匯入已有文字，上傳 `knowledge/` 的 markdown（一次一份，之後用「新增文件」加入第二份）

### 分段設定

| 項目 | 值 | 理由 |
|---|---|---|
| 模式 | 常規 | 先用最簡單的，不用父子分段 |
| 分段識別符號 | `\n\n` | 預設 `\n` 會把表格逐行切碎 |
| 分段最大長度 | 1500 | 票價表加說明可接近 1,000 字 |
| 分段重疊長度 | 50 | 預設 |
| 替換連續空格、換行、製表符 | 勾選 | |
| **刪除所有 URL 和電子郵件** | **不勾** | 文件中的來源網址要保留，機器人才能標示出處 |

### 索引與檢索

| 項目 | 值 |
|---|---|
| 索引方式 | 高品質（建立後無法改回經濟模式） |
| Embedding 模型 | gemini-embedding-2 |
| 檢索方式 | 向量檢索（混合檢索需要 Rerank 模型，未設定） |
| Top K | 5 |
| Score 閾值 | **0.71（建議）**，依據見 [報告 4.5](phase1-rag-audit-report.md)。建庫初期未啟用（0），先取得完整分數分佈再校準；安全區間僅 0.6975–0.7147，每次改版都要重測 |

建立前先用「預覽資料塊」檢查：票價表是否與警告在同一塊、每塊標題是否帶航線標籤。

## 4. 更新知識文件

改了 `knowledge/*.md` 之後：刪除知識庫中的舊文件 → 重新上傳 → 確認「嵌入已完成」→ 重跑召回測試。分段設定要重新確認（上傳時要重設）。

## 5. 召回測試

用 [`../evaluation/questions.csv`](../evaluation/questions.csv)，在知識庫的「檢索測試」逐題輸入，記錄每個回傳段落的分數與是否相關，格式比照 [`../evaluation/runs/run-001_2026-11-21/results.csv`](../evaluation/runs/run-001_2026-11-21/results.csv)。

## 6. 自動化召回測試

[`../evaluation/run_recall.py`](../evaluation/run_recall.py) 讀取測試題，呼叫 Dify 知識庫 API 的
`POST /datasets/{dataset_id}/retrieve`（官方規格：[Retrieve Chunks from a Knowledge Base / Test Retrieval](https://docs.dify.ai/en/api-reference/knowledge-bases/retrieve-chunks-from-a-knowledge-base-test-retrieval)），
寫出一個不可覆蓋的結果資料夾（`config.json` + `results.csv`）。只用 Python 標準函式庫。

**準備**
1. 複製 [`../.env.example`](../.env.example) 成 `.env`（已被 `.gitignore` 排除，**不要提交**）。
2. `DIFY_KB_API_KEY`：知識庫的 API 金鑰（Dify 知識庫頁右上角「服務 API」），**不是**應用程式的金鑰。
3. `DIFY_DATASET_ID`：知識庫頁面網址中的 UUID。

**使用**
```bash
python evaluation/run_recall.py --name run-002 --dry-run               # 只印請求，不呼叫
python evaluation/run_recall.py --name run-002 --ids Q1,Q8             # 先只跑兩題確認 API 正常
python evaluation/run_recall.py --name run-002 --note "v3 docs"        # 全部題目，閾值關閉，取得完整分數分佈
python evaluation/score_run.py evaluation/runs/run-002_<日期>           # 自動評分、閾值掃描
python evaluation/run_recall.py --name run-004 --ids Q6,Q7,Q8,Q20 --threshold 0.71   # 驗證閾值效果
```

**原理**：`questions.csv` 的 `expected_sections` 欄位寫了每題「應該抓到哪個段落」（以段落標題的片段表示）；
`score_run.py` 比對實際回傳段落的標題，自動判定相關或不相關，再算 Hit rate、MRR、Precision@k，
以及「該為空的題目是否真的為空」。閾值關閉的那一輪還會做**閾值掃描**，列出每個候選閾值會損失或放行什麼。

**已知限制**
- `query` 最長 250 字（官方規格）。
- 已對真實 API 執行（run-002～004）。檢索設定以請求參數傳入（`semantic_search`、不使用重排序、閾值）；run-004 證明請求參數的閾值會生效，但當時知識庫畫面上的閾值開關是關閉的，因此**畫面設定與請求參數衝突時以哪個為準，仍未驗證**。
- **免費方案有每分鐘請求上限**：實測連續送出約 10 次後回 403（rate limit）。腳本預設每次間隔 6.5 秒，遇到限制自動等待 65 秒重試；中途失敗會把已完成的結果存成 `*.partial.csv`。
- `query` 最長 250 字（官方規格）。
- 相關性自動判定依 `questions.csv` 的 `expected_sections`；新增題目時要同時寫預期段落（庫外題則 `expect_empty = yes`）。

## 7. 尚未完成

- 聊天機器人（聊天助手 app）與系統提示。
- 回答層面的評測（忠實度、幻覺、引用正確性）。
- 匯出 app DSL 存入版本庫（建好 app 後）。
