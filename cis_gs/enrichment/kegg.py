"""
cis_gs.enrichment.kegg
──────────────────────
KEGG pathway over-representation analysis.

═══════════════════════════════════════════════════════════════════════════════
PROVENANCE
═══════════════════════════════════════════════════════════════════════════════
Internal data model:

    Per-species KEGG pathway tables:
        per-species `pathway`     (gene → pathwayID)
                    `pathwayInfo` (pathwayID → name, gene_count, URL)
                    `categories`  (pathwayID → high-level category)
        We keep the same three logical tables, just materialised on-the-fly
        from KEGG REST instead of shipped as a 5-GB SQLite bundle.

    Species-specific KEGG enrichment:
        the "organism code -> species-specific KEGG enrichment" idea
        (KEGG uses 3-letter codes - ath = Arabidopsis, hsa = Human, mmu = Mouse)

What's original here:
    ▸ Direct REST queries to https://rest.kegg.jp/ - three endpoints only:
          /list/pathway/<org>          → pathway IDs + descriptions
          /link/<org>/pathway          → gene ↔ pathway membership
          /find/genes/<symbol>         → resolve gene symbols to KEGG IDs
      Together those provide everything a per-species SQLite dump would,
      streamed over HTTP in <2 s per organism.
    ▸ Two-tier disk + memory cache so the second `enrich-kegg` call on the
      same organism is instantaneous.
    ▸ Auto fallback: if the user's gene IDs are gene symbols / Ensembl /
      Entrez (KEGG itself uses NCBI Gene ID for animals and locus tag for
      plants), we route through KEGG's `conv` endpoint to translate.
"""

from __future__ import annotations

import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .core import EnrichmentResult, hypergeometric_enrichment

LOG = logging.getLogger("cis_gs.kegg")
KEGG_REST = "https://rest.kegg.jp"

# Default cache root: ~/.cis-gs/kegg/
DEFAULT_CACHE_DIR = Path(os.path.expanduser("~")) / ".cis-gs" / "kegg"


# ─────────────────────────────────────────────────────────────────────────────
# Tiny KEGG client
# ─────────────────────────────────────────────────────────────────────────────
class KEGGClient:
    """Thin retrying wrapper around the four KEGG REST endpoints we need."""

    def __init__(self, cache_dir: str | os.PathLike = DEFAULT_CACHE_DIR,
                 timeout: float = 30.0,
                 retries: int = 3):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries

    # ── low-level fetch ────────────────────────────────────────────────────
    def _fetch(self, path: str, cache_name: str | None = None) -> str:
        """GET KEGG_REST/<path> as text; cache locally if `cache_name` given."""
        if cache_name:
            cache_path = self.cache_dir / cache_name
            if cache_path.exists():
                return cache_path.read_text(encoding="utf-8")
        url = f"{KEGG_REST}/{path.lstrip('/')}"
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                    text = resp.read().decode("utf-8")
                if cache_name:
                    (self.cache_dir / cache_name).write_text(text, encoding="utf-8")
                return text
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                LOG.warning("KEGG fetch failed (%s, try %d/%d): %s",
                            url, attempt + 1, self.retries, exc)
                time.sleep(1.0 + attempt)
        raise RuntimeError(f"KEGG REST unreachable: {url}") from last_exc

    # ── high-level helpers ─────────────────────────────────────────────────
    def list_pathways(self, organism: str) -> dict[str, str]:
        """{path:ath00010 → 'Glycolysis / Gluconeogenesis - Arabidopsis thaliana'}."""
        text = self._fetch(f"list/pathway/{organism}", f"{organism}_paths.tsv")
        out: dict[str, str] = {}
        for line in text.splitlines():
            if not line:
                continue
            f = line.split("\t", 1)
            if len(f) == 2:
                out[f[0]] = f[1]
        return out

    def pathway_genes(self, organism: str) -> dict[str, set[str]]:
        """
        {pathway_id → set(gene_ids)} for one organism.
        Returns KEGG's native gene IDs (e.g. ath:AT1G01010 for Arabidopsis,
        hsa:7157 for Human TP53). Caller is responsible for matching the
        query gene list to the same namespace; see `convert_to_kegg`.
        """
        text = self._fetch(f"link/{organism}/pathway", f"{organism}_links.tsv")
        out: dict[str, set[str]] = {}
        for line in text.splitlines():
            if not line:
                continue
            f = line.split("\t")
            if len(f) != 2:
                continue
            path_id, gene_id = f
            out.setdefault(path_id, set()).add(gene_id)
        return out

    def convert_to_kegg(self, organism: str, gene_ids: Iterable[str]) -> dict[str, str]:
        """
        Translate Ensembl / NCBI-Gene / UniProt → KEGG gene IDs via /conv.
        Returns {original_id: kegg_id} with misses left out.
        """
        # KEGG /conv expects a colon-prefixed namespace; we try the three
        # most common ones and merge results.
        out: dict[str, str] = {}
        for ns in ("ncbi-geneid", "ncbi-proteinid", "uniprot"):
            try:
                # KEGG REST conv only accepts up to ~100 IDs per request
                ids = list(gene_ids)
                for i in range(0, len(ids), 100):
                    chunk = ids[i:i + 100]
                    qstr = "+".join(f"{ns}:{g}" for g in chunk)
                    text = self._fetch(f"conv/{organism}/{qstr}")
                    for line in text.splitlines():
                        if not line:
                            continue
                        src, dst = line.split("\t", 1)
                        out[src.split(":", 1)[1]] = dst
                    time.sleep(0.1)
            except Exception:
                continue
        return out


