#!/usr/bin/env python3
"""Preview the Pallid Mask PART (rendering/amalgam.draw_pallid_mask_part /
carved_pallid_surface). Proves the two hard rules from the design:
  1. the Mask is SMALLER THAN THE PLAYER (measured against the real
     draw_player_sprite bounding box), and
  2. it ALWAYS FACES THE PI -- bearers ringed around the player all show
     the face head-on, eyes tracking the player.
Plus the deploy ramp (surface -> borne -> sink) at part scale.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
        python tools/preview_pallid_part.py
Writes /tmp/pallid_part.png.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import math
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
from rendering.amalgam import (draw_amalgam_sprite, draw_pallid_mask_part,  # noqa: E402
                               carved_pallid_surface)
from rendering.sprites_player import draw_player_sprite                      # noqa: E402


def player_height():
    t = pygame.Surface((240, 240), pygame.SRCALPHA)
    draw_player_sprite(t, 120, 170, (0, 1), view="front")
    r = t.get_bounding_rect()
    return r.height, t, r


def dusk(s, top=(46, 44, 55), bot=(17, 15, 22)):
    W, H = s.get_size()
    for y in range(H):
        f = (y / H) ** 0.85
        pygame.draw.line(s, tuple(int(top[k] + (bot[k] - top[k]) * f) for k in range(3)),
                         (0, y), (W, y))


def label(s, txt, x, y, col=(214, 208, 194), sz=24):
    s.blit(pygame.font.Font(None, sz).render(txt, True, col), (x, y))


PH, pt, prect = player_height()
# the Mask is His hand-object off the altar: target ~45% of player height.
# carved_pallid_surface face height ~= 2*ry = 2*1.05r, so r = 0.45*PH/2.1.
MR = max(6, int(0.45 * PH / 2.1))

W, H = 1300, 1180
out = pygame.Surface((W, H))
dusk(out)

# ---- Panel 1: ALWAYS FACES THE PI (player centre, bearers ringed) ----------
label(out, "ALWAYS FACES THE PI  --  bearers ringed around the player, the Mask head-on and eyes tracking", 18, 12)
label(out, f"(player sprite height = {PH}px; Mask face height ~= {int(2.1*MR)}px, ~{int(200*MR*1.05/PH)}% of the player)",
      18, 40, (150, 146, 134))
pcx, pcy = W // 2, 300
# player at the centre
draw_player_sprite(out, pcx, pcy, (0, 1), view="front")
pygame.draw.circle(out, (90, 100, 120), (pcx, pcy - PH // 2), 3)   # the "eye" target
ring = [(pcx, pcy - 210, "N"), (pcx + 320, pcy - 20, "E"),
        (pcx, pcy + 150, "S"), (pcx - 320, pcy - 20, "W")]
for i, (bx, by, tag) in enumerate(ring):
    draw_amalgam_sprite(out, bx, by, seed=400 + i * 13, birth=1.0)
    # gaze points from the mask toward the player eye (screen space, -1..1)
    mgx = pcx - bx
    mgy = (pcy - PH // 2) - (by - 44)
    ml = math.hypot(mgx, mgy) or 1
    draw_amalgam_sprite(out, bx, by, seed=400 + i * 13, birth=1.0,
                        mask={"r": MR, "deploy": 1.0,
                              "gaze": (mgx / ml, mgy / ml), "seed": 7 + i})
    label(out, tag, bx - 6, by + 10, (150, 146, 134), 22)

# ---- Panel 2: SUB-PLAYER SCALE (player vs the mask alone, 3 sizes) ----------
y2 = 560
label(out, "SUB-PLAYER SCALE  --  the player, then the Mask part alone at three sizes", 18, y2)
bx = 150
# the measured player, isolated
out.blit(pt, (bx - 120, y2 + 40))
label(out, "player", bx - 34, y2 + 40 + prect.height + 8, (150, 146, 134), 22)
for i, (frac, tag) in enumerate([(0.35, "0.35x"), (0.45, "0.45x (target)"), (0.6, "0.6x")]):
    cx = 470 + i * 260
    r = max(6, int(frac * PH / 2.1))
    cy = y2 + 60 + PH // 2
    # a faint player-height rule beside it
    pygame.draw.line(out, (70, 74, 84), (cx - 90, cy - PH // 2), (cx - 90, cy + PH // 2), 2)
    draw_pallid_mask_part(out, cx, cy, r, deploy=1.0, gaze=(-0.2, 0.3), seed=7)
    label(out, tag, cx - 40, cy + PH // 2 + 10, (150, 146, 134), 22)

# ---- Panel 3: THE DEPLOY RAMP (surface -> borne -> sink) --------------------
y3 = 900
label(out, "THE DEPLOY RAMP  --  the Mask rides out of its cut, held by the flesh, embers guttering as it sinks", 18, y3)
for i, (d, tag) in enumerate([(0.35, "surfacing"), (0.7, "cresting"), (1.0, "borne (His regard)"),
                              (0.5, "sinking"), (0.15, "gone (to rise elsewhere)")]):
    cx = 170 + i * 245
    cy = y3 + 130
    draw_pallid_mask_part(out, cx, cy, int(MR * 2.3), deploy=d, gaze=(-0.2, 0.35), seed=7)
    label(out, tag, cx - 70, y3 + 240, (150, 146, 134), 22)

path = "/tmp/pallid_part.png"
pygame.image.save(out, path)
print(f"player height {PH}px  mask r {MR}  ->  {path} {out.get_size()}")
