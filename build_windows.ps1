# ═══════════════════════════════════════════════════════════════════════════
# Cis-GS Application Builder (PowerShell)
# Alternative to the .bat file for PowerShell users
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                   Cis-GS Application Builder                          ║" -ForegroundColor Cyan
Write-Host "║                         PowerShell Edition                            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python ──────────────────────────────────────────────────
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# ── Step 2: Create virtual environment ────────────────────────────────────
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# ── Step 3: Install dependencies ──────────────────────────────────────────
Write-Host "[3/6] Installing dependencies..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# ── Step 4: Clean old builds ──────────────────────────────────────────────
Write-Host "[4/6] Cleaning old builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
Write-Host "✓ Old builds cleaned" -ForegroundColor Green
Write-Host ""

# ── Step 5: Build executable ──────────────────────────────────────────────
Write-Host "[5/6] Building executable..." -ForegroundColor Yellow
Write-Host "This may take 3-5 minutes. Please wait..." -ForegroundColor Cyan
$buildStart = Get-Date
pyinstaller --clean --noconfirm Cis-GS.spec
$buildEnd = Get-Date
$buildTime = ($buildEnd - $buildStart).TotalSeconds
Write-Host ""

# ── Step 6: Check result ──────────────────────────────────────────────────
Write-Host "[6/6] Checking build result..." -ForegroundColor Yellow
if (Test-Path "dist\Cis-GS.exe") {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                        BUILD SUCCESSFUL! ✓                            ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build completed in: $([math]::Round($buildTime, 1)) seconds" -ForegroundColor Cyan
    Write-Host ""
    
    $exeSize = (Get-Item "dist\Cis-GS.exe").Length / 1MB
    Write-Host "Executable location: dist\Cis-GS.exe" -ForegroundColor White
    Write-Host "File size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Test: dist\Cis-GS.exe" -ForegroundColor White
    Write-Host "  2. Distribute the .exe file (fully portable!)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                         BUILD FAILED ✗                                ║" -ForegroundColor Red
    Write-Host "╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Missing dependencies: Run 'pip install -r requirements.txt'" -ForegroundColor White
    Write-Host "  - Assets folder missing: Ensure assets\ folder exists" -ForegroundColor White
    Write-Host "  - Check build\Cis-GS\warn-Cis-GS.txt for warnings" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
