Installation
============

Cis-GS ships in three flavours. Pick whichever matches your situation.

.. contents:: :local:

From PyPI (recommended)
-----------------------

.. code-block:: bash

   pip install cis-gs

That installs both entry points:

.. code-block:: bash

   cis-gs --help          # interactive CLI
   cis-gs-gui             # PyQt5 GUI

Requires **Python 3.9 or newer**.

Standalone Windows executable
-----------------------------

Grab ``Cis-GS.exe`` from the latest
`GitHub release <https://github.com/Ayushmania2002/Cis-GS/releases>`_.
Double-click — no Python install required. ~120 MB single file.

From source (for development)
-----------------------------

.. code-block:: bash

   git clone https://github.com/Ayushmania2002/Cis-GS.git
   cd Cis-GS
   python -m venv venv
   source venv/bin/activate              # Windows: venv\Scripts\activate
   pip install -e ".[dev,docs]"
   python app_v4_open.py                 # launch GUI
   python -m cis_gs --help               # CLI

Building the .exe yourself
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bat

   setup_and_build.bat

See :doc:`../BUILD <https://github.com/Ayushmania2002/Cis-GS/blob/main/BUILD.md>`
for the PyInstaller spec, macOS/Linux build scripts, and the PyPI release
workflow.

First-run setup
---------------

On first launch the GUI asks for your **NCBI email** (required by Entrez
for any genome download). It is stored only in ``~/CisGS-Workspace/.ncbi_email``
and is never transmitted anywhere except to NCBI on your own requests.

Workspace location
~~~~~~~~~~~~~~~~~~

All Cis-GS outputs land in ``~/CisGS-Workspace/`` by default. Change it
from **Settings → Change Workspace** in the GUI.
