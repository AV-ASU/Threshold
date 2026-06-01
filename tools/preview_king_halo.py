"""Preview the HALO / orbit King redesign (rendering/king_halo.py) headlessly.

Drives the full escalation arc to an MP4 (and a strip): serene mask -> rouse ->
orbiting counter-rotating halo with faces-in-the-light + too-many-eyes -> iris
-> the CROWN BEAT (snap + inversion flash + keyhole). Run from repo root:

    python tools/preview_king_halo.py
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.king_halo import draw_king_halo, reset_king_halo_fx

BG = (12, 11, 16)
W, H = 340, 360
SCALE = 3.4


def frame(t, threat, beat, yaw, kscale):
    s = pygame.Surface((W, H))
    s.fill(BG)
    draw_king_halo(s, W // 2, H // 2, yaw, t, threat=threat, scale=kscale, beat=beat)
    import numpy as np
    return np.transpose(pygame.surfarray.array3d(s), (1, 0, 2))


def arc_mp4():
    import imageio.v2 as imageio
    reset_king_halo_fx()
    fps = 30
    frames = []
    T = 15.0
    n = int(T * fps)
    for i in range(n):
        t = i / fps
        u = i / (n - 1)
        beat = 0.0
        ks = SCALE
        if u < 0.12:                       # serene whole mask
            threat = 0.0
        elif u < 0.42:                     # approach: crack/seep -> lift to halo
            threat = (u - 0.12) / 0.30 * 0.78
        elif u < 0.66:                     # hold the orbiting halo
            threat = 0.78 + 0.04 * math.sin(t)
        elif u < 0.86:                     # lethal: iris in
            threat = 0.86 + (u - 0.66) / 0.20 * 0.14
        elif u < 0.93:                     # THE CROWN BEAT + keyhole
            threat = 1.0
            bp = (u - 0.86) / 0.07
            beat = math.sin(bp * math.pi)          # 0 -> 1 -> 0
            ks = SCALE * (1.0 + 2.2 * beat)         # keyhole: blow past bounds
        else:                              # collapse
            threat = max(0.0, 1.0 - (u - 0.93) / 0.07)
        yaw = math.sin(t * 0.45) * 0.7
        frames.append(frame(t, threat, beat, yaw, ks))
    imageio.mimsave("/tmp/king_halo.mp4", frames, fps=fps, macro_block_size=1)
    print("wrote /tmp/king_halo.mp4")


def strip():
    reset_king_halo_fx()
    font = pygame.font.SysFont("monospace", 11)
    cells = [(0.0, 0.0, 0.0, "calm"), (0.55, 0.0, 0.3, "rouse"),
             (0.85, 0.0, 0.0, "halo"), (0.97, 0.0, 0.0, "iris"),
             (1.0, 0.45, 0.0, "crown")]
    cw, ch = 170, 190
    out = pygame.Surface((cw * len(cells), ch + 16))
    out.fill((6, 6, 9))
    for i, (thr, beat, _g, lbl) in enumerate(cells):
        c = pygame.Surface((cw, ch)); c.fill(BG)
        draw_king_halo(c, cw // 2, ch // 2, 0.3, 2.0 + i, threat=thr,
                       scale=2.2, beat=beat)
        out.blit(c, (i * cw, 0))
        out.blit(font.render(lbl, True, (170, 170, 180)), (i * cw + 6, ch + 2))
    pygame.image.save(out, "/tmp/king_halo.png")
    print("wrote /tmp/king_halo.png")


if __name__ == "__main__":
    strip()
    arc_mp4()
    print("done")
