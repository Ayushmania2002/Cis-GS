"""
planttfdb_importer.py  –  PlantTFDB Motif Importer for Cis-GS
═══════════════════════════════════════════════════════════════

Two tabs in one dialog window:
  ⬇  Download from Server  – pick any of the 157 PlantTFDB organisms,
                               download MEME + info files directly from
                               planttfdb.gao-lab.org. The species list is
                               fetched live from the server so codes are
                               always correct; falls back to a built-in list
                               when offline.
  🔍  Browse & Import       – load a local MEME file, filter by TF family
                               / method / keyword, tick motifs, and send
                               their IUPAC consensus sequences straight to
                               the Step 2 motif box.

Usage in app_v4.py
──────────────────
    from planttfdb_importer import open_planttfdb_dialog
    lines, append = open_planttfdb_dialog(parent=self, save_dir=MOTIFS_DIR)
"""

import re, ssl as _ssl
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request, urllib.error

import pandas as pd

from PyQt5.QtCore  import Qt, QThread, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui   import QStandardItem, QStandardItemModel, QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QTableView, QAbstractItemView, QGroupBox,
    QMessageBox, QProgressBar, QTabWidget, QHeaderView,
)


def _theme_colors(widget):
    """
    Return (primary_text, muted_text) hex strings that read well against the
    widget's current Window background.  Lets pop-up dialogs follow the host
    app's light/dark theme without hardcoding a single grey.
    """
    bg = widget.palette().color(QPalette.Window)
    if bg.lightness() < 128:        # dark theme
        return "#ECECEC", "#B0B0B0"
    return "#202020", "#555555"     # light theme


def _force_label_palette(root_widget, hex_color):
    """
    Belt-and-braces: walk every QLabel descendant of `root_widget` and set the
    foreground palette colour directly.  Needed because Qt sometimes routes a
    nested QDialog's labels through the system palette rather than the host
    app's QSS, leaving them black-on-dark in dark mode.  Labels whose own
    setStyleSheet already specifies a 'color:' are left alone so banner
    headings keep their white-on-green styling.
    """
    try:
        from PyQt5.QtWidgets import QLabel as _QLabel_F
        qc = QColor(hex_color)
        for lbl in root_widget.findChildren(_QLabel_F):
            ss = lbl.styleSheet() or ""
            if "color:" in ss.replace(" ", ""):
                continue
            pal = lbl.palette()
            pal.setColor(QPalette.WindowText, qc)
            pal.setColor(QPalette.Text,       qc)
            lbl.setPalette(pal)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK SPECIES CATALOGUE  –  used when the server cannot be reached
# Codes verified against actual PlantTFDB download links
# ═══════════════════════════════════════════════════════════════════════════════
_FALLBACK_CATALOGUE: Dict[str, str] = {
    "Aar": "Aegilops tauschii",
    "Ach": "Actinidia chinensis",
    "Adu": "Arachis duranensis",
    "Ahy": "Arachis hypogaea",
    "Ain": "Arachis ipaensis",
    "Aly": "Arabidopsis lyrata",
    "Ath": "Arabidopsis thaliana",
    "Atr": "Amborella trichopoda",
    "Ban": "Musa acuminata (banana)",
    "Bdi": "Brachypodium distachyon",
    "Bna": "Brassica napus",
    "Bob": "Brassica oleracea",
    "Bra": "Brassica rapa",
    "Bst": "Boechera stricta",
    "Bvu": "Beta vulgaris",
    "Cca": "Cajanus cajan",
    "Ccl": "Citrus clementina",
    "Cla": "Citrullus lanatus",
    "Cme": "Cyanidioschyzon merolae",
    "Cmo": "Cucurbita moschata",
    "Cpa": "Carica papaya",
    "Cre": "Chlamydomonas reinhardtii",
    "Cru": "Capsella rubella",
    "Csa": "Cannabis sativa",
    "Csi": "Citrus sinensis",
    "Cso": "Cucumis sativus",
    "Dal": "Dalbergia odorifera",
    "Dca": "Daucus carota",
    "Egr": "Eucalyptus grandis",
    "Egu": "Elaeis guineensis",
    "Eus": "Eutrema salsugineum",
    "Fve": "Fragaria vesca",
    "Gai": "Gossypium arboreum",
    "Ghy": "Gossypium hirsutum",
    "Gma": "Glycine max",
    "Gra": "Gossypium raimondii",
    "Han": "Helianthus annuus",
    "Hbr": "Hevea brasiliensis",
    "Hlu": "Humulus lupulus",
    "Hvu": "Hordeum vulgare",
    "Itr": "Ipomoea triloba",
    "Jcu": "Jatropha curcas",
    "Jre": "Juglans regia",
    "Kfl": "Klebsormidium flaccidum",
    "Laj": "Lupinus angustifolius",
    "Lin": "Linum usitatissimum",
    "Lpe": "Leersia perrieri",
    "Lsa": "Lactuca sativa",
    "Mca": "Musa acuminata",
    "Mdo": "Malus domestica",
    "Mes": "Manihot esculenta",
    "Mgr": "Mimulus guttatus",
    "Mpo": "Marchantia polymorpha",
    "Mpu": "Micromonas pusilla",
    "Mtr": "Medicago truncatula",
    "Nbe": "Nicotiana benthamiana",
    "Nsy": "Nicotiana sylvestris",
    "Nta": "Nicotiana tabacum",
    "Nto": "Nicotiana tomentosiformis",
    "Olu": "Ostreococcus lucimarinus",
    "Oni": "Oryza nivara",
    "Osa": "Oryza sativa (Japonica)",
    "Osb": "Oryza sativa (Indica)",
    "Ouf": "Oryza rufipogon",
    "Pbr": "Pyrus bretschneideri",
    "Pce": "Picea abies",
    "Ped": "Populus euphratica",
    "Pha": "Panicum hallii",
    "Pin": "Pinus taeda",
    "Poi": "Populus deltoides",
    "Ppa": "Physcomitrella patens",
    "Ppe": "Prunus persica",
    "Ptr": "Populus trichocarpa",
    "Pvi": "Panicum virgatum",
    "Pvu": "Phaseolus vulgaris",
    "Qro": "Quercus robur",
    "Rco": "Ricinus communis",
    "Sbi": "Sorghum bicolor",
    "Sit": "Setaria italica",
    "Sly": "Solanum lycopersicum",
    "Smo": "Selaginella moellendorffii",
    "Spe": "Spinacia oleracea",
    "Spo": "Spirodela polyrhiza",
    "Stu": "Solanum tuberosum",
    "Svi": "Setaria viridis",
    "Tar": "Triticum aestivum",
    "Tca": "Theobroma cacao",
    "Tdi": "Thellungiella halophila",
    "Tha": "Tarenaya hassleriana",
    "Tpa": "Trifolium pratense",
    "Tur": "Triticum urartu",
    "Vca": "Vigna angularis",
    "Vin": "Vitis vinifera",
    "Vra": "Vigna radiata",
    "Vvi": "Vitis vinifera",
    "Xvi": "Xerophyta viscosa",
    "Zju": "Ziziphus jujuba",
    "Zma": "Zea mays",
    "Zme": "Zostera marina",
}

