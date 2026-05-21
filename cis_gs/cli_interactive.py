"""
cis_gs.cli_interactive
======================
Step-by-step interactive wizards for every Cis-GS workflow.

Why this exists
---------------
The GUI is the easiest way to drive Cis-GS, but many users work on
headless servers or HPC nodes where Qt is unavailable. The interactive
wizards in this module replicate the GUI experience inside a terminal:
- live searchable organism dropdowns become live prompts
  ("type a few letters of the organism, get matches with codes")
- multi-step workflows become numbered prompts with sensible defaults
- every typo gets a "did you mean ..." suggestion from difflib

Entry points (all callable from cli.py):
    interactive_kegg_enrichment()    - KEGG over-representation, step-by-step
    interactive_id_convert()         - LOC <-> Ensembl <-> Entrez mapping
    interactive_feed()               - motif hits + expression -> filtered CSV
    interactive_coexpr()             - co-expression network + modules
    interactive_kmeans()             - K-means clustering
    interactive_fetch()              - NCBI Assembly fetch
    interactive_extract()            - promoter extraction
    interactive_search()             - motif search
    interactive_wizard_menu()        - top-level menu

Helpers:
    did_you_mean(query, choices)     - fuzzy suggester
    prompt(...)                      - readline-aware input with default
    prompt_yes_no(...), prompt_int(...), prompt_float(...), prompt_path(...)
    prompt_kegg_organism()           - live KEGG organism filter
    prompt_ncbi_taxon()              - live NCBI Taxonomy filter
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI styling (auto-disabled on non-TTY / Windows-without-color)
# ---------------------------------------------------------------------------
_TTY = sys.stdout.isatty()
_C   = (lambda code: f"\033[{code}m") if _TTY else (lambda _: "")
BOLD = _C("1")
DIM  = _C("2")
CYAN = _C("36")
GREEN= _C("32")
YEL  = _C("33")
RED  = _C("31")
BLUE = _C("34")
RST  = _C("0")


def _heading(title: str) -> None:
    bar = "=" * max(len(title) + 4, 60)
    print()
    print(f"{CYAN}{bar}{RST}")
    print(f"{CYAN}{BOLD}  {title}{RST}")
    print(f"{CYAN}{bar}{RST}")


def _step(n: int, total: int, label: str) -> None:
    print(f"\n{BOLD}{CYAN}[Step {n}/{total}]{RST} {BOLD}{label}{RST}")


def _info(text: str) -> None:
    for line in text.splitlines():
        print(f"  {DIM}{line}{RST}")


def _ok(text: str) -> None:
    print(f"  {GREEN}OK{RST}  {text}")


def _warn(text: str) -> None:
    print(f"  {YEL}WARN{RST}  {text}")


def _err(text: str) -> None:
    print(f"  {RED}ERR{RST}  {text}")


# ---------------------------------------------------------------------------
# Fuzzy-match suggester ("did you mean ...?")
# ---------------------------------------------------------------------------
def did_you_mean(query: str, choices, n: int = 3, cutoff: float = 0.55) -> list[str]:
    """Return up to *n* close matches from *choices* using SequenceMatcher.

    Used by the top-level parser to suggest corrections when a user mistypes
    a subcommand:  'cis-gs entich-kegg' -> 'Did you mean enrich-kegg?'
    """
    return difflib.get_close_matches(str(query), list(choices), n=n, cutoff=cutoff)


# ---------------------------------------------------------------------------
# Generic prompt helpers
# ---------------------------------------------------------------------------
def prompt(label: str, default: str | None = None, allow_empty: bool = False) -> str:
    """Show 'label [default]: ' and return the user's response (or default)."""
    suffix = f" [{DIM}{default}{RST}]" if default is not None else ""
    while True:
        try:
            raw = input(f"  {label}{suffix}: ").strip()
        except EOFError:
            print()
            raise SystemExit(0)
        if not raw:
            if default is not None:
                return default
            if allow_empty:
                return ""
            _err("Empty input not allowed. Try again, or press Ctrl+C to abort.")
            continue
        return raw


