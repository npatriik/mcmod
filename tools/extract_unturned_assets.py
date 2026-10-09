#!/usr/bin/env python3
"""
Unturned -> Minecraft asset-kinyero.

Mit csinal:
  1. Megnyitja az Unturned fo asset-csomagjat (Bundles/core.masterbundle). Ez egy
     Unity "asset bundle": ebben vannak a modellek, texturak es hangok.
  2. A lenti ITEMS listaban felsorolt targyakhoz kikeresi a modellt (mesh), a
     texturat es a hangokat.
  3. Atalakitja oket olyan formatumba, amit a Minecraft / NeoForge be tud tolteni:
        modell   -> .obj + .mtl   (assets/<modid>/models/item/)
        textura  -> .png          (assets/<modid>/textures/item/)
        hang     -> .ogg (mono)   (assets/<modid>/sounds/)

Futtatas (a mod mappajabol):
    pip install UnityPy numpy pillow soundfile
    python tools/extract_unturned_assets.py ^
        --unturned "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Unturned" ^
        --out src/main/resources/assets/unturnedcraft

Uj targy hozzaadasa: vegyel fel egy uj sort az ITEMS listaba. Azt, hogy egy
targynak mi az utvonala a csomagon belul, a Bundles/core.masterbundle.manifest
szoveges fajlbol tudod kikeresni (pl. keress ra a fegyver nevere).
"""
import argparse
import io
import math
import os
import sys

import numpy as np
import soundfile as sf
import UnityPy
from PIL import Image
from UnityPy.helpers.MeshHelper import MeshHandler

# A csomagon belul minden utvonal ezzel kezdodik (lasd Bundles/MasterBundle.dat).
BUNDLE_PREFIX = "assets/coremasterbundle/"

# Mit szedjunk ki. "name" = ahogy a Minecraft modban hivjuk a targyat.
ITEMS = [
    {
        "name": "colt",
        "prefab": "items/guns/colt/item.prefab",
        "sounds": {
            "colt/shoot": "items/guns/colt/shoot.mp3",
            "colt/reload": "items/guns/colt/reload.mp3",
            "colt/hammer": "items/guns/colt/hammer.mp3",
        },
    },
    {
        "name": "colt_magazine",
        "prefab": "items/magazines/colt_7/item.prefab",
        "sounds": {},
    },
]


# --------------------------------------------------------------------------
# Unity prefab bejarasa
# --------------------------------------------------------------------------
def quat_to_matrix(q):
    """Unity kvaternio (x, y, z, w) -> 3x3 forgatasi matrix."""
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def local_matrix(transform, is_root):
    """Egy Transform helyi 4x4 matrixa. A gyoker poziciojat eldobjuk (az csak azt
    mondja meg, hol allt a targy a keszito Unity-jeleneteben), a forgatasat megtartjuk."""
    m = np.identity(4)
    s = transform.m_LocalScale
    m[:3, :3] = quat_to_matrix(transform.m_LocalRotation) @ np.diag([s.x, s.y, s.z])
    if not is_root:
        p = transform.m_LocalPosition
        m[:3, 3] = [p.x, p.y, p.z]
    return m


def walk(game_object, parent_matrix=None):
    """Vegigmegy a prefab faszerkezeten. Minden csomopontra visszaadja:
    (nev, vilag-matrix, mesh vagy None, a textura vagy None)."""
    transform, mesh, texture = None, None, None
    for comp in game_object.m_Component:
        obj = (comp.component if hasattr(comp, "component") else comp).read()
        kind = type(obj).__name__
        if kind == "Transform":
            transform = obj
        elif kind == "MeshFilter" and obj.m_Mesh:
            mesh = obj.m_Mesh.read()
        elif kind == "MeshRenderer":
            for mat_ptr in obj.m_Materials:
                if not mat_ptr:
                    continue
                for key, env in mat_ptr.read().m_SavedProperties.m_TexEnvs:
                    if key == "_MainTex" and env.m_Texture:
                        texture = env.m_Texture.read()
    is_root = parent_matrix is None
    world = local_matrix(transform, is_root)
    if not is_root:
        world = parent_matrix @ world
    yield game_object.m_Name, world, mesh, texture
    for child in transform.m_Children:
        yield from walk(child.read().m_GameObject.read(), world)


