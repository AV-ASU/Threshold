#!/usr/bin/env python3
"""Preview the possessed BEARER's new features (TODO #25):
  1. the Mask turned in 3D (`yaw`) -- seen on the side, respecting the world,
  2. the POWER-UP -- the Mask jumping to an amalgam bulks it up (mass + royal
     parts), ramped by deploy,
  3. the special royal parts -- reaching arms into the dark, the ember crown,
     extra eyes, the gold rift.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
        python tools/preview_bearer.py
Writes /tmp/bearer.png.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import math
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
from rendering.amalgam import draw_amalgam_sprite, draw_pallid_mask_part  # noqa: E402
from rendering.sprites_player import draw_player_sprite                    # noqa: E402

MR = 21


def dusk(s, top=(46, 44, 55), bot=(15, 13, 20)):
    W, H = s.get_size()
    for y in range(H):
        f = (y / H) ** 0.85
        pygame.draw.line(s, tuple(int(top[k] + (bot[k] - top[k]) * f) for k in range(3)),
                         (0, y), (W, y))


def lab(s, t, x, y, c=(214, 208, 194), sz=26):
    s.blit(pygame.font.Font(None, sz).render(t, True, c), (x, y))


W, H = 1340, 1200
out = pygame.Surface((W, H))
dusk(out)

# ---- Panel 1: the MASK as a full-360 3D object ------------------------------
lab(out, "1.  THE MASK IN FULL 3D  --  yaw spins it 360: His face toward you, a curved lens at profile, the blank back turned away (no eyes)", 18, 14)
for i, (deg, tag) in enumerate([(0, "0  face"), (60, "60"), (90, "90  profile"),
                                (135, "135"), (180, "180  back"), (300, "300")]):
    cx = 130 + i * 200
    draw_pallid_mask_part(out, cx, 190, 54, deploy=1.0, gaze=(0.0, 0.2),
                          yaw=math.radians(deg), seed=7)
    lab(out, tag, cx - 42, 272, (150, 146, 134), 22)

# ---- Panel 2: the POWER-UP (plain amalgam vs possessed bearer) --------------
y2 = 330
lab(out, "2.  THE POWER-UP  --  a plain amalgam, then the SAME seed possessed: a BIGGER body + the Mask + His crown of cuts", 18, y2)
# a player for scale
draw_player_sprite(out, 150, y2 + 250, (0, 1), view="front")
lab(out, "player", 120, y2 + 262, (150, 146, 134), 22)
draw_amalgam_sprite(out, 470, y2 + 250, seed=21, birth=1.0)
lab(out, "plain amalgam", 400, y2 + 262, (150, 146, 134), 22)
draw_amalgam_sprite(out, 900, y2 + 250, seed=21, birth=1.0,
                    mask={"r": MR, "deploy": 1.0, "gaze": (-0.4, 0.3), "yaw": 0.25})
lab(out, "POSSESSED (bearer)", 800, y2 + 262, (150, 146, 134), 22)

# ---- Panel 3: the ramp (the Mask jumping in bulks it up) --------------------
y3 = 740
lab(out, "3.  POSSESSION RAMP  --  the body is already big; the Mask rises and the crown kindles as His regard settles", 18, y3)
for i, (p, tag) in enumerate([(0.15, "arriving"), (0.5, "surging"),
                              (1.0, "borne (full)")]):
    cx = 260 + i * 400
    draw_amalgam_sprite(out, cx, y3 + 330, seed=21, birth=1.0,
                        mask={"r": MR, "deploy": p, "gaze": (-0.3, 0.3), "yaw": 0.2})
    lab(out, f"{tag}  (deploy {p:.2f})", cx - 90, y3 + 345, (150, 146, 134), 24)

pygame.image.save(out, "/tmp/bearer.png")
print("/tmp/bearer.png", out.get_size())
