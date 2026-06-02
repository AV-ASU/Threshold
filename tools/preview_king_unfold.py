"""Preview THE UNFOLDING (rendering/king_unfold.py) headlessly -- the non-humanoid
4D King: a tesseract everting through 4D, dark + light-eating, with eyes and the
Sign surfacing on its facets. Renders to an MP4 + a strip.

    python tools/preview_king_unfold.py
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.king_unfold import draw_king_unfold, reset_king_unfold_fx

W, H = 420, 420
SCALE = 78.0
_BG = None


def _bg():
    """A dim, foggy void with faint cold motes -- enough light for the hole to
    eat, nothing warm."""
    global _BG
    if _BG is not None:
        return _BG.copy()
    import random
    r = random.Random(3)
    s = pygame.Surface((W, H))
    cx, cy = W // 2, H // 2
    maxr = math.hypot(cx, cy)
    for i in range(60, 0, -1):
        rr = int(maxr * i / 60)
        f = 1 - i / 60
        v = 16 + int(26 * f)
        pygame.draw.circle(s, (int(v * 0.82), int(v * 0.86), int(v * 0.96)), (cx, cy), rr)
    for _ in range(2200):
        x, y = r.randrange(W), r.randrange(H)
        d = r.randint(-7, 9)
        c = s.get_at((x, y))
        s.set_at((x, y), (max(0, min(255, c[0] + d)),
                          max(0, min(255, c[1] + d)),
                          max(0, min(255, c[2] + d))))
    for _ in range(40):                  # faint cold motes
        x, y = r.randrange(W), r.randrange(H)
        v = r.randint(40, 70)
        s.set_at((x, y), (v, v, int(v * 1.1)))
    _BG = s
    return s.copy()


def _vignette():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2
    maxr = math.hypot(cx, cy)
    for i in range(26):
        r = int(maxr * (1 - i / 26))
        pygame.draw.circle(v, (0, 0, 0, min(175, int(4.2 * i))), (cx, cy), r)
    return v


_VIG = None


def frame(t, threat):
    s = _bg()
    draw_king_unfold(s, W // 2, H // 2, t, threat=threat, scale=SCALE)
    s.blit(_VIG, (0, 0))
    import numpy as np
    return np.transpose(pygame.surfarray.array3d(s), (1, 0, 2))


def arc_mp4():
    import imageio.v2 as imageio
    reset_king_unfold_fx()
    fps = 30
    frames = []
    T = 20.0
    n = int(T * fps)
    for i in range(n):
        t = i / fps
        u = i / (n - 1)
        if u < 0.26:
            threat = 0.08
        elif u < 0.52:
            threat = 0.08 + (u - 0.26) / 0.26 * 0.4
        elif u < 0.74:
            threat = 0.48 + (u - 0.52) / 0.22 * 0.24
        elif u < 0.94:
            threat = 0.72 + (u - 0.74) / 0.20 * 0.26
        else:
            threat = 0.99
        frames.append(frame(t, threat))
    imageio.mimsave("/tmp/king_unfold.mp4", frames, fps=fps, macro_block_size=1)
    print("wrote /tmp/king_unfold.mp4")


def strip():
    reset_king_unfold_fx()
    font = pygame.font.SysFont("monospace", 11)
    cells = [(0.08, "distant fold"), (0.45, "everting"),
             (0.7, "eyes surface"), (0.97, "it looms")]
    cw, ch = W, H
    out = pygame.Surface((cw * len(cells), ch + 16))
    out.fill((4, 4, 6))
    for i, (thr, lbl) in enumerate(cells):
        s = _bg()
        draw_king_unfold(s, cw // 2, ch // 2, 2.0 + i * 1.6, threat=thr, scale=SCALE)
        s.blit(_VIG, (0, 0))
        out.blit(s, (i * cw, 0))
        out.blit(font.render(lbl, True, (150, 150, 160)), (i * cw + 6, ch + 2))
    pygame.image.save(out, "/tmp/king_unfold.png")
    print("wrote /tmp/king_unfold.png")


if __name__ == "__main__":
    _VIG = _vignette()
    strip()
    arc_mp4()
    print("done")