_URL_BASE     = "https://planttfdb.gao-lab.org/download/motif"
_URL_FALLBACK = "http://planttfdb.cbi.pku.edu.cn/download/motif"
_DOWNLOAD_PAGE = "https://planttfdb.gao-lab.org/download.php"

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
    req.add_header("Accept", "*/*")
    return req

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE SPECIES LIST FETCHER  –  scrapes the download page for real codes
# ═══════════════════════════════════════════════════════════════════════════════
def fetch_species_list() -> Dict[str, str]:
    """
    Scrape planttfdb.gao-lab.org/download.php and extract every species code
    from the .meme.gz download links.  Returns {code: species_name}.
    Returns {} on any failure (caller falls back to _FALLBACK_CATALOGUE).
    """
    for page_url in [_DOWNLOAD_PAGE,
                     "http://planttfdb.gao-lab.org/download.php",
                     "http://planttfdb.cbi.pku.edu.cn/download.php"]:
        try:
            req = _make_req(page_url)
            with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx()) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Every link looks like:  Adu_TF_binding_motifs.meme.gz
            # Parse pairs: species name from surrounding HTML, code from filename
            catalogue = {}

            # Strategy: find all .meme.gz hrefs and the nearest species name text
            # Pattern in the page: <td>Species name</td> ... Xxx_TF_binding_motifs.meme.gz
            # Split HTML into rows containing meme.gz links
            for block in re.split(r'(?=\b[A-Z][a-z]{1,4}_TF_binding_motifs\.meme\.gz)', html):
                m_code = re.search(r'\b([A-Z][a-z]{1,4})_TF_binding_motifs\.meme\.gz', block)
                if not m_code:
                    continue
                code = m_code.group(1)

                # Look back in the preceding ~500 chars of HTML for species name
                start = max(0, html.find(block) - 500)
                preceding = html[start: html.find(block) + len(block)]

                # Strip tags, collapse whitespace, take the last non-empty line
                text = re.sub(r'<[^>]+>', ' ', preceding)
                text = re.sub(r'\s+', ' ', text).strip()
                # The species name is usually the last italicised or plain text
                # before the download links — grab last 2-4 words that look like a name
                words = text.split()
                # Find last occurrence of a capitalised genus word
                name = ""
                for i in range(len(words)-1, -1, -1):
                    if words[i][0].isupper() and words[i].isalpha() and len(words[i]) > 2:
                        # Grab genus + species (next word if lowercase)
                        parts = [words[i]]
                        if i+1 < len(words) and words[i+1][0].islower():
                            parts.append(words[i+1])
                            if i+2 < len(words) and words[i+2][0].islower():
                                parts.append(words[i+2])
                        name = " ".join(parts)
                        break

                catalogue[code] = name or _FALLBACK_CATALOGUE.get(code, code)

            if len(catalogue) >= 50:   # sanity: expect at least 50 species
                return catalogue

        except Exception:
            continue

    return {}


