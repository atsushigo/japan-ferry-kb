#!/usr/bin/env python3
"""Run the recall (retrieval) test against a Dify knowledge base through the Knowledge API.

Reads the questions CSV, calls  POST {base}/datasets/{id}/retrieve  once per question and
writes an immutable run folder:

    evaluation/runs/<name>_<YYYY-MM-DD>/
        config.json   what was tested (git commit, settings, hashes of the knowledge files)
        results.csv   one row per returned chunk (score, document, section title, ...)

Only the Python standard library is used.

Configuration (environment variables or a .env file in the repo root, never committed):
    DIFY_BASE_URL         default https://api.dify.ai/v1
    DIFY_KB_API_KEY       knowledge-base API key (NOT an app key)
    DIFY_DATASET_ID       UUID of the knowledge base (it is in the knowledge base page URL)

Examples:
    python evaluation/run_recall.py --name run-002 --dry-run
    python evaluation/run_recall.py --name run-002 --top-k 5 --note "v3 docs, threshold off"
    python evaluation/run_recall.py --name run-003 --threshold 0.72 --runs-filter run2
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
RATE_LIMIT_WAIT = 65  # seconds; the Sandbox plan allows roughly 10 knowledge requests per minute
RESULT_FIELDS = ["query_id", "query", "language", "rank", "score", "document",
                 "segment_position", "segment_id", "section_title", "top_k", "score_threshold"]


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
    def run(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    try:
        return {"commit": run("rev-parse", "--short", "HEAD") or None,
                "dirty": bool(run("status", "--porcelain", "knowledge"))}
    except OSError:
        return {"commit": None, "dirty": None}


def build_body(query: str, top_k: int, threshold, method: str) -> dict:
    return {
        "query": query,
        "retrieval_model": {
            "search_method": method,
            "reranking_enable": False,
            "top_k": top_k,
            "score_threshold_enabled": threshold is not None,
            "score_threshold": threshold,
        },
    }


def call_api(url: str, key: str, body: dict, retries: int = 3) -> dict:
    data = json.dumps(body).encode("utf-8")
    for attempt in range(1, retries + 3):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code == 403 and "rate limit" in detail.lower() and attempt < retries + 2:
                print(f"  rate limit reached, waiting {RATE_LIMIT_WAIT}s then retrying ...", flush=True)
                time.sleep(RATE_LIMIT_WAIT)
                continue
            if e.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise SystemExit(f"HTTP {e.code} from Dify: {detail}")
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(2 * attempt)
                continue
            raise SystemExit(f"Network error: {e.reason}")
    raise SystemExit("unreachable")


def section_title(content: str) -> str:
    for line in (content or "").splitlines():
        line = line.strip()
        if line:
            return line.lstrip("#").strip()
    return ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="run name, e.g. run-002")
    ap.add_argument("--questions", default=str(ROOT / "evaluation" / "questions.csv"))
    ap.add_argument("--runs-filter", default="run2",
                    help="only questions whose recall_runs column contains this text ('' = all)")
    ap.add_argument("--ids", default="", help="comma-separated question ids to run, e.g. Q1,Q8 (overrides --runs-filter)")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=None,
                    help="score threshold; omit to disable filtering (full score distribution)")
    ap.add_argument("--search-method", default="semantic_search",
                    choices=["semantic_search", "full_text_search", "hybrid_search", "keyword_search"])
    ap.add_argument("--out-root", default=str(ROOT / "evaluation" / "runs"))
    ap.add_argument("--note", default="", help="free text stored in config.json")
    ap.add_argument("--delay", type=float, default=6.5,
                    help="seconds between requests (6.5 keeps the Sandbox plan under 10 requests/minute)")
    ap.add_argument("--dry-run", action="store_true", help="print the requests, call nothing")
    a = ap.parse_args()

    load_dotenv(ROOT / ".env")
    base = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
    key = os.environ.get("DIFY_KB_API_KEY", "")
    dataset = os.environ.get("DIFY_DATASET_ID", "")

    with open(a.questions, encoding="utf-8", newline="") as f:
        questions = list(csv.DictReader(f))
    if a.ids:
        wanted = [x.strip() for x in a.ids.split(",") if x.strip()]
        questions = [q for q in questions if q["id"] in wanted]
    elif a.runs_filter:
        questions = [q for q in questions if a.runs_filter in q.get("recall_runs", "")]
    if not questions:
        raise SystemExit("no questions selected")
    too_long = [q["id"] for q in questions if len(q["query"]) > 250]
    if too_long:
        raise SystemExit(f"query longer than the API limit (250): {too_long}")

    if a.dry_run:
        for q in questions:
            print(json.dumps({"id": q["id"], **build_body(q["query"], a.top_k, a.threshold, a.search_method)},
                             ensure_ascii=False))
        print(f"\n{len(questions)} requests would be sent to {base}/datasets/<id>/retrieve")
        return
    if not key or not dataset:
        raise SystemExit("set DIFY_KB_API_KEY and DIFY_DATASET_ID (environment or .env); see .env.example")

    out = Path(a.out_root) / f"{a.name}_{date.today().isoformat()}"
    if out.exists():
        raise SystemExit(f"{out} already exists; runs are immutable, pick another --name")

    url = f"{base}/datasets/{dataset}/retrieve"
    rows = []

    def save_partial():
        if rows:
            part = Path(a.out_root) / f"{a.name}_{date.today().isoformat()}.partial.csv"
            part.parent.mkdir(parents=True, exist_ok=True)
            with open(part, "w", encoding="utf-8", newline="") as pf:
                pw = csv.DictWriter(pf, fieldnames=RESULT_FIELDS, lineterminator="\n")
                pw.writeheader(); pw.writerows(rows)
            print(f"partial results saved to {part}", file=sys.stderr)

    for i, q in enumerate(questions, 1):
        try:
            resp = call_api(url, key, build_body(q["query"], a.top_k, a.threshold, a.search_method))
        except SystemExit:
            save_partial()
            raise
        records = resp.get("records") or []
        print(f"[{i}/{len(questions)}] {q['id']}: {len(records)} chunk(s)")
        common = {"query_id": q["id"], "query": q["query"], "language": q.get("language", ""),
                  "top_k": a.top_k, "score_threshold": "" if a.threshold is None else a.threshold}
        if not records:
            rows.append({**common, "rank": "", "score": "", "document": "", "segment_position": "",
                         "segment_id": "", "section_title": "(no results)"})
        for rank, rec in enumerate(records, 1):
            seg = rec.get("segment") or {}
            doc = seg.get("document") or {}
            score = rec.get("score")
            rows.append({**common, "rank": rank, "score": "" if score is None else round(float(score), 4),
                         "document": doc.get("name", ""), "segment_position": seg.get("position", ""),
                         "segment_id": seg.get("id", ""), "section_title": section_title(seg.get("content", ""))})
        time.sleep(a.delay)

    out.mkdir(parents=True)  # created only after every request succeeded, so a failed run leaves nothing behind
    with open(out / "results.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    kdir = ROOT / "knowledge"
    config = {
        "run": a.name, "date": date.today().isoformat(), "note": a.note,
        "git": git_info(),
        "api": {"base_url": base, "search_method": a.search_method, "top_k": a.top_k,
                "score_threshold": a.threshold, "reranking_enable": False},
        "questions_file": os.path.relpath(a.questions, ROOT),
        "questions_sha256": sha256(Path(a.questions)),
        "questions_run": [q["id"] for q in questions],
        "knowledge_files": {p.name: sha256(p) for p in sorted(kdir.glob("*.md"))},
    }
    (out / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out}/results.csv ({len(rows)} rows) and config.json")


if __name__ == "__main__":
    main()
