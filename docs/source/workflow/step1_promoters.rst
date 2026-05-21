Step 1 — Promoter Extraction
============================

Pulls the upstream region of every gene out of a genome FASTA, using the
coordinates and strand information from a matching GFF3 annotation.

Inputs
------

* **Genome FASTA** — any standard ``.fa`` / ``.fasta`` / ``.fa.gz``.
* **Annotation GFF3** — NCBI RefSeq, Ensembl, or any GFF3 that contains
  ``gene`` features with ``ID=`` attributes.
* **Promoter length** (bp) — default 2000.

What it does
------------

For every ``gene`` feature in the GFF3:

1. Read the gene's chromosome, start, end, and strand.
2. On the **+** strand, take ``[start - upstream, start)``.
3. On the **-** strand, take ``(end, end + upstream]`` and reverse-complement.
4. Clip at neighbouring gene boundaries (intergenic only) if the
   *"Avoid overlapping genes"* box is checked.

Output
------

* ``promoters.fa`` — one entry per gene; FASTA header is the gene ID,
  optionally prefixed with chromosome and coordinate range.

CLI equivalent
--------------

.. code-block:: bash

   cis-gs extract --fasta genome.fa --gff annot.gff3 \
                  --upstream 2000 --avoid-overlap --out promoters.fa