def prompt_yes_no(label: str, default: bool = True) -> bool:
    suf = "Y/n" if default else "y/N"
    while True:
        raw = prompt(label + f" ({suf})", default="y" if default else "n")
        r = raw.strip().lower()
        if r in ("y", "yes", "1", "true", "t"):  return True
        if r in ("n", "no", "0", "false", "f"):  return False
        _err(f"Please answer y / n (got {raw!r}).")


def prompt_int(label: str, default: int | None = None,
               min_val: int | None = None, max_val: int | None = None) -> int:
    while True:
        raw = prompt(label, default=str(default) if default is not None else None)
        try:
            v = int(raw)
        except ValueError:
            _err(f"Not an integer: {raw!r}. Try again.")
            continue
        if min_val is not None and v < min_val:
            _err(f"Must be >= {min_val}.")
            continue
        if max_val is not None and v > max_val:
            _err(f"Must be <= {max_val}.")
            continue
        return v


def prompt_float(label: str, default: float | None = None,
                 min_val: float | None = None, max_val: float | None = None) -> float:
    while True:
        raw = prompt(label, default=f"{default}" if default is not None else None)
        try:
            v = float(raw)
        except ValueError:
            _err(f"Not a number: {raw!r}. Try again.")
            continue
        if min_val is not None and v < min_val:
            _err(f"Must be >= {min_val}.")
            continue
        if max_val is not None and v > max_val:
            _err(f"Must be <= {max_val}.")
            continue
        return v


def prompt_path(label: str, default: str | None = None,
                must_exist: bool = True) -> Path:
    while True:
        raw = prompt(label, default=default)
        p = Path(raw).expanduser()
        if must_exist and not p.exists():
            close = did_you_mean(p.name,
                [c.name for c in p.parent.glob("*")] if p.parent.exists() else [])
            _err(f"File not found: {p}")
            if close:
                _info("Did you mean one of these in the same folder?")
                for c in close:
                    _info(f"  - {c}")
            if not prompt_yes_no("Try again", default=True):
                raise SystemExit(1)
            continue
        return p


def prompt_choice(label: str, choices: list[str], default: int = 0) -> str:
    """Print a numbered menu, return the chosen string."""
    print(f"\n  {BOLD}{label}{RST}")
    for i, c in enumerate(choices, 1):
        marker = f"{GREEN}*{RST}" if i - 1 == default else " "
        print(f"   {marker} {i:>2}. {c}")
    while True:
        raw = prompt("Pick a number", default=str(default + 1))
        try:
            idx = int(raw) - 1
        except ValueError:
            _err(f"Not a number: {raw!r}.")
            continue
        if 0 <= idx < len(choices):
            return choices[idx]
        _err(f"Pick a number between 1 and {len(choices)}.")


# ---------------------------------------------------------------------------
# Live KEGG organism lookup (mirrors the GUI dropdown)
# ---------------------------------------------------------------------------
_KEGG_ORGS_CACHE: list[tuple[str, str, str]] | None = None
_UA = "Mozilla/5.0 (Cis-GS / Python urllib) https://github.com/Ayushmania2002/Cis-GS"


def _fetch_kegg_organisms() -> list[tuple[str, str, str]]:
    """Pull the live KEGG organism catalogue and return [(code, name, lineage), ...].

    Cached in memory for the lifetime of the process.
    """
    global _KEGG_ORGS_CACHE
    if _KEGG_ORGS_CACHE is not None:
        return _KEGG_ORGS_CACHE
    url = "https://rest.kegg.jp/list/organism"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        _err(f"Could not reach rest.kegg.jp ({exc}).  Using built-in fallback list.")
        # Tiny fallback so the prompt still works offline
        _KEGG_ORGS_CACHE = [
            ("ath", "Arabidopsis thaliana (thale cress)", "Plants"),
            ("osa", "Oryza sativa japonica (Japanese rice)", "Plants"),
            ("zma", "Zea mays (maize)", "Plants"),
            ("gma", "Glycine max (soybean)", "Plants"),
            ("ahf", "Arachis hypogaea (peanut)", "Plants"),
            ("sly", "Solanum lycopersicum (tomato)", "Plants"),
            ("hsa", "Homo sapiens (human)", "Animals"),
            ("mmu", "Mus musculus (mouse)", "Animals"),
            ("rno", "Rattus norvegicus (rat)", "Animals"),
            ("dre", "Danio rerio (zebrafish)", "Animals"),
            ("dme", "Drosophila melanogaster (fruit fly)", "Animals"),
            ("cel", "Caenorhabditis elegans (nematode)", "Animals"),
            ("sce", "Saccharomyces cerevisiae (yeast)", "Fungi"),
            ("eco", "Escherichia coli K-12 MG1655", "Bacteria"),
        ]
        return _KEGG_ORGS_CACHE

    out: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) >= 3:
            code = cols[1].strip()
            name = cols[2].strip()
            lineage = cols[3].strip() if len(cols) > 3 else ""
            out.append((code, name, lineage))
    _KEGG_ORGS_CACHE = out
    return out


