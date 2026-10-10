"""
Minecraft-oldali fajlok irasa: .obj/.mtl modell, a modell .json leirasa, es annak kiszamolasa,
hogyan alljon a targy kezben, a hotbaron stb. (a .json "display" resze).

Koordinatak: a Minecraft targymodelljei blokk-egysegben vannak, a modell kozepe a (0.5, 0.5, 0.5)
pont. A fegyverek csove a -Z (eszak) fele nez, a felso reszuk +Y fele.

A "display" egy-egy nezethez (kezben, hotbaron, foldon...) harom dolgot ad meg, es a jatek ebben
a sorrendben alkalmazza a modell kozepe korul:  meretezes -> forgatas -> eltolas.
  rotation     fokban, X, Y, Z tengely korul (a jatek eloszor Z, aztan Y, vegul X korul forgat)
  translation  1/16 blokkban, legfeljebb +-80
  scale        legfeljebb 4
"""
import json
import math
import os

import numpy as np

MODID = "unturnedcraft"
CENTER = np.array([0.5, 0.5, 0.5])

# Belso nezetben a jatek a kezben tartott targy modelljenek kozepet ide teszi a kamerahoz kepest
# (jobbra, lefele, elore), mielott a "display" eltolasa ramenne. Forras: a jatek kodja.
FIRST_PERSON_ARM = np.array([0.56, -0.52, -0.72])

# Hova keruljon a fegyver "markolatpontja" (az Unturned-modell origoja: ott fogja a kez).
# Ezek az 1911 kezzel beallitott, jatekban jovahagyott tartasabol vannak visszaszamolva, igy
# minden fegyver ugyanoda kerul a kezben, akarmekkora.
FIRST_PERSON_GRIP = np.array([0.2768, -0.1744, -0.8104])   # a kamerahoz kepest
FIRST_PERSON_YAW = 4.0                                     # kicsit befele forditva
THIRD_PERSON_GRIP = np.array([0.0, 0.153, 0.1269])         # a kez koordinata-rendszereben
THIRD_PERSON_ROTATION = (90.0, 0.0, 0.0)                   # a cso elore nezzen, ne lefele

# Ha a fegyveren nincs se iranyzek, se View pont, a szemet az iranyzek helye moge-fole tesszuk
# ennyivel (a tobbi fegyver atlagos erteke).
FALLBACK_EYE_OFFSET = np.array([0.0, 0.07, 0.23])


# --------------------------------------------------------------------------------------------
# Forgatasok
# --------------------------------------------------------------------------------------------
def rotation_matrix(rx, ry, rz):
    """A Minecraft "rotation": [rx, ry, rz] fokban. A jatek az Rx * Ry * Rz matrixot hasznalja,
    vagyis egy pontot eloszor a Z, aztan az Y, vegul az X tengely korul forgat."""
    ax, ay, az = (math.radians(a) for a in (rx, ry, rz))
    mx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    my = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    mz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return mx @ my @ mz


def euler_from_matrix(m):
    """Az elozo fuggveny forditottja: egy forgatasi matrixbol a Minecraft [rx, ry, rz] szogei."""
    ry = math.asin(max(-1.0, min(1.0, m[0][2])))
    rx = math.atan2(-m[1][2], m[2][2])
    rz = math.atan2(-m[0][1], m[0][0])
    angles = tuple(round(math.degrees(a), 2) for a in (rx, ry, rz))
    assert np.allclose(rotation_matrix(*angles), m, atol=1e-3), "nem bonthato fel"
    return angles


def anchor_translation(rotation, scale, model_point, target, base=np.zeros(3)):
    """Mekkora eltolas kell ahhoz, hogy a modell egy adott pontja (model_point) a forgatas es a
    meretezes utan pontosan a kert helyre (target) keruljon? 1/16 blokkban adja vissza."""
    moved = rotation_matrix(*rotation) @ ((np.array(model_point) - CENTER) * scale)
    return [round(float(v), 2) for v in (np.array(target) - base - moved) * 16.0]


def projected_extent(rotation, size):
    """A befoglalo doboz szelessege/magassaga a kepernyon (X es Y iranyban) adott forgatas utan."""
    half = np.array(size) / 2.0
    corners = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) * half
    rotated = corners @ rotation_matrix(*rotation).T
    return 2 * np.abs(rotated[:, :2]).max(axis=0)


def _entry(rotation, translation, scale):
    return {
        "rotation": [round(float(a), 2) for a in rotation],
        "translation": [max(-80.0, min(80.0, round(float(t), 2))) for t in translation],
        "scale": [round(float(scale), 3)] * 3,
    }


# A hotbaron: oldalnezet (a cso jobbra mutat), majd 45 fokkal megdontve, hogy a hosszu fegyverek
# is kitoltsek a negyzetes helyet (az atlo hosszabb, mint az oldal).
GUI_ROTATION = euler_from_matrix(rotation_matrix(0, 0, 45) @ rotation_matrix(0, -90, 0))


