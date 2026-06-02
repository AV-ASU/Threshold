"""Preview THE PALLID HOLE (rendering/king_void.py) headlessly -- the fear-first
King: a void that eats the light, full of drowning faces, gold only as the wake.

Renders against a DIM LIT ROOM (so the light-eating reads) to an MP4 + a strip.

    python tools/preview_king_void.py
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.king_void import draw_king_void, reset_king_void_fx

W, H = 360, 460
SCALE = 6.2
_BG = None


def _room():
    """A dim wooden room with a single weak cold light -- something for the hole
    to eat. Deliberately desaturated and underlit."""
    global _BG
    if _BG is not None:
        return _BG.copy()
    import random
    r = random.Random(5)
    s = pygame.Surface((W, H))
    # base floor gradient (darker at the edges)
    for y in range(H):
        f = 1 - abs(y - H * 0.55) / H
        v = 30 + int(18 * f)
        pygame.draw.line(s, (v, int(v * 0.95), int(v * 0.86)), (0, y), (W, y))
    # floorboards
    for by in range(0, H, 26):
        pygame.draw.line(s, (20, 19, 17), (0, by), (W, by), 2)
    # faint grain noise
    for _ in range(2600):
        x, y = r.randrange(W), r.randrange(H)
        d = r.randint(-10, 10)
        c = s.get_at((x, y))
        s.set_at((x, y), (max(0, min(255, c[0] + d)),
                          max(0, min(255, c[1] + d)),
                          max(0, min(255, c[2] + d))))
    # a soft cold light from upper-left. NOTE: BLEND_RGB_ADD ignores alpha, so
    # the falloff must live in the RGB values -- bake the gradient, blit once.
    light = pygame.Surface((W, H))
    lx, ly = int(W * 0.30), int(H * 0.26)
    maxd = math.hypot(W, H)
    for i in range(80, 0, -1):
        rr = int(maxd * 0.55 * i / 80)
        f = 1 - i / 80
        v = int(44 * f)
        pygame.draw.circle(light, (int(v * 0.74), int(v * 0.84), v), (lx, ly), rr)
    s.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    _BG = s
    return s.copy()


def _vignette():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2
    maxr = math.hypot(cx, cy)
    for i in range(26):
        r = int(maxr * (1 - i / 26))
        pygame.draw.circle(v, (0, 0, 0, min(170, int(4 * i))), (cx, cy), r)
    return v


_VIG = None


def frame(t, threat):
    global _VIG
    if _VIG is None:
        _VIG = _vignette()
    s = _room()
    draw_king_void(s, W // 2, int(H * 0.52), t, threat=threat, scale=SCALE)
    s.blit(_VIG, (0, 0))
    import numpy as np
    return np.transpose(pygame.surfarray.array3d(s), (1, 0, 2))


def arc_mp4():
    import imageio.v2 as imageio
    reset_king_void_fx()
    fps = 30
    frames = []
    T = 20.0
    n = int(T * fps)
    for i in range(n):
        t = i / fps
        u = i / (n - 1)
        if u < 0.28:                 # long dormant stillness -- just a wrong dark
            threat = 0.06
        elif u < 0.52:               # the dead begin to surface in him
            threat = 0.06 + (u - 0.28) / 0.24 * 0.34
        elif u < 0.72:               # HE SEES YOU: the gold wakes, holds
            threat = 0.45 + (u - 0.52) / 0.20 * 0.22
        elif u < 0.94:               # he stutters closer; the arms reach
            threat = 0.67 + (u - 0.72) / 0.22 * 0.31
        else:                        # right at the threshold of the catch
            threat = 0.98
        frames.append(frame(t, threat))
    imageio.mimsave("/tmp/king_void.mp4", frames, fps=fps, macro_block_size=1)
    print("wrote /tmp/king_void.mp4")


def strip():
    reset_king_void_fx()
    font = pygame.font.SysFont("monospace", 11)
    cells = [(0.06, "dormant"), (0.4, "the dead surface"),
             (0.66, "it sees you"), (0.97, "it reaches")]
    cw, ch = W, H
    out = pygame.Surface((cw * len(cells), ch + 16))
    out.fill((4, 4, 6))
    for i, (thr, lbl) in enumerate(cells):
        s = _room()
        draw_king_void(s, cw // 2, int(ch * 0.52), 2.0 + i * 1.7, threat=thr, scale=SCALE)
        s.blit(_VIG if _VIG else _vignette(), (0, 0))
        out.blit(s, (i * cw, 0))
        out.blit(font.render(lbl, True, (150, 150, 160)), (i * cw + 6, ch + 2))
    pygame.image.save(out, "/tmp/king_void.png")
    print("wrote /tmp/king_void.png")


if __name__ == "__main__":
    _VIG = _vignette()
    strip()
    arc_mp4()
    print("done")
