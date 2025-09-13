import subprocess
from .utils import write_text
from .config import Config
from typing import List, Tuple

ModInfo = Tuple[str, str]  # (id, display_name)


def build_steamcmd_commands(cfg: Config, mods: List[ModInfo]) -> list[str]:
    """Baut die SteamCMD-Befehle für alle Mods."""
    cmds = [
        "@sSteamCmdForcePlatformType windows",
        f'force_install_dir "{cfg.paths.final_mod_path}"',
    ]
    if cfg.steam.login_user:
        cmds.append(f'login {cfg.steam.login_user} {cfg.steam.login_pass}'.strip())
    else:
        cmds.append("login anonymous")

    for mod_id, _ in mods:
        line = f"workshop_download_item {cfg.steam.app_id} {mod_id}"
        if cfg.behavior.validate:
            line += " validate"
        cmds.append(line)

    cmds.append("quit")
    return cmds


def run_steamcmd(cfg: Config, commands: list[str], logger) -> int:
    """Schreibt das RunScript und startet SteamCMD."""
    exe = cfg.steam.cmd_path / cfg.steam.exe_name
    runscript = cfg.steam.runscript_path

    if not exe.exists():
        logger.error(f"SteamCMD fehlt: {exe}")
        return 2
    if not runscript.parent.exists():
        logger.error(f"RunScript-Pfad existiert nicht: {runscript.parent}")
        return 3

    # RunScript schreiben
    write_text(runscript, "\n".join(commands))

    cmd = [str(exe), "+runscript", str(runscript)]
    logger.info(f"Starte SteamCMD: {cmd}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )
    for line in proc.stdout:
        logger.info(line.rstrip())
    proc.wait()

    rc = proc.returncode or 0
    if rc == 0:
        logger.info("SteamCMD erfolgreich abgeschlossen")
    else:
        logger.error(f"SteamCMD Fehlercode: {rc}")
    return rc
