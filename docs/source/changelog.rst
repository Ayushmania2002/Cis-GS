Changelog
=========

v1.3.2.5 — 2026-10
------------------

**Fixes**

* ``cis-gs extract`` and ``cis-gs batch`` now reverse-complement minus-strand
  promoters with the full IUPAC complement table. Previously only A, C, G, T
  and N were complemented and any other ambiguity code (R, Y, K, M, B, D, H,
  V) was left unchanged. The effect is limited to promoters that contain
  ambiguity codes (1 of 33,623 promoters in the rice IRGSP-1.0 RefSeq genome);
  all other promoters were already identical to bedtools and seqkit output.
  The GUI was not affected.
* ``cis-gs --help`` no longer crashes on consoles that use the Windows cp1252 code
  page (a non-ASCII arrow in one help string); the CLI now substitutes any
  character the console cannot print.

----

v1.3.2.4 — 2026-10
------------------

**Fixes**

* ``cis-gs extract`` and ``cis-gs batch`` no longer fail with
  ``'str' object has no attribute 'open'`` (path arguments are now coerced
  to ``Path``).
* **Motif significance model corrected.** The per-promoter binomial test now
  uses each promoter's own base composition (previously a single GC value
  estimated from the hit sequences themselves), and the Benjamini-Hochberg
  correction is applied over all promoters x motif strands scanned
  (previously only over pairs that already had a hit, which flagged nearly
  every hit as significant). The set of hits is unchanged; the ``p_value``,
  ``p_value_adj`` and ``significance`` columns change, so results from
  earlier versions should not be compared directly. Validated on
  composition-preserving shuffled promoter sets (no false positives).

**Features**

* ``cis-gs search`` now reports a motif-level enrichment summary (observed
  versus expected hits under the composition-matched null) and the number
  of hits significant at FDR <= 0.05.

**Performance**

* Promoter extraction reads through a FASTA offset index (samtools ``.fai``
  compatible, built in memory if absent) instead of loading whole
  chromosomes. On the 2.6 Gb *Arachis hypogaea* genome (106,608 promoters)
  extraction dropped from ~63 s / 1.9 GB to ~5 s / 0.4 GB with
  byte-identical output. The GUI build previously re-read the chromosome
  for every gene and benefits as well. Irregular FASTA layouts fall back to
  the previous reader.
* Motif scanning parses the FASTA once instead of once per motif.

----

v1.3.2.3 — 2026-08
------------------

**Fixes**

* Fixed a severe performance bug in the Step 2 motif-search significance
  (p-value / FDR) calculation: the per-gene/motif p-value lookup re-scanned
  the *entire* hits table on every iteration (an accidental O(n²) pattern),
  which could hang indefinitely on genome-wide promoter sets with a short,
  common motif (e.g. a 5 bp IUPAC pattern against 100,000+ promoters).
  Replaced with a precomputed lookup dict and vectorized pandas indexing.
  Verified on a 106,608-promoter genome-wide run: full scan + significance
  calculation now completes in ~21 seconds (previously did not finish after
  30+ minutes).

----

v1.3.2.2 — 2026-06
------------------

**Fixes**

* Cleaned up the ``authors`` / ``maintainers`` fields in
  ``pyproject.toml`` so that the package's ``Author`` metadata renders
  cleanly as ``Ayushman Mallick`` on PyPI and pepy.tech. The
  ``Plant Signaling Lab, IISER Tirupati`` attribution is now carried in
  the ``Maintainer`` field, eliminating comma-driven truncation issues
  on third-party indexes.

----

v1.3.2.1 — 2026-06
------------------

**Fixes**

* Replaced broken shields.io ``pypi/dt`` downloads badge with the
  pepy.tech all-time downloads badge in the README, ensuring the
  downloads counter renders correctly on both GitHub and PyPI.

----

v1.3.2 — 2026-06
----------------

**Fixes**

* Corrected PyPI author metadata — ``Author`` field now correctly displays
  the authors on PyPI and
  pypistats.org.

----

v1.3.1 — 2026-06
----------------

**Fixes**

* First attempt at PyPI author field correction (superseded by v1.3.2).

----

v1.3.0 — 2026-06
----------------

**Highlights**

* **Multi-species batch mode** — new ``cis-gs batch`` subcommand accepts a
  tab-separated manifest file (species, FASTA path, GFF3 path, optional
  upstream bp) and runs promoter extraction + motif search for every species
  in a single automated pass, writing per-species hit CSVs and a combined
  ``batch_hits.csv`` with a ``species`` column.
* **Batch wizard** — ``cis-gs wizard batch`` provides a step-by-step
  interactive guide for the new batch workflow, consistent with all other
  wizard commands.

**Documentation**

* Added ``cis-gs batch`` to the CLI command reference.
* Rewrote the Wizard page with a full workflow table and dedicated
  multi-species batch section.
* Added missing ``cis-gs logo`` command to the CLI reference (was
  implemented but not documented).

----

v1.2.0 — 2026-05
----------------

**Highlights**

* **37× faster Louvain clustering** — replaced the O(N²) Python double loop
  for co-expression graph construction with NumPy vectorised masking
  (``np.triu``), and switched the community-detection backend from
  ``python-louvain`` + NetworkX to the ``igraph`` C-library
  (``community_multilevel``).  Louvain time for *A. hypogaea* (56 513 genes)
  dropped from ~150 s to ~4 s.
* **igraph added as a dependency** — ``igraph >= 0.11`` added to
  ``pyproject.toml``; ``python-louvain`` retained as fallback.
* **PyInstaller bundle updated** — ``igraph`` and ``igraph._igraph`` added to
  ``hiddenimports`` in ``Cis-GS.spec``; Windows ``.exe`` rebuilt and uploaded
  to the v1.2.0 GitHub release.

**Performance (benchmarked)**

* Promoter extraction: 11–87 s across four genome assemblies (O(C) disk reads,
  where C = chromosome count).
* Motif scanning: 6–18 s scaling linearly with sequence count.
* KEGG REST retrieval: 5–8 s on first use; < 30 ms on subsequent calls via
  local disk cache (229–311× speedup).
* Full co-expression pipeline (normalisation → Pearson → Louvain → k-means):
  77–159 s per species.

**Fixes**

* All em dashes replaced with hyphens throughout GUI and CLI output.
* ``scan_fasta_for_motifs`` import aligned with the canonical function name
  in ``cis_gs.app``.

----

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

----

v1.0.0 — 2026-03
----------------

Initial public release.

* Seven-step pipeline: Promoters → Motifs → Logos → Expression →
  Coexpression → K-means → Enrichment.
* PlantTFDB importer.
* PyQt5 GUI + first-cut CLI.
* Standalone Windows ``.exe`` via PyInstaller.
