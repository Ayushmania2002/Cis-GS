Step 7 — KEGG Enrichment
========================

Tests whether a gene list is over-represented in any KEGG pathway, using a
one-sided hypergeometric test with Benjamini-Hochberg FDR. All data is
fetched **live** from the KEGG REST API — no shipped 5 GB SQLite bundle.

Inputs
------

* **Organism** — pick from the live KEGG dropdown (11 700+ organisms).
  Three-letter codes: ``hsa`` = human, ``mmu`` = mouse, ``ath`` =
  Arabidopsis, ``ahf`` = peanut, etc.
* **Query gene list** — paste, file, or output from any earlier step.
* **Background** *(optional)* — defaults to every KEGG-annotated gene for
  the chosen organism.

Statistics
----------

.. math::

   p = P(X \geq k) \;\text{where}\; X \sim \text{Hypergeom}(N, K, n)

with one-sided over-representation filter
:math:`\frac{k}{n} > \frac{n_\text{query}}{N}` and fold-enrichment

.. math::

   \mathrm{FE} = \frac{k / n_\text{query}}{n / N}

REST endpoints used
-------------------

* ``/list/pathway/<org>`` — pathway IDs and descriptions
* ``/link/<org>/pathway`` — gene ↔ pathway membership
* ``/conv/<org>/<ns>:<id>`` — namespace conversion (Ensembl / NCBI Gene / UniProt → KEGG)

All responses are cached under ``~/.cis-gs/kegg/`` so the second call on
the same organism is instantaneous.

Output
------

``kegg_enrichment.csv`` columns: ``term, description, k, list_n, n, total_n,
fold_enrichment, p_value, q_value, genes``.

CLI equivalent
--------------

.. code-block:: bash

   cis-gs enrich-kegg --organism ath --genes top_module.txt \
                      --min-overlap 2 --min-set-size 5 \
                      --out kegg.csv
