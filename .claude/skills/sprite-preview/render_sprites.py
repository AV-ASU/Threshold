#!/usr/bin/env python3
"""Render this game's procedural sprites to a labelled animation strip.

Sprites here are drawn in code (rendering/sprites.py) and animate off
``pygame.time.get_ticks()`` -- there are no image files to open. This
script renders any NPC sprite kind(s) into one PNG: one row per kind,
each column a frame stepped through the animation cycle, so the motion
is visible in a single still. It runs headless (dummy SDL drivers), so
no display is needed.

Usage (from the repo root):
    python .claude/skills/sprite-preview/render_sprites.py [kind ...] \
        [--out PATH] [--frames N] [--scale S] [--span SECONDS] \
        [--facing dx,dy] [--gaze] [--bg R,G,B]

Examples:
    python .claude/skills/sprite-preview/render_sprites.py
    python .claude/skills/sprite-preview/render_sprites.py watcher cultist
    python .claude/skills/sprite-preview/render_sprites.py yellow_king \
        --frames 10 --span 4 --out /tmp/king.png

Kinds are whatever rendering.sprites.draw_npc_sprite understands
(e.g. yellow_king, cultist, watcher, wolf, doll, ...).
"""
import os
import sys
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# This file lives at <repo>/.claude/skills/sprite-preview/; add the repo
# root to sys.path so `rendering` imports resolve from anywhere.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))
from rendering.sprites import draw_npc_sprite

DEFAULT_KINDS = ["cultist", "watcher", "yellow_king"]


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("kinds", nargs="*", help="sprite kinds (default: the threat creatures)")
    ap.add_argument("--out", default="/tmp/sprite_preview.png")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--scale", type=int, default=5)
    ap.add_argument("--span", type=float, default=4.0,
                    help="seconds of animation spread across the row")
    ap.add_argument("--facing", default="0,1", help="facing as 'dx,dy'")
    ap.add_argument("--gaze", action="store_true",
                    help="pass gaze=True (player is looking AT the sprite)")
    ap.add_argument("--bg", default="26,22,30", help="cell background 'R,G,B'")
    return ap.parse_args()


def main():
    a = parse_args()
    kinds = a.kinds or DEFAULT_KINDS
    fx, fy = (float(v) for v in a.facing.split(","))
    facing = (fx, fy)
    bg = tuple(int(v) for v in a.bg.split(","))

    # A 64x88 cell with the origin (feet) low-centre fits every creature.
    CW, CH = 64, 88
    ox, oy = CW // 2, CH - 20
    S, N = a.scale, a.frames
    cellw, cellh = CW * S, CH * S
    label_h, pad, name_w = 18, 8, 150

    font = pygame.font.Font(None, 22)
    sheet = pygame.Surface((name_w + N * cellw + pad * 2,
                            label_h + len(kinds) * cellh + pad * 2))
    sheet.fill((14, 12, 18))

    # Column headers: the animation time at each frame.
    for c in range(N):
        ft = (c / max(1, N - 1)) * a.span
        sheet.blit(font.render(f"{ft:.2f}s", True, (180, 176, 168)),
                   (name_w + c * cellw + 6, 2))

    # Drive the animation clock so each column is a fixed, reproducible
    # frame instead of whatever the wall clock happens to read.
    frame_ms = [0]
    pygame.time.get_ticks = lambda: frame_ms[0]

    for r, kind in enumerate(kinds):
        ry = label_h + pad + r * cellh
        sheet.blit(font.render(kind, True, (235, 230, 215)),
                   (6, ry + cellh // 2 - 8))
        for c in range(N):
            frame_ms[0] = int((c / max(1, N - 1)) * a.span * 1000)
            cell = pygame.Surface((CW, CH))
            cell.fill(bg)
            try:
                draw_npc_sprite(cell, ox, oy, kind, facing, gaze=a.gaze)
            except Exception as e:                       # noqa: BLE001
                cell.fill((60, 20, 20))
                cell.blit(font.render("ERR", True, (240, 120, 120)), (4, 4))
                print(f"  {kind} frame {c}: {e}")
            sheet.blit(pygame.transform.scale(cell, (cellw, cellh)),
                       (name_w + c * cellw, ry))

    pygame.image.save(sheet, a.out)
    print(f"saved {a.out} {sheet.get_size()} -- {len(kinds)} kind(s) x {N} frames")


if __name__ == "__main__":
    main()
