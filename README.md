# Japan Ferry KB — 關西出發國際渡輪 RAG 知識庫

以 **Dify Cloud** 建立的「從大阪／神戶出發的國際渡輪」知識庫聊天機器人。重點不只是做出聊天機器人，而是示範：**資料怎麼查證、怎麼整理、怎麼測試、怎麼在資料矛盾或過期時不讓機器人亂答**。

> **狀態（2026-11-21）**：Phase 1 進行中。知識庫已建立並完成第一輪召回測試；聊天機器人（系統提示與回答流程）尚未建立。
> 完整分析見 **[第一階段 RAG 資料稽核與檢索調校報告](docs/phase1-rag-audit-report.md)**。

## 這個專案發現了什麼

1. **官方資料互相矛盾，不能直接餵給模型。**
   上海航線：官方 2025-12-08 公告旅客運送暫停、再開未定，但官網船班表仍列出到 2027 年 6 月的班次，且不區分載客或貨運。釜山航線：日文與韓文兩個官方網站的退票規定數字不一致。
2. **有價值的資訊藏在 PDF、圖片，甚至頁面原始碼裡。** 票價表的文字層是亂碼，必須轉成圖片目視核對；釜山官網 FAQ 的答案被抓取工具判定為「只有標題」，直接解析原始 HTML 才拿到 62 題完整答案。
3. **向量檢索的分數無法分辨「檔頭／標題」這類沒有答案的段落**（它們最高可達 0.80，和答案段落一樣高），只能靠改文件結構解決；但閾值可以擋住「知識庫沒有的題目」。
4. **檢索閾值要靠實測校準，而且安全區間很窄。** 這個嵌入模型的分數集中在 0.61–0.83，未啟用閾值時所有結果都會通過，常見的中間值（例如 0.5）也擋不住任何東西。用 24 題（含 9 題庫外題）校準後，能同時「不漏掉答案」與「擋住庫外題」的區間只有 0.6975–0.7147（寬 0.017），建議閾值 0.71；語意相近但不在範圍內的問題（例如福岡到釜山）也能拿到 0.70，所以閾值不能是唯一的防線。
5. **改文件結構比調參數有效。** 把文件改成「一段一個主題、標題帶航線標籤、來源寫在段落內」後，15 題有預期答案的題目，相關段落全數排第 1、預期段落 21/21 全部找回，結構性段落從 7/26 降到 0。

![閾值校準圖](docs/assets/threshold-calibration.png)

*第一輪（手動、舊版文件）的分數分佈見 [報告 4.3](docs/phase1-rag-audit-report.md)。*

## 架構

```mermaid
flowchart LR
  A["官方網站與 PDF<br/>panstar.jp · panstarcruise.com · shinganjin.com"] --> B["查證與整理<br/>平行 agent 讀取 + 人工核對"]
  B --> C["knowledge/*.md<br/>一段一個主題，附來源與確認日期"]
  C --> D["Dify Cloud 知識庫<br/>gemini-embedding-2 · 分段 1500 字"]
  D --> E["向量檢索<br/>Top K 5 · 閾值 0.71"]
  E --> F["聊天機器人<br/>Gemini Flash（設計中）"]
  F --> G["使用者"]
  F -.-> H["Phase 2：FastAPI + PostgreSQL"]
```

## 聊天機器人的回答流程（設計目標，尚未實作）

```mermaid
flowchart TD
  Q["使用者提問"] --> R["檢索知識庫"]
  R --> E{"有達閾值的段落？"}
  E -- 否 --> N["回答：知識庫沒有這項資料<br/>並建議洽營運公司"]
  E -- 是 --> S{"該航線公告暫停？"}
  S -- 是 --> W["先說明暫停狀態<br/>不提供訂票或搭乘建議"]
  S -- 否 --> C{"不同官方來源互相矛盾？"}
  W --> C
  C -- 是 --> B["兩邊規定都列出並標明來源"]
  C -- 否 --> A["依段落內容回答"]
  B --> F["附上來源與確認日期"]
  A --> F
```

