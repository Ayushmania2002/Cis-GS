# Biopython-CYC-re-Genome-Scanning
Genome-wide identification and analysis of CYCLOPS-responsive cis-elements in Arachis hypogaea

# Genome-wide Identification of CYCLOPS-Responsive Cis-Acting Regulatory Elements in *Arachis hypogaea*

## Overview

This repository contains the complete computational pipeline used in the study:

**“Genome-wide identification and functional analysis of CYCLOPS-responsive cis-acting regulatory elements in *Arachis hypogaea*.”**

The pipeline implements a systematic, genome-wide strategy to identify cis-acting regulatory elements (CREs) associated with the CYCLOPS transcription factor, evaluate their conservation and binding potential using position weight matrices (PWMs), integrate gene expression and co-expression analyses, and visualise cis-element distributions relative to genomic features.

All scripts are modular, reproducible, and organised to directly reflect the *Materials and Methods* section of the associated manuscript.

---

## Repository Structure

The repository is organised as a multi-stage analysis pipeline, with each directory corresponding to a defined analytical step.


### `src/` – Core analysis pipeline

Scripts are numbered to indicate execution order:

1. **01_genome_preprocessing**
   - Parsing GFF3 annotations
   - Strand normalization
   - Extraction of promoter regions

2. **02_cis_element_detection**
   - Construction of degenerate motif variants
   - Genome-wide motif scanning
   - Mapping motif hits to genomic coordinates

3. **03_pwm_analysis**
   - Position Weight Matrix (PWM) construction
   - Log-likelihood ratio (LLR) scoring
   - KDE-based motif strength visualisation

4. **04_expression_analysis**
   - Expression data normalization
   - Differential expression analysis
   - Expression clustering and plotting

5. **05_coexpression_analysis**
   - Co-expression matrix construction
   - Threshold selection
   - Network analysis and visualisation

6. **06_functional_annotation**
   - Automated retrieval of gene annotations from NCBI
   - Functional summary generation

7. **07_visualisation**
   - Chromosome-level cis-element distribution plots
   - Gene-level, zoomed visualisations
   - Figure export scripts

---

## Data Availability

Due to file size constraints, large input datasets are **not hosted** in this repository.

The following data were obtained from publicly available resources:

- Genome FASTA files: PeanutBase / Phytozome
- Gene annotations (GFF3): Phytozome v13
- Expression datasets: Public RNA-seq repositories

Detailed instructions and source links are provided in:

