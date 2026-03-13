# Cis-GS — Cis-regulatory Element Genome Scanner

[![PyPI version](https://img.shields.io/pypi/v/Cis-GS?color=teal)](https://pypi.org/project/Cis-GS/)
[![Python versions](https://img.shields.io/pypi/pyversions/Cis-GS)](https://pypi.org/project/Cis-GS/)
[![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Win%20%7C%20Linux%20%7C%20macOS-blue)](https://github.com/Ayushmania2002/Cis-GS/releases)

A complete pipeline for analyzing transcription factor binding sites across genomes — from NCBI genome download to interactive co-expression networks. Works as a GUI desktop app, a command-line tool, or a standalone Windows `.exe`.

Developed at the **Plant Signaling Lab, IISER Tirupati**.

---

## Installation

### Option 1 — Standalone Windows .exe (No Python required)

Download `Cis-GS.zip` from the [**GitHub Releases**](https://github.com/Ayushmania2002/Cis-GS/releases/latest) page, extract it, and double-click `Cis-GS.exe`. No Python, no pip, no dependencies needed.

> **Note:** Windows may show a SmartScreen warning on first launch. Click **"More info" → "Run anyway"** to proceed.

### Option 2 — Windows / Linux / macOS via pip (GUI + CLI)

All platforms with Python 3.8+ installed:

```bash
pip install Cis-GS
cis-gs
```

If `cis-gs` is not found after install (PATH not configured), use:
```bash
python -m cis_gs        # Windows
python3 -m cis_gs       # Linux / macOS
```

#### macOS

```bash
# Install Python 3 if not already installed (via Homebrew)
brew install python

pip3 install Cis-GS
cis-gs
```

> **macOS note:** If PyQt5 fails to install, try:
> ```bash
> pip3 install --upgrade pip
> pip3 install PyQt5 Cis-GS
> ```

#### Linux (Ubuntu / Debian)

```bash
# Install system PyQt5 and pip if needed
sudo apt update
sudo apt install python3-pip python3-pyqt5

pip3 install Cis-GS
cis-gs
```

#### Linux (Fedora / RHEL / CentOS)

```bash
sudo dnf install python3-pip python3-qt5
pip3 install Cis-GS
cis-gs
```

> **Linux note:** If you see a display error (`cannot connect to X server`), make sure you are running a desktop session, not a headless SSH terminal. For headless servers, use the CLI only — the GUI requires a display.

### Option 3 — From Source

```bash
git clone https://github.com/Ayushmania2002/Cis-GS.git
cd Cis-GS
pip install -e .
cis-gs
```

---

## What Does Cis-GS Do?

Cis-GS takes you from a raw genome to a list of transcription factor binding sites and their expression context, step by step:

```
[TF Databases]    PlantTFDB / JASPAR / HOCOMOCO  →  motif patterns
                                     ↓
[Step 1]          NCBI genome + GFF3 annotation
                                     ↓
[Step 2]          Extract upstream promoter sequences (N bp per gene)
                                     ↓
[Step 3]          Scan promoters for TFBS using IUPAC motif patterns
                                     ↓
         ┌─────────────────┬──────────────────────┐
         ↓                 ↓                      ↓
   Sequence Logos    Expression Feeding    Co-expression Network
   (Step 4)          (Step 5)              (Step 6a) + K-means (6b)
```

---

## Step-by-Step Usage

### Using the GUI

Launch with `cis-gs` (or double-click the .exe). Eight tabs appear across the top — work left to right.

#### Step 0 — Get TF Motifs (recommended first)

Before scanning, you need motif patterns from a database.

**For plant species (PlantTFDB):**
1. Go to the **Step 2** tab → click **"Import from PlantTFDB"**
2. Search for your organism (e.g., "arabidopsis"), select it from the dropdown
3. Click **"Download from PlantTFDB Server"** and choose a save folder
4. Switch to the **"Browse & Import"** tab in the dialog
5. Filter by TF Family (e.g., MYB, ERF, WRKY), tick your motifs
6. Click **"Import Selected → Step 2"**

**For animal/vertebrate species (JASPAR / HOCOMOCO):**
1. Go to the **Step 2** tab → click **"Import from JASPAR/HOCOMOCO"**
2. Select a dataset (e.g., JASPAR 2024 Vertebrates or HOCOMOCO Human)
3. Download, browse, filter by species or family, then import

#### Step 1 — NCBI Fetch Tab

1. Type your organism name (e.g., *Arabidopsis thaliana*) and press **Search**
2. Select an assembly from the results table
3. Tick **Download FASTA** and **Download GFF3**, choose an output folder
4. Click **Download** — a progress bar shows progress and a **Stop** button lets you cancel

#### Step 2 — Promoter Extraction (Step 1 Tab)

1. Click **Browse** to select the downloaded FASTA and GFF3 files
2. Set the promoter length (default: 2000 bp upstream of TSS)
3. Click **Extract Promoters**
4. Outputs: `promoters.fasta` and `promoters.tsv` (summary table)

#### Step 3 — Motif Search (Step 2 Tab)

1. The promoter FASTA auto-fills from the previous step
2. Motifs from the database import also auto-fill; or type IUPAC patterns manually:
   ```
   MYB|AT1G00010    AACCGTTA
   ERF|AT2G00020    GCAGCCGCC
   ```
3. Click **Run Scan** — results appear in the table and are saved as a CSV

#### Step 4 — Sequence Logos (Step 3 Tab)

1. Select the motif hits CSV from Step 3
2. Optionally filter by sequence length
3. Click **Generate Logo** — a PNG sequence logo is saved

#### Step 5 — Expression Feeding (Expression Tab)

1. Load your gene expression CSV (rows = genes, columns = samples/time-points)
2. Load the motif hits CSV from Step 3
3. Click **Match Genes** — output is a filtered expression CSV containing only genes with motif hits

#### Step 6a — Co-expression Network (Co-expression Tab)

1. Load the filtered expression CSV from Step 5
2. Set the correlation method (Pearson or Spearman) and threshold (default: 0.7)
3. Click **Run Analysis** — outputs:
   - Correlation heatmap (PNG)
   - Interactive HTML5 network (opens in your browser)
   - Module membership CSV (gene → module)

#### Step 6b — K-means Clustering (K-means Tab)

1. Load an expression CSV
2. Set K (number of clusters; start with K = 5–8)
3. Click **Run K-means** — outputs:
   - Cluster assignments CSV
   - Centroid profiles CSV
   - Spaghetti plot PNG (expression trajectories coloured by cluster)

---

### Using the CLI

After `pip install Cis-GS`, every GUI feature is available from the command line. Run `cis-gs` with no arguments to open the GUI, or pass a subcommand.

Get help for any command:
```bash
cis-gs --help
cis-gs tfdb --help
cis-gs search --help
```

#### Step 0 — Get TF Motifs

```bash
# Find your species code in PlantTFDB
cis-gs tfdb species --search arabidopsis     # → code: Ath
cis-gs tfdb species --search oryza           # → code: Osa
cis-gs tfdb species                          # list all 157+ species

# Download PlantTFDB motifs for your species
cis-gs tfdb download Ath -o ./motif_db

# Explore what TF families are available
cis-gs tfdb filter ./motif_db/Ath_TF_binding_motifs.meme --list-families

# Export motifs for a specific family
cis-gs tfdb filter ./motif_db/Ath_TF_binding_motifs.meme \
       --info ./motif_db/Ath_TF_binding_motifs_information.txt \
       --family MYB -o myb_motifs.txt

# For vertebrates / animals — list available datasets
cis-gs tfdb sources
cis-gs tfdb download-db jaspar2024_vertebrates -o ./motif_db
cis-gs tfdb download-db hocomoco_human -o ./motif_db

# Filter JASPAR by species
cis-gs tfdb filter ./motif_db/JASPAR2024_CORE_vertebrates_non-redundant.meme \
       --species "Homo sapiens" --family GATA -o gata_motifs.txt
```

The output motifs file (`myb_motifs.txt`) is tab-separated: `NAME<TAB>IUPAC_SEQUENCE` per line.

#### Step 1 — Download Genome from NCBI

Find your assembly accession at [ncbi.nlm.nih.gov/assembly](https://www.ncbi.nlm.nih.gov/assembly):

```bash
cis-gs fetch GCF_000001735.4 -o ./genome
```

Output files:
```
./genome/GCF_000001735.4_genomic.fasta
./genome/GCF_000001735.4_genomic.gff3
```

Options:
```bash
cis-gs fetch GCF_000001735.4 --no-fasta    # GFF3 only
cis-gs fetch GCF_000001735.4 --no-gff      # FASTA only
```

#### Step 2 — Extract Promoter Sequences

```bash
cis-gs extract ./genome/GCF_000001735.4_genomic.fasta \
               ./genome/GCF_000001735.4_genomic.gff3 \
               -l 1500 -o promoters.fasta
```

`-l 1500` extracts 1500 bp upstream per gene (default: 1000 bp). Output:
```
promoters.fasta    # one sequence per gene
promoters.tsv      # table: gene ID, chromosome, coordinates, strand
```

#### Step 3 — Scan for TFBS Motif Hits

```bash
# Using the motifs file from Step 0
cis-gs search promoters.fasta --motifs-file myb_motifs.txt -o hits.csv

# Or type motifs inline
cis-gs search promoters.fasta -m ACGTG -m RGATCY -o hits.csv

# Forward strand only
cis-gs search promoters.fasta --motifs-file myb_motifs.txt --no-revcomp
```

Output `hits.csv` columns: `gene_id, motif_name, pattern, strand, position, matched_seq`

#### Step 4 — Build Sequence Logos

```bash
cis-gs logo hits.csv -o ./logos
cis-gs logo hits.csv -o ./logos --scale probability
```

One PNG per motif name, saved to `./logos/`.

#### Step 5 — Filter Expression Data

```bash
cis-gs feed hits.csv expression.csv -o filtered_expr.csv
```

Gene ID prefix differences (`gene-`, `rna-`) and version suffixes (`.1`) are handled automatically.

Expression CSV format:
```
gene_id,0h,6h,12h,24h
AT1G00010,5.2,8.1,6.3,4.9
AT1G00020,1.1,1.3,1.2,1.0
```

#### Step 6a — Co-expression Network

```bash
cis-gs coexpr filtered_expr.csv -o ./coexpr_results

# Spearman correlation, stricter threshold
cis-gs coexpr filtered_expr.csv --method spearman --threshold 0.8 --hide-isolated
```

Output files in `./coexpr_results/`:
```
correlation_matrix.csv          pairwise correlation values
correlation_heatmap.png         heatmap image
module_membership.csv           gene → co-expression module
coexpression_network.html       interactive network (open in browser)
coexpression_network.png        static network image
```

#### Step 6b — K-means Clustering

```bash
cis-gs kmeans filtered_expr.csv -k 6 -o ./clusters
```

Output files:
```
kmeans_clusters.csv     gene → cluster assignment
kmeans_centroids.csv    mean expression profile per cluster
kmeans_plot.png         spaghetti plot of expression trajectories
```

#### Full One-liner Example

```bash
# Arabidopsis MYB binding site analysis — complete pipeline
cis-gs tfdb download Ath -o ./db
cis-gs tfdb filter ./db/Ath_TF_binding_motifs.meme \
       --info ./db/Ath_TF_binding_motifs_information.txt \
       --family MYB -o myb_motifs.txt
cis-gs fetch GCF_000001735.4 -o ./genome
cis-gs extract ./genome/GCF_000001735.4_genomic.fasta \
               ./genome/GCF_000001735.4_genomic.gff3 \
               -l 2000 -o promoters.fasta
cis-gs search promoters.fasta --motifs-file myb_motifs.txt -o myb_hits.csv
cis-gs logo myb_hits.csv -o ./logos
cis-gs feed myb_hits.csv expression.csv -o filtered_expr.csv
cis-gs coexpr filtered_expr.csv -o ./coexpr_results
cis-gs kmeans filtered_expr.csv -k 6 -o ./clusters
```

---

## Supported Motif Databases

| Database | Coverage | CLI Command |
|---|---|---|
| **PlantTFDB** | 157+ plant species | `cis-gs tfdb download <code>` |
| **JASPAR 2024 Vertebrates** | ~575 non-redundant profiles | `cis-gs tfdb download-db jaspar2024_vertebrates` |
| **JASPAR 2024 Insects** | ~99 non-redundant profiles | `cis-gs tfdb download-db jaspar2024_insects` |
| **HOCOMOCO v11 Human** | ~700 ChIP-Seq motifs | `cis-gs tfdb download-db hocomoco_human` |
| **HOCOMOCO v11 Mouse** | ~400 ChIP-Seq motifs | `cis-gs tfdb download-db hocomoco_mouse` |

---

## Data Formats

### Inputs

| Format | Used for |
|---|---|
| FASTA | Genome sequences (from NCBI) |
| GFF3 | Gene annotations (from NCBI) |
| IUPAC pattern | Motif consensus (e.g., `RGATCY`, `AACCGTTA`) |
| MEME | Position frequency matrices from PlantTFDB / JASPAR / HOCOMOCO |
| CSV | Gene expression matrix (genes × samples) |

### IUPAC Codes

```
R=A/G  Y=C/T  S=G/C  W=A/T  K=G/T  M=A/C
B=C/G/T  D=A/G/T  H=A/C/T  V=A/C/G  N=any
```

### Outputs

| File | Produced by |
|---|---|
| `promoters.fasta` | `extract` |
| `motif_hits.csv` | `search` |
| `logos/*.png` | `logo` |
| `filtered_expression.csv` | `feed` |
| `correlation_heatmap.png` | `coexpr` |
| `coexpression_network.html` | `coexpr` |
| `module_membership.csv` | `coexpr` |
| `kmeans_clusters.csv` | `kmeans` |
| `kmeans_plot.png` | `kmeans` |

---

## Requirements

- Python ≥ 3.8
- All dependencies install automatically via pip:

```
PyQt5, numpy, pandas, scipy, matplotlib, seaborn,
biopython, scikit-learn, logomaker, Pillow, networkx, python-louvain
```

---

## Citation

If you use Cis-GS in your research, please cite:

> [Authors] (2026). Cis-GS: A comprehensive tool for cis-regulatory element analysis across genomes. [Journal/Preprint]. DOI: [your-doi]

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contact

**Ayushman Mallick**
- GitHub: [github.com/Ayushmania2002](https://github.com/Ayushmania2002)
- LinkedIn: [linkedin.com/in/ayushman-mallick-68490922b](https://www.linkedin.com/in/ayushman-mallick-68490922b)
- Email: ayushmania2002@gmail.com

**Plant Signaling Lab**, IISER Tirupati
- Website: [srchoudhury0.wixsite.com/plant-signaling-lab](https://srchoudhury0.wixsite.com/plant-signaling-lab)

Bug reports & feature requests: [github.com/Ayushmania2002/Cis-GS/issues](https://github.com/Ayushmania2002/Cis-GS/issues)
