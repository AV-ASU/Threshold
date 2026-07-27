"""Contact sheet for THRESHOLD's scenes.

Renders EVERY registered scene (via tools/render_scenes.render_scene, so it
shares the in-game terrain/decoration/grade draw) and tiles them into a
single labelled grid PNG. This is the composition-audit tool for the
liminal-composition pass (DESIGN.md §6): one glance at the whole game's
per-scene layout, and clean before/after sheets as scenes are reworked.

Usage (from the repo root):
    python tools/contact_sheet.py                 # all scenes -> one sheet
    python tools/contact_sheet.py --cols 6        # grid width
    python tools/contact_sheet.py --cell 360x260  # per-scene cell size
    python tools/contact_sheet.py --out /tmp/x.png
    python tools/contact_sheet.py well store_row   # only these keys

Each cell fits the scene thumbnail (aspect-preserved, centred) on a dark
backing; the scene's own baked label (key - name - WxH) rides along.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import SCENE_BUILDERS
from tools.render_scenes import render_scene

PAD = 10            # gap between cells
BG = (16, 14, 20)   # sheet backing


def _parse_args(argv):
    out = "/tmp/threshold_contact_sheet.png"
    cols = 5
    cw, ch = 380, 280
    keys = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out" and i + 1 < len(argv):
            out = argv[i + 1]; i += 2
        elif a == "--cols" and i + 1 < len(argv):
            cols = int(argv[i + 1]); i += 2
        elif a == "--cell" and i + 1 < len(argv):
            cw, ch = (int(v) for v in argv[i + 1].lower().split("x")); i += 2
        else:
            keys.append(a); i += 1
    return out, cols, cw, ch, (keys or None)


def _fit(thumb, cw, ch):
    """Scale a thumbnail to fit a (cw, ch) cell, preserving aspect."""
    w, h = thumb.get_size()
    s = min(cw / w, ch / h)
    return pygame.transform.smoothscale(
        thumb, (max(1, int(w * s)), max(1, int(h * s))))


def main():
    out, cols, cw, ch, keys = _parse_args(sys.argv[1:])
    font = pygame.font.Font(None, 30)
    label_font = pygame.font.Font(None, 26)
    cells = []
    for i, key in enumerate(SCENE_BUILDERS):
        if keys is not None and key not in keys:
            continue
        try:
            cells.append((i, key, render_scene(key, font)))
        except Exception as exc:
            print(f"SKIP {key}: {exc}")
    if not cells:
        print("no scenes rendered"); return
    rows = (len(cells) + cols - 1) // cols
    sheet_w = cols * cw + (cols + 1) * PAD
    sheet_h = rows * ch + (rows + 1) * PAD
    sheet = pygame.Surface((sheet_w, sheet_h))
    sheet.fill(BG)
    for idx, (_i, _key, thumb) in enumerate(cells):
        r, c = divmod(idx, cols)
        cx = PAD + c * (cw + PAD)
        cy = PAD + r * (ch + PAD)
        pygame.draw.rect(sheet, (8, 8, 11), (cx, cy, cw, ch))
        fit = _fit(thumb, cw, ch)
        fw, fh = fit.get_size()
        sheet.blit(fit, (cx + (cw - fw) // 2, cy + (ch - fh) // 2))
        pygame.draw.rect(sheet, (40, 38, 48), (cx, cy, cw, ch), 1)
        # Crisp label bar at sheet scale (the baked-in one is downscaled
        # to mush). Index + key is enough to identify a scene to rework.
        lbl = label_font.render(f"{_i:02d}  {_key}", True, (255, 235, 90))
        bar_h = lbl.get_height() + 6
        bar = pygame.Surface((cw, bar_h)); bar.set_alpha(205); bar.fill((0, 0, 0))
        sheet.blit(bar, (cx, cy))
        sheet.blit(lbl, (cx + 6, cy + 3))
    pygame.image.save(sheet, out)
    print(f"contact sheet: {len(cells)} scenes, {cols}x{rows} grid "
          f"-> {out} ({sheet_w}x{sheet_h})")


if __name__ == "__main__":
    main()
