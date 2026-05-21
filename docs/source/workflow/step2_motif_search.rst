Step 2 — Motif Search
=====================

Scans every promoter for transcription-factor binding motifs and
computes a hypergeometric over-representation p-value per motif.

Inputs
------

* **Target FASTA** — usually the ``promoters.fa`` from Step 1.
* **Motifs** — any combination of:

  * Free-text IUPAC consensus (one per line, ``NAME SEQ``)
  * MEME file
  * Live import from **PlantTFDB** (157 species), **AnimalTFDB** (vertebrates
    + insects), **JASPAR 2024**, or **HOCOMOCO v11**.

Statistics
----------

For each motif:

.. math::

   p = P(X \geq k) \;\text{where}\; X \sim \text{Hypergeom}(N, K, n)

with

.. list-table::
   :widths: 20 80

   * - :math:`N`
     - Total number of promoters
   * - :math:`K`
     - Number of promoters in which the motif occurs at least once
   * - :math:`n`
     - Number of *query* promoters (e.g. a K-means cluster from Step 6)
   * - :math:`k`
     - Number of *query* promoters with a hit

Multiple-testing correction: Benjamini-Hochberg (``cis_gs.enrichment.core.bh_fdr``).

Outputs
-------

* ``hits.csv`` — one row per gene × motif, with hit position, strand, raw and
  adjusted p-value.
* **Significance Summary** — collapsed table with one row per (gene × motif).

Gene-ID Resolution
------------------

Cis-GS adds three optional ID-mapping methods to bridge the common
NCBI ``LOC###`` ↔ species-database mismatch:

1. **Column swap** — append ``XM_`` / ``XP_`` accessions to the exported CSV.
2. **Mapping CSV** — user-supplied two-column lookup.
3. **GFF3 Dbxref expansion** — pull every synonym from ``Dbxref=`` and
   ``locus_tag=`` attributes in the annotation.
