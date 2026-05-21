Step 6 — K-means Clustering
===========================

Partitions genes into ``k`` co-regulated groups based on their expression
profiles across samples / conditions.

Inputs
------

* The expression matrix from Step 4 / 5.

Settings
--------

* **k** — number of clusters. Use the elbow + silhouette plot to pick.
* **Max iterations** — default 300.
* **Random seed** — deterministic by default (seed = 42), exposed for
  reproducibility.

Diagnostics
-----------

* **Elbow plot** — within-cluster SSE vs k for k = 2 … 15.
* **Silhouette plot** — mean silhouette score vs k.

Outputs
-------

* ``clusters/cluster_1.txt`` … ``cluster_k.txt`` — gene lists per cluster.
* ``cluster_centers.png`` — average expression profile per cluster.
