"""Close-up examine TABLEAUX -- the diegetic "look at the thing" cutscenes.

Press [E] on a tagged prop and the world pauses on a high-detail, animated
close-up of that thing, with a menu of options that mutate the tableau live
(take the gun -> it leaves the table) and can open readable text. One system,
reused for the bedroom desk (the pilot), and later a pedestal / a face across
a table. Pure procedural draw, no assets (the project ethos).

The per-kind art fns live here; the state machine + menu + reading overlay
live on Game (`systems/tableau_mixin.py`). An art fn takes (surf, t, state)
and draws the close-up only -- the menu and reading overlay are generic UI
drawn by the mixin on top.
"""
import math
import random


def _lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def draw_desk_tableau(surf, t, state):
    """The writing desk in the spare room: the pistol + the open case file
    under the desk lamp. `state["gun_present"]` toggles the revolver off once
    it is taken (its clean outline stays in the dust)."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    gun_present = state.get("gun_present", True)

    # --- wood desk surface, warm lamp pool from the upper-left ---
    top = (26, 20, 13)
    bot = (13, 9, 5)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    # plank seams, slightly skewed so the grain reads under the tilt-ish angle
    for gx in range(-1, 8):
        x = int(gx * (W / 6) + 18 * math.sin(gx * 1.3))
        pygame.draw.line(surf, (9, 6, 3), (x, 0), (x + 46, H), 2)

    # lamp pool (warm radial, upper-left), a slow candle-flicker
    lamp = pygame.Surface((W, H), pygame.SRCALPHA)
    lx, ly = int(W * 0.30), int(H * 0.22)
    flick = 0.86 + 0.14 * math.sin(t * 5.3) * math.sin(t * 1.7)
    rad = int(H * 0.72)
    for r in range(rad, 0, -12):
        a = int(48 * (1 - r / rad) * flick)
        pygame.draw.circle(lamp, (255, 208, 120, a), (lx, ly), r)
    surf.blit(lamp, (0, 0))

    # dust motes drifting up through the lamp light
    rnd = random.Random(4)
    for _ in range(44):
        bx = rnd.randint(int(W * 0.10), int(W * 0.60))
        base = rnd.randint(0, int(H * 0.7))
        yy = int(H * 0.10 + (t * 9 + base) % (H * 0.72))
        a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.8 + bx))
        c = int(210 * a)
        surf.set_at((bx, yy), (255, 230, 180)) if 0 <= yy < H else None
        pygame.draw.circle(surf, (min(255, 200 + c // 4), 210, 170),
                           (bx, yy), 1)

    # --- the open case file: manila folder + typed page + clipped photo ---
    fx, fy = int(W * 0.44), int(H * 0.44)
    pw, ph = int(W * 0.31), int(H * 0.33)
    pygame.draw.polygon(surf, (50, 44, 33),
                        [(fx, fy), (fx + pw, fy - 22), (fx + pw + 18, fy + ph),
                         (fx + 14, fy + ph + 20)])
    pygame.draw.polygon(surf, (210, 202, 182),
                        [(fx + 22, fy + 6), (fx + pw - 12, fy - 10),
                         (fx + pw, fy + ph - 16), (fx + 30, fy + ph)])
    for i in range(7):
        yy = fy + 24 + i * int(ph / 8.5)
        ww = int(pw * 0.62) if i else int(pw * 0.34)
        pygame.draw.line(surf, (58, 50, 42), (fx + 40, yy),
                         (fx + 40 + ww, yy - 6), 3 if i == 0 else 2)
    # clipped photo of Mara (a grey portrait + paperclip)
    px_, py_ = fx + int(pw * 0.66), fy + 14
    pygame.draw.rect(surf, (148, 148, 152), (px_, py_, int(pw * 0.24),
                                             int(ph * 0.5)))
    pygame.draw.rect(surf, (92, 92, 98), (px_, py_, int(pw * 0.24),
                                          int(ph * 0.5)), 2)
    pygame.draw.ellipse(surf, (122, 122, 128),
                        (px_ + int(pw * 0.06), py_ + int(ph * 0.08),
                         int(pw * 0.12), int(ph * 0.2)))
    pygame.draw.arc(surf, (176, 176, 128),
                    (px_ + int(pw * 0.08), py_ - 12, 20, 38), 0.4, 3.4, 3)

    # --- the pistol, lying at an angle (or the clean spot where it lay) ---
    gx, gy = int(W * 0.17), int(H * 0.54)
    if gun_present:
        g = pygame.Surface((260, 150), pygame.SRCALPHA)
        # slide + frame
        pygame.draw.rect(g, (38, 40, 46), (26, 44, 158, 30), border_radius=5)
        pygame.draw.rect(g, (58, 61, 68), (26, 44, 158, 9), border_radius=4)
        pygame.draw.rect(g, (24, 25, 29), (36, 66, 120, 8))     # slide seam
        pygame.draw.circle(g, (128, 132, 140), (30, 59), 5)     # muzzle glint
        # wood grip, angled down
        pygame.draw.polygon(g, (70, 44, 24),
                            [(150, 64), (190, 66), (178, 130), (138, 118)])
        pygame.draw.polygon(g, (96, 62, 36),
                            [(150, 64), (170, 65), (162, 116), (144, 110)])
        pygame.draw.line(g, (48, 30, 16), (156, 74), (168, 112), 2)
        # trigger guard
        pygame.draw.arc(g, (30, 32, 36), (128, 60, 36, 44), 3.1, 6.1, 5)
        g = pygame.transform.rotate(g, 13)
        # a soft contact shadow under it
        sh = pygame.Surface(g.get_size(), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 0))
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (20, 90, 220, 40))
        surf.blit(sh, (gx - 6, gy + 12))
        surf.blit(g, (gx, gy))
    else:
        clean = pygame.Surface((190, 96), pygame.SRCALPHA)
        clean.fill((255, 220, 150, 14))
        pygame.draw.rect(clean, (255, 225, 160, 26), (0, 0, 190, 96), 2)
        clean = pygame.transform.rotate(clean, 13)
        surf.blit(clean, (gx + 18, gy + 8))

    # --- vignette to hold the eye on the lit pool ---
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = int(W * 0.42), int(H * 0.5)
    maxr = int(math.hypot(W, H) * 0.62)
    for r in range(maxr, int(maxr * 0.55), -10):
        a = int(150 * (1 - (r - maxr * 0.55) / (maxr * 0.45)))
        pygame.draw.circle(vig, (0, 0, 0, max(0, a)), (cx, cy), r)
    surf.blit(vig, (0, 0))