def prompt_kegg_organism() -> str:
    """Interactive KEGG organism picker (live filter against ~11,700 entries).

    Returns the 3-4 letter KEGG organism code (ahf, hsa, ath, etc.).
    """
    print(f"  {DIM}Loading KEGG organism list from rest.kegg.jp ...{RST}")
    orgs = _fetch_kegg_organisms()
    print(f"  {GREEN}{len(orgs):,} organisms loaded.{RST}")

    print()
    _info("Type a few letters of the organism name (or the KEGG code).")
    _info("Examples: 'arabidopsis', 'rice', 'peanut', 'human', 'ath', 'ahf', 'hsa'")
    _info("Press Enter on an empty line to abort.")

    while True:
        q = prompt("organism", allow_empty=True).strip()
        if not q:
            raise SystemExit("Aborted by user.")
        ql = q.lower()

        # Exact code match wins immediately
        for code, name, lineage in orgs:
            if code.lower() == ql:
                if prompt_yes_no(f"Use exact match '{code}' ({name})?", default=True):
                    return code

        # Substring match in code or name
        matches = [
            (code, name, lineage) for code, name, lineage in orgs
            if ql in code.lower() or ql in name.lower()
        ]
        # Common-name shortcuts the GUI also handles
        aliases = {
            "rice":        "oryza sativa",
            "peanut":      "arachis hypogaea",
            "groundnut":   "arachis hypogaea",
            "wheat":       "triticum aestivum",
            "barley":      "hordeum vulgare",
            "maize":       "zea mays",
            "corn":        "zea mays",
            "soybean":     "glycine max",
            "tomato":      "solanum lycopersicum",
            "potato":      "solanum tuberosum",
            "human":       "homo sapiens",
            "mouse":       "mus musculus",
            "rat":         "rattus norvegicus",
            "zebrafish":   "danio rerio",
            "fly":         "drosophila melanogaster",
            "fruit fly":   "drosophila melanogaster",
            "worm":        "caenorhabditis elegans",
            "yeast":       "saccharomyces cerevisiae",
            "ecoli":       "escherichia coli",
            "e. coli":     "escherichia coli",
            "thale cress": "arabidopsis thaliana",
            "cattle":      "bos taurus",
            "pig":         "sus scrofa",
            "chicken":     "gallus gallus",
        }
        if not matches and ql in aliases:
            alias = aliases[ql].lower()
            matches = [(c, n, l) for c, n, l in orgs if alias in n.lower()]
            if matches:
                _info(f"(treating '{q}' as alias for '{aliases[ql]}')")

        if not matches:
            # Fuzzy fallback over the species names
            names = [n for _, n, _ in orgs]
            close = did_you_mean(q, names, n=5, cutoff=0.5)
            _err(f"No KEGG organism matched '{q}'.")
            if close:
                _info("Did you mean one of these?")
                for c in close:
                    _info(f"  - {c}")
            continue

        # Show top 20 matches; user picks by number, or refines the query
        matches = matches[:20]
        print(f"\n  {BOLD}{len(matches)} match(es) for '{q}':{RST}")
        for i, (code, name, lineage) in enumerate(matches, 1):
            tag = ""
            ll = lineage.lower()
            if   "plant"    in ll: tag = f" {GREEN}[Plants]{RST}"
            elif "animal"   in ll or "vertebrate" in ll or "insect" in ll: tag = f" {BLUE}[Animals]{RST}"
            elif "fung"     in ll: tag = " [Fungi]"
            elif "bacter"   in ll or "prokaryote" in ll: tag = " [Bacteria]"
            elif "arch"     in ll: tag = " [Archaea]"
            elif "vir"      in ll: tag = " [Viruses]"
            print(f"    {i:>3}.  {BOLD}{code}{RST:<8}  {name}{tag}")
        if len(matches) >= 20:
            print(f"    {DIM}(showing first 20; refine your query to see more){RST}")

        sel = prompt("Pick a number (or press Enter to search again)",
                     allow_empty=True)
        if not sel.strip():
            continue
        try:
            idx = int(sel) - 1
            if 0 <= idx < len(matches):
                return matches[idx][0]
        except ValueError:
            pass
        _err(f"Not a valid number: {sel!r}. Try again.")


