@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  Cis-GS  —  Windows Build Script
REM  Produces:  dist\Cis-GS.exe  (standalone, no Python needed on target)
REM  Run this ON a Windows machine.
REM ═══════════════════════════════════════════════════════════════════════════
setlocal EnableDelayedExpansion

echo.
echo ╔═══════════════════════════════════════════════════════════════════════╗
echo ║          Cis-GS  ^|  Windows Build  ^|  Plant Signaling Lab            ║
echo ╚═══════════════════════════════════════════════════════════════════════╝
echo.

REM ── 0. Sanity checks ──────────────────────────────────────────────────────
echo [1/7] Checking requirements...

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found in PATH.
    echo  Install Python 3.8+ from https://www.python.org/downloads/
    echo  During install, tick "Add Python to PATH".
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python !PYVER! found.

if not exist "app_v4_open.py" (
    echo  ERROR: app_v4_open.py not found in this folder.
    echo  Put all project files in the same folder as this script.
    pause & exit /b 1
)
if not exist "Cis-GS.spec" (
    echo  ERROR: Cis-GS.spec not found.
    pause & exit /b 1
)
echo  All required files present.
echo.

REM ── 1. Assets ─────────────────────────────────────────────────────────────
echo [2/7] Checking assets...
if not exist "assets" (
    echo  assets\ folder missing - generating placeholders...
    python create_assets.py
    if errorlevel 1 (
        echo  WARNING: create_assets.py failed. Creating empty assets folder.
        mkdir assets
    )
) else (
    echo  assets\ folder found.
)

REM Convert favicon.png to favicon.ico if Pillow is available and .ico missing
if exist "assets\favicon.png" (
    if not exist "assets\favicon.ico" (
        echo  Converting favicon.png to favicon.ico...
        python -c "from PIL import Image; img=Image.open('assets/favicon.png'); img.save('assets/favicon.ico', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])" 2>nul
        if exist "assets\favicon.ico" (echo  favicon.ico created.) else (echo  Skipped .ico conversion ^(Pillow may not be installed yet^).)
    )
)
echo.

REM ── 2. Detect usable Python environment ───────────────────────────────────
echo [3/7] Detecting Python environment...

REM Check if system Python already has all key packages (fast path - skip venv)
python -c "import PyQt5, pandas, scipy, networkx, Bio, PyInstaller" >nul 2>&1
if not errorlevel 1 (
    echo  System Python has all packages. Using system Python directly.
    set USE_SYSTEM_PYTHON=1
    goto :DEPS_DONE
)

set USE_SYSTEM_PYTHON=0
echo  Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo  Virtual environment created.
) else (
    echo  Virtual environment already exists.
)
call venv\Scripts\activate.bat

REM ── 3. Dependencies ───────────────────────────────────────────────────────
echo [4/7] Installing / updating dependencies...
python -m pip install --upgrade pip setuptools wheel --quiet

REM First try binary-only (fast, no compiler needed) ─────────────────────────
echo  Trying binary-only install (no compiler required)...
pip install -r requirements.txt --only-binary :all: --quiet 2>nul
if not errorlevel 1 (
    echo  Binary install succeeded.
    goto :DEPS_DONE
)

REM Fall back to allowing source builds ─────────────────────────────────────
echo  Binary install incomplete, retrying with source allowed...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo  Dependency install failed in venv. Trying system Python instead...
    deactivate
    set USE_SYSTEM_PYTHON=1
)

:DEPS_DONE
REM Favicon conversion now that Pillow is definitely installed
if exist "assets\favicon.png" (
    if not exist "assets\favicon.ico" (
        python -c "from PIL import Image; img=Image.open('assets/favicon.png'); img.save('assets/favicon.ico', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])" 2>nul
    )
)
echo  Dependencies ready.
echo.

REM ── 4. Clean old builds ───────────────────────────────────────────────────
echo [5/7] Cleaning old builds...
if exist "build"       rmdir /s /q "build"
if exist "dist"        rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo  Cleaned.
echo.

REM ── 5. Build ──────────────────────────────────────────────────────────────
echo [6/7] Building executable (this takes 3-8 minutes)...
echo.

REM Locate pyinstaller - prefer venv, fall back to system
if "%USE_SYSTEM_PYTHON%"=="1" (
    REM Use system PyInstaller (install it if missing)
    python -m pip install pyinstaller --quiet 2>nul
    python -m PyInstaller --clean --noconfirm Cis-GS.spec
) else (
    pyinstaller --clean --noconfirm Cis-GS.spec
)
echo.

REM ── 6. Result ─────────────────────────────────────────────────────────────
echo [7/7] Checking result...
if exist "dist\Cis-GS.exe" (
    for %%A in ("dist\Cis-GS.exe") do set SIZE=%%~zA
    set /a SIZEMB=!SIZE! / 1048576
    echo.
    echo ╔═══════════════════════════════════════════════════════════════════════╗
    echo ║                    BUILD SUCCESSFUL  ✓                                ║
    echo ╚═══════════════════════════════════════════════════════════════════════╝
    echo.
    echo   Executable : dist\Cis-GS.exe
    echo   Size       : ~!SIZEMB! MB
    echo.
    echo  What to do next:
    echo   1.  Test:      double-click dist\Cis-GS.exe
    echo   2.  Distribute: share the single .exe file - no Python needed!
    echo   3.  Optional:  zip it for easier sharing
    echo.
) else (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════════════╗
    echo ║                       BUILD FAILED  ✗                                 ║
    echo ╚═══════════════════════════════════════════════════════════════════════╝
    echo.
    echo  Troubleshooting:
    echo   1. Edit Cis-GS.spec and set console=True, then rebuild to see errors.
    echo   2. Run: pip install -r requirements.txt  manually to see what fails.
    echo   3. Check PyInstaller logs in build\Cis-GS\warn-Cis-GS.txt
    echo   4. Try: python -m pip install pyinstaller then python -m PyInstaller Cis-GS.spec
    echo.
)

REM ── 7. Clear Windows icon cache so Explorer shows new icon ───────────────
if exist "dist\Cis-GS.exe" (
    echo  Refreshing Windows icon cache...
    ie4uinit.exe -show >nul 2>&1
    REM Delete the icon cache DB so Explorer rebuilds it on next launch
    del /f /q "%localappdata%\IconCache.db" >nul 2>&1
    del /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*.db" >nul 2>&1
    REM Touch the exe so Explorer notices the file changed
    copy /b "dist\Cis-GS.exe" +,, >nul 2>&1
    echo  Icon cache cleared. Right-click the .exe and choose Refresh if icon still shows old.
)

if "%USE_SYSTEM_PYTHON%"=="0" deactivate
echo Press any key to close...
pause >nul
