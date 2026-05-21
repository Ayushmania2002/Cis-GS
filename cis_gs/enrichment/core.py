"""
cis_gs.enrichment.core
──────────────────────
Generic over-representation analysis (ORA) primitives shared by every
enrichment back-end (GO, KEGG, custom gene sets, motif targets …).

═══════════════════════════════════════════════════════════════════════════════
STATISTICAL KERNEL
═══════════════════════════════════════════════════════════════════════════════
Standard one-sided hypergeometric over-representation test with
Benjamini-Hochberg FDR correction:

    pval = scipy.stats.hypergeom.sf(k - 1, totalN, n, listN)
    over-rep filter: keep terms where k / n > listN / totalN
    fold-enrichment: (k / listN) / (n / totalN)
    bh_fdr()  - re-uses Cis-GS's from-scratch Benjamini-Hochberg
                routine from app_v4_open.py (no scipy.multitest dependency).

Two implementation notes specific to Cis-GS:

    1.  A *single* vectorised pass over thousands of pathways - we treat
        the whole pathway table as a NumPy column operation instead of
        looping one category at a time.
    2.  Optional minimum-overlap and gene-symbol-cleaning guards that prevent
        the spurious "1-gene-overlap pathway with q~0" hits that surface on
        small query lists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import hypergeom


# ─────────────────────────────────────────────────────────────────────────────
# Benjamini-Hochberg correction
# ─────────────────────────────────────────────────────────────────────────────
def bh_fdr(pvals: Sequence[float]) -> np.ndarray:
    """
    Benjamini-Hochberg step-up FDR.

    This is the same from-scratch implementation Cis-GS already ships in
    app_v4_open.py for motif-hit q-values; reused verbatim so we don't add
    a statsmodels dependency just for one call.

        order  = argsort(p)
        ranks  = invert(order) + 1
        adj    = min(1, p · n / rank)
        adj[i] = min(adj[i], adj[i+1])      (monotone step-up sweep)

    Parameters
    ----------
    pvals : array-like of float
        Raw p-values (any length, any order).

    Returns
    -------
    np.ndarray
        BH-adjusted q-values, same order as input.
    """
    p = np.asarray(pvals, dtype=float)
    n = p.size
    if n == 0:
        return p.copy()

    order = np.argsort(p)
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(1, n + 1)

    adj = np.minimum(1.0, p * n / ranks)

    # monotone step-up sweep, walking from largest p downward
    sorted_idx = order[::-1]
    running_min = 1.0
    for i in sorted_idx:
        running_min = min(running_min, adj[i])
        adj[i] = running_min

    return adj


# ─────────────────────────────────────────────────────────────────────────────
# Fold enrichment
# ─────────────────────────────────────────────────────────────────────────────
def fold_enrichment(k: np.ndarray, list_n: int,
                    n: np.ndarray, total_n: int) -> np.ndarray:
    """
    Fold-enrichment definition:

        FE = (k / listN) / (n / totalN)

    where
        k       = #genes shared by query list and pathway
        listN   = size of query list
        n       = #genes in pathway (within the background)
        totalN  = size of the background universe
    """
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        fe = (k / list_n) / (n / total_n)
    return np.where(np.isfinite(fe), fe, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# The enrichment table itself
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class EnrichmentResult:
    """Tidy container returned by hypergeometric_enrichment()."""
    table: pd.DataFrame                # full results, sorted by q ascending
    n_query: int                       # |query ∩ universe|  (after cleaning)
    n_universe: int                    # |universe|
    method: str = "hypergeometric"     # for downstream reporting
    notes: list[str] = field(default_factory=list)


def hypergeometric_enrichment(
    query_genes: Iterable[str],
    gene_sets: Mapping[str, Iterable[str]],
    universe: Iterable[str] | None = None,
    *,
    set_descriptions: Mapping[str, str] | None = None,
    min_overlap: int = 2,
    min_set_size: int = 5,
    max_set_size: int = 2000,
    one_sided: bool = True,
) -> EnrichmentResult:
    """
    Vectorised over-representation analysis.

    Parameters
    ----------
    query_genes : iterable of str
        The user's gene list (e.g. K-means cluster from Cis-GS Module 6, or
        the gene list a user pastes into the GO/KEGG dialog).
    gene_sets : mapping {term_id: iterable of gene IDs}
        The annotation database - GO terms, KEGG pathways, custom MSigDB-style
        sets, etc.  Term IDs are used as the table primary key.
    universe : iterable of str, optional
        Background gene set (totalN).  If None, taken as the union of every
        gene appearing in any value of `gene_sets`.  Default is the
        protein-coding gene complement; pass that explicitly when you have it.
    set_descriptions : mapping {term_id: human-readable name}, optional
        For the `Description` column.  KEGG's `pathway_name` table or QuickGO's
        `name` field both fit naturally here.
    min_overlap : int
        Drop terms with fewer than this many query-genes in them.  Defaults to
        2 (raised from 1 to silence single-gene noise on small
        K-means clusters).
    min_set_size, max_set_size : int
        Drop pathways/categories outside the size window.  Defaults
        (5..2000).  Filters out near-empty and near-universal terms that
        produce uninterpretable p-values.
    one_sided : bool
        If True, apply a one-sided over-representation guard
        (`k/n > listN/totalN`).  If False, every term gets a p-value.

    Returns
    -------
    EnrichmentResult
        .table is a pandas.DataFrame with columns:
            term, description, k, list_n, n, total_n,
            fold_enrichment, p_value, q_value, genes
    """

    # ── 1. clean & freeze inputs ────────────────────────────────────────────
    query_set = {g.strip() for g in query_genes if g and isinstance(g, str)}
    if universe is None:
        bg = set()
        for genes in gene_sets.values():
            bg.update(genes)
    else:
        bg = {g.strip() for g in universe if g}

    notes: list[str] = []
    if not bg:
        raise ValueError("Empty universe: cannot compute enrichment.")

    # Restrict the query to genes that exist in the background;
    # otherwise the hypergeometric is mis-specified.
    query_in_bg = query_set & bg
    if len(query_in_bg) < len(query_set):
        notes.append(
            f"{len(query_set) - len(query_in_bg)} of {len(query_set)} query "
            f"genes were not found in the background and were dropped."
        )

    list_n = len(query_in_bg)
    total_n = len(bg)
    if list_n == 0:
        return EnrichmentResult(
            table=_empty_table(),
            n_query=0,
            n_universe=total_n,
            notes=notes + ["No query gene survived background intersection."],
        )

    # ── 2. assemble the per-term arrays in one pass ─────────────────────────
    rows = []
    for term, genes in gene_sets.items():
        members = {g for g in genes if g in bg}        # restrict to universe
        size = len(members)
        if size < min_set_size or size > max_set_size:
            continue
        overlap = members & query_in_bg
        k = len(overlap)
        if k < min_overlap:
            continue
        rows.append((term, k, size, sorted(overlap)))

    if not rows:
        return EnrichmentResult(
            table=_empty_table(),
            n_query=list_n,
            n_universe=total_n,
            notes=notes + ["No gene set passed size/overlap filters."],
        )

    terms = np.array([r[0] for r in rows])
    k_arr = np.array([r[1] for r in rows], dtype=int)
    n_arr = np.array([r[2] for r in rows], dtype=int)
    overlap_lists = [r[3] for r in rows]

    # ── 3. one-sided over-rep filter ────────────────────────────────
    if one_sided:
        keep = (k_arr / n_arr) > (list_n / total_n)
        if not keep.any():
            return EnrichmentResult(
                table=_empty_table(),
                n_query=list_n,
                n_universe=total_n,
                notes=notes + ["No term over-represented (k/n ≤ listN/totalN)."],
            )
        terms = terms[keep]
        k_arr = k_arr[keep]
        n_arr = n_arr[keep]
        overlap_lists = [g for g, k in zip(overlap_lists, keep) if k]

    # ── 4. vectorised hypergeometric SF ─────────────────────────────────────
    # scipy.stats.hypergeom.sf(k - 1, M, n, N) is identical to R's
    # phyper(k - 1, n, M - n, N, lower.tail = FALSE)
    pvals = hypergeom.sf(k_arr - 1, total_n, n_arr, list_n)
    pvals = np.clip(pvals, a_min=0.0, a_max=1.0)

    # ── 5. fold enrichment & BH-FDR ─────────────────────────────────────────
    fe = fold_enrichment(k_arr, list_n, n_arr, total_n)
    qvals = bh_fdr(pvals)

    # ── 6. assemble tidy DataFrame ──────────────────────────────────────────
    desc_map = set_descriptions or {}
    df = pd.DataFrame({
        "term": terms,
        "description": [desc_map.get(t, "") for t in terms],
        "k": k_arr,
        "list_n": list_n,
        "n": n_arr,
        "total_n": total_n,
        "fold_enrichment": fe,
        "p_value": pvals,
        "q_value": qvals,
        "genes": [",".join(g) for g in overlap_lists],
    }).sort_values("q_value", kind="mergesort").reset_index(drop=True)

    return EnrichmentResult(
        table=df,
        n_query=list_n,
        n_universe=total_n,
        notes=notes,
    )


def _empty_table() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "term", "description", "k", "list_n", "n", "total_n",
        "fold_enrichment", "p_value", "q_value", "genes",
    ])
