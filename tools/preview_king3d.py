"""Preview the volumetric King in Yellow (rendering/king3d.py) headlessly.

Self-configures SDL dummy drivers. Run from repo root:
    python tools/preview_king3d.py

Writes to /tmp/:
    king3d_turntable.png   yaw 0 -> 2pi at the chosen threat (default calm 0)
    king3d_threat.png      threat 0 -> 1 face-on (calm -> seep -> crack -> shatter)
    king3d_turntable.mp4    spin loop  (if imageio present)
    king3d_threat.mp4       threat ramp (if imageio present)
    king3d_birth.mp4        birth(converge) -> hold -> shatter sequence

The MP4s are what the user reviews; the PNG strips are quick eyeball checks.
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.king3d import draw_king3d

BG = (12, 11, 16)
CELL = (150, 170)
SCALE = 3.2


def _ground(s):
    pygame.draw.line(s, (30, 28, 36), (8, CELL[1] - 18),
                     (CELL[0] - 8, CELL[1] - 18), 1)


def cell(yaw, t, threat, birth=1.0):
    s = pygame.Surface(CELL, pygame.SRCALPHA)
    s.fill(BG)
    _ground(s)
    draw_king3d(s, CELL[0] // 2, CELL[1] // 2 + 6, yaw, t, threat=threat,
                scale=SCALE, birth=birth)
    return s


def strip(path, items, label):
    font = pygame.font.SysFont("monospace", 11)
    n = len(items)
    out = pygame.Surface((CELL[0] * n, CELL[1] + 18))
    out.fill((6, 6, 9))
    for i, it in enumerate(items):
        yaw, t, threat, lbl = it[0], it[1], it[2], it[3]
        birth = it[4] if len(it) > 4 else 1.0
        out.blit(cell(yaw, t, threat, birth), (i * CELL[0], 0))
        out.blit(font.render(lbl, True, (160, 160, 172)),
                 (i * CELL[0] + 6, CELL[1] + 3))
    pygame.image.save(out, path)
    print("wrote", path, "  (" + label + ")")


def birth_strip():
    n = 6
    items = [(0.25, 1.0 + i, 0.0, f"birth {i / (n - 1):.1f}", i / (n - 1))
             for i in range(n)]
    strip("/tmp/king3d_birth.png", items, "birth: shards converge -> whole")


def shatter_strip():
    n = 6
    # threat 0.5 -> 1.0 is the shatter band
    items = [(0.25, 1.0 + i, 0.5 + 0.5 * i / (n - 1), f"thr {0.5 + 0.5 * i / (n - 1):.2f}")
             for i in range(n)]
    strip("/tmp/king3d_shatter.png", items, "shatter: whole -> flung apart")


def turntable_strip():
    n = 8
    items = [((i / n) * math.tau, 1.7, 0.0,
              f"{int(math.degrees((i / n) * math.tau))}deg") for i in range(n)]
    strip("/tmp/king3d_turntable.png", items, "yaw turntable, calm")


def threat_strip():
    n = 6
    items = [(0.0, 1.7, i / (n - 1), f"thr {i / (n - 1):.1f}") for i in range(n)]
    strip("/tmp/king3d_threat.png", items, "threat ramp, face-on")


def _mp4(path, frames, fps=30):
    try:
        import imageio.v2 as imageio
    except ImportError:
        print("imageio missing; skip", path)
        return
    imageio.mimsave(path, frames, fps=fps, macro_block_size=1)
    print("wrote", path)


def _frame(yaw, t, threat, birth=1.0, w=320, h=340):
    s = pygame.Surface((w, h))
    s.fill(BG)
    pygame.draw.line(s, (30, 28, 36), (16, h - 40), (w - 16, h - 40), 1)
    draw_king3d(s, w // 2, h // 2 + 10, yaw, t, threat=threat, scale=SCALE * 1.7,
                birth=birth)
    import numpy as np
    return np.transpose(pygame.surfarray.array3d(s), (1, 0, 2))


def turntable_mp4():
    fr = 90
    frames = [_frame((i / fr) * math.tau, i * 0.1, 0.0) for i in range(fr)]
    _mp4("/tmp/king3d_turntable.mp4", frames)


def threat_mp4():
    fr = 90
    frames = [_frame(0.0, i * 0.1, i / (fr - 1)) for i in range(fr)]
    _mp4("/tmp/king3d_threat.mp4", frames)


def birth_mp4():
    # birth (shards converge) -> hold calm -> shatter (fling apart again).
    fr = 150
    frames = []
    for i in range(fr):
        u = i / (fr - 1)
        if u < 0.30:                       # birth: converge over the first 30%
            birth = u / 0.30; threat = 0.0
        elif u < 0.55:                     # hold the calm whole mask
            birth = 1.0; threat = 0.0
        else:                              # rouse + shatter
            birth = 1.0; threat = (u - 0.55) / 0.45
        frames.append(_frame(0.3, i * 0.1, threat, birth=birth))
    _mp4("/tmp/king3d_birth.mp4", frames)


if __name__ == "__main__":
    turntable_strip()
    threat_strip()
    birth_strip()
    shatter_strip()
    turntable_mp4()
    threat_mp4()
    birth_mp4()
    print("done")
