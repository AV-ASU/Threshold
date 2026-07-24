#!/usr/bin/env python3
"""Preview THE STORM (systems.storm.Storm): the sim run over time, six
frames, showing the Pallid Mask MIGRATING between bearers (one at a time),
units drifting toward His lagged SENSE of the player, and units slowed at
the light pool (never burned). The Mask draws at player scale against the
real draw_player_sprite.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
        python tools/preview_storm.py
Writes /tmp/storm.png.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import math
import random
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
import systems.storm as st                                          # noqa: E402
from systems.storm import Storm                                     # noqa: E402
from rendering.sprites_player import draw_player_sprite             # noqa: E402

# livelier migration for the preview (the shipping dwell is 3-5.5s)
st.STORM_DWELL_LO, st.STORM_DWELL_HI = 1.8, 2.6

FW, FH = 440, 330
PLX, PLY = 220, 262                     # the player, in the refuge, bottom-centre
POOL_RX, POOL_RY = 150, 58


def lit_at(x, y):
    return ((x - PLX) / POOL_RX) ** 2 + ((y - PLY) / POOL_RY) ** 2 < 1.0


def make_anchors():
    rng = random.Random(7)
    pts = []
    tries = 0
    while len(pts) < 15 and tries < 900:
        tries += 1
        x = rng.uniform(24, FW - 24)
        y = rng.uniform(40, FH - 30)
        # a couple deliberately near the pool rim (to show the slow); the
        # rest out in the dark
        if lit_at(x, y):
            continue
        if any(abs(x - px) < 40 and abs(y - py) < 34 for px, py in pts):
            continue
        pts.append((x, y))
    return pts


def dusk(s, top=(46, 44, 55), bot=(15, 13, 20)):
    for y in range(FH):
        f = (y / FH) ** 0.85
        pygame.draw.line(s, tuple(int(top[k] + (bot[k] - top[k]) * f) for k in range(3)),
                         (0, y), (FW, y))


def frame(storm):
    s = pygame.Surface((FW, FH))
    dusk(s)
    pool = pygame.Surface((FW, FH), pygame.SRCALPHA)
    for i in range(26):
        f = i / 25
        a = int(40 * (1 - f) ** 1.9)
        pygame.draw.ellipse(pool, (84, 94, 110, a),
                            (int(PLX - POOL_RX * (1 - f * 0.95)),
                             int(PLY - POOL_RY * (1 - f * 0.95)),
                             int(POOL_RX * 2 * (1 - f * 0.95)),
                             int(POOL_RY * 2 * (1 - f * 0.95))))
    s.blit(pool, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    storm.draw(s, project=lambda x, y: (x, y), player_screen=(PLX, PLY))
    draw_player_sprite(s, PLX, PLY, (0, 1), view="front")
    return s


def run():
    storm = Storm(make_anchors(), seed=5, mask_r=st.STORM_MASK_R)
    caps = {}
    targets = [1.0, 2.6, 4.2, 5.8, 7.4, 9.0]
    t = 0.0
    dt = 1 / 30.0
    ti = 0
    while ti < len(targets):
        storm.update(dt, PLX, PLY, lit_at=lit_at)
        t += dt
        if t >= targets[ti]:
            caps[targets[ti]] = (frame(storm), storm.bearer, storm.deploy, storm.state)
            ti += 1

    cols, rows = 3, 2
    pad = 12
    lab = 34
    font = pygame.font.Font(None, 26)
    small = pygame.font.Font(None, 22)
    W = cols * FW + (cols + 1) * pad
    H = lab + rows * (FH + lab) + pad
    out = pygame.Surface((W, H))
    out.fill((13, 12, 17))
    out.blit(font.render("THE STORM  --  the Mask migrates (one bearer at a time); units drift to His SENSE of you, slowed at the light",
                         True, (216, 210, 196)), (pad, 8))
    for i, tt in enumerate(targets):
        fr, bearer, deploy, state = caps[tt]
        c, r = i % cols, i // cols
        x = pad + c * (FW + pad)
        y = lab + r * (FH + lab)
        out.blit(fr, (x, y))
        tag = f"t={tt:.1f}s   bearer #{bearer}   mask {state} {deploy:.2f}"
        out.blit(small.render(tag, True, (150, 146, 134)), (x + 4, y + FH + 6))
    pygame.image.save(out, "/tmp/storm.png")
    print(f"mask_r={st.STORM_MASK_R}  ->  /tmp/storm.png {out.get_size()}")


run()
