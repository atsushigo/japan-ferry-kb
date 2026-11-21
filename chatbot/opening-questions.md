# 對話開場白與開場問題（Dify「功能」→「對話開場白」）

目的：使用者不知道可以問什麼時，點按鈕就能得到一個確定會命中的問題（[FKB-012](../docs/issues/FKB-012-overview-questions-miss-threshold.md)）。
規則：**每個按鈕的問題都必須是 `test-conversations.csv` 裡已測過的題目，字句完全一致**，這樣按鈕同時也是回歸測試的一部分。

## 開場白（貼進「對話開場白」欄；三語並列）

```text
你好！我是「關西出發國際渡輪」資訊助理，可以回答大阪—釜山（Pan Star）與大阪／神戶—上海（鑑真号）的票價、取消、行李、證件等問題。資料整理自官方網站，可能已過期，請以官方最新公告為準。

Hi! I answer questions about the Osaka–Busan (Pan Star) and Osaka/Kobe–Shanghai (Jianzhen) ferries: fares, cancellation, luggage and documents. The information comes from the official websites and may be out of date; please check the latest official notices.

こんにちは！大阪―釜山（パンスター）と大阪／神戸―上海（鑑真号）の運賃、取消、手荷物、必要書類などにお答えします。情報は公式サイトをもとにしており、最新でない場合があります。公式の最新情報をご確認ください。
```

## 開場問題（每行一個按鈕）

| 按鈕文字（逐字貼上） | 對應測試題 | 語言 |
|---|---|---|
| 大阪到釜山船票多少錢？ | A1 | 中文 |
| 大阪釜山的取消費怎麼算？ | A3 | 中文 |
| 上海航線現在有開嗎？ | A2 | 中文 |
| What documents do I need for the Osaka–Busan ferry? | A8 | English |
| 大阪港から釜山までの荷物制限は？ | A7 | 日本語 |

## 多語言怎麼做

Dify 的開場問題是**一個按鈕一句固定文字**，沒有「依使用者語言自動切換」的設定，所以做法是把三種語言的按鈕**並列**（上表）。按鈕送出的就是按鈕上的字，模型照提問語言回答（規則 8）。

## 已知問題（設定前先看）

- 日文與英文按鈕（A7、A8）會暴露 [FKB-009](../docs/issues/FKB-009-answer-language-mismatch.md)：目前日文、英文提問常得到中文內容（A7 3/3、A8 2/3）。**FKB-009 修好之前不要拿去展示**；修好後再用這兩個按鈕驗證。
- 按鈕只能引導，不能保證使用者不問庫外題；庫外與概括性問題仍靠閾值與固定訊息處理。
