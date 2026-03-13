# RNA-seq Expression and Differential Analysis

This directory contains scripts for transcriptomic analysis of inoculated
versus control plant samples, including differential expression, visualization,
and cross-species gene mapping.

Two species are analysed independently:
- Lotus japonicus (reference RNA-seq quantification)
- Arachis hypogaea (time-course differential expression)

Expression-derived candidate genes are later used for cis-element analysis
and co-expression network construction.

---

## Biological context

- Inoculated samples correspond to rhizobial-treated plants
- Control samples represent uninoculated conditions
- Differential expression is assessed using log2 fold change
- Stringent filtering is applied to remove lowly expressed genes

---

## Execution order

1. Quantify Lotus RNA-seq reads using Kallisto  
2. Compute differential expression (inoculated vs control)  
3. Generate volcano plots and Venn diagrams  
4. Analyse Arachis time-course RNA-seq data  
5. Identify conserved genes across Lotus and Arachis  

---

## Notes

- FASTQ, FASTA, and annotation files are expected under `data/`
- Absolute file paths have been intentionally avoided
- Scripts are modular and can be executed independently

