"""Blind-spot sight preview (CAMERA.md Phase 4).

Top-down schematic of the line-of-sight model in rendering/sight.py: a player
in a small room with a few walls and a scatter of NPC markers. As the head
sweeps the +/-45 arc the sight cone swings; NPCs inside the cone AND with clear
line of sight light up (revealed), the rest stay dark (free to rearrange in the
blind spot). Walls cast LOS shadows. Top-down on purpose — this is a
ground-plane mechanic and the schematic reads clearest flat.

    python tools/preview_sight.py   -> /tmp/sight_demo.png (+ .gif)
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.sight import (cone_factor, los_clear, visible_factor,
                             SIGHT_HALF, SIGHT_RANGE, SIGHT_ANG_FEATHER)

TILE = 32
COLS, ROWS = 16, 12
W, H = COLS * TILE, ROWS * TILE
BG = (10, 10, 14)
FLOOR_A = (30, 28, 26)
FLOOR_B = (25, 23, 22)
WALL = (64, 56, 48)
CONE = (210, 180, 96)

# A few wall tiles (tx, ty) the player must see around.
WALLS = {(7, 3), (7, 4), (7, 5), (11, 7), (12, 7), (4, 8), (5, 8)}

PLAYER = (5 * TILE + 16, 6 * TILE + 16)

# NPC / item markers scattered about — some in cone, some behind walls.
MARKERS = [
    (9 * TILE + 16, 4 * TILE + 16, "npc"),    # behind the vertical wall
    (10 * TILE + 16, 6 * TILE + 16, "npc"),   # open, ahead-right
    (8 * TILE + 16, 8 * TILE + 16, "item"),   # lower-right
    (2 * TILE + 16, 6 * TILE + 16, "npc"),    # directly behind/left
    (5 * TILE + 16, 2 * TILE + 16, "npc"),    # straight up
    (13 * TILE + 16, 8 * TILE + 16, "item"),  # far, behind the low wall
    (3 * TILE + 16, 9 * TILE + 16, "npc"),    # behind the lower wall
]


def blocks(x, y):
    tx, ty = int(x // TILE), int(y // TILE)
    return (tx, ty) in WALLS


def draw_floor(surf):
    for ty in range(ROWS):
        for tx in range(COLS):
            r = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
            if (tx, ty) in WALLS:
                pygame.draw.rect(surf, WALL, r)
                pygame.draw.rect(surf, (20, 18, 16), r, 1)
            else:
                pygame.draw.rect(surf, FLOOR_A if (tx + ty) % 2 == 0 else FLOOR_B, r)


def draw_cone(surf, heading):
    """Shade the visible region: sample the floor on a coarse grid and tint
    each cell by visible_factor (cone membership gated by walls)."""
    cone = pygame.Surface((W, H), pygame.SRCALPHA)
    px, py = PLAYER
    s = 8
    for y in range(0, H, s):
        for x in range(0, W, s):
            f = visible_factor(px, py, heading, x + s / 2, y + s / 2, blocks)
            if f > 0.02:
                a = int(70 * f)
                pygame.draw.rect(cone, (*CONE, a), (x, y, s, s))
    surf.blit(cone, (0, 0))
    # cone edge rays for legibility
    for edge in (-1, 1):
        ang = heading + edge * SIGHT_HALF
        ex = px + math.cos(ang) * SIGHT_RANGE
        ey = py + math.sin(ang) * SIGHT_RANGE
        pygame.draw.line(surf, (150, 130, 70), (px, py), (ex, ey), 1)


def draw_player(surf, heading):
    px, py = PLAYER
    pygame.draw.circle(surf, (150, 120, 70), (px, py), 7)
    pygame.draw.circle(surf, (220, 190, 120), (px, py), 7, 1)
    # facing tick
    pygame.draw.line(surf, (240, 220, 150), (px, py),
                     (px + math.cos(heading) * 14, py + math.sin(heading) * 14), 2)


def draw_markers(surf, heading, font):
    px, py = PLAYER
    for (mx, my, kind) in MARKERS:
        f = visible_factor(px, py, heading, mx, my, blocks)
        seen = f >= 0.5
        if kind == "item":
            base = (90, 200, 150)
        else:
            base = (210, 90, 90)
        if seen:
            col = base
            pygame.draw.circle(surf, col, (mx, my), 6)
            pygame.draw.circle(surf, (255, 255, 255), (mx, my), 6, 1)
            lab = font.render("SEEN", True, (240, 240, 240))
        else:
            # hidden: a faint ghost — in the live game it simply isn't drawn,
            # and is free to move. Shown dim here so the preview is legible.
            col = tuple(c // 4 for c in base)
            pygame.draw.circle(surf, col, (mx, my), 5)
            pygame.draw.circle(surf, (60, 60, 60), (mx, my), 5, 1)
            lab = font.render("hidden", True, (110, 110, 110))
        surf.blit(lab, (mx - lab.get_width() // 2, my + 8))


def render(head_deg):
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    font = pygame.font.SysFont("monospace", 9)
    # heading: "up" the screen is -90deg; the head peeks +/- around forward.
    heading = math.radians(-90 + head_deg)
    draw_floor(surf)
    draw_cone(surf, heading)
    draw_markers(surf, heading, font)
    draw_player(surf, heading)
    return surf


def strip():
    font = pygame.font.SysFont("monospace", 12)
    heads = [-45, -22, 0, 22, 45]
    out = pygame.Surface((W * len(heads), H + 20))
    out.fill((6, 6, 8))
    for i, hd in enumerate(heads):
        out.blit(render(hd), (i * W, 0))
        tag = "FORWARD" if hd == 0 else f"head {hd:+d}deg"
        out.blit(font.render(tag, True, (180, 180, 190)), (i * W + 8, H + 4))
    pygame.image.save(out, "/tmp/sight_demo.png")
    print("wrote /tmp/sight_demo.png  (half=%.0fdeg range=%.0f)" % (
        math.degrees(SIGHT_HALF), SIGHT_RANGE))


def gif():
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; skipping gif"); return
    frames = []
    N = 60
    for i in range(N):
        head = 45 * math.sin(i / N * 2 * math.pi)
        s = render(head)
        raw = pygame.image.tostring(s, "RGB")
        frames.append(Image.frombytes("RGB", (W, H), raw).convert("P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/sight_demo.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/sight_demo.gif")


if __name__ == "__main__":
    strip()
    gif()
