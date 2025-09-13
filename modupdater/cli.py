import argparse
from pathlib import Path
from dataclasses import replace
from .config import Config, DEFAULT_CONFIG_PATH
from .logging_utils import setup_logging
from .workflow import run_workflow

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="modupdater", description="Arma 3 Mod Updater")
    p.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG_PATH,
                   help="Pfad zur TOML-Konfiguration")
    p.add_argument("--dry-run", action="store_true",
                   help="Trockenlauf (überschreibt Config)")
    sub = p.add_subparsers(dest="command", required=True)
    for cmd in ["parse", "download", "link", "clean", "rename", "all"]:
        sub.add_parser(cmd)
    return p

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    if args.dry_run:
        cfg = replace(cfg, behavior=replace(cfg.behavior, dry_run=True))

    logger = setup_logging(cfg.paths.log_file)
    return run_workflow(cfg, args.command, logger)