# ---------------------------------------------------------------------------
# Live NCBI Taxonomy lookup (mirrors the GUI smart dropdown)
# ---------------------------------------------------------------------------
def prompt_ncbi_taxon() -> str:
    """Interactive NCBI Taxonomy ID picker.  Returns the chosen taxid."""
    BUILTIN = [
        ("9606",   "Homo sapiens (human)"),
        ("10090",  "Mus musculus (mouse)"),
        ("10116",  "Rattus norvegicus (rat)"),
        ("7227",   "Drosophila melanogaster (fly)"),
        ("6239",   "Caenorhabditis elegans (worm)"),
        ("7955",   "Danio rerio (zebrafish)"),
        ("3702",   "Arabidopsis thaliana"),
        ("4530",   "Oryza sativa (rice)"),
        ("39947",  "Oryza sativa Japonica Group"),
        ("4577",   "Zea mays (maize)"),
        ("3847",   "Glycine max (soybean)"),
        ("3818",   "Arachis hypogaea (peanut)"),
        ("4081",   "Solanum lycopersicum (tomato)"),
        ("4565",   "Triticum aestivum (wheat)"),
        ("4513",   "Hordeum vulgare (barley)"),
        ("559292", "Saccharomyces cerevisiae (yeast)"),
        ("562",    "Escherichia coli"),
    ]
    print()
    _info("Type the organism name (English or scientific), or paste a numeric taxon ID.")
    _info("Examples: 'arabidopsis', 'rice', 'peanut', '3818', '9606'")
    _info("Press Enter on an empty line to abort.")

    while True:
        q = prompt("organism / taxon", allow_empty=True).strip()
        if not q:
            raise SystemExit("Aborted by user.")
        if q.isdigit():
            return q

        # First search the built-in list
        ql = q.lower()
        builtin_hits = [(t, n) for t, n in BUILTIN if ql in n.lower()]
        live_hits: list[tuple[str, str]] = []

        # Then query NCBI Taxonomy live
        try:
            url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                   f"?db=taxonomy&term={urllib.parse.quote(q)}&retmax=15&retmode=json")
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            ids = data.get("esearchresult", {}).get("idlist", [])
            if ids:
                url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                       f"?db=taxonomy&id={','.join(ids)}&retmode=json")
                req = urllib.request.Request(url, headers={"User-Agent": _UA})
                with urllib.request.urlopen(req, timeout=15) as r:
                    summ = json.loads(r.read().decode())
                result = summ.get("result", {})
                for uid in result.get("uids", []):
                    rec = result.get(uid, {})
                    sci = rec.get("scientificname", "")
                    common = (rec.get("commonname")
                              or rec.get("genbankcommonname") or "")
                    label = sci + (f" ({common})" if common else "")
                    live_hits.append((uid, label))
        except Exception as exc:
            _warn(f"NCBI Taxonomy live search failed: {exc}")

        # Merge, deduplicate by taxid, built-in first
        seen, merged = set(), []
        for tid, label in builtin_hits + live_hits:
            if tid in seen:
                continue
            seen.add(tid)
            merged.append((tid, label))

        if not merged:
            names = [n for _, n in BUILTIN]
            close = did_you_mean(q, names, n=5)
            _err(f"No organism matched '{q}'.")
            if close:
                _info("Did you mean one of these built-in entries?")
                for c in close:
                    _info(f"  - {c}")
            continue

        print(f"\n  {BOLD}{len(merged)} match(es) for '{q}':{RST}")
        for i, (tid, label) in enumerate(merged[:20], 1):
            print(f"    {i:>3}.  {BOLD}{tid:>7s}{RST}  {label}")
        sel = prompt("Pick a number (or press Enter to search again)",
                     allow_empty=True)
        if not sel.strip():
            continue
        try:
            idx = int(sel) - 1
            if 0 <= idx < len(merged):
                return merged[idx][0]
        except ValueError:
            pass
        _err(f"Not a valid number: {sel!r}. Try again.")


