"""
Cis-GS Command-Line Interface
══════════════════════════════════════════════════════════════════════════════

Run without arguments to launch the GUI:
    cis-gs

Analysis pipeline (run in order):
    cis-gs fetch    <assembly_id>           Download genome from NCBI
    cis-gs extract  <fasta> <gff3>          Extract promoter sequences
    cis-gs search   <fasta> -m PATTERN      Scan promoters for TFBS motifs
    cis-gs logo     <hits.csv>              Build sequence logos from hits
    cis-gs feed     <hits.csv> <expr.csv>   Filter expression to motif genes
    cis-gs coexpr   <expr.csv>              Co-expression network analysis
    cis-gs kmeans   <expr.csv>              K-means temporal clustering

Transcription factor database commands:
    cis-gs tfdb species                     List all PlantTFDB species
    cis-gs tfdb download  <code>            Download PlantTFDB motifs
    cis-gs tfdb sources                     List JASPAR / HOCOMOCO datasets
    cis-gs tfdb download-db <source_id>     Download JASPAR / HOCOMOCO
    cis-gs tfdb filter <meme_file>          Filter & export motifs to a text file

Enrichment + ID-conversion commands:
    cis-gs enrich-go        -g genes.txt --gaf … --obo go.obo
                              GO over-representation (BP/CC/MF)
    cis-gs enrich-kegg      -g genes.txt --organism ath
                              KEGG pathway enrichment via KEGG REST
    cis-gs id-convert       -g ids.txt --species human
                              Auto-detect & translate gene IDs
    cis-gs fetch-expression --geo GSE16997 -o expr.csv
                              Public RNA-seq matrix (GEO/Atlas/Ensembl Plants)
"""

import argparse
import sys
import ssl as _ssl
import urllib.request
import urllib.error
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _ssl_ctx():
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = _ssl.CERT_NONE
    return ctx

def _make_req(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36")
    req.add_header("Accept", "*/*")
    return req

def _download_file(url, dest_path, label="", progress=True):
    """Download a single URL to dest_path. Returns (success, error_msg)."""
    try:
        req = _make_req(url)
        with urllib.request.urlopen(req, timeout=120, context=_ssl_ctx()) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            received = 0
            with open(dest_path, "wb") as fout:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fout.write(chunk)
                    received += len(chunk)
                    if progress and total:
                        pct = int(received * 100 / total)
                        mb  = received / (1024 * 1024)
                        tmb = total / (1024 * 1024)
                        print(f"\r  {label}: {mb:.1f} / {tmb:.1f} MB ({pct}%)", end="", flush=True)
                    elif progress:
                        mb = received / (1024 * 1024)
                        print(f"\r  {label}: {mb:.1f} MB", end="", flush=True)
        if progress:
            print()
        return True, ""
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def _try_urls(urls, dest_path, label=""):
    """Try each URL in order. Returns (success, error_summary)."""
    errors = []
    for url in urls:
        ok, err = _download_file(url, dest_path, label=label)
        if ok and dest_path.exists() and dest_path.stat().st_size > 0:
            return True, ""
        errors.append(f"  • {url}\n    → {err or 'empty file'}")
        if dest_path.exists():
            dest_path.unlink()
    return False, "\n".join(errors)

def _setup_entrez_email():
    from Bio import Entrez
    email_file = Path.home() / "CisGS-Workspace" / ".ncbi_email"
    if email_file.exists():
        try:
            email = email_file.read_text().strip()
            if email and "@" in email:
                Entrez.email = email
                return
        except Exception:
            pass
    Entrez.email = "cisgs-cli@example.com"

def _normalize_gene_id(gid):
    gid = str(gid).strip()
    for prefix in ("gene-", "rna-", "cds-", "Gene:", "GENE:"):
        if gid.lower().startswith(prefix.lower()):
            gid = gid[len(prefix):]
            break
    for sep in ("|", " ", "\t", ":", ";"):
        if sep in gid:
            gid = gid.split(sep)[0].strip()
            break
    return gid


# ══════════════════════════════════════════════════════════════════════════════
# GUI LAUNCHER
# ══════════════════════════════════════════════════════════════════════════════

def cmd_gui(args):
    from cis_gs.app import main
    main()


# ══════════════════════════════════════════════════════════════════════════════
# FETCH  -  download genome from NCBI
# ══════════════════════════════════════════════════════════════════════════════

def cmd_fetch(args):
    _setup_entrez_email()
    from cis_gs.app import download_assembly_files

    acc    = args.assembly
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    def _progress(downloaded, total, label):
        if total > 0:
            pct = int(downloaded * 100 / total)
            mb  = downloaded / (1024 * 1024)
            tmb = total / (1024 * 1024)
            print(f"\r  {label}: {mb:.1f} / {tmb:.1f} MB ({pct}%)", end="", flush=True)
        else:
            mb = downloaded / (1024 * 1024)
            print(f"\r  {label}: {mb:.1f} MB", end="", flush=True)

    print(f"Fetching assembly {acc} from NCBI...")
    fasta_text, gff_text, message = download_assembly_files(
        acc, not args.no_fasta, not args.no_gff, progress_callback=_progress
    )
    print()

    if fasta_text:
        p = outdir / f"{acc}_genomic.fasta"
        p.write_text(fasta_text, encoding="utf-8")
        print(f"  Saved FASTA : {p}")
    if gff_text:
        p = outdir / f"{acc}_genomic.gff3"
        p.write_text(gff_text, encoding="utf-8")
        print(f"  Saved GFF3  : {p}")

    if not fasta_text and not gff_text:
        print(f"\n  ERROR: {message}")
        # Tip: Make sure the accession is correct (e.g. GCF_000001735.4 not GCF_000001735)
        # Tip: You need an internet connection to access NCBI FTP
        # Tip: NCBI sometimes times out - wait a moment and try again
        # Tip: Run 'cis-gs fetch --help' to see all options
        sys.exit(1)
    print(f"  {message}")


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACT  -  extract promoter sequences
# ══════════════════════════════════════════════════════════════════════════════

def cmd_extract(args):
    from cis_gs.app import extract_promoters

    fasta     = Path(args.fasta)
    gff3      = Path(args.gff3)
    out_fasta = Path(args.output)
    out_table = out_fasta.with_suffix(".tsv")

    # Validate inputs before doing any work
    if not fasta.exists():
        print(f"\n  ERROR: FASTA file not found: {fasta}")
        # Tip: Run 'cis-gs fetch <assembly_id>' first to download the genome FASTA
        # Tip: Use the full path if the file is in a different directory
        sys.exit(1)
    if not gff3.exists():
        print(f"\n  ERROR: GFF3 annotation file not found: {gff3}")
        # Tip: Run 'cis-gs fetch <assembly_id>' to download the GFF3 annotation file
        # Tip: The GFF3 must match the same assembly as the FASTA
        sys.exit(1)

    print(f"Extracting {args.length} bp upstream promoter sequences...")
    print(f"  Genome     : {fasta}")
    print(f"  Annotation : {gff3}")

    try:
        extract_promoters(str(fasta), str(gff3), out_fasta, out_table,
                          promoter_len=args.length)
    except Exception as e:
        print(f"\n  ERROR during extraction: {e}")
        # Tip: Make sure your GFF3 file uses the same chromosome names as the FASTA
        # Tip: Some GFF3 files use 'Chr1' while FASTA uses '1' - they must match
        # Tip: Run 'cis-gs extract --help' for all available options
        sys.exit(1)

    print(f"  FASTA out  : {out_fasta}")
    print(f"  Table out  : {out_table}")
    print("  Done.")


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH  -  scan promoters for TFBS motif hits
# ══════════════════════════════════════════════════════════════════════════════

def cmd_search(args):
    import pandas as pd
    from cis_gs.app import scan_fasta_for_motifs

    fasta = Path(args.fasta)
    if not fasta.exists():
        print(f"\n  ERROR: Promoter FASTA file not found: {fasta}")
        # Tip: Run 'cis-gs extract <genome.fasta> <genome.gff3>' to generate this file
        # Tip: The output of 'cis-gs extract' is named 'promoters.fasta' by default
        sys.exit(1)

    # Build motif list from -m flags or --motifs-file
    motifs = []
    if args.motif:
        for i, seq in enumerate(args.motif):
            motifs.append((f"motif_{i+1}", seq.strip().upper()))
    elif args.motifs_file:
        mpath = Path(args.motifs_file)
        if not mpath.exists():
            print(f"\n  ERROR: Motifs file not found: {mpath}")
            # Tip: Create a motifs file with one motif per line: NAME<TAB>IUPAC_PATTERN
            # Tip: Use 'cis-gs tfdb filter <meme_file> -o motifs.txt' to export from a DB
            # Tip: Example motif file line:  ERF|AT1G00010  GCAGCCGCC
            sys.exit(1)
        for line in mpath.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                name, seq = line.split("\t", 1)
            elif ": " in line:
                name, seq = line.split(": ", 1)
            else:
                name, seq = line, line
            motifs.append((name.strip(), seq.strip().upper()))
    else:
        print("\n  ERROR: No motifs specified.")
        print("  Provide motifs with -m PATTERN or --motifs-file FILE")
        # Tip: Single motif:   cis-gs search promoters.fasta -m ACGTG
        # Tip: Multiple:       cis-gs search promoters.fasta -m ACGTG -m RGATCY
        # Tip: From a file:    cis-gs search promoters.fasta --motifs-file motifs.txt
        # Tip: Export motifs:  cis-gs tfdb filter Ath_TF_binding_motifs.meme -o motifs.txt
        sys.exit(1)

    if not motifs:
        print("\n  ERROR: Motifs file is empty or has no valid entries.")
        # Tip: Each line in the motifs file should be:  NAME<TAB>IUPAC_SEQUENCE
        # Tip: Lines starting with '#' are treated as comments and ignored
        sys.exit(1)

    output = Path(args.output)
    print(f"Scanning {fasta.name} for {len(motifs)} motif(s)...")
    print(f"  IUPAC mode   : {'on (default)' if not args.no_iupac else 'off (literal match)'}")
    print(f"  Reverse comp : {'off' if args.no_revcomp else 'on (default)'}")

    try:
        df = scan_fasta_for_motifs(
            str(fasta), motifs,
            treat_as_iupac=not args.no_iupac,
            allow_overlaps=True,
            search_revcomp=not args.no_revcomp,
        )
    except Exception as e:
        print(f"\n  ERROR during scan: {e}")
        # Tip: Make sure the FASTA file is not corrupted
        # Tip: Try running with --no-iupac if you have non-standard characters in your motifs
        sys.exit(1)

    if isinstance(df, __import__("pandas").DataFrame) and not df.empty:
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        print(f"  {len(df)} hit(s) found")
        print(f"  Saved: {output}")
        print(f"\n  Next step: cis-gs logo {output}  OR  cis-gs feed {output} expression.csv")
    else:
        print("  No hits found.")
        # Tip: Your motif pattern may be too strict - try a shorter or more degenerate IUPAC
        # Tip: Check that gene IDs in your FASTA headers match those in the expression file
        # Tip: Try with --no-revcomp if you only want to search the forward strand


# ══════════════════════════════════════════════════════════════════════════════
# BATCH  -  multi-species extract + search in one run
# ══════════════════════════════════════════════════════════════════════════════

def cmd_batch(args):
    """Run promoter extraction + motif search for every species in a manifest."""
    import pandas as pd
    from cis_gs.app import extract_promoters, scan_fasta_for_motifs

    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"\n  ERROR: Manifest file not found: {manifest}")
        print("  Create a TSV with columns: species_name<TAB>fasta<TAB>gff3[<TAB>upstream_bp]")
        sys.exit(1)

    # ---- parse manifest ---------------------------------------------------
    rows = []
    for raw in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            print(f"  WARNING: Skipping malformed manifest row: {line!r}")
            continue
        species  = parts[0].strip()
        fasta_p  = parts[1].strip()
        gff3_p   = parts[2].strip()
        upstream = int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() \
                   else (args.upstream or 2000)
        rows.append((species, fasta_p, gff3_p, upstream))

    if not rows:
        print("\n  ERROR: Manifest has no valid rows.")
        sys.exit(1)

    # ---- load motifs -------------------------------------------------------
    motifs = []
    mpath = Path(args.motifs_file)
    if not mpath.exists():
        print(f"\n  ERROR: Motifs file not found: {mpath}")
        sys.exit(1)
    for line in mpath.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            name, seq = line.split("\t", 1)
        elif ": " in line:
            name, seq = line.split(": ", 1)
        else:
            name, seq = line, line
        motifs.append((name.strip(), seq.strip().upper()))

    if not motifs:
        print("\n  ERROR: Motifs file is empty or has no valid entries.")
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Batch run: {len(rows)} species  x  {len(motifs)} motif(s)")
    print(f"Output directory: {out_dir}\n")

    all_frames = []

    for species, fasta_path, gff3_path, upstream in rows:
        fasta = Path(fasta_path)
        gff3  = Path(gff3_path)
        safe  = species.replace(" ", "_").replace(".", "").replace("/", "_")

        print(f"  [{species}]")
        if not fasta.exists():
            print(f"    WARNING: FASTA not found: {fasta} - skipping")
            continue
        if not gff3.exists():
            print(f"    WARNING: GFF3 not found: {gff3} - skipping")
            continue

        prom_fa  = out_dir / f"{safe}_promoters.fa"
        prom_tsv = out_dir / f"{safe}_promoters.tsv"

        print(f"    Extracting {upstream} bp promoters ...")
        try:
            extract_promoters(str(fasta), str(gff3), str(prom_fa), str(prom_tsv),
                              promoter_len=upstream)
        except Exception as exc:
            print(f"    WARNING: Extraction failed: {exc} - skipping")
            continue

        print(f"    Scanning {len(motifs)} motif(s) ...")
        try:
            df = scan_fasta_for_motifs(
                str(prom_fa), motifs,
                treat_as_iupac=True,
                allow_overlaps=True,
                search_revcomp=True,
            )
        except Exception as exc:
            print(f"    WARNING: Search failed: {exc} - skipping")
            continue

        if isinstance(df, pd.DataFrame) and not df.empty:
            df.insert(0, "species", species)
            sp_csv = out_dir / f"{safe}_hits.csv"
            df.to_csv(sp_csv, index=False)
            print(f"    {len(df)} hit(s) -> {sp_csv.name}")
            all_frames.append(df)
        else:
            print(f"    No hits found.")

    print()
    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_path = out_dir / "batch_hits.csv"
        combined.to_csv(combined_path, index=False)
        print(f"  Combined: {combined_path}  ({len(combined):,} total hits, "
              f"{combined['species'].nunique()} species)")
        print(f"\n  Next step: cis-gs feed {combined_path} expression.csv")
    else:
        print("  No hits found for any species.")


