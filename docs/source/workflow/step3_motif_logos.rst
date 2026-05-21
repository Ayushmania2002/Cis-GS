Step 3 — Motif Logos
====================

Renders publication-quality sequence logos for every motif you scanned in
Step 2, using `logomaker <https://logomaker.readthedocs.io>`_ under the
hood.

Inputs
------

* The motif set imported in Step 2 (or any MEME / IUPAC list).

Settings
--------

* **Information-content shading** — characters scaled by Shannon entropy.
* **Colour scheme** — classic (A=green, C=blue, G=orange, T=red), Weblogo,
  Skylign, or grayscale.
* **Reverse-complement** — render the RC strand as a separate logo.

Outputs
-------

Per motif: ``logos/<motif>.svg`` and ``logos/<motif>.png``.
