# Cis-GS — Technical Documentation
### Cis-regulatory Element Genome Scanner
**Version 1.0.0** | Plant Signaling Lab, IISER Tirupati
**Author:** Ayushman Mallick | ayushmania2002@gmail.com

---

## Table of Contents

1. [Software Overview](#1-software-overview)
2. [Architecture and Technology Stack](#2-architecture-and-technology-stack)
3. [Module 0 — NCBI Genome Fetcher](#3-module-0--ncbi-genome-fetcher)
4. [Module 1 — Promoter Extraction Engine](#4-module-1--promoter-extraction-engine)
5. [Module 2 — TFBS Motif Scanner](#5-module-2--tfbs-motif-scanner)
6. [Module 3 — Sequence Logo Builder](#6-module-3--sequence-logo-builder)
7. [Module 4 — Expression Feeding](#7-module-4--expression-feeding)
8. [Module 5 — Co-expression Network Analysis](#8-module-5--co-expression-network-analysis)
9. [Module 6 — K-means Temporal Clustering](#9-module-6--k-means-temporal-clustering)
10. [TF Database Integration](#10-tf-database-integration)
11. [Chromosome Visualization](#11-chromosome-visualization)
12. [Statistical Framework](#12-statistical-framework)
13. [Command-Line Interface](#13-command-line-interface)
14. [Data Formats](#14-data-formats)
15. [Dependencies and Rationale](#15-dependencies-and-rationale)

---

## 1. Software Overview

Cis-GS (Cis-regulatory Element Genome Scanner) is a standalone desktop application designed for the systematic, genome-wide identification and functional characterization of cis-regulatory elements (CREs) — specifically transcription factor binding sites (TFBS) — in genomic promoter sequences. It integrates a seven-step bioinformatics pipeline, three external TF motif databases, statistical enrichment analysis, gene expression integration, and network-level co-regulatory analysis into a single unified interface.

### Motivation

Regulatory genomics research typically requires chaining together multiple external tools — NCBI genome download utilities, custom GFF parsers, MEME/FIMO for motif scanning, R or Python scripts for expression analysis, Cytoscape or custom code for network visualization — with no standardized interface between them. Cis-GS eliminates this fragmentation by implementing every step internally, with seamless data flow between modules, within a desktop application that runs entirely offline after the initial genome and database downloads.

### Design Philosophy

- **End-to-end**: Every step from genome retrieval to network visualization is implemented natively — no external tool calls
- **Genome-wide scale**: All operations (promoter extraction, motif scanning) process the entire genome at once, not gene-by-gene
- **Dual interface**: Full GUI for interactive use and a complete CLI for scripting and remote server execution
- **Database-integrated**: Direct in-app access to PlantTFDB, JASPAR 2024, and HOCOMOCO v11 without leaving the application

---

## 2. Architecture and Technology Stack

### Application Framework

Cis-GS is built on **PyQt5**, a Python binding for the Qt5 cross-platform framework. The application follows a tabbed multi-panel architecture where each analysis module occupies its own tab, implemented as a subclass of a custom `BackgroundWidget` base class. All computationally intensive operations run in `QThread` background workers, keeping the GUI responsive during long operations.

### Threading Model

```
MainWindow (QMainWindow)
│
├── QTabWidget
│   ├── NCBITab          ← DownloadWorkerThread (QThread)
│   ├── Step1Tab         ← WorkerThread (QThread)
│   ├── Step2Tab         ← WorkerThread (QThread)
│   ├── Step3Tab         ← WorkerThread (QThread)
│   ├── ExpressionFeedingTab
│   ├── CoexpressionTab  ← WorkerThread (QThread)
│   ├── KMeansClusteringTab ← WorkerThread (QThread)
│   ├── HelpTab
│   └── ContactTab
```

Worker threads emit `pyqtSignal` objects (`progress`, `result`, `error`) to communicate back to the GUI thread, following Qt's signal-slot mechanism. This prevents any analysis step from blocking the event loop.

### Theme System

A `ThemeManager` class manages two complete visual themes (dark/light) by manipulating `QPalette` colour roles at the application level:

- `QPalette.Window`, `QPalette.Base`, `QPalette.AlternateBase`
- `QPalette.Text`, `QPalette.ButtonText`, `QPalette.Button`
- `QPalette.Highlight`, `QPalette.HighlightedText`

Theme preferences are persisted to a JSON settings file in the user's home directory (`~/CisGS-Workspace/settings.json`) and restored on next launch.

### Core Technology Stack

| Component | Library | Version |
|---|---|---|
| GUI framework | PyQt5 | ≥ 5.15 |
| Sequence parsing | Biopython | ≥ 1.79 |
| Numerical computing | NumPy | ≥ 1.21 |
| Data manipulation | Pandas | ≥ 1.3 |
| Plotting | Matplotlib + Seaborn | ≥ 3.3 / 0.11 |
| Sequence logos | logomaker | ≥ 0.8 |
| Machine learning | scikit-learn | ≥ 1.0 |
| Network analysis | NetworkX | ≥ 2.6 |
| Community detection | python-louvain | ≥ 0.15 |
| Statistical computing | SciPy | ≥ 1.7 |
| Image processing | Pillow | ≥ 9.0 |

---

## 3. Module 0 — NCBI Genome Fetcher

### Function: `search_ncbi_assemblies(organism_name, max_results=20)`

Queries the NCBI Assembly database using Biopython's `Entrez.esearch()` with the `assembly` database type. Returns a list of assembly records with fields: accession number, organism name, assembly level (Complete/Chromosome/Scaffold/Contig), and submission date. Up to 20 results are returned by default, rendered in a sortable `QTableWidget`.

### Function: `detect_accession_type(query)`

Disambiguates whether a user-supplied string is a GCF/GCA assembly accession, a chromosome-level RefSeq accession (NC_XXXXXX), a nucleotide accession (NW_, NZ_), or a free-text organism name. Routes appropriately to either direct FTP download or an Entrez search.

### Function: `download_assembly_files(assembly_accession, download_fasta, download_gff, progress_callback, cancel_flag)`

The core genome download function. Implements the following steps:

1. **Assembly report retrieval**: Queries `Entrez.esummary()` for the assembly to obtain the FTP directory path on the NCBI RefSeq server
2. **FTP path construction**: Constructs URLs for the genomic FASTA (`.fna.gz`) and GFF3 annotation (`.gff.gz`) from the assembly report
3. **Chunked HTTP download**: Calls `_download_url_chunked()` — downloads in 256 KB chunks, calling `progress_callback(bytes_received, total_bytes, label)` after each chunk to update the progress bar in real-time
4. **Cancellation**: Checks `cancel_flag` (a mutable dict `{'cancel': False}`) after each chunk; sets by the Stop button in the UI
5. **Decompression**: Decompresses `.gz` files in memory using Python's `gzip` module
6. **Content validation**: Verifies that the downloaded content is valid FASTA or GFF3 by checking for expected header tokens

The download worker (`DownloadWorkerThread`) runs the entire process in a `QThread`, emitting `progress(int, int, str)` signals to update the UI progress bar and a `stop_btn` to cancel mid-download.

### NCBI Email Management

NCBI's Entrez API requires a registered email. Cis-GS stores the user's email in `~/CisGS-Workspace/.ncbi_email` and prompts for it on first use via `prompt_email_dialog()`. The email is set on `Bio.Entrez.email` before every API call.

---

## 4. Module 1 — Promoter Extraction Engine

### Function: `parse_gff3_genes(gff_path, feature_preference="gene")`

Parses a GFF3 annotation file and extracts all protein-coding gene records. Implementation details:

- Reads GFF3 line by line; skips comment lines (`#`)
- Filters for `feature_type == "gene"` (or "mRNA" as fallback if no gene features found)
- Parses the `attributes` column (column 9) using regex to extract `ID=`, `Name=`, `gene=`, and `locus_tag=` fields
- Strand is preserved (`+` or `-`)
- Chromosome/sequence identifiers are extracted from column 1
- Returns a list of `GeneRecord` dataclass objects: `(gene_id, chromosome, start, end, strand)`

### Function: `build_transcript_map_from_gff3(gff_path)`

Builds a secondary gene ID mapping for expression data cross-referencing. Extracts all synonym identifiers from GFF3 attributes — `ID`, `Name`, `gene`, `locus_tag`, `old_locus_tag`, `gene_synonym` — and maps all aliases to a canonical ID. This resolves the common problem where the genome annotation uses `gene-AT1G00010` but the expression dataset uses `AT1G00010`.

### Function: `extract_promoters(genome_fasta, gff3, out_fasta, out_table, promoter_len=1000)`

The main promoter extraction function. Algorithm:

1. **Genome indexing**: Loads the genome FASTA using `Bio.SeqIO.to_dict()` — indexes all chromosome sequences in memory by their sequence ID for O(1) lookup
2. **GFF3 parsing**: Calls `parse_gff3_genes()` to get all gene records
3. **Coordinate calculation**: For each gene:
   - **Forward strand (+)**: Promoter = `[TSS - promoter_len : TSS]` where TSS = `gene.start`
   - **Reverse strand (−)**: Promoter = `[TES : TES + promoter_len]` where TES = `gene.end`; sequence is then reverse-complemented
   - Boundary clipping: if the upstream region extends beyond chromosome start (position < 0), it is clipped to position 0 with a warning
4. **Output**: Writes a multi-FASTA file (one sequence per gene, header = gene ID) and a TSV summary table with columns: `gene_id`, `chromosome`, `promoter_start`, `promoter_end`, `strand`, `length`

This function processes every gene in the genome in a single pass — typical Arabidopsis genomes (~27,000 genes) complete in under 30 seconds.

---

## 5. Module 2 — TFBS Motif Scanner

### IUPAC Pattern Expansion: `iupac_to_regex(seq)`

Converts an IUPAC degenerate nucleotide string into a Python regular expression. The full IUPAC-to-regex mapping:

```
R → [AG]    Y → [CT]    S → [GC]    W → [AT]
K → [GT]    M → [AC]    B → [CGT]   D → [AGT]
H → [ACT]   V → [ACG]   N → [ACGT]
A → A       C → C       G → G       T → T
```

Example: `RGATCY` → `[AG]GATC[CT]`

The resulting regex is compiled with `re.compile()` and applied using `re.finditer()` with `overlapping=True` support (implemented by advancing one character at a time to capture overlapping matches).

### Function: `scan_fasta_for_motifs(fasta_path, motifs, treat_as_iupac, allow_overlaps, search_revcomp)`

The core genome-wide scanning engine. For each sequence in the promoter FASTA:

1. **Forward strand scan**: Applies compiled regex for each motif pattern to the sequence
2. **Reverse complement scan** (if `search_revcomp=True`): Generates the reverse complement using `str(Seq(seq).reverse_complement())` and scans again; positions are re-mapped to forward-strand coordinates
3. **Hit recording**: Each hit records:
   - `gene_id` — parsed from FASTA header using `record_to_gene_id()`
   - `motif_name` — user-supplied name
   - `pattern` — original IUPAC pattern
   - `strand` — `+` or `-`
   - `position` — 0-based position within the promoter
   - `matched_seq` — the actual matched nucleotide sequence
   - `p_value` — computed statistical significance (see below)

### Statistical Significance: `_motif_match_prob()` and `add_pvalues_to_hits()`

For each motif hit, Cis-GS computes an approximate p-value representing the probability of observing that hit by chance given the background nucleotide composition.

**Background model**: A binomial/Bernoulli model using the GC content of the input promoter sequences. For each IUPAC position, the probability of a match is computed from `_motif_match_prob()`:

- Each IUPAC symbol maps to a set of matching bases
- The probability of matching at a single position = sum of background frequencies of matching bases
- The overall motif match probability = product across all positions (independence assumption)
- The expected number of hits in a sequence of length L = `L × match_prob`
- p-value (Poisson approximation) = `1 - e^(-expected)` for at least one hit

**Multiple testing correction**: After scanning, `add_pvalues_to_hits()` applies the Benjamini-Hochberg FDR correction across all hits using `scipy.stats.false_discovery_rate` — producing adjusted q-values alongside raw p-values in the output CSV.

**Significance classification**: Hits are labelled as:
- `***` p < 0.001
- `**`  p < 0.01
- `*`   p < 0.05
- `ns`  p ≥ 0.05

### Motif Input Parsing: `parse_motif_lines(text)`

Parses the motif text box in the GUI, supporting three formats:

- `NAME<TAB>SEQUENCE` — standard tab-separated format
- `NAME: SEQUENCE` — colon-separated format
- `SEQUENCE` alone — auto-generates a name (`motif_1`, `motif_2`, ...)
- Lines starting with `#` are treated as comments

---

## 6. Module 3 — Sequence Logo Builder

### Functions: `probs_from_iupac_motif()`, `probs_from_sequences()`, `probs_to_bits()`, `render_logo_to_png()`

Sequence logos are generated using the **logomaker** library, which produces publication-quality SVG/PNG figures conforming to the Schneider & Stephens (1990) information-content framework.

**Frequency matrix construction** (`probs_from_sequences()`):
1. Input: a list of aligned nucleotide sequences of equal length (the `matched_seq` values from the hit CSV, filtered to a single length)
2. Counts matrix: a (L × 4) matrix where L = motif length, columns = [A, C, G, T]
3. Pseudocount: 0.5 added to each cell to avoid log(0)
4. Probability matrix: row-normalized counts matrix

**Information content** (`probs_to_bits()`):
- For each position i: `IC(i) = 2 + Σ p(b,i) × log₂(p(b,i))` for b ∈ {A,C,G,T}
- Maximum IC = 2 bits (perfectly conserved position)
- The bits matrix = `p(b,i) × IC(i)` per cell

**Rendering** (`render_logo_to_png()`):
- Calls `logomaker.Logo(matrix, color_scheme='classic')` for the standard nucleotide colour scheme (A=green, C=blue, G=orange, T=red)
- Scale: either `bits` (information content, y-axis 0–2 bits) or `probability` (y-axis 0–1)
- Output: rendered to a `BytesIO` buffer as PNG via `matplotlib.figure.savefig()`
- Displayed inline in the GUI via `QPixmap.loadFromData()`

**Length-based filtering**: The Step 3 tab allows the user to filter hits by exact matched sequence length before building the logo, enabling separate logos for each motif length variant (e.g., 8-mer vs 9-mer hits from the same IUPAC pattern with length ambiguity).

---

## 7. Module 4 — Expression Feeding

### Class: `ExpressionFeedingTab`

This module bridges the TFBS scan results with gene expression data, implementing robust gene ID normalization to handle the systematic discrepancy between NCBI genome annotation identifiers and identifiers used in RNA-seq quantification datasets.

### Gene ID Normalization Pipeline

The function `_normalize_gene_id_for_map()` applies the following transformations in order:

1. **Prefix stripping**: Removes `gene-`, `rna-`, `cds-`, `Gene:`, `GENE:` prefixes (common in NCBI GFF3-derived IDs)
2. **Delimiter splitting**: Splits on `|`, ` `, `\t`, `:`, `;` and takes the first token
3. **Version stripping**: Removes `.1`, `.2` etc. suffixes (e.g., `AT1G00010.1` → `AT1G00010`)
4. **Case normalization**: Lowercased for comparison

### Matching Algorithm

For each gene ID in the motif hit table:
1. Normalize the ID
2. Look up in the normalized expression index (built once at load time from the expression CSV row labels)
3. If not found: attempt base match (strip version suffix and retry)
4. If still not found: flag as unmatched

The result is a filtered expression sub-matrix containing only genes with at least one TFBS hit, exported as a CSV ready for downstream network or clustering analysis.

### Expression Data Validation

- Checks that all expression columns are numeric (non-numeric columns are flagged with a warning)
- Detects and reports the matching rate (e.g., "312 of 450 motif-hit genes found in expression dataset")
- Optionally generates example expression data (`generate_example_expression_data()`) with realistic time-course profiles for testing and demonstration

---

## 8. Module 5 — Co-expression Network Analysis

### Function: `calculate_correlation_matrix(expr_df, method='pearson')`

Computes a symmetric (n_genes × n_genes) pairwise correlation matrix.

- **Pearson**: `pandas.DataFrame.corr(method='pearson')` — measures linear co-expression, appropriate for normally distributed TPM/RPKM data
- **Spearman**: `pandas.DataFrame.corr(method='spearman')` — rank-based, more robust to outliers and non-linear relationships; preferred for raw count data or data with many zeroes

Both methods return values in [-1, 1]. The absolute value is used for edge weight (both positive and negative co-expression are biologically meaningful).

### Function: `detect_coexpression_modules(corr_matrix, threshold=0.7)`

Builds a weighted gene co-expression network and detects modules:

1. **Thresholding**: Creates a NetworkX `Graph` where an edge `(i, j)` is added if `|correlation(i,j)| ≥ threshold`. Edge weight = correlation value.
2. **Louvain community detection**: Applies `community.best_partition(G)` from `python-louvain`, which implements the Louvain method (Blondel et al., 2008) — a greedy modularity optimization algorithm
   - Time complexity: O(n log n) — scales well to hundreds of genes
   - Returns a partition dict `{gene: module_id}`
   - Modularity Q is maximized iteratively by moving nodes between communities
3. **Isolated node handling**: Genes below the correlation threshold with all others remain as singletons (module = -1); optionally hidden from visualization

### Function: `render_correlation_heatmap(corr_matrix, output_path)`

Renders the correlation matrix as a clustered heatmap using `seaborn.clustermap()`:
- Hierarchical clustering applied to both rows and columns using Ward linkage
- Diverging colour palette (blue–white–red) centred at 0
- Dendrogram displayed on both axes
- Saved as PNG at 150 DPI

### Function: `create_interactive_network_html(G, communities, output_path, hide_isolated)`

Generates a fully self-contained HTML5 network visualization using the **Vis.js** library (embedded inline — no internet required to view):

- Nodes: one per gene, coloured by module ID (up to 20 distinct colours from a curated palette)
- Edges: one per correlated gene pair above threshold, weight proportional to correlation value
- Physics engine: Barnes-Hut gravity simulation for force-directed layout
- Interactivity: zoom, pan, drag individual nodes, hover for gene name tooltip, click to highlight neighbours
- Module legend rendered as a colour key

### Function: `render_network_plot(G, communities, output_path, hide_isolated)`

Static PNG network for publication, rendered with NetworkX + Matplotlib:
- Spring layout (`nx.spring_layout()` with seed for reproducibility)
- Node size proportional to degree (more connected genes appear larger)
- Colour by module
- Edge alpha proportional to correlation weight

---

## 9. Module 6 — K-means Temporal Clustering

### Function: `kmeans_temporal_clustering(expr_df, n_clusters, n_init=50, selected_samples, random_state=42)`

Clusters genes by expression trajectory across time points or conditions.

**Pre-processing**:
1. **Sample selection**: User optionally selects a subset of columns (time points) to use for clustering
2. **Z-score normalization**: `StandardScaler()` from scikit-learn — each gene's expression vector is mean-centred and unit-variance scaled. This ensures clustering is driven by expression pattern shape rather than absolute expression level (a highly expressed gene with a flat profile should not cluster with a lowly expressed gene with the same flat profile due to absolute level)

**Clustering**:
- `sklearn.cluster.KMeans(n_clusters=k, n_init=50, random_state=42)`
- `n_init=50`: runs K-means 50 times with different random centroid initializations, selects the run with lowest inertia (sum of squared distances to centroids) — critical for avoiding local minima
- `init='k-means++'`: uses the K-means++ initialization strategy (Arthur & Vassilvitskii, 2007) to spread initial centroids, substantially improving convergence speed and solution quality compared to random initialization

**Outputs**:
- `cluster_labels`: Series mapping gene_id → cluster ID
- `centroids`: DataFrame of shape (k × n_samples) — the mean expression profile for each cluster (in original, unscaled space for interpretability)
- `inertia`: within-cluster sum of squares (used for elbow method)
- `silhouette_score`: mean silhouette coefficient across all samples (measure of cluster cohesion vs. separation; range −1 to 1, higher is better)

### Function: `elbow_method_kmeans(expr_df, max_k=15)`

Runs K-means for K = 1 to max_k, recording inertia at each K. Plots the "elbow curve" — the point of maximum curvature in the inertia vs. K plot suggests the optimal number of clusters. Computed and displayed as a diagnostic aid before the user commits to a K value.

### Function: `plot_kmeans_spaghetti(expr_df, kmeans_result, output_path)`

Generates a multi-panel spaghetti plot — one subplot per cluster — showing:
- Each gene's normalized expression trajectory as a thin semi-transparent line (alpha=0.3)
- The cluster centroid as a thick bold line (the archetype trajectory for that module)
- X-axis: time points / sample labels
- Y-axis: Z-score normalized expression
- Colour: each cluster assigned a distinct colour from a palette

This visualization allows immediate visual assessment of cluster coherence and identification of biologically meaningful patterns (early induction, late induction, transient response, sustained repression, oscillatory, etc.).

---

## 10. TF Database Integration

### PlantTFDB

**Module**: `planttfdb_importer.py`

**Live species list**: `fetch_species_list()` scrapes `planttfdb.gao-lab.org/download.php` using `urllib.request` with a browser `User-Agent` header, parsing `.meme.gz` download link filenames to extract species codes and names. Falls back to a built-in catalogue of 89 species if the server is unreachable.

**Download**: `_DownloadWorker` (QThread) tries four server URLs in order (HTTPS/HTTP × 2 mirrors), downloading `.meme.gz` first, decompressing with Python's `gzip` module, then downloading the companion `_information.txt` annotation file. Progress emitted as `(percent, message)` signals.

**MEME file parsing**: `parse_meme_file()` reads the MEME format:
- `MOTIF gene_id matrix_id` — start of a new motif block
- `letter-probability matrix: w=N nsites=N E=N` — PFM header
- Following rows: space-separated A C G T probability values

**IUPAC conversion**: `pfm_to_iupac(pfm, threshold=0.25)`:
- For each position: compute max probability across bases
- Include all bases with probability ≥ `max(threshold, max_p × 0.30)`
- Map the included base set to the IUPAC code using a frozenset lookup table
- Threshold is user-configurable (0.20 relaxed → 0.40 very strict)

**Annotation enrichment**: `parse_info_file()` reads the tab-separated `_information.txt` file, providing TF Family, experimental method (ChIP-Seq, DAP-Seq, SELEX, Y1H), species name, and data source ID for each motif.

---

### JASPAR 2024 and HOCOMOCO v11

**Module**: `animaltfdb_importer.py`

Four datasets are pre-configured with primary and fallback download URLs:

| Dataset ID | Source | Motifs | Format |
|---|---|---|---|
| `jaspar2024_vertebrates` | EMBL-EBI / jaspar.elixir.no | ~575 | ZIP → MEME |
| `jaspar2024_insects` | EMBL-EBI / jaspar.elixir.no | ~99 | ZIP → MEME |
| `hocomoco_human` | hocomoco11.autosome.org | ~700 | MEME |
| `hocomoco_mouse` | hocomoco11.autosome.org | ~400 | MEME |

JASPAR ZIPs are extracted in memory using Python's `zipfile` module. HOCOMOCO annotation files (TF family, ChIP-Seq quality tier A/B/C/D) are downloaded separately and merged with the MEME data.

Both databases use the same `parse_meme_file()` and `pfm_to_iupac()` functions as PlantTFDB, since all three use the MEME Position Frequency Matrix format.

**Motif browser**: Both importers share a common `MotifBrowserWidget` with:
- QSortFilterProxyModel for real-time filtering by family, method, species, or keyword
- Checkable rows for motif selection
- Column-level background colouring by TF family using a curated colour palette
- IUPAC threshold selector (recomputes consensus on-the-fly without re-downloading)
- "Import Selected → Step 2" button to transfer motifs directly into the scan tab

---

## 11. Chromosome Visualization

**Module**: `chromosome_utils.py`

### Function: `extract_chromosome_from_record_id(record_id)`

Maps NCBI RefSeq accession identifiers (e.g., `NC_003070.9`) to chromosome names (e.g., `Chr1`) using a curated lookup table covering major plant and animal model organisms. Falls back to regex extraction of the numeric suffix.

### Function: `plot_chromosome_with_hits(df, chromosome, output_path)`

Generates a chromosome ideogram plot showing the positions of all TFBS hits along a chromosome:
- Chromosome drawn as a scaled rectangle proportional to its length in bp
- Each TFBS hit marked as a vertical tick at its genomic coordinate
- Hits coloured by motif name
- Density track (KDE) overlaid to show hotspot regions of TFBS clustering

This visualization reveals whether TFBS hits are uniformly distributed across the genome or clustered in specific chromosomal regions — a pattern that may indicate chromatin accessibility or genomic context effects.

---

## 12. Statistical Framework

### Background Model for TFBS Significance

Cis-GS uses an analytical (non-permutation) approach for p-value estimation:

**Null hypothesis**: The observed motif hit is due to random sequence composition matching the background nucleotide frequencies of the input promoter set.

**Model**:
- Background GC content (gc) is computed from all promoter sequences combined
- Per-base background: P(G) = P(C) = gc/2; P(A) = P(T) = (1-gc)/2
- Per-position match probability: product of background frequencies of IUPAC-matching bases
- Whole-motif match probability: product across all positions (independence)
- Expected hits in a sequence of length L: λ = L × p_match
- P(at least one hit) ≈ 1 − e^(−λ) [Poisson approximation]

**Multiple testing**: Benjamini-Hochberg FDR correction applied across all hits in the output table. Adjusted q-values are reported alongside raw p-values.

**Limitation**: This model assumes positional independence (no dinucleotide or higher-order dependencies), which is a standard approximation. For more rigorous enrichment testing, users can compare hit frequencies against a shuffled-sequence background using the CLI.

---

## 13. Command-Line Interface

**Module**: `cis_gs/cli.py`

The CLI wraps every GUI function using `argparse` with sub-subparsers, covering 11 distinct commands:

```
cis-gs                         Launch GUI
cis-gs fetch                   NCBI genome download
cis-gs extract                 Promoter extraction
cis-gs search                  TFBS motif scanning
cis-gs logo                    Sequence logo generation
cis-gs feed                    Expression data filtering
cis-gs coexpr                  Co-expression network
cis-gs kmeans                  K-means clustering
cis-gs tfdb species            List PlantTFDB organisms
cis-gs tfdb download           Download PlantTFDB MEME
cis-gs tfdb sources            List JASPAR/HOCOMOCO datasets
cis-gs tfdb download-db        Download JASPAR/HOCOMOCO
cis-gs tfdb filter             Filter MEME and export motifs
```

Each command mirrors its GUI equivalent exactly — the CLI calls the same underlying Python functions. This means any analysis reproducible in the GUI is identically reproducible from a shell script, enabling pipeline automation and integration with workflow managers (Snakemake, Nextflow, etc.).

All commands implement:
- `--help` with detailed usage, examples, and output file descriptions
- Informative error messages with `# Tip:` guidance explaining common failure modes
- Progress reporting to stdout for long-running steps (download, scan)

---

## 14. Data Formats

### Input

| Format | Specification | Used By |
|---|---|---|
| FASTA | Standard multi-FASTA, any line length | Promoter extraction, motif scan |
| GFF3 | NCBI GFF3 with column-9 attribute parsing | Promoter extraction |
| MEME | MEME PFM format v4 | PlantTFDB / JASPAR / HOCOMOCO import |
| IUPAC string | Standard IUPAC nucleotide codes | Motif scan |
| Expression CSV | Genes × samples, first column = gene IDs | Expression feeding, coexpr, kmeans |

### Output

| File | Format | Contents |
|---|---|---|
| `promoters.fasta` | Multi-FASTA | One promoter sequence per gene |
| `promoters.tsv` | TSV | gene_id, chr, start, end, strand, length |
| `motif_hits.csv` | CSV | gene_id, motif_name, pattern, strand, position, matched_seq, p_value, q_value, significance |
| `logos/<name>.png` | PNG | Sequence logo (bits or probability scale) |
| `filtered_expression.csv` | CSV | Expression submatrix for motif-hit genes |
| `correlation_matrix.csv` | CSV | n_genes × n_genes pairwise correlations |
| `correlation_heatmap.png` | PNG | Clustered heatmap (Ward linkage) |
| `module_membership.csv` | CSV | gene_id, module |
| `coexpression_network.html` | HTML5 | Self-contained interactive Vis.js network |
| `coexpression_network.png` | PNG | Static network (spring layout) |
| `kmeans_clusters.csv` | CSV | gene_id, cluster |
| `kmeans_centroids.csv` | CSV | k × n_samples centroid profiles |
| `kmeans_plot.png` | PNG | Multi-panel spaghetti plot |

---

## 15. Dependencies and Rationale

| Library | Why This Library |
|---|---|
| **PyQt5** | Mature, cross-platform GUI framework; threading via QThread; native look-and-feel on Win/Mac/Linux |
| **Biopython** | Gold-standard for NCBI Entrez API access, FASTA/GFF parsing, sequence reverse-complement |
| **logomaker** | Purpose-built for sequence logos; information-content correct; matplotlib-based for easy PNG export |
| **NetworkX** | De-facto standard for graph construction, layout, and analysis in Python |
| **python-louvain** | Efficient Louvain modularity optimization; well-tested on biological networks |
| **scikit-learn** | K-means++ implementation with n_init robustness; StandardScaler for z-score normalization |
| **Matplotlib + Seaborn** | Publication-quality figures; seaborn clustermap for hierarchically clustered heatmaps |
| **SciPy** | Hierarchical clustering (Ward linkage), statistical distributions for p-value computation |
| **Pandas** | Efficient in-memory data manipulation for large expression matrices and hit tables |
| **NumPy** | Vectorized operations on expression matrices and correlation computations |
| **Pillow** | PNG encoding and decoding for in-GUI image display |

---

*Cis-GS v1.0.0 — Plant Signaling Lab, IISER Tirupati*
*Ayushman Mallick | ayushmania2002@gmail.com*
*github.com/Ayushmania2002/Cis-GS*
