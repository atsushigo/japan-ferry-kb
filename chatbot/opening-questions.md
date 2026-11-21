# 對話開場白與開場問題（Dify「功能」→「對話開場白」）

目的：使用者不知道可以問什麼時，點按鈕就能得到一個確定會命中的問題（[FKB-012](../docs/issues/FKB-012-overview-questions-miss-threshold.md)）。
規則：**每個按鈕的問題都必須是 `test-conversations.csv` 裡已測過的題目，字句完全一致**，這樣按鈕同時也是回歸測試的一部分。

## 開場白（貼進「對話開場白」欄；三語並列）

```text
你好！我是「關西出發國際渡輪」資訊助理，可以回答大阪—釜山（Pan Star）與大阪／神戶—上海（鑑真号）的票價、取消、行李、證件等問題。資料整理自官方網站，可能已過期，請以官方最新公告為準。

Hi! I answer questions about the Osaka–Busan (Pan Star) and Osaka/Kobe–Shanghai (Jianzhen) ferries: fares, cancellation, luggage and documents. The information comes from the official websites and may be out of date; please check the latest official notices.

こんにちは！大阪―釜山（パンスター）と大阪／神戸―上海（鑑真号）の運賃、取消、手荷物、必要書類などにお答えします。情報は公式サイトをもとにしており、最新でない場合があります。公式の最新情報をご確認ください。
```

## 開場問題（每行一個按鈕，逐字貼上）

五個主題各有中文、English、日本語三種版本，共 15 個。每個都對應 `test-conversations.csv` 的一題（A15–A24 是為按鈕新增的翻譯版）。

```text
大阪到釜山船票多少錢？
How much is a ferry ticket from Osaka to Busan?
大阪から釜山までのフェリー運賃はいくらですか？
大阪釜山的取消費怎麼算？
How are cancellation fees calculated for the Osaka–Busan ferry?
大阪―釜山のキャンセル料はどう計算されますか？
上海航線現在有開嗎？
Is the Shanghai ferry running now?
上海航路は今、運航していますか？
搭大阪釜山的船需要準備哪些證件？
What documents do I need for the Osaka–Busan ferry?
大阪―釜山のフェリーに乗るには、どんな書類が必要ですか？
大阪港到釜山的行李限制是什麼？
What is the luggage limit from Osaka to Busan?
大阪港から釜山までの荷物制限は？
```

| 主題 | 中文 | English | 日本語 |
|---|---|---|---|
| 票價 | A1 | A15 | A16 |
| 取消費 | A3 | A17 | A18 |
| 上海航線狀態 | A2 | A19 | A20 |
| 證件 | A21 | A8 | A22 |
| 行李 | A23 | A24 | A7 |

按鈕太多時，優先每種語言各留「票價、上海航線狀態、證件」三個。

## 多語言怎麼做

Dify 的開場問題是**一個按鈕一句固定文字**，沒有「依使用者語言自動切換」的設定，所以做法是把三種語言的按鈕**並列**（上表）。按鈕送出的就是按鈕上的字，模型照提問語言回答（規則 8）。

## 已知問題（設定前先看）

- 日文與英文按鈕會暴露 [FKB-009](../docs/issues/FKB-009-answer-language-mismatch.md)：目前日文、英文提問常得到中文內容（chat-006 實測：日文、英文版 8 題共 16 次，15 次回答被判為語言不一致，1 次請求失敗；看過的幾筆開頭就是中文）。**FKB-009 修好之前不要拿去展示**；修好後用這些按鈕對應的測試題（A7、A8、A15–A20、A22、A24）驗證。
- 按鈕只能引導，不能保證使用者不問庫外題；庫外與概括性問題仍靠閾值與固定訊息處理。
