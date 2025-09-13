import subprocess
import shutil
from pathlib import Path
from .utils import slugify, is_windows


def workshop_mod_path(cfg, mod_id: str) -> Path:
    return cfg.paths.final_mod_path / "steamapps" / "workshop" / "content" / cfg.steam.app_id / mod_id


def junction_create(target: Path, link_dir: Path, logger, dry_run=False):
    if not is_windows():
        raise RuntimeError("Nur unter Windows unterstützt")
    if link_dir.exists():
        return
    if dry_run:
        logger.info(f"[dry-run] mklink /J \"{link_dir}\" \"{target}\"")
        return
    cmd = f'mklink /J "{link_dir}" "{target}"'
    logger.info(f"Erzeuge Junction: {cmd}")
    subprocess.run(cmd, shell=True, check=False)


def safe_clean_final(cfg, logger):
    """
    Entfernt alte/verwaiste Ordner im final_mod_path.
    - Nutzt Flags aus cfg.behavior (dry_run, do_clean).
    """
    base = cfg.paths.final_mod_path
    if not base.exists():
        return

    dry_run = cfg.behavior.dry_run
    aggressive = cfg.behavior.do_clean

    for entry in base.iterdir():
        if entry.name.lower() == "steamapps":
            continue
        if aggressive:
            if dry_run:
                logger.info(f"[dry-run] Entferne {entry}")
            else:
                if entry.is_dir():
                    _win_rmdir(entry)
                else:
                    entry.unlink(missing_ok=True)
        elif entry.is_dir() and entry.name.startswith("@"):
            try:
                _ = list(entry.iterdir())
            except Exception:
                logger.info(f"Verwaist: {entry}")
                if dry_run:
                    logger.info(f"[dry-run] rmdir /s /q \"{entry}\"")
                else:
                    _win_rmdir(entry)


def _win_rmdir(path: Path):
    if not is_windows():
        shutil.rmtree(path, ignore_errors=True)
    else:
        subprocess.run(f'rmdir /s /q "{path}"', shell=True)


def rename_at_folders(cfg, logger):
    """
    Benennt @-Ordner konsistent um, basierend auf slugify.
    Nutzt cfg.behavior.dry_run.
    """
    base = cfg.paths.final_mod_path
    if not base.exists():
        return

    dry_run = cfg.behavior.dry_run

    for entry in base.iterdir():
        if not entry.is_dir() or entry.name.lower() == "steamapps":
            continue
        if entry.name.startswith("@"):
            original = entry.name[1:]
            target_name = f"@{slugify(original)}"
            target = base / target_name
            if entry.name != target_name and not target.exists():
                logger.info(f"Rename {entry.name} -> {target_name}")
                if not dry_run:
                    entry.rename(target)
