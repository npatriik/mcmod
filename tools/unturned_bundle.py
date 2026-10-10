"""
Az Unturned asset-csomagjanak (Bundles/core.masterbundle) olvasasa a UnityPy konyvtarral:
modellek (mesh), texturak es hangok kinyerese.

Fogalmak:
  prefab   = egy targy "osszerakott" formaja Unityben: csomopontok faja. Egy csomoponton lehet
             modell (mesh), de lehet ures is; az ures csomopontok a "hookok" (segedpontok), pl. a
             fegyveren a Magazine (ide kerul a tar), a Sight (ide az iranyzek), a View (ide a szem).
  LOD      = "level of detail": ugyanaz a modell tobb reszletessegben. Nekunk mindig a
             legreszletesebb (LOD0) kell.
"""
import io
import math
import os

import numpy as np
import soundfile as sf
import UnityPy
from PIL import Image
from UnityPy.helpers.MeshHelper import MeshHandler

# A csomagon belul minden utvonal ezzel kezdodik (lasd Bundles/MasterBundle.dat).
BUNDLE_PREFIX = "assets/coremasterbundle/"

IDENTITY = np.identity(4)


class Bundle:
    """A megnyitott asset-csomag. Az utvonalak kisbetusek, pl. "items/guns/colt/item.prefab"."""

    def __init__(self, unturned_dir):
        path = os.path.join(unturned_dir, "Bundles", "core.masterbundle")
        print("Csomag betoltese:", path)
        self.env = UnityPy.load(path)
        self.container = self.env.container

    def has(self, rel_path):
        return (BUNDLE_PREFIX + rel_path) in self.container

    def read(self, rel_path):
        return self.container[BUNDLE_PREFIX + rel_path].read()

    def find_audio(self, folder, name):
        """Hangfajl keresese kiterjesztes nelkul (az Unturnedben van .mp3, .ogg es .wav is)."""
        for ext in (".mp3", ".ogg", ".wav"):
            if self.has(f"{folder}/{name}{ext}"):
                return self.read(f"{folder}/{name}{ext}")
        return None


# --------------------------------------------------------------------------------------------
# Prefab bejarasa
# --------------------------------------------------------------------------------------------
def _quat_to_matrix(q):
    """Unity kvaternio (x, y, z, w) -> 3x3 forgatasi matrix."""
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def _local_matrix(transform):
    m = np.identity(4)
    s = transform.m_LocalScale
    m[:3, :3] = _quat_to_matrix(transform.m_LocalRotation) @ np.diag([s.x, s.y, s.z])
    p = transform.m_LocalPosition
    m[:3, 3] = [p.x, p.y, p.z]
    return m


# Az Unturned targymodelljeinek sajat koordinata-rendszere: +Y elore (erre nez a cso), +Z felfele.
# Unityben a +Y a "felfele", ezert a modellt -90 fokkal el kell forgatni az X tengely korul.
# A legtobb prefab gyokere pontosan ezt a forgatast tartalmazza, de nehany (pl. a Quadbarrel) nem;
# a jatek ugyanis a targyat kezbe adaskor ugyis maga allitja be. Ezert a gyoker sajat forgatasat es
# poziciojat figyelmen kivul hagyjuk, es mindig ezt a rogzitett forgatast hasznaljuk.
ITEM_SPACE = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
])


def _components(game_object):
    found = {}
    for comp in game_object.m_Component:
        obj = (comp.component if hasattr(comp, "component") else comp).read()
        found[type(obj).__name__] = obj
    return found


def _lod0_object_ids(prefab_root):
    """A LODGroup megmondja, melyik csomopont melyik reszletessegi szinthez tartozik.
    Visszaad ket halmazt: a LOD0-hoz tartozo es a tobbi szinthez tartozo csomopontok."""
    lod0, other = set(), set()
    group = _components(prefab_root).get("LODGroup")
    if group is not None:
        for level, lod in enumerate(group.m_LODs):
            for entry in lod.renderers:
                renderer = (entry.renderer if hasattr(entry, "renderer") else entry).read()
                (lod0 if level == 0 else other).add(renderer.m_GameObject.path_id)
    return lod0, other