# ══════════════════════════════════════════════════════════════════════════════
# LOGO  -  build sequence logos from motif hit CSV
# ══════════════════════════════════════════════════════════════════════════════

def cmd_logo(args):
    import pandas as pd
    import logomaker
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from cis_gs.app import render_logo_to_png

    hits_csv = Path(args.hits_csv)
    if not hits_csv.exists():
        print(f"\n  ERROR: Hits CSV not found: {hits_csv}")
        # Tip: Run 'cis-gs search <promoters.fasta> -m PATTERN -o hits.csv' first
        # Tip: The hits CSV is produced automatically by 'cis-gs search'
        sys.exit(1)

    try:
        df = pd.read_csv(hits_csv)
    except Exception as e:
        print(f"\n  ERROR: Could not read CSV: {e}")
        # Tip: Make sure the file is a valid CSV (comma-separated), not TSV or Excel
        sys.exit(1)

    if "matched_seq" not in df.columns:
        print("\n  ERROR: CSV must have a 'matched_seq' column.")
        print(f"  Columns found: {list(df.columns)}")
        # Tip: This column is automatically included in the output of 'cis-gs search'
        # Tip: If you edited the CSV manually, make sure column headers are intact
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    motif_col = "motif_name" if "motif_name" in df.columns else None

    def _render_group(seqs, label):
        if args.length:
            seqs = [s for s in seqs if len(s) == args.length]
        if not seqs:
            print(f"  Skipping {label}: no sequences of length {args.length}")
            # Tip: Try without --length to include all sequence lengths
            return
        # Use the most common length (modal length) for the logo
        modal_len = max(set(len(s) for s in seqs),
                        key=lambda l: sum(1 for s in seqs if len(s) == l))
        seqs = [s for s in seqs if len(s) == modal_len]
        try:
            probs = logomaker.alignment_to_matrix(seqs, to_type="probability")
        except Exception as e:
            print(f"  WARNING: Could not build matrix for {label}: {e}")
            # Tip: logomaker requires all sequences to be the same length
            # Tip: Use --length to filter to an exact length first
            return
        png_bytes = render_logo_to_png(probs, scale=args.scale)
        fname = outdir / f"logo_{label.replace('/', '_').replace(' ', '_')}.png"
        fname.write_bytes(png_bytes)
        print(f"  {label}: {len(seqs)} seqs, {modal_len} bp → {fname.name}")

    print(f"Building sequence logos from {hits_csv.name}...")
    if motif_col:
        for motif_name, grp in df.groupby(motif_col):
            seqs = grp["matched_seq"].dropna().str.upper().tolist()
            _render_group(seqs, str(motif_name))
    else:
        seqs = df["matched_seq"].dropna().str.upper().tolist()
        _render_group(seqs, "all_motifs")

    print(f"  Logos saved to: {outdir}/")


# ══════════════════════════════════════════════════════════════════════════════
# FEED  -  match motif hit genes with expression data
# ══════════════════════════════════════════════════════════════════════════════

def cmd_feed(args):
    import pandas as pd

    hits_csv = Path(args.hits_csv)
    expr_csv = Path(args.expr_csv)
    output   = Path(args.output)

    if not hits_csv.exists():
        print(f"\n  ERROR: Hits CSV not found: {hits_csv}")
        # Tip: Run 'cis-gs search <promoters.fasta> -m PATTERN' to generate this file
        sys.exit(1)
    if not expr_csv.exists():
        print(f"\n  ERROR: Expression CSV not found: {expr_csv}")
        # Tip: Expression CSV format: rows = genes, columns = samples/time-points
        # Tip: First column should be gene IDs (no header for that column, or use index)
        # Tip: Example header:  (blank),0h,6h,12h,24h
        sys.exit(1)

    print("Matching motif hit genes with expression data...")
    try:
        hits_df = pd.read_csv(hits_csv)
        expr_df = pd.read_csv(expr_csv, index_col=0)
    except Exception as e:
        print(f"\n  ERROR reading files: {e}")
        # Tip: Make sure both files are valid CSV files (not TSV or Excel format)
        sys.exit(1)

    if "gene_id" not in hits_df.columns:
        print("\n  ERROR: Hits CSV must have a 'gene_id' column.")
        print(f"  Columns found: {list(hits_df.columns)}")
        # Tip: This column is automatically produced by 'cis-gs search'
        # Tip: The gene_id is taken from the FASTA sequence headers
        sys.exit(1)

    # Normalize IDs (strip prefixes like 'gene-', 'rna-') then match
    motif_genes_norm = {_normalize_gene_id(g): g for g in hits_df["gene_id"].unique()}
    expr_genes_norm  = {_normalize_gene_id(g): g for g in expr_df.index}

    matched_expr_ids = []
    for norm_id in motif_genes_norm:
        if norm_id in expr_genes_norm:
            matched_expr_ids.append(expr_genes_norm[norm_id])
        else:
            # Try without version suffix (e.g. AT1G00010.1 → AT1G00010)
            base = norm_id.rsplit(".", 1)[0]
            if base in expr_genes_norm:
                matched_expr_ids.append(expr_genes_norm[base])

    matched_expr_ids = list(dict.fromkeys(matched_expr_ids))  # deduplicate

    if not matched_expr_ids:
        print("\n  WARNING: No matching genes found between motif hits and expression data.")
        print(f"  Motif hit genes  : {len(motif_genes_norm)}")
        print(f"  Expression genes : {len(expr_genes_norm)}")
        print(f"  Example hit IDs  : {list(motif_genes_norm.keys())[:3]}")
        print(f"  Example expr IDs : {list(expr_genes_norm.keys())[:3]}")
        # Tip: Gene IDs must match between the FASTA headers and expression file row labels
        # Tip: Check for prefix differences (e.g. 'gene-AT1G00010' vs 'AT1G00010')
        # Tip: Check for version differences (e.g. 'AT1G00010.1' vs 'AT1G00010')
        # Tip: Cis-GS automatically strips 'gene-', 'rna-', version suffixes
        sys.exit(1)

    filtered = expr_df.loc[matched_expr_ids]
    output.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output)

    print(f"  Motif hit genes  : {len(motif_genes_norm)}")
    print(f"  Matched in expr  : {len(matched_expr_ids)}")
    print(f"  Saved            : {output}")
    print(f"\n  Next step: cis-gs coexpr {output}  OR  cis-gs kmeans {output}")


