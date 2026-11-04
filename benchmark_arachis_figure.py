"""
Performance figure for the manuscript (Arachis hypogaea Tifrunner genome only).
Reads the raw run files written by the WSL2 benchmark harness (benchmark_out/arachis_final_*):
one untimed warm-up run followed by three timed runs per measurement, every individual run stored.
Panels: A extraction, B motif scan, C co-expression pipeline, D parallel scan scaling (prototype).
"""
import json, re, statistics as st
from math import sqrt
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

res = {r["label"]: r for r in json.load(open(OUT / "arachis_final_results.json"))}
scal = json.load(open(OUT / "arachis_final_scaling.json"))
runs = []
for line in open(OUT / "arachis_final_coexpr_runs.log"):
    m = re.match(r"RESULT run=(\d+) (\{.*\})", line)
    if m and int(m.group(1)) >= 1:            # run 0 is the discarded warm-up
        runs.append(json.loads(m.group(2)))

C_CIS, C_CIS2, C_OTH, C_OLD = "#0072B2", "#56A0D3", "#8c8c8c", "#D55E00"

fig, axs = plt.subplots(2, 2, figsize=(14, 10.5))

# ---- A: promoter extraction (wall time and CPU time; reference tools also need a BED file) ----
ax = axs[0, 0]
bed_wall, bed_cpu = res["bed generation (awk)"]["wall_mean"], res["bed generation (awk)"]["cpu_mean"]
items = [("Cis-GS\n(index present)", res["Cis-GS extract"], False, C_CIS, "#9CC9E6"),
         ("Cis-GS\n(builds index)", res["Cis-GS extract (no .fai, index built in memory)"], False, C_CIS2, "#CFE3F2"),
         ("bedtools\ngetfasta", res["bedtools getfasta"], True, "#6b6b6b", "#c4c4c4"),
         ("seqkit\nsubseq", res["seqkit subseq"], True, "#6b6b6b", "#c4c4c4"),
         ("pyfaidx\nloop", res["pyfaidx loop"], True, "#6b6b6b", "#c4c4c4")]
wd = 0.38
for i, (name, r, add_bed, c_wall, c_cpu) in enumerate(items):
    wall = r["wall_mean"] + (bed_wall if add_bed else 0); cpu = r["cpu_mean"] + (bed_cpu if add_bed else 0)
    ax.bar(i - wd / 2, wall, wd, yerr=r["wall_sd"], color=c_wall, capsize=3, error_kw={"lw": 1})
    ax.bar(i + wd / 2, cpu, wd, yerr=r["cpu_sd"], color=c_cpu, hatch="///", edgecolor="#555", linewidth=0.6, capsize=3, error_kw={"lw": 1})
    ax.text(i - wd / 2, (wall + r["wall_sd"]) * 1.12, f"{wall:.1f}", ha="center", va="bottom", fontsize=10)
    ax.text(i + wd / 2, (cpu + r["cpu_sd"]) * 1.12, f"{cpu:.1f}", ha="center", va="bottom", fontsize=10)
ax.set_yscale("log"); ax.set_ylim(0.5, 60)
ax.set_xticks(range(len(items)))
ax.set_xticklabels([f"{n}\n{r['peak_mib']:.0f} MiB" for n, r, *_ in items], fontsize=10)
ax.set_ylabel("Time (s, log scale)")
ax.set_title("A  Promoter extraction (106,608 genes, 2 kb)", loc="left", fontweight="bold")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor="#6b6b6b", label="Wall time"), Patch(facecolor="#c4c4c4", hatch="///", edgecolor="#555", label="CPU time")],
          frameon=False, fontsize=10, loc="upper right")
ax.text(0.99, 0.80, "bedtools, seqkit, pyfaidx: + 1.4 s to make a BED file\nPeak memory (MiB) under each tool name", transform=ax.transAxes,
        ha="right", va="top", fontsize=9, color="#555")