## 目前涵蓋的航線

| 航線 | 營運公司 | 狀態（2026-11-21 確認） | 知識文件 |
|---|---|---|---|
| 大阪 ⇄ 釜山 | PANSTAR Cruise Ferry（日本代理 Sunstar Line） | 官網未見停航公告，無法確認最新班表 | [`knowledge/osaka-busan-panstar.md`](knowledge/osaka-busan-panstar.md) |
| 大阪／神戶 ⇄ 上海 | 日中国際フェリー「鑑真号」 | **旅客運送暫停中**（官方公告），官網班表矛盾 | [`knowledge/kansai-shanghai-shinganjin.md`](knowledge/kansai-shanghai-shinganjin.md) |

Phase 1 只做這兩條國際航線，國內航線（神戶–高松等）留到第二階段。

## 專案結構

```text
japan-ferry-kb/
├── README.md
├── knowledge/                      知識庫來源文件（持續更新）
│   ├── osaka-busan-panstar.md
│   ├── kansai-shanghai-shinganjin.md
│   ├── overview-routes.md          航線總覽（讓「有哪些航線」這類問題能命中）
│   └── history/                    曾上傳並測試過的舊版本（對應測試紀錄）
├── chatbot/                        Dify 聊天流設定、系統提示詞（含版本）、回答層測試題
├── evaluation/
│   ├── questions.csv          測試題、預期行為與預期段落
│   ├── run_recall.py          呼叫 Dify 知識庫 API 跑召回測試
│   ├── score_run.py           自動評分與閾值掃描
│   ├── run_chat.py            呼叫聊天應用 API 跑回答層測試（可重複、限速）
│   ├── score_chat.py          回答層規則檢查（金額溯源、禁用語、來源）
│   ├── chat_runs/             回答層每次測試一個資料夾
│   └── runs/                  每次測試一個資料夾（run-001 手動；run-002～004 自動）
│       └── run-00X_日期/      config.json、results.csv、labeled_results.csv、summary.md
└── docs/
    ├── phase1-rag-audit-report.md  稽核與調校報告
    ├── dify-setup.md               Dify 設定與重現步驟
    ├── sources.md                  資料來源與查證紀錄
    ├── coverage-matrix.md          航線 × 主題的資料覆蓋盤點
    ├── hallucination-mitigation-options.md  數字幻覺的處理選項（含本專案實例）
    ├── issues/                     問題與改善紀錄（Jira 格式，FKB-001～）
    └── assets/
        ├── threshold-calibration.png  閾值校準圖（本頁上方）
        ├── retrieval-scores.png       第一輪（舊版文件）分數分佈
        ├── make_calibration_chart.py  由 run-002／003 產生校準圖
        └── make_retrieval_chart.py    由 run-001 產生第一輪圖
```

## 重現

1. 依 [`docs/dify-setup.md`](docs/dify-setup.md) 設定模型供應商與知識庫（需自備 Gemini API key，**不要提交 key**）。
2. 上傳 `knowledge/` 底下的兩份文件。
3. 用 [`evaluation/questions.csv`](evaluation/questions.csv) 在 Dify「召回測試」逐題檢查。
4. 重畫圖表：`pip install matplotlib && python docs/assets/make_retrieval_chart.py`

## Roadmap

| 階段 | 內容 | 狀態 |
|---|---|---|
| Phase 1 | 知識庫、召回調校、聊天機器人與系統提示、基本評測 | **進行中**（知識庫與召回測試完成） |
| Phase 2 | FastAPI 串接 Dify API、PostgreSQL、國內航線資料 | 未開始 |
| Phase 3 以後 | 工作流程自動化、人工審核、品質評測、部署 | 未規劃細節 |

## 資料聲明

`knowledge/` 的內容是本專案從營運公司官方網站與公告**整理的摘要**，確認日期見各段落結尾。票價、班次與規定會變動，**可能已過期，不構成訂票或搭乘建議**，請以營運公司官方資訊為準。沒有官方依據的項目一律標示「未取得」，不補編。

授權：尚未決定。
