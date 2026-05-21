"""
Smoke tests for cis_gs - guarantees the package and its core sub-modules
can be imported on a clean machine and that the public statistics primitives
behave sanely.

Run with:  pytest -q
"""
from __future__ import annotations

import numpy as np
import pytest


def test_package_imports():
    import cis_gs  # noqa: F401


def test_enrichment_submodules_import():
    from cis_gs.enrichment import core, kegg, idmap  # noqa: F401


def test_bh_fdr_monotone_and_bounded():
    """BH-FDR output must be in [0, 1], monotone non-decreasing when sorted."""
    from cis_gs.enrichment.core import bh_fdr

    raw = [0.001, 0.01, 0.04, 0.05, 0.2, 0.8]
    q = bh_fdr(raw)
    assert q.shape == (len(raw),)
    assert np.all((q >= 0) & (q <= 1))
    sorted_q = np.sort(q)
    assert np.all(np.diff(sorted_q) >= -1e-12), "BH-FDR should be monotone"


def test_fold_enrichment_signs():
    """Fold-enrichment > 1 when k/n exceeds the background frequency."""
    from cis_gs.enrichment.core import fold_enrichment

    fe = fold_enrichment(
        k=np.array([5]), list_n=10,
        n=np.array([20]), total_n=1000,
    )
    # 5/10 vs 20/1000  ->  0.5 / 0.02 = 25
    assert fe[0] == pytest.approx(25.0)


def test_hypergeometric_enrichment_minimal():
    """End-to-end sanity check on a trivially over-represented term."""
    from cis_gs.enrichment.core import hypergeometric_enrichment

    universe   = [f"gene{i}" for i in range(100)]
    motif_set  = {"PATHWAY_A": [f"gene{i}" for i in range(10)]}
    query      = [f"gene{i}" for i in range(8)]   # 8/10 of pathway A

    res = hypergeometric_enrichment(query, motif_set, universe=universe,
                                    min_set_size=1, min_overlap=1)
    assert len(res.table) == 1
    row = res.table.iloc[0]
    assert row["k"] == 8
    assert row["q_value"] < 0.05
