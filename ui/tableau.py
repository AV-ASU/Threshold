"""Close-up examine TABLEAUX -- the diegetic "look at the thing" cutscenes.

Press [E] on a tagged prop and the world pauses on a high-detail, animated
close-up of that thing, with a menu of options that mutate the tableau live
(take the gun -> it leaves the table) and can open readable text. One system,
reused for the bedroom desk (the pilot) and the face-across-a-table principal
talks (Sable's reception desk, Vane's office), and later a pedestal. Pure
procedural draw, no assets (the project ethos).

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


# ---- Sable: his clerk sprite as a close-up host behind the reception desk --
# The human+grit MEDIUM (NARRATIVE §4, the lucky one who was happier when the
# house was full): a human face with tired eyes and a warm sad host smile,
# carried on his sprite's outfit (a dark open coat framing a wide white
# shirt-front, a short red tie). Reactive: a slow ceiling-fan shadow sweep,
# dust, a host blink, a breathing bob, and the state-gated props (the photo
# slid onto the register, the wax-sealed Invitation laid down). cx,cy = head
# centre; the lamp lights his left.
def _draw_sable(surf, cx, cy, blink, gaze_photo):
    import pygame
    skin = (172, 163, 143); sk_hi = (202, 191, 165); sk_lo = (116, 108, 90)
    sk_sh = (78, 71, 58); hair = (40, 34, 30); hair_hi = (72, 62, 52)
    grey = (128, 120, 106); part = (58, 51, 45)
    coat = (40, 36, 43); coat_drk = (20, 18, 23); coat_lit = (58, 53, 62)
    shirt = (202, 200, 195); shirt_sh = (150, 148, 145); collar = (216, 214, 209)
    tie = (120, 30, 36); brow_c = (52, 45, 40)
    HW, HH = 54, 66
    tt = cy + HH - 4
    pygame.draw.polygon(surf, coat, [(cx - 96, tt + 12), (cx + 96, tt + 12),
                                     (cx + 80, tt + 300), (cx - 80, tt + 300)])
    pygame.draw.ellipse(surf, coat, (cx - 100, tt - 8, 78, 54))
    pygame.draw.ellipse(surf, coat, (cx + 22, tt - 8, 78, 54))
    pygame.draw.polygon(surf, coat_drk, [(cx + 12, tt + 12), (cx + 96, tt + 12),
                                         (cx + 80, tt + 300), (cx + 10, tt + 300)])
    pygame.draw.polygon(surf, coat_lit, [(cx - 96, tt + 12), (cx - 88, tt + 12),
                                         (cx - 82, tt + 300), (cx - 96, tt + 300)])
    pygame.draw.polygon(surf, shirt, [(cx - 32, tt + 22), (cx + 32, tt + 22),
                                      (cx + 27, tt + 300), (cx - 27, tt + 300)])
    pygame.draw.polygon(surf, shirt_sh, [(cx + 5, tt + 22), (cx + 32, tt + 22),
                                         (cx + 27, tt + 300), (cx + 5, tt + 300)])
    pygame.draw.polygon(surf, collar, [(cx - 32, tt + 16), (cx - 2, tt + 30),
                                       (cx - 22, tt + 52)])
    pygame.draw.polygon(surf, collar, [(cx + 32, tt + 16), (cx + 2, tt + 30),
                                       (cx + 22, tt + 52)])
    pygame.draw.polygon(surf, tie, [(cx - 9, tt + 30), (cx + 9, tt + 30),
                                    (cx + 12, tt + 150), (cx, tt + 170), (cx - 12, tt + 150)])
    pygame.draw.polygon(surf, (94, 22, 28), [(cx - 9, tt + 30), (cx + 9, tt + 30), (cx, tt + 46)])
    pygame.draw.rect(surf, sk_lo, (cx - 15, cy + HH - 22, 30, 40))
    pygame.draw.ellipse(surf, sk_sh, (cx - 20, cy + HH - 6, 40, 16))
    pygame.draw.ellipse(surf, skin, (cx - HW, cy - HH, HW * 2, HH * 2))
    dim = pygame.Surface((HW * 2, HH * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(dim, (*sk_sh, 150), (HW - 6, 8, HW + 6, HH * 2 - 20))
    surf.blit(dim, (cx - HW, cy - HH))
    lit = pygame.Surface((HW * 2, HH * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(lit, (*sk_hi, 120), (6, HH - 44, HW - 4, 76))
    surf.blit(lit, (cx - HW, cy - HH))
    pygame.draw.circle(surf, skin, (cx - HW + 2, cy + 2), 8)
    pygame.draw.circle(surf, sk_lo, (cx + HW - 2, cy + 2), 8)
    pygame.draw.ellipse(surf, hair, (cx - HW - 2, cy - HH - 6, HW * 2 + 4, 80))
    pygame.draw.ellipse(surf, skin, (cx - 40, cy - 34, 80, 42))
    pygame.draw.arc(surf, hair_hi, (cx - 42, cy - HH, 50, 44), 1.15, 2.75, 4)
    pygame.draw.line(surf, part, (cx + 6, cy - 42), (cx + 14, cy - 22), 3)
    pygame.draw.line(surf, grey, (cx - HW + 3, cy - 18), (cx - HW + 7, cy + 6), 3)
    pygame.draw.line(surf, grey, (cx + HW - 7, cy - 18), (cx + HW - 3, cy + 6), 3)
    pygame.draw.line(surf, sk_lo, (cx - 34, cy - 26), (cx + 34, cy - 27), 1)
    pygame.draw.line(surf, brow_c, (cx - 30, cy - 15), (cx - 10, cy - 17), 3)
    pygame.draw.line(surf, brow_c, (cx + 10, cy - 17), (cx + 30, cy - 15), 3)
    for sgn in (-1, 1):
        ex = cx + sgn * 22
        ey = cy - 4
        pygame.draw.ellipse(surf, sk_lo, (ex - 18, ey - 10, 36, 19))
        if blink:
            pygame.draw.ellipse(surf, skin, (ex - 15, ey - 7, 30, 15))
            pygame.draw.line(surf, sk_sh, (ex - 14, ey), (ex + 14, ey), 2)
        else:
            pygame.draw.ellipse(surf, (212, 206, 190), (ex - 14, ey - 6, 28, 14))
            ix = ex + (4 if gaze_photo else 0)
            iy = ey + (4 if gaze_photo else 2)
            pygame.draw.circle(surf, (94, 80, 64), (ix, iy), 6)
            pygame.draw.circle(surf, (24, 20, 16), (ix, iy), 3)
            pygame.draw.circle(surf, (226, 222, 208), (ix - 2, iy - 2), 1)
            pygame.draw.line(surf, sk_sh, (ex - 14, ey - 6), (ex + 13, ey - 7), 2)
        pygame.draw.line(surf, sk_lo, (ex - 11, ey + 8), (ex + 11, ey + 8), 1)
        pygame.draw.line(surf, sk_lo, (ex + sgn * 15, ey - 3), (ex + sgn * 19, ey), 1)
    pygame.draw.line(surf, sk_lo, (cx + 1, cy - 12), (cx - 3, cy + 11), 2)
    pygame.draw.line(surf, sk_hi, (cx - 3, cy - 12), (cx - 6, cy + 8), 1)
    pygame.draw.ellipse(surf, sk_hi, (cx - 5, cy + 6, 8, 7))
    pygame.draw.circle(surf, sk_sh, (cx - 6, cy + 14), 2)
    pygame.draw.circle(surf, sk_sh, (cx + 4, cy + 14), 2)
    my = cy + 29
    pygame.draw.lines(surf, (128, 88, 82), False,
                      [(cx - 20, my - 3), (cx - 8, my + 2), (cx + 8, my + 2), (cx + 20, my - 3)], 3)
    pygame.draw.lines(surf, (182, 148, 132), False,
                      [(cx - 11, my + 5), (cx, my + 6), (cx + 11, my + 5)], 2)


def draw_sable_tableau(surf, t, state):
    """The Arcadia reception desk close-up. `state` reads two live flags: the
    photo slid onto the register (`photo_present`) and the wax-sealed
    Invitation laid on the counter (`envelope_present`)."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    photo = state.get("photo_present", False)
    envelope = state.get("envelope_present", False)
    top = (48, 37, 27); bot = (19, 14, 9)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    wains = int(H * 0.54)
    for sx in range(0, W, 44):
        pygame.draw.line(surf, (42, 32, 24), (sx, 0), (sx, wains), 1)
    pygame.draw.rect(surf, (22, 16, 10), (0, wains, W, 6))
    pygame.draw.rect(surf, (26, 19, 12), (0, wains + 6, W, H - wains))
    ccx, ccy, cr = int(W * 0.14), int(H * 0.19), 40                  # stopped clock
    pygame.draw.circle(surf, (150, 142, 120), (ccx, ccy), cr)
    pygame.draw.circle(surf, (22, 16, 10), (ccx, ccy), cr, 5)
    pygame.draw.circle(surf, (60, 50, 38), (ccx, ccy), cr - 5, 1)
    pygame.draw.line(surf, (30, 24, 18), (ccx, ccy), (ccx + int(cr * 0.5), ccy - 6), 3)
    pygame.draw.line(surf, (30, 24, 18), (ccx, ccy), (ccx - 4, ccy - int(cr * 0.66)), 2)
    pygame.draw.circle(surf, (20, 14, 9), (ccx, ccy), 3)
    bx, by, bw, bh = int(W * 0.56), int(H * 0.07), int(W * 0.36), int(H * 0.40)  # key wall
    pygame.draw.rect(surf, (46, 34, 22), (bx, by, bw, bh))
    pygame.draw.rect(surf, (26, 19, 12), (bx, by, bw, bh), 4)
    for r in range(4):
        for c in range(6):
            hx = bx + int((c + 0.5) * bw / 6)
            hy = by + int((r + 0.5) * bh / 4)
            pygame.draw.circle(surf, (72, 56, 36), (hx, hy), 2)
            if (r * 6 + c) not in (7, 15):
                pygame.draw.circle(surf, (150, 140, 96), (hx, hy + 8), 4, 2)
                pygame.draw.line(surf, (150, 140, 96), (hx, hy + 12), (hx, hy + 24), 2)
                pygame.draw.line(surf, (150, 140, 96), (hx, hy + 24), (hx + 4, hy + 24), 2)
    fan = pygame.Surface((W, H), pygame.SRCALPHA)                     # ceiling-fan sweep
    fcx, fcy = int(W * 0.44), -int(H * 0.05)
    for k in range(4):
        a = t * 0.5 + k * math.pi / 2
        pygame.draw.line(fan, (0, 0, 0, 24), (fcx, fcy),
                         (int(fcx + math.cos(a) * W * 0.75), int(fcy + math.sin(a) * W * 0.75)), 52)
    surf.blit(fan, (0, 0))
    flick = 0.9 + 0.1 * math.sin(t * 5.3) * math.sin(t * 1.7)
    amb = pygame.Surface((W, H), pygame.SRCALPHA)
    lx, ly = int(W * 0.26), int(H * 0.46)
    for r in range(int(H * 0.9), 0, -16):
        pygame.draw.circle(amb, (150, 116, 66, int(30 * (1 - r / (H * 0.9)) * flick)), (lx, ly), r)
    surf.blit(amb, (0, 0))
    rnd = random.Random(7)                                           # dust motes
    for _ in range(40):
        mx = rnd.randint(int(W * 0.10), int(W * 0.62))
        base = rnd.randint(0, int(H * 0.6))
        yy = int(H * 0.16 + (t * 8 + base) % (H * 0.62))
        pygame.draw.circle(surf, (240, 214, 168), (mx, yy), 1)
    bob = int(2 * math.sin(t * 1.25))                                # Sable + blink + bob
    _draw_sable(surf, int(W * 0.37), int(H * 0.25) + bob, (t % 4.2) < 0.16, gaze_photo=photo)
    ctop = int(H * 0.63)                                             # counter
    pygame.draw.polygon(surf, (34, 25, 15), [(0, ctop), (W, ctop), (W, H), (0, H)])
    pygame.draw.polygon(surf, (50, 38, 23),
                        [(int(W * 0.05), ctop - 30), (int(W * 0.95), ctop - 30), (W, ctop), (0, ctop)])
    pygame.draw.line(surf, (78, 60, 36), (0, ctop), (W, ctop), 2)
    for gx in range(0, W, 120):
        pygame.draw.line(surf, (24, 17, 10), (gx, ctop + 6), (gx - 10, H), 1)
    lsx = int(W * 0.14)                                              # lamp
    pygame.draw.rect(surf, (28, 22, 14), (lsx + 4, ctop - 34, 10, 34))
    pygame.draw.polygon(surf, (58, 46, 26),
                        [(lsx - 6, ctop - 34), (lsx + 24, ctop - 34), (lsx + 18, ctop - 52), (lsx, ctop - 52)])
    pygame.draw.ellipse(surf, (255, 222, 150), (lsx, ctop - 38, 22, 8))
    rx, ry = int(W * 0.30), ctop - 4                                 # register + the lead
    pygame.draw.polygon(surf, (58, 50, 38),
                        [(rx, ry), (rx + 156, ry - 16), (rx + 176, ry + 16), (rx + 18, ry + 34)])
    pygame.draw.polygon(surf, (206, 198, 176),
                        [(rx + 12, ry - 2), (rx + 146, ry - 14), (rx + 158, ry + 12), (rx + 24, ry + 26)])
    for i in range(6):
        pygame.draw.line(surf, (120, 110, 92), (rx + 24, ry + 2 + i * 4), (rx + 128, ry - 6 + i * 4), 1)
    pygame.draw.line(surf, (150, 130, 70), (rx + 150, ry - 8), (rx + 160, ry + 26), 3)
    pygame.draw.circle(surf, (30, 26, 22), (rx + 160, ry + 26), 2)
    blx, bly = int(W * 0.60), ctop + 4                               # service bell
    pygame.draw.ellipse(surf, (70, 64, 48), (blx - 4, bly + 2, 52, 9))
    pygame.draw.ellipse(surf, (118, 110, 84), (blx, bly - 18, 44, 22))
    pygame.draw.ellipse(surf, (156, 148, 116), (blx + 7, bly - 15, 18, 8))
    pygame.draw.rect(surf, (92, 86, 66), (blx + 18, bly - 26, 8, 9))
    if photo:                                                        # the photo (flat on the desk)
        px, py = int(W * 0.44), ctop - 4
        quad = [(px, py), (px + 74, py - 5), (px + 68, py - 27), (px - 6, py - 22)]
        pygame.draw.polygon(surf, (0, 0, 0), [(x + 3, y + 4) for x, y in quad])
        pygame.draw.polygon(surf, (150, 148, 152), quad)
        pygame.draw.polygon(surf, (92, 92, 98), quad, 2)
        pygame.draw.ellipse(surf, (120, 120, 126), (px + 24, py - 21, 22, 18))
        pygame.draw.polygon(surf, (108, 108, 114),
                            [(px + 16, py - 7), (px + 54, py - 10), (px + 52, py - 2), (px + 14, py + 1)])
    if envelope:                                                     # the Invitation (flat, sealed)
        ex, ey = int(W * 0.43), ctop - 2
        quad = [(ex, ey), (ex + 152, ey - 10), (ex + 142, ey - 46), (ex - 10, ey - 36)]
        pygame.draw.polygon(surf, (0, 0, 0), [(x + 4, y + 5) for x, y in quad])
        pygame.draw.polygon(surf, (208, 196, 170), quad)
        pygame.draw.polygon(surf, (176, 164, 138), quad, 2)
        nmid = ((quad[0][0] + quad[1][0]) // 2, (quad[0][1] + quad[1][1]) // 2)
        pygame.draw.polygon(surf, (194, 182, 156), [quad[3], quad[2], nmid])
        pygame.draw.line(surf, (150, 140, 118), quad[3], nmid, 1)
        pygame.draw.line(surf, (150, 140, 118), quad[2], nmid, 1)
        sx, sy = nmid[0], nmid[1] - 6
        pygame.draw.ellipse(surf, (128, 24, 30), (sx - 14, sy - 8, 28, 16))
        pygame.draw.ellipse(surf, (150, 40, 44), (sx - 14, sy - 8, 28, 16), 2)
        pygame.draw.line(surf, (150, 140, 60), (sx - 6, sy - 3), (sx + 6, sy + 3), 2)
        pygame.draw.line(surf, (150, 140, 60), (sx + 6, sy - 3), (sx - 6, sy + 3), 2)
    key = pygame.Surface((W, H), pygame.SRCALPHA)                    # warm lamp wash
    kx, ky = int(W * 0.33), int(H * 0.36)
    for r in range(int(H * 0.9), 0, -12):
        pygame.draw.circle(key, (255, 208, 142, int(94 * (1 - r / (H * 0.9)) * flick)), (kx, ky), r)
    surf.blit(key, (0, 0))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)                    # eased vignette
    vcx, vcy = int(W * 0.40), int(H * 0.44)
    maxr = int(math.hypot(W, H) * 0.66); inner = int(maxr * 0.56)
    for r in range(maxr, inner, -10):
        pygame.draw.circle(vig, (0, 0, 0, max(0, int(150 * (1 - (r - inner) / (maxr - inner))))), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- Vane: his sheriff sprite as a close-up lawman behind the office desk --
# The human+grit register (the Sable precedent): a broad, square-jawed face
# under the brimmed hat, tired eyes inside the brim's shadow, stubble, a set
# flat mouth. Poses read the hidden ledger as body language: neutral squares
# up and waits you out; despair turns his head toward the window (he is not
# looking at you); hope leans him in, a forearm on the desk.
def _draw_vane(surf, cx, cy, blink, mood):
    import pygame
    skin = (170, 160, 132); sk_hi = (198, 186, 156); sk_lo = (118, 111, 89)
    sk_sh = (82, 77, 62); stub = (100, 96, 79)
    shirt = (110, 97, 67); shirt_dk = (70, 61, 43); shirt_lt = (134, 119, 84)
    hc = (66, 51, 36); hc_hi = (98, 79, 54); hb = (48, 36, 24); hb_lo = (30, 22, 15)
    star = (158, 148, 90); star_dk = (100, 92, 52)
    turn = 22 if mood == "despair" else 0          # head toward the window
    lean = 6 if mood == "hope" else 0              # leaning in, a notch lower
    cy = cy + lean
    HW, HH = 58, 64                                # broad, squarer than Sable
    tt = cy + HH - 2

    # -- torso: the tan duty shirt on a wide frame --
    pygame.draw.polygon(surf, shirt, [(cx - 124, tt + 8), (cx + 124, tt + 8),
                                      (cx + 106, tt + 300), (cx - 106, tt + 300)])
    pygame.draw.ellipse(surf, shirt, (cx - 130, tt - 16, 100, 58))   # shoulders
    pygame.draw.ellipse(surf, shirt, (cx + 30, tt - 16, 100, 58))
    pygame.draw.polygon(surf, shirt_dk, [(cx - 124, tt + 8), (cx - 110, tt + 8),
                                         (cx - 100, tt + 300), (cx - 106, tt + 300)])
    pygame.draw.polygon(surf, shirt_lt, [(cx + 106, tt + 8), (cx + 124, tt + 8),
                                         (cx + 106, tt + 300), (cx + 92, tt + 300)])
    pygame.draw.line(surf, shirt_dk, (cx, tt + 30), (cx, tt + 300), 2)   # placket
    for py_ in (tt + 60, tt + 104):                                      # buttons
        pygame.draw.circle(surf, (60, 52, 36), (cx, py_), 3)
    # collar: open one button over a dark undershirt notch
    pygame.draw.polygon(surf, shirt_lt, [(cx - 44, tt + 6), (cx - 4, tt + 28),
                                         (cx - 32, tt + 52)])
    pygame.draw.polygon(surf, shirt, [(cx + 44, tt + 6), (cx + 4, tt + 28),
                                      (cx + 32, tt + 52)])
    pygame.draw.polygon(surf, (32, 28, 22), [(cx - 9, tt + 24), (cx + 9, tt + 24),
                                             (cx, tt + 44)])
    # breast pockets with flaps; the tin star above the viewer-left pocket
    for sgn in (-1, 1):
        px_ = cx + sgn * 62
        pygame.draw.rect(surf, shirt_dk, (px_ - 21, tt + 78, 42, 34), 2)
        pygame.draw.polygon(surf, shirt_dk, [(px_ - 21, tt + 78), (px_ + 21, tt + 78),
                                             (px_, tt + 89)])
    scx, scy = cx - 62, tt + 58                                          # the star
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        r = 17 if k % 2 == 0 else 7
        pts.append((scx + int(r * math.cos(ang)), scy + int(r * math.sin(ang))))
    pygame.draw.polygon(surf, star, pts)
    pygame.draw.polygon(surf, star_dk, pts, 2)
    pygame.draw.circle(surf, star_dk, (scx, scy), 4, 1)

    # -- neck + head --
    pygame.draw.rect(surf, sk_lo, (cx - 17 + turn // 2, cy + HH - 22, 34, 40))
    pygame.draw.ellipse(surf, sk_sh, (cx - 24 + turn // 2, cy + HH - 6, 48, 16))
    hx = cx + turn                                  # feature centre (turned head)
    pygame.draw.ellipse(surf, skin, (cx - HW, cy - HH, HW * 2, HH * 2))
    # square the skull into the heavy jaw (the sprite's box); follows the turn
    pygame.draw.polygon(surf, skin, [(cx - HW + 12, cy + 12), (cx + HW - 8 + turn // 2, cy + 12),
                                     (cx + HW - 14 + turn // 2, cy + HH + 2),
                                     (hx + 18, cy + HH + 16), (hx - 18, cy + HH + 16),
                                     (cx - HW + 20, cy + HH + 2)])
    # lit toward the window (viewer-right), shadowed left
    dim = pygame.Surface((HW * 2 + 24, HH * 2 + 24), pygame.SRCALPHA)
    pygame.draw.ellipse(dim, (*sk_sh, 110), (0, 12, HW - 2 - turn, HH * 2 - 14))
    surf.blit(dim, (cx - HW, cy - HH))
    lit = pygame.Surface((HW * 2 + 24, HH * 2 + 24), pygame.SRCALPHA)
    pygame.draw.ellipse(lit, (*sk_hi, 120), (HW + 10, HH - 42, HW - 6, 82))
    surf.blit(lit, (cx - HW, cy - HH))
    pygame.draw.circle(surf, sk_lo, (cx - HW + 2, cy + 6), 9)            # ears
    pygame.draw.circle(surf, skin, (cx + HW - 2, cy + 6), 9)

    # -- the hat, worn low but CLEAR of the eyes: brim at brow height --
    bw = HW + 36
    pygame.draw.ellipse(surf, hb, (cx - bw, cy - 56, bw * 2, 36))        # brim
    pygame.draw.ellipse(surf, hb_lo, (cx - bw + 6, cy - 46, bw * 2 - 12, 22))  # underside
    pygame.draw.ellipse(surf, hc, (cx - HW + 2, cy - HH - 34, HW * 2 - 4, 66))  # crown
    pygame.draw.ellipse(surf, hc_hi, (cx - HW + 14, cy - HH - 30, HW + 6, 20))  # crown light
    pygame.draw.line(surf, (24, 18, 12), (cx - 22, cy - HH - 26), (cx + 2, cy - HH - 6), 2)  # dent
    pygame.draw.rect(surf, hb_lo, (cx - HW + 6, cy - 60, HW * 2 - 12, 9))       # hat band
    # the brim's soft shadow across the brow (the sprite's dark band, gentled)
    band = pygame.Surface((HW * 2, 26), pygame.SRCALPHA)
    for i in range(26):
        band.fill((30, 26, 20, max(0, 84 - i * 4)), (0, i, HW * 2, 1))
    surf.blit(band, (cx - HW, cy - 34))

    # -- face: heavy brows, tired eyes, blunt nose, set mouth, stubble --
    blift = 3 if mood == "hope" else 0             # the brows come up a notch
    pygame.draw.line(surf, (58, 50, 38), (hx - 34, cy - 16 - blift), (hx - 8, cy - 19 - blift), 5)
    pygame.draw.line(surf, (58, 50, 38), (hx + 8, cy - 19 - blift), (hx + 34, cy - 16 - blift), 5)
    for sgn in (-1, 1):
        ex = hx + sgn * 22
        ey = cy - 4
        if blink:
            pygame.draw.line(surf, sk_sh, (ex - 12, ey + 1), (ex + 12, ey + 1), 3)
        else:
            pygame.draw.ellipse(surf, (206, 200, 182), (ex - 13, ey - 6, 26, 13))
            ix = ex + (7 if mood == "despair" else 0)                    # eyes off you
            iy = ey + (0 if mood == "despair" else 1)
            pygame.draw.circle(surf, (74, 60, 42), (ix, iy), 5)
            pygame.draw.circle(surf, (22, 18, 14), (ix, iy), 2)
            pygame.draw.circle(surf, (222, 218, 202), (ix - 2, iy - 2), 1)
            pygame.draw.line(surf, sk_sh, (ex - 13, ey - 6), (ex + 12, ey - 7), 3)  # heavy lid
        pygame.draw.arc(surf, sk_lo, (ex - 12, ey + 4, 24, 12), 3.5, 5.9, 2)  # the bags
        pygame.draw.arc(surf, sk_lo, (ex - 9, ey + 8, 18, 9), 3.5, 5.9, 1)
    # nose: blunt, sun-worn
    pygame.draw.line(surf, sk_lo, (hx + 2, cy - 10), (hx - 2, cy + 16), 3)
    pygame.draw.line(surf, sk_hi, (hx - 5, cy - 10), (hx - 7, cy + 12), 1)
    pygame.draw.ellipse(surf, sk_lo, (hx - 7, cy + 12, 14, 9))
    # drawn cheek lines
    pygame.draw.arc(surf, sk_lo, (hx - 38, cy + 4, 22, 30), 0.6, 2.0, 2)
    pygame.draw.arc(surf, sk_lo, (hx + 16, cy + 4, 22, 30), 1.1, 2.5, 2)
    # the set mouth: flat, a hair down at the corners; no host smile in here
    my = cy + 31
    pygame.draw.lines(surf, (92, 68, 60), False,
                      [(hx - 20, my + 3), (hx - 9, my), (hx + 9, my), (hx + 20, my + 3)], 4)
    pygame.draw.line(surf, sk_lo, (hx, my + 12), (hx, my + 19), 2)       # cleft chin
    rnd = random.Random(11)                                              # stubble
    for _ in range(64):
        sx2 = hx + rnd.randint(-32, 32)
        sy2 = my + rnd.randint(4, 24) + abs(sx2 - hx) // 4
        surf.set_at((sx2, sy2), stub)
        surf.set_at((sx2 + 1, sy2), stub) if rnd.random() < 0.3 else None

    # (the hope forearm lands on the desk TOP and is drawn by the tableau fn
    # after the desk slab, or the slab would swallow it)


def draw_vane_tableau(surf, t, state):
    """The sheriff's office close-up, across Vane's desk. Cold window daylight
    (his office; Sable's lodge is the warm one). `state`: the ledger MOOD as
    his pose, the given newspaper flat on the desk, the opened gun cabinet."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    mood = state.get("mood", "neutral")
    paper = state.get("paper_present", False)
    cache = state.get("cache_open", False)

    # -- plaster wall, cold and institutional; dark wainscot below --
    top = (76, 76, 63); bot = (40, 40, 33)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    wains = int(H * 0.58)
    pygame.draw.rect(surf, (44, 37, 27), (0, wains, W, H - wains))
    pygame.draw.rect(surf, (28, 23, 17), (0, wains, W, 6))
    for sx in range(0, W, 52):
        pygame.draw.line(surf, (36, 30, 22), (sx, wains + 6), (sx, H), 1)
    pygame.draw.lines(surf, (58, 58, 48), False,                          # plaster crack
                      [(int(W * 0.50), 0), (int(W * 0.52), int(H * 0.09)),
                       (int(W * 0.505), int(H * 0.17))], 1)

    # -- the cell, a sliver at the left edge: bars over dark, door ajar --
    pygame.draw.rect(surf, (18, 16, 12), (0, 0, int(W * 0.07), wains))
    for bx in range(8, int(W * 0.07), 12):
        pygame.draw.line(surf, (64, 61, 55), (bx, 0), (bx, wains), 3)
    pygame.draw.line(surf, (74, 70, 62), (int(W * 0.07), 0), (int(W * 0.07), wains), 4)

    # -- the JAN 15 calendar (every calendar in town stops there) --
    cx_, cy_ = int(W * 0.145), int(H * 0.12)
    cw, ch = 88, 104
    pygame.draw.rect(surf, (24, 21, 16), (cx_ + 4, cy_ + 5, cw, ch))      # drop shadow
    pygame.draw.rect(surf, (202, 194, 174), (cx_, cy_, cw, ch))
    pygame.draw.rect(surf, (126, 42, 36), (cx_, cy_, cw, 24))             # month band
    pygame.draw.circle(surf, (74, 66, 50), (cx_ + cw // 2, cy_ + 6), 3)   # the pin
    ink = (222, 212, 192)                                                 # J A N
    jx, jy = cx_ + 26, cy_ + 7
    pygame.draw.line(surf, ink, (jx - 4, jy), (jx + 4, jy), 2)
    pygame.draw.line(surf, ink, (jx + 2, jy), (jx + 2, jy + 9), 2)
    pygame.draw.line(surf, ink, (jx + 2, jy + 9), (jx - 3, jy + 9), 2)
    ax = cx_ + 42
    pygame.draw.line(surf, ink, (ax - 4, jy + 10), (ax, jy), 2)
    pygame.draw.line(surf, ink, (ax, jy), (ax + 4, jy + 10), 2)
    pygame.draw.line(surf, ink, (ax - 2, jy + 6), (ax + 2, jy + 6), 1)
    nx_ = cx_ + 58
    pygame.draw.line(surf, ink, (nx_ - 3, jy + 10), (nx_ - 3, jy), 2)
    pygame.draw.line(surf, ink, (nx_ - 3, jy), (nx_ + 3, jy + 10), 2)
    pygame.draw.line(surf, ink, (nx_ + 3, jy + 10), (nx_ + 3, jy), 2)
    seg = (56, 50, 42)                                                    # big 15
    ox, oy = cx_ + 20, cy_ + 38
    pygame.draw.line(surf, seg, (ox + 8, oy), (ox + 8, oy + 46), 8)
    pygame.draw.line(surf, seg, (ox, oy + 9), (ox + 8, oy), 6)
    ox = cx_ + 42
    pygame.draw.line(surf, seg, (ox, oy), (ox + 26, oy), 7)
    pygame.draw.line(surf, seg, (ox + 3, oy), (ox + 3, oy + 20), 7)
    pygame.draw.line(surf, seg, (ox, oy + 20), (ox + 22, oy + 20), 7)
    pygame.draw.line(surf, seg, (ox + 22, oy + 20), (ox + 22, oy + 46), 7)
    pygame.draw.line(surf, seg, (ox, oy + 46), (ox + 24, oy + 46), 7)
    pygame.draw.polygon(surf, (176, 168, 148),                            # curled corner
                        [(cx_ + cw - 16, cy_ + ch), (cx_ + cw, cy_ + ch), (cx_ + cw, cy_ + ch - 16)])

    # -- a pinned list beside the calendar: names, some struck through --
    lx_, ly_ = int(W * 0.265), int(H * 0.15)
    pygame.draw.rect(surf, (24, 21, 16), (lx_ + 3, ly_ + 4, 54, 86))
    pygame.draw.rect(surf, (188, 180, 160), (lx_, ly_, 54, 86))
    pygame.draw.circle(surf, (74, 66, 50), (lx_ + 27, ly_ + 4), 2)
    for i in range(7):
        yy = ly_ + 15 + i * 10
        pygame.draw.line(surf, (98, 92, 77), (lx_ + 7, yy), (lx_ + 46, yy), 2)
        if i in (1, 3, 4):
            pygame.draw.line(surf, (74, 55, 46), (lx_ + 5, yy), (lx_ + 48, yy - 2), 1)

    # -- the window: sallow overcast daylight, the light of the whole room --
    wx, wy = int(W * 0.60), int(H * 0.05)
    ww, wh = int(W * 0.235), int(H * 0.46)
    pygame.draw.rect(surf, (30, 25, 19), (wx - 10, wy - 10, ww + 20, wh + 20))
    glass_t = (222, 214, 180); glass_b = (184, 174, 138)
    for gy in range(wh):
        surf.fill(_lerp(glass_t, glass_b, gy / wh), (wx, wy + gy, ww, 1))
    pygame.draw.rect(surf, (146, 138, 108), (wx, wy + int(wh * 0.62), ww, int(wh * 0.12)))  # treeline
    pygame.draw.rect(surf, (166, 156, 122), (wx, wy + int(wh * 0.74), ww, int(wh * 0.26)))  # dead corn
    for cxx in range(wx + 4, wx + ww, 9):
        pygame.draw.line(surf, (142, 132, 100), (cxx, wy + int(wh * 0.76)), (cxx, wy + wh), 1)
    pygame.draw.line(surf, (30, 25, 19), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 6)  # muntins
    pygame.draw.line(surf, (30, 25, 19), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 6)
    pygame.draw.rect(surf, (54, 45, 33), (wx - 10, wy - 10, ww + 20, wh + 20), 4)
    pygame.draw.rect(surf, (54, 45, 33), (wx - 16, wy + wh + 10, ww + 32, 10))            # sill

    # the light shaft, angling down-left onto the desk; dust hanging in it
    shaft = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(shaft, (230, 218, 176, 34),
                        [(wx, wy + 8), (wx + ww, wy), (int(W * 0.48), int(H * 0.88)),
                         (int(W * 0.20), int(H * 0.88))])
    surf.blit(shaft, (0, 0))
    rnd = random.Random(9)
    for _ in range(52):
        base = rnd.randint(0, 1000)
        fr = ((t * 7 + base) % 460) / 460.0
        mx = int(wx + ww * 0.5 + (int(W * 0.33) - wx - ww * 0.5) * fr + 14 * math.sin(t * 0.7 + base))
        my_ = int(wy + 30 + (int(H * 0.80) - wy - 30) * fr)
        pygame.draw.circle(surf, (238, 228, 192), (mx, my_), 1)

    # -- the gun cabinet at the right edge (the back of the office) --
    gx_, gy_ = int(W * 0.875), int(H * 0.09)
    gw, gh = int(W * 0.115), int(H * 0.62)
    pygame.draw.rect(surf, (40, 32, 22), (gx_, gy_, gw, gh))
    pygame.draw.rect(surf, (62, 49, 34), (gx_, gy_, gw, gh), 4)
    if cache:
        pygame.draw.rect(surf, (14, 12, 9), (gx_ + 6, gy_ + 8, gw - 12, gh - 16))
        for py_ in range(gy_ + 30, gy_ + gh - 40, 36):                   # empty shelves
            pygame.draw.line(surf, (52, 46, 38), (gx_ + 10, py_), (gx_ + gw - 10, py_), 3)
        pygame.draw.rect(surf, (156, 138, 96), (gx_ + 14, gy_ + gh - 60, 32, 17))  # one carton left
        pygame.draw.line(surf, (110, 96, 64), (gx_ + 14, gy_ + gh - 52, ), (gx_ + 46, gy_ + gh - 52), 1)
        pygame.draw.polygon(surf, (68, 55, 38),                          # the swung door
                            [(gx_ + 2, gy_ + 4), (gx_ - 30, gy_ + 18), (gx_ - 30, gy_ + gh + 8),
                             (gx_ + 2, gy_ + gh - 4)])
        pygame.draw.polygon(surf, (38, 30, 20),
                            [(gx_ + 2, gy_ + 4), (gx_ - 30, gy_ + 18), (gx_ - 30, gy_ + gh + 8),
                             (gx_ + 2, gy_ + gh - 4)], 2)
        pygame.draw.circle(surf, (94, 88, 72), (gx_ - 22, gy_ + gh // 2), 4)      # its handle
    else:
        pygame.draw.line(surf, (62, 49, 34), (gx_ + gw // 2, gy_), (gx_ + gw // 2, gy_ + gh), 3)
        for py_ in (gy_ + int(gh * 0.3), gy_ + int(gh * 0.7)):           # door panels
            pygame.draw.rect(surf, (52, 42, 28), (gx_ + 8, py_ - 22, gw // 2 - 14, 44), 2)
            pygame.draw.rect(surf, (52, 42, 28), (gx_ + gw // 2 + 6, py_ - 22, gw // 2 - 14, 44), 2)
        # the hasp strap across both doors + the padlock hung from it
        pygame.draw.rect(surf, (78, 72, 58), (gx_ + gw // 2 - 22, gy_ + int(gh * 0.46), 44, 9))
        pygame.draw.rect(surf, (58, 54, 44), (gx_ + gw // 2 - 22, gy_ + int(gh * 0.46), 44, 9), 1)
        pygame.draw.arc(surf, (72, 68, 56), (gx_ + gw // 2 - 7, gy_ + int(gh * 0.46) + 8, 14, 12), 0.0, 3.4, 3)
        pygame.draw.rect(surf, (84, 78, 62), (gx_ + gw // 2 - 9, gy_ + int(gh * 0.46) + 16, 18, 16))
    # cornice + plinth feet so it reads FURNITURE, never a door
    pygame.draw.rect(surf, (74, 59, 41), (gx_ - 8, gy_ - 10, gw + 16, 12))
    pygame.draw.rect(surf, (52, 41, 28), (gx_ - 4, gy_ + gh, 12, 14))
    pygame.draw.rect(surf, (52, 41, 28), (gx_ + gw - 8, gy_ + gh, 12, 14))

    # -- Vane, behind his desk: breath bob, tired blink, the ledger pose --
    bob = int(2 * math.sin(t * 1.1))
    _draw_vane(surf, int(W * 0.385), int(H * 0.30) + bob, (t % 3.7) < 0.18, mood)

    # -- the desk slab --
    dtop = int(H * 0.655)
    pygame.draw.polygon(surf, (36, 27, 17), [(0, dtop), (W, dtop), (W, H), (0, H)])
    pygame.draw.polygon(surf, (60, 47, 31),
                        [(int(W * 0.03), dtop - 26), (int(W * 0.97), dtop - 26), (W, dtop), (0, dtop)])
    pygame.draw.line(surf, (84, 66, 44), (0, dtop), (W, dtop), 2)
    for gxx in range(0, W, 130):
        pygame.draw.line(surf, (26, 20, 13), (gxx, dtop + 8), (gxx - 12, H), 1)

    # -- hope: his forearm comes over the desk edge, hand flat on the top --
    if mood == "hope":
        vcx_ = int(W * 0.385)
        pygame.draw.polygon(surf, (110, 97, 67),
                            [(vcx_ + 76, dtop - 76), (vcx_ + 138, dtop - 60),
                             (vcx_ + 132, dtop + 20), (vcx_ + 64, dtop + 10)])
        pygame.draw.polygon(surf, (70, 61, 43),
                            [(vcx_ + 76, dtop - 76), (vcx_ + 92, dtop - 72),
                             (vcx_ + 78, dtop + 12), (vcx_ + 64, dtop + 10)])
        pygame.draw.line(surf, (70, 61, 43), (vcx_ + 70, dtop - 6),      # cuff seam
                         (vcx_ + 132, dtop + 4), 4)
        pygame.draw.ellipse(surf, (170, 160, 132), (vcx_ + 92, dtop - 2, 62, 32))  # the hand
        pygame.draw.ellipse(surf, (118, 111, 89), (vcx_ + 92, dtop - 2, 62, 32), 1)
        for fk in range(4):                                              # fingers
            pygame.draw.line(surf, (118, 111, 89), (vcx_ + 116 + fk * 10, dtop + 4),
                             (vcx_ + 126 + fk * 10, dtop + 26), 3)

    # -- the desk phone (1994, corded, black; it does not ring) --
    phx, phy = int(W * 0.105), dtop - 10
    pygame.draw.polygon(surf, (44, 44, 50), [(phx, phy), (phx + 100, phy - 8), (phx + 108, phy + 24),
                                             (phx + 10, phy + 32)])
    pygame.draw.polygon(surf, (62, 62, 70), [(phx + 4, phy - 2), (phx + 96, phy - 9), (phx + 100, phy + 3),
                                             (phx + 8, phy + 10)])
    pygame.draw.rect(surf, (54, 54, 62), (phx + 18, phy - 28, 66, 17), border_radius=8)  # handset
    pygame.draw.rect(surf, (72, 72, 82), (phx + 24, phy - 26, 54, 5), border_radius=3)
    pygame.draw.circle(surf, (54, 54, 62), (phx + 23, phy - 19), 11)
    pygame.draw.circle(surf, (54, 54, 62), (phx + 79, phy - 19), 11)
    for k in range(4):                                                    # the cord, hanging dead
        pygame.draw.circle(surf, (46, 46, 53), (phx + 104 + (k % 2) * 5, phy + 28 + k * 7), 4, 2)

    # -- the files + booking box --
    fx_, fy_ = int(W * 0.225), dtop - 6
    pygame.draw.polygon(surf, (82, 71, 50), [(fx_, fy_), (fx_ + 124, fy_ - 12), (fx_ + 136, fy_ + 10),
                                             (fx_ + 14, fy_ + 22)])
    pygame.draw.polygon(surf, (108, 97, 70), [(fx_ + 4, fy_ - 5), (fx_ + 120, fy_ - 16), (fx_ + 126, fy_ - 7),
                                              (fx_ + 10, fy_ + 4)])
    pygame.draw.line(surf, (60, 52, 36), (fx_ + 8, fy_ + 3), (fx_ + 122, fy_ - 9), 1)

    # -- the coffee, going cold slower than the town --
    cux, cuy = int(W * 0.585), dtop - 8
    pygame.draw.ellipse(surf, (22, 17, 11), (cux - 6, cuy + 16, 54, 10))
    pygame.draw.rect(surf, (158, 154, 144), (cux, cuy - 16, 40, 34), border_radius=4)
    pygame.draw.ellipse(surf, (118, 114, 106), (cux, cuy - 23, 40, 13))
    pygame.draw.ellipse(surf, (48, 33, 22), (cux + 5, cuy - 20, 30, 8))
    pygame.draw.arc(surf, (158, 154, 144), (cux + 34, cuy - 12, 18, 22), 4.6, 1.6, 3)
    for w_ in range(2):                                                   # steam, barely
        sxx = cux + 13 + w_ * 13
        pts = [(sxx + int(5 * math.sin(t * 1.9 + w_ * 2.1 + k * 0.9)), cuy - 28 - k * 9)
               for k in range(4)]
        pygame.draw.lines(surf, (132, 128, 118), False, pts, 1)

    # -- the newspaper, spread flat where he left it (once given) --
    if paper:
        nx, ny = int(W * 0.40), dtop - 2
        quad = [(nx, ny), (nx + 176, ny - 14), (nx + 192, ny + 28), (nx + 16, ny + 42)]
        pygame.draw.polygon(surf, (16, 13, 10), [(x + 4, y + 5) for x, y in quad])
        pygame.draw.polygon(surf, (196, 190, 172), quad)
        pygame.draw.polygon(surf, (152, 146, 128), quad, 2)
        pygame.draw.line(surf, (152, 146, 128), (nx + 88, ny - 7), (nx + 104, ny + 35), 1)  # fold
        pygame.draw.line(surf, (62, 58, 50), (nx + 12, ny), (nx + 78, ny - 7), 6)           # masthead
        for i in range(3):                                                                  # columns
            yy = ny + 8 + i * 8
            pygame.draw.line(surf, (116, 110, 95), (nx + 16, yy + 2), (nx + 80, yy - 4), 2)
        pygame.draw.rect(surf, (98, 94, 83), (nx + 106, ny - 6, 44, 28))                    # front-page photo
        pygame.draw.ellipse(surf, (74, 70, 61), (nx + 117, ny - 1, 20, 17))

    # -- cold key light from the window; eased vignette --
    key = pygame.Surface((W, H), pygame.SRCALPHA)
    kx, ky = int(W * 0.60), int(H * 0.30)
    for r in range(int(H * 0.95), 0, -12):
        a = int(80 * (1 - r / (H * 0.95)))
        pygame.draw.circle(key, (226, 216, 180, a), (kx, ky), r)
    surf.blit(key, (0, 0))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = int(W * 0.44), int(H * 0.42)
    maxr = int(math.hypot(W, H) * 0.66); inner = int(maxr * 0.58)
    for r in range(maxr, inner, -10):
        a = max(0, int(140 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- Hettie: her shop sprite as a close-up counter-keeper -----------------
# The human+grit register with HER tell kept intact: you never find her eyes.
# Small wire spectacles, lenses filled black, a glint sitting on the SAME
# side of both (impossible under one light). `glance` turns her head toward
# the shop door (viewer-left); `dark` kills the glints for a beat (her blink:
# the light going out of the lenses, nothing else moving).
def _draw_hettie(surf, cx, cy, glance, dark):
    import pygame
    skin = (158, 152, 128); sk_hi = (186, 178, 150); sk_lo = (112, 107, 87)
    sk_sh = (78, 74, 60)
    dress = (92, 55, 70); dress_dk = (60, 36, 46); dress_lt = (114, 70, 87)
    apron = (136, 131, 118); apron_dk = (100, 96, 86); apron_hem = (92, 82, 74)
    hair = (128, 126, 130); hair_dk = (94, 92, 98); kerch = (104, 60, 76)
    turn = -int(16 * glance)                       # toward the door, left
    HW, HH = 46, 58                                # a small, spare frame
    tt = cy + HH - 4

    # -- torso: the housedress, the apron bib over it --
    pygame.draw.polygon(surf, dress, [(cx - 88, tt + 14), (cx + 88, tt + 14),
                                      (cx + 74, tt + 300), (cx - 74, tt + 300)])
    pygame.draw.ellipse(surf, dress, (cx - 94, tt - 6, 70, 48))     # slight shoulders
    pygame.draw.ellipse(surf, dress, (cx + 24, tt - 6, 70, 48))
    pygame.draw.polygon(surf, dress_dk, [(cx + 30, tt + 14), (cx + 88, tt + 14),
                                         (cx + 74, tt + 300), (cx + 28, tt + 300)])
    pygame.draw.polygon(surf, dress_lt, [(cx - 88, tt + 14), (cx - 78, tt + 14),
                                         (cx - 70, tt + 300), (cx - 88, tt + 300)])
    # the apron bib, straps over the shoulders, a mended patch
    pygame.draw.polygon(surf, apron, [(cx - 40, tt + 34), (cx + 40, tt + 34),
                                      (cx + 46, tt + 300), (cx - 46, tt + 300)])
    pygame.draw.polygon(surf, apron_dk, [(cx + 16, tt + 34), (cx + 40, tt + 34),
                                         (cx + 46, tt + 300), (cx + 18, tt + 300)])
    pygame.draw.line(surf, apron_dk, (cx - 38, tt + 36), (cx - 26, tt + 8), 5)   # straps
    pygame.draw.line(surf, apron_dk, (cx + 38, tt + 36), (cx + 26, tt + 8), 5)
    pygame.draw.rect(surf, apron_hem, (cx - 18, tt + 96, 26, 20), 1)             # the patch
    pygame.draw.line(surf, apron_hem, (cx - 18, tt + 100), (cx + 8, tt + 100), 1)
    # a high dress collar closed at the throat, a bone button
    pygame.draw.polygon(surf, dress_lt, [(cx - 22, tt + 12), (cx, tt + 26),
                                         (cx + 22, tt + 12), (cx + 16, tt + 2),
                                         (cx - 16, tt + 2)])
    pygame.draw.circle(surf, (188, 182, 164), (cx, tt + 16), 4)
    pygame.draw.circle(surf, (128, 122, 106), (cx, tt + 16), 4, 1)

    # -- neck + head (narrow, drawn) --
    pygame.draw.rect(surf, sk_lo, (cx - 12 + turn // 2, cy + HH - 20, 24, 34))
    hx = cx + turn                                  # feature centre (the glance)
    pygame.draw.ellipse(surf, skin, (cx - HW, cy - HH, HW * 2, HH * 2))
    # age: hollow the cheeks, no heavy jaw here -- a pointed, spare face
    pygame.draw.polygon(surf, skin, [(cx - HW + 12, cy + 16), (cx + HW - 12 + turn // 2, cy + 16),
                                     (hx + 12, cy + HH + 6), (hx - 12, cy + HH + 6)])
    dim = pygame.Surface((HW * 2 + 20, HH * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(dim, (*sk_sh, 90), (0, 12, HW - 2 - turn, HH * 2 - 18))
    surf.blit(dim, (cx - HW, cy - HH))              # shadowed side away from the bulb
    lit = pygame.Surface((HW * 2 + 20, HH * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(lit, (*sk_hi, 110), (HW + 8, HH - 38, HW - 8, 66))
    surf.blit(lit, (cx - HW, cy - HH))
    pygame.draw.circle(surf, sk_lo, (cx - HW + 2, cy + 2), 7)        # ears
    pygame.draw.circle(surf, sk_lo, (cx + HW - 2, cy + 2), 7)

    # -- grey hair pinned back under the kerchief band, the bun behind --
    pygame.draw.circle(surf, hair_dk, (cx - 8, cy - HH + 2, ), 14)   # the bun, high behind
    pygame.draw.circle(surf, hair_dk, (cx - 8, cy - HH + 2), 14)
    pygame.draw.ellipse(surf, hair, (cx - HW - 2, cy - HH - 8, HW * 2 + 4, 58))
    pygame.draw.ellipse(surf, skin, (cx - 34, cy - 30, 68 + turn // 3, 34))      # forehead reveal
    for k in range(5):                                               # combed-back strands
        pygame.draw.arc(surf, hair_dk, (cx - HW + 6 + k * 16, cy - HH - 4, 30, 40),
                        1.2, 2.6, 1)
    pygame.draw.rect(surf, kerch, (cx - HW - 2, cy - HH - 12, HW * 2 + 4, 14))   # kerchief band
    pygame.draw.line(surf, (70, 40, 52), (cx - HW - 2, cy - HH + 1), (cx + HW + 2, cy - HH + 1), 2)

    # -- the spectacles: black lenses, glints on the SAME side of both --
    pygame.draw.line(surf, (168, 160, 140), (hx - 7, cy - 5), (hx + 7, cy - 5), 2)  # bridge
    for sgn in (-1, 1):
        ex = hx + sgn * 17
        ey = cy - 3
        pygame.draw.ellipse(surf, (8, 7, 10), (ex - 9, ey - 7, 18, 14))          # filled lens
        pygame.draw.ellipse(surf, (198, 190, 164), (ex - 10, ey - 8, 20, 16), 2)  # bright wire rim
        if not dark:
            # both glints upper-LEFT: the same side, the wrong side
            pygame.draw.circle(surf, (244, 238, 220), (ex - 4, ey - 3), 2)
            pygame.draw.circle(surf, (190, 184, 168), (ex - 2, ey - 1), 1)
        pygame.draw.line(surf, (198, 190, 164),                                   # temple arm
                         (ex + sgn * 10, ey - 2), (cx + sgn * (HW - 2), cy), 1)
    # thin brows above the rims
    pygame.draw.line(surf, (104, 100, 96), (hx - 26, cy - 16), (hx - 8, cy - 18), 2)
    pygame.draw.line(surf, (104, 100, 96), (hx + 8, cy - 18), (hx + 26, cy - 16), 2)

    # -- nose, the drawn cheeks, the careful mouth --
    pygame.draw.line(surf, sk_lo, (hx + 1, cy - 4), (hx - 1, cy + 14), 2)
    pygame.draw.ellipse(surf, sk_lo, (hx - 5, cy + 11, 10, 6))
    pygame.draw.arc(surf, sk_lo, (hx - 32, cy + 4, 18, 24), 0.7, 2.1, 2)         # hollows
    pygame.draw.arc(surf, sk_lo, (hx + 14, cy + 4, 18, 24), 1.0, 2.4, 2)
    my = cy + 26
    pygame.draw.line(surf, (118, 84, 80), (hx - 12, my), (hx + 12, my), 2)       # pressed thin
    pygame.draw.line(surf, sk_lo, (hx - 14, my + 1), (hx - 11, my), 1)
    pygame.draw.line(surf, sk_lo, (hx + 11, my), (hx + 14, my + 1), 1)
    for sgn in (-1, 1):                                                          # age lines
        pygame.draw.arc(surf, sk_lo, (hx + sgn * 12 - 6, my - 10, 12, 16),
                        (1.1 if sgn > 0 else 0.5), (2.6 if sgn > 0 else 2.0), 1)


def draw_hettie_tableau(surf, t, state):
    """The gutted shop, across Hettie's counter. Her ONE kept bulb burns over
    it (the shelves behind her are bare, dust-ghosts where the stock stood,
    one tin left); the shop door stands at her left and she keeps glancing at
    it. `state`: the glance (idle-driven), Mara's tab on the spike until it
    is lifted, the traded newspaper open on the counter after."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    glance = state.get("glance", 0.0)
    tab = state.get("tab_present", True)
    paper = state.get("paper_present", False)

    # -- dim shop wall; the gloom the bulb holds back --
    top = (72, 64, 53); bot = (34, 30, 25)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))

    # -- the shop door + front-window strip, viewer-left: weak daylight --
    dx_, dy_ = int(W * 0.035), int(H * 0.06)
    dw, dh = int(W * 0.155), int(H * 0.55)
    pygame.draw.rect(surf, (44, 34, 25), (dx_ - 8, dy_ - 8, dw + 16, dh + 16))
    pygame.draw.rect(surf, (58, 45, 32), (dx_ - 8, dy_ - 8, dw + 16, dh + 16), 4)
    glass_t = (158, 152, 132); glass_b = (122, 116, 97)
    gh2 = int(dh * 0.52)
    for gy in range(gh2):                                            # glass upper panel
        surf.fill(_lerp(glass_t, glass_b, gy / gh2), (dx_, dy_ + gy, dw, 1))
    pygame.draw.rect(surf, (40, 31, 23), (dx_, dy_ + gh2, dw, dh - gh2))  # wood lower
    pygame.draw.rect(surf, (52, 40, 29), (dx_ + 10, dy_ + gh2 + 14, dw - 20, dh - gh2 - 28), 2)
    pygame.draw.line(surf, (44, 34, 25), (dx_ + dw // 2, dy_), (dx_ + dw // 2, dy_ + gh2), 4)
    # the faded sign card hanging inside the glass, string and all
    sx_, sy_ = dx_ + dw // 2 + 8, dy_ + 22
    pygame.draw.line(surf, (120, 112, 96), (sx_ + 14, dy_ + 2), (sx_ + 14, sy_), 1)
    pygame.draw.rect(surf, (150, 140, 118), (sx_, sy_, 30, 20))
    pygame.draw.rect(surf, (108, 100, 84), (sx_, sy_, 30, 20), 1)
    for i in range(3):                                               # faded letters, unreadable
        pygame.draw.line(surf, (110, 102, 86), (sx_ + 5 + i * 8, sy_ + 6),
                         (sx_ + 5 + i * 8, sy_ + 14), 2)
    pygame.draw.circle(surf, (96, 90, 76), (dx_ + dw - 12, dy_ + gh2 + int(dh * 0.16)), 4)  # knob

    # -- the bare shelves behind her: dust-ghosts and the one tin --
    shx, shy = int(W * 0.29), int(H * 0.055)
    shw, shh = int(W * 0.585), int(H * 0.50)
    pygame.draw.rect(surf, (48, 39, 28), (shx, shy, shw, shh))
    pygame.draw.rect(surf, (58, 46, 32), (shx, shy, shw, shh), 4)
    for r in range(3):                                               # three shelf boards
        by = shy + int(shh * (0.30 + r * 0.30))
        pygame.draw.rect(surf, (66, 53, 37), (shx + 4, by - 6, shw - 8, 8))
        pygame.draw.line(surf, (30, 24, 17), (shx + 4, by + 2), (shx + shw - 4, by + 2), 2)
        # dust-ghost rectangles where the stock stood
        rnd = random.Random(31 + r)
        gx0 = shx + 16
        while gx0 < shx + shw - 40:
            gw2 = rnd.randint(22, 46)
            if rnd.random() < 0.72:
                ghost = pygame.Surface((gw2, 26), pygame.SRCALPHA)
                ghost.fill((178, 170, 150, 26))
                pygame.draw.rect(ghost, (178, 170, 150, 44), (0, 0, gw2, 26), 1)
                surf.blit(ghost, (gx0, by - 34))
            gx0 += gw2 + rnd.randint(8, 22)
    tinx, tiny = shx + int(shw * 0.68), shy + int(shh * 0.60) - 34   # the one tin left
    pygame.draw.rect(surf, (120, 112, 92), (tinx, tiny + 4, 22, 26))
    pygame.draw.ellipse(surf, (146, 138, 114), (tinx, tiny, 22, 10))
    pygame.draw.rect(surf, (86, 66, 50), (tinx, tiny + 12, 22, 8))   # its label band

    # -- HER KEPT LIGHT: the one burning bulb over the counter, swaying --
    sway = 0.05 * math.sin(t * 0.85)
    bx0, by0 = int(W * 0.54), -6
    blen = int(H * 0.15)
    bx1 = bx0 + int(math.sin(sway) * blen)
    by1 = by0 + int(math.cos(sway) * blen)
    pygame.draw.line(surf, (30, 27, 22), (bx0, by0), (bx1, by1), 2)  # the cord
    pygame.draw.rect(surf, (52, 48, 40), (bx1 - 5, by1 - 4, 10, 8))  # the socket
    pygame.draw.circle(surf, (255, 232, 168), (bx1, by1 + 12), 11)   # the bulb
    pygame.draw.circle(surf, (255, 246, 210), (bx1, by1 + 12), 6)
    halo = pygame.Surface((W, H), pygame.SRCALPHA)                   # its held-back gloom
    for r in range(int(H * 0.74), 0, -10):
        a = int(94 * (1 - r / (H * 0.74)))
        pygame.draw.circle(halo, (255, 218, 150, a), (bx1, by1 + 14), r)
    surf.blit(halo, (0, 0))
    rnd2 = random.Random(17)                                         # dust round the bulb
    for _ in range(30):
        base = rnd2.randint(0, 600)
        yy = int(H * 0.06 + (t * 6 + base) % (H * 0.52))
        mx = bx1 + int(44 * math.sin(t * 0.5 + base)) + rnd2.randint(-30, 30)
        pygame.draw.circle(surf, (232, 218, 184), (mx, yy), 1)

    # -- Hettie behind the counter: breath, the glance, the lens-dark blink --
    bob = int(2 * math.sin(t * 1.35))
    dark = (t % 5.1) < 0.22                                          # the glints go out
    _draw_hettie(surf, int(W * 0.415), int(H * 0.30) + bob, glance, dark)

    # -- the counter --
    ctop = int(H * 0.655)
    pygame.draw.polygon(surf, (34, 26, 17), [(0, ctop), (W, ctop), (W, H), (0, H)])
    pygame.draw.polygon(surf, (56, 44, 29),
                        [(int(W * 0.04), ctop - 26), (int(W * 0.96), ctop - 26), (W, ctop), (0, ctop)])
    pygame.draw.line(surf, (80, 63, 42), (0, ctop), (W, ctop), 2)
    for gxx in range(0, W, 120):
        pygame.draw.line(surf, (24, 18, 12), (gxx, ctop + 8), (gxx - 10, H), 1)

    # -- the till, empty since the new year: an old register, keys and all --
    tx_, ty_ = int(W * 0.60), ctop - 12
    pygame.draw.polygon(surf, (66, 60, 53), [(tx_, ty_), (tx_ + 110, ty_ - 8), (tx_ + 118, ty_ + 24),
                                             (tx_ + 10, ty_ + 32)])
    pygame.draw.polygon(surf, (74, 66, 58), [(tx_ + 4, ty_ - 26), (tx_ + 104, ty_ - 33),
                                             (tx_ + 108, ty_ - 6), (tx_ + 6, ty_ + 1)])
    pygame.draw.rect(surf, (44, 40, 36), (tx_ + 14, ty_ - 58, 84, 30))           # the amount window
    pygame.draw.rect(surf, (150, 144, 124), (tx_ + 20, ty_ - 52, 72, 18))
    pygame.draw.rect(surf, (44, 40, 36), (tx_ + 20, ty_ - 52, 72, 18), 2)
    rnd3 = random.Random(5)                                                      # the key rows
    for rr in range(3):
        for cc in range(7):
            pygame.draw.circle(surf, (108, 100, 88),
                               (tx_ + 22 + cc * 12 + rr * 3, ty_ - 20 + rr * 8), 3)
    pygame.draw.line(surf, (36, 32, 28), (tx_ + 4, ty_ + 8), (tx_ + 108, ty_ + 1), 2)  # the shut drawer

    # -- the spike by the till: Mara's tab curled on it, or bare --
    px_, py_ = int(W * 0.755), ctop - 4
    pygame.draw.ellipse(surf, (20, 15, 10), (px_ - 16, py_ + 8, 40, 9))
    pygame.draw.ellipse(surf, (96, 88, 74), (px_ - 14, py_ + 4, 36, 10))         # the base
    pygame.draw.line(surf, (140, 134, 118), (px_ + 4, py_ + 8), (px_ + 4, py_ - 34), 2)  # the spike
    if tab:
        pygame.draw.polygon(surf, (196, 188, 166),                    # the curled slip
                            [(px_ - 12, py_ - 20), (px_ + 22, py_ - 26), (px_ + 18, py_ - 6),
                             (px_ - 8, py_ - 2)])
        pygame.draw.polygon(surf, (156, 148, 126),
                            [(px_ - 12, py_ - 20), (px_ - 4, py_ - 22), (px_ - 2, py_ - 4),
                             (px_ - 8, py_ - 2)])
        for i in range(3):                                            # her hand, faint lines
            pygame.draw.line(surf, (128, 120, 102), (px_ - 4, py_ - 16 + i * 5),
                             (px_ + 14, py_ - 19 + i * 5), 1)
        pygame.draw.line(surf, (140, 134, 118), (px_ + 4, py_ - 12), (px_ + 4, py_ - 34), 2)

    # -- the traded newspaper, open on the counter (she reads it after) --
    if paper:
        nx, ny = int(W * 0.415), ctop - 4
        quad = [(nx, ny), (nx + 150, ny - 12), (nx + 164, ny + 24), (nx + 14, ny + 36)]
        pygame.draw.polygon(surf, (14, 12, 9), [(x + 3, y + 4) for x, y in quad])
        pygame.draw.polygon(surf, (192, 186, 168), quad)
        pygame.draw.polygon(surf, (148, 142, 124), quad, 2)
        pygame.draw.line(surf, (148, 142, 124), (nx + 75, ny - 6), (nx + 89, ny + 30), 1)
        pygame.draw.line(surf, (60, 56, 48), (nx + 10, ny), (nx + 66, ny - 6), 5)  # masthead
        for i in range(3):
            yy = ny + 7 + i * 7
            pygame.draw.line(surf, (112, 106, 92), (nx + 13, yy + 2), (nx + 68, yy - 3), 2)
        pygame.draw.rect(surf, (96, 92, 81), (nx + 92, ny - 5, 38, 24))
        pygame.draw.ellipse(surf, (72, 68, 59), (nx + 101, ny - 1, 17, 15))

    # -- the bulb's warm pool on the counter; vignette --
    key = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(int(H * 0.8), 0, -12):
        a = int(96 * (1 - r / (H * 0.8)))
        pygame.draw.circle(key, (255, 216, 148, a), (bx1, int(H * 0.42)), r)
    surf.blit(key, (0, 0))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = int(W * 0.45), int(H * 0.42)
    maxr = int(math.hypot(W, H) * 0.66); inner = int(maxr * 0.60)
    for r in range(maxr, inner, -10):
        a = max(0, int(132 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- Crane: his preacher sprite as a close-up at the lectern --------------
# Gaunt, grey, half a ghost: the high balding brow with thin grey hair at
# the sides, deep eye hollows, the black cassock swallowing everything below
# the white collar band. `doomed` hardens him: brows angle in, the head
# comes a notch forward, the mouth sets. (His hands live on the lectern and
# are drawn by the tableau fn, over its top.)
def _draw_crane(surf, cx, cy, blink, doomed):
    import pygame
    skin = (166, 166, 146); sk_hi = (190, 188, 166); sk_lo = (116, 116, 98)
    sk_sh = (80, 80, 66)
    cas = (32, 30, 36); cas_dk = (18, 17, 21); cas_lt = (48, 45, 53)
    hair = (128, 128, 134); collar = (214, 214, 218); cross = (158, 152, 128)
    fwd = 8 if doomed else 0                       # a notch forward
    cy = cy + fwd
    HW, HH = 48, 62                                # gaunt, tall-skulled
    tt = cy + HH - 4

    # -- the cassock: one black mass, a button line, the collar band --
    pygame.draw.polygon(surf, cas, [(cx - 96, tt + 12), (cx + 96, tt + 12),
                                    (cx + 84, tt + 300), (cx - 84, tt + 300)])
    pygame.draw.ellipse(surf, cas, (cx - 102, tt - 8, 76, 50))      # narrow shoulders
    pygame.draw.ellipse(surf, cas, (cx + 26, tt - 8, 76, 50))
    pygame.draw.polygon(surf, cas_dk, [(cx + 20, tt + 12), (cx + 96, tt + 12),
                                       (cx + 84, tt + 300), (cx + 22, tt + 300)])
    pygame.draw.polygon(surf, cas_lt, [(cx - 96, tt + 12), (cx - 86, tt + 12),
                                       (cx - 78, tt + 300), (cx - 96, tt + 300)])
    pygame.draw.line(surf, cas_dk, (cx, tt + 26), (cx, tt + 300), 2)    # button line
    for py_ in range(tt + 44, tt + 240, 34):
        pygame.draw.circle(surf, (52, 49, 58), (cx, py_), 2)
    # the white clerical collar, a clean band at the throat
    pygame.draw.rect(surf, collar, (cx - 22, tt + 4, 44, 12), border_radius=5)
    pygame.draw.rect(surf, (168, 168, 174), (cx - 22, tt + 12, 44, 4))
    pygame.draw.rect(surf, cas, (cx - 7, tt + 4, 14, 12))               # the notch
    # the small pale cross on its cord
    pygame.draw.line(surf, (96, 92, 78), (cx - 14, tt + 16), (cx - 2, tt + 52), 1)
    pygame.draw.line(surf, (96, 92, 78), (cx + 14, tt + 16), (cx + 2, tt + 52), 1)
    pygame.draw.line(surf, cross, (cx, tt + 48), (cx, tt + 72), 4)
    pygame.draw.line(surf, cross, (cx - 7, tt + 56), (cx + 7, tt + 56), 4)
    pygame.draw.line(surf, (110, 104, 86), (cx + 1, tt + 48), (cx + 1, tt + 72), 1)

    # -- neck + the gaunt head --
    pygame.draw.rect(surf, sk_lo, (cx - 12, cy + HH - 22, 24, 36))
    pygame.draw.ellipse(surf, skin, (cx - HW, cy - HH, HW * 2, HH * 2))
    # hollow it: shadowed sides, sunken cheeks (the dim pass carries age)
    dim = pygame.Surface((HW * 2 + 20, HH * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(dim, (*sk_sh, 96), (0, 12, HW - 4, HH * 2 - 16))
    surf.blit(dim, (cx - HW, cy - HH))
    lit = pygame.Surface((HW * 2 + 20, HH * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(lit, (*sk_hi, 112), (HW + 8, HH - 40, HW - 6, 74))
    surf.blit(lit, (cx - HW, cy - HH))
    pygame.draw.circle(surf, sk_lo, (cx - HW + 2, cy + 4), 8)           # ears
    pygame.draw.circle(surf, skin, (cx + HW - 2, cy + 4), 8)

    # -- the high balding brow: thin grey hair at the sides only --
    pygame.draw.arc(surf, hair, (cx - HW - 2, cy - HH + 14, 22, 52), 1.4, 3.4, 5)
    pygame.draw.arc(surf, hair, (cx + HW - 20, cy - HH + 14, 22, 52), 6.0, 8.0, 5)
    pygame.draw.arc(surf, (100, 100, 106), (cx - HW, cy - HH + 22, 18, 36), 1.6, 3.1, 2)
    for k in range(3):                                                  # strands combed over
        pygame.draw.arc(surf, hair, (cx - 30 + k * 9, cy - HH - 2, 46, 26), 0.5, 2.2, 1)

    # -- the face: deep hollows, hard grey brows, the named-them mouth --
    tilt = 4 if doomed else 0
    pygame.draw.line(surf, (88, 88, 92), (cx - 30, cy - 15), (cx - 8, cy - 13 + tilt), 4)
    pygame.draw.line(surf, (88, 88, 92), (cx + 8, cy - 13 + tilt), (cx + 30, cy - 15), 4)
    pygame.draw.line(surf, sk_lo, (cx - 3, cy - 16), (cx - 3, cy - 6), 2)   # sermon creases
    pygame.draw.line(surf, sk_lo, (cx + 3, cy - 16), (cx + 3, cy - 6), 2)
    for sgn in (-1, 1):
        ex = cx + sgn * 19
        ey = cy - 2
        sock = pygame.Surface((30, 20), pygame.SRCALPHA)                 # soft deep socket
        pygame.draw.ellipse(sock, (*sk_sh, 120), (0, 0, 30, 20))
        surf.blit(sock, (ex - 15, ey - 10))
        if blink:
            pygame.draw.line(surf, sk_sh, (ex - 10, ey + 1), (ex + 10, ey + 1), 3)
        else:
            pygame.draw.ellipse(surf, (182, 180, 164), (ex - 9, ey - 4, 18, 9))
            pygame.draw.circle(surf, (96, 100, 96), (ex, ey), 4)
            pygame.draw.circle(surf, (20, 20, 18), (ex, ey), 2)
            pygame.draw.circle(surf, (208, 206, 192), (ex - 2, ey - 1), 1)
            pygame.draw.line(surf, sk_sh, (ex - 10, ey - 4), (ex + 9, ey - 5), 3)  # heavy lid
        pygame.draw.arc(surf, sk_lo, (ex - 10, ey + 3, 20, 11), 3.5, 5.9, 2)  # hung under-eyes
    # long thin nose, the sunken cheeks
    pygame.draw.line(surf, sk_lo, (cx + 1, cy - 10), (cx - 1, cy + 16), 2)
    pygame.draw.ellipse(surf, sk_lo, (cx - 5, cy + 13, 10, 6))
    pygame.draw.arc(surf, sk_sh, (cx - 36, cy - 2, 20, 34), 0.6, 2.1, 3)      # HOLLOWS
    pygame.draw.arc(surf, sk_sh, (cx + 16, cy - 2, 20, 34), 1.0, 2.5, 3)
    # the mouth: thin, corners pinned down; set harder when he is done waiting
    my = cy + 30
    pygame.draw.line(surf, (104, 80, 74), (cx - 12, my), (cx + 12, my), 3 if doomed else 2)
    pygame.draw.line(surf, sk_lo, (cx - 15, my + 3), (cx - 11, my), 2)   # the down corners
    pygame.draw.line(surf, sk_lo, (cx + 11, my), (cx + 15, my + 3), 2)
    pygame.draw.line(surf, sk_lo, (cx, my + 10), (cx, my + 16), 1)      # a thin chin crease
    for sgn in (-1, 1):                                                 # deep age folds
        pygame.draw.arc(surf, sk_lo, (cx + sgn * 14 - 7, my - 14, 14, 20),
                        (1.2 if sgn > 0 else 0.4), (2.7 if sgn > 0 else 1.9), 2)


def draw_crane_tableau(surf, t, state):
    """The church chancel, across Crane's lectern. Candled dusk (his light is
    the flames he keeps lit for nobody): board walls, the plain cross, the
    stopped hymn board, the tall arched window going out, the bell rope dead
    at the edge. `state["doomed"]`: pressed, his hands grip the lectern and
    he is done waiting; else they stay folded over it."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    doomed = state.get("doomed", False)

    # -- board walls, dusk-dark; vertical planks --
    top = (64, 54, 44); bot = (30, 26, 22)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    for sx in range(0, W, 46):
        pygame.draw.line(surf, (44, 37, 30), (sx, 0), (sx, H), 1)
    pygame.draw.rect(surf, (38, 32, 26), (0, int(H * 0.78), W, int(H * 0.06)))  # rail shadow line

    # -- the bell rope, hanging dead at the left edge; it barely drifts --
    rx = int(W * 0.055) + int(2 * math.sin(t * 0.6))
    pygame.draw.line(surf, (118, 106, 84), (int(W * 0.055), 0), (rx, int(H * 0.52)), 3)
    pygame.draw.circle(surf, (100, 90, 70), (rx, int(H * 0.53)), 6)     # the knotted end
    pygame.draw.line(surf, (84, 75, 58), (rx - 4, int(H * 0.50)), (rx + 4, int(H * 0.50)), 2)

    # -- the hymn board: the numbers of a service nobody held since --
    hbx, hby = int(W * 0.125), int(H * 0.10)
    hbw, hbh = 118, 150
    pygame.draw.rect(surf, (22, 19, 15), (hbx + 4, hby + 5, hbw, hbh))
    pygame.draw.rect(surf, (52, 42, 30), (hbx, hby, hbw, hbh))
    pygame.draw.rect(surf, (74, 60, 42), (hbx, hby, hbw, hbh), 4)
    pygame.draw.rect(surf, (150, 140, 118), (hbx + 12, hby + 10, hbw - 24, 18))  # title strip
    for i in range(3):
        pygame.draw.line(surf, (96, 88, 72), (hbx + 18 + i * 30, hby + 15),
                         (hbx + 34 + i * 30, hby + 23), 2)
    seg = (196, 188, 164)
    rnd0 = random.Random(3)
    for r in range(3):                                                  # three hymn rows
        ty = hby + 42 + r * 34
        for c in range(3):
            tx2 = hbx + 16 + c * 32
            if r == 2 and c == 2:
                continue                                                # one tile long fallen
            pygame.draw.rect(surf, (30, 26, 21), (tx2, ty, 24, 24))
            d = rnd0.randint(0, 9)
            # crude seven-seg digit
            if d not in (1, 4):
                pygame.draw.line(surf, seg, (tx2 + 6, ty + 4), (tx2 + 18, ty + 4), 2)
            if d not in (0, 1, 7):
                pygame.draw.line(surf, seg, (tx2 + 6, ty + 12), (tx2 + 18, ty + 12), 2)
            if d not in (1, 4, 7):
                pygame.draw.line(surf, seg, (tx2 + 6, ty + 20), (tx2 + 18, ty + 20), 2)
            if d in (0, 2, 6, 8):
                pygame.draw.line(surf, seg, (tx2 + 6, ty + 12), (tx2 + 6, ty + 20), 2)
            if d not in (2,):
                pygame.draw.line(surf, seg, (tx2 + 18, ty + 4), (tx2 + 18, ty + 12), 2)
            if d in (0, 1, 3, 4, 5, 6, 8, 9):
                pygame.draw.line(surf, seg, (tx2 + 18, ty + 12), (tx2 + 18, ty + 20), 2)
            if d in (0, 4, 8, 9):
                pygame.draw.line(surf, seg, (tx2 + 6, ty + 4), (tx2 + 6, ty + 12), 2)

    # -- the plain wooden cross, high on the chancel wall --
    ccx, ccy = int(W * 0.565), int(H * 0.115)
    pygame.draw.rect(surf, (20, 17, 13), (ccx - 7 + 4, ccy - 8 + 5, 18, 128))   # drop shadow
    pygame.draw.rect(surf, (20, 17, 13), (ccx - 42 + 4, ccy + 24 + 5, 88, 16))
    pygame.draw.rect(surf, (86, 66, 46), (ccx - 7, ccy - 8, 14, 124))
    pygame.draw.rect(surf, (86, 66, 46), (ccx - 42, ccy + 24, 84, 13))
    pygame.draw.line(surf, (112, 88, 62), (ccx - 5, ccy - 6, ), (ccx - 5, ccy + 112), 2)
    pygame.draw.line(surf, (112, 88, 62), (ccx - 40, ccy + 26), (ccx + 38, ccy + 26), 2)
    pygame.draw.line(surf, (56, 42, 30), (ccx - 2, ccy + 30), (ccx + 3, ccy + 34), 1)  # grain

    # -- the tall arched window, the day going out of it --
    wx, wy = int(W * 0.695), int(H * 0.07)
    ww, wh = int(W * 0.185), int(H * 0.55)
    pygame.draw.rect(surf, (34, 28, 22), (wx - 10, wy + ww // 2, ww + 20, wh - ww // 2 + 10))
    pygame.draw.circle(surf, (34, 28, 22), (wx + ww // 2, wy + ww // 2), ww // 2 + 10)
    glass_t = (150, 138, 112); glass_b = (96, 88, 72)                   # dusk, not day
    for gy in range(wh):
        c = _lerp(glass_t, glass_b, gy / wh)
        if gy < ww // 2:                                                # arched top rows
            half = int(math.sqrt(max(0, (ww // 2) ** 2 - (ww // 2 - gy) ** 2)))
            surf.fill(c, (wx + ww // 2 - half, wy + gy, half * 2, 1))
        else:
            surf.fill(c, (wx, wy + gy, ww, 1))
    pygame.draw.rect(surf, (120, 110, 88), (wx, wy + int(wh * 0.70), ww, int(wh * 0.10)))  # treeline
    pygame.draw.rect(surf, (132, 120, 94), (wx, wy + int(wh * 0.80), ww, int(wh * 0.20)))  # corn band
    for cxx in range(wx + 3, wx + ww, 9):
        pygame.draw.line(surf, (112, 102, 78), (cxx, wy + int(wh * 0.82)), (cxx, wy + wh), 1)
    pygame.draw.line(surf, (34, 28, 22), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 5)  # muntins
    pygame.draw.line(surf, (34, 28, 22), (wx, wy + int(wh * 0.42)), (wx + ww, wy + int(wh * 0.42)), 5)
    arc_r = ww // 2 + 10
    pygame.draw.arc(surf, (58, 46, 34), (wx - 10, wy - 10 + 6, ww + 20, arc_r * 2),
                    0.0, math.pi, 6)                                    # arch frame
    pygame.draw.rect(surf, (58, 46, 34), (wx - 10, wy + arc_r - 4, ww + 20, wh - arc_r + 14), 4)

    # -- the candle stand: his kept flames, the light of the room --
    csx, csy = int(W * 0.845), int(H * 0.70)
    pygame.draw.line(surf, (54, 48, 40), (csx, csy), (csx, csy - 96), 5)     # the standard
    pygame.draw.ellipse(surf, (44, 39, 33), (csx - 26, csy - 4, 52, 12))     # the foot
    pygame.draw.line(surf, (54, 48, 40), (csx - 30, csy - 96), (csx + 30, csy - 96), 4)
    flames = []
    for k, dx in enumerate((-30, 0, 30)):
        chx = csx + dx
        chy = csy - 96
        pygame.draw.rect(surf, (204, 196, 172), (chx - 4, chy - 26, 8, 26))  # candles
        fl = 1.0 + 0.22 * math.sin(t * 6.1 + k * 2.4) * math.sin(t * 2.3 + k)
        pygame.draw.ellipse(surf, (255, 216, 130), (chx - 4, chy - 26 - int(14 * fl), 8, int(14 * fl)))
        pygame.draw.ellipse(surf, (255, 244, 200), (chx - 2, chy - 26 - int(9 * fl), 4, int(8 * fl)))
        flames.append((chx, chy - 30))
    halo = pygame.Surface((W, H), pygame.SRCALPHA)                       # candle wash
    fl0 = 0.92 + 0.08 * math.sin(t * 5.3) * math.sin(t * 1.9)
    for r in range(int(H * 0.78), 0, -12):
        a = int(84 * (1 - r / (H * 0.78)) * fl0)
        pygame.draw.circle(halo, (255, 206, 130, a), (csx - 20, csy - 120), r)
    surf.blit(halo, (0, 0))
    rnd2 = random.Random(23)                                             # dust in the glow
    for _ in range(36):
        base = rnd2.randint(0, 700)
        yy = int(H * 0.10 + (t * 6 + base) % (H * 0.58))
        mx = int(W * 0.60) + int(90 * math.sin(t * 0.4 + base)) + rnd2.randint(-40, 40)
        pygame.draw.circle(surf, (236, 220, 184), (mx, yy), 1)

    # -- Crane at his lectern: breath, blink, the fork carried in his set --
    bob = int(2 * math.sin(t * 1.05))
    _draw_crane(surf, int(W * 0.395), int(H * 0.285) + bob, (t % 4.6) < 0.16, doomed)

    # -- the lectern, rising into frame; the open book; his hands on it --
    lx0, ly0 = int(W * 0.395), int(H * 0.70)
    pygame.draw.polygon(surf, (46, 36, 25),                              # the shaft
                        [(lx0 - 44, H), (lx0 + 44, H), (lx0 + 34, ly0 + 40), (lx0 - 34, ly0 + 40)])
    pygame.draw.polygon(surf, (64, 50, 34),                              # the sloped top
                        [(lx0 - 96, ly0 + 10), (lx0 + 96, ly0 + 10), (lx0 + 78, ly0 + 52),
                         (lx0 - 78, ly0 + 52)])
    pygame.draw.polygon(surf, (40, 31, 21),
                        [(lx0 - 96, ly0 + 8), (lx0 + 96, ly0 + 8), (lx0 + 96, ly0 + 14),
                         (lx0 - 96, ly0 + 14)])
    pygame.draw.line(surf, (88, 70, 46), (lx0 - 96, ly0 + 10), (lx0 + 96, ly0 + 10), 2)
    pygame.draw.line(surf, (30, 24, 17), (lx0 - 60, ly0 + 62), (lx0 + 60, ly0 + 62), 2)  # front cross rail
    # the open book on the slope
    pygame.draw.polygon(surf, (196, 190, 172),
                        [(lx0 - 58, ly0 + 18), (lx0 - 4, ly0 + 14), (lx0 - 2, ly0 + 40),
                         (lx0 - 52, ly0 + 46)])
    pygame.draw.polygon(surf, (188, 182, 164),
                        [(lx0 + 2, ly0 + 14), (lx0 + 56, ly0 + 18), (lx0 + 50, ly0 + 46),
                         (lx0, ly0 + 40)])
    pygame.draw.line(surf, (120, 112, 96), (lx0 - 2, ly0 + 14), (lx0, ly0 + 42), 2)  # the gutter
    for i in range(4):                                                   # scripture lines
        pygame.draw.line(surf, (128, 120, 104), (lx0 - 48, ly0 + 22 + i * 6),
                         (lx0 - 10, ly0 + 19 + i * 6), 1)
        pygame.draw.line(surf, (128, 120, 104), (lx0 + 8, ly0 + 19 + i * 6),
                         (lx0 + 46, ly0 + 22 + i * 6), 1)
    # his hands: folded at the slope's front edge at rest (the book stays
    # readable above them); pressed, they GRIP the top corners, fingers
    # wrapped over the front edge
    skin = (172, 170, 150); sk_lo2 = (116, 116, 98)
    if doomed:
        for sgn in (-1, 1):
            hx2 = lx0 + sgn * 82
            pygame.draw.ellipse(surf, skin, (hx2 - 20, ly0 + 4, 40, 26))
            pygame.draw.ellipse(surf, sk_lo2, (hx2 - 20, ly0 + 4, 40, 26), 2)
            for fk in range(4):                                          # fingers over the edge
                pygame.draw.line(surf, sk_lo2, (hx2 - 12 + fk * 8, ly0 + 8),
                                 (hx2 - 13 + fk * 8, ly0 + 26), 3)
            pygame.draw.line(surf, (222, 218, 202), (hx2 - 12, ly0 + 8),
                             (hx2 + 12, ly0 + 6), 2)                     # white knuckle ridge
    else:
        fy0 = ly0 + 40
        pygame.draw.ellipse(surf, skin, (lx0 - 30, fy0, 60, 24))         # the under hand
        pygame.draw.ellipse(surf, sk_lo2, (lx0 - 30, fy0, 60, 24), 1)
        pygame.draw.ellipse(surf, skin, (lx0 - 20, fy0 - 8, 46, 22))     # the over hand
        pygame.draw.ellipse(surf, sk_lo2, (lx0 - 20, fy0 - 8, 46, 22), 1)
        for fk in range(4):                                              # laced fingers
            pygame.draw.line(surf, sk_lo2, (lx0 - 12 + fk * 9, fy0 - 2),
                             (lx0 - 8 + fk * 9, fy0 + 12), 2)

    # -- pew-back slivers at the bottom corners (the empty nave at our back) --
    pygame.draw.polygon(surf, (40, 31, 21), [(0, int(H * 0.90)), (int(W * 0.22), int(H * 0.94)),
                                             (int(W * 0.22), H), (0, H)])
    pygame.draw.line(surf, (58, 45, 30), (0, int(H * 0.905)), (int(W * 0.22), int(H * 0.945)), 3)
    pygame.draw.polygon(surf, (40, 31, 21), [(W, int(H * 0.90)), (int(W * 0.78), int(H * 0.94)),
                                             (int(W * 0.78), H), (W, H)])
    pygame.draw.line(surf, (58, 45, 30), (W, int(H * 0.905)), (int(W * 0.78), int(H * 0.945)), 3)

    # -- the candle key on him; eased vignette --
    key = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(int(H * 0.85), 0, -12):
        a = int(70 * (1 - r / (H * 0.85)) * fl0)
        pygame.draw.circle(key, (255, 210, 140, a), (int(W * 0.56), int(H * 0.38)), r)
    surf.blit(key, (0, 0))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = int(W * 0.45), int(H * 0.42)
    maxr = int(math.hypot(W, H) * 0.66); inner = int(maxr * 0.58)
    for r in range(maxr, inner, -10):
        a = max(0, int(140 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))
