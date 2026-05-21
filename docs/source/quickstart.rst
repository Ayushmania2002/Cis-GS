Quick Start
===========

A 60-second tour of both the GUI and the CLI.

GUI in 5 clicks
---------------

.. code-block:: bash

   cis-gs-gui

1. **Step 1 — Promoters**: drop a FASTA + GFF3, set promoter length, click *Extract*.
2. **Step 2 — Motif Search**: click *Import from PlantTFDB*, pick your species, tick motifs, *Import Selected → Step 2*.
3. **Step 2 (still)**: click *Scan* — hits CSV with hypergeometric p-values appears.
4. **Step 7 — KEGG Enrichment**: select a KEGG organism from the live dropdown, paste your gene list, *Run*.
5. Done — CSVs and SVGs land in ``~/CisGS-Workspace/``.

CLI wizard
----------

.. code-block:: bash

   cis-gs wizard

The wizard auto-detects what you already produced and offers the next
sensible step. Arrow keys to navigate, *Enter* to confirm.

One-liner CLI examples
----------------------

Extract 2 kb promoters:

.. code-block:: bash

   cis-gs extract --fasta genome.fa --gff annot.gff3 \
                  --upstream 2000 --out promoters.fa

Scan with a MEME motif file:

.. code-block:: bash

   cis-gs search --promoters promoters.fa --motifs motifs.meme \
                 --out hits.csv

Convert NCBI Gene IDs → Ensembl in one batched request:

.. code-block:: bash

   cis-gs id-convert --species human --target ensembl \
                     --infile genes.txt --out ensembl.csv

KEGG enrichment on the top module:

.. code-block:: bash

   cis-gs enrich-kegg --organism ath --genes top_module.txt \
                      --out kegg.csv

Every command supports ``-i / --interactive`` to be walked through it.