# ---- B: motif scan (wall time) ----
ax = axs[0, 1]
r1, r2 = res["seqkit locate -d (CYC-RE_RAM1)"], res["seqkit locate -d (CYC-RE_NIN)"]
cs, fm_ = res["Cis-GS search (2 motifs, incl. p-values)"], res["FIMO (2 motifs, p<=1e-4)"]
items = [("Cis-GS\nsearch", cs["wall_mean"], cs["wall_sd"], C_CIS, cs["peak_mib"]),
         ("seqkit locate\n(2 runs)", r1["wall_mean"] + r2["wall_mean"], sqrt(r1["wall_sd"] ** 2 + r2["wall_sd"] ** 2), C_OTH, max(r1["peak_mib"], r2["peak_mib"])),
         ("FIMO\n(PWM, p<=1e-4)", fm_["wall_mean"], fm_["wall_sd"], C_OTH, fm_["peak_mib"])]
ax.bar(range(3), [v for _, v, *_ in items], yerr=[s for _, _, s, *_ in items], color=[c for *_, c, _ in items], capsize=4)
for i, (_, v, _, _, mb) in enumerate(items):
    ax.text(i, v + 2.5, f"{v:.1f} s\n{mb:.0f} MiB", ha="center", va="bottom", fontsize=11)
ax.set_ylim(0, 90)
ax.set_xticks(range(3)); ax.set_xticklabels([n for n, *_ in items])
ax.set_ylabel("Wall time (s)")
ax.set_title("B  Motif scan, CYC-RE_RAM1 + CYC-RE_NIN", loc="left", fontweight="bold")
ax.text(0.98, 0.95, "Cis-GS and seqkit: identical 161 hits\nFIMO: 25,774 hits (PWM, not exact-match)",
        transform=ax.transAxes, ha="right", va="top", fontsize=10.5, color="#444")

# ---- C: co-expression pipeline (igraph backend, timed runs 1-3) ----
ax = axs[1, 0]
mean = lambda k: st.mean(r["stages"][k] for r in runs)
stage_rows = [("Load + filter + log2", mean("load") + mean("filter_topvar") + mean("log2"), "#bbbbbb"),
              ("Pearson correlation", mean("pearson"), "#56B4E9"),
              ("Graph + Louvain (igraph)", mean("graph_louvain"), "#D55E00"),
              ("K-means elbow (k = 2-15)", mean("elbow_k2_15"), "#009E73"),
              ("Final K-means", mean("kmeans_final"), "#CC79A7")]
total = st.mean(r["stages"]["total"] for r in runs)
ypos = list(range(len(stage_rows)))[::-1]
ax.barh(ypos, [v for _, v, _ in stage_rows], color=[c for *_, c in stage_rows], height=0.6)
for y, (_, v, _) in zip(ypos, stage_rows):
    ax.text(v + 0.08, y, f"{v:.1f} s", va="center", fontsize=11)
ax.set_yticks(ypos); ax.set_yticklabels([n for n, *_ in stage_rows])
ax.set_xlim(0, 5.6); ax.set_xlabel("Wall time (s)")
ax.set_title("C  Co-expression pipeline (5,000 genes x 54 samples)", loc="left", fontweight="bold")
mods = sorted(set(r["modules"] for r in runs))
mod_txt = f"{mods[0]}-{mods[-1]}" if len(mods) > 1 else str(mods[0])
ax.text(0.97, 0.115, f"Total {total:.1f} s, peak RAM {max(r['peak_mb'] for r in runs)/1024:.1f} GiB" + chr(10) +
        f"{runs[0]['edges']:,} edges (|r| >= 0.70), {mod_txt} modules",
        transform=ax.transAxes, ha="right", fontsize=11, color="#444")
ax.text(0.97, 0.045, "PlantPAN 4.0 (web server, precomputed networks): not timed",
        transform=ax.transAxes, ha="right", fontsize=9.5, color="#666", style="italic")

# ---- D: parallel scan scaling (prototype) ----
ax = axs[1, 1]
for lab, key, c, mk in (("CYC-RE_RAM1 + CYC-RE_NIN", "two CYC-RE motifs (RAM1, NIN)", C_CIS, "o"), ("GGATT (short, common motif)", "GGATT", C_OLD, "s")):
    d = scal[key]
    w = sorted(int(k) for k in d)
    mean_w = {k: st.mean(x["wall_s"] for x in d[str(k)]) for k in w}
    ax.plot(w, [mean_w[1] / mean_w[k] for k in w], marker=mk, color=c, lw=2.2, ms=8, label=lab)
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
