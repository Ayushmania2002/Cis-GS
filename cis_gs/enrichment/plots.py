"""
cis_gs.enrichment.plots
───────────────────────
Matplotlib renditions of the two canonical enrichment views (dot-plot + bar-plot).

Provenance
----------
We render the same two canonical plots
(dot-plot ordered by fold enrichment, top-N bar of −log10 q) in matplotlib so
no R bridge is needed.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def dot_plot(table: pd.DataFrame,
             top_n: int = 20,
             out_path: str | None = None,
             title: str = "Enrichment dot plot") -> matplotlib.figure.Figure:
    """
    Top-N enriched terms as a dot plot.

    X-axis  : fold enrichment    
    Y-axis  : term description   (ordered by q ascending)
    Size    : k (overlap count)
    Colour  : −log10(q)
    """
    df = table.head(top_n).copy()
    if df.empty:
        raise ValueError("No enrichment rows to plot.")

    df["neg_log_q"] = -np.log10(df["q_value"].clip(lower=1e-300))
    labels = df["description"].where(df["description"].astype(bool), df["term"])

    fig, ax = plt.subplots(figsize=(9, max(4, 0.35 * len(df))))
    sc = ax.scatter(
        df["fold_enrichment"], np.arange(len(df))[::-1],
        s=df["k"] * 25 + 30,
        c=df["neg_log_q"], cmap="viridis", edgecolor="black", linewidth=0.4,
    )
    ax.set_yticks(np.arange(len(df))[::-1])
    ax.set_yticklabels(labels)
    ax.set_xlabel("Fold enrichment")
    ax.set_title(title)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("−log10(q)")
    plt.tight_layout()
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig


def bar_plot(table: pd.DataFrame,
             top_n: int = 20,
             out_path: str | None = None,
             title: str = "Top enriched terms") -> matplotlib.figure.Figure:
    """Top-N bar plot of −log10(q)."""
    df = table.head(top_n).copy()
    if df.empty:
        raise ValueError("No enrichment rows to plot.")
    df["neg_log_q"] = -np.log10(df["q_value"].clip(lower=1e-300))
    labels = df["description"].where(df["description"].astype(bool), df["term"])

    fig, ax = plt.subplots(figsize=(9, max(4, 0.35 * len(df))))
    ax.barh(np.arange(len(df))[::-1], df["neg_log_q"],
            color="#3FB950", edgecolor="black", linewidth=0.4)
    ax.set_yticks(np.arange(len(df))[::-1])
    ax.set_yticklabels(labels)
    ax.set_xlabel("−log10(q)")
    ax.set_title(title)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
    return fig
