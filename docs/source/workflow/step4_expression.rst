Step 4 — Expression Feeding
===========================

Joins the motif-hits table with your own expression data (RNA-seq,
microarray, qPCR) so you can ask *"do my motif-bearing genes actually
respond?"*.

Inputs
------

* ``hits.csv`` from Step 2.
* **Expression CSV** — first column = gene ID, remaining columns =
  samples / conditions (counts, TPM, log2FC — anything numeric).

Gene-ID Mapping Methods
-----------------------

Expression tables and annotation GFF3s rarely use the same ID space.
Cis-GS offers three matching strategies:

1. **Method 1 — Column swap.** Pick the expression column that already
   matches your annotation IDs (e.g. ``LOC112706767``).
2. **Method 2 — Mapping CSV.** Supply a two-column lookup
   (``annotation_id, expression_id``).
3. **Method 3 — GFF3 Dbxref expansion.** Cis-GS parses every
   ``Dbxref=`` and ``locus_tag=`` from the GFF3 and tries each synonym
   against the expression IDs automatically.

Outputs
-------

* ``expression_matched.csv`` — hits joined with their expression values.
* Per-motif direction-of-effect plot (boxplot of expression of
  motif-bearing vs motif-free genes).
