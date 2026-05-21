Step 5 — Co-expression Network
==============================

Builds a gene-gene correlation network from your expression matrix and
detects modules (communities of co-regulated genes).

Inputs
------

* The expression matrix carried over from Step 4 (or any CSV).

Pipeline
--------

1. **Normalisation** — log2(x+1), variance-stabilising, or none.
2. **Similarity** — Pearson, Spearman, or biweight midcorrelation.
3. **Adjacency** — soft threshold (WGCNA-style :math:`a_{ij} = |r_{ij}|^\beta`)
   or hard threshold (binary above a cutoff).
4. **Module detection** — Louvain, Leiden (if installed), or hierarchical
   clustering with dynamic tree cut.
5. **Eigengene** — first principal component per module, plotted across
   samples.

Outputs
-------

* ``network.gexf`` — for Cytoscape / Gephi.
* ``modules.csv`` — gene → module assignment.
* ``eigengenes.png`` — eigengene heat-map.
