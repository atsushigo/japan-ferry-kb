#!/usr/bin/env python3
"""Score a recall run automatically.

A returned chunk counts as RELEVANT when its section title contains one of the strings listed in
the question's `expected_sections` column (questions.csv). Everything else is OFF_TOPIC; a chunk
whose title does not start with a route tag ("【") is META (a structural chunk such as a header).
Questions with `expect_empty = yes` (out-of-scope questions) should return nothing.

Reads   <run_dir>/results.csv         (written by run_recall.py)
Writes  <run_dir>/labeled_results.csv, metrics.json, summary.md

If the run was made with the score threshold disabled, the report also contains a threshold
sweep: for each candidate threshold, what would have been lost or let through.

Usage:  python evaluation/score_run.py evaluation/runs/run-002_2026-11-21
"""
import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWEEP = [0.50, 0.60, 0.65, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75]


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def label_of(title: str, expected: list) -> str:
    if title == "(no results)":
        return ""
    if expected and any(e in title for e in expected):
        return "relevant"
    if not title.startswith("【"):
        return "meta"
    return "off_topic"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--questions", default=str(ROOT / "evaluation" / "questions.csv"))
    a = ap.parse_args()
    run = Path(a.run_dir)

    questions = {q["id"]: q for q in csv.DictReader(open(a.questions, encoding="utf-8", newline=""))}
    results = list(csv.DictReader(open(run / "results.csv", encoding="utf-8", newline="")))
    config = json.loads((run / "config.json").read_text(encoding="utf-8")) if (run / "config.json").exists() else {}
    threshold_used = config.get("api", {}).get("score_threshold")

    by_q = OrderedDict()
    for r in results:
        by_q.setdefault(r["query_id"], []).append(r)

    labeled, per_q = [], []
    for qid, rs in by_q.items():
        q = questions.get(qid, {})
        expected = [s for s in (q.get("expected_sections") or "").split("|") if s]
        expect_empty = q.get("expect_empty") == "yes"
        rs = sorted([r for r in rs if r["rank"] != ""], key=lambda r: int(r["rank"])) or rs
        for r in rs:
            labeled.append({**r, "label": label_of(r["section_title"], expected)})
        got = [r for r in rs if r["rank"] != ""]
        rel = [r for r in got if label_of(r["section_title"], expected) == "relevant"]
        scores = [fnum(r["score"]) for r in got if fnum(r["score"]) is not None]
        per_q.append({
            "id": qid, "query": rs[0]["query"], "expect_empty": expect_empty, "n_expected": len(expected),
            "n_returned": len(got), "n_relevant": len(rel),
            "hit": bool(rel) if expected else None,
            "first_relevant_rank": int(rel[0]["rank"]) if rel else None,
            "precision": round(len(rel) / len(got), 3) if got and expected else None,
            "top_score": max(scores) if scores else None,
            "relevant_min": min(fnum(r["score"]) for r in rel) if rel else None,
            "offtopic_max": max([fnum(r["score"]) for r in got if label_of(r["section_title"], expected) != "relevant"] or [None]) if got else None,
            "missing_sections": [e for e in expected if not any(e in r["section_title"] for r in got)],
        })

    scored = [p for p in per_q if p["hit"] is not None]
    hits = [p for p in scored if p["hit"]]
    mrr = sum(1 / p["first_relevant_rank"] for p in hits) / len(scored) if scored else 0
    prec = [p["precision"] for p in scored if p["precision"] is not None]
    empties = [p for p in per_q if p["expect_empty"]]
    overall = {
        "questions": len(per_q), "scored_questions": len(scored),
        "hit_rate": round(len(hits) / len(scored), 3) if scored else None,
        "mrr": round(mrr, 3), "mean_precision_at_k": round(sum(prec) / len(prec), 3) if prec else None,
        "expect_empty_questions": len(empties),
        "expect_empty_returned_nothing": sum(1 for p in empties if p["n_returned"] == 0),
        "threshold_used": threshold_used,
    }

    sweep = []
    if threshold_used is None:
        for t in SWEEP:
            lost = sum(1 for r in labeled if r["label"] == "relevant" and (fnum(r["score"]) or 0) < t)
            off = sum(1 for r in labeled if r["label"] == "off_topic" and (fnum(r["score"]) or 0) >= t)
            meta = sum(1 for r in labeled if r["label"] == "meta" and (fnum(r["score"]) or 0) >= t)
            missed = sum(1 for p in scored if p["hit"] and (p["relevant_min"] is not None) and
                         not any(r["query_id"] == p["id"] and r["label"] == "relevant" and (fnum(r["score"]) or 0) >= t
                                 for r in labeled))
            unblocked = sum(1 for p in empties if any(r["query_id"] == p["id"] and (fnum(r["score"]) or 0) >= t for r in labeled))
            sweep.append({"threshold": t, "relevant_chunks_lost": lost, "questions_losing_all_relevant": missed,
                          "off_topic_passing": off, "meta_passing": meta, "expect_empty_not_blocked": unblocked})

    # write outputs
    with open(run / "labeled_results.csv", "w", encoding="utf-8", newline="") as f:
        fields = list(labeled[0].keys()) if labeled else ["query_id"]
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(labeled)
    (run / "metrics.json").write_text(json.dumps({"overall": overall, "per_question": per_q, "threshold_sweep": sweep},
                                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def f2(x):
        return "" if x is None else f"{x:.2f}"

    L = [f"# 召回測試評分：{run.name}", "",
         f"- 設定：{json.dumps(config.get('api', {}), ensure_ascii=False)}",
         f"- 知識文件指紋：{json.dumps(config.get('knowledge_files', {}), ensure_ascii=False)}",
         f"- git：{json.dumps(config.get('git', {}), ensure_ascii=False)}", "",
         "## 整體指標", "",
         "| 指標 | 值 |", "|---|---|",
         f"| 有預期段落的題數 | {overall['scored_questions']} |",
         f"| Hit rate（前 k 名含相關段落） | {overall['hit_rate']} |",
         f"| MRR（第一個相關段落的排名倒數平均） | {overall['mrr']} |",
         f"| 平均 Precision@k | {overall['mean_precision_at_k']} |",
         f"| 該為空的題數／實際為空 | {overall['expect_empty_questions']} / {overall['expect_empty_returned_nothing']} |",
         "", "## 逐題結果", "",
         "| 題 | 問題 | 命中 | 首個相關排名 | 回傳數 | 相關數 | 相關最低分 | 不相關最高分 | 缺少的預期段落 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for p in per_q:
        hit = "—（應為空）" if p["expect_empty"] else ("✅" if p["hit"] else ("❌" if p["hit"] is False else "—"))
        L.append(f"| {p['id']} | {p['query']} | {hit} | {p['first_relevant_rank'] or ''} | {p['n_returned']} | "
                 f"{p['n_relevant']} | {f2(p['relevant_min'])} | {f2(p['offtopic_max'])} | {'；'.join(p['missing_sections'])} |")
    if sweep:
        L += ["", "## 閾值掃描（本輪未啟用閾值，由完整分數計算）", "",
              "| 閾值 | 損失的相關段落 | 完全找不到相關段落的題數 | 通過的不相關段落 | 通過的結構性段落 | 應為空但仍有結果的題數 |",
              "|---|---|---|---|---|---|"]
        for s in sweep:
            L.append(f"| {s['threshold']:.2f} | {s['relevant_chunks_lost']} | {s['questions_losing_all_relevant']} | "
                     f"{s['off_topic_passing']} | {s['meta_passing']} | {s['expect_empty_not_blocked']} |")
    L += ["", "> 相關性由 `questions.csv` 的 `expected_sections` 自動判定（段落標題包含預期字串即相關），"
          "不是人工逐筆判讀；預期字串本身是人工設定的。", ""]
    (run / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:14]))
    print(f"\nwrote {run}/labeled_results.csv, metrics.json, summary.md")


if __name__ == "__main__":
    main()
