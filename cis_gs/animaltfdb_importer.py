"""
animaltfdb_importer.py  –  TF Motif Importer for Cis-GS
═════════════════════════════════════════════════════════

Downloads TF binding motifs from JASPAR 2024 and HOCOMOCO v11:

  JASPAR 2024 — Vertebrates (EMBL-EBI, ~879 motifs)
  JASPAR 2024 — Insects     (EMBL-EBI, ~286 motifs)
  HOCOMOCO v11 — Human      (~700 motifs, ChIP-Seq)
  HOCOMOCO v11 — Mouse      (~400 motifs, ChIP-Seq)

After downloading, JASPAR metadata (species, TF family) is fetched
from the JASPAR REST API using parallel requests (20 threads).

Browse & Import tab filters:
  • Species  (Homo sapiens, Mus musculus, Danio rerio, …)
  • Source   (JASPAR, HOCOMOCO)
  • TF Family
  • Free-text search

Usage in app_v4.py
──────────────────
    from animaltfdb_importer import open_animaltfdb_dialog
    lines, append = open_animaltfdb_dialog(parent=self, save_dir=MOTIFS_DIR)
"""

import re, ssl as _ssl
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import urllib.request, urllib.error

# Suppress InsecureRequestWarning from requests when verify=False
try:
    import requests as _requests_mod
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

import pandas as pd

from PyQt5.QtCore  import Qt, QThread, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui   import QStandardItem, QStandardItemModel, QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QButtonGroup, QFileDialog, QTableView, QAbstractItemView,
    QMessageBox, QProgressBar, QTabWidget, QHeaderView, QGroupBox,
    QFrame,
)

# ═══════════════════════════════════════════════════════════════════════════════
# DATASET CATALOGUE  –  the downloadable file bundles from AnimalTFDB
# ═══════════════════════════════════════════════════════════════════════════════
# Each dataset has explicit "urls" (tried in order) and "annot_urls".
# "local_name"  = filename saved locally.
# "zip_member"  = if download is a .zip, auto-extract the first .meme inside.
DATASETS = [
    # ── JASPAR — EMBL-EBI European server, always reachable ───────────────
    {
        "id":         "jaspar2024_vertebrates",
        "label":      "JASPAR 2024 — Vertebrates (575 motifs, non-redundant)",
        "description":"Best-curated open-access vertebrate TF collection. Hosted at EMBL-EBI.",
        "icon":       "🐟",
        "note":       "Reliable EU server · Human, Mouse, Zebrafish, and more",
        "local_name": "JASPAR2024_CORE_vertebrates_non-redundant.meme",
        "zip_member": None,
        "urls": [
            "https://jaspar.elixir.no/download/data/2024/CORE/JASPAR2024_CORE_vertebrates_non-redundant_pfms_meme.zip",
            "https://jaspar.genereg.net/download/data/2024/CORE/JASPAR2024_CORE_vertebrates_non-redundant_pfms_meme.zip",
            "https://jaspar.elixir.no/download/data/2022/CORE/JASPAR2022_CORE_vertebrates_non-redundant_pfms_meme.zip",
        ],
        "annot_urls": [],
        "jaspar_api":  True,     # fetch rich metadata from JASPAR REST API
        "jaspar_tax":  "vertebrates",
    },
    {
        "id":         "jaspar2024_insects",
        "label":      "JASPAR 2024 — Insects (99 motifs, non-redundant)",
        "description":"Curated insect TF motifs from JASPAR 2024.",
        "icon":       "🦟",
        "note":       "Reliable EU server · Drosophila, Apis, Bombyx, and more",
        "local_name": "JASPAR2024_CORE_insects_non-redundant.meme",
        "zip_member": None,
        "urls": [
            "https://jaspar.elixir.no/download/data/2024/CORE/JASPAR2024_CORE_insects_non-redundant_pfms_meme.zip",
            "https://jaspar.genereg.net/download/data/2024/CORE/JASPAR2024_CORE_insects_non-redundant_pfms_meme.zip",
        ],
        "annot_urls": [],
        "jaspar_api":  True,
        "jaspar_tax":  "insects",
    },
    # ── HOCOMOCO — reliable international mirror ──────────────────────────
    {
        "id":         "hocomoco_human",
        "label":      "HOCOMOCO v11 — Human (~700 motifs, ChIP-Seq)",
        "description":"Gold standard for human TF analysis from large-scale ChIP-Seq.",
        "icon":       "🧬",
        "note":       "Reliable EU server · Homo sapiens only",
        "local_name": "HOCOMOCOv11_full_HUMAN_mono_meme_format.meme",
        "zip_member": None,
        "urls": [
            "https://hocomoco11.autosome.org/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_HUMAN_mono_meme_format.meme",
            "http://hocomoco11.autosome.org/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_HUMAN_mono_meme_format.meme",
            "https://hocomoco11.autosome.ru/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_HUMAN_mono_meme_format.meme",
        ],
        "annot_urls": [
            "https://hocomoco11.autosome.org/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_annotation_HUMAN_mono.tsv",
            "http://hocomoco11.autosome.org/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_annotation_HUMAN_mono.tsv",
            "https://hocomoco11.autosome.ru/final_bundle/hocomoco11/full/HUMAN/mono/HOCOMOCOv11_full_annotation_HUMAN_mono.tsv",
        ],
        "hocomoco_annot":   True,
        "hocomoco_species": "Homo sapiens",
    },
    {
        "id":         "hocomoco_mouse",
        "label":      "HOCOMOCO v11 — Mouse (~400 motifs, ChIP-Seq)",
        "description":"High-confidence mouse TF motifs from ChIP-Seq experiments.",
        "icon":       "🐭",
        "note":       "Reliable EU server · Mus musculus only",
        "local_name": "HOCOMOCOv11_full_MOUSE_mono_meme_format.meme",
        "zip_member": None,
        "urls": [
            "https://hocomoco11.autosome.org/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_MOUSE_mono_meme_format.meme",
            "http://hocomoco11.autosome.org/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_MOUSE_mono_meme_format.meme",
            "https://hocomoco11.autosome.ru/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_MOUSE_mono_meme_format.meme",
        ],
        "annot_urls": [
            "https://hocomoco11.autosome.org/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_annotation_MOUSE_mono.tsv",
            "http://hocomoco11.autosome.org/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_annotation_MOUSE_mono.tsv",
            "https://hocomoco11.autosome.ru/final_bundle/hocomoco11/full/MOUSE/mono/HOCOMOCOv11_full_annotation_MOUSE_mono.tsv",
        ],
        "hocomoco_annot":   True,
        "hocomoco_species": "Mus musculus",
    },
]

_DOWNLOAD_PAGE = "https://jaspar.elixir.no/"

