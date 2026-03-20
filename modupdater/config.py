from __future__ import annotations
import sys
import dataclasses
import tomllib
from tomllib import TOMLDecodeError
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_CONFIG_PATH = Path(r"C:\Tools\steamcmd\modupdater.toml")


def _guess_app_dir() -> Path:
    """Return the directory that should be treated as the app root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    argv0 = Path(sys.argv[0])
    if argv0.exists():
        return argv0.resolve().parent
    return Path(__file__).resolve().parent


def _default_global_config_path() -> Path:
    return _guess_app_dir() / "modupdater.global.toml"


DEFAULT_GLOBAL_CONFIG_PATH = _default_global_config_path()


_PATH_KEYS_BY_SECTION = {
    "steam": {"cmd_path", "runscript_path"},
    "paths": {"final_mod_path", "repo_html", "mods_txt", "log_file", "master_copy"},
}


def _sanitize_windows_paths(raw_text: str) -> str:
    section = None
    lines = raw_text.splitlines()
    changed = False

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]").split(".", 1)[0]
            continue

        if not section or section not in _PATH_KEYS_BY_SECTION:
            continue
        if "=" not in line:
            continue

        key_part, value_part = line.split("=", 1)
        key = key_part.strip()
        if key not in _PATH_KEYS_BY_SECTION[section]:
            continue

        value_lstrip = value_part.lstrip()
        leading_ws = value_part[: len(value_part) - len(value_lstrip)]
        if not value_lstrip.startswith('"'):
            continue

        try:
            closing_index = value_lstrip.index('"', 1)
        except ValueError:
            continue

        inner = value_lstrip[1:closing_index]
        tail = value_lstrip[closing_index + 1 :]

        if "\\" not in inner or "\\\\" in inner:
            continue

        sanitized = inner.replace("\\", "\\\\")
        lines[idx] = f"{key_part}={leading_ws}\"{sanitized}\"{tail}"
        changed = True

    if changed:
        return "\n".join(lines)
    return raw_text


def _load_toml(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    try:
        return tomllib.loads(raw_text)
    except TOMLDecodeError:
        sanitized = _sanitize_windows_paths(raw_text)
        if sanitized == raw_text:
            raise
        return tomllib.loads(sanitized)


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
    def load(
        path: Path = DEFAULT_CONFIG_PATH,
        global_path: Optional[Path] = DEFAULT_GLOBAL_CONFIG_PATH,
    ) -> "Config":
        path = Path(path)
        data = _load_toml(path)

        global_data: dict = {}
        if global_path:
            gpath = Path(global_path)
            if gpath.exists():
                global_data = _load_toml(gpath)

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

        copy_data = dict(data.get("copy", {}))
        global_copy_data = dict(global_data.get("copy", {})) if global_data else {}

        if "exclude_dirs" in copy_data:
            exclude_dirs = list(copy_data.get("exclude_dirs") or [])
        else:
            exclude_dirs = list(global_copy_data.get("exclude_dirs", []))

        if "map_rename" in copy_data:
            map_rename = dict(copy_data.get("map_rename") or {})
        else:
            map_rename = dict(global_copy_data.get("map_rename", {}))

        copy = CopyConfig(
            mode=copy_data.get("mode", "mods"),
            options=list(copy_data.get("options", ["/MIR", "/COPYALL", "/R:5", "/W:10"])),
            exclude_dirs=exclude_dirs,
            map_rename=map_rename,
        )

        return Config(steam=steam, paths=paths, behavior=behavior, copy=copy)
