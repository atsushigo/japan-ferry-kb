"""Draw the threshold-calibration chart from the automated recall runs (run-002 + run-003).

Usage:  python make_calibration_chart.py [run_dir ...]
Default runs: evaluation/runs/run-002_2026-11-21 and run-003_2026-11-21
Needs:  matplotlib and a CJK font (see make_retrieval_chart.py).

Reads labeled_results.csv (written by evaluation/score_run.py) and evaluation/questions.csv.
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
RUNS = [Path(p) for p in sys.argv[1:]] or [ROOT / "evaluation/runs/run-002_2026-11-21",
                                           ROOT / "evaluation/runs/run-003_2026-11-21"]
PNG = HERE / "threshold-calibration.png"
CHOSEN = 0.71

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
ACCENT, GRAY, BAND = "#2a78d6", "#898781", "#e6eefa"

for p in ("/mnt/c/Windows/Fonts/msjh.ttc", "/mnt/c/Windows/Fonts/msjhbd.ttc", "C:/Windows/Fonts/msjh.ttc",
          "C:/Windows/Fonts/msjhbd.ttc", "/System/Library/Fonts/PingFang.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
    if Path(p).exists():
        font_manager.fontManager.addfont(p)
installed = {f.name for f in font_manager.fontManager.ttflist}
for name in ("Microsoft JhengHei", "PingFang TC", "Noto Sans CJK TC", "Noto Sans TC", "Noto Sans JP"):
    if name in installed:
        plt.rcParams["font.family"] = name
        break
plt.rcParams["axes.unicode_minus"] = False

questions = {q["id"]: q for q in csv.DictReader(open(ROOT / "evaluation/questions.csv", encoding="utf-8"))}
rows = []
for run in RUNS:
    rows += list(csv.DictReader(open(run / "labeled_results.csv", encoding="utf-8")))
for r in rows:
    r["s"] = float(r["score"])

order = []
for r in rows:
    if r["query_id"] not in order:
        order.append(r["query_id"])
in_scope = [q for q in order if questions[q]["expect_empty"] != "yes"]
oos = [q for q in order if questions[q]["expect_empty"] == "yes"]
rows_order = in_scope + oos
n = len(rows_order)
ypos = {q: n - i - (0.7 if q in oos else 0) for i, q in enumerate(rows_order)}   # gap between the groups

rel_scores = [r["s"] for r in rows if r["label"] == "relevant"]
oos_scores = [r["s"] for r in rows if r["query_id"] in oos]
rel_min, oos_max = min(rel_scores), max(oos_scores)
rel_min_q = next(r["query_id"] for r in rows if r["label"] == "relevant" and r["s"] == rel_min)
oos_max_q = next(r["query_id"] for r in rows if r["query_id"] in oos and r["s"] == oos_max)

fig, ax = plt.subplots(figsize=(10.5, 9.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.axvspan(oos_max, rel_min, color=BAND, zorder=0)
ax.axvline(CHOSEN, color=INK2, lw=1.4, ls=(0, (5, 3)), zorder=1)
ax.text(CHOSEN, n + 0.85, f"建議閾值 {CHOSEN}", ha="center", va="bottom", color=INK, fontsize=10.5, fontweight="bold")

for label, mk, face, edge, size in (("off_topic", "o", SURFACE, GRAY, 70), ("relevant", "o", ACCENT, SURFACE, 100)):
    pts = [r for r in rows if r["label"] == label]
    ax.scatter([r["s"] for r in pts], [ypos[r["query_id"]] for r in pts], marker=mk, s=size,
               facecolor=face, edgecolor=edge, linewidth=1.6 if label == "off_topic" else 2, zorder=3)

ax.set_yticks([ypos[q] for q in rows_order])
def short(t, k=19):
    return t if len(t) <= k else t[:k] + "…"


ax.set_yticklabels([f"{q}  {short(questions[q]['query'])}" for q in rows_order], color=INK, fontsize=9)
ax.tick_params(axis="y", length=0)
ax.set_xlim(0.54, 0.84)
ax.set_ylim(0.2, n + 1.5)
ax.set_xticks([0.55, 0.60, 0.65, 0.70, 0.75, 0.80])
ax.tick_params(axis="x", colors=INK2, labelsize=9.5)
ax.set_xlabel("向量相似度分數（Dify 知識庫 API，gemini-embedding-2，v3 文件）", color=INK2, fontsize=10, labelpad=8)
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)

split = (ypos[in_scope[-1]] + ypos[oos[0]]) / 2
ax.axhline(split, color=GRID, lw=1)
ax.text(0.545, split + 0.45, "庫內題", color=INK2, fontsize=9, va="bottom")
ax.text(0.545, split - 0.45, "庫外題（應為空）", color=INK2, fontsize=9, va="top")

ax.annotate(f"庫外題最高分 {oos_max:.4f}\n（{oos_max_q}：{short(questions[oos_max_q]['query'], 11)}）",
            xy=(oos_max, ypos[oos_max_q]), xytext=(0.735, ypos[oos_max_q] + 0.55), color=INK, fontsize=9,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8, shrinkB=5))
ax.annotate(f"相關段落最低分 {rel_min:.4f}\n（{rel_min_q}：{short(questions[rel_min_q]['query'], 11)}）",
            xy=(rel_min, ypos[rel_min_q]), xytext=(0.765, ypos[rel_min_q] - 1.6), color=INK, fontsize=9, ha="left",
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8, shrinkB=5))

fig.text(0.015, 0.975, "閾值只有一個很窄的安全區間", color=INK, fontsize=14, fontweight="bold", ha="left", va="top")
fig.text(0.015, 0.948, f"需高於所有庫外題（最高 {oos_max:.4f}），又要低於所有相關段落（最低 {rel_min:.4f}）；"
         "每題顯示前 5 名。相關性依 questions.csv 的預期段落自動判定。", color=INK2, fontsize=9.5, ha="left", va="top")
handles = [plt.Line2D([], [], marker="o", ls="", markersize=9, markerfacecolor=ACCENT, markeredgecolor=SURFACE,
                      markeredgewidth=1.6, label="相關段落（含答案）"),
           plt.Line2D([], [], marker="o", ls="", markersize=8, markerfacecolor=SURFACE, markeredgecolor=GRAY,
                      markeredgewidth=1.6, label="不相關段落"),
           plt.Rectangle((0, 0), 1, 1, facecolor=BAND, edgecolor="none", label=f"安全區間（寬 {rel_min - oos_max:.3f}）")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.06), ncol=3, frameon=False,
          fontsize=9.5, labelcolor=INK2)
fig.subplots_adjust(left=0.29, right=0.97, top=0.91, bottom=0.1)
fig.savefig(PNG, facecolor=SURFACE)
print("saved", PNG, "| oos_max", oos_max, "rel_min", rel_min)
