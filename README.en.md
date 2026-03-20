# ModUpdater (English)

ModUpdater automates Arma 3 workshop management on Windows (SteamCMD + Arma3Sync).

- Parse Arma3Sync repos (`repo.html`)
- Download + optional validation via SteamCMD
- Create junctions (`@mod` folders)
- Cleanup + rename existing folders
- Optional: mirror everything into a "master" folder via Robocopy (maps / mods / both)

---

## 🔧 Installation

```powershell
git clone https://github.com/deinuser/modupdater.git
cd modupdater
pip install -e .
```

Python >= 3.13 on Windows Server 2019+ is recommended. `beautifulsoup4` is optional but improves HTML parsing.

---

## ⚙️ Configuration

All settings live in a TOML file (default `C:\Tools\steamcmd\modupdater.toml`).
Use the bundled `modupdater.example.toml` (German) or `modupdater.example.en.toml` (English) as a template:

1. Copy the desired example file to `modupdater.toml`.
2. Adjust SteamCMD paths, Arma3Sync paths, behavior flags, and copy settings.

> 👉 Windows paths can be entered with single backslashes (`C:\Tools\steamcmd`).
> The loader auto-escapes them if needed.

### Global defaults

If several servers share the same `copy.exclude_dirs` or `[copy.map_rename]`, create a `modupdater.global.toml` next to the binary (`modupdater.exe`, `modupdater.pyz`).
Any value missing in the local config falls back to the global file.

---

## 🚀 Usage

```powershell
modupdater all          # parse -> download -> clean -> link -> rename -> (copy)
modupdater parse        # only update mods.txt from repo.html
modupdater download     # run SteamCMD only
modupdater link         # create @junctions (uses mods.txt)
modupdater clean        # remove orphaned @folders
modupdater rename       # slugify existing @folders
modupdater copy         # run Robocopy step only (requires behavior.do_copy=true)
modupdater -c custom.toml all           # alternate config
modupdater --global-config shared.toml  # alternate global defaults
modupdater --dry-run all                # print actions only
```

---

## 🗂 Copy modes

`behavior.do_copy=true` enables the Robocopy step after `all` or on demand via `modupdater copy`:

- `maps`: copy only mapped entries from `[copy.map_rename]`
- `mods`: mirror everything from `paths.final_mod_path` and skip `exclude_dirs`
- `all`: run `mods` first, then `maps` to preserve renamed folders

The Robocopy options default to `[/MIR, /COPYALL, /R:5, /W:10]` but can be overridden.

---

## 🧱 Packaging

Two distributable formats are available:

### PyInstaller (`dist\modupdater`)

```powershell
pwsh -File .\scripts\build_exe.ps1
```

Outputs `dist\modupdater\modupdater.exe`, `_internal`, and both `README` + `modupdater.*.toml` templates.
`modupdater.global.toml` and `modupdater.example*.toml` remain editable next to the EXE.

### Shiv Zipapp (`dist\modupdater.pyz`)

```powershell
pwsh -File .\scripts\build_pyz.ps1
python .\dist\modupdater.pyz all
```

The script stages dependencies locally, creates `dist\modupdater.pyz`, and copies the same README/template files beside it.
The runtime looks for `modupdater.global.toml` in the same directory as the `.pyz` unless `--global-config` is provided.

---

## 📝 Logging

Logs go to both stdout and `paths.log_file`. Rotation: 2 MB, 3 backups.

---

## ✅ Requirements

- Windows Server 2019+
- Python 3.13+
- SteamCMD (`steamcmd.exe`)
- Optional: `beautifulsoup4`

---

## 👨‍💻 Development

```powershell
pip install -e .[dev]
pytest
```

Static checks via `ruff`, `mypy` (included in `[dev]`). Feel free to adapt the templates for additional environments.
