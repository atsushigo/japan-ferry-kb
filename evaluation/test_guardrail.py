#!/usr/bin/env python3
"""Offline test of chatbot/guardrail/amount_check.py against every answer collected so far.

1. Replay: run the guardrail on all rows of evaluation/chat_runs/*/results.csv (answer + retrieved_text).
   Report how many answers it would have blocked, and list them.
2. Injection: take answers that passed, change one correct amount into a wrong one (the wrong values seen in
   FKB-007 and a few others) and check that the guardrail blocks every one of them.

Usage: python evaluation/test_guardrail.py
"""
import csv
import glob
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("amount_check", ROOT / "chatbot" / "guardrail" / "amount_check.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

rows = []
for f in sorted(glob.glob(str(ROOT / "evaluation" / "chat_runs" / "*" / "results.csv"))):
    run = Path(f).parent.name.split("_")[0]
    for r in csv.DictReader(open(f, encoding="utf-8", newline="")):
        if r["answer"]:
            rows.append((run, r))
print(f"replay: {len(rows)} answers from {len({r for r, _ in rows})} runs")

blocked = []
with_amounts = 0
for run, r in rows:
    if g._amounts(r["answer"]):
        with_amounts += 1
    res = g.main(r["answer"], r["retrieved_text"])
    if res["verdict"] == "block":
        blocked.append((run, r["query_id"], r["repeat"], res["bad"]))
print(f"answers that contain an amount: {with_amounts}")
print(f"would be blocked: {len(blocked)}")
for b in blocked:
    print("  ", *b)

# injection test
WRONG = ["2", "2,000", "2,500,000", "50,000", "12,000", "999,999"]
tests = fails = 0
for run, r in rows:
    if g.main(r["answer"], r["retrieved_text"])["verdict"] != "pass":
        continue
    amts = re.findall(r"[₩¥￥]\s?\d[\d,]*", r["answer"])
    if not amts:
        continue
    target = amts[0]
    sym = target[0]
    for w in WRONG:
        if w.replace(",", "") in g._amounts(r["retrieved_text"]):
            continue  # the "wrong" value happens to be a real one for this answer
        bad_answer = r["answer"].replace(target, f"{sym}{w}", 1)
        tests += 1
        if g.main(bad_answer, r["retrieved_text"])["verdict"] != "block":
            fails += 1
            print("  NOT BLOCKED:", run, r["query_id"], r["repeat"], target, "->", sym + w)
print(f"injection: {tests} wrong-amount variants, {fails} not blocked")
