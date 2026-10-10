#!/usr/bin/env python3
"""
Elonezet a legyartott modellekrol, a jatek elinditasa nelkul.

Beolvassa a projektbol a kesz .obj modelleket es a "display" beallitasaikat, es egy kis
szoftveres rajzoloval harom attekinto kepet keszit a build/preview mappaba:

    gui.png          minden fegyver es tar ugy, ahogy a hotbaron / inventoryban latszik
    firstperson.png  minden fegyver belso nezetben, kezben tartva
    aiming.png       minden fegyver celzas kozben; a feher kereszt a kepernyo kozepe (a celkereszt)

Arra jo, hogy egy generalas utan gyorsan latsszon, ha valamelyik fegyver rossz iranyba all, tul
nagy, vagy celzaskor nem a celkereszt ala kerul az iranyzeka. NEM a jatek rajzoloja: nincs benne
a jatekos keze, es a fenyek is csak hasonlitanak. A vegso szot mindig a jatek mondja ki.

Futtatas (a projekt mappajabol):
    pip install numpy pillow
    python tools/preview_models.py                 minden fegyver
    python tools/preview_models.py colt eaglefire  csak a felsoroltak

Hogyan rajzol: minden haromszoget a kepernyore vetit, es a kepernyo-pontokrol egyenkent eldonti,
beleesnek-e (baricentrikus koordinatak). Hogy a kozelebbi felulet takarja a tavolabbit, minden
keppontnal megjegyzi az eddigi legkisebb tavolsagot (ez a "z-buffer").
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minecraft_model as mc   # noqa: E402

BACKGROUND = (40, 44, 52, 255)
SHEET_BACKGROUND = (20, 20, 20, 255)
LABEL_HEIGHT = 14
LIGHT_DIRECTION = np.array([0.3, 0.8, 0.6])
FIELD_OF_VIEW = 70.0     # a Minecraft alap latoszoge (fuggoleges, fokban)


# --------------------------------------------------------------------------------------------
# Modell beolvasasa
# --------------------------------------------------------------------------------------------
class Model:
    """Egy targymodell: csucsok, texturakoordinatak, normalisok, haromszogek es a 'display'."""

    def __init__(self, assets_dir, name):
        models_dir = os.path.join(assets_dir, "models", "item")
        with open(os.path.join(models_dir, name + ".json"), encoding="utf-8") as f:
            description = json.load(f)

        if "model" not in description:
            # A celzo modell (<nev>_aiming.json) csak orokol a szulojetol, es felulir egy nezetet.
            parent = Model(assets_dir, description["parent"].split("/")[-1])
            self.__dict__.update(parent.__dict__)
            self.display = dict(parent.display)
            self.display.update(description.get("display", {}))
            return

        vertices, uvs, normals, self.faces, self.face_materials = [], [], [], [], []
        material = None
        with open(os.path.join(models_dir, name + ".obj"), encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == "v":
                    vertices.append([float(x) for x in parts[1:4]])
                elif parts[0] == "vt":
                    uvs.append([float(x) for x in parts[1:3]])
                elif parts[0] == "vn":
                    normals.append([float(x) for x in parts[1:4]])
                elif parts[0] == "usemtl":
                    material = parts[1]
                elif parts[0] == "f":
                    # "f 1/1/1 2/2/2 3/3/3": a generator mindharom indexet egyformara irja.
                    self.faces.append([int(corner.split("/")[0]) - 1 for corner in parts[1:]])
                    self.face_materials.append(material)
        self.vertices, self.uvs, self.normals = np.array(vertices), np.array(uvs), np.array(normals)

        # Texturak: a modell .json "textures" resze mondja meg, melyik anyaghoz melyik kep tartozik.
        self.textures = {}
        for slot, reference in description["textures"].items():
            if reference.startswith("#"):
                continue   # pl. "particle": "#valami", csak hivatkozas egy masik helyre
            path = os.path.join(assets_dir, "textures", "item", reference.split("/")[-1] + ".png")
            self.textures[slot] = np.array(Image.open(path).convert("RGBA"))
        self.display = description["display"]

    def placed(self, view):
        """A csucsok es a normalisok a kert nezet 'display' beallitasa utan:
        meretezes -> forgatas -> eltolas, a modell kozepe (0.5, 0.5, 0.5) korul."""
        entry = self.display[view]
        rotation = mc.rotation_matrix(*entry["rotation"])
        scale = np.array(entry["scale"])
        translation = np.array(entry["translation"]) / 16.0
        return ((self.vertices - mc.CENTER) * scale) @ rotation.T + translation, self.normals @ rotation.T


# --------------------------------------------------------------------------------------------
# Vetites: 3D pont -> (kepernyo x, kepernyo y, tavolsag)
# --------------------------------------------------------------------------------------------
def orthographic(width, height):
    """Parhuzamos vetites, ahogy a hotbar rajzol: 1 blokk = a kep teljes szelessege."""
    def project(points):
        return np.column_stack(((points[:, 0] + 0.5) * width, (0.5 - points[:, 1]) * height,
                                10.0 - points[:, 2]))
    return project


def perspective(width, height):
    """Perspektiv vetites: a kamera az origoban all, es a -Z fele nez (mint a jatekos szeme)."""
    focal = 1.0 / math.tan(math.radians(FIELD_OF_VIEW) / 2.0)

    def project(points):
        depth = -points[:, 2]
        safe = np.where(depth < 0.01, 0.01, depth)
        x = (points[:, 0] * focal / (width / height) / safe * 0.5 + 0.5) * width
        y = (0.5 - points[:, 1] * focal / safe * 0.5) * height
        return np.column_stack((x, y, depth))
    return project


# --------------------------------------------------------------------------------------------
# Rajzolas
# --------------------------------------------------------------------------------------------
def rasterize(model, points, normals, project, width, height):
    image = np.zeros((height, width, 4), np.uint8)
    image[:] = BACKGROUND
    nearest = np.full((height, width), np.inf)          # z-buffer
    screen = project(points)
    light = LIGHT_DIRECTION / np.linalg.norm(LIGHT_DIRECTION)

    for face, material in zip(model.faces, model.face_materials):
        a, b, c = screen[face[0]], screen[face[1]], screen[face[2]]
        if min(a[2], b[2], c[2]) <= 0.02:
            continue   # a kamera mogott van
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if area >= 0:
            continue   # hatulrol latszik (vagy elfajult): a jatek sem rajzolja ki

        x0, x1 = max(int(min(a[0], b[0], c[0])), 0), min(int(max(a[0], b[0], c[0])) + 1, width - 1)
        y0, y1 = max(int(min(a[1], b[1], c[1])), 0), min(int(max(a[1], b[1], c[1])) + 1, height - 1)
        if x1 < x0 or y1 < y0:
            continue   # nem er bele a kepbe

        # A haromszog befoglalo teglalapjanak minden keppontjara: a harom sulybol (w0, w1, w2)
        # latszik, hogy a pont a haromszogben van-e, es ugyanezekkel a sulyokkal keverjuk ki a
        # tavolsagot es a texturakoordinatat a harom csucs ertekeibol.
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((b[0] - xs) * (c[1] - ys) - (b[1] - ys) * (c[0] - xs)) / area
        w1 = ((c[0] - xs) * (a[1] - ys) - (c[1] - ys) * (a[0] - xs)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        depth = w0 * a[2] + w1 * b[2] + w2 * c[2]

        uv = model.uvs
        u = w0 * uv[face[0]][0] + w1 * uv[face[1]][0] + w2 * uv[face[2]][0]
        v = w0 * uv[face[0]][1] + w1 * uv[face[1]][1] + w2 * uv[face[2]][1]
        # Tu-vekony haromszogeknel a sulyok elszallhatnak; a texturakoordinata amugy is 0 es 1 kozotti.
        u, v = np.clip(np.nan_to_num(u), 0.0, 1.0), np.clip(np.nan_to_num(v), 0.0, 1.0)
        texture = model.textures[material]
        texture_height, texture_width = texture.shape[:2]
        column = np.clip((u * texture_width).astype(int), 0, texture_width - 1)
        row = np.clip(((1.0 - v) * texture_height).astype(int), 0, texture_height - 1)

        # Egyszeru arnyalas: minel inkabb a feny fele nez a lap, annal vilagosabb.
        normal = normals[face[0]] + normals[face[1]] + normals[face[2]]
        normal = normal / max(np.linalg.norm(normal), 1e-9)
        brightness = 0.45 + 0.55 * max(0.0, float(normal @ light))
        color = texture[row, column].astype(float) * brightness
        color[..., 3] = 255
        color = color.clip(0, 255).astype(np.uint8)

        window = nearest[y0:y1 + 1, x0:x1 + 1]
        visible = inside & (depth < window)
        window[visible] = depth[visible]
        image[y0:y1 + 1, x0:x1 + 1][visible] = color[visible]
    return Image.fromarray(image)


def draw_gui(model, size=112):
    points, normals = model.placed("gui")
    return rasterize(model, points, normals, orthographic(size, size), size, size)


def draw_first_person(model, width=320, height=180, crosshair=False):
    points, normals = model.placed("firstperson_righthand")
    # A jatek a kezben tartott targyat eloszor a kamera ele-jobbra-le teszi, a "display" ezutan jon.
    image = rasterize(model, points + mc.FIRST_PERSON_ARM, normals, perspective(width, height), width, height)
    if crosshair:
        draw = ImageDraw.Draw(image)
        cx, cy = width / 2, height / 2
        draw.line([(cx - 5, cy), (cx + 5, cy)], fill=(255, 255, 255, 255))
        draw.line([(cx, cy - 5), (cx, cy + 5)], fill=(255, 255, 255, 255))
    return image


def contact_sheet(names, draw_one, cell, columns):
    """Sok kis kep egy nagy tablan, mindegyik folott a targy azonositoja."""
    cell_width, cell_height = cell
    rows = (len(names) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * cell_width, rows * (cell_height + LABEL_HEIGHT)), SHEET_BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for index, name in enumerate(names):
        x = (index % columns) * cell_width
        y = (index // columns) * (cell_height + LABEL_HEIGHT)
        sheet.paste(draw_one(name), (x, y + LABEL_HEIGHT))
        draw.text((x + 3, y + 1), name, fill=(230, 230, 230, 255))
    return sheet


def main():
    default_project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="Elonezet a legyartott modellekrol.")
    parser.add_argument("only", nargs="*", help="csak ezek a fegyverek (azonosito szerint); alapbol mind")
    parser.add_argument("--project", default=default_project, help="a mod projektmappaja")
    parser.add_argument("--out", default=None, help="ide kerulnek a kepek (alapbol build/preview)")
    args = parser.parse_args()

    resources = os.path.join(args.project, "src", "main", "resources")
    assets = os.path.join(resources, "assets", mc.MODID)
    out_dir = args.out or os.path.join(args.project, "build", "preview")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(resources, "unturnedcraft_guns.json"), encoding="utf-8") as f:
        data = json.load(f)
    guns = [gun["id"] for gun in data["guns"] if not args.only or gun["id"] in args.only]
    magazines = [magazine["id"] for magazine in data["magazines"]] if not args.only else []
    if not guns:
        sys.exit("Nincs ilyen fegyver. Az azonositok az unturnedcraft_guns.json-ban vannak.")

    cache = {}

    def model(name):
        if name not in cache:
            cache[name] = Model(assets, name)
        return cache[name]

    sheets = {
        "gui.png": contact_sheet(guns + magazines, lambda n: draw_gui(model(n)), (112, 112), 10),
        "firstperson.png": contact_sheet(guns, lambda n: draw_first_person(model(n)), (320, 180), 4),
        "aiming.png": contact_sheet(guns, lambda n: draw_first_person(model(n + "_aiming"), crosshair=True),
                                    (320, 180), 4),
    }
    for file_name, sheet in sheets.items():
        path = os.path.join(out_dir, file_name)
        sheet.save(path)
        print("kesz:", path)


if __name__ == "__main__":
    main()
