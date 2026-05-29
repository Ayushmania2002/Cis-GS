Command Reference
=================

cis-gs fetch
------------

.. code-block:: bash

   cis-gs fetch --organism "Arabidopsis thaliana" --out ./refs/

Searches NCBI Assembly, picks the latest RefSeq, downloads FASTA + GFF3.

cis-gs extract
--------------

.. code-block:: bash

   cis-gs extract --fasta genome.fa --gff annot.gff3 \
                  --upstream 2000 [--avoid-overlap] --out promoters.fa

cis-gs search
-------------

.. code-block:: bash

   cis-gs search --promoters promoters.fa --motifs motifs.meme \
                 [--allow-overlap] [--rc] --out hits.csv

cis-gs batch
------------

.. code-block:: bash

   cis-gs batch species.tsv --motifs-file motifs.txt
   cis-gs batch species.tsv --motifs-file motifs.txt -o results/ --upstream 1500

Runs promoter extraction (Step 1) and motif search (Step 2) for every species
listed in a tab-separated manifest file, then writes per-species hit CSVs and a
combined ``batch_hits.csv`` with an extra ``species`` column.

Manifest format (tab-separated, one species per line):

.. code-block:: text

   # species_name<TAB>fasta<TAB>gff3[<TAB>upstream_bp]
   O. sativa     /data/rice.fa      /data/rice.gff3      2000
   A. hypogaea   /data/peanut.fa    /data/peanut.gff3    2000

Options:

- ``--motifs-file FILE``  Motifs file - ``NAME<TAB>IUPAC_PATTERN`` per line (required)
- ``-o / --out DIR``      Output directory (default: ``batch_out/``)
- ``--upstream BP``       Default upstream length when not specified per row (default: 2000)

Interactive: ``cis-gs wizard batch``

cis-gs logo
-----------

.. code-block:: bash

   cis-gs logo hits.csv
   cis-gs logo hits.csv -o ./logos --scale probability
   cis-gs logo hits.csv --length 9

Generates sequence logo images (PNG) from the ``matched_seq`` column of a
motif hit CSV produced by ``cis-gs search``. One PNG is written per motif:
``logos/logo_<motif_name>.png``.

Options:

- ``-o / --outdir DIR``  Output directory (default: ``logos/``)
- ``--scale``            y-axis scale: ``bits`` (information content, default) or ``probability``
- ``--length N``         Only include sequences of exactly N bp (useful when a motif has length-variable hits)

cis-gs feed
-----------

.. code-block:: bash

   cis-gs feed --hits hits.csv --expression expr.csv \
               [--mapping mapping.csv] [--gff3 annot.gff3] \
               --out matched.csv

cis-gs coexpr
-------------

.. code-block:: bash

   cis-gs coexpr --expression expr.csv \
                 [--method pearson|spearman] \
                 [--soft-power 6] \
                 [--module-method louvain|hierarchical] \
                 --out network.gexf

cis-gs kmeans
-------------

.. code-block:: bash

   cis-gs kmeans --expression expr.csv -k 6 \
                 [--seed 42] [--elbow] --out clusters/

cis-gs enrich-kegg
------------------

.. code-block:: bash

   cis-gs enrich-kegg --organism ath --genes top_module.txt \
                      [--background bg.txt] \
                      [--min-overlap 2] [--min-set-size 5] \
                      --out kegg.csv

cis-gs id-convert
-----------------

.. code-block:: bash

   cis-gs id-convert --species human --target ensembl \
                     --infile genes.txt --out ensembl.csv

Routes through MyGene.info via a batched POST (chunks of 1 000 IDs) with
a live progress bar. ~60× faster than the legacy per-ID GET.
