"""
cis_gs.enrichment
-----------------
Functional-enrichment subsystem for Cis-GS.

Provenance of the algorithms in this sub-package:

    core.hypergeometric_enrichment   implemented in Cis-GS
                                     (phyper(k-1,n,totalN-n,listN) +
                                      k/n > listN/totalN over-rep filter +
                                      fold = (k/listN)/(n/totalN)).
                                     Re-implemented in NumPy/SciPy.
    core.bh_fdr                      reuses Cis-GS's from-scratch
                                     Benjamini-Hochberg routine that
                                     lives in app_v4_open.py.
    kegg.KEGGEnricher                KEGG REST endpoints (link/list/get);
                                     no R bridge, no kegg.db dump.
    idmap.IDConverter                MyGene.info-backed gene-ID converter
                                     (REST, batched POST, ~60x speedup).
    plots                            matplotlib renditions of the canonical
                                     enrichment dot-plot and bar-plot.
"""

from .core import hypergeometric_enrichment, bh_fdr, fold_enrichment
from .kegg import KEGGEnricher
from .idmap import IDConverter
from . import plots

__all__ = [
    "hypergeometric_enrichment",
    "bh_fdr",
    "fold_enrichment",
    "KEGGEnricher",
    "IDConverter",
    "plots",
]
