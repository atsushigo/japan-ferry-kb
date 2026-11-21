# 回答層規則檢查：chat-006_2026-11-22

- 模型標籤：gemini-3.5-flash-lite　提示詞版本：v4　每題重複：2
- 請求完成：20 / 20
- git：{"commit": "65add39", "dirty": true}

## 規則違規次數（全部回答）

| 規則 | 違規次數 |
|---|---|
| 請求失敗 | 1 / 20 |
| 數字溯源（金額不在檢索段落中） | 0 / 20 |
| 出現禁止用語 | 0 / 20 |
| 預期行為（拒答／做不到） | 0 / 20 |
| 回答語言與提問不一致 | 16 / 20 |
| 疑似兩段輸出拼接（啟發式） | 1 / 20 |
| 缺固定結尾句 | 0 / 20 |
| 缺來源網址 | 0 / 20 |
| 暫停狀態沒有出現在前 120 字 | 1 / 20 |
| 沒說明這不代表現在可以購買 | 0 / 20 |

## 逐題

| 題 | 問題 | 次數 | 需人工複核 | 違規 | 憑空金額 |
|---|---|---|---|---|---|
| A15 | How much is a ferry ticket from Osaka to Busan? | 2 | 2 | language | — |
| A16 | 大阪から釜山までのフェリー運賃はいくらですか？ | 2 | 2 | language | — |
| A17 | How are cancellation fees calculated for the Osaka–Busan ferry? | 2 | 2 | language | — |
| A18 | 大阪―釜山のキャンセル料はどう計算されますか？ | 2 | 2 | language | — |
| A19 | Is the Shanghai ferry running now? | 2 | 2 | glued_output、language | — |
| A20 | 上海航路は今、運航していますか？ | 2 | 2 | language、request_error、status_not_first | — |
| A21 | 搭大阪釜山的船需要準備哪些證件？ | 2 | 0 | — | — |
| A22 | 大阪―釜山のフェリーに乗るには、どんな書類が必要ですか？ | 2 | 2 | language | — |
| A23 | 大阪港到釜山的行李限制是什麼？ | 2 | 0 | — | — |
| A24 | What is the luggage limit from Osaka to Busan? | 2 | 2 | language | — |

> 本檢查是規則式的：只能發現金額不在來源中、禁用語、缺來源等。**回答用字是否忠於來源，仍須人工閱讀 `checks.csv` 的 answer 欄**，尤其是 `needs_review = True` 的列。金額偵測只認 ₩／¥ 符號或貨幣單位旁的數字，寫成「50萬韓元」之類的形式會漏掉。