# ═══════════════════════════════════════════════════════════════════════════════
# SSL + REQUEST HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _ssl_ctx():
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = _ssl.CERT_NONE
    return ctx

def _make_req(url: str) -> urllib.request.Request:
    req = urllib.request.Request(url)
    req.add_header("User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36")
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "en-US,en;q=0.5")
    req.add_header("Accept-Encoding", "gzip, deflate")
    req.add_header("Connection", "keep-alive")
    # Referer is required — AnimalTFDB server blocks direct downloads without it
    return req

# ═══════════════════════════════════════════════════════════════════════════════
# IUPAC HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
_BASE_ORDER = ["A", "C", "G", "T"]
_BASES_TO_IUPAC: Dict[frozenset, str] = {
    frozenset("A"):"A",    frozenset("C"):"C",
    frozenset("G"):"G",    frozenset("T"):"T",
    frozenset("AG"):"R",   frozenset("CT"):"Y",
    frozenset("GC"):"S",   frozenset("AT"):"W",
    frozenset("GT"):"K",   frozenset("AC"):"M",
    frozenset("CGT"):"B",  frozenset("AGT"):"D",
    frozenset("ACT"):"H",  frozenset("ACG"):"V",
    frozenset("ACGT"):"N",
}

def pfm_to_iupac(pfm: List[List[float]], threshold: float = 0.25) -> str:
    result = []
    for row in pfm:
        probs = list(zip(_BASE_ORDER, row))
        max_p = max(p for _, p in probs)
        cutoff = max(threshold, max_p * 0.30)
        included = [b for b, p in probs if p >= cutoff] or [max(probs, key=lambda x: x[1])[0]]
        result.append(_BASES_TO_IUPAC.get(frozenset(included), "N"))
    return "".join(result)

def pfm_to_simple(pfm: List[List[float]]) -> str:
    return "".join(_BASE_ORDER[row.index(max(row))] for row in pfm)

# ═══════════════════════════════════════════════════════════════════════════════
# FILE PARSERS
# ═══════════════════════════════════════════════════════════════════════════════
def parse_meme_file(path: str) -> List[dict]:
    """Parse a standard MEME file. Works for both PlantTFDB and AnimalTFDB."""
    motifs, current = [], None
    with open(path, "r", errors="replace") as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("MOTIF "):
            parts = line.split()
            current = dict(
                motif_id  = parts[1] if len(parts) > 1 else "unknown",
                alt_id    = parts[2] if len(parts) > 2 else "",
                pfm=[], width=0, nsites=0, evalue="",
                iupac="", consensus="",
                # will be filled by annotation:
                tf_name="", species="", source="", family="",
            )
            motifs.append(current)
        elif current is not None:
            if line.startswith("letter-probability matrix:"):
                for pat, key in [(r"w=\s*(\d+)","width"),
                                 (r"nsites=\s*(\d+)","nsites"),
                                 (r"E=\s*(\S+)","evalue")]:
                    m = re.search(pat, line)
                    if m:
                        current[key] = int(m.group(1)) if key != "evalue" else m.group(1)
                i += 1
                while i < len(lines):
                    rl = lines[i].strip()
                    if not rl or rl.startswith("MOTIF") or rl.startswith("URL"): break
                    vals = rl.split()
                    if len(vals) == 4:
                        try: current["pfm"].append([float(v) for v in vals])
                        except ValueError: break
                    else: break
                    i += 1
                if current["pfm"]:
                    current["iupac"]     = pfm_to_iupac(current["pfm"])
                    current["consensus"] = pfm_to_simple(current["pfm"])
                continue
        i += 1
    return motifs


def parse_annotation_file(path: str) -> Dict[str, dict]:
    """
    Parse annotation files from AnimalTFDB or JASPAR REST API TSV.

    Supported formats (all tab-separated):
      JASPAR API TSV   : motif_id  tf_name  species  family  source
      AnimalTFDB 4     : motif_id  TF_name  Species  Source  Family
      hTFtarget        : motif_id  TF_name  ...

    Returns {motif_id: {tf_name, species, source, family}}.
    """
    info: Dict[str, dict] = {}
    try:
        df = pd.read_csv(path, sep="\t", header=0, dtype=str, comment=None)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        def _col(*candidates):
            for c in candidates:
                if c in df.columns: return c
            return None

        id_col      = _col("motif_id", "matrix_id", "id", "#id", "motif")
        name_col    = _col("tf_name", "name", "gene_name", "gene", "tf", "symbol")
        species_col = _col("species", "organism", "taxon", "species_name")
        source_col  = _col("source", "database", "db", "origin")
        family_col  = _col("family", "tf_family", "tf_class", "class", "type")

        if id_col is None:
            id_col = df.columns[0]

        for _, row in df.iterrows():
            mid = str(row.get(id_col, "")).strip()
            if not mid or mid == "nan": continue
            info[mid] = {
                "tf_name": (str(row[name_col]).strip()
                            if name_col and str(row.get(name_col,"")) != "nan" else ""),
                "species": (str(row[species_col]).strip()
                            if species_col and str(row.get(species_col,"")) != "nan" else ""),
                "source":  (str(row[source_col]).strip()
                            if source_col and str(row.get(source_col,"")) != "nan" else ""),
                "family":  (str(row[family_col]).strip()
                            if family_col and str(row.get(family_col,"")) != "nan" else ""),
            }
    except Exception:
        pass
    return info


def enrich_motifs(motifs: List[dict], info: Dict[str, dict]) -> List[dict]:
    for m in motifs:
        # Try both motif_id and alt_id for lookup
        meta = info.get(m["motif_id"]) or info.get(m["alt_id"]) or {}
        m["tf_name"] = meta.get("tf_name", "") or m["alt_id"] or m["motif_id"]
        m["species"] = meta.get("species", "")
        m["source"]  = meta.get("source",  "")
        m["family"]  = meta.get("family",  "")
    return motifs

def _fill_defaults(motifs: List[dict]) -> List[dict]:
    for m in motifs:
        m.setdefault("tf_name", m.get("alt_id") or m.get("motif_id", ""))
        m.setdefault("species", "")
        m.setdefault("source",  "")
        m.setdefault("family",  "")
    return motifs

# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class _DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, str)   # meme_path, annot_path (empty if failed)
    error    = pyqtSignal(str)

    def __init__(self, dataset: dict, save_dir: Path):
        super().__init__()
        self.dataset  = dataset
        self.save_dir = save_dir

    def run(self):
        import zipfile as _zf, io as _bio
        ds       = self.dataset
        save_dir = self.save_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        local_name = ds["local_name"]
        meme_dest  = save_dir / local_name
        urls_meme  = ds["urls"]
        urls_annot = ds.get("annot_urls", [])

        # ── MEME / ZIP file ────────────────────────────────────────────────
        self.progress.emit(0, f"Connecting for '{ds['label']}' …")

        # Download to a temp name first so we can handle .zip
        tmp_dest = save_dir / (local_name + ".tmp")
        ok, errors = self._download(urls_meme, tmp_dest, 0, 60,
                                    "MEME", validate_meme=False)
        if not ok:
            tried = "\n".join(f"  • {u}\n      → {e}" for u, e in errors)
            note  = ds.get("note", "")
            self.error.emit(
                f"Could not download the MEME file for:\n"
                f"  {ds['label']}\n\n"
                f"URLs tried:\n{tried}\n\n"
                + (f"Note: {note}\n\n" if note else "")
                + "The AnimalTFDB server blocks automated downloads but\n"
                  "works fine in a browser. To get the file manually:\n\n"
                  "  1. Open the database website in your browser\n"
                  "  2. Go to the Download page → TFBS section\n"
                  "  3. Download the .meme file (and optionally the .annotation file)\n"
                  "  4. Come back here → Browse & Import tab → Browse to load the file"
            )
            return

        # Handle .zip — concatenate ALL .meme files inside into one
        with open(tmp_dest, "rb") as fh:
            header4 = fh.read(4)
        if header4[:2] == b"PK":   # zip magic
            self.progress.emit(62, "Extracting motifs from zip …")
            try:
                with _zf.ZipFile(tmp_dest) as zf:
                    meme_members = sorted(m for m in zf.namelist()
                                         if m.endswith(".meme"))
                    if not meme_members:
                        self.error.emit("Downloaded zip contains no .meme files."); return

                    self.progress.emit(63, f"Merging {len(meme_members)} motif files …")

                    if len(meme_members) == 1:
                        # Single file — extract directly
                        with zf.open(meme_members[0]) as sf, open(meme_dest, "wb") as df:
                            df.write(sf.read())
                    else:
                        # Multiple files — write one combined MEME file
                        # Header comes from first file; only MOTIF blocks from the rest
                        with open(meme_dest, "wb") as out:
                            first = True
                            for i, member in enumerate(meme_members):
                                pct = 63 + int(i / len(meme_members) * 15)
                                self.progress.emit(pct,
                                    f"Merging {i+1}/{len(meme_members)} motifs …")
                                data = zf.read(member).decode("utf-8", errors="replace")
                                if first:
                                    out.write(data.encode("utf-8"))
                                    first = False
                                else:
                                    # Extract only the MOTIF blocks (skip header)
                                    in_motif = False
                                    for line in data.splitlines(keepends=True):
                                        if line.startswith("MOTIF "):
                                            in_motif = True
                                        if in_motif:
                                            out.write(line.encode("utf-8"))
                tmp_dest.unlink()
            except Exception as ex:
                self.error.emit(f"Could not extract zip: {ex}"); return
        else:
            if meme_dest.exists():
                meme_dest.unlink()
            tmp_dest.rename(meme_dest)

        # Final validation — must contain MEME text
        with open(meme_dest, "rb") as fh:
            sample = fh.read(100)
        if b"MEME" not in sample:
            meme_dest.unlink()
            self.error.emit(
                f"Downloaded file does not look like a MEME file\n"
                f"(first bytes: {sample[:40]!r}).\n\n"
                "The server may have returned an error page.\n"
                "Try downloading the file manually."
            )
            return

        # ── Annotation: JASPAR API or file download ───────────────────────
        annot_dest = save_dir / (local_name.replace(".meme", ".annotation"))
        ok_a = False

        if ds.get("jaspar_api"):
            self.progress.emit(79, "Fetching metadata from JASPAR REST API …")
            ok_a = self._fetch_jaspar_metadata(
                tax_group = ds.get("jaspar_tax", "vertebrates"),
                dest      = annot_dest,
            )
            if not ok_a:
                self.progress.emit(85, "⚠ JASPAR API unavailable — names will be motif IDs")
        elif ds.get("hocomoco_annot") and urls_annot:
            self.progress.emit(79, "Downloading HOCOMOCO annotation …")
            ok_a, _ = self._download(urls_annot, annot_dest, 79, 95,
                                     "Annotation", validate_meme=False)
            if ok_a:
                ok_a = self._convert_hocomoco_annotation(
                    annot_dest,
                    species=ds.get("hocomoco_species", "")
                )
        elif urls_annot:
            self.progress.emit(79, "Downloading annotation file …")
            ok_a, _ = self._download(urls_annot, annot_dest, 79, 95,
                                     "Annotation", validate_meme=False)

        self.progress.emit(100, "Download complete ✅")
        self.finished.emit(str(meme_dest), str(annot_dest) if ok_a else "")

    def _fetch_jaspar_metadata(self, tax_group: str, dest: Path) -> bool:
        """
        Fetch full JASPAR metadata (name, species, family) for every motif.

        Strategy:
          Step 1 — list endpoint: gets matrix_id + detail URL for every motif
          Step 2 — detail endpoints (threaded, 20 workers): gets species + family
        The list endpoint only returns name/id; species and family only appear
        in individual matrix detail responses.
        """
        import json as _json
        from concurrent.futures import ThreadPoolExecutor, as_completed

        api_bases = [
            "https://jaspar.elixir.no/api/v1",
            "https://jaspar.genereg.net/api/v1",
        ]

        def _get_json(url, timeout=30):
            """Fetch JSON from url using requests (preferred) or urllib."""
            try:
                import requests as _req
                r = _req.get(url, timeout=timeout, verify=False)
                r.raise_for_status()
                return r.json()
            except Exception:
                req = _make_req(url)
                with urllib.request.urlopen(req, timeout=timeout,
                                            context=_ssl_ctx()) as r:
                    return _json.loads(r.read().decode())

        def _fetch_detail(item):
            """Fetch a single matrix detail URL; return enriched dict."""
            mid  = item["matrix_id"]
            name = item.get("name", "")
            url  = item.get("url", "")
            if not url:
                return mid, name, "", "", "JASPAR"
            try:
                d = _get_json(url)
                species = "; ".join(
                    s.get("name", "") for s in d.get("species", []) if s.get("name")
                )
                family = "; ".join(
                    str(f) for f in d.get("family", []) if f
                )
                if not family:
                    family = "; ".join(
                        str(c) for c in d.get("class", []) if c
                    )
                return mid, name, species, family, "JASPAR"
            except Exception:
                return mid, name, "", "", "JASPAR"

        for base in api_bases:
            try:
                # ── Step 1: collect all matrix summaries (has detail URLs) ──
                self.progress.emit(79, f"JASPAR API: fetching motif list …")
                summaries = []
                page_url = (f"{base}/matrix/"
                            f"?collection=CORE&tax_group={tax_group}"
                            f"&page_size=1000&format=json")
                while page_url:
                    data = _get_json(page_url)
                    summaries.extend(data.get("results", []))
                    page_url = data.get("next")

                if not summaries:
                    continue

                total = len(summaries)
                self.progress.emit(80, f"JASPAR API: fetching details for {total} motifs …")

                # ── Step 2: fetch detail for each motif (20 threads) ────────
                rows = [None] * total
                done = [0]

                with ThreadPoolExecutor(max_workers=20) as pool:
                    future_map = {
                        pool.submit(_fetch_detail, s): i
                        for i, s in enumerate(summaries)
                    }
                    for fut in as_completed(future_map):
                        i = future_map[fut]
                        try:
                            rows[i] = fut.result()
                        except Exception:
                            s = summaries[i]
                            rows[i] = (s["matrix_id"], s.get("name",""), "", "", "JASPAR")
                        done[0] += 1
                        pct = 80 + int(done[0] / total * 15)
                        self.progress.emit(
                            pct,
                            f"JASPAR API: {done[0]}/{total} motifs enriched …"
                        )

                rows = [r for r in rows if r]
                if rows:
                    break   # success

            except Exception:
                rows = []
                continue

        if not rows:
            return False

        try:
            with open(dest, "w", encoding="utf-8") as fout:
                fout.write("motif_id\ttf_name\tspecies\tfamily\tsource\n")
                for mid, name, species, family, source in rows:
                    fout.write(f"{mid}\t{name}\t{species}\t{family}\t{source}\n")
            return True
        except Exception:
            return False

    def _convert_hocomoco_annotation(self, tsv_path: Path, species: str = "") -> bool:
        """
        Convert HOCOMOCO's native annotation TSV into the standard
        (motif_id, tf_name, species, family, source) format.

        HOCOMOCO TSV columns (example):
          Model                  → motif ID, e.g. AHR_HUMAN.H11MO.0.B
          Transcription factor   → TF name,  e.g. AHR (AHR_HUMAN)
          TF family              → family,   e.g. PAS domain factors
          (other columns ignored)
        """
        import csv
        try:
            rows_out = []
            with open(tsv_path, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh, delimiter="\t")
                for row in reader:
                    rn = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                    # motif ID → "Model" column
                    mid = (rn.get("model") or rn.get("matrix_id") or
                           next(iter(rn.values()), "")).strip()
                    if not mid:
                        continue

                    # TF name → "Transcription factor" column
                    # HOCOMOCO format: "AHR (AHR_HUMAN)" — take gene symbol part
                    tf_raw = (rn.get("transcription factor") or
                              rn.get("tf name") or rn.get("name") or "")
                    if "(" in tf_raw:
                        # Prefer the part inside parens: "AHR (AHR_HUMAN)" → "AHR"
                        tf_name = tf_raw.split("(")[0].strip()
                    else:
                        # Fall back to first part of motif ID: AHR_HUMAN.H11MO → AHR
                        tf_name = tf_raw or mid.split("_")[0]

                    # TF family
                    family = (rn.get("tf family") or rn.get("family") or
                              rn.get("class") or rn.get("pfam") or "")

                    # Species — from arg or annotation column
                    sp = species or rn.get("species", "")

                    rows_out.append((mid, tf_name, sp, family, "HOCOMOCO"))

            if not rows_out:
                return False

            with open(tsv_path, "w", encoding="utf-8") as fout:
                fout.write("motif_id\ttf_name\tspecies\tfamily\tsource\n")
                for mid, name, sp, fam, src in rows_out:
                    fout.write(f"{mid}\t{name}\t{sp}\t{fam}\tHOCOMOCO\n")
            return True

        except Exception:
            return False

    def _download(self, urls, dest, start_pct, end_pct, label, validate_meme=False):
        """
        Try each URL with three escalating strategies:
          1. cloudscraper  — bypasses JS bot-challenges (needs: pip install cloudscraper)
          2. requests      — handles session cookies + redirects
          3. urllib        — plain fallback
        """
        import gzip as _gzip

        try:
            import cloudscraper as _cs
            HAS_SCRAPER = True
        except ImportError:
            HAS_SCRAPER = False

        try:
            import requests as _req
            HAS_REQUESTS = True
        except ImportError:
            HAS_REQUESTS = False

        BROWSER_HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        errors = []
        for url in urls:
            try:
                # ── Determine referer / homepage for this domain ───────────
                from urllib.parse import urlparse
                parsed   = urlparse(url)
                homepage = f"{parsed.scheme}://{parsed.netloc}/"
                is_animal_tfdb = False  # AnimalTFDB removed; no bot-challenge needed

                if HAS_SCRAPER and is_animal_tfdb:
                    # ── cloudscraper path — solves JS bot challenges ────────
                    scraper = _cs.create_scraper(browser={"browser":"chrome",
                                                           "platform":"windows",
                                                           "mobile":False})
                    if is_animal_tfdb:
                        try: scraper.get(_DOWNLOAD_PAGE, timeout=15)
                        except Exception: pass
                    resp = scraper.get(url, stream=True, timeout=120,
                                       headers={"Referer": _DOWNLOAD_PAGE})
                    resp.raise_for_status()
                    total = int(resp.headers.get("Content-Length", 0))
                    received = 0; raw = b""
                    for chunk in resp.iter_content(chunk_size=131072):
                        if not chunk: continue
                        raw += chunk; received += len(chunk)
                        if total:
                            pct = int(start_pct + (received/total)*(end_pct-start_pct))
                            self.progress.emit(pct, f"{label}: {received//1024:,} KB")

                elif HAS_REQUESTS:
                    # ── requests path (handles cookies + redirects natively) ─
                    session = _req.Session()
                    session.verify = False          # skip SSL cert check
                    session.headers.update(BROWSER_HEADERS)

                    if is_animal_tfdb:
                        # Visit homepage first to pick up any session cookies
                        try:
                            session.get(_DOWNLOAD_PAGE, timeout=15,
                                        headers={"Referer": homepage})
                        except Exception:
                            pass   # best-effort; continue even if this fails

                    dl_headers = {
                        "Referer":  _DOWNLOAD_PAGE if is_animal_tfdb else homepage,
                        "Origin":   f"{parsed.scheme}://{parsed.netloc}",
                    }

                    resp = session.get(url, headers=dl_headers,
                                       stream=True, timeout=120)
                    resp.raise_for_status()

                    total    = int(resp.headers.get("Content-Length", 0))
                    received = 0
                    raw      = b""
                    for chunk in resp.iter_content(chunk_size=131072):
                        if not chunk: continue
                        raw      += chunk
                        received += len(chunk)
                        if total:
                            pct = int(start_pct + (received/total)*(end_pct-start_pct))
                            self.progress.emit(pct, f"{label}: {received//1024:,} KB")

                else:
                    # ── urllib fallback ────────────────────────────────────
                    req = _make_req(url)
                    if is_animal_tfdb:
                        req.add_header("Referer", _DOWNLOAD_PAGE)
                        req.add_header("Origin",
                                       f"{parsed.scheme}://{parsed.netloc}")
                    with urllib.request.urlopen(req, timeout=120,
                                                context=_ssl_ctx()) as r:
                        total    = int(r.headers.get("Content-Length", 0))
                        received = 0
                        raw      = b""
                        while True:
                            chunk = r.read(131072)
                            if not chunk: break
                            raw      += chunk
                            received += len(chunk)
                            if total:
                                pct = int(start_pct + (received/total)*(end_pct-start_pct))
                                self.progress.emit(pct, f"{label}: {received//1024:,} KB")

                # Decompress gzip-encoded body if needed
                if raw[:2] == b'\x1f\x8b':
                    try: raw = _gzip.decompress(raw)
                    except Exception: pass

                # Reject HTML error pages for MEME downloads
                if validate_meme and (b"<html" in raw[:200].lower() or
                                      b"<!doctype" in raw[:200].lower()):
                    errors.append((url, "Server returned an HTML page — likely a 404 or session issue"))
                    continue

                with open(dest, "wb") as fout:
                    fout.write(raw)

                if not (dest.exists() and dest.stat().st_size > 0):
                    errors.append((url, "Downloaded file is empty"))
                    if dest.exists(): dest.unlink()
                    continue

                if validate_meme:
                    with open(dest, "rb") as f: hdr = f.read(100)
                    if b"MEME" not in hdr and hdr[:2] != b'\x1f\x8b':
                        dest.unlink()
                        # Detect JS bot-challenge pages specifically
                        if b"<html" in hdr.lower() and b"var arg" in hdr.lower():
                            errors.append((url,
                                "BOT_CHALLENGE: Server returned a JavaScript "
                                "bot-protection page — automated download blocked"))
                        else:
                            errors.append((url,
                                f"Not a MEME file (starts with {hdr[:40]!r})"))
                        continue

                return True, []

            except Exception as e:
                # Catch everything — requests HTTPError, urllib errors, etc.
                code = ""
                if HAS_REQUESTS:
                    import requests as _rq
                    if isinstance(e, _rq.exceptions.HTTPError):
                        code = f"HTTP {e.response.status_code} {e.response.reason} — "
                    elif isinstance(e, _rq.exceptions.ConnectionError):
                        code = "Connection error — "
                errors.append((url, f"{code}{type(e).__name__}: {e}"))
                if dest.exists(): dest.unlink()

        return False, errors


