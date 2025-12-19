# Source Code Structure and Execution Order

This directory contains all scripts used for genome-wide cis-element discovery,
expression-based filtering, functional annotation, and visualisation.

Scripts are organised into numbered folders reflecting the recommended
execution order of the analysis pipeline.

---

## Execution Order Overview

Scripts should be executed sequentially following the folder numbering below.
Downstream analyses assume outputs generated in earlier steps.

---

## 01_genome_preprocessing/

**Purpose:**  
Prepare genome annotation and extract promoter regions for downstream analysis.

**Key scripts:**
- `parse_gff.py` — parses genome annotation files
- `extract_promoters.py` — extracts promoter sequences
- `strand_normalization.py` — ensures strand-consistent coordinates

**Outputs:**  
Processed annotation files and promoter FASTA sequences.

---

## 02_cis_element_detection/

**Purpose:**  
Identify cis-regulatory elements in promoter regions using motif-based searches.

**Key scripts:**
- `build_motif_variants.py` — generates motif variants
- `scan_cis_elements.py` — scans promoter sequences
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
PWM score tables and distribution plots.

---

## 04_expression_analysis/

**Purpose:**  
Filter candidate genes based on tissue-specific and time-course expression profiles.

**Key scripts:**
- `prepare_expression_data.py` — converts raw expression data to analysis-ready format
- `normalize_expression.py`
- `differential_expression.py`
- `expression_clustering.py`
- `expression_plots.py`

**Outputs:**  
Expression-filtered gene lists and heatmaps.

---

## 05_coexpression_analysis/

**Purpose:**  
Construct and analyse co-expression networks to identify CYCLOPS-associated modules.

**Key scripts:**
- `build_coexpression_matrix.py`
- `threshold_selection.py`
- `network_analysis.py`
- `network_plots.py`

**Outputs:**  
Co-expression matrices and network visualisations.

---

## 06_functional_annotation/

**Purpose:**  
Assign functional information to shortlisted genes using NCBI resources.

**Key scripts:**
- `extract_gene_sequences.py`
- `blast_search.py`
- `ncbi_entrez_fetch.py`
- `annotation_summary.py`

**Outputs:**  
Annotated gene tables and functional descriptions.

---

## 07_visualisation/

**Purpose:**  
Generate chromosome-level and gene-level visual representations of cis-elements.

**Key scripts:**
- `chromosome_visualisation.py`
- `gene_level_visualisation.py`
- `figure_exports.py`

**Outputs:**  
Publication-quality figures used in the manuscript.

---

## Notes

- Not all scripts are mandatory for reproducing every figure.
- Exploratory analyses are provided for transparency.
- All figures and tables in the manuscript can be traced to scripts in this directory.

