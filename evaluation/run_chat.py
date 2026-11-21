#!/usr/bin/env python3
"""Run the answer-level test: send each question to the published Dify chat app and store the answers.

Reads chatbot/test-conversations.csv, calls  POST {base}/chat-messages  (blocking mode, a fresh
conversation per request) and writes an immutable run folder:

    evaluation/chat_runs/<name>_<YYYY-MM-DD>/
        config.json   what was tested (model label, prompt version, git commit, hashes)
        results.csv   one row per (question, repeat): answer, retrieved chunks, tokens, price, latency

Why repeats: Gemini 3 models expose no temperature setting, so the same question can give different
answers (FKB-007). One preview proves little; use --repeat.

Configuration (environment or .env in the repo root, never committed):
    DIFY_BASE_URL        default https://api.dify.ai/v1
    DIFY_APP_API_KEY     the chat APP key (not the knowledge-base key)

The model name is not returned by the API, so pass it with --model (it is only a label stored in
config.json; the real model is whatever the Dify app is set to at that moment).

Examples:
    python3 evaluation/run_chat.py --name chat-001 --model gemini-3.5-flash-lite --prompt-version v2 --dry-run
    python3 evaluation/run_chat.py --name chat-001 --model gemini-3.5-flash-lite --prompt-version v2 --repeat 3
    python3 evaluation/run_chat.py --name chat-002 --ids A1,A13 --repeat 10 --model gemini-3.5-flash-lite --prompt-version v2
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["query_id", "repeat", "language", "query", "answer", "n_retrieved", "retrieved_scores",
          "retrieved_docs", "retrieved_text", "total_tokens", "total_price_usd", "latency_s", "error"]
QUOTA_MARKERS = ("quota", "exceeded your current quota", "rate limit", "rate_limit", "429")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def git_info() -> dict:
    def run(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    try:
        return {"commit": run("rev-parse", "--short", "HEAD") or None,
                "dirty": bool(run("status", "--porcelain", "knowledge", "chatbot"))}
    except OSError:
        return {"commit": None, "dirty": None}


def ask(base: str, key: str, query: str, timeout: int = 120):
    body = json.dumps({"inputs": {}, "query": query, "response_mode": "blocking",
                       "conversation_id": "", "user": "eval-runner"}).encode("utf-8")
    req = urllib.request.Request(f"{base}/chat-messages", data=body, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), time.time() - t0, ""
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}"
    except urllib.error.URLError as e:
        return None, time.time() - t0, f"network: {e.reason}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--questions", default=str(ROOT / "chatbot" / "test-conversations.csv"))
    ap.add_argument("--ids", default="", help="comma-separated ids, e.g. A1,A13 (default: all)")
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--delay", type=float, default=5.0,
                    help="seconds between requests (free tier: 15 requests/min on Flash-Lite, 5 on 3.8 Flash -> use 13)")
    ap.add_argument("--model", default="unspecified", help="label only; the Dify app decides the real model")
    ap.add_argument("--prompt-version", default="unspecified")
    ap.add_argument("--note", default="")
    ap.add_argument("--out-root", default=str(ROOT / "evaluation" / "chat_runs"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    load_dotenv(ROOT / ".env")
    base = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
    key = os.environ.get("DIFY_APP_API_KEY", "")

    qs = list(csv.DictReader(open(a.questions, encoding="utf-8", newline="")))
    if a.ids:
        want = [x.strip() for x in a.ids.split(",") if x.strip()]
        qs = [q for q in qs if q["id"] in want]
    if not qs:
        raise SystemExit("no questions selected")
    total = len(qs) * a.repeat
    if a.dry_run:
        for q in qs:
            print(f"{q['id']} x{a.repeat}: {q['query']}")
        print(f"\n{total} requests, about {total * a.delay / 60:.1f} min at {a.delay}s spacing -> {base}/chat-messages")
        return
    if not key:
        raise SystemExit("set DIFY_APP_API_KEY in .env (the chat app key, see .env.example)")

    out = Path(a.out_root) / f"{a.name}_{date.today().isoformat()}"
    if out.exists():
        raise SystemExit(f"{out} already exists; runs are immutable, pick another --name")

    rows, n = [], 0
    stop_reason = ""
    for q in qs:
        for rep in range(1, a.repeat + 1):
            n += 1
            resp, dt, err = ask(base, key, q["query"])
            row = {"query_id": q["id"], "repeat": rep, "language": q.get("language", ""), "query": q["query"],
                   "answer": "", "n_retrieved": "", "retrieved_scores": "", "retrieved_docs": "",
                   "retrieved_text": "", "total_tokens": "", "total_price_usd": "",
                   "latency_s": round(dt, 2), "error": err}
            if resp is not None:
                meta = resp.get("metadata") or {}
                res = meta.get("retriever_resources") or []
                usage = meta.get("usage") or {}
                row.update({
                    "answer": resp.get("answer", ""),
                    "n_retrieved": len(res),
                    "retrieved_scores": ";".join(str(round(float(r.get("score") or 0), 4)) for r in res),
                    "retrieved_docs": ";".join(f"{r.get('document_name','')}#{r.get('position','')}" for r in res),
                    "retrieved_text": "\n<<<chunk>>>\n".join((r.get("content") or "") for r in res),
                    "total_tokens": usage.get("total_tokens", ""),
                    "total_price_usd": usage.get("total_price", ""),
                })
            rows.append(row)
            status = "ERROR" if err else f"{row['n_retrieved']} chunks, {row['total_tokens']} tokens"
            print(f"[{n}/{total}] {q['id']} #{rep}: {status} ({dt:.1f}s)", flush=True)
            if err and any(m in err.lower() for m in QUOTA_MARKERS):
                stop_reason = f"stopped at {q['id']} #{rep}: quota or rate limit ({err[:120]})"
                break
            if err and err.startswith("HTTP 401"):
                stop_reason = "stopped: HTTP 401, check DIFY_APP_API_KEY"
                break
            time.sleep(a.delay)
        if stop_reason:
            break

    out.mkdir(parents=True)
    with open(out / "results.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    config = {
        "run": a.name, "date": date.today().isoformat(), "note": a.note,
        "model_label": a.model, "prompt_version": a.prompt_version,
        "git": git_info(), "repeat": a.repeat, "delay_s": a.delay,
        "questions_file": os.path.relpath(a.questions, ROOT), "questions_sha256": sha256(Path(a.questions)),
        "questions_run": [q["id"] for q in qs],
        "knowledge_files": {p.name: sha256(p) for p in sorted((ROOT / "knowledge").glob("*.md"))},
        "completed_requests": len(rows), "planned_requests": total, "stopped_early": stop_reason or None,
    }
    (out / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out}/results.csv ({len(rows)} rows) and config.json")
    if stop_reason:
        print(stop_reason, file=sys.stderr)


if __name__ == "__main__":
    main()
