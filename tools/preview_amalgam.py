#!/usr/bin/env python3
"""Preview the AMALGAMS (rendering/amalgam.py): the Watcher-family shadows
assembled from seeded parts. A contact sheet of DEALS -- several seeds side
by side against a player-height ruler -- plus the state rows that change what
a deal looks like (the birth build-out, the gaze-dispel peel, gaze on/off).

Why this exists: the amalgams are near-black on near-black by design, so they
are unreadable in a whole-scene capture AND on the bearer sheet (which is lit
for the Mask, not for them). Judging "does a deal read as a body" from either
of those is how the family's composition rules go unchecked. This renders them
on a chosen backdrop with the player beside them for scale.

  python tools/preview_amalgam.py [--seeds 1 2 3 ...] [--bg dark|mid|lit]
  python tools/preview_amalgam.py --bearer     # include the possessed deal

Writes /tmp/amalgam.png.
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                                    # noqa: E402
pygame.init()

from rendering.amalgam import draw_amalgam_sprite, assemble      # noqa: E402
from rendering.sprites import draw_player_sprite                 # noqa: E402

# The three readings that matter: the near-black the player actually meets,
# a mid grey that shows silhouette, and a lit card that shows the parts.
BACKDROPS = {"dark": (10, 9, 14), "mid": (46, 44, 54), "lit": (96, 92, 104)}
PLAYER_H = 20          # world units, for the ruler (a wall is 26)


def _label(surf, text, x, y, size=15, col=(206, 202, 212)):
    f = pygame.font.SysFont("dejavusans", size)
    surf.blit(f.render(text, True, col), (x, y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*",
                    default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--bg", choices=sorted(BACKDROPS), default="mid")
    ap.add_argument("--bearer", action="store_true",
                    help="add the possessed deal (Mask + crown) for contrast")
    a = ap.parse_args()

    cell_w, cell_h = 190, 250
    cols = max(len(a.seeds), 4)
    W = cols * cell_w + 40
    H = cell_h * 3 + 150
    out = pygame.Surface((W, H))
    out.fill(BACKDROPS[a.bg])

    # --- row 1: the DEALS, with the player for scale --------------------
    _label(out, "1.  THE DEALS  --  one seed each, player at left for scale "
                f"(backdrop: {a.bg})", 20, 16, 16)
    gy = 40 + cell_h - 40
    draw_player_sprite(out, 40, gy, "down", 0.0, False)
    _label(out, "player", 18, gy + 12, 12, (150, 148, 158))
    for i, s in enumerate(a.seeds):
        cx = 130 + i * cell_w
        draw_amalgam_sprite(out, cx, gy, seed=s)
        parts = assemble(s)
        _label(out, f"seed {s}  ({len(parts)} parts)", cx - 52, gy + 12, 12,
               (150, 148, 158))

    # --- row 2: the BIRTH build-out -------------------------------------
    y2 = 40 + cell_h
    _label(out, "2.  BIRTH  --  parts build out of their own cuts, staggered",
           20, y2 + 6, 16)
    gy2 = y2 + cell_h - 40
    for i, b in enumerate((0.15, 0.35, 0.55, 0.8, 1.0)):
        cx = 130 + i * cell_w
        draw_amalgam_sprite(out, cx, gy2, seed=a.seeds[0], birth=b)
        _label(out, f"birth {b:.2f}", cx - 34, gy2 + 12, 12, (150, 148, 158))

    # --- row 3: the DISPEL peel + gaze ----------------------------------
    y3 = 40 + cell_h * 2
    _label(out, "3.  DISPEL  --  stared apart: parts peel back in reverse "
                "(last two: gaze off / on)", 20, y3 + 6, 16)
    gy3 = y3 + cell_h - 40
    for i, d in enumerate((0.25, 0.55, 0.85)):
        cx = 130 + i * cell_w
        draw_amalgam_sprite(out, cx, gy3, seed=a.seeds[0], dispel=d)
        _label(out, f"dispel {d:.2f}", cx - 36, gy3 + 12, 12, (150, 148, 158))
    for i, g in enumerate((False, True)):
        cx = 130 + (3 + i) * cell_w
        draw_amalgam_sprite(out, cx, gy3, seed=a.seeds[1], gaze=g)
        _label(out, f"gaze {'ON' if g else 'off'}", cx - 32, gy3 + 12, 12,
               (150, 148, 158))

    if a.bearer:
        cx = 130 + 5 * cell_w if len(a.seeds) < 6 else W - 120
        draw_amalgam_sprite(out, cx, gy, seed=a.seeds[0],
                            mask={"deploy": 1.0})
        _label(out, "BEARER", cx - 26, gy + 12, 12, (198, 176, 120))

    path = "/tmp/amalgam.png"
    pygame.image.save(out, path)
    print(f"{path} {out.get_size()}  seeds={a.seeds} bg={a.bg}")


if __name__ == "__main__":
    main()