# ---------------------------------------------------------------------------
# Top-level menu
# ---------------------------------------------------------------------------
_WORKFLOWS = [
    ("KEGG pathway enrichment",     "interactive_kegg_enrichment"),
    ("Gene-ID conversion",          "interactive_id_convert"),
    ("Expression Feeding (filter)", "interactive_feed"),
    ("Co-expression network",       "interactive_coexpr"),
    ("K-means clustering",          "interactive_kmeans"),
    ("NCBI genome fetch",           "interactive_fetch"),
    ("Promoter extraction (Step 1)","interactive_extract"),
    ("Motif search (Step 2)",       "interactive_search"),
]


def interactive_wizard_menu() -> int:
    """Top-level menu shown by `cis-gs wizard` with no further arguments."""
    _heading("Cis-GS Interactive Wizard")
    _info("Step-by-step assistant for every Cis-GS workflow.")
    _info("Each wizard mirrors the corresponding GUI tab.")
    choices = [label for label, _ in _WORKFLOWS]
    pick = prompt_choice("Which workflow would you like to run?", choices)
    fn_name = dict(_WORKFLOWS)[pick]
    fn = globals().get(fn_name)
    if fn is None:
        _err(f"Wizard '{fn_name}' not implemented yet.")
        return 1
    return fn()


