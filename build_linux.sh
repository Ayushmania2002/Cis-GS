#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  Cis-GS  —  Linux Build Script
#  Produces:  dist/Cis-GS  (standalone binary, no Python needed on target)
#  Run this ON a Linux machine.
#  Tested on: Ubuntu 20.04+, Debian 11+, Fedora 36+
# ═══════════════════════════════════════════════════════════════════════════
set -e

# ── Colours ────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN} ✓${NC}  $1"; }
err()  { echo -e "${RED} ✗  ERROR: $1${NC}"; exit 1; }
warn() { echo -e "${YELLOW} ⚠  $1${NC}"; }
hdr()  { echo -e "\n${GREEN}[$1]${NC} $2"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║      Cis-GS  |  Linux Build  |  Plant Signaling Lab             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Sanity checks ───────────────────────────────────────────────────────
hdr "1/7" "Checking requirements..."

command -v python3 >/dev/null 2>&1 || err "python3 not found. Install with: sudo apt install python3 python3-venv python3-pip"
PYVER=$(python3 --version)
ok "$PYVER found"

[[ -f "app_v4.py" ]]    || err "app_v4.py not found. Run this script from the project folder."
[[ -f "Cis-GS.spec" ]]  || err "Cis-GS.spec not found."
[[ -f "requirements.txt" ]] || err "requirements.txt not found."

# Check for Qt dependencies on Linux
echo "  Checking system Qt libraries..."
if ! python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    warn "PyQt5 system libs may be missing. Installing prerequisites..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y python3-pyqt5 libxcb-xinerama0 libxcb-icccm4 \
             libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
             libxkbcommon-x11-0 libegl1 2>/dev/null || true
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-qt5 xcb-util-wm xcb-util-image \
             xcb-util-keysyms xcb-util-renderutil libxkbcommon-x11 2>/dev/null || true
    fi
fi
ok "System checks done"

# ── 2. Assets ──────────────────────────────────────────────────────────────
hdr "2/7" "Checking assets..."
if [[ ! -d "assets" ]]; then
    warn "assets/ folder missing — generating placeholders..."
    python3 create_assets.py || { mkdir -p assets; warn "create_assets.py failed, created empty assets/"; }
else
    ok "assets/ folder found"
fi

# ── 3. Virtual environment ─────────────────────────────────────────────────
hdr "3/7" "Setting up virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi
source venv/bin/activate

# ── 4. Dependencies ────────────────────────────────────────────────────────
hdr "4/7" "Installing dependencies..."
pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q || err "pip install failed. Check your internet connection and requirements.txt"
ok "Dependencies installed"

# ── 5. Clean old builds ────────────────────────────────────────────────────
hdr "5/7" "Cleaning old builds..."
rm -rf build dist __pycache__ *.pyc
ok "Cleaned"

# ── 6. Build ───────────────────────────────────────────────────────────────
hdr "6/7" "Building binary (3-8 minutes)..."
echo ""
pyinstaller --clean --noconfirm Cis-GS.spec
echo ""

# ── 7. Result ──────────────────────────────────────────────────────────────
hdr "7/7" "Checking result..."
if [[ -f "dist/Cis-GS" ]]; then
    chmod +x dist/Cis-GS
    SIZE=$(du -sh dist/Cis-GS | cut -f1)
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                  BUILD SUCCESSFUL  ✓                            ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    ok "Executable: dist/Cis-GS  (${SIZE})"
    echo ""
    echo "  What to do next:"
    echo "   1.  Test:       ./dist/Cis-GS"
    echo "   2.  Distribute: share the single binary file — no Python needed!"
    echo "   3.  Package:    tar -czf Cis-GS-linux.tar.gz dist/Cis-GS"
    echo ""
    echo "  Note for users: they may need to run  chmod +x Cis-GS  once."
    echo ""
else
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║                    BUILD FAILED  ✗                              ║"
    echo -e "╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Troubleshooting:"
    echo "   1. Edit Cis-GS.spec, set console=True, then rebuild to see errors."
    echo "   2. Check: build/Cis-GS/warn-Cis-GS.txt"
    echo "   3. On display-less servers, try: export DISPLAY=:0 before running."
    echo ""
    deactivate
    exit 1
fi

deactivate
