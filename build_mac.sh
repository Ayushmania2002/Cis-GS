#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  Cis-GS  —  macOS Build Script
#  Produces:  dist/Cis-GS.app  (double-clickable macOS app bundle)
#  Run this ON a Mac.
#  Tested on: macOS 12 Monterey, 13 Ventura, 14 Sonoma  (Intel + Apple Silicon)
# ═══════════════════════════════════════════════════════════════════════════
set -e

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN} ✓${NC}  $1"; }
err()  { echo -e "${RED} ✗  ERROR: $1${NC}"; exit 1; }
warn() { echo -e "${YELLOW} ⚠  $1${NC}"; }
hdr()  { echo -e "\n${GREEN}[$1]${NC} $2"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║      Cis-GS  |  macOS Build  |  Plant Signaling Lab             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Sanity checks ───────────────────────────────────────────────────────
hdr "1/8" "Checking requirements..."

command -v python3 >/dev/null 2>&1 || err "python3 not found. Install from https://www.python.org/downloads/ or via Homebrew: brew install python"
PYVER=$(python3 --version)
ok "$PYVER found"

[[ -f "app_v4.py" ]]         || err "app_v4.py not found. Run this script from the project folder."
[[ -f "Cis-GS.spec" ]]       || err "Cis-GS.spec not found."
[[ -f "requirements.txt" ]]  || err "requirements.txt not found."
ok "All required files present"

# Check Homebrew (optional but recommended for dependencies)
if command -v brew >/dev/null 2>&1; then
    ok "Homebrew found"
else
    warn "Homebrew not found. Some dependencies may fail. Install from https://brew.sh"
fi

# ── 2. Assets ──────────────────────────────────────────────────────────────
hdr "2/8" "Checking assets..."
if [[ ! -d "assets" ]]; then
    warn "assets/ folder missing — generating placeholders..."
    python3 create_assets.py || { mkdir -p assets; warn "create_assets.py failed, created empty assets/"; }
else
    ok "assets/ folder found"
fi

# Convert favicon.png → favicon.icns (macOS needs .icns for proper app icon)
if [[ -f "assets/favicon.png" ]] && [[ ! -f "assets/favicon.icns" ]]; then
    hdr "2b/8" "Converting favicon.png → favicon.icns..."
    ICONSET="assets/favicon.iconset"
    mkdir -p "$ICONSET"
    for SIZE in 16 32 64 128 256 512; do
        sips -z $SIZE $SIZE assets/favicon.png --out "${ICONSET}/icon_${SIZE}x${SIZE}.png" 2>/dev/null
        sips -z $((SIZE*2)) $((SIZE*2)) assets/favicon.png --out "${ICONSET}/icon_${SIZE}x${SIZE}@2x.png" 2>/dev/null
    done
    iconutil -c icns "$ICONSET" -o assets/favicon.icns 2>/dev/null && \
        ok "favicon.icns created" || warn "iconutil failed — app will use default icon"
    rm -rf "$ICONSET"
fi

# ── 3. Virtual environment ─────────────────────────────────────────────────
hdr "3/8" "Setting up virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi
source venv/bin/activate

# ── 4. Dependencies ────────────────────────────────────────────────────────
hdr "4/8" "Installing dependencies..."
pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q || err "pip install failed. Check requirements.txt and your internet connection."
ok "Dependencies installed"

# ── 5. Clean old builds ────────────────────────────────────────────────────
hdr "5/8" "Cleaning old builds..."
rm -rf build dist __pycache__ *.pyc
ok "Cleaned"

# ── 6. Build ───────────────────────────────────────────────────────────────
hdr "6/8" "Building app bundle (3-8 minutes)..."
echo ""
pyinstaller --clean --noconfirm Cis-GS.spec
echo ""

# ── 7. Fix macOS permissions / quarantine ─────────────────────────────────
hdr "7/8" "Fixing macOS permissions..."
if [[ -d "dist/Cis-GS.app" ]]; then
    # Remove quarantine flag (prevents "damaged app" error on first run)
    xattr -cr dist/Cis-GS.app 2>/dev/null || true
    chmod -R 755 dist/Cis-GS.app
    ok "Permissions fixed"
fi

# ── 8. Result ──────────────────────────────────────────────────────────────
hdr "8/8" "Checking result..."
if [[ -d "dist/Cis-GS.app" ]]; then
    SIZE=$(du -sh dist/Cis-GS.app | cut -f1)
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                  BUILD SUCCESSFUL  ✓                            ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    ok "App bundle: dist/Cis-GS.app  (${SIZE})"
    echo ""
    echo "  What to do next:"
    echo "   1.  Test:       open dist/Cis-GS.app"
    echo "                   OR double-click it in Finder"
    echo "   2.  Distribute: drag Cis-GS.app to a DMG or zip it:"
    echo "                   zip -r Cis-GS-macOS.zip dist/Cis-GS.app"
    echo ""
    echo "  ⚠  If macOS says 'cannot be opened because the developer cannot"
    echo "     be verified', right-click the app → Open → Open anyway."
    echo "     (This happens because the app is not signed with an Apple"
    echo "     Developer certificate. Safe to ignore for lab/internal use.)"
    echo ""
else
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗"
    echo -e "║                    BUILD FAILED  ✗                              ║"
    echo -e "╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Troubleshooting:"
    echo "   1. Edit Cis-GS.spec → set console=True → rebuild to see errors."
    echo "   2. Check: build/Cis-GS/warn-Cis-GS.txt"
    echo "   3. Try: pip install --upgrade pyinstaller"
    echo ""
    deactivate
    exit 1
fi

deactivate
