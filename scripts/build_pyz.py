from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from importlib import util as importlib_util
from pathlib import Path

RUNTIME_DEPENDENCIES = ("bs4", "soupsieve")


def _copy_module(module_name: str, destination: Path) -> None:
    spec = importlib_util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise RuntimeError(
            f"Python-Paket '{module_name}' nicht gefunden. "
            "Bitte installiere alle dev-Abhängigkeiten (pip install -e .[dev])."
        )

    source = Path(spec.origin)
    if source.name == "__init__.py":
        source = source.parent

    target = destination / source.name
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def build_pyz(output: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    build_root = repo_root / "build"
    staging = build_root / "shivsite"

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    shutil.copytree(repo_root / "modupdater", staging / "modupdater", dirs_exist_ok=True)

    for dependency in RUNTIME_DEPENDENCIES:
        _copy_module(dependency, staging)

    output.parent.mkdir(parents=True, exist_ok=True)

    temp_root = Path(tempfile.mkdtemp(prefix="shivtmp_", dir=build_root))

    cmd = [
        sys.executable,
        "-m",
        "shiv",
        "--site-packages",
        str(staging),
        "--entry-point",
        "modupdater.cli:main",
        "--compressed",
        "--compile-pyc",
        "-o",
        str(output),
    ]

    env = os.environ.copy()
    env["TEMP"] = str(temp_root)
    env["TMP"] = str(temp_root)
    env["TMPDIR"] = str(temp_root)

    try:
        subprocess.run(cmd, check=True, env=env)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baut modupdater.pyz mittels Shiv")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("dist/modupdater.pyz"),
        help="Zielpfad für das erzeugte PYZ-Archiv",
    )
    args = parser.parse_args()
    build_pyz(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