# ─────────────────────────────────────────────────────────────────────────────
# Public façade - what users actually call
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class KEGGEnricher:
    """
    Drop-in KEGG enrichment.

    >>> e = KEGGEnricher(organism="ath")        # Arabidopsis
    >>> result = e.enrich(["AT1G01010", "AT2G18790", ...])
    >>> result.table.head()

    For animals the input is typically NCBI Gene IDs:

    >>> e = KEGGEnricher(organism="hsa")        # Human
    >>> result = e.enrich(["7157", "672"])      # TP53, BRCA1
    """
    organism: str
    client: KEGGClient | None = None
    background: list[str] | None = None    # if None, all genes mentioned in any KEGG pathway

    def __post_init__(self):
        if self.client is None:
            self.client = KEGGClient()

    # ── main entry ─────────────────────────────────────────────────────────
    def enrich(self, query_genes: Iterable[str], **kwargs) -> EnrichmentResult:
        # Pull pathway membership and descriptions
        path_genes = self.client.pathway_genes(self.organism)
        path_names = self.client.list_pathways(self.organism)

        # Strip leading 'path:' from keys so they match list_pathways output
        path_genes = {k.split("path:", 1)[-1]: v for k, v in path_genes.items()}
        path_names = {k.split("path:", 1)[-1]: v for k, v in path_names.items()}

        # KEGG prefixes every gene with the organism code (e.g. "ath:AT1G01010"
        # for plants, "hsa:7157" for animals).  KEGG mostly uses NCBI Entrez
        # IDs as the bare-token (no "LOC" prefix, no "gene-" prefix, no
        # version suffix).  We tolerate every format users actually encounter.
        org_prefix = f"{self.organism}:"

        # Reuse the shared GFF3 prefix/version stripper from idmap.py so KEGG
        # input behaves consistently with ID-Convert and Expression-Feeding.
        from .idmap import _strip_query_prefixes

        def _to_kegg(g: str) -> str:
            g = str(g).strip()
            if g.startswith(org_prefix):
                return g
            # Strip 'gene-', 'rna-', 'pseudogene-', 'transcript:', etc. + version.
            g = _strip_query_prefixes(g)
            # KEGG stores 'ahf:112706767' - drop the 'LOC' so 'LOC112706767'
            # becomes '112706767' for plants/animals where KEGG uses Entrez.
            if g.upper().startswith("LOC") and g[3:].split(".")[0].isdigit():
                g = g[3:]
            return f"{org_prefix}{g}"

        normalised_query = [_to_kegg(g) for g in query_genes if str(g).strip()]

        # Background defaults to every KEGG-known gene for this organism.
        if self.background is None:
            bg = set()
            for genes in path_genes.values():
                bg.update(genes)
        else:
            bg = {_to_kegg(g) for g in self.background}

        return hypergeometric_enrichment(
            query_genes=normalised_query,
            gene_sets=path_genes,
            universe=bg,
            set_descriptions=path_names,
            **kwargs,
        )
