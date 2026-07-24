"""Four-facing capture for ONE scene -- the VISION.md look-pass harness.

    python tools/capture_facings.py <scene_key> [--px X --py Y] [--bright] [--tag T]

Writes /tmp/facings_<tag>/<key>_{N,E,S,W}.png plus a labelled contact sheet
`<key>_sheet.png`, and PRINTS a per-pair difference report.

**Why this tool exists.** `Game._update_camera` sets the camera POSITION only,
never its yaw -- the yaw is copied from `look.cam_yaw` inside `_update_look`,
which the ad-hoc render path never runs. Skip the explicit `camera.yaw = ...`
and every "facing" renders at yaw 0, so a four-facing sheet is NORTH four
times. That has now shipped twice as "verified all four facings" (VISION.md
records the first; the lost-space islands were the second). So this tool sets
the yaw itself AND asserts the frames actually differ -- if the yaw silently
stops taking, the run FAILS instead of handing back four norths.

`--bright` drops the sight cone + film grade for clean geometry inspection;
without it you get the real player view (dark overlay, fog, grade).
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

import random
import pygame
from tools.capture_world import _boot_game
from systems.look_control import wrap

# heading per facing; the camera sits behind it (heading + pi/2)
FACINGS = (("N", -math.pi / 2, (0, -1)), ("E", 0.0, (1, 0)),
           ("S", math.pi / 2, (0, 1)), ("W", math.pi, (-1, 0)))
SEED = 7


def capture(g, key, heading, facing_vec, px=None, py=None, bright=False):
    random.seed(SEED)
    try:
        import numpy as np
        np.random.seed(SEED)
    except Exception:
        pass
    g.load_scene_now(key)
    g.look.body = wrap(heading)
    g.look.aim = wrap(heading)
    g.look.cam_yaw = wrap(heading + math.pi / 2)
    # THE LINE THIS TOOL EXISTS FOR: _update_camera never touches yaw.
    g.camera.yaw = g.look.cam_yaw
    try:
        g.player.facing = facing_vec
    except Exception:
        pass
    if px is not None:
        g.player.x = px
    if py is not None:
        g.player.y = py
    g._update_camera(snap=True)
    g.camera.yaw = g.look.cam_yaw          # re-assert (snap may re-run lerps)
    if bright:
        g._draw_dark = lambda: None
        g._draw_sight_fog = lambda: None
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    try:
        from scenes import base as _sb
        _sb._GREY_CACHE["frame"] = None
    except Exception:
        pass
    g.draw_world()
    return surf.copy()


def _frac_diff(a, b):
    """Fraction of pixels differing between two same-size Surfaces."""
    from PIL import Image, ImageChops
    ia = Image.frombytes("RGB", a.get_size(), pygame.image.tostring(a, "RGB"))
    ib = Image.frombytes("RGB", b.get_size(), pygame.image.tostring(b, "RGB"))
    diff = ImageChops.difference(ia, ib)
    changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
    return changed / float(ia.width * ia.height)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--px", type=float, default=None)
    ap.add_argument("--py", type=float, default=None)
    ap.add_argument("--bright", action="store_true")
    ap.add_argument("--tag", default="look")
    args = ap.parse_args()

    out = f"/tmp/facings_{args.tag}"
    os.makedirs(out, exist_ok=True)
    g = _boot_game()
    shots = {}
    for name, heading, fv in FACINGS:
        shots[name] = capture(g, args.scene, heading, fv,
                              args.px, args.py, args.bright)
        pygame.image.save(shots[name], f"{out}/{args.scene}_{name}.png")
        print(f"  wrote {out}/{args.scene}_{name}.png")

    # SELF-CHECK: consecutive facings must differ, or the yaw never took.
    print("\n  facing-difference report (N-E, E-S, S-W, W-N):")
    ok = True
    order = ["N", "E", "S", "W", "N"]
    for i in range(4):
        a, b = order[i], order[i + 1]
        f = _frac_diff(shots[a], shots[b])
        flag = "OK" if f > 0.02 else "IDENTICAL -- YAW NEVER TOOK"
        if f <= 0.02:
            ok = False
        print(f"    {a}->{b}: {f*100:6.2f}% of pixels differ   {flag}")

    from PIL import Image, ImageDraw
    ims = [(n, Image.frombytes("RGB", shots[n].get_size(),
                               pygame.image.tostring(shots[n], "RGB")))
           for n, _h, _v in FACINGS]
    w, h, lab, pad = ims[0][1].width, ims[0][1].height, 22, 8
    sheet = Image.new("RGB", (w * 2 + pad * 3, (h + lab) * 2 + pad * 3), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        r, c = divmod(i, 2)
        x, y = pad + c * (w + pad), pad + r * (h + lab)
        d.text((x + 2, y + 4), f"{args.scene}  facing {n}", fill=(232, 232, 180))
        sheet.paste(im, (x, y + lab))
    sheet.save(f"{out}/{args.scene}_sheet.png")
    print(f"\n  wrote {out}/{args.scene}_sheet.png")

    if not ok:
        print("\nFAIL: at least one facing pair is identical -- the camera yaw "
              "did not take. Do NOT treat this as a verified look pass.")
        sys.exit(1)
    print("\nPASS: all four facings are genuinely distinct.")


if __name__ == "__main__":
    main()
