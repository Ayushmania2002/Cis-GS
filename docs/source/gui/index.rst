GUI Overview
============

Cis-GS's PyQt5 desktop app organises every feature into nine top-level
tabs. The seven workflow tabs map 1:1 to the
:doc:`scientific pipeline <../workflow/index>`; two utility tabs handle
NCBI assembly browsing and contact / acknowledgement information.

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Tab
     - Section
     - Purpose
   * - **NCBI Fetch**
     - Utility
     - Live NCBI Assembly search + download
   * - **Step 1: Promoters**
     - Workflow
     - Extract upstream sequences
   * - **Step 2: Motif Search**
     - Workflow
     - Scan promoters; import from PlantTFDB / AnimalTFDB
   * - **Step 3: Motif Logos**
     - Workflow
     - Sequence-logo rendering
   * - **Step 4: Expression Feeding**
     - Workflow
     - Couple hits with an expression CSV
   * - **Step 5: Coexpression**
     - Workflow
     - Build network + detect modules
   * - **Step 6: K-means**
     - Workflow
     - Cluster expression profiles
   * - **Step 7: KEGG Enrichment**
     - Workflow
     - Pathway over-representation
   * - **Contact**
     - Utility
     - Author, lab, database links (with real brand icons)

Theme & shortcuts
-----------------

* **Settings → Toggle Theme** — switch light/dark (~10 ms with the v1.1
  pre-cached stylesheet swap).
* **Settings → Change Font Size** — global font scale.
* **Settings → Set NCBI Email** — required by Entrez.
* **Settings → Change Workspace** — relocates ``~/CisGS-Workspace/``.

A round teal ``?`` button in the top-right of every section opens
context-sensitive help.
