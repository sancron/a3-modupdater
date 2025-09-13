import re
import unicodedata
import os
from pathlib import Path

_INVALID_CHARS = re.compile(r'[:*?"<>|]')
_SPACE_RUN = re.compile(r"\s+")

def slugify(name: str) -> str:
    try:
        name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    except Exception:
        name = name.encode("ascii", "ignore").decode("ascii")

    # Ungültige Windows-Zeichen entfernen
    name = _INVALID_CHARS.sub("", name)

    # Apostrophe und ähnliche Zeichen entfernen
    name = name.replace("'", "").replace("’", "")

    # Bindestriche komplett entfernen
    name = name.replace("-", "")

    # Whitespace → "_"
    name = _SPACE_RUN.sub("_", name)

    # Mehrere Unterstriche zusammenfassen
    name = re.sub(r"_+", "_", name)

    # Anfang/Ende bereinigen und lowercase
    return name.strip("._ ").lower()


def is_windows() -> bool:
    return os.name == "nt"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")
