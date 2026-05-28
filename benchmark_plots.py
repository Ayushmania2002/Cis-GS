"""
Cis-GS Benchmark - Publication Figure Generator  v1.2.0
Run:  python benchmark_plots.py
Outputs:  benchmark_out/benchmark_figures.png  (300 dpi)
          benchmark_out/benchmark_figures.svg  (vector)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
import matplotlib.font_manager as fm
from pathlib import Path

# ── Font setup ─────────────────────────────────────────────────────────────
_available = {f.name for f in fm.fontManager.ttflist}
FONT = "Arial" if "Arial" in _available else "DejaVu Sans"

FS      = 11    # base font size (axis labels, legends)
FS_SM   = 9.5   # small (tick labels, annotations)
FS_TINY = 8.5   # tiny (data labels on bars)
FS_PNL  = 14    # panel letter size

plt.rcParams.update({
    "font.family":        FONT,
    "font.size":          FS,
    "axes.titlesize":     FS,
    "axes.titleweight":   "bold",
    "axes.labelsize":     FS,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.color":         "#E5E5E5",
    "grid.linewidth":     0.6,
    "grid.linestyle":     "--",
    "axes.axisbelow":     True,
    "xtick.labelsize":    FS_SM,
    "ytick.labelsize":    FS_SM,
    "figure.facecolor":   "white",
    "axes.facecolor":     "white",
    "legend.fontsize":    FS_SM,
    "legend.framealpha":  0.9,
    "legend.edgecolor":   "#CCCCCC",
    "errorbar.capsize":   4,
})

# ── Color palette  (Tol "Muted" + Wong; colorblind-safe, soft tones) ───────
# Species colors - Tol 2021 "Muted" palette (doi:10.5281/zenodo.3381072)
C_ARA = "#CC6677"   # Arachis  - rose       (warm, soft; safe under all CB)
C_OSA = "#88CCEE"   # Rice     - light cyan (cool, soft; safe under all CB)
C_MTR = "#44AA99"   # Medicago - teal       (neutral; distinguishable from rose)

# Function-type colors (promoter / motif)
C_PROM  = "#56B4E9"  # sky-blue  (extraction bars)
C_MOTIF = "#CC79A7"  # reddish-purple (motif bars)

# KEGG colors
C_NET   = "#E69F00"  # orange         (network fetch - safe under all CB types)
C_CACHE = "#F5DFA0"  # pale gold/sand (cached fetch - lighter tone)

# ── Hardware label ─────────────────────────────────────────────────────────
HARDWARE = (
    "Intel Core i5-14450HX  •  10 cores / 16 threads  •  25.4 GB RAM  "
    "•  Windows 11  •  Python 3.14.2  •  Cis-GS v1.2.0"
)

# ══════════════════════════════════════════════════════════════════════════
# DATA  (from benchmark run 2026-05-28)
# ══════════════════════════════════════════════════════════════════════════

# ── A: Promoter Extraction ─────────────────────────────────────────────────
prom_labels = [
    r"$\mathit{O.\ sativa}$" + "\nIRGSP-1.0 (373 Mb)",
    r"$\mathit{M.\ truncatula}$" + "\nMt5.0 (430 Mb)",
    r"$\mathit{A.\ hypogaea}$" + "\ngnm1 (2,557 Mb)",
    r"$\mathit{A.\ hypogaea}$" + "\ngnm2 (2,558 Mb)",
]
prom_mean = [11.46, 12.14, 86.51, 83.18]
prom_sd   = [ 0.214, 0.035,  6.922,  3.228]
prom_n    = [37890, 37978, 67122, 106608]
prom_mb   = [362,   421,   2500,  2500]

# ── B: Motif Search ────────────────────────────────────────────────────────
motif_labels = prom_labels
motif_mean   = [ 6.95,  6.37, 10.93, 17.90]
motif_sd     = [ 0.521,  0.509,  0.266,  1.825]
motif_nprom  = prom_n

# ── C: KEGG Pathway Fetch - network vs cached ─────────────────────────────
kegg_orgs        = [r"ahf" + "\n" + r"($\mathit{Arachis}$)",
                    "osa\n(Rice)",
                    r"mtr" + "\n" + r"($\mathit{Medicago}$)"]
kegg_net_mean    = [8.09, 4.96, 5.04]
kegg_net_sd      = [0.0,  0.0,  0.0]
kegg_cache_mean  = [0.026, 0.017, 0.022]
kegg_cache_sd    = [0.027, 0.025, 0.033]
kegg_n_pathways  = [165, 162, 162]

# ── D: Full Pipeline - 3 species (5 steps + 2 k-means sub-steps) ──────────
pipe_steps = [
    "Normalisation",
    "Correlation\nMatrix",
    "Louvain\nClustering",
    "Elbow\nMethod",
    "k-means\nClustering",
]
pipe_data = {
    # label, color, [norm, corr, louvain, elbow, kmeans], [sd×5]
    r"$\mathit{A.\ hypogaea}$ gnm1": {
        "color": C_ARA,
        "mean":  [0.030, 1.89, 4.04, 3.85, 0.33],
        "sd":    [0.001, 0.013, 0.202, 1.462, 0.001],
        "n":     "56513 genes x 54 samples",
    },
    r"$\mathit{O.\ sativa}$ IRGSP-1.0": {
        "color": C_OSA,
        "mean":  [0.020, 3.17, 3.54, 4.06, 0.48],
        "sd":    [0.002, 0.198, 0.255, 0.069, 0.015],
        "n":     "27813 genes x 80 samples",
    },
    r"$\mathit{M.\ truncatula}$ Mt5.0": {
        "color": C_MTR,
        "mean":  [0.010, 0.38, 4.17, 1.75, 0.23],
        "sd":    [0.000, 0.033, 0.283, 0.022, 0.012],
        "n":     "27142 genes x 27 samples",
    },
}

# ── E: KEGG Enrichment Scaling ─────────────────────────────────────────────
kegg_ns = [50, 200, 500, 2000]
# Values in milliseconds (from benchmark output, 0.00–0.01 s)
kegg_scale = {
    r"ahf ($\mathit{Arachis}$)": {
        "color": C_ARA, "ls": "-",
        "mean_ms": [7.0, 8.0, 8.0, 9.0],
        "sd_ms":   [1.0, 1.0, 1.0, 0.5],
    },
    "osa (Rice)": {
        "color": C_OSA, "ls": "--",
        "mean_ms": [2.5, 3.0, 3.0, 6.5],
        "sd_ms":   [0.3, 0.3, 0.3, 0.5],
    },
    r"mtr ($\mathit{Medicago}$)": {
        "color": C_MTR, "ls": "-.",
        "mean_ms": [3.5, 4.0, 3.5, 8.5],
        "sd_ms":   [0.8, 0.8, 0.5, 0.5],
    },
}


# ══════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor("white")

gs = GridSpec(
    2, 3, figure=fig,
    hspace=0.52, wspace=0.38,
    left=0.07, right=0.97, top=0.90, bottom=0.20,
)

ax_A = fig.add_subplot(gs[0, 0])          # Promoter extraction
ax_B = fig.add_subplot(gs[0, 1])          # Motif search
ax_C = fig.add_subplot(gs[0, 2])          # KEGG fetch
ax_D = fig.add_subplot(gs[1, :2])         # Full pipeline (full width left)
ax_E = fig.add_subplot(gs[1, 2])          # KEGG scaling


def _panel_label(ax, letter, dx=-0.10, dy=1.06):
    """Add bold uppercase panel letter at top-left."""
    ax.text(dx, dy, letter, transform=ax.transAxes,
            fontsize=FS_PNL, fontweight="bold",
            fontfamily=FONT, va="top", ha="left",
            color="black")


# ══════════════════════════════════════════════════════════════════════════
# A - Promoter Extraction
# ══════════════════════════════════════════════════════════════════════════
y = np.arange(len(prom_labels))
# gradient: lighter for small genomes, darker for large
bar_colors = [C_PROM + "AA", C_PROM + "AA", C_PROM, C_PROM]

bars_A = ax_A.barh(
    y, prom_mean, xerr=prom_sd,
    color=[C_PROM if m > 20 else "#6EB0D8" for m in prom_mean],
    edgecolor="white", linewidth=0.8,
    height=0.55, capsize=3,
    error_kw={"linewidth": 1.2, "ecolor": "#666666"},
)
ax_A.set_yticks(y)
ax_A.set_yticklabels(prom_labels, fontsize=FS_SM)
ax_A.set_xlabel("Wall time (s)", fontsize=FS)
ax_A.set_xlim(0, max(prom_mean) * 1.28)
ax_A.invert_yaxis()
ax_A.grid(axis="x")
ax_A.grid(axis="y", alpha=0)

for bar, val, sd in zip(bars_A, prom_mean, prom_sd):
    ax_A.text(val + sd + 1.2,
              bar.get_y() + bar.get_height() / 2,
              f"{val:.1f} s", va="center", fontsize=FS_TINY, color="#333333")

_panel_label(ax_A, "A")
ax_A.set_title("Promoter Extraction (2 kb upstream)", fontsize=FS, fontweight="bold", pad=10)


# ══════════════════════════════════════════════════════════════════════════
# B - Motif Search
# ══════════════════════════════════════════════════════════════════════════
bars_B = ax_B.barh(
    y, motif_mean, xerr=motif_sd,
    color=[C_MOTIF if m > 10 else "#E8BDD8" for m in motif_mean],
    edgecolor="white", linewidth=0.8,
    height=0.55, capsize=3,
    error_kw={"linewidth": 1.2, "ecolor": "#666666"},
)
ax_B.set_yticks(y)
ax_B.set_yticklabels(prom_labels, fontsize=FS_SM)
ax_B.set_xlabel("Wall time (s)", fontsize=FS)
ax_B.set_xlim(0, max(motif_mean) * 1.30)
ax_B.invert_yaxis()
ax_B.grid(axis="x")
ax_B.grid(axis="y", alpha=0)

for bar, val, n, sd in zip(bars_B, motif_mean, motif_nprom, motif_sd):
    ax_B.text(val + sd + 0.3,
              bar.get_y() + bar.get_height() / 2,
              f"{val:.1f} s", va="center", fontsize=FS_TINY, color="#333333")

_panel_label(ax_B, "B")
ax_B.set_title("Motif Scan (CYC-RE_RAM1 + CYC-RE_NIN)", fontsize=FS, fontweight="bold", pad=10)


# ══════════════════════════════════════════════════════════════════════════
# C - KEGG Pathway Fetch: network vs cached  (log scale)
# ══════════════════════════════════════════════════════════════════════════
x_C   = np.arange(len(kegg_orgs))
w     = 0.35
bars_Cn = ax_C.bar(
    x_C - w / 2, kegg_net_mean,
    width=w, color=C_NET, edgecolor="white", linewidth=0.8,
    label="Network (REST API)",
    yerr=kegg_net_sd, capsize=3,
    error_kw={"linewidth": 1.2, "ecolor": "#666666"},
)
bars_Cc = ax_C.bar(
    x_C + w / 2, kegg_cache_mean,
    width=w, color="#F0B27A", edgecolor="white", linewidth=0.8,
    label="Disk cache",
    yerr=kegg_cache_sd, capsize=3,
    error_kw={"linewidth": 1.2, "ecolor": "#666666"},
)
ax_C.set_xticks(x_C)
ax_C.set_xticklabels(kegg_orgs, fontsize=FS_SM)
ax_C.set_ylabel("Wall time (s)", fontsize=FS)
ax_C.set_yscale("log")
ax_C.set_ylim(0.005, 60)
ax_C.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:g}" if v >= 1 else f"{v:.3f}"))
ax_C.legend(fontsize=FS_SM, loc="upper left",
            bbox_to_anchor=(0.02, 0.98), borderaxespad=0)

_panel_label(ax_C, "C")
ax_C.set_title("KEGG Pathway Fetch", fontsize=FS, fontweight="bold", pad=10)


# ══════════════════════════════════════════════════════════════════════════
# D - Full Co-expression + k-means Pipeline  (3 species, log scale)
# ══════════════════════════════════════════════════════════════════════════
n_steps   = len(pipe_steps)
n_species = len(pipe_data)
w_D = 0.24
offsets = [-w_D, 0, w_D]
x_D = np.arange(n_steps)

for (sp_label, sp), offset in zip(pipe_data.items(), offsets):
    ax_D.bar(
        x_D + offset,
        sp["mean"], yerr=sp["sd"],
        width=w_D,
        color=sp["color"], edgecolor="white", linewidth=0.8,
        label=f"{sp_label}  ({sp['n']})",
        capsize=2.5,
        error_kw={"linewidth": 1.0, "ecolor": "#666666"},
    )

ax_D.set_yscale("log")
ax_D.set_xticks(x_D)
ax_D.set_xticklabels(pipe_steps, fontsize=FS_SM)
ax_D.set_ylabel("Wall time (s, log scale)", fontsize=FS)
ax_D.set_ylim(5e-4, 50)
ax_D.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"{v:.3g}"))
ax_D.legend(fontsize=FS_SM, loc="upper right", ncol=1)

# Annotate each bar group with time values (only top species per step)
for s_idx, (sp_label, sp) in enumerate(pipe_data.items()):
    offset = offsets[s_idx]
    for x_i, (val, sd) in enumerate(zip(sp["mean"], sp["sd"])):
        label = (f"{val*1000:.1f} ms" if val < 0.1
                 else f"{val:.2f} s" if val < 10
                 else f"{val:.0f} s")
        ax_D.text(
            x_i + offset,
            max(val * 2.5, 1e-3),
            label,
            ha="center", va="bottom",
            fontsize=7.0, color="#333333",
            rotation=90 if val > 10 else 0,
        )

_panel_label(ax_D, "D")
ax_D.set_title(
    "Co-expression and Clustering Pipeline - Three Species Comparison",
    fontsize=FS, fontweight="bold", pad=10,
)


# ══════════════════════════════════════════════════════════════════════════
# E - KEGG Enrichment Scaling  (all 3 organisms, ms)
# ══════════════════════════════════════════════════════════════════════════
markers = {r"ahf ($\mathit{Arachis}$)": "o", "osa (Rice)": "s", r"mtr ($\mathit{Medicago}$)": "^"}

for org, vals in kegg_scale.items():
    ax_E.errorbar(
        kegg_ns, vals["mean_ms"], yerr=vals["sd_ms"],
        fmt=f"{markers[org]}{vals['ls']}",
        color=vals["color"], markersize=7,
        linewidth=1.8, elinewidth=1.2,
        markeredgecolor="white", markeredgewidth=0.8,
        label=org,
    )

ax_E.set_xlabel("Query gene list size (n)", fontsize=FS)
ax_E.set_ylabel("Wall time (ms)", fontsize=FS)
ax_E.set_xscale("log")
ax_E.set_xticks(kegg_ns)
ax_E.set_xticklabels([str(n) for n in kegg_ns], fontsize=FS_SM)
ax_E.xaxis.set_major_formatter(ticker.ScalarFormatter())
ax_E.set_ylim(0, 14)
ax_E.legend(fontsize=FS_SM, loc="lower right")

_panel_label(ax_E, "E")
ax_E.set_title("KEGG Enrichment Scaling", fontsize=FS, fontweight="bold", pad=10)


# ══════════════════════════════════════════════════════════════════════════
# Overall title + hardware note
# ══════════════════════════════════════════════════════════════════════════
fig.suptitle(
    "Cis-GS v1.2.0 - Computational Performance Benchmark",
    fontsize=14, fontweight="bold", color="black", y=0.955,
)


# ══════════════════════════════════════════════════════════════════════════
# Figure Legend  (below all panels)
# ══════════════════════════════════════════════════════════════════════════
legend_text = (
    "Figure 1. Computational performance of the Cis-GS v1.2.0 pipeline across three plant genomes.  "
    "All experiments were performed in triplicate (n = 3–5 replicates) on an Intel Core "
    "i5-14450HX workstation (10 cores / 16 threads, 25.4 GB RAM, Windows 11, Python 3.14.2).  "
    "Error bars represent ±1 standard deviation.\n"
    "(A) Promoter extraction (2 kb upstream of the transcription start site) wall time for four "
    "genome annotations: O. sativa IRGSP-1.0 (362 MB, 37,890 genes), M. truncatula Mt5.0 "
    "(421 MB, 37,978 genes), A. hypogaea gnm1 (2.5 GB, 67,122 genes), and A. hypogaea gnm2 "
    "(2.5 GB, 106,608 genes).  "
    "(B) Motif scanning time (CYC-REham1 TGGCCCGGCCCA and CYC-REnIn "
    "NGCCATGTGGCN) across the same four promoter sets.  "
    "(C) KEGG REST API pathway fetch time (network) versus disk-cache read time for three organisms: "
    "ahf (A. hypogaea, 165 pathways), osa (O. sativa, 162 pathways), and mtr (M. truncatula, 162 pathways). "
    "(D) Full co-expression and clustering pipeline timing across three species on a log scale. "
    "Steps shown: log2(n + 1) expression normalisation, Pearson correlation matrix (top "
    "variable genes; n = 5,000 for Arachis and Rice, n = 3,000 for Medicago), "
    "Louvain community detection via igraph C backend (r ≥ 0.70), k-means elbow optimisation "
    "(k = 2– 15), and k-means clustering at the optimal k.  "
    "(E) KEGG hypergeometric enrichment scaling test: mean wall time (ms) as a function of query "
    "gene-list size (50– 2,000 genes) for all three KEGG organisms. "
    "Times remain below 10 ms across all query sizes, confirming sub-second per-module enrichment "
    "irrespective of species."
)

fig.text(
    0.5, 0.01,
    legend_text,
    ha="center", va="bottom",
    fontsize=8.5, color="#333333",
    wrap=True,
    fontstyle="normal",
    transform=fig.transFigure,
    multialignment="left",
    bbox=dict(facecolor="#F9F9F9", edgecolor="#CCCCCC",
              boxstyle="round,pad=0.5", linewidth=0.8),
)


# ══════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════
out_dir = Path("benchmark_out")
out_dir.mkdir(exist_ok=True)

fig.savefig(out_dir / "benchmark_figures.png", dpi=1200, bbox_inches="tight",
            facecolor="white")
fig.savefig(out_dir / "benchmark_figures.svg", bbox_inches="tight",
            facecolor="white")

print(f"Saved -> {out_dir / 'benchmark_figures.png'}  (1200 dpi)")
print(f"Saved -> {out_dir / 'benchmark_figures.svg'}  (vector)")
