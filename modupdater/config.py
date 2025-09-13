from __future__ import annotations
import dataclasses
import tomllib
from pathlib import Path
from typing import Dict, List


DEFAULT_CONFIG_PATH = Path(r"C:\Tools\steamcmd\modupdater.toml")


# -------------------------
# Steam / Paths / Behavior
# -------------------------

@dataclasses.dataclass(frozen=True)
class SteamConfig:
    cmd_path: Path
    exe_name: str
    app_id: str
    login_user: str
    login_pass: str
    runscript_path: Path


@dataclasses.dataclass(frozen=True)
class PathsConfig:
    final_mod_path: Path
    repo_html: Path
    mods_txt: Path
    log_file: Path
    master_copy: Path


@dataclasses.dataclass(frozen=True)
class BehaviorConfig:
    do_clean: bool          # ersetzt vorher clean_aggressive
    do_rename: bool         # ersetzt vorher implizit
    do_copy: bool           # bleibt
    do_symlink: bool
    validate: bool          # bleibt
    dry_run: bool           # bleibt


# -------------------------
# CopyConfig (NEU)
# -------------------------

@dataclasses.dataclass(frozen=True)
class CopyConfig:
    mode: str                   # "maps" | "mods" | "all"
    options: List[str]          # Robocopy Optionen
    exclude_dirs: List[str]     # Ordner, die ausgelassen werden
    map_rename: Dict[str, str]  # Mapping: Quelle -> Ziel (für Karten)


# -------------------------
# Haupt-Config
# -------------------------

@dataclasses.dataclass(frozen=True)
class Config:
    steam: SteamConfig
    paths: PathsConfig
    behavior: BehaviorConfig
    copy: CopyConfig

    @staticmethod
    def load(path: Path = DEFAULT_CONFIG_PATH) -> "Config":
        with path.open("rb") as f:
            data = tomllib.load(f)

        steam = SteamConfig(
            cmd_path=Path(data["steam"]["cmd_path"]),
            exe_name=data["steam"]["exe_name"],
            app_id=str(data["steam"]["app_id"]),
            login_user=data["steam"].get("login_user", ""),
            login_pass=data["steam"].get("login_pass", ""),
            runscript_path=Path(data["steam"]["runscript_path"]),
        )

        paths = PathsConfig(
            final_mod_path=Path(data["paths"]["final_mod_path"]),
            repo_html=Path(data["paths"]["repo_html"]),
            mods_txt=Path(data["paths"]["mods_txt"]),
            log_file=Path(data["paths"]["log_file"]),
            master_copy=Path(data["paths"]["master_copy"]),
        )

        behavior = BehaviorConfig(
            do_clean=bool(data["behavior"].get("do_clean", False)),
            do_rename=bool(data["behavior"].get("do_rename", True)),
            do_copy=bool(data["behavior"].get("do_copy", False)),
            do_symlink=bool(data["behavior"].get("do_symlink", True)),
            validate=bool(data["behavior"].get("validate", True)),
            dry_run=bool(data["behavior"].get("dry_run", False)),
        )

        copy = CopyConfig(
            mode=data["copy"].get("mode", "mods"),
            options=list(data["copy"].get("options", ["/MIR", "/COPYALL", "/R:5", "/W:10"])),
            exclude_dirs=list(data["copy"].get("exclude_dirs", [])),
            map_rename=dict(data["copy"].get("map_rename", {})),
        )

        return Config(steam=steam, paths=paths, behavior=behavior, copy=copy)
