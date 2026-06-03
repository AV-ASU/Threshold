"""Preview THE UNFOLDING (rendering/king_unfold.py) headlessly -- the non-humanoid
4D King: an irregular oily 4D mass with a hypersphere heart everting inside it,
carved masks surfacing on its skin, and limbs that stretch toward the player.
Renders to an MP4 + a strip.

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

W, H = 480, 560
CY = int(H * 0.40)                  # high-ish: leaves room for the reaching arms
SCALE = 102.0
_BG = None


def _bg():
    global _BG
    if _BG is not None:
        return _BG.copy()
    import random
    r = random.Random(3)
    s = pygame.Surface((W, H))
    maxr = math.hypot(W, H)
    for i in range(72, 0, -1):
        rr = int(maxr * i / 72); f = 1 - i / 72; v = 15 + int(25 * f)
        pygame.draw.circle(s, (int(v * 0.82), int(v * 0.86), int(v * 0.96)),
                           (W // 2, CY), rr)
    for _ in range(2600):
        x, y = r.randrange(W), r.randrange(H); d = r.randint(-7, 9)
        c = s.get_at((x, y))
        s.set_at((x, y), tuple(max(0, min(255, c[k] + d)) for k in range(3)))
    for _ in range(46):                  # faint cold motes
        x, y = r.randrange(W), r.randrange(H); v = r.randint(40, 70)
        s.set_at((x, y), (v, v, int(v * 1.1)))
    _BG = s
    return s.copy()


def _vignette():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    maxr = math.hypot(W, H)
    for i in range(28):
        pygame.draw.circle(v, (0, 0, 0, min(170, int(3.8 * i))),
                           (W // 2, CY), int(maxr * (1 - i / 28)))
    return v


_VIG = None


def frame(t, threat):
    s = _bg()
    draw_king_unfold(s, W // 2, CY, t, threat=threat, scale=SCALE)
    s.blit(_VIG, (0, 0))
    import numpy as np
    return np.transpose(pygame.surfarray.array3d(s), (1, 0, 2))


def arc_mp4():
    import imageio.v2 as imageio
    reset_king_unfold_fx()
    fps = 30
    frames = []
    T = 22.0
    n = int(T * fps)
    for i in range(n):
        t = i / fps
        u = i / (n - 1)
        if u < 0.24:
            threat = 0.07
        elif u < 0.50:
            threat = 0.07 + (u - 0.24) / 0.26 * 0.42
        elif u < 0.72:
            threat = 0.49 + (u - 0.50) / 0.22 * 0.24
        elif u < 0.92:
            threat = 0.73 + (u - 0.72) / 0.20 * 0.25
        else:
            threat = 0.99
        frames.append(frame(t, threat))
    imageio.mimsave("/tmp/king_unfold.mp4", frames, fps=fps, macro_block_size=1)
    print("wrote /tmp/king_unfold.mp4")


def strip():
    reset_king_unfold_fx()
    font = pygame.font.SysFont("monospace", 12)
    cells = [(2.0, 0.08, "distant fold"), (3.4, 0.5, "everting"),
             (5.0, 0.8, "masks + heart"), (7.6, 0.99, "arms reach")]
    out = pygame.Surface((W * len(cells), H + 16))
    out.fill((4, 4, 6))
    for i, (t, thr, lbl) in enumerate(cells):
        s = _bg()
        draw_king_unfold(s, W // 2, CY, t, threat=thr, scale=SCALE)
        s.blit(_VIG, (0, 0))
        out.blit(s, (i * W, 0))
        out.blit(font.render(lbl, True, (155, 155, 165)), (i * W + 6, H + 2))
    pygame.image.save(out, "/tmp/king_unfold.png")
    print("wrote /tmp/king_unfold.png")


if __name__ == "__main__":
    _VIG = _vignette()
    strip()
    arc_mp4()
    print("done")
