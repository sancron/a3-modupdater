from __future__ import annotations
from .config import Config
from .parser_html import parse_repo_html, write_mods_txt
from .steamcmd import build_steamcmd_commands, run_steamcmd
from .linkmanager import junction_create, safe_clean_final, rename_at_folders, workshop_mod_path
from .utils import read_text, slugify
from . import robocopy


def run_parse(cfg: Config, logger):
    html = read_text(cfg.paths.repo_html)
    mods = parse_repo_html(html, logger)
    write_mods_txt(mods, cfg.paths.mods_txt, logger)
    logger.info(f"{len(mods)} Mods in {cfg.paths.mods_txt} gespeichert")
    return mods


def run_download(cfg: Config, logger, mods=None):
    if mods is None:
        text = read_text(cfg.paths.mods_txt)
        mods = [line.split(",", 1) for line in text.splitlines() if line.strip()]

    commands = build_steamcmd_commands(cfg, mods)
    run_steamcmd(cfg, commands, logger)


def run_clean(cfg: Config, logger):
    safe_clean_final(cfg, logger)


def run_link(cfg: Config, logger, mods=None):
    if mods is None:
        text = read_text(cfg.paths.mods_txt)
        mods = [line.split(",", 1) for line in text.splitlines() if line.strip()]

    for mod_id, mod_name in mods:
        normalized = slugify(mod_name)
        target = workshop_mod_path(cfg, mod_id)
        link_dir = cfg.paths.final_mod_path / f"@{normalized}"
        junction_create(target, link_dir, logger, cfg.behavior.dry_run)


def run_rename(cfg: Config, logger):
    rename_at_folders(cfg, logger)


def run_copy_step(cfg: Config, logger):
    if cfg.behavior.do_copy:
        robocopy.run_copy(cfg, logger)


def run_workflow(cfg: Config, steps: list[str], logger):
    steps_map = {
        "parse": lambda: run_parse(cfg, logger),
        "download": lambda: run_download(cfg, logger),
        "clean": lambda: run_clean(cfg, logger),
        "link": lambda: run_link(cfg, logger),
        "rename": lambda: run_rename(cfg, logger),
        "copy": lambda: run_copy_step(cfg, logger),
    }

    # Dynamische "all"-Liste aufbauen
    base_steps = ["parse", "download"]
    if cfg.behavior.do_clean:
        base_steps.append("clean")
    if cfg.behavior.do_symlink:
        base_steps.append("link")
    if cfg.behavior.do_rename:
        base_steps.append("rename")
    if cfg.behavior.do_copy:
        base_steps.append("copy")

    if "all" in steps:
        steps = base_steps

    mods_cache = None
    for step in steps:
        fn = steps_map.get(step)
        if fn:
            logger.info(f"==> Starte Schritt: {step}")
            if step == "parse":
                mods_cache = fn()
            elif step == "download":
                run_download(cfg, logger, mods_cache)
            elif step == "link":
                run_link(cfg, logger, mods_cache)
            else:
                fn()
        else:
            logger.warning(f"Unbekannter Schritt: {step}")
