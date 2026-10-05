Step 2 — Motif Search
=====================

Scans every promoter for transcription-factor binding motifs and
tests every gene-motif pair against a composition-matched null model.

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

*Per promoter and motif strand* (the ``p_value`` column): the probability of
seeing at least :math:`k` matches of the motif in a promoter of length
:math:`L`, under a binomial model

.. math::

   p = P(X \geq k), \qquad X \sim \text{Binomial}(L - w + 1,\; q)

where :math:`w` is the motif length and :math:`q` is the probability that a
random sequence matches the (IUPAC) motif at one position, computed from **that
promoter's own base composition**. A GC-rich motif is therefore expected more
often in GC-rich promoters, which prevents spurious calls.

*Multiple testing* (``p_value_adj``): Benjamini-Hochberg over **all promoters x
motif strands scanned**, not only over the pairs that happen to contain a hit.
Individual occurrences of a short or degenerate motif are therefore rarely
significant on their own; that is expected.

*Motif-level enrichment*: ``cis-gs search`` also prints, for every motif
strand, the observed number of hits, the number expected under the same null,
the fold enrichment and a one-sided Poisson P-value. This is the appropriate
test for "is this motif enriched in these promoters at all?". In Python it is
available as ``df.attrs["motif_enrichment"]``.

.. note::

   Versions up to 1.3.2.3 estimated the background GC from the hit sequences
   and corrected only over the pairs with hits, which flagged nearly every
   hit as significant. Significance columns from those versions should not be
   compared with 1.3.2.4 and later.

Outputs
-------

* ``hits.csv`` — one row per hit with position, strand, matched sequence,
  ``p_value``, ``p_value_adj``, ``neg_log10_p`` and ``significance``.
* **Significance Summary** — collapsed table with one row per (gene x motif).

CLI equivalent
--------------

.. code-block:: bash

   cis-gs search promoters.fasta --motifs-file motifs.txt -o hits.csv

Gene-ID Resolution
------------------

Cis-GS adds three optional ID-mapping methods to bridge the common
NCBI ``LOC###`` ↔ species-database mismatch:

1. **Column swap** — append ``XM_`` / ``XP_`` accessions to the exported CSV.
2. **Mapping CSV** — user-supplied two-column lookup.
3. **GFF3 Dbxref expansion** — pull every synonym from ``Dbxref=`` and
   ``locus_tag=`` attributes in the annotation.
