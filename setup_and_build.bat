@echo off
REM ===========================================================================
REM  Cis-GS Complete Setup & Build Script
REM  Runs the assets check then chains into build_windows.bat to produce the
REM  standalone Cis-GS.exe in the dist/ folder.
REM ===========================================================================

echo.
echo +=========================================================================+
echo ^|            Cis-GS Complete Setup ^& Build Script                         ^|
echo ^|        This will set up everything and build your .exe                  ^|
echo +=========================================================================+
echo.

REM -- Check that the main entry script exists ---------------------------------
if not exist "app_v4_open.py" (
    echo [ERROR] app_v4_open.py not found in current directory!
    echo.
    echo Please ensure these files are all in the same folder:
    echo   1. app_v4_open.py
    echo   2. requirements.txt
    echo   3. Cis-GS.spec
    echo   4. build_windows.bat
    echo   5. This script  (setup_and_build.bat)
    echo.
    pause
    exit /b 1
)

REM -- Create assets folder if missing -----------------------------------------
echo [SETUP] Checking assets folder...
if not exist "assets" (
    echo Assets folder not found. Creating placeholder images...
    python create_assets.py
    if errorlevel 1 (
        echo [WARN] create_assets.py failed; creating empty assets folder.
        mkdir assets
    )
) else (
    echo Assets folder exists.
)
echo.

REM -- Hand off to the main build script ---------------------------------------
echo [BUILD] Starting build process...
echo.
if not exist "build_windows.bat" (
    echo [ERROR] build_windows.bat not found in current directory.
    pause
    exit /b 1
)
call build_windows.bat
