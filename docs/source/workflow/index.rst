The 7-Step Workflow
===================

Cis-GS organises every analysis into seven numbered steps that mirror the
tabs in the GUI. Each step writes to ``~/CisGS-Workspace/`` so you can
pause, swap tools, and resume.

.. list-table::
   :widths: 8 28 32 32
   :header-rows: 1

   * - #
     - Step
     - What it does
     - Key output
   * - 1
     - :doc:`Promoters <step1_promoters>`
     - Strand-aware promoter extraction from FASTA + GFF3
     - ``promoters.fa``
   * - 2
     - :doc:`Motif Search <step2_motif_search>`
     - IUPAC / MEME / PlantTFDB / AnimalTFDB scanning with hypergeom p-vals
     - ``hits.csv``
   * - 3
     - :doc:`Motif Logos <step3_motif_logos>`
     - logomaker sequence logos with IC shading
     - per-motif SVG / PNG
   * - 4
     - :doc:`Expression Feeding <step4_expression>`
     - Joins hits with an expression CSV via 3 ID-mapping methods
     - ``expression_matched.csv``
   * - 5
     - :doc:`Coexpression <step5_coexpression>`
     - Pearson / Spearman / WGCNA soft-threshold, Louvain modules
     - ``network.gexf``
   * - 6
     - :doc:`K-means <step6_kmeans>`
     - Elbow + silhouette, deterministic seeding
     - ``clusters/*.txt``
   * - 7
     - :doc:`KEGG Enrichment <step7_kegg>`
     - Live REST query, hypergeom ORA, BH-FDR
     - ``kegg_enrichment.csv``

Each step is independent — you can start at any point if you already
have the inputs that step expects.
