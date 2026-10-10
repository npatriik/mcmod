#!/usr/bin/env python3
"""
Unturned -> Minecraft generator.

Egy futtatasra vegigmegy az Unturned osszes fegyveren, es mindegyikhez, amit a mod tamogat,
legyartja a Minecraft-oldali fajlokat:

    modell      assets/unturnedcraft/models/item/<nev>.obj + .mtl + .json + <nev>_aiming.json
    textura     assets/unturnedcraft/textures/item/*.png
    hang        assets/unturnedcraft/sounds/<nev>/*.ogg   es a sounds.json
    targyleiro  assets/unturnedcraft/items/<nev>.json
    nevek       assets/unturnedcraft/lang/*.json          (csak az item.unturnedcraft.* sorok)
    adatok      unturnedcraft_guns.json                   (ezt olvassa be a Java-kod)

A fegyverekhez tartozo tarakat is legyartja. A fegyver modelljere rakerul az alap tar es az
alap iranyzek is, ahogy az Unturnedben latszik.

Futtatas (a projekt mappajabol):
    pip install UnityPy numpy pillow soundfile
    python tools/extract_unturned_assets.py --unturned "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Unturned"

A vegen kiirja, melyik fegyver maradt ki es miert. A modulok:
    unturned_dat.py      a .dat fajlok olvasasa
    unturned_bundle.py   modellek, texturak, hangok kinyerese az asset-csomagbol
    minecraft_model.py   a Minecraft-fajlok irasa es a kezben tartas kiszamolasa
    preview_models.py    kulon futtathato: elonezeti kepek a kesz modellekrol (jatek nelkul)

Regi fajlokat nem torol: ha egy fegyver kikerul a tamogatottak kozul, a korabban legyartott
fajljai a mappakban maradnak (artani nem artanak, a jatek egyszeruen nem hasznalja oket).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minecraft_model as mc          # noqa: E402
import unturned_bundle as ub          # noqa: E402
from unturned_dat import load_items   # noqa: E402

MODID = mc.MODID

# A kepernyore kiirt szovegek szandekosan ekezet nelkuliek: a Windows parancssora nem mindig
# tudja megjeleniteni az ekezetes betuket. A fajlokba irt (pl. nyelvi) szovegek ekezetesek.

# Azok a mukodesi modok (a .dat "Action" sora), amiket a mod tud. A tobbihez kulon lovedek kellene.
SUPPORTED_ACTIONS = {"Trigger", "Bolt", "Pump", "Break", "Minigun"}
SKIP_REASONS = {
    "String": "ij vagy szamszerij: repulo lovedek kell hozza",
    "Rocket": "raketaveto: repulo, robbano lovedek kell hozza",
    "Rail": "sinagyu: robbano lovedeket lo",
}

# Ha egy fegyvernek nincs sajat hangja valamire, ennek a fegyvernek a hangjat kapja.
FALLBACK_SOUND_GUN = "colt"
# Ha a .dat nem adja meg, ennyi ido alatt emelkedik celzasra a fegyver (sajat alapertek).
DEFAULT_AIM_IN_SECONDS = 0.2
# Ha nincs ujratoltes-hang, amibol az idot venni lehetne (sajat alapertek).
DEFAULT_RELOAD_SECONDS = 2.0

# A tarak magyar neve az angol nev vegzodese alapjan.
HUNGARIAN_SUFFIXES = [
    (" Magazine", " tár"), (" Clip", " töltőléc"), (" Drum", " dobtár"), (" Box", " lőszeres doboz"),
    ("12 Gauge Shells", "12-es sörétes lőszer"), ("20 Gauge Shells", "20-as sörétes lőszer"),
]


def item_id(item):
    """A Minecraft-beli azonosito: az Unturned-mappa neve kisbetuvel (pl. Desert_Falcon -> desert_falcon)."""
    return item.name.lower()


def prefab_path(item, kind):
    return f"items/{item.category.lower()}/{item.name.lower()}/{kind}.prefab"


# --------------------------------------------------------------------------------------------
# Unity -> Minecraft koordinatak
# --------------------------------------------------------------------------------------------
# Unity: balkezes rendszer, Y felfele; az Unturned fegyverek csove a prefabban a -Z fele nez.
# Minecraft: jobbkezes rendszer, Y felfele; a cso nalunk szinten a -Z fele nez, mert kezben
# tartva az "elore" irany a -Z. Balkezesbol jobbkezest az X tengely tukrozesevel kapunk; ilyenkor
# a haromszogek korbejarasi iranyat is meg kell forditani, kulonben kifordulna a modell.
def to_minecraft(vectors):
    out = np.array(vectors, dtype=float).reshape(-1, 3).copy()
    out[:, 0] *= -1
    return out


def build_parts(surface_groups, model_name):
    """surface_groups: lista (slot-nev, Surface-ok). Atvaltja Minecraft-koordinatakba, es
    elokesziti a texturakat. Visszaad: (reszek, texturak szotara fajlnev -> kep)."""
    parts, textures = [], {}
    for slot_base, surfaces in surface_groups:
        for index, surface in enumerate(surfaces):
            slot = slot_base if index == 0 else f"{slot_base}{index + 1}"
            image, uvs = ub.prepare_texture(surface)
            if surface.texture is None:
                # Egyszinu anyag: a szin nevu kozos kis kepet hasznaljuk (pl. flat_333333).
                r, g, b = (int(round(c * 255)) for c in surface.color)
                texture_name = f"flat_{r:02x}{g:02x}{b:02x}"
            else:
                texture_name = model_name if slot == "gun" or slot == "item" else f"{model_name}_{slot}"
            textures[texture_name] = image
            parts.append({
                "slot": slot,
                "texture": texture_name,
                "positions": to_minecraft(surface.positions),
                "normals": to_minecraft(surface.normals),
                "uvs": uvs,
                "triangles": [(c, b, a) for a, b, c in surface.triangles],  # forditott korbejaras
            })
    return parts, textures


def center_parts(parts):
    """A modell befoglalo dobozanak kozepet a (0.5, 0.5, 0.5) pontra tolja.
    Visszaad: (az eltolas, a doboz merete)."""
    all_points = np.vstack([p["positions"] for p in parts])
    lo, hi = all_points.min(axis=0), all_points.max(axis=0)
    shift = 0.5 - (lo + hi) / 2
    for part in parts:
        part["positions"] = part["positions"] + shift
    return shift, hi - lo


# --------------------------------------------------------------------------------------------
# Fegyver
# --------------------------------------------------------------------------------------------
def gun_calibers(gun):
    """Milyen kaliberu tarat fogad a fegyver. A legtobbnel egy "Caliber" sor van, nehanynal lista."""
    calibers = gun.numbered_list("Magazine_Calibers", "Magazine_Caliber_")
    if gun.has("Caliber") and gun.text("Caliber") not in calibers:
        calibers.insert(0, gun.text("Caliber"))
    return [int(c) for c in calibers]


def magazine_calibers(magazine):
    return [int(c) for c in magazine.numbered_list("Calibers", "Caliber_")]


def is_explosive(magazine):
    return magazine.has("Explosive") or magazine.has("Explosion")


def skip_reason(gun, items, bundle):
    """None, ha a fegyvert tamogatjuk; kulonben a kihagyas oka."""
    action = gun.text("Action", "")
    if gun.has("Turret"):
        return "jarmure szerelt fegyver"
    if action not in SUPPORTED_ACTIONS:
        return SKIP_REASONS.get(action, f"ismeretlen mukodesi mod: {action}")
    if not bundle.has(prefab_path(gun, "item")):
        return "nincs sajat modellje (egy masik fegyver valtozata)"
    magazine = items.get(gun.text("Magazine", ""))
    if magazine is None:
        return "az alap tara nem szam-azonositoval van megadva"
    if is_explosive(magazine):
        return "robbano loszert lo"
    return None


def damage_profile(gun, target):
    return {
        "damage": gun.number(f"{target}_Damage"),
        "leg": gun.number(f"{target}_Leg_Multiplier", 1.0),
        "spine": gun.number(f"{target}_Spine_Multiplier", 1.0),
        "skull": gun.number(f"{target}_Skull_Multiplier", 1.0),
    }


def generate_gun(gun, items, bundle, out):
    """Egy fegyver osszes fajlja. Visszaadja a guns.json-ba kerulo adatait."""
    name = item_id(gun)
    root = bundle.read(prefab_path(gun, "item"))
    surfaces, hooks = ub.collect(root, ub.ITEM_SPACE)
    groups = [("gun", surfaces)]

    # --- Az alap kiegeszitok rakerulnek a modellre, a megfelelo hookra illesztve ---
    eye = None
    sight_zoom = 0.0
    shoot_clip = bundle.find_audio(f"items/guns/{name}", "shoot")
    for kind in ("Magazine", "Sight", "Barrel", "Grip", "Tactical"):
        attachment = items.get(gun.text(kind, ""))
        if attachment is None or kind not in hooks:
            continue
        if kind == "Sight":
            sight_zoom = attachment.number("Zoom", 0.0)
        if kind == "Barrel":
            # A hangtompitos fegyvereknek nincs sajat loveshangjuk: a csoveg (Barrel) adja.
            shoot_clip = bundle.find_audio(f"items/barrels/{attachment.name.lower()}", "shoot") or shoot_clip
        path = prefab_path(attachment, kind.lower())
        if not bundle.has(path):
            continue
        # A kiegeszito gyokere a fegyver hookjanak helyere es allasaba kerul.
        attached, attached_hooks = ub.collect(bundle.read(path), hooks[kind])
        if attached:
            groups.append((kind.lower(), attached))
        if kind == "Sight" and "Aim" in attached_hooks:
            eye = attached_hooks["Aim"][:3, 3]   # az iranyzek megmondja, hova kell tenni a szemet

    # --- Hova keruljon a szem celzaskor ---
    if eye is None and "View" in hooks:
        eye = hooks["View"][:3, 3]               # iranyzek nelkuli fegyverek (pl. pisztolyok)
    eye = to_minecraft(eye)[0] if eye is not None else None
    if eye is None and "Sight" in hooks:
        eye = to_minecraft(hooks["Sight"][:3, 3])[0] + mc.FALLBACK_EYE_OFFSET

    parts, textures = build_parts(groups, name)
    shift, size = center_parts(parts)
    grip = shift                                  # az Unturned-modell origoja: itt fogja a kez
    if eye is None:
        eye = np.array([0.5, 0.5 + size[1] / 2 + 0.03, 0.5 + size[2] / 2 + 0.25])
    else:
        eye = eye + shift

    scoped = sight_zoom > 1.0
    display, aiming = mc.gun_display(size, grip, eye, scoped)
    mc.write_obj(out.models, name, parts)
    mc.write_model_json(out.models, name, parts, display)
    mc.write_aiming_json(out.models, name, aiming)
    mc.write_gun_item_json(out.items, name)
    out.save_textures(textures)

    # --- Hangok ---
    sounds = {}
    reload_seconds = None
    clips = {
        "shoot": shoot_clip,
        "reload": bundle.find_audio(f"items/guns/{name}", "reload"),
        "hammer": bundle.find_audio(f"items/guns/{name}", "hammer"),
    }
    for sound, clip in clips.items():
        if clip is not None:
            seconds = ub.write_ogg(os.path.join(out.sounds, name, sound + ".ogg"), clip)
            sounds[sound] = f"{MODID}:{name}/{sound}"
            if sound == "reload":
                reload_seconds = seconds
        else:
            sounds[sound] = f"{MODID}:{FALLBACK_SOUND_GUN}/{sound}"
    out.sound_events[name] = sounds

    # --- Adatok a Java-kodnak (nyers Unturned-ertekek; az atvaltas a GunStats.java dolga) ---
    magazine = items[gun.text("Magazine")]
    return {
        "id": name,
        "name": gun.english_name or gun.name,
        "rarity": gun.text("Rarity", "Common"),
        "slot": gun.text("Slot", "Primary"),
        "action": gun.text("Action"),
        "calibers": gun_calibers(gun),
        "defaultMagazine": item_id(magazine),
        "range": gun.number("Range"),
        "automatic": gun.has("Auto"),
        "firerate": gun.integer("Firerate"),
        "reloadSeconds": round(gun.number("Reload_Time", reload_seconds or DEFAULT_RELOAD_SECONDS), 3),
        "spreadAngleDegrees": gun.number("Spread_Angle_Degrees"),
        "spreadAim": gun.number("Spread_Aim", 1.0),
        "aimInSeconds": gun.number("Aim_In_Duration", DEFAULT_AIM_IN_SECONDS),
        "sightZoom": sight_zoom,
        "recoilMinY": gun.number("Recoil_Min_Y"),
        "recoilMaxY": gun.number("Recoil_Max_Y"),
        "players": damage_profile(gun, "Player"),
        "zombies": damage_profile(gun, "Zombie"),
        "animals": damage_profile(gun, "Animal"),
    }, size


# --------------------------------------------------------------------------------------------
# Tar
# --------------------------------------------------------------------------------------------
def generate_magazine(magazine, bundle, out):
    name = item_id(magazine)
    root = bundle.read(prefab_path(magazine, "item"))
    surfaces, _ = ub.collect(root, ub.ITEM_SPACE)
    parts, textures = build_parts([("item", surfaces)], name)
    _, size = center_parts(parts)
    mc.write_obj(out.models, name, parts)
    mc.write_model_json(out.models, name, parts, mc.small_item_display(size))
    mc.write_plain_item_json(out.items, name)
    out.save_textures(textures)
    return {
        "id": name,
        "name": magazine.english_name or magazine.name,
        "rarity": magazine.text("Rarity", "Common"),
        "calibers": magazine_calibers(magazine),
        "amount": magazine.integer("Amount", 1),
        "pellets": max(1, magazine.integer("Pellets", 1)),
    }


def hungarian_name(english):
    for suffix, replacement in HUNGARIAN_SUFFIXES:
        if english.endswith(suffix):
            return english[: -len(suffix)] + replacement
    return english


# --------------------------------------------------------------------------------------------
# Kimenet
# --------------------------------------------------------------------------------------------
class Output:
    """A projekt mappai, es amit a vegen egyben kell kiirni (hangok listaja, nevek)."""

    def __init__(self, project_dir):
        self.resources = os.path.join(project_dir, "src", "main", "resources")
        assets = os.path.join(self.resources, "assets", MODID)
        self.assets = assets
        self.models = os.path.join(assets, "models", "item")
        self.textures = os.path.join(assets, "textures", "item")
        self.items = os.path.join(assets, "items")
        self.sounds = os.path.join(assets, "sounds")
        self.lang = os.path.join(assets, "lang")
        for d in (self.models, self.textures, self.items, self.sounds, self.lang):
            os.makedirs(d, exist_ok=True)
        self.sound_events = {}
        self.saved_textures = set()

    def save_textures(self, textures):
        for name, image in textures.items():
            if name not in self.saved_textures:
                image.save(os.path.join(self.textures, name + ".png"))
                self.saved_textures.add(name)

    def write_sounds_json(self):
        """A sounds.json koti ossze a hangesemenyek nevet (amit a Java-kod hasznal) az .ogg fajlokkal."""
        events = {}
        for gun, sounds in sorted(self.sound_events.items()):
            for event, source in (("shoot", "shoot"), ("reload", "reload"), ("empty", "hammer")):
                events[f"item.{gun}.{event}"] = {
                    "subtitle": f"subtitles.{MODID}.gun.{event}",
                    "sounds": [sounds[source]],
                }
        mc.write_json(os.path.join(self.assets, "sounds.json"), events)

    def update_lang(self, names):
        """A nyelvi fajlokban csak a targynevek (item.unturnedcraft.*) sorait irja ujra;
        a kezzel irt tobbi sor (gombok, uzenetek...) erintetlen marad."""
        for language, translate in (("en_us", lambda n: n), ("hu_hu", hungarian_name)):
            path = os.path.join(self.lang, language + ".json")
            existing = {}
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    existing = json.load(f)
            prefix = f"item.{MODID}."
            merged = {k: v for k, v in existing.items() if not k.startswith(prefix)}
            for name, english in sorted(names.items()):
                merged[prefix + name] = translate(english)
            mc.write_json(path, merged)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unturned", required=True, help="az Unturned telepitesi mappaja")
    ap.add_argument("--project", default=None,
                    help="a mod projektmappaja (alapbol az, amiben ez a script van)")
    ap.add_argument("--only", nargs="*",
                    help="csak ezek a fegyverek (az Unturned mappaneve szerint, pl. Eaglefire); "
                         "kiserletezeshez, kulon --project mappaval")
    args = ap.parse_args()
    if args.only and args.project is None:
        # A kozos fajlok (unturnedcraft_guns.json, sounds.json, nevek) mindig csak azt tartalmazzak,
        # ami az adott futasban elkeszult, ezert reszleges futas a projektbe irva kitorolne a tobbit.
        sys.exit("Az --only csak kiserletezeshez valo: adj meg hozza egy kulon --project mappat, "
                 "kulonben a kozos fajlokbol a tobbi fegyver kimaradna.")
    if args.project is None:
        args.project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Csak a fegyverek es a rajuk szerelheto dolgok kellenek.
    items = load_items(os.path.join(args.unturned, "Bundles"),
                       ["Guns", "Magazines", "Sights", "Optics", "Barrels", "Grips", "Tacticals"])
    bundle = ub.Bundle(args.unturned)
    out = Output(args.project)

    # --- Fegyverek ---
    guns, skipped, sizes = [], [], {}
    for gun in sorted((i for i in items.values() if i.category == "Guns"), key=lambda i: i.name):
        if args.only and gun.name not in args.only:
            continue
        reason = skip_reason(gun, items, bundle)
        if reason:
            skipped.append((gun, reason))
            continue
        data, size = generate_gun(gun, items, bundle, out)
        guns.append(data)
        sizes[data["id"]] = size
        print(f"  fegyver  {data['id']:<18} {data['name']}")

    # --- Tarak: minden nem robbano tar, ami legalabb egy tamogatott fegyverbe valo ---
    wanted = {c for g in guns for c in g["calibers"]}
    magazines = []
    for magazine in sorted((i for i in items.values() if i.type == "Magazine"), key=lambda i: i.name):
        if is_explosive(magazine) or not wanted & set(magazine_calibers(magazine)):
            continue
        if not bundle.has(prefab_path(magazine, "item")):
            continue
        magazines.append(generate_magazine(magazine, bundle, out))
        print(f"  tar      {magazines[-1]['id']:<18} {magazines[-1]['name']}")

    # --- Kozos fajlok ---
    out.write_sounds_json()
    out.update_lang({d["id"]: d["name"] for d in guns + magazines})
    mc.write_json(os.path.join(out.resources, MODID + "_guns.json"), {
        "_comment": "Generalt fajl (tools/extract_unturned_assets.py). Kezzel ne szerkeszd: "
                    "a kovetkezo futtatas felulirja. Az ertekek az Unturned .dat fajljaibol jonnek.",
        "magazines": magazines,
        "guns": guns,
    })

    print(f"\nKesz: {len(guns)} fegyver, {len(magazines)} tar, {len(out.saved_textures)} textura.")
    if skipped:
        print("Kimaradt:")
        for gun, reason in skipped:
            print(f"  {gun.name:<18} {reason}")


if __name__ == "__main__":
    sys.exit(main())
