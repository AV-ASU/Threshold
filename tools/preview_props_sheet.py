"""Isolated prop contact sheet -- CLAUDE.md scene-dressing process step 2.

Renders any decoration/prop kinds through the REAL tilt camera against a
plain ground with a wall-height ruler, so a kind is judged by what it
DRAWS, never by what its name suggests ("pillar" was a Roman column,
"shelf" a bookcase). SOLID_PROPS kinds project as volumes; anything else
falls back to its flat Decoration draw.

    python tools/preview_props_sheet.py shoring_frame spoil_heap ore_cart
    python tools/preview_props_sheet.py "shoring_frame:seed=3,ang=1.57,span=64"
    python tools/preview_props_sheet.py mailbox --flat      # one dead-on view

**IT TURNTABLES BY DEFAULT.** VISION's all-directions rule applies to a PROP
exactly as it does to a scene, and for the same reason: what hides on one
angle is the whole failure mode. The first version of this tool built its
camera with `pitch=55` and never set `yaw`, so every prop was drawn dead-on
at yaw 0 -- one face, no corner, no top. Under that view a real volume and a
flat card are indistinguishable, which is precisely backwards for a tool
whose job is telling them apart. (Same defect as the one `capture_facings.py`
exists for; both came from a camera whose yaw was never assigned.)

Each kind now gets a ROW of four yaws, and reading that row catches the two
things that keep going wrong:

* **A part placed off `cam.yaw` instead of the deco's own yaw** swings around
  the object as the view turns, and disappears from some headings entirely.
  The mailbox's flag, the woodpile's cut ends and the stoop's treads were all
  built that way and all three read fine dead-on.
* **A camera-facing card** holds its outline as the row turns. Right for
  fire, a glow, or thin foliage; a bug for anything man-made (VISION trap #1).

Both are judged BY EYE from the sheet. An automatic detector was tried and
removed: byte-identity fails because many prop draws use unseeded `random`
for speckle, and silhouette comparison fails because the pitch flatten means
even a deliberately camera-locked box changes outline as the view turns. It
could not be made to fail on a real standee, so it went rather than ship a
green light that means nothing.

Output: /tmp/props_sheet.png (view it; that's the point).
"""
import os
import sys
import math
import argparse
import textwrap

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame

from rendering.camera import Camera
from rendering.props import draw_prop_solid
from rendering.assemblies import ASSEMBLIES, base
from rendering.assembly import validate
from rendering import references as R
from entities.decoration import Decoration
from scenes.base import _TILT_WALL_RISE

# The turntable. Never 0: a prop square to the camera shows one face and
# reads flat no matter how solid it really is.
YAWS = (0.65, 1.44, 2.36, 3.93)


def _parse(spec):
    """'kind' or 'kind:seed=3,ang=1.57,axe=True' -> (kind, kwargs).

    BOOLEANS matter here: most of the yard vocabulary is variant factories
    switched by a flag (a mailbox that is `full`, a fence bay whose wire is
    down, a genset that is not `running`), and the whole point of previewing
    a kind before placing it is to see the variant the scene will actually
    ask for. Reading `running=False` as an int used to crash the tool, which
    meant the only variant anybody ever looked at was the default."""
    if ":" not in spec:
        return spec, {}
    kind, _, args = spec.partition(":")
    kw = {}
    for part in args.split(","):
        k, _, v = part.partition("=")
        v = v.strip()
        if v.lower() in ("true", "false"):
            kw[k.strip()] = (v.lower() == "true")
            continue
        try:
            kw[k.strip()] = float(v) if "." in v else int(v)
        except ValueError:
            kw[k.strip()] = v
    return kind, kw


def _cell(surf, cam, x, y, kind, kw, yaw):
    cam.origin = (x, y)
    cam.yaw = yaw
    d = Decoration(0, 0, kind, **kw)
    # draw_prop_solid handles BOTH paths -- an assembly if the kind has one,
    # otherwise its hand-written function -- and returns False only for a
    # flat decal, which falls through to the Decoration draw.
    if not draw_prop_solid(surf, cam, d):
        d.draw(surf, -x, -y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="*",
                    default=["shoring_frame", "spoil_heap", "ore_cart"])
    ap.add_argument("--flat", action="store_true",
                    help="one dead-on view per kind (the OLD behaviour; only "
                         "useful for reading a flat decal, never a volume)")
    ap.add_argument("--scale", type=float, default=2.8)
    args = ap.parse_args()
    specs = args.specs or ["shoring_frame", "spoil_heap", "ore_cart"]
    yaws = (0.0,) if args.flat else YAWS

    pygame.init()
    pygame.display.set_mode((1, 1))
    cw, ch = 190, 240
    W = cw * len(yaws) + 300
    H = ch * len(specs) + 30
    surf = pygame.Surface((W, H))
    surf.fill((38, 36, 42))
    cam = Camera(pitch=math.radians(55), scale=args.scale, origin=(0, 0))
    font = pygame.font.Font(None, 20)

    for r, spec in enumerate(specs):
        kind, kw = _parse(spec)
        y = 40 + r * ch
        for c, yaw in enumerate(yaws):
            x = 240 + c * cw
            _cell(surf, cam, x, y + 130, kind, kw, yaw)
            surf.blit(font.render(f"yaw {math.degrees(yaw):.0f}", True,
                                  (128, 126, 134)), (x - 24, y + 150))
        surf.blit(font.render(spec[:22], True, (232, 232, 180)), (12, y + 30))
        # THE REFERENCE, printed beside the render. This is the whole 5-to-1
        # mechanism: a wrong proportion is visible at the moment of judging
        # rather than three revisions later.
        small = pygame.font.Font(None, 17)
        lines = R.describe(kind, width=30)
        asm = base(kind) if kind in ASSEMBLIES else None
        if asm is not None:
            pm = R.check_proportion(kind, asm)
            sm = R.check_stature(kind, asm)
            vm = validate(asm, kind)
            lines.append("")
            lines.append("PROPORTION: " + ("off -- see below" if pm else "ok"))
            if pm:
                lines += textwrap.wrap(pm, 30)
            b_ = asm.bounds()
            lines.append(f"STANDS {b_[5] - b_[2]:.1f} tall (player 20, wall 26)")
            if sm:
                lines += textwrap.wrap(sm, 30)
            for m in vm:
                lines += textwrap.wrap("! " + m, 30)
        for li, ln in enumerate(lines[:11]):
            surf.blit(small.render(ln[:40], True, (150, 148, 156)),
                      (12, y + 50 + li * 15))

    # the wall-height ruler: judge every prop against what a wall rises to
    cam.origin = (W - 50, 40 + 130)
    cam.yaw = yaws[0]
    p0 = cam.project(0, 0, 0)
    p1 = cam.project(0, 0, _TILT_WALL_RISE)
    pygame.draw.line(surf, (150, 150, 160), p0, p1, 2)
    surf.blit(font.render(f"wall {_TILT_WALL_RISE}", True, (200, 200, 208)),
              (W - 110, 40 + 172))

    out = "/tmp/props_sheet.png"
    pygame.image.save(surf, out)
    print(f"wrote {out}")
    if not args.flat:
        print("  Read the ROW, not one cell: a part that swings around the "
              "object (or vanishes)\n  is placed off cam.yaw instead of the "
              "deco's own yaw; an outline that never\n  changes is a "
              "camera-facing card (fine for flame/glow/foliage, a bug "
              "otherwise).")


if __name__ == "__main__":
    main()
