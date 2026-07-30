#!/usr/bin/env python3
"""Preview THE APEX -- the Mask wearing a unit, in its various forms.

The apex is the storm's one real threat and the entity getting the most care, so
it needs its own look surface rather than being judged off the amalgam sheet (it
is a different thing: a host's deal PLUS 2-3 parts, PLUS the Mask, at a size and
a role no ordinary unit has).

Four rows, because these answer different questions:
  1. THE DEALS   -- the same apex across host seeds. How much does it vary?
  2. THE FACE    -- the Mask alone, turned. What expression range exists?
  3. THE REACH   -- the grabbing limbs, aimed around the compass and extended
                    from nothing to full. Do they read as ARMS COMING FOR YOU?
  4. THE SCALE   -- apex beside an ordinary unit beside the player. Does it
                    read as the apex at play size, or just as another unit?

    python tools/preview_apex.py [--seeds 3 11 23 ...] [--bg dark|mid]

Writes /tmp/apex_forms.png.
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                                    # noqa: E402
pygame.init()

from rendering.amalgam import (draw_amalgam_sprite, draw_pallid_3d,   # noqa: E402
                               assemble, reset_amalgam_cache)
from rendering.sprites import draw_player_sprite                 # noqa: E402
from systems.config import APEX_EXTRA_LO, APEX_EXTRA_HI          # noqa: E402

BACKDROPS = {"dark": (9, 8, 12), "mid": (46, 44, 54)}


def _label(surf, text, x, y, size=14, col=(212, 208, 216)):
    f = pygame.font.SysFont("dejavusans", size)
    surf.blit(f.render(text, True, col), (x, y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*",
                    default=[3, 11, 23, 31, 47, 52])
    ap.add_argument("--bg", choices=sorted(BACKDROPS), default="dark")
    a = ap.parse_args()

    cw, ch = 200, 210
    W = cw * max(len(a.seeds), 6) + 30
    out = pygame.Surface((W, ch * 4 + 60))
    out.fill(BACKDROPS[a.bg])

    # --- 1. the same apex across host seeds -----------------------------
    _label(out, "1.  THE DEALS  --  one apex per host seed. It wears the host's "
                "own parts plus 2-3 more; the MASK is identical every time.",
           16, 12, 15)
    gy = 40 + ch - 40
    for i, sd in enumerate(a.seeds):
        cx = 110 + i * cw
        draw_amalgam_sprite(out, cx, gy, seed=sd,
                            mask={"deploy": 1.0, "extra": APEX_EXTRA_HI,
                                  "gaze": (0.0, 0.25), "seed": 7})
        _label(out, f"host {sd}  ({len(assemble(sd))}+{APEX_EXTRA_HI} parts)",
               cx - 60, gy + 14, 12, (146, 144, 154))

    # --- 2. THE EXPRESSION RANGE -----------------------------------------
    y2 = 40 + ch
    _label(out, "2.  THE FACE  --  intent narrows the sockets and steadies the "
                "embers; strain gaps the seam and runs the crack; skew makes "
                "them disagree.", 16, y2 + 8, 15)
    gy2 = y2 + ch - 60
    faces = [("slack", 0.0, 0.0, 0.0),
             ("intent .5", 0.5, 0.0, 0.0),
             ("intent 1", 1.0, 0.0, 0.0),
             ("+skew", 1.0, 0.0, 0.55),
             ("+strain .6", 1.0, 0.6, 0.25),
             ("taking you", 1.0, 1.0, 0.4)]
    for i, (nm, it, st, sk) in enumerate(faces):
        cx = 110 + i * cw
        draw_pallid_3d(out, cx, gy2, 54, yaw=0.0, lean=6.0,
                       gaze=(0.0, 0.2), blend=0.5, seed=7, ember=1.0,
                       intent=it, strain=st, skew=sk)
        _label(out, nm, cx - 34, gy2 + 56, 12, (146, 144, 154))

    # --- 3. THE REACH -----------------------------------------------------
    y3 = 40 + ch * 2
    _label(out, "3.  THE REACH  --  the grabbing limbs. First three: extending "
                "as it closes. Last three: aimed where you actually are.",
           16, y3 + 8, 15)
    gy3 = y3 + ch - 30
    reaches = [("far, no hold", (0.0, 1.0), 0.0),
               ("it has you", (0.0, 1.0), 0.45),
               ("on you", (0.0, 1.0), 1.0),
               ("you: left", (-1.0, 0.15), 1.0),
               ("you: right", (1.0, 0.15), 1.0),
               ("you: behind", (0.2, -1.0), 1.0)]
    for i, (nm, dirn, amt) in enumerate(reaches):
        cx = 110 + i * cw
        # A whole sheet renders inside one animation bucket, and the unit cache
        # HOLDS the aim and the face for the length of a bucket (that hold is
        # what keeps the bearer affordable). Six cells with the same host seed
        # would therefore all show cell one, which is a sheet that lies about
        # the very thing it is here to show.
        reset_amalgam_cache()
        draw_amalgam_sprite(out, cx, gy3, seed=a.seeds[0],
                            mask={"deploy": 1.0, "extra": APEX_EXTRA_HI,
                                  "gaze": (0.0, 0.25), "seed": 7,
                                  "intent": 1.0, "strain": amt,
                                  "reach": (dirn[0], dirn[1], amt)})
        _label(out, nm, cx - 34, gy3 + 12, 12, (146, 144, 154))

    # --- 4. scale: apex vs unit vs player --------------------------------
    y3 = 40 + ch * 3
    _label(out, "4.  THE SCALE  --  apex, ordinary unit, player. At play size, "
                "is the apex readable as the apex?", 16, y3 + 8, 15)
    gy3 = y3 + ch - 30
    draw_amalgam_sprite(out, 120, gy3, seed=a.seeds[0],
                        mask={"deploy": 1.0, "extra": APEX_EXTRA_HI,
                              "gaze": (0.0, 0.25), "seed": 7})
    _label(out, "APEX", 96, gy3 + 12, 12, (198, 176, 120))
    draw_amalgam_sprite(out, 120 + cw, gy3, seed=a.seeds[0])
    _label(out, "same host, no Mask", 120 + cw - 60, gy3 + 12, 12,
           (146, 144, 154))
    draw_player_sprite(out, 120 + cw * 2, gy3, "down", 0.0, False)
    _label(out, "player", 120 + cw * 2 - 20, gy3 + 12, 12, (146, 144, 154))

    path = "/tmp/apex_forms.png"
    pygame.image.save(out, path)
    print(f"{path} {out.get_size()}  seeds={a.seeds} bg={a.bg}")


if __name__ == "__main__":
    main()
