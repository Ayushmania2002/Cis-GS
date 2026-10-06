"""
Performance figure for the manuscript (Arachis hypogaea Tifrunner genome only).
Reads the JSON/log files written by the WSL2 benchmark harness (benchmark_out/arachis_*).
Panels: A extraction, B motif scan, C co-expression pipeline, D parallel scan scaling.
"""
import json, re, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

OUT = Path("benchmark_out")
_avail = {f.name for f in fm.fontManager.ttflist}
plt.rcParams.update({"font.family": "Arial" if "Arial" in _avail else "DejaVu Sans",
                     "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "svg.fonttype": "none"})

res = {r["label"]: r for r in json.load(open(OUT / "arachis_compare_results.json"))}
new = {r["label"]: r for r in json.load(open(OUT / "arachis_compare_results_v1324.json"))}   # indexed-extraction build
scal = json.load(open(OUT / "arachis_stress_scaling.json"))
runs = [json.loads(l[7:]) for l in open(OUT / "arachis_coexpr_runs.log") if l.startswith("RESULT ")]

C_CIS, C_OTH, C_OLD = "#0072B2", "#8c8c8c", "#D55E00"

fig, axs = plt.subplots(2, 2, figsize=(14, 10.5))

# ---- A: promoter extraction ----
ax = axs[0, 0]
bed = res["bed generation (awk)"]["wall_mean"]
items = [("Cis-GS\nextract", new["Cis-GS extract"], 0, C_CIS),
         ("bedtools\ngetfasta", res["bedtools getfasta"], bed, C_OTH),
         ("seqkit\nsubseq", res["seqkit subseq"], bed, C_OTH),
         ("pyfaidx\nloop", res["pyfaidx loop"], bed, C_OTH)]
# CPU time is plotted (stable under page-cache variation); wall time is annotated.
vals = [r["cpu_mean"] + extra for _, r, extra, _ in items]
ax.bar(range(len(items)), vals, color=[c for *_, c in items])
for i, (_, r, extra, _) in enumerate(items):
    ax.text(i, vals[i] * 1.12, f"{vals[i]:.1f} s CPU\n{r['peak_mb']:.0f} MB peak", ha="center", va="bottom", fontsize=11)
ax.set_yscale("log"); ax.set_ylim(0.5, 400)
ax.set_xticks(range(len(items))); ax.set_xticklabels([n for n, *_ in items], fontsize=11)
ax.set_ylabel("CPU time (s, log scale)")
ax.set_title("A  Promoter extraction (106,608 genes, 2 kb)", loc="left", fontweight="bold")

# ---- B: motif scan ----
ax = axs[0, 1]
seq_total = res["seqkit locate -d (CYC-RE_RAM1)"]["wall_mean"] + res["seqkit locate -d (CYC-RE_NIN)"]["wall_mean"]
items = [("Cis-GS\nsearch", new["Cis-GS search (2 motifs, incl. p-values)"]["wall_mean"], new["Cis-GS search (2 motifs, incl. p-values)"]["wall_sd"], C_CIS, 639),
         ("seqkit locate\n(2 runs)", seq_total, 0.2, C_OTH, 61),
         ("FIMO\n(PWM, p<=1e-4)", res["FIMO (2 motifs, p<=1e-4)"]["wall_mean"], res["FIMO (2 motifs, p<=1e-4)"]["wall_sd"], C_OTH, 44)]
ax.bar(range(3), [v for _, v, *_ in items], yerr=[s for _, _, s, *_ in items], color=[c for *_, c, _ in items], capsize=4)
for i, (_, v, _, _, mb) in enumerate(items):
    ax.text(i, v + 2, f"{v:.1f} s\n{mb} MB", ha="center", va="bottom", fontsize=11)
ax.set_ylim(0, 90)
ax.set_xticks(range(3)); ax.set_xticklabels([n for n, *_ in items])
ax.set_ylabel("Wall time (s)")
ax.set_title("B  Motif scan, CYC-RE_RAM1 + CYC-RE_NIN", loc="left", fontweight="bold")
ax.text(0.98, 0.95, "Cis-GS and seqkit: identical 161 hits\nFIMO: 25,774 hits (PWM, not exact-match)",
        transform=ax.transAxes, ha="right", va="top", fontsize=10.5, color="#444")

# ---- C: co-expression pipeline (current igraph backend only) ----
ax = axs[1, 0]
rr = [r for r in runs if r["variant"] == "igraph"]
mean = lambda k: st.mean(r["stages"][k] for r in rr)
stage_rows = [("Load + filter + log2", mean("load") + mean("filter_topvar") + mean("log2"), "#bbbbbb"),
              ("Pearson correlation", mean("pearson"), "#56B4E9"),
              ("Graph + Louvain (igraph)", mean("graph_louvain"), "#D55E00"),
              ("K-means elbow (k = 2-15)", mean("elbow_k2_15"), "#009E73"),
              ("Final K-means", mean("kmeans_final"), "#CC79A7")]
total = sum(v for _, v, _ in stage_rows)
ypos = list(range(len(stage_rows)))[::-1]
ax.barh(ypos, [v for _, v, _ in stage_rows], color=[c for *_, c in stage_rows], height=0.6)
for y, (_, v, _) in zip(ypos, stage_rows):
    ax.text(v + 0.08, y, f"{v:.1f} s", va="center", fontsize=11)
ax.set_yticks(ypos); ax.set_yticklabels([n for n, *_ in stage_rows])
ax.set_xlim(0, 5.6); ax.set_xlabel("Wall time (s)")
ax.set_title("C  Co-expression pipeline (5,000 genes x 54 samples)", loc="left", fontweight="bold")
ax.text(0.97, 0.115, f"Total {total:.1f} s, peak RAM {max(r['peak_mb'] for r in rr)/1000:.1f} GB" + chr(10) +
        f"{rr[0]['edges']:,} edges (|r| >= 0.70), {rr[0]['modules']} modules",
        transform=ax.transAxes, ha="right", fontsize=11, color="#444")
ax.text(0.97, 0.045, "PlantPAN 4.0 (web server, precomputed networks): not timed",
        transform=ax.transAxes, ha="right", fontsize=9.5, color="#666", style="italic")

# ---- D: parallel scan scaling (prototype) ----
ax = axs[1, 1]
for lab, c, mk in (("CYC-RE_RAM1 + CYC-RE_NIN", C_CIS, "o"), ("GGATT (short, common motif)", C_OLD, "s")):
    d = scal["scaling"]["CYC-RE x2 motifs" if lab.startswith("CYC") else "GGATT"]
    w = sorted(int(k) for k in d)
    sp = [d["1"]["wall"] / d[str(k)]["wall"] for k in w]
    ax.plot(w, sp, marker=mk, color=c, lw=2.2, ms=8, label=lab)
ax.plot([1, 16], [1, 16], ls="--", color="#999", lw=1.2, label="Ideal")
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.set_xticks([1, 2, 4, 8, 16]); ax.set_xticklabels([1, 2, 4, 8, 16])
ax.set_yticks([1, 2, 4, 8, 16]); ax.set_yticklabels([1, 2, 4, 8, 16])
ax.set_xlabel("Worker processes"); ax.set_ylabel("Speed-up vs 1 worker")
ax.legend(frameon=False, fontsize=11, loc="upper left")
ax.set_title("D  Motif-scan scaling (multiprocessing prototype)", loc="left", fontweight="bold")

fig.tight_layout()
fig.savefig(OUT / "arachis_performance_figure.png", dpi=300, facecolor="white")
fig.savefig(OUT / "arachis_performance_figure.svg", facecolor="white")
print("saved")