def gun_display(size, grip, eye, scoped):
    """Egy fegyver "display" bejegyzesei.
      size    a modell befoglalo dobozanak merete (X, Y, Z) blokkban
      grip    a markolatpont helye a modellben
      eye     a szem helye celzaskor a modellben
      scoped  tavcsoves-e (akkor celzaskor a fegyvert kivisszuk a kepbol)
    Visszaad: (a normal display, a celzo nezet first-person bejegyzese)."""
    first_rotation = (0.0, FIRST_PERSON_YAW, 0.0)
    first_translation = anchor_translation(first_rotation, 1.0, grip, FIRST_PERSON_GRIP, FIRST_PERSON_ARM)
    gui_scale = min(4.0, 0.95 / projected_extent(GUI_ROTATION, size).max())
    length = max(size[2], size[1])
    display = {
        "firstperson_righthand": _entry(first_rotation, first_translation, 1.0),
        "thirdperson_righthand": _entry(
            THIRD_PERSON_ROTATION,
            anchor_translation(THIRD_PERSON_ROTATION, 1.0, grip, THIRD_PERSON_GRIP), 1.0),
        "gui": _entry(GUI_ROTATION, (0, 0, 0), gui_scale),
        "ground": _entry((0, 0, 0), (0, 1, 0), 1.0),
        "fixed": _entry((0, 90, 0), (0, 0, 0), min(1.6, 0.95 / length)),
    }
    if scoped:
        # Tavcsonel a kep kozepere nagyitunk; a fegyver modellje csak kitakarna a latvanyt,
        # ezert celzas kozben egy blokknyit lesullyesztjuk, ki a kepbol.
        aim_translation = [first_translation[0], first_translation[1] - 16.0, first_translation[2]]
        aiming = _entry(first_rotation, aim_translation, 1.0)
    else:
        # A szem keruljon pontosan a kamera helyere (0, 0, 0): igy az iranyzek a celkereszt ala esik.
        aiming = _entry((0, 0, 0), anchor_translation((0, 0, 0), 1.0, eye, (0, 0, 0), FIRST_PERSON_ARM), 1.0)
    return display, aiming


def small_item_display(size):
    """Kisebb targyak (tarak) display bejegyzesei."""
    gui_rotation = (20.0, -50.0, 0.0)
    biggest = max(size)
    return {
        "firstperson_righthand": _entry((0, 30, 0), (-4.5, 4, -1), 1.0),
        "thirdperson_righthand": _entry((90, 0, 0), (0, 1, 1), 1.0),
        "gui": _entry(gui_rotation, (0, 0, 0), min(4.0, 0.9 / projected_extent(gui_rotation, size).max())),
        "ground": _entry((0, 0, 0), (0, 1, 0), 1.0),
        "fixed": _entry((0, 90, 0), (0, 0, 0), min(2.5, 0.6 / biggest)),
    }


# --------------------------------------------------------------------------------------------
# Fajlok irasa
# --------------------------------------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_obj(models_dir, name, parts):
    """parts: lista, elemei szotarak: slot, positions, uvs, normals, triangles.
    Minden resz kulon anyagot (usemtl) kap, mert mas-mas textura tartozik hozza."""
    lines = [f"# Generalta: tools/extract_unturned_assets.py ({name})", f"mtllib {name}.mtl", f"o {name}"]
    faces, offset = [], 0
    for part in parts:
        lines += ["v %.6f %.6f %.6f" % tuple(p) for p in part["positions"]]
        lines += ["vt %.6f %.6f" % tuple(t) for t in part["uvs"]]
        lines += ["vn %.6f %.6f %.6f" % tuple(n) for n in part["normals"]]
        faces.append(f"usemtl {part['slot']}")
        # OBJ-ben a sorszamozas 1-tol indul, es az egesz fajlra kozos; pont/uv/normal indexe egyezik.
        faces += ["f " + " ".join(f"{i + offset + 1}/{i + offset + 1}/{i + offset + 1}" for i in tri)
                  for tri in part["triangles"]]
        offset += len(part["positions"])
    with open(os.path.join(models_dir, name + ".obj"), "w", newline="\n") as f:
        f.write("\n".join(lines + faces) + "\n")
    # A "#nev" nem fajlnev, hanem hivatkozas: a modell .json fajljanak "textures" reszeben az
    # ugyanilyen nevu bejegyzes mondja meg, melyik kep tartozik ide. "Ka 0 0 0": ne vilagitson.
    with open(os.path.join(models_dir, name + ".mtl"), "w", newline="\n") as f:
        for part in parts:
            f.write(f"newmtl {part['slot']}\nKa 0 0 0\nKd 1 1 1\nmap_Kd #{part['slot']}\n\n")


def write_model_json(models_dir, name, parts, display):
    textures = {part["slot"]: f"{MODID}:item/{part['texture']}" for part in parts}
    textures["particle"] = "#" + parts[0]["slot"]
    write_json(os.path.join(models_dir, name + ".json"), {
        "loader": "neoforge:obj",
        "model": f"{MODID}:models/item/{name}.obj",
        "flip_v": True,
        "emissive_ambient": False,
        "automatic_culling": False,
        "gui_light": "side",
        "textures": textures,
        "display": display,
    })


def write_plain_item_json(items_dir, name):
    write_json(os.path.join(items_dir, name + ".json"),
               {"model": {"type": "minecraft:model", "model": f"{MODID}:item/{name}"}})


def write_gun_item_json(items_dir, name):
    """A fegyver ket modell-leiras kozul valaszt aszerint, hogy a jatekos epp celoz-e
    (vagyis "hasznalja-e" a targyat)."""
    write_json(os.path.join(items_dir, name + ".json"), {"model": {
        "type": "minecraft:condition",
        "property": "minecraft:using_item",
        "on_true": {"type": "minecraft:model", "model": f"{MODID}:item/{name}_aiming"},
        "on_false": {"type": "minecraft:model", "model": f"{MODID}:item/{name}"},
    }})


def write_aiming_json(models_dir, name, aiming_entry):
    """A celzo nezet mindent a fegyver alap modelljetol orokol, csak a belso nezetet irja felul."""
    write_json(os.path.join(models_dir, name + "_aiming.json"), {
        "parent": f"{MODID}:item/{name}",
        "display": {"firstperson_righthand": aiming_entry},
    })
