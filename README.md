# ModUpdater

Ein modularer **Arma 3 Mod Updater** für **SteamCMD** (Windows Server 2019+), geschrieben in **Python 3.13**.  
Er automatisiert:

- Parsen von Arma3Sync-Repos (`repo.html`)
- Download & Validierung via **SteamCMD**
- Erstellen von **@mod Junctions**
- Aufräumen & Umbenennen
- **Optional**: Kopieren nach einem **Master-Ordner** per `robocopy`  
  - Nur Maps
  - Nur Mods
  - Beide (Maps + Mods)

---

## 🔧 Installation

1. Projekt klonen oder entpacken:
```powershell
git clone https://github.com/sancron/a3-modupdater.git
cd modupdater
```

2. Installation im Entwicklungsmodus:

```powershell
python -m pip install -e .
```

3. Ab jetzt ist `modupdater` als CLI-Befehl verfügbar.

---

## ⚙️ Konfiguration

Die Einstellungen liegen in einer TOML-Datei (`modupdater.toml`).
Beispiel (`C:\Tools\a3-modupdater\modupdater.toml`):

```toml
[steam]
cmd_path = "C:\\Tools\\steamcmd"
exe_name = "steamcmd.exe"
app_id   = "107410"  # Arma 3
login_user = ""      # optional
login_pass = ""      # optional
runscript_path = "C:\\Tools\\steamcmd\\SteamCMD.txt"

[paths]
final_mod_path = "C:\\Arma3Sync\\workshop_download\\final"
repo_html      = "C:\\Arma3Sync\\workshop_download\\repo.html"
mods_txt       = "C:\\Arma3Sync\\workshop_download\\mods.txt"
log_file       = "C:\\Tools\\steamcmd\\arma3_modmanager.log"
master_copy    = "C:\\Arma3Sync\\master"

[behavior]
do_clean = true
do_rename = true
do_symlink = true
do_copy = true
validate = true
dry_run = false

[copy]
# "maps" = nur Karten kopieren (mit Rename-Mapping)
# "mods" = alle Mods kopieren, Maps bleiben unberührt
# "all"  = erst Maps kopieren, dann Mods (Maps bleiben erhalten)
mode = "all"

options = ["/MIR", "/COPYALL", "/R:5", "/W:10"]

# Verzeichnisse, die beim Mods-Kopieren ausgelassen werden
exclude_dirs = ["steamapps", ".a3s"]

# Mapping für Karten (Quelle -> Zielname mit ter_/Suffix)
[copy.map_rename]
"@anizay" = "@ter_anizay_cup"
"@cham" = "@ter_cham_gm"
"@rosche,_germany" = "@ter_rosche_cup"
# ...
```

---

## 🚀 Verwendung

### Komplettlauf (parse → download → clean → link → rename \[+ copy])

```powershell
modupdater all
```

### Nur repo.html auswerten

```powershell
modupdater parse
```

### Mods herunterladen

```powershell
modupdater download
```

### Symbolic-Links (@modname) erstellen

```powershell
modupdater link
```

### Aufräumen (verwaiste Links löschen)

```powershell
modupdater clean
```

### Bestehende @-Ordner slugifizieren/umbenennen

```powershell
modupdater rename
```

### Mit alternativer Config

```powershell
modupdater -c C:\Tools\steamcmd\modupdater_serverB.toml all
```

### Trockenlauf (zeigt nur an, was passieren würde)

```powershell
modupdater --dry-run all
```

---

## 🗂 Copy-Modi (Robocopy)

Wenn `do_copy = true`, wird nach `all` automatisch `robocopy` ausgeführt.
Der Modus wird über `copy.mode` gesteuert:

### 🔹 `maps`

* Kopiert **nur Karten** aus `final/maps/`
* Nutzt das `map_rename`-Mapping, um Zielordnernamen automatisch anzupassen
* Beispiel: `@anizay` → `@ter_anizay_cup`

### 🔹 `mods`

* Kopiert **alle Mods** aus `final/`
* Schließt `exclude_dirs` (z. B. `steamapps`, `.a3s`, Karten-Ziele) aus
* Karten bleiben im Ziel erhalten und werden nicht überschrieben

### 🔹 `all`

* Führt beide Schritte nacheinander aus:

  1. **Maps kopieren** (mit Rename-Mapping)
  2. **Mods kopieren**, Karten bleiben erhalten

---

## 📝 Logging

* Alle Ausgaben erscheinen in der Konsole **und** im Logfile (`arma3_modmanager.log`).
* Logrotation: max. 2 MB pro Datei, bis zu 3 Backups.

---

## ✅ Voraussetzungen

* Windows Server 2019 oder neuer
* Python **3.13**
* SteamCMD installiert (`steamcmd.exe`)
* Optional: `beautifulsoup4` (für robustes HTML-Parsing)

---

## 📦 Entwickler

* Tests (`pytest`) im `tests/` Ordner
* Code-Qualität: `ruff`, `mypy`
* Entwicklermodus starten:

  ```powershell
  pip install -e .[dev]
  ```

---

## 📜 Lizenz


GPLv3