def walk(prefab_root, root_matrix):
    """Vegigmegy a prefab fajan. A gyoker sajat helyzete helyett a megadott root_matrix-ot
    hasznalja (igy lehet egy kiegeszitot a fegyver egyik hookjara "ratenni").
    Minden csomopontra visszaadja: (GameObject, a csomopont azonositoja, vilag-matrix, aktiv-e)."""
    def visit(game_object, matrix, active):
        active = active and bool(getattr(game_object, "m_IsActive", True))
        transform = _components(game_object)["Transform"]
        yield game_object, transform.m_GameObject.path_id, matrix, active
        for child_ptr in transform.m_Children:
            child = child_ptr.read()
            yield from visit(child.m_GameObject.read(), matrix @ _local_matrix(child), active)
    yield from visit(prefab_root, root_matrix, True)


# --------------------------------------------------------------------------------------------
# Geometria
# --------------------------------------------------------------------------------------------
class Surface:
    """Egy modellresz egyetlen anyaggal: pontok, UV-k, normalok, haromszogek, es a textura
    (vagy ha nincs textura, az anyag egyszinu szine). Meg Unity-koordinatakban."""

    def __init__(self, texture, texture_id, color):
        self.texture = texture          # UnityPy Texture2D vagy None
        self.texture_id = texture_id    # a textura azonositoja a csomagban (ha van)
        self.color = color              # (r, g, b) 0..1, ha nincs textura
        self.positions, self.uvs, self.normals, self.triangles = [], [], [], []

    def key(self):
        return ("tex", self.texture_id) if self.texture is not None else ("flat", self.color)


def _material_of(renderer, submesh_index):
    """Egy modellresz anyaga: (textura, textura-azonosito, szin)."""
    white = (1.0, 1.0, 1.0)
    materials = [m for m in renderer.m_Materials]
    if not materials:
        return None, None, white
    pointer = materials[min(submesh_index, len(materials) - 1)]
    if not pointer:
        return None, None, white
    material = pointer.read()
    texture, texture_id, color = None, None, white
    for key, env in material.m_SavedProperties.m_TexEnvs:
        if key == "_MainTex" and env.m_Texture:
            texture, texture_id = env.m_Texture.read(), env.m_Texture.path_id
    for key, value in material.m_SavedProperties.m_Colors:
        if key == "_Color":
            color = (round(value.r, 3), round(value.g, 3), round(value.b, 3))
    return texture, texture_id, color


def collect(prefab_root, root_matrix):
    """Osszegyujti egy prefab lathato, legreszletesebb modelljeit.
    Visszaad: (Surface-ok listaja, hookok szotara nev -> 4x4 vilag-matrix)."""
    lod0, other_lods = _lod0_object_ids(prefab_root)
    surfaces, hooks = {}, {}
    for game_object, object_id, matrix, active in walk(prefab_root, root_matrix):
        comps = _components(game_object)
        mesh_filter, renderer = comps.get("MeshFilter"), comps.get("MeshRenderer")
        if mesh_filter is None or not mesh_filter.m_Mesh or renderer is None:
            hooks.setdefault(game_object.m_Name, matrix)
            continue
        # Kihagyjuk: a kikapcsolt reszeket (pl. a tavcso lencseje), es ami csak a butitott
        # (tavolrol hasznalt) valtozathoz tartozik.
        if not active or object_id in other_lods:
            continue
        handler = MeshHandler(mesh_filter.m_Mesh.read())
        handler.process()
        rotation = matrix[:3, :3]
        normal_matrix = np.linalg.inv(rotation).T
        for submesh_index, submesh in enumerate(handler.get_triangles()):
            probe = Surface(*_material_of(renderer, submesh_index))
            surface = surfaces.setdefault(probe.key(), probe)
            # A pontokat submeshenkent ujra felvesszuk; az egyszeruseg megeri a par bajt tobbletet.
            remap = {}
            for tri in submesh:
                corners = [np.array(handler.m_Vertices[i][:3]) for i in tri]
                if np.linalg.norm(np.cross(corners[1] - corners[0], corners[2] - corners[0])) < 1e-12:
                    continue  # nulla teruletu (elfajult) haromszog, nem latszik
                new_tri = []
                for i in tri:
                    if i not in remap:
                        remap[i] = len(surface.positions)
                        surface.positions.append(rotation @ np.array(handler.m_Vertices[i][:3]) + matrix[:3, 3])
                        n = normal_matrix @ np.array(handler.m_Normals[i][:3])
                        surface.normals.append(n / max(np.linalg.norm(n), 1e-9))
                        uv = handler.m_UV0[i] if handler.m_UV0 else (0.5, 0.5)
                        surface.uvs.append((uv[0], uv[1]))
                    new_tri.append(remap[i])
                surface.triangles.append(tuple(new_tri))
    return [s for s in surfaces.values() if s.triangles], hooks


