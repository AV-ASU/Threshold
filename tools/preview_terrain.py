"""LOOK at the GROUND and what grows on it, in isolation.

    python tools/preview_terrain.py                  # every floor char
    python tools/preview_terrain.py --chars g d ";"  # just these
    python tools/preview_terrain.py --seams          # char-vs-char boundaries
    python tools/preview_terrain.py --plants         # trees / corn / billboards

The terrain equivalent of `preview_props_sheet.py`, and it exists for the
same reason: a floor char kept being judged from a whole-scene capture, where
it is four pixels of a scene full of props, actors, fringes and shadow. Two
things hide completely at that size and both have shipped:

* **A char whose colour does not sit with its neighbours.** Marsh mud `;` is
  a brown near-black scattered as ISOLATED SINGLE TILES through green grass,
  which reads as square black holes in the lawn -- the maintainer's "black
  patches in the grass at certain angles". At map zoom it looks like shadow.
* **A char with no texture at all.** Under the tilt the ground is most of the
  frame, so a flat fill reads as flat fill across half the screen. That is
  invisible in a thumbnail and glaring at 8x.

So this builds a synthetic scene -- blocks of each char, or a grid of every
char meeting every other char with `--seams` -- and renders it through the
REAL tilt camera at four facings. Seams matter separately from fills: tiles
are cached BY CHAR, so no tile knows its neighbours, and every boundary
between two chars is a hard step unless something is drawn across it.

Output: /tmp/terrain_<tag>/sheet.png
"""
import os
import sys
import math
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame

# The ground chars worth judging together: the outdoor palette. Interior
# floors and the void are excluded -- they are never seen beside these.
OUTDOOR = ["g", "d", ";", ":", "P", "_"]
PLANTS = ["T", "p", "c"]
BLOCK = 5          # tiles per patch side
PAD = 1


def _grids(chars, mode):
    """(floor_rows, object_rows) for the synthetic scene."""
    if mode == "seams":
        # every char against every other, so each boundary is visible once
        n = len(chars)
        w = n * (BLOCK + PAD) + PAD
        h = n * (BLOCK + PAD) + PAD
        floor = [[chars[0]] * w for _ in range(h)]
        for r, a in enumerate(chars):
            for c, b in enumerate(chars):
                for y in range(BLOCK):
                    for x in range(BLOCK):
                        ty = PAD + r * (BLOCK + PAD) + y
                        tx = PAD + c * (BLOCK + PAD) + x
                        # each cell is half a, half b -- one shared seam
                        floor[ty][tx] = a if x < BLOCK // 2 else b
        obj = [["."] * w for _ in range(h)]
        return floor, obj
    if mode == "plants":
        w = len(chars) * (BLOCK + PAD) + PAD + 6
        h = BLOCK + 2 * PAD + 6
        floor = [["g"] * w for _ in range(h)]
        obj = [["."] * w for _ in range(h)]
        for c, ch in enumerate(chars):
            for y in range(BLOCK):
                for x in range(BLOCK):
                    if (x + y) % 2 == 0:
                        obj[PAD + 3 + y][PAD + 3 + c * (BLOCK + PAD) + x] = ch
        return floor, obj
    cols = min(3, len(chars))
    rows = (len(chars) + cols - 1) // cols
    w = cols * (BLOCK + PAD) + PAD
    h = rows * (BLOCK + PAD) + PAD
    floor = [["g"] * w for _ in range(h)]
    obj = [["."] * w for _ in range(h)]
    for i, ch in enumerate(chars):
        r, c = divmod(i, cols)
        for y in range(BLOCK):
            for x in range(BLOCK):
                floor[PAD + r * (BLOCK + PAD) + y][
                    PAD + c * (BLOCK + PAD) + x] = ch
    return floor, obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", nargs="*", default=None)
    ap.add_argument("--seams", action="store_true")
    ap.add_argument("--plants", action="store_true")
    ap.add_argument("--zoom", type=float, default=2.0)
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--tag", default="look")
    args = ap.parse_args()

    mode = "seams" if args.seams else ("plants" if args.plants else "fill")
    chars = args.chars or (PLANTS if mode == "plants" else OUTDOOR)
    floor, obj = _grids(chars, mode)

    from scenes.base import Scene
    import scenes as _scenes
    key = "_terrain_preview"
    sc_floor = ["".join(r) for r in floor]
    sc_obj = ["".join(r) for r in obj]
    _scenes.SCENE_BUILDERS[key] = lambda: Scene(key, sc_floor, sc_obj,
                                                music=None)

    import systems.game as _sg
    _sg.TILT_ZOOM = _sg.TILT_ZOOM * args.zoom
    from tools.capture_world import _boot_game
    from tools.capture_facings import FACINGS, capture
    from constants import TILE

    g = _boot_game()
    px = (len(floor[0]) / 2.0) * TILE
    py = (len(floor) / 2.0) * TILE
    shots = {}
    for name, heading, fv in FACINGS:
        shots[name] = capture(g, key, heading, fv, px, py,
                              bright=not args.dark)

    out = f"/tmp/terrain_{args.tag}"
    os.makedirs(out, exist_ok=True)
    from PIL import Image, ImageDraw
    ims = [(n, Image.frombytes("RGB", shots[n].get_size(),
                               pygame.image.tostring(shots[n], "RGB")))
           for n, _h, _v in FACINGS]
    w, h, lab, pad = ims[0][1].width, ims[0][1].height, 22, 8
    sheet = Image.new("RGB", (w * 2 + pad * 3, (h + lab) * 2 + pad * 3),
                      (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        r, c = divmod(i, 2)
        x, y = pad + c * (w + pad), pad + r * (h + lab)
        d.text((x + 2, y + 4),
               f"terrain {mode} {' '.join(chars)}  x{args.zoom:g}  facing {n}",
               fill=(232, 232, 180))
        sheet.paste(im, (x, y + lab))
    sheet.save(f"{out}/sheet.png")
    print(f"wrote {out}/sheet.png")
    print("  order (row-major): " + ", ".join(chars))


if __name__ == "__main__":
    main()
