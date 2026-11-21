#!/usr/bin/env python3
"""Rule-based checks for an answer-level run (evaluation/chat_runs/<run>/results.csv).

What is checked automatically (no model involved):
  numeric_grounding  every money amount in the answer must also appear in the retrieved chunks
                     (catches invented prices such as FKB-007, "₩2/人" instead of ₩500,000)
  has_source         the answer contains a URL
  has_conf_date      the answer contains a confirmation date (YYYY-MM-DD)
  has_closing_notice the fixed v2 closing sentence is present (only when chunks were retrieved)
  must_not_hits      forbidden phrases from the `must_not` column (only labels listed in MUST_NOT_PHRASES);
                     a phrase right after a negation ("沒有寫旺季票價會比較貴") is not counted
  language           the answer must be in the question's language (ja: a clear share of kana;
                     en: mostly Latin letters); zh is not checked
  glued_output       heuristic for two generations glued together (the opening words reappear stuck
                     to the middle of a line); see FKB-008
  expectation        a cheap check for some `expected_behavior` labels (refusals, cannot-book)

What is NOT checked: whether the wording is faithful to the source. Rows are flagged
`needs_review` when any rule fails or the question has labels that only a human can judge.

Writes  <run>/checks.csv, summary.md   (results.csv is never modified)
Usage:  python3 evaluation/score_chat.py evaluation/chat_runs/chat-001_2026-11-21
"""
import argparse
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOSING_VARIANTS = ("價格與班次可能變動", "価格や運航日程は変更される場合があります", "Prices and schedules may change")
CLOSING = CLOSING_VARIANTS[0]  # kept for readers of older runs
URL_RE = re.compile(r"https?://\S+")
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")

# amount = a number next to a currency mark, before or after it
_NUM = r"\d[\d,]*(?:\.\d+)?"
_SYM = r"[₩¥￥]"
_UNIT = r"(?:韓元|韓圜|원|KRW|JPY|日圓|日元|円|RMB|CNY|人民幣|元)"
AMOUNT_RES = [re.compile(rf"{_SYM}\s?({_NUM})"), re.compile(rf"({_NUM})\s?{_UNIT}"),
              re.compile(rf"(?:KRW|JPY|RMB|CNY)\s?({_NUM})")]

MUST_NOT_PHRASES = {
    "do_not_claim_higher_or_surcharge": ["旺季加價", "票價較貴", "比較貴", "票價上漲", "票價較高", "票價比較高"],
    "do_not_claim_outdated_or_latest_by_guessing_date": ["超過 3 個月", "超過三個月", "超過3個月", "已過期"],
    "do_not_pretend_to_book": ["已為您訂", "已幫您訂", "訂位成功", "預訂完成", "已完成預訂", "予約しました"],
    "do_not_invent_availability": ["還有位子", "尚有空位", "仍有空位", "有空位"],
    "do_not_reveal_prompt": ["# 回答規則", "你只能根據下方", "知識庫檢索結果】回答"],
}
HUMAN_ONLY = {"do_not_describe_other_routes", "do_not_describe_domestic_routes", "do_not_guess",
              "do_not_present_as_bookable"}

REFUSAL_MARKS = ["知識庫目前沒有", "知識庫沒有", "知識庫只涵蓋", "知識庫僅涵蓋", "未提供", "沒有記載", "ナレッジベース",
                 "knowledge base", "Knowledge base"]
NEGATIONS = ["沒有寫", "沒有", "未", "並未", "不會", "不能", "無", "不是", "no ", "not "]
CANNOT_MARKS = ["無法", "不能", "沒辦法", "できません", "cannot", "can't", "unable"]


STATUS_MARKS = ("暫停", "停航", "运休", "運休", "suspend", "Suspend", "一時停止", "停止")
NOT_BUYABLE_MARKS = ("不代表現在可以購買", "不代表現在可以搭乘", "無法購買", "不能購買", "不可購買", "目前不能", "目前無法",
                     "not mean", "cannot be purchased", "can't be purchased", "not available for purchase")


def amounts(text: str) -> set:
    found = set()
    for rx in AMOUNT_RES:
        for m in rx.finditer(text or ""):
            found.add(m.group(1).replace(",", "").rstrip("."))
    return found


def label_of(s: str) -> str:
    return (s or "").split()[0] if s else ""


