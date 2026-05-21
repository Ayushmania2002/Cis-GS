Cis-GS Documentation
====================

**Cis-regulatory Element Genome Scanner** — a whole-genome pipeline for
discovering cis-regulatory elements, coupling them to expression, and
finishing with KEGG enrichment, in one PyQt5 desktop app *and* one
interactive CLI.

.. image:: https://img.shields.io/pypi/v/cis-gs.svg?color=16A085
   :target: https://pypi.org/project/cis-gs/
.. image:: https://img.shields.io/pypi/pyversions/cis-gs.svg
   :target: https://pypi.org/project/cis-gs/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://github.com/Ayushmania2002/Cis-GS/blob/main/LICENSE

----

Quick links
-----------

* :doc:`installation` — pip, standalone .exe, from source
* :doc:`quickstart` — one-minute GUI + CLI walkthrough
* :doc:`workflow/index` — the 7-step scientific pipeline
* :doc:`gui/index` — every tab of the PyQt5 desktop app explained
* :doc:`cli/index` — `cis-gs` command reference
* :doc:`api/index` — programmatic Python API

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: Scientific Workflow

   workflow/index
   workflow/step1_promoters
   workflow/step2_motif_search
   workflow/step3_motif_logos
   workflow/step4_expression
   workflow/step5_coexpression
   workflow/step6_kmeans
   workflow/step7_kegg

.. toctree::
   :maxdepth: 2
   :caption: GUI

   gui/index
   gui/ncbi_fetch
   gui/contact_tab

.. toctree::
   :maxdepth: 2
   :caption: CLI

   cli/index
   cli/wizard
   cli/commands

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/enrichment
   api/idmap

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
   contributing
   citation


Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
