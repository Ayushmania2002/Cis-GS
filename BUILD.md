# Building Cis-GS

Three ways to get a working Cis-GS on a fresh machine:

1. **`pip install cis-gs`** — easiest, cross-platform, requires Python 3.9+
2. **Standalone `Cis-GS.exe`** — Windows, no Python required (build with PyInstaller)
3. **From source** — for development

---

## 1. Install from PyPI (recommended for end users)

```bash
pip install cis-gs
cis-gs --help          # CLI entry point
cis-gs-gui             # launches the PyQt5 GUI
```

That's it. Works on Windows, macOS, and Linux.

---

## 2. Build the standalone Windows executable

Requires Python 3.9+ and the dev requirements installed.

```bat
:: Clone the repo
git clone https://github.com/Ayushmania2002/Cis-GS.git
cd Cis-GS

:: One-shot build (creates a virtual env, installs deps, runs PyInstaller)
setup_and_build.bat
```

The finished binary appears at `dist\Cis-GS.exe`. Double-click to launch.

### What `setup_and_build.bat` does

1. Verifies `app_v4_open.py` is present.
2. Creates `assets/` folder if missing (runs `create_assets.py` for placeholder logos).
3. Calls `build_windows.bat`, which:
   - Creates / activates `venv\`
   - `pip install -r requirements.txt` + `pyinstaller`
   - Runs `pyinstaller Cis-GS.spec`
   - Outputs `dist/Cis-GS.exe` (single-file, ~120 MB)

### Manual PyInstaller invocation

```bash
pip install -r requirements.txt pyinstaller
pyinstaller Cis-GS.spec
```

### Building on macOS / Linux

```bash
bash build_mac.sh        # produces Cis-GS.app
bash build_linux.sh      # produces a single-file executable
```

---

## 3. Develop from source

```bash
git clone https://github.com/Ayushmania2002/Cis-GS.git
cd Cis-GS
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev]"           # editable install + dev extras
```

Run the GUI:
```bash
python app_v4_open.py
```

Run the CLI:
```bash
python -m cis_gs --help
```

---

## 4. Publishing a new release to PyPI

Maintainers only. Requires a PyPI API token.

```bash
# 1) Bump the version in pyproject.toml
# 2) Build sdist + wheel
python -m build

# 3) Smoke-test on TestPyPI first
twine upload --repository testpypi dist/*

# 4) Real upload
twine upload dist/*
```

A GitHub Actions workflow (`.github/workflows/publish.yml`) does this automatically when you push a tag like `v1.2.0`.

---

## 5. Building the documentation locally

```bash
pip install -r docs/requirements.txt
cd docs
make html                # → docs/_build/html/index.html
```

The same docs are auto-deployed to GitHub Pages on every push to `main`
(see `.github/workflows/docs.yml`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python` not recognised | Python not on `PATH` | Re-install Python with "Add to PATH" checked |
| PyInstaller `MODULE NOT FOUND` | Missing hidden import | Add the module to `hiddenimports` in `Cis-GS.spec` |
| `.exe` is 0 bytes / crashes on start | Antivirus quarantine | Whitelist `dist\Cis-GS.exe` |
| `qt.qpa.plugin: Could not load Qt platform plugin "windows"` | Missing PyQt5 platform DLLs | Re-build after `pip install --force-reinstall PyQt5` |
| GUI launches but icons missing | `assets/` folder not bundled | Re-run `python create_assets.py` then rebuild |
| NCBI downloads fail | No email set | Set one in **Settings → Set NCBI Email** |
