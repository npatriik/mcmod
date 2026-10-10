"""
Az Unturned .dat fajljainak olvasasa.

Az Unturned minden targyat (fegyver, tar, iranyzek, ruha...) egy sima szoveges fajllal ir le:

    Bundles/Items/Guns/Colt/Colt.dat       a targy adatai
    Bundles/Items/Guns/Colt/English.dat    a neve es a leirasa

A formatum soronkent "Kulcs ertek". Ha egy sorban csak kulcs all (pl. "Auto"), az egy kapcsolo:
a puszta jelenlete szamit. A szogletes/kapcsos zarojelek kozotti reszek (pl. a Blueprints,
vagyis a barkacsreceptek) beagyazott listak, ezeket itt atugorjuk.
"""
import os
from dataclasses import dataclass, field


def parse_dat(path):
    """Egy .dat fajl beolvasasa szotarba. A kapcsolok erteke ures szoveg ("")."""
    values = {}
    depth = 0  # hany zarojelen belul vagyunk eppen
    # utf-8-sig: a fajlok elejen levo lathatatlan BOM jelet is lenyeli
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if line[0] in "[{":
                depth += 1
                continue
            if line[0] in "]}":
                depth -= 1
                continue
            if depth > 0:
                continue
            line = line.split("//")[0].strip()  # sor vegi megjegyzes le
            key, _, value = line.partition(" ")
            values[key] = value.strip()
    return values


@dataclass
class Item:
    """Egy Unturned-targy: a mappaja es a .dat fajljanak tartalma."""
    id: str            # az Unturned szamozott azonositoja, pl. "97"
    category: str      # a szulo mappa, pl. "Guns", "Magazines", "Sights"
    name: str          # a sajat mappaja, pl. "Colt"
    directory: str
    dat: dict = field(repr=False)
    english_name: str = ""

    @property
    def type(self):
        return self.dat.get("Type", "")

    def has(self, key):
        """Igaz, ha a kulcs szerepel a fajlban (kapcsoloknal ez a lenyeg)."""
        return key in self.dat

    def text(self, key, default=None):
        return self.dat.get(key, default)

    def number(self, key, default=0.0):
        try:
            return float(self.dat[key])
        except (KeyError, ValueError):
            return default

    def integer(self, key, default=0):
        return int(round(self.number(key, default)))

    def numbered_list(self, count_key, item_prefix):
        """Az Unturned listai igy neznek ki: "Calibers 2", "Caliber_0 1", "Caliber_1 9".
        Visszaadja az elemeket: ["1", "9"]."""
        return [self.dat[f"{item_prefix}{i}"] for i in range(self.integer(count_key))
                if f"{item_prefix}{i}" in self.dat]


def load_items(bundles_dir, categories=None):
    """Vegigjarja a Bundles/Items mappat, es azonosito szerint visszaadja a targyakat.
    categories: ha meg van adva, csak ezeket az almappakat olvassa be (pl. ["Guns", "Magazines"]);
    az Unturnednek kozel ketezer targya van, mindet beolvasni feleslegesen lassu lenne."""
    items = {}
    root = os.path.join(bundles_dir, "Items")
    for category in sorted(os.listdir(root)):
        category_dir = os.path.join(root, category)
        if not os.path.isdir(category_dir) or (categories and category not in categories):
            continue
        for name in sorted(os.listdir(category_dir)):
            directory = os.path.join(category_dir, name)
            dat_path = os.path.join(directory, name + ".dat")
            if not os.path.isfile(dat_path):
                continue
            dat = parse_dat(dat_path)
            if "ID" not in dat:
                continue
            english_path = os.path.join(directory, "English.dat")
            english = parse_dat(english_path).get("Name", "") if os.path.isfile(english_path) else ""
            items[dat["ID"]] = Item(dat["ID"], category, name, directory, dat, english)
    return items