# ══════════════════════════════════════════════════════════════════════════════
# COEXPR  -  co-expression network analysis
# ══════════════════════════════════════════════════════════════════════════════

def cmd_coexpr(args):
    import pandas as pd
    from cis_gs.app import (calculate_correlation_matrix, detect_coexpression_modules,
                             render_correlation_heatmap, create_interactive_network_html,
                             render_network_plot)

    expr_csv = Path(args.expr_csv)
    if not expr_csv.exists():
        print(f"\n  ERROR: Expression CSV not found: {expr_csv}")
        # Tip: Use 'cis-gs feed hits.csv expression.csv' to generate a filtered CSV first
        # Tip: Or pass your raw expression CSV (genes x samples) directly
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Loading expression data: {expr_csv.name}")
    try:
        expr_df = pd.read_csv(expr_csv, index_col=0)
    except Exception as e:
        print(f"\n  ERROR reading CSV: {e}")
        sys.exit(1)

    if expr_df.empty:
        print("\n  ERROR: Expression CSV is empty.")
        sys.exit(1)
    if expr_df.shape[1] < 2:
        print("\n  ERROR: Expression CSV must have at least 2 sample columns.")
        # Tip: Columns = samples/time-points, rows = genes
        # Tip: Make sure the first column is gene IDs, not a data column
        sys.exit(1)

    print(f"  {len(expr_df)} genes × {len(expr_df.columns)} samples")

    print(f"Computing {args.method} correlation matrix...")
    try:
        corr = calculate_correlation_matrix(expr_df, method=args.method)
    except Exception as e:
        print(f"\n  ERROR computing correlations: {e}")
        # Tip: Make sure all expression values are numeric (no text cells)
        # Tip: Genes with zero variance (same value in all samples) are excluded
        sys.exit(1)

    # Save correlation matrix
    corr_csv = outdir / "correlation_matrix.csv"
    corr.to_csv(corr_csv)
    print(f"  Correlation matrix saved : {corr_csv}")

    # Heatmap
    heatmap_path = outdir / "correlation_heatmap.png"
    try:
        render_correlation_heatmap(corr, output_path=str(heatmap_path))
        print(f"  Heatmap PNG saved        : {heatmap_path}")
    except Exception as e:
        print(f"  WARNING: Could not render heatmap: {e}")
        # Tip: Heatmap requires matplotlib and seaborn - run 'pip install seaborn'

    # Module detection
    print(f"Detecting co-expression modules (threshold={args.threshold})...")
    try:
        communities, G = detect_coexpression_modules(corr, threshold=args.threshold)
    except Exception as e:
        print(f"\n  ERROR during module detection: {e}")
        # Tip: Try a lower --threshold (e.g. 0.5) if no modules are detected
        # Tip: The default threshold is 0.7 (Pearson r ≥ 0.7 forms an edge)
        sys.exit(1)

    n_modules = len(set(communities.values())) if communities else 0
    print(f"  {n_modules} modules detected, {len(communities)} genes assigned")

    # Module membership CSV
    mod_df = pd.DataFrame.from_dict(communities, orient="index", columns=["module"])
    mod_df.index.name = "gene"
    mod_csv = outdir / "module_membership.csv"
    mod_df.to_csv(mod_csv)
    print(f"  Module membership CSV    : {mod_csv}")

    # Interactive HTML network
    html_path = outdir / "coexpression_network.html"
    try:
        create_interactive_network_html(G, communities, str(html_path),
                                        hide_isolated=args.hide_isolated)
        print(f"  Interactive network HTML : {html_path}")
    except Exception as e:
        print(f"  WARNING: Could not create network HTML: {e}")
        # Tip: Open coexpression_network.html in any web browser to explore the network

    # Static PNG
    png_path = outdir / "coexpression_network.png"
    try:
        render_network_plot(G, communities, output_path=str(png_path),
                            hide_isolated=args.hide_isolated)
        print(f"  Network PNG              : {png_path}")
    except Exception as e:
        print(f"  WARNING: Could not render network PNG: {e}")

    print(f"\n  All outputs saved to: {outdir}/")


# ══════════════════════════════════════════════════════════════════════════════
# KMEANS  -  K-means temporal clustering
# ══════════════════════════════════════════════════════════════════════════════

def cmd_kmeans(args):
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    from cis_gs.app import kmeans_temporal_clustering, plot_kmeans_spaghetti

    expr_csv = Path(args.expr_csv)
    if not expr_csv.exists():
        print(f"\n  ERROR: Expression CSV not found: {expr_csv}")
        # Tip: Use 'cis-gs feed hits.csv expression.csv' to produce the input file
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Loading expression data: {expr_csv.name}")
    try:
        expr_df = pd.read_csv(expr_csv, index_col=0)
    except Exception as e:
        print(f"\n  ERROR reading CSV: {e}")
        sys.exit(1)

    print(f"  {len(expr_df)} genes × {len(expr_df.columns)} samples")

    if args.k >= len(expr_df):
        print(f"\n  ERROR: K ({args.k}) must be less than the number of genes ({len(expr_df)}).")
        # Tip: A good K is typically sqrt(number_of_genes) or between 3 and 10
        # Tip: Use -k 5 for a starting point, then adjust based on the plot
        sys.exit(1)

    print(f"Running K-means clustering (K={args.k})...")
    try:
        result = kmeans_temporal_clustering(expr_df, n_clusters=args.k,
                                            n_init=50, random_state=42)
    except Exception as e:
        print(f"\n  ERROR during clustering: {e}")
        # Tip: All expression values must be numeric
        # Tip: Remove genes with all-zero expression before running K-means
        sys.exit(1)

    # Cluster assignments
    labels      = result["cluster_labels"]
    assignments = __import__("pandas").DataFrame(
        {"gene": labels.index, "cluster": labels.values})
    csv_path = outdir / "kmeans_clusters.csv"
    assignments.to_csv(csv_path, index=False)
    print(f"  Cluster assignments saved : {csv_path}")

    # Centroids
    centroids = result["centroids"]
    cent_path = outdir / "kmeans_centroids.csv"
    centroids.to_csv(cent_path)
    print(f"  Centroids saved           : {cent_path}")

    # Per-cluster summary
    for cid in sorted(assignments["cluster"].unique()):
        n = (assignments["cluster"] == cid).sum()
        print(f"    Cluster {cid}: {n} gene(s)")

    # Spaghetti plot
    png_path = outdir / "kmeans_plot.png"
    try:
        plot_kmeans_spaghetti(expr_df, result, output_path=str(png_path))
        print(f"  Spaghetti plot saved      : {png_path}")
    except Exception as e:
        print(f"  WARNING: Could not render plot: {e}")
        # Tip: Install matplotlib if missing: pip install matplotlib

    print(f"\n  All outputs saved to: {outdir}/")


# ══════════════════════════════════════════════════════════════════════════════
# TFDB  -  transcription factor database commands
# ══════════════════════════════════════════════════════════════════════════════

def cmd_tfdb_species(args):
    """List all available PlantTFDB species (157+ plant organisms)."""
    from cis_gs.planttfdb_importer import fetch_species_list, _FALLBACK_CATALOGUE

    search = args.search.lower() if args.search else ""

    print("Fetching live species list from PlantTFDB...")
    live = fetch_species_list()
    catalogue = live if len(live) >= 50 else _FALLBACK_CATALOGUE
    source = "PlantTFDB (live)" if len(live) >= 50 else "built-in fallback list"

    entries = sorted(catalogue.items(), key=lambda x: x[1])
    if search:
        entries = [(c, n) for c, n in entries
                   if search in n.lower() or search in c.lower()]

    print(f"\n  Source: {source}  ({len(catalogue)} total organisms)")
    if search:
        print(f"  Filter: '{args.search}' - {len(entries)} match(es)\n")
    else:
        print(f"  Showing all {len(entries)} species\n")

    print(f"  {'Code':<6}  Species")
    print(f"  {'────':<6}  ───────────────────────────────────────")
    for code, name in entries:
        print(f"  {code:<6}  {name}")

    if not entries:
        print("  No species matched your search.")
        # Tip: Search is case-insensitive. Try part of the genus name (e.g. 'oryza', 'arabid')
        # Tip: Run 'cis-gs tfdb species' with no --search to see all organisms

    print(f"\n  To download motifs for a species:")
    print(f"    cis-gs tfdb download <code>  (e.g. cis-gs tfdb download Ath)")