# ---------------------------------------------------------------------------
# KEGG enrichment wizard (the user's headline example)
# ---------------------------------------------------------------------------
def interactive_kegg_enrichment() -> int:
    _heading("KEGG Pathway Enrichment Wizard")
    _info("This wizard mirrors the GUI's 'Enrichment > KEGG Pathway' tab.")
    _info("You will be guided through 5 steps:")
    _info("  1. Pick the KEGG organism (live search of ~11,700 entries)")
    _info("  2. Provide the query gene list (CSV / TSV / TXT)")
    _info("  3. (Optional) provide a background gene list")
    _info("  4. Configure pathway-size and overlap filters")
    _info("  5. Run the enrichment and save the results")

    # ---- Step 1: organism ------------------------------------------------
    _step(1, 5, "KEGG organism")
    organism = prompt_kegg_organism()
    _ok(f"Using KEGG organism code: {BOLD}{organism}{RST}")

    # ---- Step 2: query gene list ----------------------------------------
    _step(2, 5, "Query gene list")
    _info("Path to a CSV, TSV or plain-text file containing your gene IDs")
    _info("(one ID per line, OR a column named 'gene_id' / 'user_input').")
    _info("Cis-GS auto-strips GFF3 prefixes ('gene-', 'rna-'), the 'LOC'")
    _info("prefix on numeric IDs and any RefSeq '.1' / '.2' version suffix,")
    _info("so any of these spellings refer to the same KEGG entry:")
    _info("    gene-LOC112706767  ==  LOC112706767  ==  112706767  ==  ahf:112706767")
    query_path = prompt_path("Gene list file", must_exist=True)

    # ---- Step 3: background ---------------------------------------------
    _step(3, 5, "Background gene list (optional)")
    _info("By default, Cis-GS uses every KEGG-known gene for the organism")
    _info("as the universe.  Provide a custom background only if your")
    _info("upstream filtering already shrunk the gene space.")
    bg_path = None
    if prompt_yes_no("Provide a custom background list?", default=False):
        bg_path = prompt_path("Background file", must_exist=True)

    # ---- Step 4: filters ------------------------------------------------
    _step(4, 5, "Filters")
    min_overlap  = prompt_int("Min overlap (k >= ?)", default=2,  min_val=1)
    min_set_size = prompt_int("Min pathway size",       default=5,  min_val=1)
    max_set_size = prompt_int("Max pathway size",       default=2000, min_val=10)

    # ---- Step 5: run & save ---------------------------------------------
    _step(5, 5, "Run KEGG enrichment")
    default_out = f"{organism}_kegg_enrichment.csv"
    out_csv = prompt("Output CSV path", default=default_out)
    save_plots = prompt_yes_no("Also save dot-plot and bar-plot PNGs?", default=True)

    print()
    _info("Calling KEGGEnricher.enrich() ...")
    try:
        from cis_gs.enrichment.kegg import KEGGEnricher
        from cis_gs.cli_enrichment import _read_gene_list, _save_df
    except ImportError as exc:
        _err(f"Cannot import the enrichment back-end: {exc}")
        return 1

    query = _read_gene_list(str(query_path))
    bg    = _read_gene_list(str(bg_path)) if bg_path else None
    print(f"  Query genes : {len(query):,}")
    if bg is not None:
        print(f"  Background  : {len(bg):,}")

    try:
        result = KEGGEnricher(organism=organism, background=bg).enrich(
            query_genes=query,
            min_overlap=min_overlap,
            min_set_size=min_set_size,
            max_set_size=max_set_size,
        )
    except Exception as exc:
        _err(f"KEGG enrichment failed: {exc}")
        return 1

    print()
    print(f"  Pathways returned : {len(result.table):,}")
    print(f"  Query used        : {result.n_query} / {len(query)}")
    print(f"  Universe (KEGG)   : {result.n_universe:,}")
    for note in result.notes:
        _warn(note)

    _save_df(result.table, out_csv)
    if save_plots and not result.table.empty:
        try:
            from cis_gs.enrichment.plots import dot_plot, bar_plot
            out_dir = Path(out_csv).parent
            dot_plot(result.table, top_n=20,
                     out_path=str(out_dir / "kegg_dotplot.png"),
                     title=f"KEGG enrichment ({organism})")
            bar_plot(result.table, top_n=20,
                     out_path=str(out_dir / "kegg_barplot.png"),
                     title=f"KEGG enrichment ({organism})")
            _ok(f"Plots saved to {out_dir}/kegg_dotplot.png and kegg_barplot.png")
        except Exception as exc:
            _warn(f"Plotting failed: {exc}")
    _ok("KEGG enrichment complete.")
    return 0


# ---------------------------------------------------------------------------
# ID-Convert wizard
# ---------------------------------------------------------------------------
def interactive_id_convert() -> int:
    _heading("Gene-ID Conversion Wizard")
    _info("Translates gene IDs across naming systems (LOC <-> Ensembl <->")
    _info("Entrez <-> symbol) using the MyGene.info REST API.  Mirrors the")
    _info("GUI's 'Enrichment > ID Convert' tab.")

    _step(1, 3, "Species (REQUIRED)")
    _info("MyGene.info needs a species hint - without it the matcher searches")
    _info("across every organism and returns junk for non-model species.")
    taxon = prompt_ncbi_taxon()
    _ok(f"Species taxon ID: {BOLD}{taxon}{RST}")

    _step(2, 3, "Input gene list")
    in_path = prompt_path("Gene list file (CSV / TSV / TXT)", must_exist=True)

    _step(3, 3, "Output")
    out_path = prompt("Output TSV path", default="id_mapping.tsv")

    try:
        from cis_gs.enrichment.idmap import IDConverter, detect_id_type
        from cis_gs.cli_enrichment import _read_gene_list, _save_df
    except ImportError as exc:
        _err(f"Cannot import idmap backend: {exc}")
        return 1

    ids = _read_gene_list(str(in_path))
    print(f"\n  Translating {len(ids):,} IDs via MyGene.info batch endpoint ...")

    def _progress(done, total, label):
        bar_w = 30
        filled = int(bar_w * done / max(total, 1))
        bar = "#" * filled + "-" * (bar_w - filled)
        pct = int(100 * done / max(total, 1))
        sys.stdout.write(f"\r  [{bar}] {pct:3d}%  {label[:60]:<60s}")
        sys.stdout.flush()

    try:
        conv = IDConverter(species=taxon)
        df = conv.convert(ids, progress_callback=_progress)
    except Exception as exc:
        print()
        _err(f"Conversion failed: {exc}")
        return 1
    print()

    if not df.empty:
        df.insert(1, "detected_type", [detect_id_type(g) for g in df["user_input"]])
    n_entrez  = int(df["entrez_id"].notna().sum())  if not df.empty else 0
    n_ensembl = int(df["ensembl_gene_id"].notna().sum()) if not df.empty else 0
    print(f"  Resolved {len(df):,} rows  "
          f"({n_entrez:,} with Entrez ID, {n_ensembl:,} with Ensembl ID).")
    _save_df(df, out_path)
    _ok("ID conversion complete.")
    return 0


