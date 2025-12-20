# Co-expression Analysis of CYCLOPS-Associated Genes

This directory contains scripts used to perform gene co-expression analysis
centered on the CYCLOPS gene (XM_025842227), using normalized RNA-seq expression
profiles across multiple post-inoculation time points.

The analysis integrates correlation-based network construction, module detection,
and downstream visualization (performed in `src/07_visualisation/`).

---

## Input Data

The co-expression pipeline requires the following inputs:

- `WGCNA_expression_matrix.csv`  
  A gene × condition expression matrix generated in  
  `src/04_expression_analysis/prepare_coexpression_matrix.py`

- Expression values correspond to multiple time points
  (e.g. 0 dpi, 6 dpi, 10 dpi, 15 dpi, 21 dpi)

- Gene identifiers are harmonized (version numbers removed, consistent XM IDs)

---

## Analysis Workflow and Execution Order

Scripts in this directory should be executed in the order listed below.

---

### 1️ `correlation_matrix.py`

**Purpose:**  
Compute pairwise Pearson correlation coefficients between all genes
based on their expression profiles.

**Key steps:**
- Remove genes with missing or zero-variance expression
- Calculate gene–gene correlation matrix
- Save correlation matrix for downstream network analysis

**Output:**
- `correlation_matrix.csv`

---

### 2️ `tom_analysis.py`

**Purpose:**  
Estimate network connectivity using a WGCNA-like Topological Overlap Matrix (TOM).

**Key steps:**
- Convert correlation matrix to adjacency matrix
- Apply soft-thresholding (β parameter)
- Compute TOM to capture shared network neighbors
- Diagnose and remove NaN or unstable entries

**Output:**
- `TOM_matrix.csv`

**Note:**  
This implementation follows the conceptual framework of WGCNA,
but is implemented manually in Python for transparency and flexibility.

---

### 3️ `cyclops_centered_network.py`

**Purpose:**  
Identify genes co-expressed with CYCLOPS.

**Key steps:**
- Compute correlation of each gene with CYCLOPS expression profile
- Apply correlation threshold (e.g. r ≥ 0.7)
- Construct a CYCLOPS-centered co-expression network

**Output:**
- Filtered gene lists
- Network object for visualization

---

### 4️ `module_detection_louvain.py`

**Purpose:**  
Detect co-expression modules using graph-based community detection.

**Key steps:**
- Build gene co-expression graph from correlation matrix
- Apply Louvain community detection
- Assign module labels to each gene
- Export gene lists per module

**Outputs:**
- `module_<ID>_genes.csv` files

---

## Visualization (Performed Separately)

Visualization scripts are located in: src/07_visualisation


