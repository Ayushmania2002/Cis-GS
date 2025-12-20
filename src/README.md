# Source Code Structure and Execution Order

This directory contains all scripts used for genome-wide cis-regulatory element
discovery, transcriptomic filtering, coexpression network analysis, and
functional annotation of CYCLOPS-associated genes.

Scripts are organised into numbered folders reflecting the recommended
execution order of the analysis pipeline.

---

## Execution Order Overview

Scripts should be executed sequentially following the folder numbering below.
Downstream analyses depend on outputs generated in earlier steps.

---

## 01_data_preprocessing/

**Purpose:**  
Prepare genome annotations and retrieve sequence data required for promoter
analysis and cross-species comparisons.

**Key scripts:**
- `add_arahy_prefix.py` — 
- `extract_cis_in_genes.py` — extracts cis element sequences in the 2 kb upstream promoter 

**Outputs:**  
Processed annotation files, promoter FASTA sequences, and transcript FASTA files.

---

## 02_cis_element_detection/

**Purpose:**  
Identify cis-regulatory elements in promoter regions using motif-based searches.

**Key scripts:**
- `build_motif_variants.py` — generates motif variants
- `scan_cis_elements.py` — scans promoter sequences for cis-elements
- `map_genomic_coordinates.py` — maps motif positions to genomic coordinates

**Outputs:**  
CSV files containing cis-element positions and gene associations.

---

## 03_pwm_analysis/

**Purpose:**  
Quantify cis-element binding strength using position weight matrices (PWM).

**Key scripts:**
- `build_pwm.py`
- `pwm_scoring.py`
- `pwm_kde_plots.py`

**Outputs:**  
PWM score tables and binding affinity distribution plots.

---

## 04_expression_analysis/

**Purpose:**  
Analyse RNA-seq datasets and identify differentially expressed genes following
inoculation, including cross-species comparisons.

**Key analyses implemented:**
- Transcript quantification using Kallisto
- TPM-based expression comparison
- Log2 fold-change estimation
- Differential expression filtering
- Cross-species BLAST-based gene mapping

**Representative scripts:**
- `kallisto_quantification.py`
- `tpm_log2fc_analysis.py`
- `deg_classification.py`
- `blast_cross_species_mapping.py`
- `arachis_deg_analysis.py`

**Outputs:**  
Differentially expressed gene lists, log2FC tables, and cross-species gene matches.

---

## 05_coexpression_analysis/

**Purpose:**  
Construct and analyse coexpression networks to identify genes co-regulated with
CYCLOPS across time-course expression data.

**Key analyses implemented:**
- Expression matrix cleaning and harmonisation
- Pearson correlation-based coexpression
- WGCNA-like topological overlap (TOM) analysis
- Cyclops-centered coexpression networks
- Louvain community (module) detection

**Representative scripts:**
- `prepare_expression_matrix.py`
- `build_coexpression_matrix.py`
- `network_analysis.py`
- `network_plots.py`

**Outputs:**  
Coexpression matrices, network graphs, module assignments, and gene clusters.

---

## 06_functional_annotation/

**Purpose:**  
Assign functional annotations to shortlisted genes using sequence similarity and
database-based annotations.

**Key scripts:**
- `blast_search.py`
- `annotation_summary.py`
- `export_modules.py`

**Outputs:**  
Annotated gene tables and functional summaries.

---

## 07_visualisation/

**Purpose:**  
Generate publication-quality figures for transcriptomic and network analyses.

**Key scripts:**
- `gene_level_visualisation.py`
- `network_plots.py`
- `figure_exports.py`

**Outputs:**  
Figures used directly in the manuscript, including volcano plots and
coexpression network visualisations.

---

## Notes

- Not all scripts are required to reproduce every figure.
- Exploratory and parameter-testing steps are retained for transparency.
- All figures and tables in the manuscript can be traced to scripts in this
  repository.
