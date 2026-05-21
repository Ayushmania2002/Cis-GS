"""
cis_gs.cli_enrichment
=====================
CLI sub-commands for the enrichment extensions:

    cis-gs enrich-kegg      Run KEGG pathway enrichment on a gene list
    cis-gs id-convert       Auto-detect & translate gene IDs across naming systems

This file is intentionally self-contained - `cis_gs/cli.py` only needs one
import + one register() call to expose both commands.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _read_gene_list(path: str) -> list[str]:
    """One ID per line, blank lines and comments (#) ignored."""
    out: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line.split()[0])   # tolerate trailing annotation cols
    return out


def _save_df(df: pd.DataFrame, out: str | None, kind: str = "csv") -> None:
    if out is None:
        df.to_csv(sys.stdout, index=False, sep="\t")
        return
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    if out.endswith((".tsv", ".tab")):
        df.to_csv(out, index=False, sep="\t")
    else:
        df.to_csv(out, index=False)
    print(f"  → wrote {len(df)} rows to {out}")


# ─────────────────────────────────────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────────────────────────────────────

def cmd_enrich_kegg(args: argparse.Namespace) -> None:
    """KEGG pathway enrichment."""
    from cis_gs.enrichment.kegg import KEGGEnricher
    from cis_gs.enrichment.plots import dot_plot, bar_plot

    query = _read_gene_list(args.genes)
    print(f"[enrich-kegg] organism         : {args.organism}")
    print(f"[enrich-kegg] query genes      : {len(query)}")

    bg = _read_gene_list(args.background) if args.background else None
    enricher = KEGGEnricher(organism=args.organism, background=bg)
    result = enricher.enrich(
        query_genes=query,
        min_overlap=args.min_overlap,
        min_set_size=args.min_set_size,
        max_set_size=args.max_set_size,
    )
    print(f"[enrich-kegg] pathways returned: {len(result.table)}")
    for n in result.notes:
        print(f"  ! {n}")

    _save_df(result.table, args.out)

    if args.plot:
        out_dir = Path(args.out).parent if args.out else Path(".")
        dot_plot(result.table, top_n=args.top_n,
                 out_path=str(out_dir / "kegg_dotplot.png"),
                 title=f"KEGG enrichment ({args.organism})")
        bar_plot(result.table, top_n=args.top_n,
                 out_path=str(out_dir / "kegg_barplot.png"),
                 title=f"KEGG enrichment ({args.organism})")
        print(f"  → plots: {out_dir/'kegg_dotplot.png'},  {out_dir/'kegg_barplot.png'}")


def cmd_id_convert(args: argparse.Namespace) -> None:
    """Auto-detect input ID type and convert via MyGene.info."""
    from cis_gs.enrichment.idmap import IDConverter, consensus_id_type, detect_id_type

    ids = _read_gene_list(args.genes)
    print(f"[id-convert] input IDs        : {len(ids)}")
    print(f"[id-convert] dominant ID type : {consensus_id_type(ids)}")

    conv = IDConverter(species=args.species)
    df = conv.convert(ids)
    df.insert(1, "detected_type", [detect_id_type(g) for g in df["user_input"]])
    _save_df(df, args.out)



# ─────────────────────────────────────────────────────────────────────────────
# Parser registration  (called from cis_gs/cli.py)
# ─────────────────────────────────────────────────────────────────────────────
def register(sub: argparse._SubParsersAction) -> None:
    """Attach KEGG + ID-convert commands to the main subparser."""


    # enrich-kegg -------------------------------------------------------------
    p = sub.add_parser(
        "enrich-kegg",
        help="KEGG pathway enrichment on a gene list (any of ~7000 organisms)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "KEGG pathway enrichment via the KEGG REST API.\n"
            "Pathway / membership tables are pulled live from rest.kegg.jp and\n"
            "cached under ~/.cis-gs/kegg/ so the second run on the same organism\n"
            "is instantaneous.  Statistics: one-sided hypergeometric test\n"
            "phyper(k-1, n, totalN-n, listN) with Benjamini-Hochberg FDR.\n"
        ),
        epilog=(
            "Common organism codes:\n"
            "  ath = Arabidopsis     hsa = Human          mmu = Mouse\n"
            "  osa = Rice            zma = Maize          dme = Fly\n"
            "  cel = C. elegans      sce = Yeast          dre = Zebrafish\n"
            "\nExamples:\n"
            "  cis-gs enrich-kegg -g cluster_genes.txt --organism ath -o kegg.csv --plot\n"
            "  cis-gs enrich-kegg -g human_DEG.txt --organism hsa -o kegg.csv\n"
        ),
    )
    p.add_argument("-g", "--genes", required=True, metavar="FILE")
    p.add_argument("--organism", required=True,
                   help="3-letter KEGG organism code (e.g. ath, hsa, mmu, osa).")
    p.add_argument("--background", metavar="FILE",
                   help="Background gene list (default: all KEGG-known genes for the organism).")
    p.add_argument("--min-overlap",  type=int, default=2)
    p.add_argument("--min-set-size", type=int, default=5)
    p.add_argument("--max-set-size", type=int, default=2000)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--plot",  action="store_true")
    p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_enrich_kegg)

    # id-convert --------------------------------------------------------------
    p = sub.add_parser(
        "id-convert",
        help="Auto-detect & translate gene IDs (symbol ↔ Ensembl ↔ Entrez ↔ TAIR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Translate a heterogeneous gene-ID list to a canonical\n"
            "(user_input, ensembl_gene_id, entrez_id, symbol, species) frame.\n"
            "Uses an offline regex pre-classifier (recognises TAIR, RefSeq,\n"
            "Ensembl, UniProt, Entrez, rice / maize locus tag patterns) plus\n"
            "the MyGene.info REST API for any ID type the regex doesn't catch.\n"
            "Always pass --species when you know the organism - without it\n"
            "MyGene.info searches across every organism and may return wrong\n"
            "or empty hits, especially for non-model species.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs id-convert -g symbols.txt --species human -o mapped.tsv\n"
            "  cis-gs id-convert -g tair_ids.txt --species 3702 -o athaliana_map.tsv\n"
        ),
    )
    p.add_argument("-g", "--genes", required=True, metavar="FILE")
    p.add_argument("--species", default=None,
                   help="Taxon ID, common name (human/mouse/rat) or binomial.")
    p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_id_convert)
