"""Draw the retrieval-score chart from the run-001 results.csv.

Usage:  python make_retrieval_chart.py [csv_path] [png_path]
Needs:  matplotlib (pip install matplotlib) and any CJK font
        (Noto Sans TC / Noto Sans CJK TC / Microsoft JhengHei / Noto Sans JP).
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evaluation/runs/run-001_2026-11-21/results.csv"
PNG_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "retrieval-scores.png"
THRESHOLD = 0.72

# --- design tokens (light surface) ---------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
ACCENT = "#2a78d6"      # relevant chunk (the one thing the reader looks for)
GRAY = "#898781"        # everything else is deliberately de-emphasised
GRAY_LIGHT = "#c9c8c3"

# --- font -----------------------------------------------------------------
for p in ("/mnt/c/Windows/Fonts/msjh.ttc", "/mnt/c/Windows/Fonts/msjhbd.ttc",      # WSL
          "C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjhbd.ttc",              # Windows
          "/System/Library/Fonts/PingFang.ttc",                                    # macOS
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):               # Linux
    if Path(p).exists():
        font_manager.fontManager.addfont(p)
installed = {f.name for f in font_manager.fontManager.ttflist}
for name in ("Microsoft JhengHei", "PingFang TC", "Noto Sans CJK TC", "Noto Sans TC",
             "Noto Sans JP", "Yu Gothic"):
    if name in installed:
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

# --- data -----------------------------------------------------------------
rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
queries = []
for r in rows:
    if r["query_id"] not in [q[0] for q in queries]:
        queries.append((r["query_id"], r["query"], r["query_type"]))

TAG = {"no_answer_in_kb": "（庫內無答案）", "out_of_scope": "（庫外題）", "in_scope": ""}
STYLE = {  # label -> (marker, face, edge, size, legend text)
    "relevant":  ("o", ACCENT, SURFACE, 120, "相關段落（含答案）"),
    "meta":      ("D", GRAY, SURFACE, 80, "結構性段落（檔頭／標題，無答案內容）"),
    "off_topic": ("o", SURFACE, GRAY, 100, "不相關段落（鄰近或無關主題）"),
}

fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

n = len(queries)
ypos = {q[0]: n - i for i, q in enumerate(queries)}   # Q1 on top

ax.axvspan(0.56, THRESHOLD, color="#f1f0ec", zorder=0)
ax.axvline(THRESHOLD, color=INK2, lw=1.4, ls=(0, (5, 3)), zorder=1)
ax.text(THRESHOLD + 0.002, n + 0.62, f"閾值 {THRESHOLD}", color=INK2, fontsize=9.5,
        va="center", ha="left")
ax.text(THRESHOLD - 0.002, n + 0.62, "低於閾值：被過濾", color=INK2, fontsize=9.5,
        va="center", ha="right")

# jitter points that share (query, score) so none is hidden
seen = {}
for r in rows:
    key = (r["query_id"], r["score"])
    k = seen.get(key, 0)
    seen[key] = k + 1
    r["_dy"] = (k - 0.5) * 0.22 if sum(1 for x in rows if (x["query_id"], x["score"]) == key) > 1 else 0

for label in ("off_topic", "meta", "relevant"):      # relevant drawn last = on top
    mk, face, edge, size, _ = STYLE[label]
    pts = [r for r in rows if r["label"] == label]
    ax.scatter([float(r["score"]) for r in pts],
               [ypos[r["query_id"]] + r["_dy"] for r in pts],
               marker=mk, s=size, facecolor=face, edgecolor=edge,
               linewidth=2 if label != "off_topic" else 1.6, zorder=3)

# row labels
ax.set_yticks([ypos[q[0]] for q in queries])
ax.set_yticklabels([f"{q[0]}  {q[1]}{TAG[q[2]]}" for q in queries], color=INK, fontsize=10)
ax.tick_params(axis="y", length=0)

ax.set_xlim(0.58, 0.89)
ax.set_ylim(0.4, n + 1.0)
ax.set_xticks([0.60, 0.65, 0.70, 0.75, 0.80, 0.85])
ax.tick_params(axis="x", colors=INK2, labelsize=9.5)
ax.set_xlabel("向量相似度分數（Dify 召回測試，gemini-embedding-2）", color=INK2, fontsize=10, labelpad=8)
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)

# selective direct labels (three findings, not a number on every point)
def note(qid, score, text, dx, dy, ha="left"):
    ax.annotate(text, xy=(score, ypos[qid]), xytext=(score + dx, ypos[qid] + dy),
                color=INK, fontsize=9, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8, shrinkA=0, shrinkB=6))

note("Q7", 0.73, "相關段落中的最低分 0.73", 0.045, 0.0)
note("Q3", 0.72, "鄰近主題最高分 0.72", -0.13, 0.42)
note("Q8", 0.70, "庫外題的最高分 0.70", 0.045, 0.0)
note("Q1", 0.80, "結構性段落同為 0.80", 0.014, 0.0)

# title + legend
fig.text(0.015, 0.965, "檢索分數分不開「結構性段落」，但能擋住「庫外題」", color=INK,
         fontsize=14, fontweight="bold", ha="left", va="top")
fig.text(0.015, 0.915, "8 題向量檢索的前 3～5 名段落；標籤為人工判讀。結構性段落（檔頭／標題）最高可達 0.80，"
         "只能靠改文件結構排除，不能靠閾值。", color=INK2, fontsize=9.5, ha="left", va="top")

handles = [plt.Line2D([], [], marker=s[0], ls="", markersize=9 if s[0] == "o" else 7.5,
                      markerfacecolor=s[1], markeredgecolor=(s[2] if s[1] != SURFACE else GRAY),
                      markeredgewidth=1.6, label=s[4]) for s in STYLE.values()]
leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.12), ncol=3,
                frameon=False, fontsize=9.2, labelcolor=INK2, handletextpad=0.4, columnspacing=1.6)

fig.subplots_adjust(left=0.30, right=0.97, top=0.85, bottom=0.2)
fig.savefig(PNG_PATH, facecolor=SURFACE)
print("saved", PNG_PATH)