# ═══════════════════════════════════════════════════════════════════════════════
# COLOUR MAP  (by source database)
# ═══════════════════════════════════════════════════════════════════════════════
_SOURCE_COLORS = {
    "JASPAR":    "#7FB3D8",
    "HOCOMOCO":  "#81C784",
    "TRANSFAC":  "#A8D08D",
    "CIS-BP":    "#BA94D1",
    "hTFtarget": "#E0967A",
}
_FAM_COLORS = {
    "bHLH":"#7FB3D8", "bZIP":"#BA94D1", "C2H2":"#6EC6D0",
    "ETS":"#81C784",  "Forkhead":"#A8D08D", "GATA":"#8E99CC",
    "Homeodomain":"#E0967A", "MYB":"#E8A0B5", "NHR":"#E8B96E",
    "p53":"#A0A8B0",  "SMAD":"#C5D97E",  "T-box":"#A8D08D",
    "Zinc finger":"#6EC6D0",
}
def _row_color(m: dict) -> str:
    src = m.get("source",""); fam = m.get("family","")
    return _SOURCE_COLORS.get(src, _FAM_COLORS.get(fam, "#8CA0A8"))

# ═══════════════════════════════════════════════════════════════════════════════
# MOTIF BROWSER WIDGET  (same pattern as planttfdb_importer, but with Species col)
# ═══════════════════════════════════════════════════════════════════════════════
_HEADERS = ["✓", "Motif ID", "TF Name", "Species", "Source",
            "TF Family", "IUPAC Consensus", "Width", "# Sites"]