def cmd_tfdb_download(args):
    """Download PlantTFDB MEME + info files for a species code."""
    import gzip, shutil

    code   = args.code.strip()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    meme_gz_fname = f"{code}_TF_binding_motifs.meme.gz"
    meme_fname    = f"{code}_TF_binding_motifs.meme"
    info_fname    = f"{code}_TF_binding_motifs_information.txt"
    meme_gz_dest  = outdir / meme_gz_fname
    meme_dest     = outdir / meme_fname
    info_dest     = outdir / info_fname

    # Use cached files if they already exist
    if meme_dest.exists() and meme_dest.stat().st_size > 0 and not args.force:
        print(f"  MEME file already exists (use --force to re-download): {meme_dest}")
    else:
        domains = [
            "https://planttfdb.gao-lab.org/download/motif",
            "http://planttfdb.gao-lab.org/download/motif",
            "https://planttfdb.cbi.pku.edu.cn/download/motif",
            "http://planttfdb.cbi.pku.edu.cn/download/motif",
        ]
        # Try .meme.gz first, then plain .meme
        gz_urls   = [f"{d}/{meme_gz_fname}"  for d in domains]
        meme_urls = [f"{d}/{meme_fname}"     for d in domains]

        print(f"Downloading MEME file for species '{code}'...")
        ok, err = _try_urls(gz_urls, meme_gz_dest, label="MEME.gz")
        if ok:
            print(f"  Decompressing...")
            try:
                with gzip.open(meme_gz_dest, "rb") as fi, open(meme_dest, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
                meme_gz_dest.unlink()
            except Exception as e:
                print(f"\n  ERROR: Downloaded but failed to decompress: {e}")
                # Tip: The downloaded file may be corrupted - try again with --force
                sys.exit(1)
        else:
            ok, err2 = _try_urls(meme_urls, meme_dest, label="MEME")
            if not ok:
                print(f"\n  ERROR: Could not download MEME file for '{code}'")
                print(f"  URLs tried:\n{err}\n{err2}")
                # Tip: Verify the species code with: cis-gs tfdb species --search <name>
                # Tip: The PlantTFDB server may be temporarily down - try again in a few minutes
                # Tip: Download manually from planttfdb.gao-lab.org and use 'cis-gs tfdb filter'
                sys.exit(1)

        print(f"  Saved MEME : {meme_dest}")

    # Download info/annotation file
    if info_dest.exists() and info_dest.stat().st_size > 0 and not args.force:
        print(f"  Info file already exists (use --force to re-download): {info_dest}")
    else:
        info_urls = [f"{d}/{info_fname}" for d in [
            "https://planttfdb.gao-lab.org/download/motif",
            "http://planttfdb.gao-lab.org/download/motif",
            "https://planttfdb.cbi.pku.edu.cn/download/motif",
            "http://planttfdb.cbi.pku.edu.cn/download/motif",
        ]]
        print(f"Downloading info/annotation file for '{code}'...")
        ok, err = _try_urls(info_urls, info_dest, label="Info")
        if ok:
            print(f"  Saved info : {info_dest}")
        else:
            print(f"  WARNING: Info file unavailable (TF Family/Method will show Unknown)")
            # Tip: The info file adds TF Family names to the browser
            # Tip: You can still use the MEME file without it

    print(f"\n  To browse and export motifs:")
    print(f"    cis-gs tfdb filter {meme_dest} --info {info_dest} -o motifs.txt")
    print(f"\n  To search your promoters with these motifs:")
    print(f"    cis-gs search promoters.fasta --motifs-file motifs.txt")


def cmd_tfdb_sources(args):
    """List available JASPAR / HOCOMOCO datasets for download."""
    from cis_gs.animaltfdb_importer import DATASETS

    print("\n  Available JASPAR / HOCOMOCO datasets:\n")
    print(f"  {'ID':<30}  {'Label'}")
    print(f"  {'──':<30}  {'─────'}")
    for ds in DATASETS:
        print(f"  {ds['id']:<30}  {ds['icon']} {ds['label']}")
    print(f"\n  To download a dataset:")
    print(f"    cis-gs tfdb download-db jaspar2024_vertebrates")
    print(f"    cis-gs tfdb download-db hocomoco_human")
    print(f"\n  To filter/export after downloading:")
    print(f"    cis-gs tfdb filter <downloaded.meme> -o motifs.txt")


def cmd_tfdb_download_db(args):
    """Download a JASPAR or HOCOMOCO dataset by source ID."""
    import zipfile, io
    from cis_gs.animaltfdb_importer import DATASETS

    sid = args.source_id.strip()
    ds  = next((d for d in DATASETS if d["id"] == sid), None)
    if ds is None:
        print(f"\n  ERROR: Unknown source ID: '{sid}'")
        print("  Run 'cis-gs tfdb sources' to see available IDs.")
        # Tip: Source IDs are case-sensitive - use exactly as shown in 'cis-gs tfdb sources'
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    dest   = outdir / ds["local_name"]

    if dest.exists() and dest.stat().st_size > 0 and not args.force:
        print(f"  Already downloaded (use --force to re-download): {dest}")
    else:
        print(f"Downloading {ds['icon']} {ds['label']}...")
        print(f"  This may take a minute for large files.\n")

        # If the URL is a .zip, download to a temp path then extract
        first_url = ds["urls"][0]
        if first_url.endswith(".zip"):
            tmp = outdir / (ds["local_name"] + ".zip")
            ok, err = _try_urls(ds["urls"], tmp, label=ds["id"])
            if not ok:
                print(f"\n  ERROR: Download failed.\n{err}")
                # Tip: Check your internet connection
                # Tip: Try 'cis-gs tfdb download-db --force' to retry
                sys.exit(1)
            print(f"  Extracting ZIP...")
            try:
                with zipfile.ZipFile(tmp, "r") as zf:
                    # Extract the first .meme file found inside the zip
                    meme_members = [m for m in zf.namelist() if m.endswith(".meme")]
                    if not meme_members:
                        raise ValueError("No .meme file found inside ZIP")
                    with zf.open(meme_members[0]) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                tmp.unlink()
            except Exception as e:
                print(f"\n  ERROR extracting ZIP: {e}")
                # Tip: The downloaded file may be corrupted - delete and retry with --force
                sys.exit(1)
        else:
            ok, err = _try_urls(ds["urls"], dest, label=ds["id"])
            if not ok:
                print(f"\n  ERROR: Download failed.\n{err}")
                sys.exit(1)

        print(f"  Saved MEME : {dest}")

    # Download annotation file if available (HOCOMOCO)
    annot_dest = None
    if ds.get("annot_urls"):
        annot_name = ds["local_name"].replace(".meme", "_annotation.tsv")
        annot_dest = outdir / annot_name
        if annot_dest.exists() and not args.force:
            print(f"  Annotation already exists: {annot_dest}")
        else:
            print(f"  Downloading annotation file...")
            ok, err = _try_urls(ds["annot_urls"], annot_dest, label="annotation")
            if ok:
                print(f"  Saved annotation : {annot_dest}")
            else:
                print(f"  WARNING: Annotation file unavailable - TF Family will show Unknown")
                annot_dest = None

    print(f"\n  To browse and export motifs from this dataset:")
    cmd = f"    cis-gs tfdb filter {dest}"
    if annot_dest:
        cmd += f" --info {annot_dest}"
    print(cmd + " -o motifs.txt")


def cmd_tfdb_filter(args):
    """
    Filter a MEME file (PlantTFDB, JASPAR, or HOCOMOCO) and export
    selected motif IUPAC sequences to a text file for use with 'cis-gs search'.
    """
    from cis_gs.planttfdb_importer import (
        parse_meme_file, parse_info_file, enrich_motifs,
        _fill_defaults, pfm_to_iupac
    )

    meme_path = Path(args.meme_file)
    if not meme_path.exists():
        print(f"\n  ERROR: MEME file not found: {meme_path}")
        # Tip: Download a MEME file first:
        #   cis-gs tfdb download Ath              (PlantTFDB - Arabidopsis)
        #   cis-gs tfdb download-db hocomoco_human (HOCOMOCO - Human)
        #   cis-gs tfdb download-db jaspar2024_vertebrates (JASPAR)
        sys.exit(1)

    print(f"Parsing MEME file: {meme_path.name}")
    try:
        motifs = parse_meme_file(str(meme_path))
    except Exception as e:
        print(f"\n  ERROR parsing MEME file: {e}")
        # Tip: Make sure the file is a valid MEME-format file (not a ZIP or gz)
        # Tip: Download fresh with: cis-gs tfdb download <code> --force
        sys.exit(1)

    if not motifs:
        print("\n  ERROR: No motifs found in the MEME file.")
        # Tip: The file may be corrupted or in an unsupported format
        sys.exit(1)

    # Enrich with info/annotation file if provided
    if args.info:
        info_path = Path(args.info)
        if not info_path.exists():
            print(f"  WARNING: Info file not found: {info_path} - skipping annotation")
            # Tip: Download the info file alongside the MEME file:
            #   cis-gs tfdb download Ath  (downloads both MEME + info automatically)
        else:
            try:
                info = parse_info_file(str(info_path))
                motifs = enrich_motifs(motifs, info)
                print(f"  Loaded annotation from: {info_path.name}")
            except Exception as e:
                print(f"  WARNING: Could not parse info file: {e}")
    _fill_defaults(motifs)

    # Re-compute IUPAC at requested threshold
    threshold = args.threshold
    for m in motifs:
        if m.get("pfm"):
            m["iupac"] = pfm_to_iupac(m["pfm"], threshold=threshold)

    total = len(motifs)
    print(f"  {total} motifs loaded  (IUPAC threshold: {threshold})")

    # Apply filters
    filtered = motifs

    if args.family:
        fam_lower = args.family.lower()
        filtered = [m for m in filtered if fam_lower in m.get("family", "").lower()]
        print(f"  Family filter '{args.family}': {len(filtered)} remaining")

    if args.method:
        met_lower = args.method.lower()
        filtered = [m for m in filtered if met_lower in m.get("method", "").lower()]
        print(f"  Method filter '{args.method}': {len(filtered)} remaining")

    if args.species:
        sp_lower = args.species.lower()
        filtered = [m for m in filtered if sp_lower in m.get("species", "").lower()]
        print(f"  Species filter '{args.species}': {len(filtered)} remaining")

    if args.search:
        kw = args.search.lower()
        filtered = [m for m in filtered
                    if kw in m.get("gene_id", "").lower()
                    or kw in m.get("family", "").lower()
                    or kw in m.get("iupac", "").lower()
                    or kw in m.get("matrix_id", "").lower()]
        print(f"  Keyword filter '{args.search}': {len(filtered)} remaining")

    if args.min_width:
        filtered = [m for m in filtered if m.get("width", 0) >= args.min_width]
        print(f"  Min width {args.min_width}: {len(filtered)} remaining")

    if args.max_width:
        filtered = [m for m in filtered if m.get("width", 0) <= args.max_width]
        print(f"  Max width {args.max_width}: {len(filtered)} remaining")

    if not filtered:
        print("\n  WARNING: No motifs passed the filters.")
        # Tip: Relax your filters - try without --family or --species first
        # Tip: Run 'cis-gs tfdb filter <meme_file> --list-families' to see available families
        # Tip: Family names are case-insensitive partial matches (e.g. --family myb matches MYB)
        if args.list_families or args.list_species:
            pass  # handled below
        else:
            sys.exit(1)

    # --list-families / --list-species: show unique values then exit
    if args.list_families:
        families = sorted({m.get("family", "Unknown") for m in motifs})
        print(f"\n  TF Families in this MEME file ({len(families)} total):")
        for f in families:
            count = sum(1 for m in motifs if m.get("family") == f)
            print(f"    {f:<20}  {count} motifs")
        sys.exit(0)

    if args.list_species:
        species = sorted({m.get("species", "Unknown") for m in motifs})
        print(f"\n  Species in this MEME file ({len(species)} total):")
        for s in species:
            count = sum(1 for m in motifs if m.get("species") == s)
            print(f"    {s:<35}  {count} motifs")
        sys.exit(0)

    # Build output lines
    lines = []
    for m in filtered:
        iupac = m.get("iupac", "")
        if not iupac or len(iupac) < 3:
            continue  # skip degenerate/empty motifs
        gene_id = m.get("gene_id", "unknown")
        family  = m.get("family", "")
        if args.no_prefix or not family or family == "Unknown":
            name = gene_id
        else:
            name = f"{family}|{gene_id}"
        lines.append(f"{name}\t{iupac}")

    if not lines:
        print("\n  WARNING: No motifs had valid IUPAC sequences after filtering.")
        # Tip: Lower the IUPAC threshold with --threshold 0.20 for more permissive consensus
        sys.exit(1)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n  Exported {len(lines)} motifs → {output}")
    print(f"\n  To scan your promoters with these motifs:")
    print(f"    cis-gs search promoters.fasta --motifs-file {output}")


# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ══════════════════════════════════════════════════════════════════════════════

def _build_parser():
    parser = argparse.ArgumentParser(
        prog="cis-gs",
        description=(
            "Cis-GS: Cis-regulatory Element Genome Scanner\n"
            "Analyzes cis-regulatory elements (TFBS) across genomes.\n"
            "Run without arguments to launch the graphical interface (GUI)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "===  INTERACTIVE WIZARD  =============================================\n"
            "\n"
            "  Don't remember the flags?  Use the step-by-step wizard:\n"
            "    cis-gs wizard               # top-level menu, pick a workflow\n"
            "    cis-gs wizard kegg          # KEGG enrichment, live organism picker\n"
            "    cis-gs wizard id-convert    # ID conversion, live NCBI Taxonomy\n"
            "    cis-gs wizard feed          # Expression Feeding\n"
            "    cis-gs wizard coexpr        # Co-expression network\n"
            "    cis-gs wizard kmeans        # K-means clustering\n"
            "    cis-gs wizard fetch         # NCBI genome fetch\n"
            "    cis-gs wizard extract       # Promoter extraction\n"
            "    cis-gs wizard search        # Motif search\n"
            "\n"
            "  Every regular subcommand also accepts -i / --interactive to\n"
            "  promote it into a wizard:\n"
            "    cis-gs enrich-kegg -i\n"
            "    cis-gs id-convert -i\n"
            "    cis-gs coexpr -i\n"
            "\n"
            "===  TYPICAL WORKFLOW  ===============================================\n"
            "\n"
            "  Step 0 -- Get TF motifs (choose one database):\n"
            "    cis-gs tfdb species --search arabidopsis   # find species code\n"
            "    cis-gs tfdb download Ath -o ./motif_db     # download PlantTFDB\n"
            "    cis-gs tfdb sources                        # list JASPAR/HOCOMOCO\n"
            "    cis-gs tfdb download-db jaspar2024_vertebrates -o ./motif_db\n"
            "    cis-gs tfdb filter ./motif_db/Ath_TF_binding_motifs.meme \\\n"
            "           --family MYB -o myb_motifs.txt      # export chosen motifs\n"
            "\n"
            "  Step 1 -- Download genome from NCBI:\n"
            "    cis-gs fetch GCF_000001735.4 -o ./genome\n"
            "\n"
            "  Step 2 -- Extract upstream promoter sequences (PROMOTERS):\n"
            "    cis-gs extract genome.fasta genome.gff3 -l 1500 -o promoters.fasta\n"
            "\n"
            "  Step 3 -- Scan promoters for TFBS motif hits (MOTIF SEARCH):\n"
            "    cis-gs search promoters.fasta --motifs-file myb_motifs.txt\n"
            "    cis-gs search promoters.fasta -m ACGTG -m RGATCY   # inline motifs\n"
            "\n"
            "  Step 3b -- Build sequence logos from the hits (MOTIF LOGOS):\n"
            "    cis-gs logo motif_hits.csv -o ./logos\n"
            "\n"
            "  Step 4 -- Match motif hits with expression data (EXPRESSION FEEDING):\n"
            "    cis-gs feed motif_hits.csv expression.csv -o filtered_expr.csv\n"
            "    cis-gs feed -i                              # interactive wizard\n"
            "\n"
            "  Step 5 -- Co-expression network analysis (COEXPRESSION):\n"
            "    cis-gs coexpr filtered_expr.csv -o ./coexpr_results\n"
            "\n"
            "  Step 6 -- K-means temporal clustering (K-MEANS):\n"
            "    cis-gs kmeans filtered_expr.csv -k 6 -o ./kmeans_results\n"
            "\n"
            "  Step 7 -- KEGG pathway enrichment (KEGG ENRICHMENT):\n"
            "    cis-gs id-convert -g motif_hits.csv --species 3818 -o id_map.tsv\n"
            "    cis-gs enrich-kegg -g id_map.tsv --organism ahf -o kegg.csv\n"
            "    cis-gs wizard kegg                          # interactive\n"
            "\n"
            "===  COMMON OPTIONS  =================================================\n"
            "  Use --help on any subcommand for full details:\n"
            "    cis-gs fetch --help\n"
            "    cis-gs tfdb --help\n"
            "    cis-gs enrich-kegg --help\n"
            "    cis-gs id-convert --help\n"
            "    cis-gs wizard --help\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # ── fetch ─────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "fetch",
        help="Download genome FASTA + GFF3 annotation from NCBI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Download a genome assembly (FASTA) and annotation (GFF3) from NCBI FTP.\n"
            "Accession numbers can be found at: https://www.ncbi.nlm.nih.gov/assembly\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs fetch GCF_000001735.4                 # Arabidopsis thaliana\n"
            "  cis-gs fetch GCF_000001405.40 -o ./genome    # Human GRCh38\n"
            "  cis-gs fetch GCF_001433935.1 --no-fasta      # GFF3 only\n"
            "\n"
            "Output files:\n"
            "  <assembly_id>_genomic.fasta   - genome sequences\n"
            "  <assembly_id>_genomic.gff3    - gene annotations\n"
            "\n"
            "Common errors:\n"
            "  'Assembly not found' - double-check the accession at ncbi.nlm.nih.gov/assembly\n"
            "  Timeout - NCBI FTP can be slow; try again or download manually\n"
        ),
    )
    p.add_argument("assembly", help="NCBI assembly accession (e.g. GCF_000001735.4)")
    p.add_argument("-o", "--outdir", default=".", metavar="DIR",
                   help="Output directory (default: current directory)")
    p.add_argument("--no-fasta", action="store_true", help="Skip genome FASTA download")
    p.add_argument("--no-gff",   action="store_true", help="Skip GFF3 annotation download")
    p.set_defaults(func=cmd_fetch)

    # ── extract ───────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "extract",
        help="Extract upstream promoter sequences from genome + GFF3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Extract N bp of upstream sequence for every gene in a GFF3 annotation.\n"
            "Produces a multi-FASTA file ready for motif scanning.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs extract genome.fasta annotation.gff3\n"
            "  cis-gs extract genome.fasta annotation.gff3 -l 2000 -o promoters_2kb.fasta\n"
            "\n"
            "Output files:\n"
            "  promoters.fasta   - promoter sequences in FASTA format\n"
            "  promoters.tsv     - table of gene IDs, coordinates, strand\n"
            "\n"
            "Common errors:\n"
            "  'Chromosome not found' - FASTA and GFF3 use different chromosome names\n"
            "  Solution: Check that chr names match (e.g. 'Chr1' in GFF vs '1' in FASTA)\n"
        ),
    )
    p.add_argument("fasta", help="Genome FASTA file (from 'cis-gs fetch')")
    p.add_argument("gff3",  help="GFF3 annotation file (from 'cis-gs fetch')")
    p.add_argument("-o", "--output", default="promoters.fasta", metavar="FILE",
                   help="Output FASTA file (default: promoters.fasta)")
    p.add_argument("-l", "--length", type=int, default=1000, metavar="BP",
                   help="Promoter length in base pairs upstream of TSS (default: 1000)")
    p.set_defaults(func=cmd_extract)

    # ── search ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "search",
        help="Scan promoter FASTA for transcription factor binding site (TFBS) motifs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Search promoter sequences for TFBS motifs using IUPAC patterns.\n"
            "Motifs can be typed directly (-m) or loaded from a file (--motifs-file).\n"
            "Both strands are searched by default.\n"
        ),
        epilog=(
            "IUPAC codes:  R=A/G  Y=C/T  S=G/C  W=A/T  K=G/T  M=A/C\n"
            "              B=C/G/T  D=A/G/T  H=A/C/T  V=A/C/G  N=any\n"
            "\n"
            "Examples:\n"
            "  cis-gs search promoters.fasta -m ACGTG\n"
            "  cis-gs search promoters.fasta -m ACGTG -m RGATCY -m WBOXNTERF\n"
            "  cis-gs search promoters.fasta --motifs-file myb_motifs.txt\n"
            "  cis-gs search promoters.fasta --motifs-file motifs.txt --no-revcomp\n"
            "\n"
            "Motifs file format (NAME<TAB>IUPAC - one per line):\n"
            "  ERF|AT1G00010  GCAGCCGCC\n"
            "  MYB|AT1G00020  AACCGTTA\n"
            "  # Lines starting with # are comments\n"
            "\n"
            "Export motifs from a database:\n"
            "  cis-gs tfdb download Ath && cis-gs tfdb filter Ath_TF_binding_motifs.meme \\\n"
            "         --family MYB -o myb_motifs.txt\n"
            "\n"
            "Output columns in hits CSV:\n"
            "  gene_id, motif_name, pattern, strand, position, matched_seq\n"
        ),
    )
    p.add_argument("fasta", help="Promoter FASTA file (from 'cis-gs extract')")
    p.add_argument("-m", "--motif", action="append", metavar="PATTERN",
                   help="IUPAC motif pattern - repeatable (e.g. -m ACGTG -m RGATCY)")
    p.add_argument("--motifs-file", metavar="FILE",
                   help="File with motifs, one per line: NAME<TAB>IUPAC_PATTERN")
    p.add_argument("-o", "--output", default="motif_hits.csv", metavar="FILE",
                   help="Output hits CSV (default: motif_hits.csv)")
    p.add_argument("--no-iupac", action="store_true",
                   help="Disable IUPAC expansion - treat patterns as literal strings")
    p.add_argument("--no-revcomp", action="store_true",
                   help="Only search the forward strand (default: both strands)")
    p.set_defaults(func=cmd_search)

    # ── logo ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "logo",
        help="Build sequence logos (PNG) from motif hit sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Generate sequence logo images from the 'matched_seq' column of a\n"
            "motif hits CSV (produced by 'cis-gs search').\n"
            "One PNG is generated per motif name.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs logo motif_hits.csv\n"
            "  cis-gs logo motif_hits.csv -o ./logo_output --scale probability\n"
            "  cis-gs logo motif_hits.csv --length 9   # only 9-mer sequences\n"
            "\n"
            "Output:\n"
            "  logos/logo_<motif_name>.png   - one file per motif\n"
        ),
    )
    p.add_argument("hits_csv", help="Motif hits CSV from 'cis-gs search'")
    p.add_argument("-o", "--outdir", default="logos", metavar="DIR",
                   help="Output directory for PNG files (default: logos/)")
    p.add_argument("--scale", choices=["bits", "probability"], default="bits",
                   help="Y-axis scale: 'bits' (information content, default) or 'probability'")
    p.add_argument("--length", type=int, default=None, metavar="N",
                   help="Only use sequences of this exact length (optional)")
    p.set_defaults(func=cmd_logo)

    # ── batch ─────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "batch",
        help="Multi-species promoter extraction + motif search from a manifest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Run promoter extraction and motif search for multiple species in one\n"
            "automated pass. Reads a tab-separated manifest file where each row\n"
            "describes one species; writes per-species hit CSVs and a combined\n"
            "'batch_hits.csv' with an extra 'species' column.\n"
        ),
        epilog=(
            "Manifest format (tab-separated, one species per line):\n"
            "  species_name<TAB>/path/to/genome.fa<TAB>/path/to/annot.gff3[<TAB>upstream_bp]\n"
            "  Lines starting with '#' are ignored.\n"
            "\n"
            "Example manifest (species.tsv):\n"
            "  O. sativa\t/data/rice.fa\t/data/rice.gff3\t2000\n"
            "  A. hypogaea\t/data/peanut.fa\t/data/peanut.gff3\t2000\n"
            "  M. truncatula\t/data/medicago.fa\t/data/medicago.gff3\t2000\n"
            "\n"
            "Examples:\n"
            "  cis-gs batch species.tsv --motifs-file motifs.txt\n"
            "  cis-gs batch species.tsv --motifs-file motifs.txt -o results/ --upstream 1500\n"
            "\n"
            "Output files in the output directory:\n"
            "  <species>_promoters.fa    - extracted promoters per species\n"
            "  <species>_hits.csv        - motif hits per species\n"
            "  batch_hits.csv            - combined hits (all species, 'species' column added)\n"
        ),
    )
    p.add_argument("manifest", help="TSV manifest file (species, fasta, gff3[, upstream])")
    p.add_argument("--motifs-file", required=True, metavar="FILE",
                   help="Motifs file - one NAME<TAB>IUPAC_PATTERN per line")
    p.add_argument("-o", "--out", default="batch_out", metavar="DIR",
                   help="Output directory (default: batch_out/)")
    p.add_argument("--upstream", type=int, default=2000, metavar="BP",
                   help="Default upstream length in bp used when not specified per-row (default: 2000)")
    p.set_defaults(func=cmd_batch)

    # ── feed ──────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "feed",
        help="Filter an expression matrix to genes that have TFBS hits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Match the gene IDs in a motif hits CSV against a gene expression matrix,\n"
            "and output only the rows (genes) that have at least one motif hit.\n"
            "Gene ID prefixes (gene-, rna-) and version suffixes (.1, .2) are handled.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs feed motif_hits.csv expression.csv\n"
            "  cis-gs feed motif_hits.csv expression.csv -o filtered_expr.csv\n"
            "\n"
            "Expression CSV format:\n"
            "  First column  = gene IDs (row index)\n"
            "  Other columns = sample names / time points\n"
            "  Example:\n"
            "    gene_id,0h,6h,12h,24h\n"
            "    AT1G00010,5.2,8.1,6.3,4.9\n"
            "    AT1G00020,1.1,1.3,1.2,1.0\n"
        ),
    )
    p.add_argument("hits_csv", help="Motif hits CSV from 'cis-gs search'")
    p.add_argument("expr_csv", help="Expression matrix CSV (genes × samples)")
    p.add_argument("-o", "--output", default="filtered_expression.csv", metavar="FILE",
                   help="Output filtered expression CSV (default: filtered_expression.csv)")
    p.set_defaults(func=cmd_feed)

    # ── coexpr ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "coexpr",
        help="Build a co-expression network with Louvain module detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Compute pairwise gene expression correlations, apply a threshold to\n"
            "build a network graph, then detect co-expression modules using the\n"
            "Louvain community detection algorithm.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs coexpr filtered_expr.csv\n"
            "  cis-gs coexpr filtered_expr.csv -o ./network --method spearman\n"
            "  cis-gs coexpr filtered_expr.csv --threshold 0.8 --hide-isolated\n"
            "\n"
            "Output files:\n"
            "  correlation_matrix.csv       - pairwise correlation values\n"
            "  correlation_heatmap.png      - heatmap image\n"
            "  module_membership.csv        - gene → module assignment\n"
            "  coexpression_network.html    - interactive network (open in browser)\n"
            "  coexpression_network.png     - static network image\n"
            "\n"
            "Threshold guide:\n"
            "  0.7 (default) - moderate co-expression\n"
            "  0.8           - strong co-expression, fewer edges\n"
            "  0.5           - permissive, more edges and larger modules\n"
        ),
    )
    p.add_argument("expr_csv", help="Expression CSV (genes × samples)")
    p.add_argument("-o", "--outdir", default="coexpr_output", metavar="DIR",
                   help="Output directory (default: coexpr_output/)")
    p.add_argument("--method", choices=["pearson", "spearman"], default="pearson",
                   help="Correlation method: 'pearson' (default) or 'spearman'")
    p.add_argument("--threshold", type=float, default=0.7, metavar="R",
                   help="Min |correlation| to draw an edge (default: 0.7)")
    p.add_argument("--hide-isolated", action="store_true",
                   help="Hide unconnected genes (no edges) from the network plots")
    p.set_defaults(func=cmd_coexpr)

    # ── kmeans ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "kmeans",
        help="K-means temporal clustering of gene expression profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Cluster genes by their expression pattern across time points using\n"
            "K-means. Produces cluster assignments, centroids, and a spaghetti plot\n"
            "showing expression trajectories per cluster.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs kmeans filtered_expr.csv -k 5\n"
            "  cis-gs kmeans filtered_expr.csv -k 8 -o ./clusters\n"
            "\n"
            "Output files:\n"
            "  kmeans_clusters.csv    - gene → cluster assignment\n"
            "  kmeans_centroids.csv   - mean expression profile per cluster\n"
            "  kmeans_plot.png        - spaghetti plot of expression trajectories\n"
            "\n"
            "Choosing K:\n"
            "  A common starting point is K = sqrt(number_of_genes).\n"
            "  Run with different K values and compare the spaghetti plots.\n"
        ),
    )
    p.add_argument("expr_csv", help="Expression CSV (genes × samples)")
    p.add_argument("-k", "--k", type=int, default=5, metavar="K",
                   help="Number of clusters (default: 5)")
    p.add_argument("-o", "--outdir", default="kmeans_output", metavar="DIR",
                   help="Output directory (default: kmeans_output/)")
    p.set_defaults(func=cmd_kmeans)

    # ── tfdb (parent) ─────────────────────────────────────────────────────────
    tfdb_p = sub.add_parser(
        "tfdb",
        help="Transcription factor database commands (PlantTFDB, JASPAR, HOCOMOCO)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Browse and download TF binding motifs from:\n"
            "  • PlantTFDB  - 157+ plant species\n"
            "  • JASPAR 2024 - Vertebrates and Insects\n"
            "  • HOCOMOCO v11 - Human and Mouse (ChIP-Seq)\n"
        ),
        epilog=(
            "Subcommands:\n"
            "  species       List all PlantTFDB organisms with species codes\n"
            "  download      Download PlantTFDB MEME + info for a species code\n"
            "  sources       List available JASPAR / HOCOMOCO datasets\n"
            "  download-db   Download a JASPAR or HOCOMOCO dataset\n"
            "  filter        Filter a MEME file and export motifs to a text file\n"
            "\n"
            "Typical PlantTFDB workflow:\n"
            "  cis-gs tfdb species --search arabidopsis    # → code is 'Ath'\n"
            "  cis-gs tfdb download Ath -o ./db            # downloads MEME + info\n"
            "  cis-gs tfdb filter ./db/Ath_TF_binding_motifs.meme \\\n"
            "         --info ./db/Ath_TF_binding_motifs_information.txt \\\n"
            "         --family MYB -o myb_motifs.txt\n"
            "  cis-gs search promoters.fasta --motifs-file myb_motifs.txt\n"
            "\n"
            "Typical JASPAR workflow:\n"
            "  cis-gs tfdb sources\n"
            "  cis-gs tfdb download-db jaspar2024_vertebrates -o ./db\n"
            "  cis-gs tfdb filter ./db/JASPAR2024_CORE_vertebrates_non-redundant.meme \\\n"
            "         --species 'Homo sapiens' --family 'Zinc finger' -o zf_motifs.txt\n"
            "  cis-gs search promoters.fasta --motifs-file zf_motifs.txt\n"
        ),
    )
    tfdb_sub = tfdb_p.add_subparsers(dest="tfdb_command", metavar="<subcommand>")
    tfdb_p.set_defaults(func=lambda args: tfdb_p.print_help())

    # tfdb species
    p = tfdb_sub.add_parser(
        "species",
        help="List all PlantTFDB species with their 3-letter download codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Fetch and display all 157+ plant species available on PlantTFDB.",
        epilog=(
            "Examples:\n"
            "  cis-gs tfdb species\n"
            "  cis-gs tfdb species --search arabidopsis\n"
            "  cis-gs tfdb species --search oryza\n"
            "  cis-gs tfdb species --search 'Glycine max'\n"
        ),
    )
    p.add_argument("--search", metavar="TEXT",
                   help="Filter species by name or code (case-insensitive partial match)")
    p.set_defaults(func=cmd_tfdb_species)

    # tfdb download
    p = tfdb_sub.add_parser(
        "download",
        help="Download PlantTFDB MEME + annotation for a species code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Download the MEME motif file and info/annotation file for a PlantTFDB\n"
            "species. The species code is a 3-letter abbreviation (e.g. Ath, Osa, Zma).\n"
            "Run 'cis-gs tfdb species' to find the code for your organism.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs tfdb download Ath                   # Arabidopsis thaliana\n"
            "  cis-gs tfdb download Osa -o ./rice_motifs  # Oryza sativa\n"
            "  cis-gs tfdb download Zma -o ./db --force   # Zea mays (re-download)\n"
            "\n"
            "Output files:\n"
            "  <code>_TF_binding_motifs.meme             - motif file\n"
            "  <code>_TF_binding_motifs_information.txt  - annotation (family, method)\n"
        ),
    )
    p.add_argument("code", help="3-letter PlantTFDB species code (e.g. Ath, Osa, Gma)")
    p.add_argument("-o", "--outdir", default=".", metavar="DIR",
                   help="Output directory (default: current directory)")
    p.add_argument("--force", action="store_true",
                   help="Re-download even if files already exist")
    p.set_defaults(func=cmd_tfdb_download)

    # tfdb sources
    p = tfdb_sub.add_parser(
        "sources",
        help="List available JASPAR 2024 and HOCOMOCO v11 datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Show all JASPAR and HOCOMOCO datasets that can be downloaded.",
        epilog=(
            "Download a dataset using its ID:\n"
            "  cis-gs tfdb download-db jaspar2024_vertebrates\n"
            "  cis-gs tfdb download-db hocomoco_human\n"
        ),
    )
    p.set_defaults(func=cmd_tfdb_sources)

    # tfdb download-db
    p = tfdb_sub.add_parser(
        "download-db",
        help="Download a JASPAR 2024 or HOCOMOCO v11 dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Download a JASPAR or HOCOMOCO MEME file by its source ID.\n"
            "Run 'cis-gs tfdb sources' to see all available IDs.\n"
        ),
        epilog=(
            "Examples:\n"
            "  cis-gs tfdb download-db jaspar2024_vertebrates\n"
            "  cis-gs tfdb download-db jaspar2024_insects -o ./insect_db\n"
            "  cis-gs tfdb download-db hocomoco_human -o ./human_db\n"
            "  cis-gs tfdb download-db hocomoco_mouse -o ./mouse_db --force\n"
            "\n"
            "After downloading, filter and export motifs:\n"
            "  cis-gs tfdb filter <downloaded.meme> --species 'Homo sapiens' \\\n"
            "         --family GATA -o gata_motifs.txt\n"
        ),
    )
    p.add_argument("source_id",
                   help="Dataset ID from 'cis-gs tfdb sources' (e.g. jaspar2024_vertebrates)")
    p.add_argument("-o", "--outdir", default=".", metavar="DIR",
                   help="Output directory (default: current directory)")
    p.add_argument("--force", action="store_true",
                   help="Re-download even if the file already exists")
    p.set_defaults(func=cmd_tfdb_download_db)

    # tfdb filter
    p = tfdb_sub.add_parser(
        "filter",
        help="Filter a MEME file and export IUPAC motifs for use with 'cis-gs search'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Load a MEME file (from PlantTFDB, JASPAR, or HOCOMOCO), apply optional\n"
            "filters (family, species, method, keyword, width), and export the\n"
            "selected motifs as a NAME<TAB>IUPAC text file for use with 'cis-gs search'.\n"
            "\n"
            "Use --list-families or --list-species to explore what is in a MEME file\n"
            "before deciding which filters to apply.\n"
        ),
        epilog=(
            "Examples:\n"
            "  # Explore a MEME file first\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme --list-families\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme --list-species\n"
            "\n"
            "  # Export all MYB motifs from Arabidopsis PlantTFDB\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme \\\n"
            "         --info Ath_TF_binding_motifs_information.txt \\\n"
            "         --family MYB -o myb_motifs.txt\n"
            "\n"
            "  # Export ERF + WRKY motifs (run twice, append second)\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme --family ERF -o erf_wrky.txt\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme --family WRKY >> erf_wrky.txt\n"
            "\n"
            "  # Export all JASPAR vertebrate motifs for Homo sapiens\n"
            "  cis-gs tfdb filter JASPAR2024_CORE_vertebrates_non-redundant.meme \\\n"
            "         --species 'Homo sapiens' -o human_motifs.txt\n"
            "\n"
            "  # Export short (6-10 bp) high-confidence motifs\n"
            "  cis-gs tfdb filter Ath_TF_binding_motifs.meme \\\n"
            "         --min-width 6 --max-width 10 --threshold 0.30 -o short_motifs.txt\n"
            "\n"
            "IUPAC threshold guide:\n"
            "  0.20 - very relaxed (more degenerate consensus, shorter effective motif)\n"
            "  0.25 - default (balanced)\n"
            "  0.30 - strict (more specific, fewer IUPAC codes)\n"
            "  0.40 - very strict (nearly exact consensus)\n"
            "\n"
            "Output format (NAME<TAB>IUPAC per line):\n"
            "  MYB|AT1G00010  AACCGTTA\n"
            "  ERF|AT2G00020  GCAGCCGCC\n"
        ),
    )
    p.add_argument("meme_file", help="MEME format file (from PlantTFDB, JASPAR, or HOCOMOCO)")
    p.add_argument("--info", metavar="FILE",
                   help="Optional annotation/info TSV file (adds TF Family, Method, Species)")
    p.add_argument("--family", metavar="NAME",
                   help="Filter by TF family (partial, case-insensitive, e.g. MYB, ERF, bHLH)")
    p.add_argument("--method", metavar="NAME",
                   help="Filter by experimental method (e.g. ChIP-Seq, DAP-Seq)")
    p.add_argument("--species", metavar="NAME",
                   help="Filter by species (partial match, e.g. 'Homo sapiens', 'Arabidopsis')")
    p.add_argument("--search", metavar="TEXT",
                   help="Keyword search across gene ID, family, matrix ID, and IUPAC sequence")
    p.add_argument("--min-width", type=int, default=None, metavar="N",
                   help="Minimum motif width in bp (e.g. --min-width 6)")
    p.add_argument("--max-width", type=int, default=None, metavar="N",
                   help="Maximum motif width in bp (e.g. --max-width 20)")
    p.add_argument("--threshold", type=float, default=0.25, metavar="F",
                   help="IUPAC consensus threshold 0.0-1.0 (default: 0.25)")
    p.add_argument("--no-prefix", action="store_true",
                   help="Don't prefix motif names with TF family (default: 'MYB|AT1G00010')")
    p.add_argument("-o", "--output", default="motifs.txt", metavar="FILE",
                   help="Output motifs text file (default: motifs.txt)")
    p.add_argument("--list-families", action="store_true",
                   help="List all TF families in this MEME file and exit")
    p.add_argument("--list-species", action="store_true",
                   help="List all species in this MEME file and exit")
    p.set_defaults(func=cmd_tfdb_filter)

    # ── enrichment sub-commands ──────────────────────────────────────────
    # KEGG enrichment, gene-ID conversion.  See cis_gs/cli_enrichment.py.
    try:
        from cis_gs.cli_enrichment import register as _register_enrichment_cmds
        _register_enrichment_cmds(sub)
    except ImportError as _exc:
        print(f"  (enrichment commands disabled: {_exc})", file=sys.stderr)

    # ── wizard / interactive menu ────────────────────────────────────────
    wiz = sub.add_parser(
        "wizard",
        help="Run an interactive step-by-step wizard for any workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Cis-GS Interactive Wizard\n"
            "==========================\n"
            "Launches a step-by-step assistant that mirrors every GUI tab.\n"
            "Each prompt explains what the value means and provides sensible\n"
            "defaults that you can accept by pressing Enter.\n\n"
            "Pick the workflow on the command line, or run 'cis-gs wizard'\n"
            "with no topic for the top-level menu.\n"
        ),
        epilog=(
            "TOPICS:\n"
            "  cis-gs wizard               # top-level menu\n"
            "  cis-gs wizard kegg          # KEGG enrichment  (live organism picker)\n"
            "  cis-gs wizard id-convert    # ID conversion    (NCBI taxonomy picker)\n"
            "  cis-gs wizard feed          # Expression Feeding\n"
            "  cis-gs wizard coexpr        # Co-expression network\n"
            "  cis-gs wizard kmeans        # K-means clustering\n"
            "  cis-gs wizard fetch         # NCBI genome fetch\n"
            "  cis-gs wizard extract       # Promoter extraction\n"
            "  cis-gs wizard search        # Motif search\n\n"
            "EXAMPLES:\n"
            "  $ cis-gs wizard kegg\n"
            "    [Step 1/5] KEGG organism\n"
            "      organism: arachis\n"
            "      3 match(es) for 'arachis':\n"
            "        1.  ahf       Arachis hypogaea (peanut)            [Plants]\n"
            "        2.  adu       Arachis duranensis                   [Plants]\n"
            "        3.  aip       Arachis ipaensis                     [Plants]\n"
            "      Pick a number: 1\n"
            "      OK  Using KEGG organism code: ahf\n"
            "    [Step 2/5] Query gene list\n"
            "      ...\n"
        ),
    )
    wiz.add_argument(
        "wizard_topic", nargs="?",
        choices=["menu", "kegg", "id", "id-convert", "feed", "coexpr",
                 "kmeans", "fetch", "extract", "search", "batch"],
        help="Wizard to launch (omit for the top-level menu).",
    )
    wiz.set_defaults(func=lambda args: None)  # main() handles dispatch

    # ── -i / --interactive on existing commands ─────────────────────────
    # Walk through every parser we just registered and add a uniform
    # --interactive flag so users can promote any command into a wizard.
    for action in sub._name_parser_map.values():
        if action.prog.endswith("wizard"):
            continue
        try:
            action.add_argument(
                "-i", "--interactive", action="store_true",
                help="Run this command as an interactive wizard (prompts you "
                     "for every value step-by-step instead of using flags).",
            )
        except argparse.ArgumentError:
            pass  # already added

    return parser


