The Wizard
==========

.. code-block:: bash

   cis-gs wizard

Launches an interactive walkthrough of the entire 7-step pipeline. The
wizard:

* Auto-detects what you've already produced in ``~/CisGS-Workspace/``.
* Offers the next sensible step (e.g. *"You already ran Step 2; want to
  run Step 3 logos now?"*).
* Uses arrow keys + Enter for every choice — no flag memorisation.
* Falls back to text input where free-form values are required.
* Saves your last answers to ``~/CisGS-Workspace/.wizard_state`` so a
  re-run resumes where you left off.

Sample session
--------------

.. code-block:: text

   $ cis-gs wizard

   Welcome to Cis-GS v1.1.0
   --------------------------
   Which step would you like to run?

     > 1. Promoter extraction
       2. Motif search
       3. Motif logos
       4. Expression feeding
       5. Co-expression network
       6. K-means clustering
       7. KEGG enrichment

   [Enter] continue   [q] quit
