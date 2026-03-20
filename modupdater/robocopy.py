# modupdater/robocopy.py
import shutil
import subprocess
import uuid
from pathlib import Path, PureWindowsPath
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
    respektiert dabei aber Excludes sowohl in der Quelle als auch im Ziel.

    Damit Robocopy /MIR keine geschützten Zielordner löscht, werden diese
    vorübergehend weg-verschoben und danach wieder hergestellt.
    """
    src = cfg.paths.final_mod_path

    protected_rel = _collect_relative_excludes(cfg)
    source_excludes = _build_source_excludes(cfg, src, protected_rel)

    backup_root, protected_handles = _protect_destination(dest_path, protected_rel, logger)
    try:
        _robocopy(cfg, src, dest_path, log_path, source_excludes, logger)
    finally:
        _restore_protected(backup_root, protected_handles, logger)


def _collect_relative_excludes(cfg: Config) -> list[Path]:
    candidates: list[Path] = []

    rel = _normalize_relative("steamapps")
    if rel:
        candidates.append(rel)

    for name in (cfg.copy.exclude_dirs or []):
        rel = _normalize_relative(name)
        if rel:
            candidates.append(rel)

    for dst_name in (cfg.copy.map_rename or {}).values():
        rel = _normalize_relative(dst_name)
        if rel:
            candidates.append(rel)

    return _dedupe_relatives(candidates)


def _build_source_excludes(cfg: Config, src_root: Path, rel_excludes: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for rel in rel_excludes:
        paths.append(src_root / rel)

    for raw_src_name in (cfg.copy.map_rename or {}).keys():
        map_src_folder = f"@{slugify(raw_src_name.lstrip('@'))}"
        paths.append(src_root / map_src_folder)

    return _unique_paths(paths)


def _normalize_relative(value) -> Path | None:
    if value is None:
        return None
    raw = str(value).strip().replace("/", "\\")
    if not raw:
        return None

    candidate = PureWindowsPath(raw)
    parts = list(candidate.parts)
    if candidate.is_absolute() and parts:
        parts = parts[1:]
    parts = [part for part in parts if part not in ("", ".")]
    if not parts:
        return None
    rel = Path(parts[0])
    for part in parts[1:]:
        rel /= part
    return rel


def _dedupe_relatives(rel_paths: Iterable[Path]) -> list[Path]:
    cleaned: list[Path] = []
    for path in rel_paths:
        if not path:
            continue
        normalized = Path(*[p for p in path.parts if p not in ("", ".")])
        if not normalized.parts:
            continue
        cleaned.append(normalized)

    cleaned.sort(key=lambda p: (len(p.parts), tuple(part.lower() for part in p.parts)))
    deduped: list[Path] = []
    seen: list[tuple[str, ...]] = []
    for rel in cleaned:
        key = tuple(part.lower() for part in rel.parts)
        if any(key[: len(existing)] == existing for existing in seen):
            continue
        deduped.append(rel)
        seen.append(key)
    return deduped


def _protect_destination(dest_root: Path, rel_paths: list[Path], logger):
    renames: list[tuple[Path, Path]] = []
    backup_root: Path | None = None
    for rel in sorted(rel_paths, key=lambda p: len(p.parts), reverse=True):
        target = dest_root / rel
        if not target.exists() or not target.is_dir():
            continue

        if backup_root is None:
            backup_root = _create_backup_root(dest_root)
        backup_target = backup_root / rel
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        try:
            logger.info(f"Schütze Ordner vor Robocopy: {target}")
            target.rename(backup_target)
            renames.append((backup_target, target))
        except OSError as exc:
            logger.error(f"Konnte {target} nicht sichern: {exc}")
    return backup_root, renames


def _create_backup_root(dest_root: Path) -> Path:
    parent = dest_root.parent if dest_root.parent != dest_root else dest_root
    base = parent / ".modupdater_protected"
    base.mkdir(parents=True, exist_ok=True)
    run_root = base / f"run_{uuid.uuid4().hex}"
    run_root.mkdir(parents=True, exist_ok=True)
    return run_root


def _restore_protected(backup_root: Path | None, renames: list[tuple[Path, Path]], logger):
    if backup_root is None:
        return
    for backup, target in reversed(renames):
        try:
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            backup.rename(target)
            logger.info(f"Wiederhergestellt: {target}")
        except OSError as exc:
            logger.error(f"Konnte {target} nicht wiederherstellen: {exc}")
    shutil.rmtree(backup_root, ignore_errors=True)
    base = backup_root.parent
    try:
        base.rmdir()
    except OSError:
        pass


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