# ══════════════════════════════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════════════════════════════

def _print_banner():
    """Animated Cis-GS header.  Only fires in interactive TTY sessions
    so piped / scripted output stays clean.

    Phase 1 - Slim Nessie slithers across a 5-row sine-wave canvas.
              Body chars (/ \\ ~) are chosen per-column so they connect
              into proper S-curves as the snake slides from right to left.
    Phase 2 - Full banner reveals line-by-line (curtain-drop effect).
    """
    if not sys.stdout.isatty():
        return
    try:
        import time, math

        T  = "\033[36m"   # teal  (brand colour)
        B  = "\033[1m"    # bold
        D  = "\033[2m"    # dim
        R  = "\033[0m"    # reset
        CL = "\033[K"     # clear to end of line

        ROWS     = 5      # animation canvas height
        W        = 74     # canvas width (cols)
        AMP      = 1.8    # sine amplitude (rows from centre row)
        FREQ     = 0.45   # sine frequency (rad/col) → ~14-col S-curve period
        BODY_LEN = 24     # body chars trailing behind the head
        SPEED    = 3      # cols per frame  (total ≈ 1.1 s)

        def row_at(x):
            """Sine-wave row for column x, clamped to 0 … ROWS-1."""
            return max(0, min(ROWS - 1,
                round((ROWS - 1) / 2 + AMP * math.sin(x * FREQ))))

        def body_ch(x):
            """Direction char connecting column x toward the head (x-1).
            /  → head-side is a row higher (snake curves up-left)
            \\  → head-side is a row lower  (snake curves down-left)
            ~  → same row (horizontal run)
            """
            y0, y1 = row_at(x), row_at(x - 1)
            return '/' if y1 < y0 else ('\\' if y1 > y0 else '~')

        # Reserve ROWS terminal rows for the animation canvas
        sys.stdout.write("\n" * ROWS)
        UP = f"\033[{ROWS}A"
        sys.stdout.flush()

        blink = False
        for hx in range(W + BODY_LEN, -(BODY_LEN // 2 + 5), -SPEED):
            hy = row_at(hx)
            canvas = [[' '] * W for _ in range(ROWS)]

            # body: chars hx+1 … hx+BODY_LEN (trailing to the right of head)
            for i in range(1, BODY_LEN + 1):
                bx = hx + i
                by = row_at(bx)
                if 0 <= bx < W:
                    canvas[by][bx] = body_ch(bx)

            # head: single char, blinks @ / 0  (round Nessie eye)
            if 0 <= hx < W:
                canvas[hy][hx] = '0' if blink else '@'

            sys.stdout.write(UP)
            for row in canvas:
                sys.stdout.write(f"\r{T}{B}{''.join(row)}{R}{CL}\n")
            sys.stdout.flush()
            time.sleep(0.028)
            blink = not blink

        # Clear animation canvas
        sys.stdout.write(UP)
        for _ in range(ROWS):
            sys.stdout.write(f"\r{CL}\n")
        sys.stdout.flush()

        # ── Phase 2 : banner drops in line by line ──────────────────────────
        #
        # Layout (74 cols wide):
        #   Lines 1-6  : "Cis-GS" block text
        #   Lines 7-11 : Nessie head ──── DNA double helix ──── magnifying glass
        #
        #   DNA helix = two interlocked strands:
        #     top  (line 8) : \/\/\/  (29 × "\/" = 58 chars)
        #     bot  (line 9) : /\/\/\  (29 × "/\" = 58 chars)
        #   The two rows together create the classic X-crossing helix.
        #
        # LARGE Cis-GS text (left, in bordered box) + ASCII art DNA (right)
        _text_left = [
            "╔═══════════════════════════════════════════════╗",
            "║                                               ║",
            "║   ██████╗ ██╗███████╗      ██████╗ ███████╗  ║",
            "║  ██╔════╝ ██║██╔════╝     ██╔════╝ ██╔════╝  ║",
            "║  ██║      ██║███████╗     ██║  ███╗███████╗  ║",
            "║  ██║      ██║╚════██║     ██║   ██║╚════██║  ║",
            "║  ╚██████╗ ██║███████║     ╚██████╔╝███████║  ║",
            "║   ╚═════╝ ╚═╝╚══════╝      ╚═════╝ ╚══════╝  ║",
            "║                                               ║",
            "║  Cis-regulatory Element Genome Scanner       ║",
            "║                                               ║",
            "╚═══════════════════════════════════════════════╝",
        ]
        _art_right = [
            "                                                                                    ",
            "    ██████████████                        ███                        ██████████████  ",
            "    █████████████████               ██████████████               ██████████████████  ",
            "              █████████           ███████████████████          █████████             ",
            "                  ███████       ███████         ███████       ██████                 ",
            "      █             ██████     ██████             ██████    ██████              █    ",
            "      █    █    █     █████  ██████   ██   █        ██ ██  ██████     █    █    █    ",
            "      █    █    ██     ███████████    ██   █    ██   ███████████      █    █    █    ",
            "      █    █    ██      █████████     ██   █    ██    ████████        █    █    █    ",
            "      █    █    ██       █ ██ █       ██   █    ██     ██████         █    █    █    ",
            "      █    █    ██       ███████      ██   █    ██     ██████         █    █    █    ",
            "      █    █    ██      █████ ███     ██   █    ██    ████ ████       █    █    █    ",
            "      █    █    ██     ███████████    ██   █    ██   ███████████      █    █    █    ",
            "      █    █          █████  ██████   ██   █        █████  ██████          █    █    ",
            "      █             ██████     ██████             ██████    ██████                   ",
            "                  ███████       ████████       ███████        ██████                 ",
            "               ████████           ███████████████████          █████████             ",
            "    █████████████████               ██████████████                █████████████████  ",
            "    ██████████████                                                   ██████████████  ",
            "                                                                                     ",
        ]
        # Pad text left to match art right height (20 lines)
        while len(_text_left) < len(_art_right):
            _text_left.append("║                                               ║")

        banner = [
            _text_left[i] + "  " + _art_right[i]
            for i in range(len(_art_right))
        ]

        sys.stdout.write("\n")
        for line in banner:
            sys.stdout.write(f"{T}{B}{line}{R}\n")
            sys.stdout.flush()
            time.sleep(0.065)

        sys.stdout.write(
            f"\n{D}  Cis-regulatory Element Genome Scanner"
            f"  ·  v1.3.0"
            f"  ·  Plant Signaling Lab, IISER Tirupati{R}\n\n"
        )
        sys.stdout.flush()

    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def _all_subcommands(parser):
    """Walk argparse subparser tree to collect every valid subcommand."""
    out: list[str] = []
    for action in parser._actions:
        if hasattr(action, "choices") and action.choices:
            for name, sub in action.choices.items():
                out.append(name)
    return out


def _maybe_suggest_typo(argv):
    """If the first positional looks like a typo'd subcommand, suggest fixes.

    argparse exits with code 2 and an unhelpful 'invalid choice' on typos.
    We catch that case proactively before parse_args is called.
    """
    if len(argv) < 1:
        return
    first = argv[0]
    if first.startswith("-"):
        return
    p = _build_parser()
    valid = _all_subcommands(p)
    if first in valid:
        return
    try:
        from cis_gs.cli_interactive import did_you_mean, RED, GREEN, BOLD, RST, YEL
    except Exception:
        return
    matches = did_you_mean(first, valid, n=4, cutoff=0.5)
    if not matches:
        return
    print(f"\n{RED}{BOLD}Unknown command: {first!r}{RST}", file=sys.stderr)
    print(f"{YEL}Did you mean one of these?{RST}", file=sys.stderr)
    for m in matches:
        print(f"  {GREEN}cis-gs {m}{RST}", file=sys.stderr)
    print(f"\nRun {BOLD}cis-gs --help{RST} for the full command list, or "
          f"{BOLD}cis-gs wizard{RST} to launch the interactive menu.\n",
          file=sys.stderr)


def main():
    _print_banner()

    # ---- did-you-mean preflight on top-level command ---------------------
    # Skip the typo check if the user is already asking for help or a flag.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        _maybe_suggest_typo(sys.argv[1:])

    parser = _build_parser()
    args   = parser.parse_args()

    # ---- 'wizard' top-level command --------------------------------------
    if getattr(args, "command", None) == "wizard":
        from cis_gs.cli_interactive import (
            interactive_wizard_menu, interactive_kegg_enrichment,
            interactive_id_convert, interactive_feed, interactive_coexpr,
            interactive_kmeans, interactive_fetch, interactive_extract,
            interactive_search, interactive_batch,
        )
        sub = getattr(args, "wizard_topic", None)
        dispatch = {
            None:        interactive_wizard_menu,
            "menu":      interactive_wizard_menu,
            "kegg":      interactive_kegg_enrichment,
            "id":        interactive_id_convert,
            "id-convert": interactive_id_convert,
            "feed":      interactive_feed,
            "coexpr":    interactive_coexpr,
            "kmeans":    interactive_kmeans,
            "fetch":     interactive_fetch,
            "extract":   interactive_extract,
            "search":    interactive_search,
            "batch":     interactive_batch,
        }
        fn = dispatch.get(sub, interactive_wizard_menu)
        raise SystemExit(int(fn() or 0))

    if args.command is None:
        # No subcommand → launch GUI
        cmd_gui(args)
    elif args.command == "tfdb":
        if getattr(args, "tfdb_command", None) is None:
            # 'cis-gs tfdb' with no sub-subcommand → show tfdb help
            for action in parser._subparsers._actions:
                if hasattr(action, "_name_parser_map"):
                    action._name_parser_map["tfdb"].print_help()
                    break
        else:
            args.func(args)
    else:
        # If user passed -i / --interactive flag, route to the wizard for
        # this command instead of running the non-interactive command.
        if getattr(args, "interactive", False):
            try:
                from cis_gs import cli_interactive as ci
            except ImportError as exc:
                print(f"Could not load interactive module: {exc}", file=sys.stderr)
                raise SystemExit(2)
            iname = f"interactive_{args.command.replace('-', '_')}"
            fn = getattr(ci, iname, None)
            if fn is None:
                # Special-case enrich-kegg -> kegg_enrichment
                if args.command == "enrich-kegg":
                    fn = ci.interactive_kegg_enrichment
                elif args.command == "id-convert":
                    fn = ci.interactive_id_convert
            if fn is None:
                print(f"No interactive wizard for command: {args.command}",
                      file=sys.stderr)
                raise SystemExit(2)
            raise SystemExit(int(fn() or 0))
        args.func(args)


if __name__ == "__main__":
    main()
