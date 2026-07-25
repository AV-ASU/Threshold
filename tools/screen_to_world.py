"""Turn SCREEN positions in a capture back into WORLD TILES.

    python tools/screen_to_world.py <scene> --facing S [--ev N] [--px X --py Y] \
        --at 60,245 --at 500,240 ...

Prints the world tile under each screen point, plus what is on that tile.
`--grid` instead writes an overlay PNG of the same view with tile coordinates
drawn on it, so a scene can be discussed in tile numbers.

**Why this exists.** The maintainer marks up screenshots -- "put a light on
every X" -- and the only way to act on that is to know which tile each mark
is over. Under the oblique tilt that is not eyeballable: the view is yawed,
foreshortened, and the same screen y covers very different world rows
depending on depth. Guessing produced a lamp rhythm that looked right and
matched none of the marks. This inverts the projection by brute force
(project every tile centre through the real camera, take the nearest), so a
marked-up screenshot becomes a tile list in one step.

The camera is set up EXACTLY as tools/capture_facings.py does it, including
the explicit `camera.yaw` assignment that ad-hoc render paths forget -- get
that wrong and every answer is silently rotated.
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
from tools.capture_world import _boot_game
from systems.look_control import wrap
from scenes.base import TILE

HEADINGS = {"N": -math.pi / 2, "E": 0.0, "S": math.pi / 2, "W": math.pi}
FACING_VEC = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}


def setup(g, scene, facing, ev=0, px=None, py=None):
    """Boot the exact view a capture produced, so the inverse is meaningful."""
    if ev:
        g.save.set_arg("evidence", [{"name": f"s2w{i}", "content": "x"}
                                    for i in range(ev)])
    g.load_scene_now(scene)
    h = HEADINGS[facing]
    g.look.body = wrap(h)
    g.look.aim = wrap(h)
    g.look.cam_yaw = wrap(h + math.pi / 2)
    g.camera.yaw = g.look.cam_yaw          # the line ad-hoc paths forget
    try:
        g.player.facing = FACING_VEC[facing]
    except Exception:
        pass
    if px is not None:
        g.player.x = px
    if py is not None:
        g.player.y = py
    g._update_camera(snap=True)
    g.camera.yaw = g.look.cam_yaw
    return g.scene


def project_all(g, sc):
    """[(sx, sy, tx, ty)] for every tile centre in the scene, at ground level."""
    out = []
    for ty in range(sc.h):
        for tx in range(sc.w):
            sx, sy = g.camera.project(tx * TILE + TILE // 2,
                                      ty * TILE + TILE // 2, 0)
            out.append((sx, sy, tx, ty))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--facing", default="N", choices=list(HEADINGS))
    ap.add_argument("--ev", type=int, default=0)
    ap.add_argument("--px", type=float, default=None)
    ap.add_argument("--py", type=float, default=None)
    ap.add_argument("--at", action="append", default=[],
                    metavar="X,Y", help="a screen point; repeatable")
    ap.add_argument("--grid", metavar="OUT.png",
                    help="write a tile-coordinate overlay of this view instead")
    args = ap.parse_args()

    g = _boot_game()
    sc = setup(g, args.scene, args.facing, args.ev, args.px, args.py)
    pts = project_all(g, sc)

    if args.grid:
        _write_grid(g, sc, pts, args.grid)
        return

    print(f"{args.scene} facing {args.facing} (ev{args.ev}), "
          f"player at tile ({int(g.player.x//TILE)},{int(g.player.y//TILE)})\n")
    print(f"  {'screen':>12s}  {'tile':>9s}  {'floor':>6s}  object  distance")
    for spec in args.at:
        sx, sy = (float(v) for v in spec.split(","))
        px_, py_, tx, ty = min(pts, key=lambda p: (p[0] - sx) ** 2
                               + (p[1] - sy) ** 2)
        d = math.hypot(px_ - sx, py_ - sy)
        fl = sc.floor[ty][tx]
        ob = sc.objects[ty][tx]
        print(f"  {f'{sx:.0f},{sy:.0f}':>12s}  {f'({tx},{ty})':>9s}  "
              f"{fl!r:>6s}  {ob!r:>6s}  {d:.0f}px")


def _write_grid(g, sc, pts, out):
    from PIL import Image, ImageDraw
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    g.draw_world()
    im = Image.frombytes("RGB", surf.get_size(),
                         pygame.image.tostring(surf, "RGB"))
    d = ImageDraw.Draw(im)
    for sx, sy, tx, ty in pts:
        if not (0 <= sx < im.width and 0 <= sy < im.height):
            continue
        if tx % 4 or ty % 4:
            continue
        d.line([(sx - 2, sy), (sx + 2, sy)], fill=(255, 210, 90))
        d.line([(sx, sy - 2), (sx, sy + 2)], fill=(255, 210, 90))
        d.text((sx + 3, sy - 5), f"{tx},{ty}", fill=(255, 230, 140))
    im.save(out)
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