# ---------------------------------------------------------------------------
# Expression-Feeding wizard
# ---------------------------------------------------------------------------
def interactive_feed() -> int:
    _heading("Expression Feeding Wizard")
    _info("Match motif-hit genes with an expression matrix to produce a")
    _info("filtered expression CSV containing only the motif-hit genes.")
    _info("Mirrors the GUI's 'Expression Feeding' tab.")

    _step(1, 4, "Motif hits file")
    motif_path = prompt_path("Motif hits CSV / TSV / TXT", must_exist=True)

    _step(2, 4, "Expression matrix")
    expr_path = prompt_path("Expression CSV / TSV / TXT", must_exist=True)

    _step(3, 4, "Optional gene-ID mapping (Method 2 in the GUI)")
    map_path = None
    if prompt_yes_no("Upload a 2-column motif_id -> expression_id mapping file?",
                     default=False):
        map_path = prompt_path("Mapping CSV / TSV", must_exist=True)

    _step(4, 4, "Output")
    out_path = prompt("Filtered expression CSV path", default="filtered_expression.csv")

    # Build argparse-like Namespace and delegate to existing handler
    import argparse as _ap
    args = _ap.Namespace(
        motif_csv=str(motif_path),
        expr_csv=str(expr_path),
        out=str(out_path),
        mapping=str(map_path) if map_path else None,
        # Common defaults from the existing feed command
    )
    try:
        from cis_gs.cli import cmd_feed
    except ImportError as exc:
        _err(f"Could not load cmd_feed: {exc}")
        return 1
    try:
        cmd_feed(args)
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)
    except Exception as exc:
        _err(f"Feed step failed: {exc}")
        return 1
    _ok("Expression filtering complete.")
    return 0


# ---------------------------------------------------------------------------
# Co-expression wizard
# ---------------------------------------------------------------------------
def interactive_coexpr() -> int:
    _heading("Co-expression Network Wizard")
    _info("Build a Pearson/Spearman gene-gene correlation network and split")
    _info("it into modules (Louvain or connected components).")

    _step(1, 5, "Filtered expression CSV")
    expr_path = prompt_path("Expression matrix", must_exist=True)

    _step(2, 5, "Normalization")
    norm = prompt_choice("Normalization method",
                        ["log2", "zscore", "quantile", "none"], default=0)

    _step(3, 5, "Correlation method")
    corr = prompt_choice("Correlation method", ["pearson", "spearman"], default=0)

    _step(4, 5, "Threshold and module-detection method")
    threshold = prompt_float("Correlation threshold |r| >= ?",
                             default=0.7, min_val=0.0, max_val=1.0)
    method = prompt_choice("Module detection",
                           ["louvain", "connected_components"], default=0)

    _step(5, 5, "Output folder")
    out_dir = prompt("Output folder", default="./coexpr_results")

    import argparse as _ap
    args = _ap.Namespace(
        expr_csv=str(expr_path),
        out=out_dir,
        normalize=norm,
        correlation=corr,
        threshold=threshold,
        cluster=method,
    )
    try:
        from cis_gs.cli import cmd_coexpr
        cmd_coexpr(args)
    except Exception as exc:
        _err(f"Coexpr step failed: {exc}")
        return 1
    _ok("Co-expression analysis complete.")
    return 0


