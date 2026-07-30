"""LOOK AT ONE DRAWN CORRIDOR PIECE AS A REAL ROOM, from all four facings.

    python tools/preview_lost_room.py <piece> [--biome road|forest|corn]
                                     [--orient 0-7] [--bright] [--tag T]
    python tools/preview_lost_room.py --list

A piece in `scenes/lost_pieces.py` is twenty rows of twenty characters, and
`tools/plan_page.py` draws it flat. Neither tells you what it is to STAND in:
what the walls do under the tilt, whether a two-tile corridor reads as a
corridor, whether the scatter fits, whether the void gap reads as a hole or as
a texture. The field deals pieces at random, so waiting to meet one in play is
not a look pass.

This pins the piece into a field's entry cell and hands it to the ordinary
four-facing harness, so a corridor is judged exactly the way a scene is:
`tools/capture_facings.py`'s yaw handling and its assertion that the four
frames genuinely differ, both unchanged.
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame                                                  # noqa: E402
from tools.capture_world import _boot_game                     # noqa: E402
from tools.capture_facings import FACINGS, capture, _frac_diff  # noqa: E402
from scenes import lost_field as LF                            # noqa: E402
from scenes import lost_pieces as LP                           # noqa: E402

ROOT = {"road": "lost_road", "forest": "lost_forest", "corn": "lost_corn"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", nargs="?")
    ap.add_argument("--biome", default="road", choices=sorted(ROOT))
    ap.add_argument("--orient", type=int, default=0)
    ap.add_argument("--bright", action="store_true")
    ap.add_argument("--tag", default="room")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list or not args.piece:
        for n in sorted(LP.DECK):
            print("  %-14s %s" % (n, LP.DECK[n]["job"].split(".")[0]))
        return 0
    if args.piece not in LP.DECK:
        print("no piece %r. --list to see them." % args.piece)
        return 1

    # Pin the piece into the entry cell of a fresh field, then load the field's
    # ROOT key: the room the mouth drops you in is cell (0, 0), so the ordinary
    # capture path reaches it with no special casing.
    root = ROOT[args.biome]
    rots = LP.orientations(LP.DECK[args.piece]["rows"])
    fld = LF.LostField(root, args.biome, seed=5)
    fld.cells[(0, 0)] = (args.piece, args.orient % len(rots))
    fld.span.pop((0, 0), None)
    LF.FIELD = fld

    out = "/tmp/lostroom_%s" % args.tag
    os.makedirs(out, exist_ok=True)
    g = _boot_game()
    shots = {}
    for name, heading, fv in FACINGS:
        # every capture reloads the scene, and the field must survive that
        LF.FIELD = fld
        shots[name] = capture(g, root, heading, fv, None, None, args.bright,
                              0, 0, None)
        pygame.image.save(shots[name],
                          "%s/%s_%s.png" % (out, args.piece, name))
    print("  %s (%s, orientation %d) -> %s"
          % (args.piece, args.biome, args.orient, out))

    ok = True
    order = ["N", "E", "S", "W", "N"]
    for i in range(4):
        a, b = order[i], order[i + 1]
        f = _frac_diff(shots[a], shots[b])
        print("    %s->%s: %6.2f%% of pixels differ%s"
              % (a, b, f * 100, "" if f > 0.02 else "   IDENTICAL"))
        if f <= 0.02:
            ok = False

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
        d.text((x + 2, y + 4), "%s  %s  facing %s" % (args.piece, args.biome, n),
               fill=(232, 232, 180))
        sheet.paste(im, (x, y + lab))
    sheet.save("%s/%s_sheet.png" % (out, args.piece))
    print("  wrote %s/%s_sheet.png" % (out, args.piece))
    if not ok:
        print("\nFAIL: a facing pair is identical, so the yaw did not take.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
