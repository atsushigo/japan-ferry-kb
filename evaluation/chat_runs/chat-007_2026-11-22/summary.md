# 回答層規則檢查：chat-007_2026-11-22

- 模型標籤：gemini-3.5-flash-lite　提示詞版本：v4　每題重複：3
- 請求完成：15 / 15
- git：{"commit": "d794397", "dirty": true}

## 規則違規次數（全部回答）

| 規則 | 違規次數 |
|---|---|
| 請求失敗 | 0 / 15 |
| 數字溯源（金額不在檢索段落中） | 0 / 15 |
| 出現禁止用語 | 0 / 15 |
| 預期行為（拒答／做不到） | 0 / 15 |
| 回答語言與提問不一致 | 14 / 15 |
| 疑似兩段輸出拼接（啟發式） | 0 / 15 |
| 缺固定結尾句 | 0 / 15 |
| 缺來源網址 | 0 / 15 |
| 暫停狀態沒有出現在前 120 字 | 0 / 15 |
| 沒說明這不代表現在可以購買 | 0 / 15 |

## 逐題

| 題 | 問題 | 次數 | 需人工複核 | 違規 | 憑空金額 |
|---|---|---|---|---|---|
| A25 | 大阪到釜山船票多少錢？ How much is a ferry ticket from Osaka to Busan? 大阪から釜山までのフェリー運賃はいくらですか？ | 3 | 3 | language | — |
| A26 | 大阪釜山的取消費怎麼算？ How are cancellation fees calculated for the Osaka–Busan ferry? 大阪―釜山のキャンセル料はどう計算されますか？ | 3 | 3 | language | — |
| A27 | 上海航線現在有開嗎？ Is the Shanghai ferry running now? 上海航路は今、運航していますか？ | 3 | 2 | language | — |
| A28 | 搭大阪釜山的船需要準備哪些證件？ What documents do I need for the Osaka–Busan ferry? 大阪―釜山のフェリーに乗るには、どんな書類が必要ですか？ | 3 | 3 | language | — |
| A29 | 大阪港到釜山的行李限制是什麼？ What is the luggage limit from Osaka to Busan? 大阪港から釜山までの荷物制限は？ | 3 | 3 | language | — |

> 本檢查是規則式的：只能發現金額不在來源中、禁用語、缺來源等。**回答用字是否忠於來源，仍須人工閱讀 `checks.csv` 的 answer 欄**，尤其是 `needs_review = True` 的列。金額偵測只認 ₩／¥ 符號或貨幣單位旁的數字，寫成「50萬韓元」之類的形式會漏掉。