# --------------------------------------------------------------------------
# Koordinata-rendszerek
# --------------------------------------------------------------------------
# Unity: balkezes rendszer, Y felfele. Az Unturned fegyverek csove a prefabban a -Z fele nez.
# Minecraft targymodell: jobbkezes rendszer, Y felfele, es az a kenyelmes, ha a cso
# szinten a -Z (eszak) fele nez, mert kezben tartva az "elore" irany a -Z.
# Balkezesbol jobbkezest az X tengely tukrozesevel kapunk; ilyenkor a haromszogek
# korbejarasi iranyat is meg kell forditani, kulonben kifordulna a modell.
def unity_to_minecraft(vectors):
    out = np.array(vectors, dtype=float)
    out[:, 0] *= -1
    return out


def collect_geometry(prefab_root):
    """Osszegyujti a prefab legreszletesebb modelljet Minecraft-koordinatakban.
    Visszaad: (pontok, uv-k, normalok, haromszogek, textura, segedpontok)."""
    positions, uvs, normals, triangles = [], [], [], []
    texture, hooks = None, {}
    for name, world, mesh, tex in walk(prefab_root):
        if mesh is None:
            # Ures csomopont = "hook": pl. Barrel (csotorkolat), Sight, Magazine...
            hooks[name] = world[:3, 3].copy()
            continue
        # A Model_1, Model_2... a tavolrol hasznalt, butitott valtozatok (LOD). Nem kellenek.
        if name.startswith("Model_") and name != "Model_0":
            continue
        handler = MeshHandler(mesh)
        handler.process()
        base = len(positions)
        rot = world[:3, :3]
        for v in handler.m_Vertices:
            positions.append(rot @ np.array(v[:3]) + world[:3, 3])
        for n in handler.m_Normals:
            normals.append(rot @ np.array(n[:3]))
        for uv in handler.m_UV0:
            uvs.append((uv[0], uv[1]))
        for submesh in handler.get_triangles():
            for a, b, c in submesh:
                va, vb, vc = (np.array(handler.m_Vertices[i][:3]) for i in (a, b, c))
                if np.linalg.norm(np.cross(vb - va, vc - va)) < 1e-12:
                    continue  # nulla teruletu (elfajult) haromszog, nem latszik
                triangles.append((base + c, base + b, base + a))  # forditott korbejaras
        texture = tex or texture
    positions = unity_to_minecraft(positions)
    normals = unity_to_minecraft(normals)
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    hooks = {k: unity_to_minecraft([v])[0] for k, v in hooks.items()}
    return positions, np.array(uvs, dtype=float), normals, triangles, texture, hooks


# --------------------------------------------------------------------------
# Textura
# --------------------------------------------------------------------------
def next_pow2(n):
    return 1 << max(0, math.ceil(math.log2(n)))


def prepare_texture(texture, uvs):
    """A Minecraft egy nagy kozos kepre ("atlasz") pakolja az osszes texturat, ezert
    egy modell UV-koordinatai nem loghatnak ki a 0..1 tartomanybol (Unityben ilyenkor
    a textura ismetlodik, Minecraftban a szomszed targy kepe latszana). Ha kilognak,
    a kepet annyiszor egymas melle masoljuk, ahanyszor kell, es az UV-kat ehhez
    igazitjuk. Kozben a kepet negyzetesre es 2-hatvany meretre hozzuk."""
    img = texture.image.convert("RGBA")
    w, h = img.size
    u0, v0 = math.floor(uvs[:, 0].min()), math.floor(uvs[:, 1].min())
    need_u = max(1, math.ceil(uvs[:, 0].max()) - u0)
    need_v = max(1, math.ceil(uvs[:, 1].max()) - v0)
    size = next_pow2(max(w * need_u, h * need_v))
    if size % w or size % h:
        raise SystemExit(f"Nem 2-hatvany meretu textura ({w}x{h}), ezt kezzel kell atmeretezni.")
    tiles_u, tiles_v = size // w, size // h
    tiled = Image.fromarray(np.tile(np.array(img), (tiles_v, tiles_u, 1)), "RGBA")
    new_uvs = np.column_stack(((uvs[:, 0] - u0) / tiles_u, (uvs[:, 1] - v0) / tiles_v))
    return tiled, new_uvs


