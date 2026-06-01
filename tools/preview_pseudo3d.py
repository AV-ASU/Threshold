"""Render the pseudo-3D Watcher proto to a labelled turntable strip + a GIF.

Headless: self-configures SDL dummy drivers. Run from repo root:
    python tools/preview_pseudo3d.py
Outputs /tmp/pseudo3d_watcher.png (turntable) and .gif (spin loop).
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.pseudo3d import draw_pseudo3d_watcher

BG = (16, 15, 20)
CELL = (64, 96)
N = 8                       # turntable angles across the strip


def cell(yaw, t, gaze=False):
    s = pygame.Surface(CELL, pygame.SRCALPHA)
    s.fill(BG)
    # faint ground line so depth/sway read
    pygame.draw.line(s, (34, 32, 40), (6, 86), (CELL[0] - 6, 86), 1)
    draw_pseudo3d_watcher(s, CELL[0] // 2, 86, yaw=yaw, t=t)
    return s


def strip():
    font = pygame.font.SysFont("monospace", 10)
    W = CELL[0] * N
    H = CELL[1] + 16
    out = pygame.Surface((W, H))
    out.fill((8, 8, 11))
    for i in range(N):
        yaw = (i / N) * 2 * math.pi
        out.blit(cell(yaw, t=1.7), (i * CELL[0], 0))
        lbl = font.render(f"{int(math.degrees(yaw))}deg", True, (150, 150, 160))
        out.blit(lbl, (i * CELL[0] + 6, CELL[1] + 2))
    pygame.image.save(out, "/tmp/pseudo3d_watcher.png")
    print("wrote /tmp/pseudo3d_watcher.png")


def gif():
    try:
        from PIL import Image
    except ImportError:
        print("PIL not installed; skipping GIF")
        return
    frames = []
    FR = 48
    for i in range(FR):
        yaw = (i / FR) * 2 * math.pi
        t = i * 0.12
        s = cell(yaw, t)
        raw = pygame.image.tostring(s, "RGBA")
        frames.append(Image.frombytes("RGBA", CELL, raw).convert("P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/pseudo3d_watcher.gif", save_all=True,
                   append_images=frames[1:], duration=60, loop=0, disposal=2)
    print("wrote /tmp/pseudo3d_watcher.gif")


if __name__ == "__main__":
    strip()
    gif()
