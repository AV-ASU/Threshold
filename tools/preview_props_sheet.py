"""Isolated prop contact sheet -- CLAUDE.md scene-dressing process step 2.

Renders any decoration/prop kinds through the REAL tilt camera against a
plain ground with a wall-height ruler, so a kind is judged by what it
DRAWS, never by what its name suggests ("pillar" was a Roman column,
"shelf" a bookcase). SOLID_PROPS kinds project as volumes; anything else
falls back to its flat Decoration draw.

    python tools/preview_props_sheet.py shoring_frame spoil_heap ore_cart
    python tools/preview_props_sheet.py "shoring_frame:seed=3,ang=1.57,span=64"

Output: /tmp/props_sheet.png (view it; that's the point).
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame

from rendering.camera import Camera
from rendering.props import SOLID_PROPS, draw_prop_solid
from entities.decoration import Decoration
from scenes.base import _TILT_WALL_RISE


def _parse(spec):
    """'kind' or 'kind:seed=3,ang=1.57,span=64' -> (kind, kwargs)."""
    if ":" not in spec:
        return spec, {}
    kind, _, args = spec.partition(":")
    kw = {}
    for part in args.split(","):
        k, _, v = part.partition("=")
        kw[k.strip()] = float(v) if "." in v else int(v)
    return kind, kw


def main():
    specs = sys.argv[1:] or ["shoring_frame", "spoil_heap", "ore_cart"]
    pygame.init()
    pygame.display.set_mode((1, 1))
    cell = 190
    W, H = cell * (len(specs) + 1) + 40, 320
    surf = pygame.Surface((W, H))
    surf.fill((38, 36, 42))
    cam = Camera(pitch=math.radians(55), scale=2.8, origin=(0, 0))
    font = pygame.font.Font(None, 20)
    x = 110
    for spec in specs:
        kind, kw = _parse(spec)
        cam.origin = (x, 220)
        d = Decoration(0, 0, kind, **kw)
        if kind in SOLID_PROPS:
            draw_prop_solid(surf, cam, d)
        else:
            d.draw(surf, -x, -220)          # flat draw at the anchor
        surf.blit(font.render(spec[:24], True, (220, 220, 220)),
                  (x - 60, 280))
        x += cell
    # the wall-height ruler: judge every prop against what a wall rises to
    cam.origin = (x, 220)
    p0 = cam.project(0, 0, 0)
    p1 = cam.project(0, 0, _TILT_WALL_RISE)
    pygame.draw.line(surf, (150, 150, 160), p0, p1, 2)
    surf.blit(font.render(f"wall {_TILT_WALL_RISE}", True, (220, 220, 220)),
              (x - 30, 280))
    out = "/tmp/props_sheet.png"
    pygame.image.save(surf, out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
