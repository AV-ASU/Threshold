"""LOOK at the PAINTED ALPHABET on its own, flat and large.

    python tools/preview_lettering.py                    # alphabet + the board
    python tools/preview_lettering.py --text "RIVER RD"  # try a word
    python tools/preview_lettering.py --weight 0.20      # try a brush width

The lettering equivalent of `preview_props_sheet.py`. `rendering/lettering.py`
draws words as GEOMETRY in a surface's own plane, which is what stopped the
town board's words sliding off the plank as the camera turned -- but it means
the letterforms themselves are only ever seen at sign size, foreshortened,
half in shadow, three tiles away. At that size a badly drawn R and a well
drawn R are the same four pixels, and a stroke set that is subtly wrong stays
wrong forever because nothing ever shows it to you.

So this renders the glyphs FLAT (an identity projection, no camera at all) at
a size where the shapes can actually be judged, and beside it the same text at
the size it really lands on the board -- because the two questions are
different. "Is this a good R" is answered large; "can this be read from the
road" is answered small, and a line that survives one can fail the other.
Both rows carry the wear pass, since flaking is what turned the first cut of
the board's lower two lines from lettering into mould.

Output: /tmp/lettering/sheet.png
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                             # noqa: E402

from rendering import lettering                           # noqa: E402
from rendering.materials import shade_for                 # noqa: E402

ROWS = ("ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "0123456789 .'&")


def _band(surf, text, x, y, w, h, col, chip, weight, wear=True):
    """One line of painted text, laid flat: local (lx, lz) straight to pixels
    with z flipped, which is the do-nothing projection the module is built to
    accept. No camera, no tilt, no foreshortening to hide behind."""
    lettering.paint_word(
        surf, lambda lx, lz: (x + lx, y + h - lz), text,
        0.0, w, 0.0, h, col, wear=chip if wear else None,
        weight=weight, seed=sum(ord(c) for c in text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None, help="one word to try")
    ap.add_argument("--weight", type=float, default=0.17)
    a = ap.parse_args()
    pygame.init()

    W, H = 1180, 620
    surf = pygame.Surface((W, H))
    surf.fill((26, 24, 30))
    # the board's own colours, at the shade a face square to the viewer gets
    field = shade_for("sign_field", "side", 0.0, 1.0)
    col = shade_for("sign_paint", "side", 0.0, 1.0)
    font = pygame.font.SysFont(None, 17)

    def label(s, x, y):
        surf.blit(font.render(s, True, (150, 146, 160)), (x, y))

    y = 20
    rows = [(a.text, 84)] if a.text else [(r, 84) for r in ROWS]
    label("THE ALPHABET, flat and large (judge the letterforms here)", 24, y)
    y += 22
    for text, h in rows:
        pygame.draw.rect(surf, field, (24, y, W - 48, h + 16))
        _band(surf, text, 36, y + 8, W - 72, h, col, field, a.weight)
        y += h + 26

    y += 10
    label("THE BOARD's three lines, at the size they land (judge legibility)",
          24, y)
    y += 22
    # the panel's real letter field is about 28 units across and 13 tall; at
    # play zoom the whole board is roughly this many pixels wide
    for px in (300, 210, 150):
        bw = px
        bh = int(px * 0.47)
        pygame.draw.rect(surf, field, (24, y, bw, bh))
        h = bh / 13.3
        for text, z0, z1, wt in (
                ("BRIMLEY", 0.52, 0.95, 0.17),
                ("NORTHERNMOST CORN", 0.30, 0.46, 0.22),
                ("EST. 1894", 0.06, 0.22, 0.22)):
            lettering.paint_word(
                surf, lambda lx, lz: (24 + lx, y + bh - lz), text,
                bw * 0.06, bw * 0.94, bh * z0, bh * z1, col,
                wear=field, weight=wt, seed=sum(ord(c) for c in text))
        label(f"{px}px wide", 24 + bw + 12, y + bh // 2)
        y += bh + 16

    os.makedirs("/tmp/lettering", exist_ok=True)
    out = "/tmp/lettering/sheet.png"
    pygame.image.save(surf, out)
    print("wrote", out)
    print("  Large row: are these good LETTERS? Small rows: can you READ them?")
    print("  Wear that reads as age up close reads as damage at sign size.")


if __name__ == "__main__":
    main()
