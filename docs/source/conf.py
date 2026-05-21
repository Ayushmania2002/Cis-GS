"""
Sphinx configuration for Cis-GS documentation.
Built with sphinx + sphinx-rtd-theme + myst-parser (Markdown support).
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# Make the package importable for autodoc
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── Project info ────────────────────────────────────────────────────────────
project   = "Cis-GS"
author    = "Ayushman Mallick"
copyright = f"{datetime.now().year}, {author} (Plant Signaling Lab, IISER Tirupati)"

# Read version from pyproject.toml (single source of truth)
try:
    import tomllib  # py 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore
with open(ROOT / "pyproject.toml", "rb") as f:
    release = tomllib.load(f)["project"]["version"]
version = ".".join(release.split(".")[:2])

# ── General ─────────────────────────────────────────────────────────────────
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",        # google + numpy docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "myst_parser",                # markdown alongside rst
]
templates_path   = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix    = {".rst": "restructuredtext", ".md": "markdown"}

autosummary_generate    = True
autodoc_member_order    = "bysource"
autodoc_typehints       = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring  = True

intersphinx_mapping = {
    "python":      ("https://docs.python.org/3",       None),
    "numpy":       ("https://numpy.org/doc/stable",    None),
    "pandas":      ("https://pandas.pydata.org/docs",  None),
    "scipy":       ("https://docs.scipy.org/doc/scipy", None),
    "matplotlib":  ("https://matplotlib.org/stable",   None),
    "biopython":   ("https://biopython.org/docs/latest", None),
}

# ── HTML output ─────────────────────────────────────────────────────────────
html_theme        = "sphinx_rtd_theme"
html_static_path  = ["_static"]
html_title        = f"Cis-GS {release}"
html_short_title  = "Cis-GS"
html_favicon      = None        # set to "_static/favicon.ico" once added
html_logo         = None        # set to "_static/logo.png" once added
html_show_sourcelink = True
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth":    3,
    "style_external_links": True,
    "prev_next_buttons_location": "both",
    "logo_only": False,
}
html_context = {
    "display_github": True,
    "github_user":    "Ayushmania2002",
    "github_repo":    "Cis-GS",
    "github_version": "main",
    "conf_py_path":   "/docs/source/",
}

# ── Copybutton config (skip prompts and outputs) ────────────────────────────
copybutton_prompt_text = r">>> |\.\.\. |\$ |# "
copybutton_prompt_is_regexp = True
