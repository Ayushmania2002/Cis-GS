# Contributing to Cis-GS

Thank you for your interest in contributing to Cis-GS! This document outlines
how to report bugs, suggest features, and submit code contributions.

---

## Table of Contents

- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Development Setup](#development-setup)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Contact](#contact)

---

## Reporting Bugs

Before opening an issue, please:

1. Check the [existing issues](https://github.com/Ayushmania2002/Cis-GS/issues)
   to avoid duplicates.
2. Confirm the bug is reproducible on the **latest version**
   (`pip install --upgrade cis-gs`).

When filing a bug report, include:

- Cis-GS version (`cis-gs --version`)
- Operating system and Python version
- Minimal steps to reproduce the issue
- Full error traceback (if applicable)
- Input file details (genome assembly, species) — do not attach raw genomic data

Use the **Bug Report** issue template when opening the issue.

---

## Suggesting Features

Feature requests are welcome. Please open a
[GitHub Issue](https://github.com/Ayushmania2002/Cis-GS/issues) using the
**Feature Request** template and describe:

- The biological or computational problem you are trying to solve
- How the proposed feature would work
- Any relevant tools or papers that implement similar functionality

---

## Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/<your-username>/Cis-GS.git
cd Cis-GS

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows

# Install in editable mode with all dev extras
pip install -e ".[docs]"
pip install pytest

# Run the test suite
pytest tests/
```

---

## Submitting a Pull Request

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b fix/my-bug-fix
   ```

2. Make your changes, keeping commits focused and descriptive.

3. Ensure the test suite passes:
   ```bash
   pytest tests/
   ```

4. Build and verify the docs locally if you changed documentation:
   ```bash
   cd docs && make html
   ```

5. Push your branch and open a Pull Request against `main`. Fill in the
   PR template describing what changed and why.

6. A maintainer will review your PR, suggest changes if needed, and merge
   it once approved.

---

## Code Style

- **Python**: follow [PEP 8](https://peps.python.org/pep-0008/).
  Line length limit: 100 characters.
- **Docstrings**: Google-style docstrings (compatible with Napoleon/Sphinx).
- **Type hints**: encouraged for all public functions.
- **No AI-generated code** should be submitted without review and disclosure
  in the PR description.

---

## Documentation

Documentation lives in `docs/source/` (reStructuredText + MyST Markdown).
To build locally:

```bash
cd docs
make html
# Open docs/_build/html/index.html in your browser
```

If you add a new CLI command, update `docs/source/cli/commands.rst`.
If you add a new wizard, update `docs/source/cli/wizard.rst`.

---

## Contact

For questions not suited to a public issue, contact the maintainer at
**ayushmania2002@gmail.com**.

*Cis-GS is developed at the Plant Signaling Lab, IISER Tirupati.*