# --------------------------------------------------------------------------
# Kiiras
# --------------------------------------------------------------------------
def write_obj(path, name, positions, uvs, normals, triangles):
    lines = [
        f"# Generalta: tools/extract_unturned_assets.py ({name})",
        f"mtllib {name}.mtl",
        f"o {name}",
    ]
    lines += ["v %.6f %.6f %.6f" % tuple(p) for p in positions]
    lines += ["vt %.6f %.6f" % tuple(t) for t in uvs]
    lines += ["vn %.6f %.6f %.6f" % tuple(n) for n in normals]
    lines.append(f"usemtl {name}")
    # OBJ-ben a sorszamozas 1-tol indul; pont/uv/normal indexe nalunk ugyanaz.
    lines += ["f " + " ".join(f"{i + 1}/{i + 1}/{i + 1}" for i in tri) for tri in triangles]
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_mtl(path, name):
    # A "#texture" nem fajlnev, hanem hivatkozas: a modell .json fajljanak "textures"
    # reszeben a "texture" nevu bejegyzes mondja meg, melyik kep tartozik ide.
    with open(path, "w", newline="\n") as f:
        f.write(f"newmtl {name}\nKa 0 0 0\nKd 1 1 1\nmap_Kd #texture\n")


def write_ogg(path, clip):
    """Unity AudioClip -> mono OGG Vorbis. Mono kell, mert a Minecraft csak a mono
    hangokat helyezi el terben (halkul a tavolsaggal, jobbrol/balrol szol)."""
    wav_bytes = next(iter(clip.samples.values()))
    data, rate = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=True)
    sf.write(path, data.mean(axis=1), rate, format="OGG", subtype="VORBIS")
    return len(data) / rate


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unturned", required=True, help="az Unturned telepitesi mappaja")
    ap.add_argument("--out", required=True, help="a mod assets/<modid> mappaja")
    args = ap.parse_args()

    bundle = os.path.join(args.unturned, "Bundles", "core.masterbundle")
    print("Csomag betoltese:", bundle)
    env = UnityPy.load(bundle)

    def asset(rel_path):
        key = BUNDLE_PREFIX + rel_path
        if key not in env.container:
            raise SystemExit("Nincs ilyen a csomagban: " + key)
        return env.container[key].read()

    models_dir = os.path.join(args.out, "models", "item")
    textures_dir = os.path.join(args.out, "textures", "item")
    sounds_dir = os.path.join(args.out, "sounds")
    for d in (models_dir, textures_dir):
        os.makedirs(d, exist_ok=True)

    for item in ITEMS:
        name = item["name"]
        positions, uvs, normals, triangles, texture, hooks = collect_geometry(asset(item["prefab"]))
        image, uvs = prepare_texture(texture, uvs)

        # A Minecraft a targymodelleket a (0.5, 0.5, 0.5) pont korul forgatja/meretezi,
        # ezert a modell befoglalo dobozanak kozepet oda toljuk. 1 egyseg = 1 blokk.
        lo, hi = positions.min(axis=0), positions.max(axis=0)
        shift = 0.5 - (lo + hi) / 2
        positions = positions + shift

        write_obj(os.path.join(models_dir, name + ".obj"), name, positions, uvs, normals, triangles)
        write_mtl(os.path.join(models_dir, name + ".mtl"), name)
        image.save(os.path.join(textures_dir, name + ".png"))

        size = hi - lo
        print(f"\n[{name}] {len(positions)} pont, {len(triangles)} haromszog, textura {image.size[0]}x{image.size[1]}")
        print("  meret (X szelesseg, Y magassag, Z hossz) blokkban: %.3f %.3f %.3f" % tuple(size))
        for hook, pos in sorted(hooks.items()):
            print("  hook %-13s %.3f %.3f %.3f" % ((hook,) + tuple(pos + shift)))

        for sound_name, clip_path in item["sounds"].items():
            target = os.path.join(sounds_dir, sound_name + ".ogg")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            seconds = write_ogg(target, asset(clip_path))
            print(f"  hang {sound_name}.ogg  ({seconds:.2f} mp)")

    print("\nKesz.")


if __name__ == "__main__":
    sys.exit(main())
