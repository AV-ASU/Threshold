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
