Changelog
=========

v1.1.0 — 2026-05
----------------

**Highlights**

* Live KEGG organism dropdown (11 700+ organisms, fetched via REST).
* Live NCBI Taxonomy search in both GUI and CLI.
* 60× faster MyGene.info ID conversion via batched POST.
* Interactive CLI ``wizard`` plus ``-i / --interactive`` on every command.
* Fuzzy "did you mean…?" for CLI typos.
* Modern single-colour theme (``#16A085`` teal) with instant theme
  swap (pre-cached stylesheet, ``setUpdatesEnabled`` freeze).
* First-run NCBI email prompt.
* Three Gene-ID-Mapping methods (column swap, mapping CSV, GFF3 Dbxref
  expansion).
* Real brand-icon Contact tab.

**Removed**

* GO enrichment (KEGG-only for now).
* Public RNA-seq import tab.
* All ShinyGO / iDEP attribution.

**Fixes**

* Dark-mode label visibility in PlantTFDB / AnimalTFDB pop-up dialogs.
* Thin rectangular ``?`` buttons in Step 2.
* Expression-Feeding tab section overlap (now scrollable).
* Tab labels no longer clip ("NCBI Fetc", "Step 1: Promoter").
* Theme switch no longer freezes the UI for 1-2 s.

v1.0.0 — 2026-03
----------------

Initial public release.

* Seven-step pipeline: Promoters → Motifs → Logos → Expression →
  Coexpression → K-means → Enrichment.
* PlantTFDB importer.
* PyQt5 GUI + first-cut CLI.
* Standalone Windows ``.exe`` via PyInstaller.
