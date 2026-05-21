NCBI Fetch Tab
==============

Live search against the NCBI Assembly database — type an organism name,
filter by RefSeq / GenBank / assembly level, and download the genome
FASTA and GFF3 in one click.

Search strategies
-----------------

1. **RefSeq first** (``GCF_``-prefixed, annotated) — preferred for
   downstream annotation work.
2. **GenBank fallback** (``GCA_``) if no RefSeq hit exists.
3. **Taxonomy-only** — if the user knows a Taxonomy ID, skips assembly
   search entirely.

Outputs
-------

Files land in ``~/CisGS-Workspace/<organism>/`` with the assembly
accession in the filename:

* ``GCF_000004515.6_<asm_name>_genomic.fna``
* ``GCF_000004515.6_<asm_name>_genomic.gff``

A status panel shows progress and any retries.

.. note::

   First-time users must set an NCBI email under
   **Settings → Set NCBI Email**. Entrez rejects requests without one.
