# FKB-004：LLM 節點的使用者訊息帶了用不到的 `files` 變數

| Field | Value |
|---|---|
| Type / Priority / Status | Task / Low / Done |
| Component | chatbot-flow |
| Found in | Dify 聊天流預設範本 |
| Reported | 2026-11-21 22:06 JST |

## Description
聊天流範本的 LLM 節點使用者訊息預設包含 `開始 / query` 與 `開始 / files`。單步測試時出現錯誤 `sys.files 不能為空`。本專案不處理檔案。

## Root cause（Confirmed）
範本預設把檔案變數放進使用者訊息，單步測試會要求提供。

## Resolution
刪除 `files`，使用者訊息只保留 `query`。刪除後單步測試只要求輸入 `sys.query`，完整流程預覽通過。

## Verification
單步測試輸入「你好」可執行；完整流程預覽回答正常。

## Lessons learned
範本預設值要逐項檢視，不需要的輸入拿掉，可減少錯誤來源與每次請求的負擔。