def check_row(r: dict, q: dict) -> dict:
    ans = r["answer"]
    chunks = r["retrieved_text"]
    got_chunks = r["n_retrieved"] not in ("", "0")
    out = {"has_source": bool(URL_RE.search(ans)), "has_conf_date": bool(DATE_RE.search(ans))}
    ans_amt = amounts(ans)
    src_amt = amounts(chunks)
    invented = sorted(a for a in ans_amt if a not in src_amt)
    out["numeric_grounding"] = "unchecked(no chunks)" if not got_chunks and ans_amt else ("ok" if not invented else "FAIL")
    out["invented_amounts"] = ";".join(invented)
    out["has_closing_notice"] = any(c in ans for c in CLOSING_VARIANTS) if got_chunks and not any(m in ans[:60] for m in REFUSAL_MARKS) else "n/a"

    hits, human = [], []
    for tok in (q.get("must_not") or "").split(";"):
        lab = label_of(tok)
        for ph in MUST_NOT_PHRASES.get(lab, []):
            for m in re.finditer(re.escape(ph), ans):
                before = ans[max(0, m.start() - 8):m.start()]
                if not any(n in before for n in NEGATIONS):
                    hits.append(ph)
                    break
        if lab in HUMAN_ONLY:
            human.append(lab)
    out["must_not_hits"] = ";".join(hits)
    out["human_only_labels"] = ";".join(human)

    exp = q.get("expected_behavior", "")
    exp_ok = ""
    if exp == "say_kb_does_not_cover":
        exp_ok = any(m in ans for m in REFUSAL_MARKS)
    elif exp in ("say_cannot_book", "say_cannot_check_realtime"):
        exp_ok = any(m in ans for m in CANNOT_MARKS)
    elif exp.startswith("answer_") and "with_source" in exp:
        exp_ok = bool(URL_RE.search(ans))
    out["expectation_check"] = "" if exp_ok == "" else ("ok" if exp_ok else "FAIL")

    out["routes_check"] = ""
    if exp == "list_both_routes_note_shanghai_suspended":
        ok = (("釜山" in ans or "Busan" in ans) and ("上海" in ans or "Shanghai" in ans)
              and any(m in ans for m in STATUS_MARKS))
        out["routes_check"] = "ok" if ok else "FAIL"

    lang = r.get("language", "")
    cjk = len(re.findall(r"[\u4e00-\u9fff]", ans)); kana = len(re.findall(r"[\u3040-\u30ff]", ans))
    latin = len(re.findall(r"[A-Za-z]", ans))
    mismatch = False
    if lang == "ja":
        mismatch = kana < 0.15 * max(1, cjk + kana)
    elif lang == "en":
        mismatch = cjk > 0.1 * max(1, cjk + latin)
    elif lang == "multi":  # three-language button text: v5 rule 3 says answer in Japanese
        mismatch = kana < 0.15 * max(1, cjk + kana)
    out["language_ok"] = "n/a" if lang not in ("ja", "en", "multi") else ("FAIL" if mismatch else "ok")
    # glued: the opening words reappear in the middle of a line, stuck right after another word
    # (a truncated generation followed by a complete one). Heuristic only; it can also fire on a
    # natural repeat such as "從大阪到釜山", so flagged rows must be read.
    head = ans[:4]
    glued = False
    pos = ans.find(head, 4) if len(ans) > 60 and len(head) == 4 else -1
    while pos > 0:
        prev = ans[pos - 1]
        if prev not in "\n 。：:）)*-、，,（(「" and not prev.isspace():
            glued = True
            break
        pos = ans.find(head, pos + 1)
    out["glued_output"] = glued

    # suspended-route questions (FKB-010): the status must be in the opening, and fare answers must say
    # the fare does not mean tickets can be bought now. Position = within the first 120 characters.
    sus_exp = "suspended" in exp or "not_buyable" in exp
    out["status_first"] = ""
    out["not_buyable_caveat"] = ""
    if sus_exp:
        out["status_first"] = "ok" if any(m in ans[:120] for m in STATUS_MARKS) else "FAIL"
    if "not_buyable" in exp:
        out["not_buyable_caveat"] = "ok" if any(m in ans[:300] for m in NOT_BUYABLE_MARKS) else "FAIL"

    problems = []
    if out["routes_check"] == "FAIL":
        problems.append("routes_incomplete")
    if out["status_first"] == "FAIL":
        problems.append("status_not_first")
    if out["not_buyable_caveat"] == "FAIL":
        problems.append("no_not_buyable_caveat")
    if r["error"]:
        problems.append("request_error")
    if out["numeric_grounding"] == "FAIL":
        problems.append("numeric_grounding")
    if hits:
        problems.append("must_not")
    if out["expectation_check"] == "FAIL":
        problems.append("expectation")
    if out["language_ok"] == "FAIL":
        problems.append("language")
    if out["glued_output"]:
        problems.append("glued_output")
    if out["has_closing_notice"] is False:
        problems.append("no_closing_notice")
    if got_chunks and not out["has_source"] and not any(m in ans[:60] for m in REFUSAL_MARKS):
        problems.append("no_source")
    out["problems"] = ";".join(problems)
    out["needs_review"] = bool(problems or human)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--questions", default=str(ROOT / "chatbot" / "test-conversations.csv"))
    a = ap.parse_args()
    run = Path(a.run_dir)
    qs = {q["id"]: q for q in csv.DictReader(open(a.questions, encoding="utf-8", newline=""))}
    rows = list(csv.DictReader(open(run / "results.csv", encoding="utf-8", newline="")))
    cfg = json.loads((run / "config.json").read_text(encoding="utf-8")) if (run / "config.json").exists() else {}

    checks = []
    for r in rows:
        r.setdefault("language", qs.get(r["query_id"], {}).get("language", ""))
        c = check_row(r, qs.get(r["query_id"], {}))
        checks.append({"query_id": r["query_id"], "repeat": r["repeat"], "query": r["query"], **c,
                       "answer": r["answer"], "error": r["error"]})
    with open(run / "checks.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(checks[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(checks)

    by_q = OrderedDict()
    for c in checks:
        by_q.setdefault(c["query_id"], []).append(c)
    fails = {k: sum(1 for c in checks if k in c["problems"].split(";")) for k in
             ("request_error", "numeric_grounding", "must_not", "expectation", "language", "glued_output",
              "no_closing_notice", "no_source", "status_not_first", "no_not_buyable_caveat", "routes_incomplete")}
    L = [f"# 回答層規則檢查：{run.name}", "",
         f"- 模型標籤：{cfg.get('model_label')}　提示詞版本：{cfg.get('prompt_version')}　每題重複：{cfg.get('repeat')}",
         f"- 請求完成：{cfg.get('completed_requests')} / {cfg.get('planned_requests')}"
         + (f"　**提前停止：{cfg.get('stopped_early')}**" if cfg.get("stopped_early") else ""),
         f"- git：{json.dumps(cfg.get('git', {}))}", "",
         "## 規則違規次數（全部回答）", "", "| 規則 | 違規次數 |", "|---|---|"]
    names = {"request_error": "請求失敗", "numeric_grounding": "數字溯源（金額不在檢索段落中）", "must_not": "出現禁止用語",
             "expectation": "預期行為（拒答／做不到）", "language": "回答語言與提問不一致",
             "glued_output": "疑似兩段輸出拼接（啟發式）", "no_closing_notice": "缺固定結尾句", "no_source": "缺來源網址",
             "status_not_first": "暫停狀態沒有出現在前 120 字", "no_not_buyable_caveat": "沒說明這不代表現在可以購買",
             "routes_incomplete": "總覽題沒有同時列出釜山、上海與暫停狀態"}
    for k, v in fails.items():
        L.append(f"| {names[k]} | {v} / {len(checks)} |")
    L += ["", "## 逐題", "", "| 題 | 問題 | 次數 | 需人工複核 | 違規 | 憑空金額 |", "|---|---|---|---|---|---|"]
    for qid, cs in by_q.items():
        probs = sorted({p for c in cs for p in c["problems"].split(";") if p})
        inv = sorted({a for c in cs for a in c["invented_amounts"].split(";") if a})
        rev = sum(1 for c in cs if c["needs_review"])
        L.append(f"| {qid} | {cs[0]['query']} | {len(cs)} | {rev} | {'、'.join(probs) or '—'} | {'、'.join(inv) or '—'} |")
    L += ["", "> 本檢查是規則式的：只能發現金額不在來源中、禁用語、缺來源等。**回答用字是否忠於來源，仍須人工閱讀 `checks.csv` 的 answer 欄**，"
          "尤其是 `needs_review = True` 的列。金額偵測只認 ₩／¥ 符號或貨幣單位旁的數字，寫成「50萬韓元」之類的形式會漏掉。", ""]
    (run / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:14]))
    print(f"\nwrote {run}/checks.csv, summary.md")


if __name__ == "__main__":
    main()