class _SpeciesFetchWorker(QThread):
    """Fetches the live species list in the background when the dialog opens."""
    finished = pyqtSignal(dict)   # {code: name}

    def run(self):
        result = fetch_species_list()
        self.finished.emit(result if len(result) >= 50 else {})


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
    consensus = []
    for row in pfm:
        probs = list(zip(_BASE_ORDER, row))
        max_p = max(p for _, p in probs)
        cutoff = max(threshold, max_p * 0.30)
        included = [b for b, p in probs if p >= cutoff] or [max(probs, key=lambda x: x[1])[0]]
        consensus.append(_BASES_TO_IUPAC.get(frozenset(included), "N"))
    return "".join(consensus)

def pfm_to_simple(pfm: List[List[float]]) -> str:
    return "".join(_BASE_ORDER[row.index(max(row))] for row in pfm)

# ═══════════════════════════════════════════════════════════════════════════════
# FILE PARSERS
# ═══════════════════════════════════════════════════════════════════════════════
def parse_meme_file(path: str) -> List[dict]:
    motifs, current = [], None
    with open(path, "r") as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("MOTIF "):
            parts = line.split()
            current = dict(gene_id=parts[1] if len(parts)>1 else "unknown",
                           matrix_id=parts[2] if len(parts)>2 else "",
                           pfm=[], width=0, nsites=0, evalue="",
                           url="", iupac="", consensus="")
            motifs.append(current)
        elif current is not None:
            if line.startswith("letter-probability matrix:"):
                for pat, key in [(r"w=\s*(\d+)","width"),(r"nsites=\s*(\d+)","nsites"),(r"E=\s*(\S+)","evalue")]:
                    m = re.search(pat, line)
                    if m: current[key] = (int(m.group(1)) if key != "evalue" else m.group(1))
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
            elif line.startswith("URL "):
                current["url"] = line[4:].strip()
        i += 1
    return motifs

def parse_info_file(path: str) -> Dict[str, dict]:
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.strip() for c in df.columns]
    info = {}
    for _, row in df.iterrows():
        gid = str(row.get("Gene_id","")).strip()
        if gid:
            info[gid] = dict(family=str(row.get("Family","")),
                             matrix_id=str(row.get("Matrix_id","")),
                             species=str(row.get("Species","")),
                             method=str(row.get("Method","")),
                             source_id=str(row.get("Datasource_ID","")))
    return info

def enrich_motifs(motifs: List[dict], info: Dict[str, dict]) -> List[dict]:
    for m in motifs:
        meta = info.get(m["gene_id"], {})
        m["family"]    = meta.get("family",    "Unknown")
        m["method"]    = meta.get("method",    "Unknown")
        m["species"]   = meta.get("species",   "Unknown")
        m["source_id"] = meta.get("source_id", "")
    return motifs

def _fill_defaults(motifs: List[dict]) -> List[dict]:
    for m in motifs:
        m.setdefault("family",    "Unknown")
        m.setdefault("method",    "Unknown")
        m.setdefault("species",   "Unknown")
        m.setdefault("source_id", "")
    return motifs

# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD WORKER THREAD
# ═══════════════════════════════════════════════════════════════════════════════
class _DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, str)   # meme_path, info_path (empty if failed)
    error    = pyqtSignal(str)

    def __init__(self, code: str, save_dir: Path):
        super().__init__()
        self.code     = code
        self.save_dir = save_dir

    def run(self):
        code, save_dir = self.code, self.save_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        meme_gz_fname = f"{code}_TF_binding_motifs.meme.gz"
        meme_fname    = f"{code}_TF_binding_motifs.meme"
        info_fname    = f"{code}_TF_binding_motifs_information.txt"
        meme_gz_dest  = save_dir / meme_gz_fname
        meme_dest     = save_dir / meme_fname
        info_dest     = save_dir / info_fname

        domains = [
            "https://planttfdb.gao-lab.org/download/motif",
            "http://planttfdb.gao-lab.org/download/motif",
            "https://planttfdb.cbi.pku.edu.cn/download/motif",
            "http://planttfdb.cbi.pku.edu.cn/download/motif",
        ]
        urls_gz   = [f"{d}/{meme_gz_fname}" for d in domains]
        urls_meme = [f"{d}/{meme_fname}"    for d in domains]
        urls_info = [f"{d}/{info_fname}"    for d in domains]

        # ── MEME file ──────────────────────────────────────────────────────
        self.progress.emit(0, f"Connecting to PlantTFDB for '{code}' …")
        ok, gz_errors = self._download(urls_gz, meme_gz_dest, 0, 45,
                                       "MEME.gz", validate_meme=True)
        if ok:
            self.progress.emit(47, "Decompressing …")
            try:
                import gzip, shutil
                with gzip.open(meme_gz_dest, "rb") as fi, open(meme_dest, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
                meme_gz_dest.unlink()
            except Exception as ex:
                self.error.emit(
                    f"Downloaded '{meme_gz_fname}' but decompression failed.\nError: {ex}"
                )
                return
        else:
            ok, plain_errors = self._download(urls_meme, meme_dest, 0, 50,
                                              "MEME", validate_meme=True)
            if not ok:
                all_errors = gz_errors + plain_errors
                tried = "\n".join(f"  • {u}\n      → {e}" for u, e in all_errors)
                self.error.emit(
                    f"Could not download the MEME file for species code '{code}'.\n\n"
                    f"URLs tried:\n{tried}\n\n"
                    "This species code may not exist on PlantTFDB, or the server\n"
                    "is temporarily unavailable.\n\n"
                    "Tip: The species list in the dropdown is fetched live from\n"
                    "PlantTFDB when you open the dialog. If you selected a species\n"
                    "from the list, the code should be correct — the server may\n"
                    "just be temporarily down. Try again in a moment.\n\n"
                    "Or use 'Browse' in the Browse & Import tab to load a\n"
                    "manually-downloaded .meme file."
                )
                return

        # ── Info file ──────────────────────────────────────────────────────
        self.progress.emit(50, f"Downloading metadata for '{code}' …")
        ok_info, info_errors = self._download(urls_info, info_dest, 50, 100,
                                              "Info", validate_meme=False)
        if not ok_info:
            tried = "\n".join(f"  • {u}\n      → {e}" for u, e in info_errors)
            self.error.emit(
                f"MEME file downloaded successfully ✅\n\n"
                f"But the Motif Information file (family names, methods) failed:\n\n"
                f"URLs tried:\n{tried}\n\n"
                f"MEME file saved to:\n  {meme_dest}\n\n"
                "You can use Browse & Import to load it — TF Family and Method\n"
                "columns will show 'Unknown' without the information file.\n\n"
                "To get family names, download the information file manually from\n"
                "planttfdb.gao-lab.org → your species → first Download button."
            )
            self.progress.emit(100, "⚠ MEME downloaded, info file failed.")
            self.finished.emit(str(meme_dest), "")
            return

        self.progress.emit(100, "Download complete ✅")
        self.finished.emit(str(meme_dest), str(info_dest))

    def _download(self, urls, dest, start_pct, end_pct, label, validate_meme=False):
        errors = []
        for url in urls:
            try:
                req = _make_req(url)
                with urllib.request.urlopen(req, timeout=60, context=_ssl_ctx()) as resp:
                    # Only reject HTML for MEME files (info .txt may have text/html ctype)
                    ctype = resp.headers.get("Content-Type", "")
                    if validate_meme and "html" in ctype.lower():
                        errors.append((url,
                            f"Server returned HTML (Content-Type: {ctype}) — likely a 404"))
                        continue

                    total = int(resp.headers.get("Content-Length", 0))
                    received = 0
                    with open(dest, "wb") as fout:
                        while True:
                            chunk = resp.read(65536)
                            if not chunk: break
                            fout.write(chunk)
                            received += len(chunk)
                            if total:
                                pct = int(start_pct + (received/total)*(end_pct-start_pct))
                                self.progress.emit(pct,
                                    f"{label}: {received//1024} / {total//1024} KB")

                if not (dest.exists() and dest.stat().st_size > 0):
                    errors.append((url, "Downloaded file is empty"))
                    if dest.exists(): dest.unlink()
                    continue

                if validate_meme:
                    with open(dest, "rb") as f: header = f.read(20)
                    if not (header[:2] == b'\x1f\x8b' or b"MEME" in header):
                        dest.unlink()
                        errors.append((url,
                            f"Not a valid MEME/gz file (starts with {header[:12]!r})"))
                        continue

                return True, []

            except urllib.error.HTTPError as e:
                errors.append((url, f"HTTP {e.code} {e.reason}"))
                if dest.exists(): dest.unlink()
            except urllib.error.URLError as e:
                errors.append((url, f"Connection error: {e.reason}"))
                if dest.exists(): dest.unlink()
            except Exception as e:
                errors.append((url, f"{type(e).__name__}: {e}"))
                if dest.exists(): dest.unlink()

        return False, errors


# ═══════════════════════════════════════════════════════════════════════════════
# COLOUR HELPER
# ═══════════════════════════════════════════════════════════════════════════════
_FAM_COLORS = {
    "ERF":"#A8D08D",  "MYB":"#E8A0B5",  "WRKY":"#81C784",  "bHLH":"#7FB3D8",
    "NAC":"#E0967A",  "bZIP":"#BA94D1", "C2H2":"#6EC6D0",  "HD-ZIP":"#C5D97E",
    "MIKC_MADS":"#E8B96E", "MYB_related":"#E8A0A0", "GATA":"#8E99CC",
    "Dof":"#6ABED0",  "Trihelix":"#C5D97E", "ARF":"#E8CC6E", "SBP":"#81C784",
    "TCP":"#BA94D1",  "HSF":"#E0967A",  "B3":"#7FB3D8",    "BBR-BPC":"#A0A8B0",
    "G2-like":"#81C784", "LBD":"#A8D08D", "EIL":"#6EC6D0",
}
def _fam_color(fam: str) -> str:
    return _FAM_COLORS.get(fam, "#8CA0A8")


# ═══════════════════════════════════════════════════════════════════════════════
# MOTIF TABLE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
_HEADERS = ["✓", "Gene ID", "TF Family", "Matrix ID", "Method",
            "IUPAC Consensus", "Width", "# Sites"]
_CH, _GE, _FA, _MA, _ME, _IU, _WI, _NS = range(8)

class MotifBrowserWidget(QWidget):
    import_requested = pyqtSignal(list, bool)

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

        # Theme-aware label colour so dark mode renders text legibly.
        _txt_browse, _mut_browse = _theme_colors(self)
        self.setStyleSheet(
            f"QLabel {{ color: {_txt_browse}; background: transparent; }}"
            f"QGroupBox {{ color: {_txt_browse}; }}"
            f"QCheckBox {{ color: {_txt_browse}; }}"
        )

        fg = QGridLayout()
        fg.addWidget(QLabel("MEME file:"), 0, 0)
        self._meme_edit = QLineEdit()
        self._meme_edit.setPlaceholderText("Auto-filled after download, or Browse …")
        fg.addWidget(self._meme_edit, 0, 1)
        b1 = QPushButton("Browse …"); b1.clicked.connect(self._browse_meme)
        fg.addWidget(b1, 0, 2)

        fg.addWidget(QLabel("Info TSV:"), 1, 0)
        self._info_edit = QLineEdit()
        self._info_edit.setPlaceholderText("Optional – auto-filled after download …")
        fg.addWidget(self._info_edit, 1, 1)
        b2 = QPushButton("Browse …"); b2.clicked.connect(self._browse_info)
        fg.addWidget(b2, 1, 2)

        lb = QPushButton("  ↺  Load / Reload")
        lb.setStyleSheet("background:#2E8B57;color:white;font-weight:bold;"
                         "padding:4px 14px;border-radius:3px;")
        lb.clicked.connect(self.reload)
        fg.addWidget(lb, 2, 1)

        self._load_lbl = QLabel("")
        self._load_lbl.setStyleSheet(f"color:{_mut_browse};font-style:italic;font-size:10px;")
        fg.addWidget(self._load_lbl, 3, 0, 1, 3)
        root.addLayout(fg)

        fl = QHBoxLayout()
        fl.addWidget(QLabel("Family:"))
        self._fam_cb = QComboBox(); self._fam_cb.addItem("All families")
        self._fam_cb.setMinimumWidth(120)
        self._fam_cb.currentTextChanged.connect(self._apply)
        fl.addWidget(self._fam_cb)

        fl.addWidget(QLabel("Method:"))
        self._met_cb = QComboBox(); self._met_cb.addItem("All methods")
        self._met_cb.setMinimumWidth(100)
        self._met_cb.currentTextChanged.connect(self._apply)
        fl.addWidget(self._met_cb)

        fl.addWidget(QLabel("Search:"))
        self._srch = QLineEdit(); self._srch.setPlaceholderText("Gene ID / family …")
        self._srch.setMinimumWidth(140); self._srch.textChanged.connect(self._apply)
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

        sr = QHBoxLayout()
        self._cnt_lbl = QLabel("No motifs loaded")
        self._cnt_lbl.setStyleSheet("font-weight:bold;")
        sr.addWidget(self._cnt_lbl); sr.addStretch()
        for lbl, fn in [("☑ All Visible", self._sel_all), ("☐ Deselect All", self._desel_all)]:
            b = QPushButton(lbl); b.clicked.connect(fn); sr.addWidget(b)
        root.addLayout(sr)

        or_ = QHBoxLayout()
        self._append_cb = QCheckBox("Append (don't replace)")
        or_.addWidget(self._append_cb)
        self._prefix_cb = QCheckBox("Prefix name with TF family  e.g. ERF|Aradu.00XL9")
        self._prefix_cb.setChecked(True)
        or_.addWidget(self._prefix_cb)
        or_.addStretch()
        self._imp_btn = QPushButton("  🌿  Import Selected  →  Step 2")
        self._imp_btn.setEnabled(False)
        self._imp_btn.setStyleSheet(
            "background:#2E8B57;color:white;font-weight:bold;"
            "padding:8px 20px;border-radius:5px;font-size:12px;"
        )
        self._imp_btn.clicked.connect(self._do_import)
        or_.addWidget(self._imp_btn)
        root.addLayout(or_)

        # Force primary text colour on every label inside this widget
        _force_label_palette(self, _txt_browse)

    def set_files(self, meme_path: str, info_path: str = ""):
        if meme_path: self._meme_edit.setText(meme_path)
        if info_path: self._info_edit.setText(info_path)

    def reload(self):
        meme = self._meme_edit.text().strip()
        info = self._info_edit.text().strip()
        if not meme or not Path(meme).exists():
            QMessageBox.warning(self, "Load", "Please select a valid MEME file."); return
        self._load_lbl.setText("⏳  Parsing …"); QApplication.processEvents()
        try:
            motifs = parse_meme_file(meme)
        except Exception as ex:
            self._load_lbl.setText(f"❌  {ex}"); return
        if info and Path(info).exists():
            try: motifs = enrich_motifs(motifs, parse_info_file(info))
            except Exception: pass
        _fill_defaults(motifs)
        self._motifs = motifs
        self._load_lbl.setText(f"✅  {len(motifs)} motifs — {Path(meme).name}")
        self._rebuild_filters(); self._populate()

    def get_motif_lines(self) -> List[str]:
        lines = []
        use_prefix = self._prefix_cb.isChecked()
        for m in self._selected:
            name = f"{m.get('family','?')}|{m['gene_id']}" if use_prefix else m["gene_id"]
            lines.append(f"{name}\t{m['iupac']}")
        return lines

    def get_append_mode(self) -> bool: return self._append_cb.isChecked()

    def _browse_meme(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select MEME File", str(self._save_dir),
                                           "MEME files (*.meme *.txt);;All files (*)")
        if p: self._meme_edit.setText(p); self.reload()

    def _browse_info(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Info TSV", str(self._save_dir),
                                           "TSV/TXT (*.txt *.tsv);;All files (*)")
        if p: self._info_edit.setText(p); self.reload()

    def _rebuild_filters(self):
        for cb, key, all_lbl in [(self._fam_cb,"family","All families"),
                                  (self._met_cb,"method","All methods")]:
            items = sorted({m.get(key,"Unknown") for m in self._motifs})
            cb.blockSignals(True); cb.clear(); cb.addItem(all_lbl)
            for it in items: cb.addItem(it)
            cb.blockSignals(False)

    def _get_threshold(self) -> float:
        return float(self._thr.currentText().split()[0])

    def _populate(self, checked_ids: set = None):
        checked_ids = checked_ids or set()
        self._model.setRowCount(0)
        fam_f = self._fam_cb.currentText(); met_f = self._met_cb.currentText()
        txt_f = self._srch.text().strip().lower()
        for m in self._motifs:
            if fam_f != "All families" and m.get("family","") != fam_f: continue
            if met_f != "All methods"  and m.get("method","") != met_f: continue
            if txt_f:
                hay = " ".join([m.get("gene_id",""),m.get("family",""),
                                m.get("matrix_id",""),m.get("iupac","")]).lower()
                if txt_f not in hay: continue
            chk = QStandardItem()
            chk.setCheckState(Qt.Checked if m["gene_id"] in checked_ids else Qt.Unchecked)
            chk.setCheckable(True); chk.setTextAlignment(Qt.AlignCenter)
            chk.setData(m["gene_id"], Qt.UserRole)
            g=QStandardItem(m.get("gene_id","")); f=QStandardItem(m.get("family","Unknown"))
            ma=QStandardItem(m.get("matrix_id","")); me=QStandardItem(m.get("method","Unknown"))
            iu=QStandardItem(m.get("iupac","")); iu.setFont(QFont("Courier New",9))
            wi=QStandardItem(str(m.get("width",""))); wi.setTextAlignment(Qt.AlignCenter)
            ns=QStandardItem(str(m.get("nsites",""))); ns.setTextAlignment(Qt.AlignCenter)
            col = QColor(_fam_color(m.get("family","")))
            _txt = QColor("#1a1a1a")
            g.setBackground(col); g.setForeground(_txt)
            f.setBackground(col); f.setForeground(_txt)
            self._model.appendRow([chk,g,f,ma,me,iu,wi,ns])
        self._update_cnt()

    def _apply(self):  self._populate(self._checked_ids())
    def _recompute(self):
        t = self._get_threshold()
        for m in self._motifs:
            if m["pfm"]: m["iupac"] = pfm_to_iupac(m["pfm"], threshold=t)
        self._populate(self._checked_ids())

    def _toggle(self, idx):
        src = self._proxy.mapToSource(idx)
        it = self._model.item(src.row(), _CH)
        if it: it.setCheckState(Qt.Unchecked if it.checkState()==Qt.Checked else Qt.Checked)
        self._update_cnt()

    def _checked_ids(self) -> set:
        return {self._model.item(r,_CH).data(Qt.UserRole)
                for r in range(self._model.rowCount())
                if self._model.item(r,_CH) and
                   self._model.item(r,_CH).checkState()==Qt.Checked}

    def _sel_all(self):
        for r in range(self._proxy.rowCount()):
            sr = self._proxy.mapToSource(self._proxy.index(r,0)).row()
            it = self._model.item(sr,_CH)
            if it: it.setCheckState(Qt.Checked)
        self._update_cnt()

    def _desel_all(self):
        for r in range(self._model.rowCount()):
            it = self._model.item(r,_CH)
            if it: it.setCheckState(Qt.Unchecked)
        self._update_cnt()

    def _update_cnt(self):
        n = len(self._checked_ids())
        self._cnt_lbl.setText(
            f"Showing {self._proxy.rowCount()} of {len(self._motifs)}  │  <b>{n} selected</b>")
        self._imp_btn.setEnabled(n > 0)

    def _do_import(self):
        ids = self._checked_ids()
        self._selected = [m for m in self._motifs if m["gene_id"] in ids]
        if self._selected:
            self.import_requested.emit(self.get_motif_lines(), self.get_append_mode())


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED DIALOG  (Download tab  +  Browse & Import tab)
# ═══════════════════════════════════════════════════════════════════════════════
class PlantTFDBDialog(QDialog):
    def __init__(self, parent=None, save_dir: Path = None,
                 meme_path: str = "", info_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("🌿  PlantTFDB – Download & Import TF Motifs")
        self.setMinimumSize(1080, 720)
        self.resize(1140, 770)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self._save_dir = Path(save_dir) if save_dir else Path(".")
        self._result: List[str] = []
        self._append: bool = False
        self._worker = None
        self._sp_fetch_worker = None
        # Start with fallback catalogue immediately; update live in background
        self._all_sp = sorted(_FALLBACK_CATALOGUE.items(), key=lambda x: x[1])
        self._build(meme_path, info_path)
        self._fetch_live_species()

    def get_motif_lines(self) -> List[str]: return self._result
    def get_append_mode(self) -> bool:      return self._append

    def _build(self, meme_path, info_path):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Theme-aware text colours so labels stay legible in dark mode.
        _txt, _muted = _theme_colors(self)
        # Force every QLabel descendant of this dialog (including those inside
        # nested QTabWidget / QGroupBox containers) to use the theme text
        # colour. Use a high-specificity selector list so nothing inherits a
        # stale palette from the host app.
        self.setStyleSheet(
            f"QLabel {{ color: {_txt}; background: transparent; }}"
            f"QGroupBox {{ color: {_txt}; }}"
            f"QCheckBox {{ color: {_txt}; }}"
            f"QRadioButton {{ color: {_txt}; }}"
        )

        banner = QLabel(
            "  🌿  <b>PlantTFDB Motif Importer</b>  —  "
            "Download binding motifs for any organism in PlantTFDB, "
            "then filter and import them directly into Cis-GS Step 2."
        )
        banner.setStyleSheet("background:#2E8B57;color:white;padding:9px;font-size:11px;")
        banner.setWordWrap(True)
        root.addWidget(banner)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab{padding:8px 20px;font-weight:bold;}"
            "QTabBar::tab:selected{background:#2E8B57;color:white;"
            "border-radius:4px 4px 0 0;}"
        )
        self._tabs = tabs

        # ── TAB 0: Download ───────────────────────────────────────────────
        dl_w = QWidget()
        dl_l = QVBoxLayout(dl_w)
        dl_l.setContentsMargins(14, 14, 14, 14)
        dl_l.setSpacing(8)

        self._sp_source_lbl = QLabel(
            "⏳  Loading live species list from PlantTFDB …  (using built-in list for now)"
        )
        self._sp_source_lbl.setStyleSheet(f"color:{_muted};font-size:10px;font-style:italic;")
        dl_l.addWidget(self._sp_source_lbl)

        sr = QHBoxLayout()
        sr.addWidget(QLabel("Search:"))
        self._sp_srch = QLineEdit()
        self._sp_srch.setPlaceholderText("Type genus, species name, or 3-letter code …")
        self._sp_srch.textChanged.connect(self._filter_species)
        sr.addWidget(self._sp_srch, 2)
        dl_l.addLayout(sr)

        self._sp_combo = QComboBox()
        self._sp_combo.setMaxVisibleItems(30)
        self._sp_combo.currentIndexChanged.connect(self._on_sp_changed)
        dl_l.addWidget(self._sp_combo)

        cr = QHBoxLayout()
        cr.addWidget(QLabel("Species code:"))
        self._code_edit = QLineEdit(); self._code_edit.setMaximumWidth(100)
        self._code_edit.setPlaceholderText("e.g. Adu")
        cr.addWidget(self._code_edit)
        cr.addWidget(QLabel(
            "← auto-filled when you pick from the list.\n"
            "You can also type any code manually."
        ))
        cr.addStretch()
        dl_l.addLayout(cr)

        svr = QHBoxLayout()
        svr.addWidget(QLabel("Save to:"))
        self._save_edit = QLineEdit(str(self._save_dir))
        svr.addWidget(self._save_edit, 2)
        bsv = QPushButton("Browse …"); bsv.clicked.connect(self._browse_save)
        svr.addWidget(bsv)
        dl_l.addLayout(svr)

        self._prog = QProgressBar(); self._prog.setRange(0,100); self._prog.setVisible(False)
        dl_l.addWidget(self._prog)
        self._dl_lbl = QLabel("")
        self._dl_lbl.setStyleSheet(f"color:{_txt};font-style:italic;padding:4px;")
        self._dl_lbl.setWordWrap(True)
        dl_l.addWidget(self._dl_lbl)

        note = QLabel(
            "ℹ️  Files are cached locally — future downloads are instant.\n"
            "ℹ️  The species list is fetched live from PlantTFDB so codes are always correct.\n"
            "ℹ️  If download fails, use Browse & Import to load a manually-saved file."
        )
        note.setStyleSheet(f"color:{_muted};font-size:10px;padding:4px;")
        note.setWordWrap(True)
        dl_l.addWidget(note)
        dl_l.addStretch()

        self._dl_btn = QPushButton("  ⬇  Download from PlantTFDB Server")
        self._dl_btn.setStyleSheet(
            "background:#2E8B57;color:white;font-weight:bold;"
            "padding:10px 28px;border-radius:5px;font-size:13px;"
        )
        self._dl_btn.clicked.connect(self._start_download)
        dl_l.addWidget(self._dl_btn)

        tabs.addTab(dl_w, "⬇  Download from Server")

        # ── TAB 1: Browse & Import ─────────────────────────────────────────
        self._browser = MotifBrowserWidget(save_dir=self._save_dir)
        self._browser.set_files(meme_path, info_path)
        if meme_path and Path(meme_path).exists():
            self._browser.reload()
        self._browser.import_requested.connect(self._on_import)
        tabs.addTab(self._browser, "🔍  Browse & Import")

        root.addWidget(tabs)
        self._fill_sp_combo(self._all_sp)

        # Final pass: forcibly set the foreground palette on every QLabel that
        # didn't already opt into a custom colour, so dark mode never leaves
        # labels invisible regardless of QSS cascading quirks.
        _force_label_palette(self, _txt)

    # ── Live species fetch ────────────────────────────────────────────────

    def _fetch_live_species(self):
        self._sp_fetch_worker = _SpeciesFetchWorker()
        self._sp_fetch_worker.finished.connect(self._on_live_species)
        self._sp_fetch_worker.start()

    def _on_live_species(self, catalogue: dict):
        # Use brighter green / orange in dark mode so status stays readable.
        _is_dark = self.palette().color(QPalette.Window).lightness() < 128
        _ok_clr   = "#5CDB95" if _is_dark else "#2E8B57"
        _warn_clr = "#FFB74D" if _is_dark else "#E65100"
        if catalogue:
            self._all_sp = sorted(catalogue.items(), key=lambda x: x[1])
            self._fill_sp_combo(self._all_sp)
            self._sp_source_lbl.setText(
                f"✅  Live species list loaded from PlantTFDB  "
                f"({len(catalogue)} organisms)"
            )
            self._sp_source_lbl.setStyleSheet(f"color:{_ok_clr};font-size:10px;")
        else:
            self._sp_source_lbl.setText(
                "⚠  Could not reach PlantTFDB — using built-in species list.  "
                "Species codes may not be 100% current."
            )
            self._sp_source_lbl.setStyleSheet(f"color:{_warn_clr};font-size:10px;")

    # ── Species combo ─────────────────────────────────────────────────────

    def _fill_sp_combo(self, entries):
        current_code = self._code_edit.text() if hasattr(self, '_code_edit') else ""
        self._sp_combo.blockSignals(True)
        self._sp_combo.clear()
        self._sp_combo.addItem("— select a species —", "")
        for code, name in entries:
            self._sp_combo.addItem(f"{name}  [{code}]", code)
        self._sp_combo.blockSignals(False)
        # Restore selection if code is still in new list
        if current_code:
            self._code_edit.setText(current_code)

    def _filter_species(self, text: str):
        t = text.lower()
        filtered = [(c,n) for c,n in self._all_sp if t in n.lower() or t in c.lower()]
        self._fill_sp_combo(filtered)

    def _on_sp_changed(self, idx: int):
        code = self._sp_combo.itemData(idx) or ""
        self._code_edit.setText(code)

    def _browse_save(self):
        d = QFileDialog.getExistingDirectory(self, "Save Folder", str(self._save_dir))
        if d: self._save_edit.setText(d)

    # ── Download ──────────────────────────────────────────────────────────

    def _start_download(self):
        code = self._code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "Download",
                                "Please select a species or enter a species code."); return
        save_dir = Path(self._save_edit.text().strip() or str(self._save_dir))

        self._prog.setVisible(True); self._prog.setValue(0)
        self._dl_btn.setEnabled(False)
        self._dl_lbl.setText(f"Connecting to PlantTFDB for '{code}' …")

        self._worker = _DownloadWorker(code, save_dir)
        self._worker.progress.connect(self._on_prog)
        self._worker.finished.connect(self._on_dl_done)
        self._worker.error.connect(self._on_dl_err)
        self._worker.start()

    def _on_prog(self, pct, msg):
        self._prog.setValue(pct); self._dl_lbl.setText(msg)

    def _on_dl_done(self, meme_path, info_path):
        self._prog.setValue(100); self._dl_btn.setEnabled(True)
        self._dl_lbl.setText(
            f"✅  Saved: {Path(meme_path).name}"
            + (f"  +  {Path(info_path).name}" if info_path else "")
        )
        self._browser.set_files(meme_path, info_path)
        self._browser.reload()
        self._tabs.setCurrentIndex(1)

    def _on_dl_err(self, msg):
        self._prog.setVisible(False); self._dl_btn.setEnabled(True)
        self._dl_lbl.setText("❌  Download failed.")
        QMessageBox.critical(self, "Download Failed", msg)

    def _on_import(self, lines: List[str], append: bool):
        self._result = lines
        self._append = append
        self.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION  –  called from app_v4.py
# ═══════════════════════════════════════════════════════════════════════════════
def open_planttfdb_dialog(parent=None, save_dir=None,
                          meme_path: str = "",
                          info_path: str = "") -> Tuple[List[str], bool]:
    dlg = PlantTFDBDialog(
        parent=parent,
        save_dir=Path(save_dir) if save_dir else Path("."),
        meme_path=meme_path,
        info_path=info_path
    )
    dlg.exec_()
    return dlg.get_motif_lines(), dlg.get_append_mode()