# ---------------------------------------------------------------------------
# K-means wizard
# ---------------------------------------------------------------------------
def interactive_kmeans() -> int:
    _heading("K-means Clustering Wizard")
    _step(1, 3, "Expression CSV")
    expr_path = prompt_path("Expression matrix", must_exist=True)
    _step(2, 3, "Number of clusters (K)")
    k = prompt_int("How many clusters?", default=6, min_val=2, max_val=50)
    _step(3, 3, "Output folder")
    out_dir = prompt("Output folder", default="./kmeans_results")

    import argparse as _ap
    args = _ap.Namespace(expr_csv=str(expr_path), out=out_dir, k=k)
    try:
        from cis_gs.cli import cmd_kmeans
        cmd_kmeans(args)
    except Exception as exc:
        _err(f"K-means step failed: {exc}")
        return 1
    _ok("K-means clustering complete.")
    return 0


# ---------------------------------------------------------------------------
# NCBI fetch wizard
# ---------------------------------------------------------------------------
def interactive_fetch() -> int:
    _heading("NCBI Genome Fetch Wizard")
    _info("Download a genome FASTA + GFF3 annotation from NCBI.")
    _info("Mirrors the GUI's 'NCBI Fetch' tab.")
    _step(1, 2, "Assembly accession")
    _info("Format: GCF_xxxxxxxxx.x  (RefSeq, has annotation)")
    _info("    or  GCA_xxxxxxxxx.x  (GenBank, may lack annotation)")
    _info("Find accessions at https://www.ncbi.nlm.nih.gov/assembly")
    acc = prompt("Assembly accession (e.g. GCF_000001735.4)")

    _step(2, 2, "Output folder")
    out_dir = prompt("Output folder", default="./genome")

    import argparse as _ap
    args = _ap.Namespace(accession=acc, out=out_dir)
    try:
        from cis_gs.cli import cmd_fetch
        cmd_fetch(args)
    except Exception as exc:
        _err(f"NCBI fetch failed: {exc}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Promoter-extract wizard
# ---------------------------------------------------------------------------
def interactive_extract() -> int:
    _heading("Promoter Extraction Wizard (Step 1)")
    _step(1, 4, "Genome FASTA")
    fasta = prompt_path("Genome FASTA file", must_exist=True)
    _step(2, 4, "Annotation GFF3")
    gff = prompt_path("Annotation GFF3 file", must_exist=True)
    _step(3, 4, "Promoter length")
    length = prompt_int("Bases upstream of TSS to extract", default=1500,
                       min_val=50, max_val=20000)
    _step(4, 4, "Output FASTA")
    out_fa = prompt("Output promoter FASTA", default="promoters.fasta")

    import argparse as _ap
    args = _ap.Namespace(genome=str(fasta), gff=str(gff),
                         length=length, out=out_fa)
    try:
        from cis_gs.cli import cmd_extract
        cmd_extract(args)
    except Exception as exc:
        _err(f"Extraction failed: {exc}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Motif-search wizard
# ---------------------------------------------------------------------------
def interactive_search() -> int:
    _heading("Motif Search Wizard (Step 2)")
    _step(1, 3, "Promoter FASTA")
    fasta = prompt_path("Promoter FASTA", must_exist=True)

    _step(2, 3, "Motifs")
    _info("Provide motifs in one of two ways:")
    _info("  a) A motifs file (one 'NAME<tab>SEQUENCE' per line), OR")
    _info("  b) Inline motif sequences (you'll be asked one at a time).")
    motif_file = None
    inline = []
    if prompt_yes_no("Use a motifs file?", default=True):
        motif_file = prompt_path("Motifs file", must_exist=True)
    else:
        _info("Enter motifs one at a time (IUPAC OK).  Empty line ends entry.")
        while True:
            m = prompt("motif", allow_empty=True)
            if not m.strip():
                break
            inline.append(m.strip())

    _step(3, 3, "Output")
    out_path = prompt("Output hits CSV", default="motif_hits.csv")

    import argparse as _ap
    args = _ap.Namespace(
        promoters_fasta=str(fasta),
        motifs_file=str(motif_file) if motif_file else None,
        motif=inline,
        out=out_path,
    )
    try:
        from cis_gs.cli import cmd_search
        cmd_search(args)
    except Exception as exc:
        _err(f"Motif search failed: {exc}")
        return 1
    return 0
