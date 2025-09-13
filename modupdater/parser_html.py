import re
from pathlib import Path
from typing import List, Tuple
from .utils import read_text, write_text

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False

ModInfo = Tuple[str, str]  # (id, display_name)

def parse_repo_html(html: str, logger) -> List[ModInfo]:
    mods: List[ModInfo] = []
    if _HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        containers = soup.find_all("tr", {"data-type": "ModContainer"})
        for c in containers:
            name_el = c.find("td", {"data-type": "DisplayName"})
            link_el = c.find("a", {"data-type": "Link"})
            if not name_el or not link_el:
                continue
            display = name_el.text.strip()
            href = (link_el.get("href") or "").strip()
            m = re.search(r"id=(\d+)", href)
            if not m:
                continue
            mods.append((m.group(1), display))
    else:
        blocks = re.findall(r'<tr[^>]*data-type=["\']ModContainer["\'][^>]*>(.*?)</tr>', html, flags=re.S)
        for block in blocks:
            name_m = re.search(r'<td[^>]*data-type=["\']DisplayName["\'][^>]*>(.*?)</td>', block, flags=re.S)
            link_m = re.search(r'<a[^>]*data-type=["\']Link["\'][^>]*href=["\']([^"\']+)["\']', block)
            if not (name_m and link_m):
                continue
            display = re.sub(r"<[^>]+>", "", name_m.group(1)).strip()
            href = link_m.group(1).strip()
            id_m = re.search(r"id=(\d+)", href)
            if id_m:
                mods.append((id_m.group(1), display))
    logger.info(f"{len(mods)} Mods erkannt")
    return mods

def write_mods_txt(mods: List[ModInfo], path: Path, logger):
    lines = [f"{mid},{name}\n" for mid, name in mods]
    write_text(path, "".join(lines))
    logger.info(f"{len(mods)} Mods in {path} gespeichert")
