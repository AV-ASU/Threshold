#!/usr/bin/env python3
"""Preview the Pallid Mask as a REAL 3D object: `yaw` spins it a full 360 --
His carved face toward the PI, a curved lens at profile, the blank back turned
away (no eyes from behind), and round again. Writes an animated GIF.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
        python tools/preview_mask_spin.py
Writes /tmp/mask_spin.gif.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import math
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
from rendering.amalgam import draw_pallid_mask_part          # noqa: E402
from PIL import Image                                        # noqa: E402

W, H = 240, 300
N = 54                                   # frames over a full turn


def dusk(s, top=(44, 42, 54), bot=(14, 12, 18)):
    for y in range(H):
        f = (y / H) ** 0.85
        pygame.draw.line(s, tuple(int(top[k] + (bot[k] - top[k]) * f) for k in range(3)),
                         (0, y), (W, y))


frames = []
for i in range(N):
    yaw = i / N * math.tau
    s = pygame.Surface((W, H))
    dusk(s)
    draw_pallid_mask_part(s, W // 2, H // 2 - 6, 68, deploy=1.0,
                          gaze=(0.0, 0.2), yaw=yaw, lean=6.0, seed=7)
    raw = pygame.image.tostring(s, "RGB")
    frames.append(Image.frombytes("RGB", (W, H), raw))

frames[0].save("/tmp/mask_spin.gif", save_all=True, append_images=frames[1:],
               duration=70, loop=0, optimize=True)
print("/tmp/mask_spin.gif", (W, H), N, "frames")