_CH, _MI, _TN, _SP, _SO, _FA, _IU, _WI, _NS = range(9)

class AnimalMotifBrowserWidget(QWidget):
    import_requested = pyqtSignal(list, bool)   # lines, append_mode

    def __init__(self, parent=None, save_dir: Path = None):
        super().__init__(parent)
        self._save_dir = save_dir or Path(".")
        self._motifs: List[dict] = []
        self._selected: List[dict] = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        # ── File row ──────────────────────────────────────────────────────
        fg = QGridLayout()
        fg.addWidget(QLabel("MEME file:"), 0, 0)
        self._meme_edit = QLineEdit()
        self._meme_edit.setPlaceholderText("Auto-filled after download, or Browse …")
        fg.addWidget(self._meme_edit, 0, 1)
        b1 = QPushButton("Browse …"); b1.clicked.connect(self._browse_meme)
        fg.addWidget(b1, 0, 2)

        fg.addWidget(QLabel("Annotation:"), 1, 0)
        self._annot_edit = QLineEdit()
        self._annot_edit.setPlaceholderText("Optional – auto-filled after download …")
        fg.addWidget(self._annot_edit, 1, 1)
        b2 = QPushButton("Browse …"); b2.clicked.connect(self._browse_annot)
        fg.addWidget(b2, 1, 2)

        lb = QPushButton("  ↺  Load / Reload")
        lb.setStyleSheet("background:#00695C;color:white;font-weight:bold;"
                         "padding:4px 14px;border-radius:3px;")
        lb.clicked.connect(self.reload)
        fg.addWidget(lb, 2, 1)

        self._load_lbl = QLabel("")
        self._load_lbl.setStyleSheet("color:#555;font-style:italic;font-size:10px;")
        fg.addWidget(self._load_lbl, 3, 0, 1, 3)
        root.addLayout(fg)

        # ── Filter row ────────────────────────────────────────────────────
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Species:"))
        self._sp_cb = QComboBox(); self._sp_cb.addItem("All species")
        self._sp_cb.setMinimumWidth(150)
        self._sp_cb.currentTextChanged.connect(self._apply)
        fl.addWidget(self._sp_cb)

        fl.addWidget(QLabel("Source:"))
        self._src_cb = QComboBox(); self._src_cb.addItem("All sources")
        self._src_cb.setMinimumWidth(110)
        self._src_cb.currentTextChanged.connect(self._apply)
        fl.addWidget(self._src_cb)

        fl.addWidget(QLabel("Family:"))
        self._fam_cb = QComboBox(); self._fam_cb.addItem("All families")
        self._fam_cb.setMinimumWidth(110)
        self._fam_cb.currentTextChanged.connect(self._apply)
        fl.addWidget(self._fam_cb)

        fl.addWidget(QLabel("Search:"))
        self._srch = QLineEdit(); self._srch.setPlaceholderText("TF name / ID / family …")
        self._srch.setMinimumWidth(130); self._srch.textChanged.connect(self._apply)
        fl.addWidget(self._srch)

        fl.addWidget(QLabel("IUPAC threshold:"))
        self._thr = QComboBox()
        for lbl in ["0.20 (relaxed)","0.25 (default)","0.30 (strict)","0.40 (very strict)"]:
            self._thr.addItem(lbl)
        self._thr.setCurrentIndex(1)
        self._thr.currentIndexChanged.connect(self._recompute)
        fl.addWidget(self._thr)
        fl.addStretch()
        root.addLayout(fl)

        # ── Table ─────────────────────────────────────────────────────────
        self._model = QStandardItemModel(0, len(_HEADERS))
        self._model.setHorizontalHeaderLabels(_HEADERS)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterKeyColumn(-1)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self._tv = QTableView()
        self._tv.setModel(self._proxy)
        self._tv.setSortingEnabled(True)
        self._tv.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tv.setAlternatingRowColors(False)
        self._tv.verticalHeader().setVisible(False)
        hdr = self._tv.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(_IU, QHeaderView.Stretch)
        self._tv.setStyleSheet(
            "QTableView{font-size:11px;}"
            "QTableView::item:selected{background:#5EB5B1;color:white;}"
        )
        self._tv.clicked.connect(self._toggle)
        root.addWidget(self._tv, stretch=1)

        # ── Selection bar ─────────────────────────────────────────────────
        sr = QHBoxLayout()
        self._cnt_lbl = QLabel("No motifs loaded")
        self._cnt_lbl.setStyleSheet("font-weight:bold;")
        sr.addWidget(self._cnt_lbl); sr.addStretch()
        for lbl, fn in [("☑ All Visible", self._sel_all),
                         ("☐ Deselect All", self._desel_all)]:
            b = QPushButton(lbl); b.clicked.connect(fn); sr.addWidget(b)
        root.addLayout(sr)

        # ── Options + Import ──────────────────────────────────────────────
        or_ = QHBoxLayout()
        self._append_cb = QCheckBox("Append (don't replace)")
        or_.addWidget(self._append_cb)
        self._prefix_cb = QCheckBox("Prefix name:  TFName|MotifID")
        self._prefix_cb.setChecked(True)
        or_.addWidget(self._prefix_cb)
        or_.addStretch()
        self._imp_btn = QPushButton("  🐾  Import to Cis-GS Step 2")
        self._imp_btn.setEnabled(False)
        self._imp_btn.setStyleSheet(
            "background:#00695C;color:white;font-weight:bold;"
            "padding:8px 20px;border-radius:5px;font-size:12px;"
        )
        self._imp_btn.clicked.connect(self._do_import)
        or_.addWidget(self._imp_btn)
        root.addLayout(or_)

    # ── Public API ────────────────────────────────────────────────────────

    def set_files(self, meme_path: str, annot_path: str = ""):
        if meme_path: self._meme_edit.setText(meme_path)
        if annot_path: self._annot_edit.setText(annot_path)

    def reload(self):
        meme  = self._meme_edit.text().strip()
        annot = self._annot_edit.text().strip()
        if not meme or not Path(meme).exists():
            QMessageBox.warning(self, "Load", "Please select a valid MEME file."); return
        self._load_lbl.setText("⏳  Parsing …"); QApplication.processEvents()
        try:
            motifs = parse_meme_file(meme)
        except Exception as ex:
            self._load_lbl.setText(f"❌  {ex}"); return

        if annot and Path(annot).exists():
            try:
                info = parse_annotation_file(annot)
                motifs = enrich_motifs(motifs, info)
            except Exception:
                pass

        _fill_defaults(motifs)
        self._motifs = motifs
        n = len(motifs)
        has_annot = any(m.get("tf_name") for m in motifs)
        self._load_lbl.setText(
            f"✅  {n:,} motifs loaded from {Path(meme).name}"
            + ("  +  annotation" if has_annot else "  (no annotation — TF names are motif IDs)")
        )
        self._rebuild_filters()
        self._populate()

    def get_motif_lines(self) -> List[str]:
        lines = []
        use_prefix = self._prefix_cb.isChecked()
        for m in self._selected:
            name = m.get("tf_name") or m["motif_id"]
            if use_prefix:
                name = f"{name}|{m['motif_id']}"
            lines.append(f"{name}\t{m['iupac']}")
        return lines

    def get_append_mode(self) -> bool:
        return self._append_cb.isChecked()

    # ── File browse ───────────────────────────────────────────────────────

    def _browse_meme(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select MEME File", str(self._save_dir),
                                           "MEME files (*.meme *.txt);;All files (*)")
        if p: self._meme_edit.setText(p); self.reload()

    def _browse_annot(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Annotation File", str(self._save_dir),
                                           "Annotation files (*.annotation *.txt *.tsv);;All (*)")
        if p: self._annot_edit.setText(p); self.reload()

    # ── Filters ───────────────────────────────────────────────────────────

    def _rebuild_filters(self):
        combos = [
            (self._sp_cb,  "species", "All species"),
            (self._src_cb, "source",  "All sources"),
            (self._fam_cb, "family",  "All families"),
        ]
        for cb, key, lbl in combos:
            items = sorted({m.get(key,"") for m in self._motifs if m.get(key,"")})
            cb.blockSignals(True); cb.clear(); cb.addItem(lbl)
            for it in items: cb.addItem(it)
            cb.blockSignals(False)

    def _get_threshold(self) -> float:
        return float(self._thr.currentText().split()[0])

    def _populate(self, checked_ids: set = None):
        checked_ids = checked_ids or set()
        self._model.setRowCount(0)
        sp_f  = self._sp_cb.currentText()
        src_f = self._src_cb.currentText()
        fam_f = self._fam_cb.currentText()
        txt_f = self._srch.text().strip().lower()

        for m in self._motifs:
            if sp_f  != "All species"  and m.get("species","") != sp_f:  continue
            if src_f != "All sources"  and m.get("source","")  != src_f: continue
            if fam_f != "All families" and m.get("family","")  != fam_f: continue
            if txt_f:
                hay = " ".join([m.get("motif_id",""), m.get("tf_name",""),
                                m.get("species",""),  m.get("source",""),
                                m.get("family",""),   m.get("iupac","")]).lower()
                if txt_f not in hay: continue

            mid  = m["motif_id"]
            chk  = QStandardItem()
            chk.setCheckState(Qt.Checked if mid in checked_ids else Qt.Unchecked)
            chk.setCheckable(True); chk.setTextAlignment(Qt.AlignCenter)
            chk.setData(mid, Qt.UserRole)

            mi = QStandardItem(mid)
            tn = QStandardItem(m.get("tf_name","") or mid)
            sp = QStandardItem(m.get("species",""))
            so = QStandardItem(m.get("source",""))
            fa = QStandardItem(m.get("family",""))
            iu = QStandardItem(m.get("iupac","")); iu.setFont(QFont("Courier New",9))
            wi = QStandardItem(str(m.get("width",""))); wi.setTextAlignment(Qt.AlignCenter)
            ns = QStandardItem(str(m.get("nsites",""))); ns.setTextAlignment(Qt.AlignCenter)

            col = QColor(_row_color(m))
            _txt = QColor("#1a1a1a")
            for item in [tn, so, fa]:
                item.setBackground(col)
                item.setForeground(_txt)

            self._model.appendRow([chk, mi, tn, sp, so, fa, iu, wi, ns])
        self._update_cnt()

    def _apply(self):  self._populate(self._checked_ids())

    def _recompute(self):
        t = self._get_threshold()
        for m in self._motifs:
            if m["pfm"]: m["iupac"] = pfm_to_iupac(m["pfm"], threshold=t)
        self._populate(self._checked_ids())

    def _toggle(self, idx):
        src = self._proxy.mapToSource(idx)
        it  = self._model.item(src.row(), _CH)
        if it: it.setCheckState(Qt.Unchecked if it.checkState()==Qt.Checked else Qt.Checked)
        self._update_cnt()

    def _checked_ids(self) -> set:
        return {self._model.item(r, _CH).data(Qt.UserRole)
                for r in range(self._model.rowCount())
                if self._model.item(r, _CH) and
                   self._model.item(r, _CH).checkState() == Qt.Checked}

    def _sel_all(self):
        for r in range(self._proxy.rowCount()):
            sr = self._proxy.mapToSource(self._proxy.index(r, 0)).row()
            it = self._model.item(sr, _CH)
            if it: it.setCheckState(Qt.Checked)
        self._update_cnt()

    def _desel_all(self):
        for r in range(self._model.rowCount()):
            it = self._model.item(r, _CH)
            if it: it.setCheckState(Qt.Unchecked)
        self._update_cnt()

    def _update_cnt(self):
        n = len(self._checked_ids())
        self._cnt_lbl.setText(
            f"Showing {self._proxy.rowCount():,} of {len(self._motifs):,}  │  <b>{n:,} selected</b>")
        self._imp_btn.setEnabled(n > 0)

    def _do_import(self):
        ids = self._checked_ids()
        self._selected = [m for m in self._motifs if m["motif_id"] in ids]
        if self._selected:
            self.import_requested.emit(self.get_motif_lines(), self.get_append_mode())


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED DIALOG
# ═══════════════════════════════════════════════════════════════════════════════
class TFMotifDialog(QDialog):
    """
    One dialog with two tabs:
      Tab 0 – ⬇  Download from AnimalTFDB server
      Tab 1 – 🔍  Browse & Import
    """

    def __init__(self, parent=None, save_dir: Path = None,
                 meme_path: str = "", annot_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("🐾  AnimalDB – Download & Import TF Motifs")
        self.setMinimumSize(1100, 740)
        self.resize(1160, 790)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self._save_dir = Path(save_dir) if save_dir else Path(".")
        self._result: List[str] = []
        self._append: bool = False
        self._worker = None

        self._build(meme_path, annot_path)

    def get_motif_lines(self) -> List[str]: return self._result
    def get_append_mode(self) -> bool:      return self._append

    def _build(self, meme_path, annot_path):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        banner = QLabel(
            "  🐾  <b>Animal TF Motif Importer</b>  —  "
            "Download TF binding motifs from JASPAR 2024 or HOCOMOCO v11 "
            "(human, mouse, zebrafish, insects, and more), "
            "then filter by species / TF family and import into Cis-GS Step 2."
        )
        banner.setStyleSheet(
            "background:#00695C;color:white;padding:9px;font-size:11px;")
        banner.setWordWrap(True)
        root.addWidget(banner)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab{padding:8px 20px;font-weight:bold;}"
            "QTabBar::tab:selected{background:#00695C;color:white;"
            "border-radius:4px 4px 0 0;}"
        )
        self._tabs = tabs

        # ── TAB 0: Download ───────────────────────────────────────────────
        dl_w = QWidget()
        dl_l = QVBoxLayout(dl_w)
        dl_l.setContentsMargins(16, 14, 16, 14)
        dl_l.setSpacing(10)

        info_lbl = QLabel(
            "Select a dataset below and click <b>Download</b>.\n"
            "JASPAR includes species and TF family metadata fetched automatically\n"
            "from the JASPAR REST API. HOCOMOCO is human or mouse only.\n"
            "After download, use the Species and TF Family filters in Browse & Import."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color:#333; padding:4px;")
        dl_l.addWidget(info_lbl)

        # Dataset selector
        ds_grp = QGroupBox("Select Dataset")
        ds_grp.setStyleSheet("QGroupBox{font-weight:bold;}")
        ds_l = QVBoxLayout(ds_grp)
        self._ds_radios: List[QRadioButton] = []
        self._ds_group  = QButtonGroup(self)

        for i, ds in enumerate(DATASETS):
            rb = QRadioButton(f"{ds['icon']}  {ds['label']}")
            rb.setToolTip(ds["description"])
            if i == 0: rb.setChecked(True)
            self._ds_radios.append(rb)
            self._ds_group.addButton(rb, i)
            ds_l.addWidget(rb)
            note = ds.get("note", ds["description"])
            desc = QLabel(f"      {note}")
            color = "#B71C1C" if note.startswith("⚠") else "#555"
            desc.setStyleSheet(f"color:{color};font-size:10px;")
            ds_l.addWidget(desc)
            if i < len(DATASETS)-1:
                line = QFrame(); line.setFrameShape(QFrame.HLine)
                line.setStyleSheet("color:#ddd;")
                ds_l.addWidget(line)

        dl_l.addWidget(ds_grp)

        # Save dir
        svr = QHBoxLayout()
        svr.addWidget(QLabel("Save to:"))
        self._save_edit = QLineEdit(str(self._save_dir))
        svr.addWidget(self._save_edit, 2)
        bsv = QPushButton("Browse …"); bsv.clicked.connect(self._browse_save)
        svr.addWidget(bsv)
        dl_l.addLayout(svr)

        # Progress
        self._prog = QProgressBar(); self._prog.setRange(0,100)
        self._prog.setVisible(False)
        dl_l.addWidget(self._prog)
        self._dl_lbl = QLabel("")
        self._dl_lbl.setStyleSheet("color:#333;font-style:italic;padding:4px;")
        self._dl_lbl.setWordWrap(True)
        dl_l.addWidget(self._dl_lbl)

        note = QLabel(
            "ℹ️  Files are large (several MB) and cached locally — future loads are instant.\n"
            "ℹ️  JASPAR: jaspar.elixir.no (EMBL-EBI, Europe — very reliable)\n"
            "ℹ️  HOCOMOCO: hocomoco11.autosome.org (Russia/EU — reliable)\n"
            "ℹ️  After first download, files are cached locally for instant reloading."
        )
        note.setStyleSheet("color:#666;font-size:10px;padding:4px;")
        note.setWordWrap(True)
        dl_l.addWidget(note)
        dl_l.addStretch()

        self._dl_btn = QPushButton("  ⬇  Download from Server")
        self._dl_btn.setStyleSheet(
            "background:#00695C;color:white;font-weight:bold;"
            "padding:10px 28px;border-radius:5px;font-size:13px;"
        )
        self._dl_btn.clicked.connect(self._start_download)
        dl_l.addWidget(self._dl_btn)

        tabs.addTab(dl_w, "⬇  Download")

        # ── TAB 1: Browse & Import ─────────────────────────────────────────
        self._browser = AnimalMotifBrowserWidget(save_dir=self._save_dir)
        self._browser.set_files(meme_path, annot_path)
        if meme_path and Path(meme_path).exists():
            self._browser.reload()
        self._browser.import_requested.connect(self._on_import)
        tabs.addTab(self._browser, "🔍  Browse & Import")

        root.addWidget(tabs)
        self._tabs = tabs

    # ── Download ──────────────────────────────────────────────────────────

    def _browse_save(self):
        d = QFileDialog.getExistingDirectory(self, "Save Folder", str(self._save_dir))
        if d: self._save_edit.setText(d)

    def _start_download(self):
        ds_idx = self._ds_group.checkedId()
        if ds_idx < 0:
            QMessageBox.warning(self, "Download", "Please select a dataset."); return
        ds = DATASETS[ds_idx]

        save_dir = Path(self._save_edit.text().strip() or str(self._save_dir))
        self._prog.setVisible(True); self._prog.setValue(0)
        self._dl_btn.setEnabled(False)
        self._dl_lbl.setText(f"Connecting to AnimalTFDB for '{ds['label']}' …")

        self._worker = _DownloadWorker(ds, save_dir)
        self._worker.progress.connect(self._on_prog)
        self._worker.finished.connect(self._on_dl_done)
        self._worker.error.connect(self._on_dl_err)
        self._worker.start()

    def _on_prog(self, pct, msg):
        self._prog.setValue(pct); self._dl_lbl.setText(msg)

    def _on_dl_done(self, meme_path, annot_path):
        self._prog.setValue(100); self._dl_btn.setEnabled(True)
        self._dl_lbl.setText(
            f"✅  Saved: {Path(meme_path).name}"
            + (f"  +  {Path(annot_path).name}" if annot_path else "")
        )
        self._browser.set_files(meme_path, annot_path)
        self._browser.reload()
        self._tabs.setCurrentIndex(1)

    def _on_dl_err(self, msg):
        self._prog.setVisible(False); self._dl_btn.setEnabled(True)
        self._dl_lbl.setText("❌  Download failed.")

        QMessageBox.critical(self, "Download Failed", msg)

    def _show_manual_assistant(self, ds: dict):
        """
        When AnimalTFDB blocks automated download, show a helper dialog that:
          1. Offers to open the browser to the exact download URL
          2. Watches the Downloads folder for the file to appear
          3. Auto-fills Browse & Import when the file is found
        """
        import webbrowser, threading, time
        from pathlib import Path

        download_url = ds["urls"][0]
        save_dir     = Path(self._save_edit.text().strip() or str(self._save_dir))
        local_name   = ds["local_name"]

        dlg = QDialog(self)
        dlg.setWindowTitle("Manual Download Assistant")
        dlg.setMinimumWidth(560)
        lay = QVBoxLayout(dlg)

        lay.addWidget(QLabel(
            "<b>The AnimalTFDB server uses bot-protection that blocks automated downloads.</b><br><br>"
            "Use this assistant to download the file through your browser and auto-import it:<br>"
        ))

        step1 = QLabel(
            "  <b>Step 1.</b>  Click the button below — your browser will open to the download URL.<br>"
            "  The file will download to your browser's default Downloads folder."
        )
        step1.setWordWrap(True)
        lay.addWidget(step1)

        open_btn = QPushButton(f"  🌐  Open Download URL in Browser")
        open_btn.setStyleSheet(
            "background:#1565C0;color:white;font-weight:bold;"
            "padding:7px 16px;border-radius:4px;"
        )
        open_btn.clicked.connect(lambda: webbrowser.open(download_url))
        lay.addWidget(open_btn)

        step2 = QLabel(
            f"  <b>Step 2.</b>  Once downloaded, click the button below to locate the file<br>"
            f"  (<code>{local_name}</code>) and load it automatically."
        )
        step2.setWordWrap(True)
        lay.addWidget(step2)

        browse_btn = QPushButton("  📂  I've Downloaded It — Browse for File")
        browse_btn.setStyleSheet("padding:7px 14px;border-radius:4px;font-weight:bold;")
        lay.addWidget(browse_btn)

        status_lbl = QLabel("")
        status_lbl.setStyleSheet("color:#2E7D32;font-style:italic;padding:4px;")
        lay.addWidget(status_lbl)

        annot_urls = ds.get("annot_urls", [])

        def do_browse():
            p, _ = QFileDialog.getOpenFileName(
                dlg, "Locate the downloaded MEME file", str(Path.home() / "Downloads"),
                "MEME files (*.meme *.txt);;All files (*)"
            )
            if not p:
                return
            dest = save_dir / local_name
            save_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(p, dest)
            status_lbl.setText(f"✅  File copied to workspace: {dest.name}")
            self._browser.set_files(str(dest), "")
            self._browser.reload()
            self._tabs.setCurrentIndex(1)
            self._dl_lbl.setText(f"✅  Loaded from manual download: {dest.name}")
            dlg.accept()

        browse_btn.clicked.connect(do_browse)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.reject)
        lay.addWidget(close_btn)

        dlg.exec_()

    def _on_import(self, lines: List[str], append: bool):
        self._result = lines
        self._append = append
        self.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION  –  called from app_v4.py
# ═══════════════════════════════════════════════════════════════════════════════
def open_animaltfdb_dialog(parent=None, save_dir=None,
                           meme_path: str = "",
                           annot_path: str = "") -> Tuple[List[str], bool]:
    """
    Open the AnimalTFDB combined Download + Import dialog.

    Returns (motif_lines, append_mode).
    motif_lines is [] if the user closed without importing.
    """
    dlg = TFMotifDialog(
        parent=parent,
        save_dir=Path(save_dir) if save_dir else Path("."),
        meme_path=meme_path,
        annot_path=annot_path,
    )
    dlg.exec_()
    return dlg.get_motif_lines(), dlg.get_append_mode()
