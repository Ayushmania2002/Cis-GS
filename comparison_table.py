"""
Cis-GS Tool Comparison Table - Publication Figure Generator
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
from pathlib import Path
import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = None

# ── Font ───────────────────────────────────────────────────────────────────
_available = {f.name for f in fm.fontManager.ttflist}
FONT = "Arial" if "Arial" in _available else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT})

# ── Colorblind-safe palette (Tol Muted + Wong) ─────────────────────────────
C_YES       = "#44AA99"   # teal       - Yes
C_NO        = "#EEEEEE"   # light gray - No
C_PARTIAL   = "#DDCC77"   # sand       - Partial
C_CISG_HDR  = "#0072B2"   # Wong blue  - Cis-GS header
C_HDR_TOOLS = "#2C3E50"   # charcoal   - other tool headers
C_HDR_FEAT  = "#3D4D5C"   # feature col header
C_CAT_BG    = "#D5D8DC"   # category divider
C_CISG_CELL = "#EAF4FF"   # light blue tint - Cis-GS No cells

YES, NO, PARTIAL = 1, 0, 0.5

# ── Tools ──────────────────────────────────────────────────────────────────
tools = [
    "PlantCARE", "PLACE", "FIMO\n(MEME Suite)",
    "JASPAR\nScan", "Homer", "CiiiDER",
    "Cis-GS\n(v1.3.0)",
]
CISG = len(tools) - 1

# ── Feature categories and data ────────────────────────────────────────────
# values: [PlantCARE, PLACE, FIMO, JASPAR, Homer, CiiiDER, Cis-GS]
categories = [
    ("Input & Scope", [
        ("Genome-wide analysis",           [NO,      NO,      YES,     PARTIAL, YES,     PARTIAL, YES]),
        ("Automated promoter extraction",  [NO,      NO,      NO,      NO,      PARTIAL, NO,      YES]),
        ("Non-model organism support",     [NO,      NO,      YES,     YES,     YES,     YES,     YES]),
        ("Custom motif input",             [NO,      NO,      YES,     PARTIAL, YES,     YES,     YES]),
    ]),
    ("Motif Analysis", [
        ("IUPAC degeneracy support",       [PARTIAL, PARTIAL, YES,     YES,     PARTIAL, YES,     YES]),
        ("Statistical scoring (p-values)", [NO,      NO,      YES,     YES,     YES,     YES,     YES]),
        ("PWM / PSSM scoring",             [NO,      NO,      YES,     YES,     YES,     YES,     NO ]),
        ("Consensus pattern matching",     [YES,     YES,     PARTIAL, NO,      NO,      NO,      YES]),
    ]),
    ("Downstream Biology", [
        ("Co-expression analysis",         [NO,      NO,      NO,      NO,      NO,      NO,      YES]),
        ("KEGG pathway enrichment",        [NO,      NO,      NO,      NO,      NO,      NO,      YES]),
        ("Graph clustering (Louvain)",     [NO,      NO,      NO,      NO,      NO,      NO,      YES]),
        ("Expression data integration",    [NO,      NO,      NO,      NO,      NO,      NO,      YES]),
    ]),
    ("Usability", [
        ("Local execution (no limits)",    [NO,      NO,      YES,     NO,      YES,     YES,     YES]),
        ("Whole-genome batch processing",  [NO,      NO,      YES,     PARTIAL, YES,     PARTIAL, YES]),
        ("Multi-species in one run",       [NO,      NO,      NO,      NO,      NO,      NO,      YES]),
    ]),
]

# Flatten rows
all_rows = []
for cat_name, rows in categories:
    for feat, vals in rows:
        all_rows.append((feat, vals))
n_rows = len(all_rows)   # 15
n_tools = len(tools)     # 7

# ── Font sizes ─────────────────────────────────────────────────────────────
FS_TITLE    = 26     # figure title
FS_SUBTITLE = 18     # subtitle / caption line
FS_COL_HDR  = 21     # "Feature / Capability" header
FS_TOOL_HDR = 19     # tool name headers
FS_CAT      = 19     # category divider label
FS_FEAT     = 19     # feature row labels
FS_VAL      = 19     # Yes / No / Partial cell text
FS_LEGEND   = 19     # legend labels

# ── Layout constants (data units) ─────────────────────────────────────────
FEAT_W  = 6.8    # feature column width
TOOL_W  = 3.00   # each tool column width
ROW_H   = 1.30   # data row height
HDR_H   = 1.80   # tool header height
CAT_H   = 0.78   # category divider height
PAD_TOP = 3.20   # space above header for title
PAD_BOT = 2.20   # space below table for legend

n_cats  = len(categories)
total_w = FEAT_W + n_tools * TOOL_W
total_h = PAD_TOP + HDR_H + n_cats * CAT_H + n_rows * ROW_H + PAD_BOT

fig_w   = 28
fig_h   = total_h * (fig_w / total_w)

fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(0, total_w)
ax.set_ylim(0, total_h)
ax.axis("off")
fig.patch.set_facecolor("white")

# ── Helper: draw one rectangle ─────────────────────────────────────────────
def cell(x, y, w, h, fc, ec="#CCCCCC", lw=0.6, zorder=1):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="square,pad=0",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder,
    ))

def label(x, y, w, h, txt, fs, color, weight="normal", ha="center", va="center", style="normal"):
    ax.text(x + w * (0 if ha == "left" else (1 if ha == "right" else 0.5)),
            y + h / 2,
            txt, ha=ha, va=va,
            fontsize=fs, color=color, fontweight=weight,
            fontstyle=style, fontfamily=FONT)

def val_cell(x, y, val, is_cisg=False):
    if val == YES:
        bg = "#2E9E8A" if is_cisg else C_YES
        tc, sym, fw = "white", "Yes", "bold"
    elif val == PARTIAL:
        bg = C_PARTIAL
        tc, sym, fw = "#000000", "Partial", "normal"
    else:
        bg = C_CISG_CELL if is_cisg else C_NO
        tc, sym, fw = "#555555", "No", "normal"
    cell(x, y, TOOL_W, ROW_H,
         fc=bg,
         ec="#0072B2" if is_cisg else "#CCCCCC",
         lw=1.0 if is_cisg else 0.4)
    label(x, y, TOOL_W, ROW_H, sym, FS_VAL, tc, fw)

# ── Title ──────────────────────────────────────────────────────────────────
ty = total_h - PAD_TOP / 2 - 0.1
ax.text(total_w / 2, ty + 0.35,
        "Comparative analysis of cis-regulatory element discovery tools",
        ha="center", va="center", fontsize=FS_TITLE, fontweight="bold",
        color="#000000", fontfamily=FONT)
ax.text(total_w / 2, ty - 0.30,
        "Cis-GS v1.3.0 integrates genome-wide promoter extraction, motif scanning, "
        "co-expression clustering, and KEGG enrichment in a single automated pipeline",
        ha="center", va="center", fontsize=FS_SUBTITLE, color="#000000",
        fontfamily=FONT, style="italic")

# ── Header row ─────────────────────────────────────────────────────────────
hdr_y = total_h - PAD_TOP - HDR_H

# Feature column header
cell(0, hdr_y, FEAT_W, HDR_H, fc=C_HDR_FEAT, ec="white", lw=1.5)
label(0, hdr_y, FEAT_W, HDR_H, "Feature / Capability",
      FS_COL_HDR, "white", "bold", ha="center")

# Tool headers
for i, tool in enumerate(tools):
    x = FEAT_W + i * TOOL_W
    is_cisg = (i == CISG)
    bg = C_CISG_HDR if is_cisg else C_HDR_TOOLS
    cell(x, hdr_y, TOOL_W, HDR_H, fc=bg, ec="white", lw=1.5)
    label(x, hdr_y, TOOL_W, HDR_H, tool, FS_TOOL_HDR,
          "white", "bold" if is_cisg else "normal")

# ── Data rows ──────────────────────────────────────────────────────────────
y_cur   = hdr_y
row_idx = 0

for cat_name, rows in categories:
    # Category divider
    y_cur -= CAT_H
    cell(0, y_cur, total_w, CAT_H, fc=C_CAT_BG, ec="white", lw=0.5)
    label(0, y_cur, total_w, CAT_H, cat_name,
          FS_CAT, "#000000", "bold", style="italic")

    for feat, vals in rows:
        y_cur -= ROW_H
        row_bg = "#FAFAFA" if row_idx % 2 == 0 else "#FFFFFF"

        # Feature cell
        cell(0, y_cur, FEAT_W, ROW_H, fc=row_bg, ec="#DDDDDD", lw=0.4)
        ax.text(FEAT_W - 0.22, y_cur + ROW_H / 2, feat,
                ha="right", va="center", fontsize=FS_FEAT,
                color="#000000", fontfamily=FONT)

        # Tool cells
        for i, val in enumerate(vals):
            val_cell(FEAT_W + i * TOOL_W, y_cur, val, is_cisg=(i == CISG))

        row_idx += 1

# ── Outer border around Cis-GS column ──────────────────────────────────────
cisg_x     = FEAT_W + CISG * TOOL_W
col_top    = hdr_y
col_bottom = y_cur
ax.add_patch(mpatches.FancyBboxPatch(
    (cisg_x, col_bottom),
    TOOL_W, col_top + HDR_H - col_bottom,
    boxstyle="square,pad=0",
    facecolor="none", edgecolor=C_CISG_HDR,
    linewidth=3.2, zorder=10,
))

# ── Legend ─────────────────────────────────────────────────────────────────
leg_y   = y_cur - 1.00
items   = [
    ("#2E9E8A", "Fully supported"),
    (C_PARTIAL,  "Partially supported"),
    (C_NO,       "Not supported"),
    (C_CISG_HDR, "Cis-GS (this study)"),
]
box_s   = 0.55
gap     = total_w / len(items)           # evenly divide full table width
start_x = gap / 2 - box_s / 2           # centre each item in its lane

for j, (color, lbl) in enumerate(items):
    lx = start_x + j * gap
    ax.add_patch(mpatches.FancyBboxPatch(
        (lx, leg_y), box_s, box_s,
        boxstyle="square,pad=0",
        facecolor=color, edgecolor="#888888", linewidth=1.0,
    ))
    ax.text(lx + box_s + 0.30, leg_y + box_s / 2, lbl,
            ha="left", va="center", fontsize=FS_LEGEND,
            color="#000000", fontfamily=FONT)

# ── Save ───────────────────────────────────────────────────────────────────
out_dir = Path("benchmark_out").resolve()
out_dir.mkdir(exist_ok=True)
png_path = str(out_dir / "tool_comparison_table.png").replace("\\", "/")
svg_path = str(out_dir / "tool_comparison_table.svg").replace("\\", "/")
fig.savefig(png_path, dpi=600, bbox_inches="tight", facecolor="white")
fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
print(f"Saved -> {png_path}  (600 dpi)")
print(f"Saved -> {svg_path}  (vector, lossless)")
