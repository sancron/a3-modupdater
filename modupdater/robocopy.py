import subprocess
from pathlib import Path
from .config import Config
from .utils import slugify


def run_copy(cfg: Config, logger):
    """Führt Robocopy-Kopiervorgänge aus, je nach copy.mode (maps|mods|all)."""

    mode = cfg.copy.mode
    dest_path = cfg.paths.master_copy
    log_path = Path(str(cfg.paths.log_file) + ".robocopy.log")

    if not mode:
        logger.info("Kein Copy-Modus gesetzt, überspringe Copy-Schritt.")
        return

    dest_path.mkdir(parents=True, exist_ok=True)

    if mode == "maps":
        _copy_maps(cfg, dest_path, log_path, logger)
    elif mode == "mods":
        _copy_mods(cfg, dest_path, log_path, logger)
    elif mode == "all":
        _copy_maps(cfg, dest_path, log_path, logger)
        _copy_mods(cfg, dest_path, log_path, logger)
    else:
        logger.error(f"Unbekannter Copy-Modus: {mode}")


def _robocopy(src: Path, dst: Path, log_path: Path, options: list[str], exclude: list[str], logger):
    args = ["robocopy", str(src), str(dst)] + options + [f"/LOG+:{log_path}"]

    for ex in exclude:
        args.extend(["/XD", str(ex)])

    logger.info(f"Starte Robocopy: {' '.join(args)}")
    result = subprocess.run(args, capture_output=True, text=True)
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.stderr:
        logger.error(result.stderr.strip())

    code = result.returncode
    if code <= 3:
        logger.info(f"Robocopy abgeschlossen (ExitCode={code})")
    else:
        logger.error(f"Robocopy fehlgeschlagen (ExitCode={code})")


def _copy_maps(cfg: Config, dest_path: Path, log_path: Path, logger):
    src = cfg.paths.final_mod_path
    rename_map = cfg.copy.map_rename

    for raw_src_name, dst_name in rename_map.items():
        # Slugify auf den Key anwenden (gleiche Logik wie bei rename)
        src_name = f"@{slugify(raw_src_name.lstrip('@'))}"
        src_dir = src / src_name
        if not src_dir.exists():
            logger.warning(f"Überspringe Map (nicht gefunden): {src_dir}")
            continue
        dst_dir = dest_path / dst_name
        _robocopy(src_dir, dst_dir, log_path, cfg.copy.options, [], logger)


def _copy_mods(cfg: Config, dest_path: Path, log_path: Path, logger):
    src = cfg.paths.final_mod_path
    exclude = cfg.copy.exclude_dirs
    _robocopy(src, dest_path, log_path, cfg.copy.options, exclude, logger)
