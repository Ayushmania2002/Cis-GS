The Wizard
==========

.. code-block:: bash

   cis-gs wizard

Launches an interactive walkthrough of every Cis-GS workflow. The
wizard:

* Guides you through each step with numbered prompts and sensible defaults.
* Accepts free-form paths, IDs, and parameters with inline validation.
* Mirrors the GUI experience for headless servers and HPC nodes.

You can launch a specific workflow directly:

.. code-block:: bash

   cis-gs wizard                 # top-level menu - pick a workflow
   cis-gs wizard kegg            # KEGG enrichment (live organism picker)
   cis-gs wizard id-convert      # Gene-ID conversion
   cis-gs wizard feed            # Expression feeding
   cis-gs wizard coexpr          # Co-expression network
   cis-gs wizard kmeans          # K-means clustering
   cis-gs wizard fetch           # NCBI genome fetch
   cis-gs wizard extract         # Promoter extraction (Step 1)
   cis-gs wizard search          # Motif search (Step 2)
   cis-gs wizard batch           # Multi-species batch (Steps 1+2)

Available workflows
-------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Workflow
     - Description
   * - ``kegg``
     - KEGG pathway over-representation with live organism search (~11,700 entries)
   * - ``id-convert``
     - Translate gene IDs between LOC, Ensembl, Entrez, and symbol formats
   * - ``feed``
     - Filter an expression matrix to genes with motif hits
   * - ``coexpr``
     - Build a co-expression network and detect Louvain modules
   * - ``kmeans``
     - K-means clustering with optional elbow-method auto-k
   * - ``fetch``
     - Download genome FASTA + GFF3 from NCBI Assembly by organism name
   * - ``extract``
     - Extract upstream promoter sequences from a genome FASTA + GFF3
   * - ``search``
     - Scan promoters for IUPAC motif hits
   * - ``batch``
     - Run extraction + search for **multiple species** from a single manifest file

Multi-species batch wizard
--------------------------

The ``batch`` wizard (new in v1.3.0) automates Steps 1 and 2 for any number of
species in a single run. Prepare a tab-separated manifest file:

.. code-block:: text

   # species_name<TAB>fasta_path<TAB>gff3_path[<TAB>upstream_bp]
   O. sativa      /data/rice.fa        /data/rice.gff3        2000
   A. hypogaea    /data/peanut.fa      /data/peanut.gff3      2000
   M. truncatula  /data/medicago.fa    /data/medicago.gff3    2000

Then run:

.. code-block:: bash

   cis-gs wizard batch
   # or non-interactively:
   cis-gs batch species.tsv --motifs-file motifs.txt -o batch_out/

Output files written to the output directory:

- ``<species>_promoters.fa`` - extracted promoters per species
- ``<species>_hits.csv``     - motif hits per species
- ``batch_hits.csv``         - combined hits for all species (``species`` column added)