# --------------------------------------------------------------------------------------------
# Textura
# --------------------------------------------------------------------------------------------
MIN_TEXTURE_SIZE = 16


def _next_pow2(n):
    return 1 << max(0, math.ceil(math.log2(n)))


def prepare_texture(surface):
    """Elokesziti egy Surface texturajat a Minecrafthoz. Visszaad: (PIL kep, uj UV-k).

    A Minecraft egy nagy kozos kepre ("atlasz") pakolja az osszes texturat, ezert:
      - az UV-koordinatak nem loghatnak ki a 0..1 tartomanybol. Unityben ilyenkor a textura
        ismetlodik, Minecraftban a szomszed targy kepe latszana. Ha kilognak, a kepet annyiszor
        egymas melle masoljuk, ahanyszor kell, es az UV-kat ehhez igazitjuk;
      - a kep legyen negyzetes es 2-hatvany meretu;
      - a kep legyen legalabb 16x16-os. Az Unturned sok texturaja csak par keppontos szinpaletta
        (pl. 4x2), a Minecraft viszont a legkisebb textura meretehez igazitja a tavoli targyak
        elsimitasat (mipmap), es egy 2x2-es kep ezt az osszes targynal lerontana. A felnagyitas
        "legkozelebbi szomszed" modszerrel megy, igy a szinek nem mosodnak ossze.
    """
    uvs = np.array(surface.uvs, dtype=float)
    if surface.texture is None:
        r, g, b = (int(round(c * 255)) for c in surface.color)
        image = Image.new("RGBA", (MIN_TEXTURE_SIZE, MIN_TEXTURE_SIZE), (r, g, b, 255))
        return image, np.full_like(uvs, 0.5)

    image = surface.texture.image.convert("RGBA")
    w, h = image.size
    u0, v0 = math.floor(uvs[:, 0].min() + 1e-6), math.floor(uvs[:, 1].min() + 1e-6)
    need_u = max(1, math.ceil(uvs[:, 0].max() - 1e-6) - u0)
    need_v = max(1, math.ceil(uvs[:, 1].max() - 1e-6) - v0)
    size = _next_pow2(max(w * need_u, h * need_v))
    if size % w or size % h:
        raise SystemExit(f"Nem 2-hatvany meretu textura ({w}x{h}), ezt kezzel kell atmeretezni.")
    tiles_u, tiles_v = size // w, size // h
    image = Image.fromarray(np.tile(np.array(image), (tiles_v, tiles_u, 1)), "RGBA")
    if size < MIN_TEXTURE_SIZE:
        image = image.resize((MIN_TEXTURE_SIZE, MIN_TEXTURE_SIZE), Image.NEAREST)
    new_uvs = np.column_stack(((uvs[:, 0] - u0) / tiles_u, (uvs[:, 1] - v0) / tiles_v))
    return image, new_uvs


# --------------------------------------------------------------------------------------------
# Hang
# --------------------------------------------------------------------------------------------
def write_ogg(path, clip):
    """Unity AudioClip -> mono OGG Vorbis. Visszaadja a hang hosszat masodpercben.
    Mono kell, mert a Minecraft csak a mono hangokat helyezi el terben (halkul a tavolsaggal,
    jobbrol/balrol szol)."""
    wav_bytes = next(iter(clip.samples.values()))
    data, rate = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, data.mean(axis=1), rate, format="OGG", subtype="VORBIS")
    return len(data) / rate
