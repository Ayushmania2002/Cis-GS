Contributing
============

Bug reports, feature requests, and pull requests are welcome.

Development setup
-----------------

.. code-block:: bash

   git clone https://github.com/Ayushmania2002/Cis-GS.git
   cd Cis-GS
   python -m venv venv
   source venv/bin/activate           # Windows: venv\Scripts\activate
   pip install -e ".[dev,docs]"

Running the tests
-----------------

.. code-block:: bash

   pytest

Building the docs locally
-------------------------

.. code-block:: bash

   cd docs
   make html
   # output: docs/_build/html/index.html

Coding conventions
------------------

* Black-style formatting where possible (no enforcer yet).
* Google-style docstrings (Napoleon parses both Google and NumPy).
* Public functions get type hints; internal helpers may omit them.
* Every new feature gets at least one smoke test in ``tests/``.

Opening a pull request
----------------------

1. Open an issue first for anything bigger than a typo.
2. Branch off ``main``: ``git checkout -b feat/my-feature``.
3. Commit with a clear message.
4. Push and open a PR. CI runs the test suite + builds the docs.

Code of conduct
---------------

Be kind. Disagreements about science and code are expected; personal
attacks are not.
