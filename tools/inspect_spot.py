"""LOOK CLOSE at one CORNER of a real scene -- the middle altitude.

    python tools/inspect_spot.py lodge_yard --at 5,6 --zoom 3
    python tools/inspect_spot.py lodge_yard --at 5,6 --dark --ev 3

CLAUDE.md's scene-dressing step 5 asks for three altitudes and then the dark:
an isolated contact sheet, a ROOM CROP, the live room, and the same shot with
the darkness on. Two of those had tools -- `preview_props_sheet.py` for the
isolated sheet and `capture_facings.py` for the live room -- and the middle
one had none. So the room crop kept being skipped, and props were signed off
either at 5x magnification where nothing sits in context, or from a whole-map
capture where a mailbox is nine pixels across.

Both failures are real. A woodpile was judged good on a contact sheet at a
magnification where its proportions could not be read. The six props of the
lodge yard were called placed from a full-scene shot that was too small to
show they had rendered as MAGENTA PLACEHOLDER SQUARES.

This fills the gap: the real scene, the real camera, the real props, centred
on a spot you name and zoomed until you can actually see it -- from all four
facings, because a prop that hides on one heading is the whole failure mode
(VISION.md).

`--spawn KIND[:SEED][@TX,TY]` drops a CREATURE in the room first, because
judging a sprite on a preview card with a chosen backdrop is not the same as
seeing it in a real scene: that gap is exactly how an amalgam that is invisible
on a black floor got signed off. Note the darkness multiply lands AFTER the
actor pass (`draw_world`: actors, then `_draw_dark`), so a sprite tuned on a
bright card loses roughly half its value in the shot that matters -- and
whether a creature appears at a given facing is the SIGHT CONE's business, not
the sprite's, so an empty panel usually means out-of-cone, not broken art.

`--at TX,TY` centres on a tile; the camera zooms by `--zoom` (default 3x).
`--dark` keeps the darkness/fog/grade the player actually meets, which is the
last step of the dressing process: detail that only survives the debug view
is detail the player never sees. `--ev N` stages the storm for outdoor
scenes. `--tick N` runs the scene's on_update first, for driven content.

Output: /tmp/spot_<tag>/<key>_sheet.png
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
from tools.capture_facings import FACINGS, capture
from constants import TILE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--at", required=True, metavar="TX,TY",
                    help="tile to stand on and look at")
    ap.add_argument("--zoom", type=float, default=3.0)
    ap.add_argument("--dark", action="store_true",
                    help="keep the player's darkness/fog/grade (dressing "
                         "step 5: judge it in the light it is actually seen "
                         "in, not the debug view)")
    ap.add_argument("--ev", type=int, default=0)
    ap.add_argument("--tick", type=int, default=0)
    ap.add_argument("--tag", default="look")
    ap.add_argument("--spawn", metavar="KIND[:SEED][@TX,TY]",
                    help="drop a creature in the room first, e.g. "
                         "amalgam:3 -- so a sprite can be judged in a real "
                         "scene at every facing instead of on a preview card")
    args = ap.parse_args()

    tx, _, ty = args.at.partition(",")
    px, py = (int(tx) + 0.5) * TILE, (int(ty) + 0.5) * TILE

    out = f"/tmp/spot_{args.tag}"
    os.makedirs(out, exist_ok=True)
    g = _boot_game()
    # ZOOM by the camera's own scale, not by upscaling the PNG afterwards:
    # the props are polygons drawn AT this scale, so zooming the camera shows
    # their real edges while zooming the image just shows big soft pixels of
    # the same too-small render.
    #
    # It has to be done by moving TILT_ZOOM, though, because `_update_camera`
    # re-asserts `camera.scale = TILT_ZOOM` on every call -- assigning
    # `camera.scale` around the capture looks like it works and is silently
    # undone before the draw. (Exactly the trap `capture_facings.py` exists
    # for with the yaw: camera state the ad-hoc render path resets under you.)
    import systems.game as _sg
    _sg.TILT_ZOOM = _sg.TILT_ZOOM * args.zoom

    shots = {}
    for name, heading, fv in FACINGS:
        shots[name] = capture(g, args.scene, heading, fv, px, py,
                              bright=not args.dark, ticks=args.tick,
                              ev=args.ev, spawn=args.spawn)
    if abs(g.camera.scale - _sg.TILT_ZOOM) > 1e-6:
        sys.exit(f"FAIL: camera.scale is {g.camera.scale}, expected "
                 f"{_sg.TILT_ZOOM} -- the zoom did not take, so this sheet "
                 "is not the magnification it claims.")

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
               f"{args.scene} @ {args.at}  x{args.zoom:g}  facing {n}"
               + ("  [DARK]" if args.dark else ""),
               fill=(232, 232, 180))
        sheet.paste(im, (x, y + lab))
    sheet.save(f"{out}/{args.scene}_sheet.png")
    print(f"wrote {out}/{args.scene}_sheet.png")


if __name__ == "__main__":
    main()
