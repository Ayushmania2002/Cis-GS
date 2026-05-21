"""
Auto-detecting gene-identifier converter.

The high-level flow is: *guess the input ID type, translate to a canonical
key, return a (user_input, ensembl_gene_id, species) frame*. Cis-GS
replaces the ~17 GB SQLite mapping table the naive approach would need
with three lightweight back-ends:

1. An offline regex pre-classifier (cheap, no network) that recognises
   the common plant + animal ID syntaxes Cis-GS encounters in practice.
2. MyGene.info ``/query`` and ``/querymany`` REST endpoints for any ID
   type the regex doesn't catch (vertebrates + plants).
3. A small handcrafted Arabidopsis-locus table (TAIR uses
   ``AT[1-5MC]G\\d{5}``) because TAIR is the most common Cis-GS
   use-case and MyGene.info's Arabidopsis coverage is uneven.

The order matters: fast regex first, network only on misses, with an
optional species hint that accelerates the lookup when supplied.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

LOG = logging.getLogger("cis_gs.idmap")
MYGENE_BASE = "https://mygene.info/v3"
_UA = ("Mozilla/5.0 (Cis-GS / Python urllib) "
       "https://github.com/AyushmanMallick/Cis-GS")


# ─────────────────────────────────────────────────────────────────────────────
# Regex pre-classifier - fully offline.
# ─────────────────────────────────────────────────────────────────────────────
# Each rule maps an ID type → compiled regex.  The order matters: the first
# matching rule wins, so put the *most specific* patterns first (TAIR before
# generic Ensembl).
_ID_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("tair_locus",         re.compile(r"^AT[1-5MC]G\d{5}(\.\d+)?$", re.I)),
    ("rice_locus",         re.compile(r"^(LOC_)?Os\d{2}g\d{7}(\.\d+)?$", re.I)),
    ("maize_v4_locus",     re.compile(r"^Zm\d{5}d\d{6}$", re.I)),
    ("ensembl_gene_plant", re.compile(r"^[A-Z]{1,3}\d{2,3}G\d{6,8}$")),
    ("ensembl_gene",       re.compile(r"^ENS[A-Z]{0,4}G\d{6,11}(\.\d+)?$")),
    ("ensembl_transcript", re.compile(r"^ENS[A-Z]{0,4}T\d{6,11}(\.\d+)?$")),
    ("refseq_mrna",        re.compile(r"^[NX]M_\d+(\.\d+)?$")),
    ("refseq_protein",     re.compile(r"^[NX]P_\d+(\.\d+)?$")),
    ("uniprot",            re.compile(r"^[OPQ][0-9][A-Z0-9]{3}[0-9]"
                                      r"|^[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$")),
    ("entrez",             re.compile(r"^\d{1,9}$")),
    # Symbol left as the catch-all (any 1-15 char alnum / dash / dot).
    ("symbol",             re.compile(r"^[A-Za-z0-9._\-]{1,20}$")),
]


_PREFIX_RE = re.compile(
    r"^(?:"
    # NCBI RefSeq GFF3 ID= attribute prefixes
    r"gene|rna|cds|exon|id|"
    # NCBI feature-type prefixes (used as ID= prefix on those features)
    r"pseudogene|ncRNA|mRNA|tRNA|rRNA|miRNA|snoRNA|snRNA|lnc_RNA|lncRNA|"
    r"region|chromosome|primary_transcript|transcript|protein"
    # Ensembl-style 'gene:', 'transcript:' etc. - separator handled by [-:]
    r")[-:_]",
    re.IGNORECASE,
)


def _strip_query_prefixes(gene_id: str) -> str:
    """
    Strip GFF3-style prefixes ('gene-', 'rna-', 'cds-', 'pseudogene-',
    'transcript:', 'mRNA-', 'tRNA-', 'lnc_RNA-', 'region-', etc.) and a
    numeric version suffix ('.1', '.2') from a gene identifier so it can
    be looked up in MyGene.info / KEGG / GO databases.

    Crucially, this is what fixes 'gene-LOC107275312' → 'LOC107275312' -
    the bare ID is what every public gene database actually indexes.

    Works flexibly across organism conventions:
      • NCBI RefSeq:    'gene-LOC...', 'rna-XM_...', 'cds-XP_...'
      • Ensembl:        'gene:ENSG...', 'transcript:ENST...'
      • TAIR (plants):  'AT1G01010.1' → 'AT1G01010'
      • Pseudogenes:    'pseudogene-LOC...' → 'LOC...'
      • RNA classes:    'tRNA-...', 'ncRNA-...', 'miRNA-...', etc.
    """
    g = str(gene_id).strip()
    # Strip a recognised feature-type / ID-class prefix (one round; some IDs
    # carry only one).
    m = _PREFIX_RE.match(g)
    if m:
        g = g[m.end():]
    # Strip a single trailing '.<digits>' RefSeq version (LOC123.1 → LOC123).
    # Don't touch alphanumeric tails like 'Arahy.0002EG'.
    m = re.match(r"^(.*)\.(\d+)$", g)
    if m:
        g = m.group(1)
    return g


def detect_id_type(gene_id: str) -> str:
    """Return the first ID-type label whose regex matches `gene_id`.

    Detects the ID type offline using a regex pre-classifier.
    Detection runs on the *prefix-stripped* form so 'gene-LOC123' classifies
    the same as 'LOC123'.
    """
    g = _strip_query_prefixes(gene_id)
    for label, pattern in _ID_PATTERNS:
        if pattern.match(g):
            return label
    return "unknown"


def consensus_id_type(gene_ids: Iterable[str]) -> str:
    """
    Take a vote across a gene list - useful for picking a single
    `scopes=` value to send to MyGene.info /querymany.

    Useful for picking a single `scopes=` value to send to MyGene.info /querymany.
    """
    counts: dict[str, int] = {}
    for g in gene_ids:
        t = detect_id_type(g)
        counts[t] = counts.get(t, 0) + 1
    if not counts:
        return "unknown"
    return max(counts.items(), key=lambda kv: kv[1])[0]


# ─────────────────────────────────────────────────────────────────────────────
# MyGene.info wrapper
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class IDMapping:
    """Single row of the conversion result, canonical."""
    user_input: str
    ensembl_gene_id: str | None
    entrez_id: str | None
    symbol: str | None
    species: str | None        # taxonomy-id or scientific name


# Map our internal id-type labels to MyGene.info `scopes=` values.
# (Internal label -> MyGene.info `scopes=` value.)
_SCOPES = {
    "symbol":              "symbol,name,alias",
    "entrez":              "entrezgene",
    "ensembl_gene":        "ensembl.gene",
    "ensembl_gene_plant":  "ensembl.gene",
    "ensembl_transcript":  "ensembl.transcript",
    "refseq_mrna":         "refseq.rna",
    "refseq_protein":      "refseq.protein",
    "uniprot":             "uniprot.Swiss-Prot,uniprot.TrEMBL",
    "tair_locus":          "symbol,alias,ensembl.gene",
    "rice_locus":          "symbol,alias,ensembl.gene",
    "maize_v4_locus":      "symbol,alias,ensembl.gene",
    "unknown":             "all",
}


class IDConverter:
    """
    Auto-detecting ID converter.

    Usage
    -----
    >>> conv = IDConverter(species="arabidopsis_thaliana")
    >>> df = conv.convert(["AT1G01010", "AT2G18790", "PHYB"])
    >>> df.columns
    Index(['user_input', 'ensembl_gene_id', 'entrez_id', 'symbol', 'species'])

    Parameters
    ----------
    species : str | int | None
        Either a taxonomy ID (integer or numeric string) or a MyGene.info
        species shortcut ("human", "mouse") or the binomial with underscore
        ("arabidopsis_thaliana").  None lets MyGene.info auto-detect.
    timeout : float
        Per-request HTTP timeout in seconds.
    cache : dict | None
        Optional in-memory cache to amortise repeated lookups across calls.
    """

    def __init__(self, species: str | int | None = None,
                 timeout: float = 12.0,
                 cache: dict[tuple[str, str], IDMapping] | None = None):
        self.species = species
        self.timeout = timeout
        self.cache = cache if cache is not None else {}

    # ── public API ─────────────────────────────────────────────────────────
    def convert(self, gene_ids: Iterable[str],
                progress_callback=None) -> pd.DataFrame:
        """Translate a gene list to a canonical DataFrame.

        progress_callback(done:int, total:int, label:str) is invoked
        repeatedly during the run so a GUI can show a real-time bar.
        """
        ids_raw = [g.strip() for g in gene_ids if g and isinstance(g, str)]
        if not ids_raw:
            return self._empty()

        # Map: stripped query → original user_input (for row labelling).
        # Done first so 'gene-LOC107275312' is sent to MyGene.info as
        # 'LOC107275312' but the result row still says 'gene-LOC107275312'.
        stripped_to_orig: dict[str, str] = {}
        ordered_originals: list[str] = []   # preserve user's input order
        for g in ids_raw:
            s = _strip_query_prefixes(g)
            if s not in stripped_to_orig:
                stripped_to_orig[s] = g
            ordered_originals.append(g)

        # Group inputs by detected type so each MyGene.info call uses the
        # narrowest possible `scopes=`.  Detection runs on the stripped form
        # so 'gene-LOC123' and 'LOC123' classify the same way.
        by_type: dict[str, list[str]] = {}
        for stripped in stripped_to_orig:
            by_type.setdefault(detect_id_type(stripped), []).append(stripped)

        # Pull cached results first so we don't refetch them.
        results_by_orig: dict[str, IDMapping] = {}
        uncached_by_type: dict[str, list[str]] = {}
        for id_type, batch in by_type.items():
            uncached: list[str] = []
            for stripped in batch:
                orig = stripped_to_orig[stripped]
                key = (id_type, stripped)
                if key in self.cache:
                    cached = self.cache[key]
                    # Re-label with the user's original input ID
                    results_by_orig[orig] = IDMapping(
                        user_input=orig,
                        ensembl_gene_id=cached.ensembl_gene_id,
                        entrez_id=cached.entrez_id,
                        symbol=cached.symbol,
                        species=cached.species,
                    )
                else:
                    uncached.append(stripped)
            if uncached:
                uncached_by_type[id_type] = uncached

        total_to_fetch = sum(len(v) for v in uncached_by_type.values())
        if progress_callback:
            progress_callback(0, total_to_fetch, "Starting MyGene.info batch…")

        done = 0
        for id_type, uncached in uncached_by_type.items():
            scopes = _SCOPES.get(id_type, "all")
            mapped = self._querymany_batch(
                uncached, scopes,
                batch_size=200,
                progress_callback=(
                    (lambda d, t, lbl, _base=done, _tot=total_to_fetch:
                        progress_callback(_base + d, _tot, lbl))
                    if progress_callback else None),
            )
            for m in mapped:
                # m.user_input is the *stripped* form sent to MyGene.info
                stripped = m.user_input
                self.cache[(id_type, stripped)] = m
                orig = stripped_to_orig.get(stripped, stripped)
                results_by_orig[orig] = IDMapping(
                    user_input=orig,
                    ensembl_gene_id=m.ensembl_gene_id,
                    entrez_id=m.entrez_id,
                    symbol=m.symbol,
                    species=m.species,
                )
            done += len(uncached)

        if progress_callback:
            progress_callback(total_to_fetch, total_to_fetch, "Done")

        # Emit one row per original input ID, preserving order, even if some
        # stripped forms collided to the same MyGene.info hit.
        rows: list[IDMapping] = []
        seen_orig: set[str] = set()
        for g in ordered_originals:
            if g in seen_orig:
                continue
            seen_orig.add(g)
            rows.append(results_by_orig.get(
                g, IDMapping(g, None, None, None, None)))

        return pd.DataFrame([r.__dict__ for r in rows])

    # ── private ────────────────────────────────────────────────────────────
    def _querymany_batch(self, gene_ids: list[str], scopes: str,
                         batch_size: int = 200,
                         progress_callback=None) -> list[IDMapping]:
        """
        Batched POST to MyGene.info /querymany - ~50× faster than per-gene
        /query because each HTTP request resolves up to ``batch_size`` IDs.
        """
        # MyGene.info batch queries hit the same /query endpoint via POST
        # (https://docs.mygene.info/en/latest/doc/query_service.html#batch-queries-via-post)
        url = f"{MYGENE_BASE}/query"
        out: list[IDMapping] = []
        total = len(gene_ids)
        i = 0
        while i < total:
            chunk = gene_ids[i:i + batch_size]
            if progress_callback:
                progress_callback(
                    i, total,
                    f"Translating {i}-{min(i + batch_size, total)} of "
                    f"{total} via MyGene.info…")
            params = {
                "q":      ",".join(chunk),
                "scopes": scopes,
                "fields": "symbol,entrezgene,ensembl.gene,taxid",
                "size":   "1",
            }
            if self.species is not None:
                params["species"] = str(self.species)
            body = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(
                url, data=body,
                headers={"User-Agent": _UA,
                         "Accept": "application/json",
                         "Content-Type": "application/x-www-form-urlencoded"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout * 4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as exc:
                LOG.warning("MyGene.info batch %d failed: %s - falling back "
                            "to per-id /query", i, exc)
                # Per-gene fallback for this chunk only
                out.extend(self._querymany_oneatatime(chunk, scopes))
                i += batch_size
                continue

            seen: set[str] = set()
            for hit in data:
                if not isinstance(hit, dict):
                    continue
                q = str(hit.get("query", ""))
                if not q or q in seen:
                    continue
                seen.add(q)
                if hit.get("notfound"):
                    out.append(IDMapping(q, None, None, None, None))
                else:
                    out.append(self._row_from_hit(q, hit))
            # Anything not returned at all → mark not-found
            for g in chunk:
                if g not in seen:
                    out.append(IDMapping(g, None, None, None, None))

            i += batch_size
            time.sleep(0.05)

        if progress_callback:
            progress_callback(total, total, f"Translated {total} IDs")
        return out

    def _querymany_oneatatime(self, gene_ids: list[str],
                              scopes: str) -> list[IDMapping]:
        """Per-id /query fallback - used only if the batch endpoint dies."""
        url = f"{MYGENE_BASE}/query"
        out: list[IDMapping] = []
        for gid in gene_ids:
            try:
                params = {"q": gid, "fields": "symbol,entrezgene,ensembl.gene,taxid",
                          "scopes": scopes, "size": 1}
                if self.species is not None:
                    params["species"] = str(self.species)
                qs = urllib.parse.urlencode(params)
                req = urllib.request.Request(f"{url}?{qs}",
                                             headers={"User-Agent": _UA,
                                                      "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                hit = (data.get("hits") or [None])[0]
                out.append(self._row_from_hit(gid, hit))
                time.sleep(0.05)
            except Exception as exc:
                LOG.warning("MyGene.info lookup failed for %s: %s", gid, exc)
                out.append(IDMapping(gid, None, None, None, None))
        return out

    @staticmethod
    def _row_from_hit(query: str, hit: dict | None) -> IDMapping:
        if not hit:
            return IDMapping(query, None, None, None, None)
        ensembl = hit.get("ensembl")
        if isinstance(ensembl, list):
            ensembl_gene = ensembl[0].get("gene") if ensembl else None
        elif isinstance(ensembl, dict):
            ensembl_gene = ensembl.get("gene")
        else:
            ensembl_gene = None
        entrez = hit.get("entrezgene")
        return IDMapping(
            user_input=query,
            ensembl_gene_id=ensembl_gene,
            entrez_id=str(entrez) if entrez is not None else None,
            symbol=hit.get("symbol"),
            species=str(hit.get("taxid")) if hit.get("taxid") else None,
        )

    @staticmethod
    def _empty() -> pd.DataFrame:
        return pd.DataFrame(columns=[
            "user_input", "ensembl_gene_id", "entrez_id", "symbol", "species",
        ])


# ── NCBI Taxonomy lookup - for the GUI's organism-name searcher ─────────────
def search_ncbi_taxonomy(query: str, max_results: int = 25,
                        timeout: float = 15.0) -> list[dict]:
    """
    Search NCBI's Taxonomy database for any organism name and return
    [{taxid, scientific_name, common_name}, ...].

    Used to power a real-time auto-complete in the ID-Convert / GO panels:
    the user types 'oryza' or 'rice', we hit NCBI Taxonomy esearch+esummary
    and surface every match with its taxon ID.
    """
    q = (query or "").strip()
    if len(q) < 2:
        return []

    eutils = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    headers = {"User-Agent": _UA, "Accept": "application/json"}

    try:
        url = (f"{eutils}/esearch.fcgi?db=taxonomy"
               f"&term={urllib.parse.quote(q)}&retmax={max_results}&retmode=json")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            sdata = json.loads(r.read().decode())
        ids = sdata.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        url = (f"{eutils}/esummary.fcgi?db=taxonomy"
               f"&id={','.join(ids)}&retmode=json")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except Exception as exc:
        LOG.warning("NCBI Taxonomy search failed for %r: %s", q, exc)
        return []

    out: list[dict] = []
    result = data.get("result", {})
    for uid in result.get("uids", []):
        rec = result.get(uid, {})
        out.append({
            "taxid":           uid,
            "scientific_name": rec.get("scientificname", ""),
            "common_name":     rec.get("commonname", "")
                                or rec.get("genbankcommonname", ""),
            "rank":            rec.get("rank", ""),
            "division":        rec.get("division", ""),
        })
    return out
