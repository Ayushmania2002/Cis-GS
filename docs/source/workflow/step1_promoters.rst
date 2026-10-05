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
2. On the **+** strand, take the ``N`` bases immediately upstream of the gene
   start, ``[start - N, start)``.
3. On the **-** strand, take the ``N`` bases after the gene end,
   ``(end, end + N]``, and reverse-complement them.
4. Clip at chromosome ends (a promoter never runs past the sequence).

Promoters are cut out through a FASTA **offset index** (samtools ``.fai``
compatible). Only the requested intervals are read from disk, so a multi-Gb
genome is never loaded into memory. An existing ``genome.fa.fai`` is used
when present and newer than the FASTA; otherwise the index is built in memory
(a few seconds for a 2.6 Gb genome; nothing is written next to your file).
FASTA files with irregular line layouts fall back to a slower general reader.

Output
------

* ``promoters.fasta`` — one entry per gene; the header is
  ``gene_id|gene_name|chromosome:start-end(strand)``.
* ``promoters.tsv`` — one row per promoter with gene and promoter coordinates.

Performance
-----------

*Arachis hypogaea* Tifrunner (2.6 Gb, 106,608 genes, 2 kb promoters):
about 5 s and 0.4 GB of memory with a warm file cache (20 s on a first,
cold read), with output identical to bedtools ``getfasta``. See
:doc:`../performance` for the full comparison.

CLI equivalent
--------------

.. code-block:: bash

   cis-gs extract genome.fa annot.gff3 -l 2000 -o promoters.fasta
