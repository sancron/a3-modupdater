# modupdater/robocopy.py
import subprocess
from pathlib import Path
from collections.abc import Iterable
from .config import Config
from .utils import slugify


def run_copy(cfg: Config, logger):
    """
    Kopiert Dateien per Robocopy entsprechend copy.mode:
      - "maps": nur die Map-Mappings aus [copy.map_rename]
      - "mods": kompletter final_mod_path (mit Excludes)
      - "all" : erst mods, DANN maps (wichtig! So bleiben @ter_* erhalten)
    Ziel ist immer paths.master_copy. Optionen kommen aus copy.options.
    """
    dest_path = cfg.paths.master_copy
    dest_path.mkdir(parents=True, exist_ok=True)

    # robocopy-Log neben deinem normalen Log
    log_path = Path(str(cfg.paths.log_file) + ".robocopy.log")

    mode = (cfg.copy.mode or "mods").lower()

    if mode == "maps":
        _copy_maps(cfg, dest_path, log_path, logger)
    elif mode == "mods":
        _copy_mods(cfg, dest_path, log_path, logger)
    elif mode == "all":
        # WICHTIG: Erst Mods spiegeln, danach Maps gezielt kopieren.
        _copy_mods(cfg, dest_path, log_path, logger)
        _copy_maps(cfg, dest_path, log_path, logger)
    else:
        logger.error(f"Unbekannter Copy-Modus: {mode}")


def _robocopy(cfg: Config, src: Path, dst: Path, log_path: Path,
              exclude_dirs: list[Path], logger):
    """
    Startet Robocopy mit deinen Optionen + optionalen /XD-Ausschlüssen (Quelle).
    """
    args = [
        "robocopy",
        str(src),
        str(dst),
        *cfg.copy.options,
        f"/LOG+:{log_path}",
    ]

    # /XD: Verzeichnisse in der QUELLE ausschließen
    for ex in exclude_dirs:
        args.extend(["/XD", str(ex)])

    logger.info(f"Starte Robocopy: {' '.join(args)}")
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdout:
        for line in proc.stdout:
            line = line.strip()
            if line:
                logger.info(line)
    proc.wait()

    code = proc.returncode or 0
    logger.info(f"Protokolldatei: {log_path}")
    if code <= 3:
        logger.info(f"Robocopy abgeschlossen (ExitCode={code})")
    else:
        logger.error(f"Robocopy fehlgeschlagen (ExitCode={code})")


def _copy_maps(cfg: Config, dest_path: Path, log_path: Path, logger):
    """
    Kopiert die in [copy.map_rename] definierten Maps:
      Quelle:  @<slugified(map_key)> in final_mod_path
      Ziel:    map_rename[map_key] im master
    """
    src_base = cfg.paths.final_mod_path
    mapping = cfg.copy.map_rename or {}

    for raw_src_name, dst_name in mapping.items():
        # Key aus TOML robust sluggifizieren (führt auch ' & - etc. zusammen)
        src_folder = f"@{slugify(raw_src_name.lstrip('@'))}"
        src = src_base / src_folder
        if not src.exists():
            logger.warning(f"Überspringe Map (nicht gefunden): {src}")
            continue

        dst = dest_path / dst_name
        # Für den gezielten Map-Kopiervorgang KEINE Excludes nötig
        _robocopy(cfg, src, dst, log_path, [], logger)


def _copy_mods(cfg: Config, dest_path: Path, log_path: Path, logger):
    """
    Spiegelt den gesamten final_mod_path nach master_copy,
    schließt dabei aber 'steamapps' + optional definierte Ordner aus.
    WICHTIG: Wir führen diesen Schritt bei mode=all VOR _copy_maps aus.
    """
    src = cfg.paths.final_mod_path

    # Basis-Excludes in der QUELLE
    exclude_src: list[Path] = [
        src / "steamapps",
    ]

    # Benutzerdefinierte Excludes (wenn sie im SOURCE-Baum existieren)
    for name in (cfg.copy.exclude_dirs or []):
        # Excludes können relative Namen sein — wir interpretieren sie als
        # Ordner unterhalb von "src". Existieren sie nicht, stört es nicht.
        exclude_src.append(src / name)

    # Optional: Map-Quellen von der Mods-Spiegelung ausschließen,
    # damit während /MIR keine Map-Ordner im Ziel beeinflusst werden.
    # (Ist bei Reihenfolge "mods dann maps" nicht zwingend, aber sicher.)
    for raw_src_name in (cfg.copy.map_rename or {}).keys():
        map_src_folder = f"@{slugify(raw_src_name.lstrip('@'))}"
        exclude_src.append(src / map_src_folder)

    _robocopy(cfg, src, dest_path, log_path, _unique_paths(exclude_src), logger)


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen = set()
    unique: list[Path] = []
    for item in paths:
        key = str(item).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
