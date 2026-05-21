<div align="center">

<img src="assets/banner.png" alt="Cis-GS banner" width="780"/>

# Cis-GS &nbsp;&middot;&nbsp; Cis-regulatory Element Genome Scanner

**A whole-genome pipeline for discovering cis-regulatory elements, coupling them to expression, and finishing with KEGG enrichment — in one PyQt5 desktop app *and* one interactive CLI.**

[![PyPI version](https://img.shields.io/pypi/v/cis-gs.svg?color=16A085)](https://pypi.org/project/cis-gs/)
[![Python](https://img.shields.io/pypi/pyversions/cis-gs.svg)](https://pypi.org/project/cis-gs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-16A085)](https://Ayushmania2002.github.io/Cis-GS/)
[![Build](https://github.com/Ayushmania2002/Cis-GS/actions/workflows/docs.yml/badge.svg)](https://github.com/Ayushmania2002/Cis-GS/actions)
[![DOI](https://img.shields.io/badge/DOI-pending-lightgrey)](#citation)

</div>

---

## Table of Contents

- [What Cis-GS Does](#what-cis-gs-does)
- [Highlights of v1.1](#highlights-of-v11)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [The 7-Step Workflow](#the-7-step-workflow)
- [Supported Motif Databases](#supported-motif-databases)
- [CLI Reference](#cli-reference)
- [Programmatic API](#programmatic-api)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## What Cis-GS Does

Cis-GS automates the full **promoter &rarr; motif &rarr; expression &rarr; function** journey that
plant- and animal-genomics labs run by hand today:

1. **Fetch** a reference genome + annotation directly from NCBI (live Assembly search).
2. **Extract** promoter sequences (configurable length, strand-aware, intergenic-clipped) from any GFF3.
3. **Scan** those promoters for transcription-factor binding motifs imported from PlantTFDB, AnimalTFDB, JASPAR 2024, or HOCOMOCO v11 — or any user-supplied IUPAC consensus.
4. **Render** publication-ready sequence logos and per-gene hit tables with hypergeometric p-values and BH-FDR.
5. **Couple** the hits to your expression table (RNA-seq, microarray, qPCR) to flag motifs whose presence tracks expression direction.
6. **Build** a co-expression network (Pearson / Spearman / WGCNA-style soft-thresholding), detect modules via Louvain or hierarchical clustering, and visualise eigengenes.
7. **Enrich** the top module / cluster against KEGG (live REST queries, 11 700+ organisms) with one-sided hypergeometric ORA + Benjamini-Hochberg FDR.

Everything runs **locally**, **offline-friendly after the first network fetch**, and exports CSV / SVG / PDF at every step.

---

## Highlights of v1.1

- **Live KEGG dropdown** — every one of the 11 700+ organisms KEGG knows about, fetched on demand. No more stale species tables.
- **Live NCBI Taxonomy search** — type any common or Latin name; results stream back as you type.
- **60× faster ID conversion** — MyGene.info batched POST + progress bar (previously 60+ minutes for 10 k genes; now ~60 s).
- **Interactive CLI wizards** — `cis-gs wizard` walks you through every step with arrow-key menus. Every subcommand also accepts `-i / --interactive`.
- **Fuzzy "did you mean...?"** for CLI typos.
- **Brand-icon Contact tab** with real-website logos (LinkedIn, GitHub, KEGG, NCBI, PlantTFDB, AnimalTFDB, MyGene).
- **Modern single-color theme** (teal `#16A085`) with instant light / dark toggle — no more 1-2 s freeze.
- **First-run NCBI email prompt** — required by the Entrez API, stored only on your machine.
- **Three Gene-ID-Mapping methods** for the annoying NCBI-LOC vs species-database mismatch (column swap, mapping CSV, GFF3 Dbxref expansion).

See the [full release notes](https://github.com/Ayushmania2002/Cis-GS/releases) for the v1.0 &rarr; v1.1 diff.

---

## Installation

### Option 1 — PyPI (Linux / macOS / Windows)

```bash
pip install cis-gs
cis-gs --help          # CLI
cis-gs-gui             # GUI
```

Python 3.9+ required. The first GUI launch will pop up a one-time NCBI email prompt.

### Option 2 — Standalone Windows executable

Download `Cis-GS.exe` from the [latest release](https://github.com/Ayushmania2002/Cis-GS/releases) page.
Double-click. No Python install needed. Roughly 120 MB.

### Option 3 — From source

```bash
git clone https://github.com/Ayushmania2002/Cis-GS.git
cd Cis-GS
pip install -e ".[dev,docs]"
python app_v4_open.py        # GUI
python -m cis_gs --help      # CLI
```

Full build details (PyInstaller spec, build scripts for all 3 OSes, PyPI release workflow):
see [`BUILD.md`](BUILD.md).

---

## Quick Start

### GUI (one minute)

```bash
cis-gs-gui
```

1. **Step 1 — Promoters**: drop a FASTA + GFF3, set promoter length (default 2 kb), click *Extract*.
2. **Step 2 — Motif Search**: click *Import from PlantTFDB* (or AnimalTFDB), pick your species, tick the motifs you want, *Import Selected*.
3. **Step 7 — KEGG Enrichment**: pick a KEGG organism from the live dropdown, paste your gene list, run.

Done. CSVs and SVGs land in `~/CisGS-Workspace/`.

### CLI (interactive wizard)

```bash
cis-gs wizard
```

The wizard auto-detects what you've already produced and offers the next sensible step.

### CLI (one-liners)

```bash
# Extract 2 kb promoters from a GFF3 + FASTA
cis-gs extract --fasta genome.fa --gff annot.gff3 --upstream 2000 --out promoters.fa

# Scan promoters with a MEME motif file
cis-gs search --promoters promoters.fa --motifs motifs.meme --out hits.csv

# KEGG enrichment
cis-gs enrich-kegg --organism ath --genes top_module.txt --out kegg.csv
```

Every command supports `-i / --interactive` if you want to be walked through it.

---

## The 7-Step Workflow

| Step | What it does | Output |
|---|---|---|
| **1. Promoters** | Strand-aware promoter extraction from any FASTA + GFF3 | `promoters.fa` |
| **2. Motif Search** | IUPAC / MEME / PlantTFDB / AnimalTFDB scanning with hypergeometric p-values + BH-FDR | `hits.csv`, significance summary |
| **3. Motif Logos** | logomaker sequence logos with information-content shading | per-motif SVG / PNG |
| **4. Expression Feeding** | Joins hits with an expression CSV via three Gene-ID-Mapping methods (LOC swap, mapping CSV, GFF3 Dbxref expansion) | `expression_matched.csv` |
| **5. Coexpression** | Pearson / Spearman / WGCNA-style soft-thresholding, Louvain / hierarchical module detection | `network.gexf`, eigengene plot |
| **6. K-means** | Elbow + silhouette, deterministic seeding, exportable per-cluster gene lists | `clusters/*.txt` |
| **7. KEGG Enrichment** | Live REST query against any of 11 700+ KEGG organisms, hypergeometric ORA, BH-FDR, fold-enrichment | `kegg_enrichment.csv` |

A full description of each step's algorithm and parameters lives in the
[online documentation](https://Ayushmania2002.github.io/Cis-GS/).

---

## Supported Motif Databases

| Database | Coverage | Access |
|---|---|---|
| **PlantTFDB v5** | 157 plant species, ~6 000 motifs | Built-in importer with live species list |
| **AnimalTFDB v4** | Human, mouse, zebrafish, insects | Built-in importer |
| **JASPAR 2024 (non-redundant)** | 575 vertebrate + 99 insect motifs | Direct REST download |
| **HOCOMOCO v11** | ~700 human + ~400 mouse ChIP-Seq motifs | Direct REST download |
| **Custom IUPAC / MEME** | Anything you can write down | Paste into Step 2 |

---

## CLI Reference

```text
cis-gs --help

usage: cis-gs [-h] {wizard,fetch,extract,search,feed,coexpr,kmeans,enrich-kegg,id-convert} ...

  wizard         Step-by-step wizard (recommended for new users)
  fetch          Download a genome + annotation from NCBI
  extract        Extract promoter sequences from FASTA + GFF3
  search         Scan promoters for motif occurrences
  feed           Couple motif hits with an expression table
  coexpr         Build a co-expression network
  kmeans         K-means clustering with elbow / silhouette
  enrich-kegg    KEGG over-representation analysis
  id-convert     Convert gene IDs across namespaces (MyGene.info, batched)
```

Every subcommand accepts `-i / --interactive` for a guided run, and `--help` for full flags.

---

## Programmatic API

```python
from cis_gs.enrichment import KEGGEnricher

e = KEGGEnricher(organism="ath")          # Arabidopsis
result = e.enrich(["AT1G01010", "AT2G18790", "AT3G09600"])
print(result.table.head())
```

```python
from cis_gs.enrichment.idmap import IDConverter

idc = IDConverter(species="human")
mapping = idc.convert(["TP53", "BRCA1", "MYC"], target="entrez")
```

Full API reference: [`Ayushmania2002.github.io/Cis-GS/api`](https://Ayushmania2002.github.io/Cis-GS/api.html).

---

## Screenshots

<div align="center">

| Step 1: Promoter extraction | Step 2: Motif search |
|---|---|
| <img src="docs/source/_static/screenshot_step1.png" width="350"/> | <img src="docs/source/_static/screenshot_step2.png" width="350"/> |

| Step 5: Coexpression network | Step 7: KEGG enrichment |
|---|---|
| <img src="docs/source/_static/screenshot_step5.png" width="350"/> | <img src="docs/source/_static/screenshot_step7.png" width="350"/> |

</div>

> *Screenshots are placeholder paths; replace with actual PNGs in `docs/source/_static/` before publishing.*

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cis-gs-gui: command not found` after `pip install` | Scripts dir not on `PATH` | `python -m cis_gs` works, or add `pip --user` bin dir to PATH |
| First NCBI Fetch returns 0 results | NCBI email not set | Settings &rarr; Set NCBI Email, then retry |
| `KEGG REST unreachable` | Firewall or VPN | Set `HTTPS_PROXY` env var, or use the *Browse & Import* tab with a manually downloaded MEME |
| Motif hits CSV has empty `gene_symbol` column | Annotation GFF3 not loaded in Step 2 | Re-run with the same GFF3 from Step 1 in *Gene ID Resolution* |
| Coexpression freezes on > 30k genes | All-vs-all correlation is O(n²) | Pre-filter to expressed genes (TPM > 1) before Step 5 |

Open an [issue](https://github.com/Ayushmania2002/Cis-GS/issues) with the log file from `~/CisGS-Workspace/cisgs.log` if you hit anything else.

---

## Contributing

Bug reports, feature requests, and pull requests are welcome.
For substantial contributions please open an issue first to discuss the change.

```bash
git clone https://github.com/Ayushmania2002/Cis-GS.git
cd Cis-GS
pip install -e ".[dev]"
pytest                       # run the test suite
```

---

## Citation

If Cis-GS contributes to a publication, please cite:

> Mallick A. *Cis-GS: a unified pipeline for whole-genome cis-regulatory element
> discovery, expression coupling, and KEGG enrichment.* (manuscript in preparation,
> Plant Signaling Lab, IISER Tirupati, 2026).

BibTeX:

```bibtex
@software{mallick_cisgs_2026,
  author  = {Mallick, Ayushman},
  title   = {{Cis-GS}: Cis-regulatory Element Genome Scanner},
  year    = {2026},
  url     = {https://github.com/Ayushmania2002/Cis-GS},
  version = {1.1.0}
}
```

A `CITATION.cff` is included for GitHub's automatic citation widget.

---

## License

Released under the [MIT License](LICENSE). Free for academic and commercial use.

---

## Contact

**Ayushman Mallick** &middot; ayushmania2002@gmail.com
Plant Signaling Lab, [IISER Tirupati](https://www.iisertirupati.ac.in/)

<sub>&copy; 2026 Ayushman Mallick &middot; Plant Signaling Lab &middot; Cis-GS</sub>
