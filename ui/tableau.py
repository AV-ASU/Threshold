"""Close-up examine TABLEAUX -- the diegetic "look at the thing" cutscenes.

Press [E] on a tagged prop and the world pauses on a high-detail, animated
close-up of that thing, with a menu of options that mutate the tableau live
(take the gun -> it leaves the table) and can open readable text. One system,
reused for the bedroom desk (the pilot), the face-across-a-table principal
talks (Sable's reception desk, Vane's office, Hettie's counter, Crane's
lectern, Toby's table), the Talk's grip, the pedestal, and Mara's
confrontation (the unmask reveal). Pure
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

    # --- the flashlight, his own kit, in the desk's lower corner ---
    flx, fly = int(W * 0.12), int(H * 0.76)
    if state.get("fl_present", True):
        f = pygame.Surface((200, 90), pygame.SRCALPHA)
        pygame.draw.rect(f, (72, 76, 84), (30, 34, 118, 24), border_radius=10)
        pygame.draw.rect(f, (96, 100, 110), (30, 34, 118, 8), border_radius=6)
        for kx in range(46, 140, 12):                      # knurled grip
            pygame.draw.line(f, (52, 55, 62), (kx, 36), (kx, 56), 1)
        pygame.draw.rect(f, (88, 92, 102), (140, 28, 26, 36), border_radius=6)
        pygame.draw.ellipse(f, (150, 158, 130), (158, 32, 10, 28))   # lens
        pygame.draw.ellipse(f, (222, 226, 192), (160, 38, 5, 12))    # glint
        pygame.draw.rect(f, (46, 48, 54), (24, 38, 8, 16))           # tailcap
        f = pygame.transform.rotate(f, -9)
        fsh = pygame.Surface(f.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(fsh, (0, 0, 0, 80), (18, 52, 170, 26))
        surf.blit(fsh, (flx - 4, fly + 10))
        surf.blit(f, (flx, fly))
    else:
        clean = pygame.Surface((150, 46), pygame.SRCALPHA)
        clean.fill((255, 220, 150, 12))
        pygame.draw.rect(clean, (255, 225, 160, 22), (0, 0, 150, 46), 2)
        clean = pygame.transform.rotate(clean, -9)
        surf.blit(clean, (flx + 14, fly + 14))

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

    # -- the COUNTY ROAD MAP, pinned and worked over --
    # This is where the JAN 15 calendar hung before the calendars were cut
    # (TODO #28). A map is the better object in this room by a distance: it
    # is the thing Vane has actually been doing for a year -- driving every
    # road out and being handed back -- and it says so without a line. The
    # ring around the town is his own pen.
    cx_, cy_ = int(W * 0.135), int(H * 0.11)
    cw, ch = 104, 112
    pygame.draw.rect(surf, (24, 21, 16), (cx_ + 4, cy_ + 5, cw, ch))      # drop shadow
    pygame.draw.rect(surf, (186, 178, 156), (cx_, cy_, cw, ch))           # the paper
    pygame.draw.rect(surf, (132, 124, 104), (cx_, cy_, cw, ch), 1)
    for px_, py_ in ((cx_ + 6, cy_ + 6), (cx_ + cw - 6, cy_ + 6),
                     (cx_ + 6, cy_ + ch - 6), (cx_ + cw - 6, cy_ + ch - 6)):
        pygame.draw.circle(surf, (74, 66, 50), (px_, py_), 2)             # the pins
    # section lines: a survey grid, the way a county actually platted it
    for i in range(1, 4):
        gx = cx_ + cw * i // 4
        gy = cy_ + ch * i // 4
        pygame.draw.line(surf, (162, 152, 128), (gx, cy_ + 3), (gx, cy_ + ch - 3), 1)
        pygame.draw.line(surf, (162, 152, 128), (cx_ + 3, gy), (cx_ + cw - 3, gy), 1)
    # the two roads that matter, heavier: the north road in, the river road
    pygame.draw.line(surf, (86, 78, 62), (cx_ + cw // 2, cy_ + 4),
                     (cx_ + cw // 2, cy_ + ch - 4), 3)
    pygame.draw.lines(surf, (86, 78, 62), False,
                      [(cx_ + 4, cy_ + ch - 34), (cx_ + cw // 3, cy_ + ch - 46),
                       (cx_ + cw - 18, cy_ + ch - 30)], 2)
    # the river, thinner and paler, running past the town
    pygame.draw.lines(surf, (108, 116, 118), False,
                      [(cx_ + 8, cy_ + 22), (cx_ + cw // 2 - 6, cy_ + 48),
                       (cx_ + cw - 10, cy_ + 62)], 2)
    # and the ring he drew around Brimley, gone over more than once
    for r in (17, 19):
        pygame.draw.circle(surf, (128, 44, 38),
                           (cx_ + cw // 2, cy_ + ch - 44), r, 1)

    # -- a pinned list beside the map: names, some struck through --
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
    tall arched window going out, the bell rope dead at the edge. `state["doomed"]`: pressed, his hands grip the lectern and
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


# ---- Toby: his kid sprite as a close-up across the little table -----------
# Child proportions, big worried eyes under the mop fringe, the tear-streak
# cheek marks kept from the sprite. `watch` turns his head toward the window
# (viewer-right, the corn line); `believed` levels the worried brow slant
# after the PI's promise ("Okay. I believe you.").
def _draw_toby(surf, cx, cy, blink, watch, believed):
    import pygame
    skin = (178, 172, 144); sk_hi = (200, 194, 164); sk_lo = (124, 120, 99)
    sk_sh = (84, 81, 66); streak = (128, 124, 104)
    tunic = (150, 138, 64); tunic_dk = (104, 95, 42); tunic_lt = (172, 160, 82)
    hair = (66, 46, 28); hair_dk = (44, 30, 18)
    turn = int(12 * watch)                          # toward the window, right
    HW, HH = 40, 48                                 # a kid's head, small
    tt = cy + HH - 2

    # -- the tunic: narrow kid shoulders, a patched elbow out of frame --
    pygame.draw.polygon(surf, tunic, [(cx - 62, tt + 10), (cx + 62, tt + 10),
                                      (cx + 54, tt + 220), (cx - 54, tt + 220)])
    pygame.draw.ellipse(surf, tunic, (cx - 68, tt - 4, 50, 36))
    pygame.draw.ellipse(surf, tunic, (cx + 18, tt - 4, 50, 36))
    pygame.draw.polygon(surf, tunic_dk, [(cx + 20, tt + 10), (cx + 62, tt + 10),
                                         (cx + 54, tt + 220), (cx + 20, tt + 220)])
    pygame.draw.polygon(surf, tunic_lt, [(cx - 62, tt + 10), (cx - 54, tt + 10),
                                         (cx - 48, tt + 220), (cx - 62, tt + 220)])
    # the collar: a plain crew-neck band
    pygame.draw.arc(surf, tunic_dk, (cx - 15, tt, 30, 16), 3.3, 6.1, 4)

    # -- neck + head --
    pygame.draw.rect(surf, sk_lo, (cx - 9 + turn // 2, cy + HH - 16, 18, 26))
    hx = cx + turn
    pygame.draw.ellipse(surf, skin, (cx - HW, cy - HH, HW * 2, HH * 2))
    # round kid cheeks: a soft jaw, no squaring
    dim = pygame.Surface((HW * 2 + 16, HH * 2 + 16), pygame.SRCALPHA)
    pygame.draw.ellipse(dim, (*sk_sh, 62), (0, 10, HW - 2 - turn, HH * 2 - 12))
    surf.blit(dim, (cx - HW, cy - HH))
    lit = pygame.Surface((HW * 2 + 16, HH * 2 + 16), pygame.SRCALPHA)
    pygame.draw.ellipse(lit, (*sk_hi, 110), (HW + 6, HH - 32, HW - 4, 58))
    surf.blit(lit, (cx - HW, cy - HH))
    pygame.draw.circle(surf, sk_lo, (cx - HW + 2, cy + 4), 6)           # ears
    pygame.draw.circle(surf, skin, (cx + HW - 2, cy + 4), 6)

    # -- the mop: one brown mass to just over the brow, ragged tips at the
    # brow line, side falls past the ears, the cowlick on top --
    pygame.draw.ellipse(surf, hair, (cx - HW - 3, cy - HH - 8, HW * 2 + 6, 46))
    for k in range(7):                                                  # ragged ends at the brow
        fx2 = cx - 34 + k * 11
        pygame.draw.polygon(surf, hair, [(fx2, cy - 26), (fx2 + 11, cy - 28),
                                         (fx2 + 5, cy - 13)])
    pygame.draw.rect(surf, hair, (cx - HW - 2, cy - 26, 8, 32))         # side falls
    pygame.draw.rect(surf, hair, (cx + HW - 6, cy - 26, 8, 32))
    pygame.draw.line(surf, hair_dk, (cx + 8, cy - HH - 6), (cx + 13, cy - HH - 15), 3)  # cowlick
    pygame.draw.line(surf, hair_dk, (cx + 13, cy - HH - 15), (cx + 18, cy - HH - 7), 2)

    # -- the face: big kid eyes, the worried slant that levels, the streaks --
    slant = 0 if believed else 3                    # worried up-slant, inner ends high
    pygame.draw.line(surf, (52, 38, 26), (hx - 24, cy - 10), (hx - 8, cy - 13 - slant), 3)
    pygame.draw.line(surf, (52, 38, 26), (hx + 8, cy - 13 - slant), (hx + 24, cy - 10), 3)
    for sgn in (-1, 1):
        ex = hx + sgn * 17
        ey = cy - 1
        if blink:
            pygame.draw.line(surf, sk_sh, (ex - 9, ey + 1), (ex + 9, ey + 1), 2)
        else:
            pygame.draw.ellipse(surf, (218, 214, 198), (ex - 9, ey - 6, 18, 13))  # big kid eyes
            pygame.draw.circle(surf, (74, 56, 36), (ex + (3 if watch > 0.5 else 0), ey + 1), 5)
            pygame.draw.circle(surf, (20, 16, 12), (ex + (3 if watch > 0.5 else 0), ey + 1), 2)
            pygame.draw.circle(surf, (232, 228, 214), (ex - 2 + (3 if watch > 0.5 else 0), ey - 1), 1)
            pygame.draw.line(surf, sk_lo, (ex - 9, ey - 6), (ex + 9, ey - 7), 1)
    # the small nose, the round cheeks
    pygame.draw.line(surf, sk_lo, (hx, cy + 2), (hx - 1, cy + 12), 2)
    pygame.draw.ellipse(surf, sk_lo, (hx - 4, cy + 10, 8, 5))
    # THE TELL: the cheek marks, slightly low, asymmetric; old tear-streaks
    pygame.draw.line(surf, streak, (hx - 13, cy + 12), (hx - 13, cy + 20), 2)
    pygame.draw.line(surf, (118, 112, 94), (hx + 12, cy + 15), (hx + 12, cy + 22), 2)
    # a kid's mouth: small, held shut ("I keep biting my tongue. To check.")
    my = cy + 24
    pygame.draw.line(surf, (124, 92, 84), (hx - 8, my), (hx + 8, my), 2)
    pygame.draw.line(surf, sk_lo, (hx - 10, my + 1), (hx - 8, my), 1)
    pygame.draw.line(surf, sk_lo, (hx + 8, my), (hx + 10, my + 1), 1)


def draw_toby_tableau(surf, t, state):
    """Toby's room, across the little table: the one almost-normal room in
    Brimley. Plain daylight, his crayon drawings taped up, the closet door
    with its own drawing, the toy radio, crayons and paper on the table. The
    window gives onto the corn line he watches. `state`: the idle-driven
    watch, the procession drawing once he has told it, the levelled brows
    once the PI has promised."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    watch = state.get("watch", 0.0)
    drawing = state.get("drawing_present", False)
    believed = state.get("believed", False)

    # -- a plain plastered kid's room, DAYLIT: the normal one --
    top = (108, 98, 82); bot = (56, 50, 42)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    pygame.draw.rect(surf, (66, 54, 40), (0, int(H * 0.60), W, 8))      # picture rail line

    # -- the closet door, far left, its own drawing taped on (C14) --
    cdx, cdw = 0, int(W * 0.115)
    pygame.draw.rect(surf, (74, 58, 40), (cdx, int(H * 0.04), cdw, int(H * 0.66)))
    pygame.draw.rect(surf, (52, 41, 28), (cdx, int(H * 0.04), cdw, int(H * 0.66)), 4)
    pygame.draw.rect(surf, (60, 47, 32), (cdx + 12, int(H * 0.10), cdw - 24, int(H * 0.24)), 2)
    pygame.draw.rect(surf, (60, 47, 32), (cdx + 12, int(H * 0.40), cdw - 24, int(H * 0.24)), 2)
    pygame.draw.circle(surf, (108, 100, 84), (cdx + cdw - 14, int(H * 0.38)), 4)
    # the taped drawing on the closet: a door, drawn tall, kid-crooked
    ddx, ddy = cdx + 22, int(H * 0.14)
    pygame.draw.rect(surf, (196, 190, 172), (ddx, ddy, 52, 64))
    pygame.draw.rect(surf, (170, 164, 146), (ddx, ddy, 52, 64), 1)
    pygame.draw.rect(surf, (150, 146, 128), (ddx + 20, ddy - 4, 12, 8))  # tape
    pygame.draw.rect(surf, (96, 74, 52), (ddx + 14, ddy + 12, 24, 42), 2)
    pygame.draw.circle(surf, (96, 74, 52), (ddx + 34, ddy + 34), 2)

    # -- the drawings wall: taped crayon sheets, slightly crooked --
    rnd = random.Random(41)
    sheets = [(int(W * 0.16), int(H * 0.09), -4), (int(W * 0.255), int(H * 0.13), 3),
              (int(W * 0.175), int(H * 0.33), 2), (int(W * 0.27), int(H * 0.36), -3)]
    for i, (sx_, sy_, ang) in enumerate(sheets):
        sheet = pygame.Surface((78, 60), pygame.SRCALPHA)
        sheet.fill((200, 194, 176))
        pygame.draw.rect(sheet, (172, 166, 148), (0, 0, 78, 60), 1)
        if i == 0:                                                      # the house
            pygame.draw.rect(sheet, (140, 96, 72), (22, 26, 32, 24), 2)
            pygame.draw.polygon(sheet, (140, 96, 72), [(18, 28), (38, 12), (58, 28)], 2)
            pygame.draw.line(sheet, (110, 106, 92), (48, 14), (48, 6), 2)
        elif i == 1:                                                    # the family
            for k in range(4):
                fx3 = 14 + k * 16
                hh2 = 14 if k < 2 else 9
                pygame.draw.circle(sheet, (104, 88, 120), (fx3, 24), 5, 2)
                pygame.draw.line(sheet, (104, 88, 120), (fx3, 29), (fx3, 29 + hh2), 2)
        elif i == 2:                                                    # the corn
            for k in range(6):
                cx3 = 10 + k * 12
                pygame.draw.line(sheet, (128, 118, 64), (cx3, 48), (cx3, 18), 2)
                pygame.draw.line(sheet, (128, 118, 64), (cx3, 26), (cx3 + 6, 20), 1)
        else:                                                           # the sun, half-page
            pygame.draw.circle(sheet, (168, 148, 84), (58, 14), 9, 2)
            for k in range(5):
                a2 = k * 0.7 + 0.4
                pygame.draw.line(sheet, (168, 148, 84),
                                 (58 + int(11 * math.cos(a2)), 14 + int(11 * math.sin(a2))),
                                 (58 + int(16 * math.cos(a2)), 14 + int(16 * math.sin(a2))), 1)
        sheet = pygame.transform.rotate(sheet, ang)
        surf.blit(sheet, (sx_, sy_))
        pygame.draw.rect(surf, (150, 146, 128), (sx_ + 30, sy_ - 2, 14, 7))     # tape

    # -- the procession drawing, up once he has told it: the dark one --
    if drawing:
        pdx, pdy = int(W * 0.355), int(H * 0.14)
        psheet = pygame.Surface((92, 70), pygame.SRCALPHA)
        psheet.fill((198, 192, 174))
        pygame.draw.rect(psheet, (170, 164, 146), (0, 0, 92, 70), 1)
        pygame.draw.line(psheet, (90, 102, 116), (6, 52), (86, 46), 2)   # the river, wavy
        pygame.draw.line(psheet, (90, 102, 116), (10, 55), (82, 50), 1)
        for k in range(7):                                               # the line of them
            fx3 = 12 + k * 10
            fy3 = 30 - k
            pygame.draw.circle(psheet, (48, 44, 42), (fx3, fy3), 3, 1)
            pygame.draw.line(psheet, (48, 44, 42), (fx3, fy3 + 3), (fx3, fy3 + 12), 2)
        pygame.draw.ellipse(psheet, (30, 27, 25), (72, 20, 16, 10))      # the hole they went in
        psheet = pygame.transform.rotate(psheet, -2)
        surf.blit(psheet, (pdx, pdy))
        pygame.draw.rect(surf, (150, 146, 128), (pdx + 36, pdy - 3, 14, 7))
        pygame.draw.rect(surf, (150, 146, 128), (pdx + 8, pdy + 62, 12, 6))  # taped twice, careful

    # -- the window, viewer-right: plain day over the corn line he watches --
    wx, wy = int(W * 0.60), int(H * 0.08)
    ww, wh = int(W * 0.22), int(H * 0.42)
    pygame.draw.rect(surf, (66, 52, 36), (wx - 10, wy - 10, ww + 20, wh + 20))
    glass_t = (196, 190, 168); glass_b = (162, 154, 128)
    for gy in range(wh):
        surf.fill(_lerp(glass_t, glass_b, gy / wh), (wx, wy + gy, ww, 1))
    pygame.draw.rect(surf, (150, 142, 112), (wx, wy + int(wh * 0.56), ww, int(wh * 0.10)))  # treeline
    pygame.draw.rect(surf, (170, 158, 118), (wx, wy + int(wh * 0.66), ww, int(wh * 0.34)))  # THE CORN LINE
    for cxx in range(wx + 4, wx + ww, 8):
        pygame.draw.line(surf, (146, 134, 96), (cxx, wy + int(wh * 0.70)), (cxx, wy + wh), 1)
    pygame.draw.line(surf, (66, 52, 36), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 5)
    pygame.draw.line(surf, (66, 52, 36), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 5)
    pygame.draw.rect(surf, (84, 66, 44), (wx - 10, wy - 10, ww + 20, wh + 20), 4)
    pygame.draw.rect(surf, (84, 66, 44), (wx - 16, wy + wh + 10, ww + 32, 10))   # sill
    # a soft day shaft into the room
    shaft = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(shaft, (226, 216, 184, 30),
                        [(wx, wy + 10), (wx + ww, wy), (int(W * 0.50), int(H * 0.90)),
                         (int(W * 0.26), int(H * 0.90))])
    surf.blit(shaft, (0, 0))

    # -- the toy radio on its shelf corner, right of the window --
    trx, try_ = int(W * 0.875), int(H * 0.47)
    pygame.draw.rect(surf, (66, 52, 36), (trx - 12, try_ + 22, int(W * 0.11), 8))  # its shelf
    pygame.draw.rect(surf, (118, 74, 56), (trx, try_ - 10, 66, 34), border_radius=6)
    pygame.draw.rect(surf, (86, 52, 40), (trx, try_ - 10, 66, 34), 2, border_radius=6)
    pygame.draw.circle(surf, (188, 178, 156), (trx + 16, try_ + 7), 8)
    pygame.draw.circle(surf, (86, 52, 40), (trx + 16, try_ + 7), 8, 2)
    pygame.draw.line(surf, (86, 52, 40), (trx + 16, try_ + 7), (trx + 20, try_ + 2), 2)
    for k in range(4):                                                   # the speaker slots
        pygame.draw.line(surf, (86, 52, 40), (trx + 34, try_ - 2 + k * 6),
                         (trx + 58, try_ - 2 + k * 6), 2)
    pygame.draw.line(surf, (86, 52, 40), (trx + 58, try_ - 10), (trx + 70, try_ - 26), 2)  # antenna
    pygame.draw.circle(surf, (86, 52, 40), (trx + 70, try_ - 27), 2)

    # -- Toby across the little table: small, low in the frame --
    bob = int(3 * math.sin(t * 1.6))                                     # a kid never quite still
    _draw_toby(surf, int(W * 0.415), int(H * 0.375) + bob, (t % 3.1) < 0.14,
               watch, believed)

    # -- the little table: crayons, paper, his hands --
    dtop = int(H * 0.685)
    pygame.draw.polygon(surf, (58, 44, 28), [(0, dtop), (W, dtop), (W, H), (0, H)])
    pygame.draw.polygon(surf, (92, 72, 46),
                        [(int(W * 0.02), dtop - 22), (int(W * 0.98), dtop - 22), (W, dtop), (0, dtop)])
    pygame.draw.line(surf, (118, 94, 60), (0, dtop), (W, dtop), 2)
    for gxx in range(0, W, 110):
        pygame.draw.line(surf, (48, 36, 22), (gxx, dtop + 8), (gxx - 8, H), 1)
    # a half-drawn sheet + scattered crayons
    shx, shy = int(W * 0.17), dtop - 6
    quad = [(shx, shy), (shx + 92, shy - 8), (shx + 102, shy + 18), (shx + 12, shy + 26)]
    pygame.draw.polygon(surf, (14, 12, 10), [(x + 3, y + 3) for x, y in quad])
    pygame.draw.polygon(surf, (202, 196, 178), quad)
    pygame.draw.arc(surf, (110, 96, 118), (shx + 20, shy - 4, 40, 22), 0.4, 2.6, 2)
    pygame.draw.line(surf, (110, 96, 118), (shx + 30, shy + 10), (shx + 52, shy + 6), 2)
    crayons = [((0.32, 8), (150, 90, 74)), ((0.55, -4), (96, 108, 88)),
               ((0.60, 10), (104, 88, 120)), ((0.64, 2), (168, 148, 84))]
    for (fx4, dy4), col in crayons:
        cx4, cy4 = int(W * fx4), dtop + dy4
        pygame.draw.line(surf, col, (cx4, cy4), (cx4 + 26, cy4 - 5), 5)
        pygame.draw.polygon(surf, col, [(cx4 + 26, cy4 - 8), (cx4 + 32, cy4 - 6), (cx4 + 26, cy4 - 2)])
    # his hands on the table edge: one flat, one fisted round a crayon
    tcx = int(W * 0.415)
    skin2 = (168, 163, 136); sk_lo2 = (118, 114, 94)
    pygame.draw.ellipse(surf, skin2, (tcx - 58, dtop - 12, 36, 20))      # flat hand
    pygame.draw.ellipse(surf, sk_lo2, (tcx - 58, dtop - 12, 36, 20), 1)
    for fk in range(3):
        pygame.draw.line(surf, sk_lo2, (tcx - 50 + fk * 8, dtop - 10),
                         (tcx - 52 + fk * 8, dtop + 4), 1)
    fisty = dtop - 10 + int(2 * math.sin(t * 2.3))                       # the fidget
    pygame.draw.ellipse(surf, skin2, (tcx + 22, fisty, 30, 22))          # the fist
    pygame.draw.ellipse(surf, sk_lo2, (tcx + 22, fisty, 30, 22), 1)
    pygame.draw.line(surf, (150, 90, 74), (tcx + 30, fisty - 10), (tcx + 36, fisty + 4), 5)  # the crayon in it

    # -- soft daylight key; the mildest vignette of the five --
    key = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(int(H * 0.9), 0, -12):
        a = int(52 * (1 - r / (H * 0.9)))
        pygame.draw.circle(key, (238, 228, 196, a), (int(W * 0.62), int(H * 0.34)), r)
    surf.blit(key, (0, 0))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = int(W * 0.45), int(H * 0.44)
    maxr = int(math.hypot(W, H) * 0.68); inner = int(maxr * 0.62)
    for r in range(maxr, inner, -10):
        a = max(0, int(118 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- THE TALK: the first cult grab, made the closest frame in the game ----
# Every principal seat is a room with furniture between you; the Talk is the
# inversion: no room (near-nothing behind him), no table (his arm crosses the
# frame to YOUR shoulder in the corner), and no face (the carved wooden mask
# of his sprite, grafted in, void sockets with a gold ember far down, no
# mouth: the courteous words come from behind wood that does not move). He
# leans in, very slowly, the whole time.
def draw_talk_tableau(surf, t, state):
    """The grip close-up. Sprite-true: stitched hide coat with bone-thread
    seams, deep fur hood, the carved mask (an irregular hewn oval, the
    door-dream grammar: recessed sockets, no mouth) with the Sign scratched
    faint on the brow and the graft seam where wood meets flesh. His hand
    is on your shoulder at the bottom corner; `reaching` rests his other
    hand on your wrist. The only motion: the embers, the fingers, the lean."""
    import pygame
    W, H = surf.get_width(), surf.get_height()
    reaching = state.get("reaching", False)

    # -- nowhere: near-dark, the faintest corn suggestion at the edges --
    top = (26, 23, 19); bot = (8, 7, 7)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    rnd = random.Random(13)
    for _ in range(26):                                              # stalk ghosts
        sx = rnd.choice([rnd.randint(0, int(W * 0.14)),
                         rnd.randint(int(W * 0.82), W - 1)])
        sh = rnd.randint(int(H * 0.2), int(H * 0.6))
        pygame.draw.line(surf, (38, 34, 24), (sx, H), (sx + rnd.randint(-6, 6), H - sh), 1)

    # -- the lean: he is closer than he was. Slowly. --
    lean = min(16.0, t * 0.5)
    cx = int(W * 0.47)
    cy = int(H * 0.34) + int(lean * 0.7) + int(2 * math.sin(t * 0.9))
    hood_r = int(150 + lean)

    # -- the hide coat: the pelt mass owns the lower frame, edge to edge --
    tt = cy + int(hood_r * 0.72)
    pygame.draw.polygon(surf, (52, 40, 29), [(cx - 320, tt + 70), (cx + 320, tt + 70),
                                             (cx + 430, H), (cx - 430, H)])
    pygame.draw.polygon(surf, (40, 33, 28), [(cx - 20, tt + 62), (cx + 320, tt + 70),
                                             (cx + 430, H), (cx + 30, H)])
    pygame.draw.polygon(surf, (64, 50, 36), [(cx - 320, tt + 72), (cx - 130, tt + 64),
                                             (cx - 190, H), (cx - 430, H)])
    pygame.draw.polygon(surf, (46, 37, 27), [(cx - 130, tt + 64), (cx - 20, tt + 62),
                                             (cx - 40, H), (cx - 190, H)])
    for k in range(3):                                               # bone-thread seams
        for j in range(3):
            sy0 = tt + 100 + k * 74 + j * 13
            pygame.draw.line(surf, (150, 138, 112), (cx - 130 + k * 3, sy0),
                             (cx - 121 + k * 3, sy0 + 8), 3)
            pygame.draw.line(surf, (150, 138, 112), (cx + 150 - k * 3, sy0 + 30),
                             (cx + 159 - k * 3, sy0 + 38), 3)

    # -- the fur hood: a deep ring, the opening near-black --
    pygame.draw.ellipse(surf, (70, 58, 40), (cx - hood_r, cy - hood_r - 12,
                                             hood_r * 2, hood_r * 2 + 44))
    pygame.draw.ellipse(surf, (48, 39, 28), (cx - hood_r + 14, cy - hood_r + 2,
                                             hood_r * 2 - 28, hood_r * 2 + 16))
    rnd2 = random.Random(5)
    for _ in range(150):                                             # fur ticks on the rim
        a2 = rnd2.uniform(0, math.pi * 2)
        rr = hood_r - rnd2.randint(0, 12)
        fx = cx + int(math.cos(a2) * rr)
        fy = cy + 8 + int(math.sin(a2) * (rr * 0.94))
        ln = rnd2.randint(6, 13)
        pygame.draw.line(surf, (108, 90, 62), (fx, fy),
                         (fx + int(math.cos(a2) * ln), fy + int(math.sin(a2) * ln)), 1)
    pygame.draw.ellipse(surf, (13, 11, 10), (cx - hood_r + 34, cy - hood_r + 26,
                                             hood_r * 2 - 68, hood_r * 2 - 30))

    # -- the flesh the mask grafts into: a margin, hood-shadowed --
    pygame.draw.ellipse(surf, (88, 76, 66), (cx - 96, cy - 112, 192, 236))

    # -- the carved mask: an irregular HEWN oval (the door-dream grammar) --
    mw, mh = 80, 106
    rnd3 = random.Random(9)
    mask = []
    for k in range(16):                                              # jagged blob edge
        a3 = -math.pi / 2 + k * (math.pi * 2 / 16)
        jr = 1.0 + rnd3.uniform(-0.07, 0.07)
        mask.append((cx + int(math.cos(a3) * mw * jr),
                     cy + int(math.sin(a3) * mh * jr)))
    pygame.draw.polygon(surf, (150, 128, 96), mask)
    pygame.draw.polygon(surf, (96, 80, 58), mask, 4)
    # long vertical grain + adze facets (hewn, not sawn)
    pygame.draw.arc(surf, (118, 100, 74), (cx - 54, cy - mh + 10, 44, mh * 2 - 24), 1.2, 2.1, 2)
    pygame.draw.arc(surf, (118, 100, 74), (cx + 8, cy - mh + 14, 48, mh * 2 - 30), 1.1, 1.9, 2)
    pygame.draw.line(surf, (128, 108, 80), (cx - mw + 16, cy - 58), (cx - 16, cy - 84), 3)
    pygame.draw.line(surf, (128, 108, 80), (cx + 22, cy - 88), (cx + mw - 18, cy - 52), 3)
    pygame.draw.line(surf, (128, 108, 80), (cx - mw + 14, cy + 44), (cx - 10, cy + 72), 3)
    pygame.draw.lines(surf, (54, 44, 32), False,                     # a long dry crack
                      [(cx + 38, cy - mh + 6), (cx + 30, cy - 34), (cx + 42, cy + 14),
                       (cx + 34, cy + 52)], 3)
    # the Sign, scratched faint on the brow
    sgx, sgy = cx - 4, cy - mh + 46
    pygame.draw.line(surf, (122, 106, 46), (sgx, sgy - 18), (sgx, sgy + 15), 3)
    pygame.draw.line(surf, (122, 106, 46), (sgx - 16, sgy - 6), (sgx + 13, sgy - 13), 3)
    pygame.draw.line(surf, (122, 106, 46), (sgx - 13, sgy + 10), (sgx + 16, sgy + 4), 3)

    # -- the carved void sockets: recessed, and the gold far DOWN in them --
    for sgn, ph in ((-1, 0.0), (1, 1.7)):
        ex = cx + sgn * 36
        ey = cy - 12 + (4 if sgn > 0 else 0)        # carved by hand, not level
        pygame.draw.ellipse(surf, (74, 62, 46), (ex - 26, ey - 22, 52, 46))   # carved recess
        pygame.draw.ellipse(surf, (36, 30, 24), (ex - 22, ey - 15, 42, 38))
        pygame.draw.ellipse(surf, (6, 5, 7), (ex - 17, ey - 9, 32, 30))       # the pit, low
        glow = 0.5 + 0.5 * math.sin(t * 1.1 + ph)
        g = pygame.Surface((32, 30), pygame.SRCALPHA)
        pygame.draw.circle(g, (230, 186, 48, int(34 * glow)), (15, 20), 10)
        surf.blit(g, (ex - 17, ey - 9), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(surf, (150, 120, 50), (ex - 1, ey + 10), 3)        # the ember, far down
        pygame.draw.circle(surf, (255, 218, 96), (ex - 2, ey + 9), 1)
    # no mouth. the wood does not move.

    # -- the graft seam: where the wood meets the flesh, it goes IN --
    pygame.draw.lines(surf, (74, 28, 26), False,
                      [(cx + mw - 4, cy - 26), (cx + mw + 4, cy + 10), (cx + mw - 8, cy + 52)], 4)
    pygame.draw.lines(surf, (46, 18, 17), False,
                      [(cx + mw - 1, cy - 8), (cx + mw + 2, cy + 22)], 2)
    pygame.draw.lines(surf, (74, 28, 26), False,
                      [(cx - mw + 6, cy + 56), (cx - mw - 2, cy + 76)], 3)

    # -- fur collar spikes over the coat line --
    for fx in range(cx - 150, cx + 152, 11):
        fh = 14 + (fx % 17)
        pygame.draw.line(surf, (108, 90, 62), (fx, tt + 74), (fx + 3, tt + 74 - fh), 3)

    # -- YOUR shoulder, bottom-left; his arm across the frame; the GRIP --
    grip = int(3 * math.sin(t * 0.7))                                # the fingers, slowly
    pygame.draw.polygon(surf, (36, 34, 37), [(0, H - 190), (int(W * 0.34), H - 118),
                                             (int(W * 0.38), H), (0, H)])   # your coat shoulder
    pygame.draw.line(surf, (66, 63, 68), (0, H - 186), (int(W * 0.33), H - 116), 5)
    pygame.draw.line(surf, (24, 22, 24), (0, H - 178), (int(W * 0.32), H - 108), 2)
    pygame.draw.polygon(surf, (58, 45, 32),                          # his sleeve, crossing
                        [(cx - 230, tt + 96), (cx - 130, tt + 70),
                         (int(W * 0.245), H - 148), (int(W * 0.135), H - 84)])
    pygame.draw.polygon(surf, (44, 34, 25),
                        [(cx - 230, tt + 96), (cx - 196, tt + 86),
                         (int(W * 0.175), H - 108), (int(W * 0.135), H - 84)])
    for k in range(5):                                               # fur cuff
        pygame.draw.line(surf, (108, 90, 62), (int(W * 0.16) + k * 10, H - 122 + k * 7),
                         (int(W * 0.148) + k * 10, H - 142 + k * 7), 3)
    hx0, hy0 = int(W * 0.185), H - 132                               # the hand: big, weathered
    pygame.draw.ellipse(surf, (158, 138, 114), (hx0 - 18, hy0 - 8, 88, 50))
    pygame.draw.ellipse(surf, (104, 88, 70), (hx0 - 18, hy0 - 8, 88, 50), 3)
    for fk in range(4):                                              # fingers WRAP the crest
        fx3 = hx0 + 4 + fk * 18
        pygame.draw.line(surf, (158, 138, 114), (fx3, hy0 + 24),
                         (fx3 - 5, hy0 + 56 + grip + (fk % 2) * 2), 12)
        pygame.draw.circle(surf, (170, 150, 124), (fx3, hy0 + 22), 7)        # knuckles
        pygame.draw.line(surf, (104, 88, 70), (fx3 - 3, hy0 + 40 + grip // 2),
                         (fx3 - 4, hy0 + 48 + grip // 2), 3)
    pygame.draw.ellipse(surf, (158, 138, 114), (hx0 - 36, hy0 + 14, 26, 38))  # the thumb
    pygame.draw.line(surf, (206, 196, 182), (hx0 + 2, hy0 + 4), (hx0 + 58, hy0 - 1), 2)

    # -- reaching: the other hand is already on your wrist, resting --
    if reaching:
        pygame.draw.polygon(surf, (30, 28, 30),                      # your forearm, mid-reach
                            [(int(W * 0.60), H), (int(W * 0.70), H - 100),
                             (int(W * 0.80), H - 84), (int(W * 0.80), H)])
        pygame.draw.line(surf, (48, 46, 50), (int(W * 0.70), H - 98),
                         (int(W * 0.795), H - 84), 3)
        pygame.draw.polygon(surf, (58, 45, 32),                      # his sleeve, from the dark
                            [(cx + 230, tt + 90), (cx + 140, tt + 68),
                             (int(W * 0.685), H - 128), (int(W * 0.79), H - 100)])
        wx0, wy0 = int(W * 0.70), H - 118
        pygame.draw.ellipse(surf, (158, 138, 114), (wx0 - 12, wy0 - 6, 76, 44))
        pygame.draw.ellipse(surf, (104, 88, 70), (wx0 - 12, wy0 - 6, 76, 44), 3)
        for fk in range(4):                                          # fingers curled, not closed
            fx4 = wx0 + 4 + fk * 15
            pygame.draw.line(surf, (158, 138, 114), (fx4, wy0 + 18),
                             (fx4 + 3, wy0 + 44), 10)
            pygame.draw.circle(surf, (170, 150, 124), (fx4, wy0 + 17), 6)
        pygame.draw.line(surf, (206, 196, 182), (wx0, wy0 + 2), (wx0 + 50, wy0 - 2), 2)

    # -- the dark presses in: the heaviest vignette of any close-up --
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = cx, cy + 40
    maxr = int(math.hypot(W, H) * 0.62); inner = int(maxr * 0.42)
    for r in range(maxr, inner, -8):
        a = max(0, int(210 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- THE PEDESTAL: the Sign Chamber altar, made a close-up ----
# The one place the Pallid Mask is lifted, and the one place BREAK is chosen.
# Not a person -- an OBJECT close-up, but the object is His face: the whole
# machine of it here in reach. The Mask rests on the hewn stone ("pale as a
# drowned face, the eyeholes black") and warm (a gold ember far down in each
# socket, because it knows your hands); the daubed Yellow Sign (its own 2D
# brand) breathes on the apse wall above; the kneeling congregation is at
# your back in the cult-dark, two candles the only light. The lift/tear
# choice rides on top as the tableau menu.
def _sign_daub(surf, cx, cy, R, t):
    """The Yellow Sign -- His face daubed in paint (NARRATIVE 6a): the crude
    mask the cult paints, a broken jaundiced oval outline with two off-centre
    thumb-press sockets and NO mouth, paint runs off the chin. Matches the
    canonical wall daub (entities/deco_horror _draw_yellow_sign), scaled up on
    the apse wall and breathing."""
    import pygame
    rng = random.Random(3)
    pulse = 1.0 + math.sin(t * 0.9) * 0.06
    col = (176, 158, 60); dark = (86, 74, 26); sock = (5, 4, 3)
    rx, ry = R * 0.72 * pulse, R * 1.04 * pulse
    n = 22
    pts = [(cx + math.cos(i / n * math.tau) * (rx + rng.uniform(-5, 5)),
            cy + math.sin(i / n * math.tau) * (ry + rng.uniform(-5, 5)))
           for i in range(n)]
    for i in range(n):                                          # broken outline
        if rng.random() < 0.80:
            a, b = pts[i], pts[(i + 1) % n]
            pygame.draw.line(surf, dark, a, b, 8)
            pygame.draw.line(surf, col, a, b, 4)
    for fx, fy, fr in ((-0.40, -0.25, 0.22), (0.43, -0.18, 0.25)):  # sockets, no mouth
        sxp, syp = int(cx + rx * fx), int(cy + ry * fy)
        pygame.draw.circle(surf, sock, (sxp, syp), max(3, int(R * fr)))
    for dx, fl in ((-R * 0.2, 1.0), (R * 0.12, 0.7)):           # paint runs off the chin
        rl = int(R * 0.7 * fl * (1.0 + 0.25 * math.sin(t * 0.13)))
        x0 = int(cx + dx); y0 = int(cy + ry * 0.9)
        pygame.draw.line(surf, dark, (x0, y0), (x0, y0 + rl), 4)
        pygame.draw.line(surf, col, (x0, y0), (x0, y0 + rl), 2)


def _pallid_mask(surf, cx, cy, r, ember, tilt=0.0):
    """The Pallid Mask resting on the stone: a pale half-face, drowned-white,
    the eyeholes carved black with a gold ember far down in them. A vertical
    seam down the centre (His half-mask). Warm underglow. `ember` 0..1 pulses
    the gold; `tilt` leans it up toward the viewer."""
    import pygame
    pale = (224, 226, 228); pale_hi = (244, 245, 246); pale_lo = (150, 156, 162)
    seam = (120, 126, 134)
    S = int(r * 3)
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = S // 2
    # warm halo behind (it is warm, it knows your hands)
    for rr in range(int(r * 1.5), 0, -3):
        a = int(30 * (1 - rr / (r * 1.5)) * (0.6 + 0.4 * ember))
        pygame.draw.circle(m, (210, 150, 70, a), (mx, my), rr)
    # the pale plate: a tall drowned-face oval, upper face fuller than the jaw
    face = []
    rng = random.Random(7)
    for k in range(20):
        a = -math.pi / 2 + k * (math.pi * 2 / 20)
        rx = r * (0.82 + 0.05 * rng.random())
        ry = r * (1.02 + (0.10 if math.sin(a) > 0 else 0.0) + 0.04 * rng.random())
        face.append((mx + int(math.cos(a) * rx), my + int(math.sin(a) * ry)))
    pygame.draw.polygon(m, pale, face)
    pygame.draw.polygon(m, pale_lo, face, 2)
    # left side lit, right side falls to shadow (the candles are low-left)
    sh = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (54, 58, 66, 70), (mx + int(r * 0.35), my - r, int(r * 0.8), r * 2))
    m.blit(sh, (0, 0))
    hi = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.ellipse(hi, (*pale_hi, 150), (mx - r + 4, my - int(r * 0.7),
                                              int(r * 0.8), int(r * 1.4)))
    m.blit(hi, (0, 0))
    # the vertical seam of the half-mask
    pygame.draw.line(m, seam, (mx, my - int(r * 0.96)), (mx, my + int(r * 0.98)), 2)
    # the brow ridge + the long nose
    pygame.draw.arc(m, pale_lo, (mx - int(r * 0.6), my - int(r * 0.5),
                                 int(r * 1.2), int(r * 0.5)), 3.4, 6.0, 2)
    pygame.draw.line(m, pale_lo, (mx, my - int(r * 0.2)), (mx - 2, my + int(r * 0.4)), 2)
    pygame.draw.line(m, pale_hi, (mx - 3, my - int(r * 0.2)), (mx - 5, my + int(r * 0.34)), 1)
    # the carved black eye-voids + the gold ember far down
    for sgn in (-1, 1):
        ex = mx + sgn * int(r * 0.4)
        ey = my - int(r * 0.14)
        pygame.draw.ellipse(m, (150, 154, 160), (ex - int(r * 0.24), ey - int(r * 0.17),
                                                 int(r * 0.48), int(r * 0.34)))  # carved rim
        pygame.draw.ellipse(m, (6, 6, 9), (ex - int(r * 0.19), ey - int(r * 0.13),
                                           int(r * 0.38), int(r * 0.28)))        # the void
        g = pygame.Surface((int(r * 0.5), int(r * 0.5)), pygame.SRCALPHA)
        gr = g.get_width() // 2
        pygame.draw.circle(g, (235, 190, 70, int(90 * (0.4 + 0.6 * ember))),
                           (gr, gr + int(r * 0.06)), max(2, int(r * 0.11)))
        m.blit(g, (ex - gr, ey - gr), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.circle(m, (150, 120, 50), (ex, ey + int(r * 0.07)), max(1, int(r * 0.05)))
    # the closed, lipless mouth-line low on the plate (a half-mask barely has one)
    pygame.draw.line(m, pale_lo, (mx - int(r * 0.24), my + int(r * 0.6)),
                     (mx + int(r * 0.24), my + int(r * 0.6)), 2)
    if tilt:
        m = pygame.transform.rotate(m, tilt)
    surf.blit(m, m.get_rect(center=(int(cx), int(cy))))


def draw_altar_tableau(surf, t, state):
    """The Sign Chamber altar close-up: the Pallid Mask on the hewn stone
    under the daubed Sign, the kneeling congregation behind, two low candles
    the only light. His face pulses warm. The lift/tear choice rides on top
    as the tableau menu."""
    import pygame
    W, H = surf.get_width(), surf.get_height()

    # -- the cult-dark: near-black, cold stone above, the apse curve behind --
    top = (18, 17, 21); bot = (6, 6, 8)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    for i in range(6):                                              # stone seams
        yy = int(H * (0.10 + 0.085 * i))
        pygame.draw.line(surf, (26, 24, 29), (0, yy), (W, yy + 3), 1)

    # -- the kneeling congregation at your back: dark humps in rows, unmoving --
    rnd = random.Random(19)
    for row, (ry, rs, n) in enumerate([(0.30, 0.7, 7), (0.37, 0.85, 6),
                                       (0.45, 1.0, 5)]):
        yy = int(H * ry)
        for k in range(n):
            fx = int(W * (0.12 + (0.76 * (k + 0.5) / n)) + rnd.randint(-10, 10))
            hump = int(46 * rs)
            col = _lerp((14, 13, 16), (30, 27, 32), row / 2)
            pygame.draw.ellipse(surf, col, (fx - int(20 * rs), yy - hump,
                                            int(40 * rs), hump + int(20 * rs)))
            pygame.draw.circle(surf, col, (fx, yy - hump + int(8 * rs)), int(11 * rs))

    # -- the daubed Yellow Sign, breathing on the apse wall above the altar --
    sgy = int(H * 0.235)
    breath = 0.5 + 0.5 * math.sin(t * 0.7)
    glow = pygame.Surface((W, H), pygame.SRCALPHA)                   # sickly light pool
    for r in range(150, 0, -6):
        a = int(30 * (1 - r / 150) * (0.7 + 0.3 * breath))
        pygame.draw.circle(glow, (196, 176, 70, a), (W // 2, sgy), r)
    surf.blit(glow, (0, 0))
    _sign_daub(surf, W // 2, sgy, 96, t)

    # -- the altar: a hewn stone block, wax-run, two guttering candles --
    axc, ayt = W // 2, int(H * 0.64)
    pygame.draw.polygon(surf, (34, 31, 27),                          # the block top
                        [(axc - 150, ayt), (axc + 150, ayt),
                         (axc + 178, ayt + 40), (axc - 178, ayt + 40)])
    pygame.draw.polygon(surf, (24, 22, 19),                          # the front face
                        [(axc - 178, ayt + 40), (axc + 178, ayt + 40),
                         (axc + 200, H), (axc - 200, H)])
    pygame.draw.line(surf, (52, 47, 40), (axc - 150, ayt), (axc + 150, ayt), 2)
    for gx in range(axc - 150, axc + 160, 60):                       # chisel seams
        pygame.draw.line(surf, (18, 16, 14), (gx, ayt + 42), (gx - 8, H), 1)
    # wax runs down the front
    for wx in (axc - 96, axc + 70, axc + 120):
        pygame.draw.line(surf, (60, 56, 46), (wx, ayt + 40), (wx + 3, ayt + 120), 3)
    # two low candles flanking the mask, the only light
    flames = []
    for dx in (-118, 118):
        chx, chy = axc + dx, ayt + 6
        pygame.draw.rect(surf, (150, 142, 120), (chx - 4, chy - 30, 8, 30))
        pygame.draw.ellipse(surf, (44, 40, 33), (chx - 8, chy + 26, 16, 8))
        fl = 1.0 + 0.28 * math.sin(t * 7.3 + dx) * math.sin(t * 2.1)
        pygame.draw.ellipse(surf, (255, 214, 120),
                            (chx - 4, chy - 30 - int(15 * fl), 8, int(15 * fl)))
        pygame.draw.ellipse(surf, (255, 246, 206),
                            (chx - 2, chy - 30 - int(9 * fl), 4, int(9 * fl)))
        flames.append((chx, chy - 34))
    # the candle wash pooling up onto the mask
    wash = pygame.Surface((W, H), pygame.SRCALPHA)
    fl0 = 0.9 + 0.1 * math.sin(t * 5.1) * math.sin(t * 1.7)
    for r in range(int(H * 0.5), 0, -10):
        a = int(84 * (1 - r / (H * 0.5)) * fl0)
        pygame.draw.circle(wash, (255, 196, 108, a), (axc, ayt - 20), r)
    surf.blit(wash, (0, 0))

    # -- the socket the mask sits in, and the Mask itself, warm and gazing --
    pygame.draw.ellipse(surf, (8, 8, 11), (axc - 64, ayt - 18, 128, 46))
    ember = 0.5 + 0.5 * (0.5 + 0.5 * math.sin(t * 1.15))
    key = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(160, 0, -8):
        a = int(46 * (1 - r / 160) * fl0)
        pygame.draw.circle(key, (240, 210, 150, a), (axc, ayt - 44), r)
    surf.blit(key, (0, 0))
    bob = 1.0 * math.sin(t * 0.8)
    _pallid_mask(surf, axc, ayt - 52 + bob, 68, ember, tilt=0.0)

    # motes drifting up through the candlelight
    rnd2 = random.Random(11)
    for _ in range(30):
        base = rnd2.randint(0, 600)
        yy = int(H * 0.30 + (t * 6 + base) % (H * 0.5))
        mx = axc + int(120 * math.sin(t * 0.4 + base)) + rnd2.randint(-30, 30)
        pygame.draw.circle(surf, (230, 200, 150), (mx, yy), 1)

    # -- the heaviest vignette; the dark leans in on the one lit thing --
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = axc, ayt - 30
    maxr = int(math.hypot(W, H) * 0.60); inner = int(maxr * 0.40)
    for r in range(maxr, inner, -8):
        a = max(0, int(205 * (1 - (r - inner) / (maxr - inner))))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


# ---- MARA: the confrontation, the last seat -- and the REVEAL ----
# Every other seat opens on a face. This one opens on a HOOD: she stands out
# of the rank one more carved mask among the congregation (the Talk's grammar,
# slighter -- and NEW wood, the last one in, no graft), the rite still running
# at her back (the Sign's daub-strokes on the apse wall, the altar candles,
# the kneeling rank, the rite-holder who never pauses). Then she lifts the
# mask away, and the face from the photograph is under it, gone thin. Her
# hands are the dig's ledger: raw knuckles, dark nailbeds, bleeding palms.
def _mara_ease(u):
    return u * u * (3 - 2 * u)


def _draw_mara_face(surf, hx, hy, t, turn, lucid, named):
    """The face under the mask: hers. Young and gone thin -- hollowed
    cheeks, dark-ringed eyes (sad around them, like Hettie said), cracked
    lips, dirt along the jaw, matted hair pressed flat under the hood.
    `turn` shifts the features (the glance back toward the rite)."""
    import pygame
    skin = (174, 162, 148); sk_hi = (200, 190, 176); sk_lo = (124, 114, 102)
    sk_sh = (90, 84, 76)
    fx = hx + int(turn)
    # the face plate inside the hood: a narrow oval, jaw drawn to a point
    pygame.draw.ellipse(surf, skin, (hx - 64, hy - 84, 128, 158))
    pygame.draw.polygon(surf, skin, [(hx - 42, hy + 50), (hx + 42, hy + 50),
                                     (fx + 12, hy + 92), (fx - 12, hy + 92)])
    # the shadow side (the candles are behind her; the chamber's spill is
    # what lights her) + a pale key from high front
    sh = pygame.Surface((160, 200), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*sk_sh, 46), (0, 20, 56 - int(turn * 0.5), 160))
    pygame.draw.ellipse(sh, (*sk_sh, 46), (0, 34, 40 - int(turn * 0.5), 130))
    surf.blit(sh, (hx - 64, hy - 84))
    hi = pygame.Surface((160, 200), pygame.SRCALPHA)
    pygame.draw.ellipse(hi, (206, 192, 172, 40), (76, 22, 60, 116))
    pygame.draw.ellipse(hi, (206, 192, 172, 40), (86, 34, 42, 92))
    surf.blit(hi, (hx - 64, hy - 84))
    # cheeks hollowed, softly (a winter underground)
    pygame.draw.arc(surf, sk_lo, (fx - 46, hy + 2, 22, 38), 0.7, 2.1, 2)
    pygame.draw.arc(surf, sk_lo, (fx + 24, hy + 2, 22, 38), 1.0, 2.4, 2)
    # matted hair: a pressed-flat mass filling the crown, uneven hairline,
    # side falls tucked into the hood
    hair = (58, 46, 38); hair_lo = (40, 32, 27)
    pygame.draw.polygon(surf, hair, [
        (hx - 62, hy - 40), (hx - 58, hy - 74), (hx - 34, hy - 88),
        (hx + 2, hy - 92), (hx + 38, hy - 86), (hx + 58, hy - 70),
        (hx + 62, hy - 38), (hx + 52, hy - 52), (hx + 30, hy - 62),
        (fx + 12, hy - 56), (fx - 8, hy - 60), (hx - 30, hy - 64),
        (hx - 50, hy - 54)])
    rnd = random.Random(23)
    for k in range(7):                                   # comb of strands
        sx0 = hx - 44 + k * 15 + rnd.randint(-2, 2)
        pygame.draw.arc(surf, hair_lo,
                        (sx0, hy - 84 + rnd.randint(0, 6), 16, 30), 1.0, 2.4, 2)
    pygame.draw.polygon(surf, hair, [(hx - 64, hy - 44), (hx - 52, hy - 56),
                                     (hx - 46, hy + 26), (hx - 60, hy + 20)])
    pygame.draw.polygon(surf, hair, [(hx + 64, hy - 44), (hx + 52, hy - 56),
                                     (hx + 46, hy + 26), (hx + 60, hy + 20)])
    # one loose strand stuck at the brow
    pygame.draw.arc(surf, hair_lo, (fx - 22, hy - 58, 36, 26), 3.7, 5.1, 2)
    # the eyes: large, dark-ringed. Certainty is a calm, steady rest;
    # lucid opens them wide and drops them to her hands; named tears them
    # wider still, brows driven in.
    blink = 1.0
    ph = t % 4.7
    if 4.55 <= ph < 4.7 and not (lucid or named):
        blink = max(0.15, abs((ph - 4.625) / 0.075))
    ring = (106, 94, 92)
    look_dn = 7 if lucid else 0
    look_sd = int(turn * 0.6)
    for sgn in (-1, 1):
        ex = fx + sgn * 26
        ey = hy - 18
        pygame.draw.ellipse(surf, ring, (ex - 15, ey - 10, 30, 25))     # the dark ring
        pygame.draw.ellipse(surf, sk_lo, (ex - 14, ey - 8, 28, 19))
        eh = int((15 if (lucid or named) else 11) * blink)
        pygame.draw.ellipse(surf, (192, 188, 180),
                            (ex - 11, ey - eh // 2, 22, max(2, eh)))    # the white
        if blink > 0.3:
            pygame.draw.circle(surf, (66, 52, 44),
                               (ex + look_sd, ey + look_dn // 2), 5)
            pygame.draw.circle(surf, (24, 18, 16),
                               (ex + look_sd, ey + look_dn // 2), 3)
            pygame.draw.circle(surf, (222, 218, 210),
                               (ex + look_sd - 2, ey + look_dn // 2 - 2), 1)
        # lower-lid shadow: the long hunger
        pygame.draw.arc(surf, ring, (ex - 12, ey + 3, 24, 15), 3.5, 6.0, 2)
    # brows: soft, inner ends lifted (sad around the eyes); named drives
    # them in hard, lucid raises them
    for sgn in (-1, 1):
        bx = fx + sgn * 26
        by = hy - 36
        if named:
            pygame.draw.line(surf, (70, 58, 50), (bx - sgn * 14, by + 5),
                             (bx + sgn * 12, by - 3), 4)
        elif lucid:
            pygame.draw.line(surf, (70, 58, 50), (bx - sgn * 14, by - 5),
                             (bx + sgn * 12, by - 1), 4)
        else:
            pygame.draw.line(surf, (70, 58, 50), (bx - sgn * 14, by - 1),
                             (bx + sgn * 12, by + 1), 3)
    # the nose: thin, a shadow line
    pygame.draw.line(surf, sk_lo, (fx + 1, hy - 12), (fx - 1, hy + 16), 3)
    pygame.draw.ellipse(surf, sk_lo, (fx - 5, hy + 13, 10, 6))
    # the mouth: pale, cracked. Calm-set at rest; parted at lucid; pulled
    # open at named.
    my = hy + 38
    lip = (132, 94, 90)
    if named:
        pygame.draw.ellipse(surf, (54, 38, 36), (fx - 11, my - 4, 22, 12))
        pygame.draw.line(surf, lip, (fx - 14, my - 3), (fx + 14, my - 3), 2)
    elif lucid:
        pygame.draw.ellipse(surf, (60, 44, 42), (fx - 8, my - 3, 16, 9))
        pygame.draw.line(surf, lip, (fx - 11, my - 3), (fx + 11, my - 3), 2)
    else:
        pygame.draw.line(surf, lip, (fx - 12, my), (fx + 12, my), 3)
        pygame.draw.line(surf, sk_lo, (fx - 15, my + 1), (fx - 11, my), 1)
        pygame.draw.line(surf, sk_lo, (fx + 11, my), (fx + 15, my + 1), 1)
    for k in range(2):                                                # cracked lips
        pygame.draw.line(surf, sk_lo, (fx - 6 + k * 9, my - 3),
                         (fx - 6 + k * 9, my + 3), 1)
    # dirt: smudges along the jaw and one streak at the temple
    dirt = (100, 86, 68)
    pygame.draw.arc(surf, dirt, (fx - 34, hy + 48, 26, 16), 3.6, 5.4, 2)
    pygame.draw.arc(surf, dirt, (fx + 10, hy + 54, 24, 14), 3.8, 5.6, 2)
    pygame.draw.line(surf, dirt, (hx + 44, hy - 30), (hx + 48, hy - 8), 2)


def _mara_carved_mask(surf, mx, my, tilt_deg, embers, t):
    """Her carved mask: the congregation's grammar (a hewn oval, recessed
    void sockets, no mouth) but NEW wood -- the last one in, the cleanest
    cuts, no graft. `embers` 0..1: the gold far down in the sockets (it
    dies as the wood comes off the face)."""
    import pygame
    S = 240
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    cx = cy = S // 2
    mw, mh = 78, 102
    rnd = random.Random(31)
    pts = []
    for k in range(14):
        a = -math.pi / 2 + k * (math.pi * 2 / 14)
        jr = 1.0 + rnd.uniform(-0.05, 0.05)
        pts.append((cx + int(math.cos(a) * mw * jr),
                    cy + int(math.sin(a) * mh * jr)))
    pygame.draw.polygon(m, (172, 150, 114), pts)
    pygame.draw.polygon(m, (112, 94, 68), pts, 4)
    # fine straight grain: new wood, cleanly worked
    for gx in range(-40, 44, 11):
        pygame.draw.arc(m, (146, 124, 90),
                        (cx + gx - 7, cy - mh + 14, 20, mh * 2 - 28), 1.3, 1.9, 1)
    pygame.draw.line(m, (152, 130, 96), (cx - mw + 14, cy - 52), (cx - 9, cy - 72), 3)
    pygame.draw.line(m, (152, 130, 96), (cx + 12, cy - 74), (cx + mw - 14, cy - 50), 3)
    pygame.draw.line(m, (152, 130, 96), (cx - mw + 12, cy + 40), (cx - 8, cy + 62), 3)
    # the carved void sockets, hand-cut a little unlevel
    for sgn, ph in ((-1, 0.0), (1, 1.6)):
        ex = cx + sgn * 29
        ey = cy - 12 + (4 if sgn > 0 else 0)
        pygame.draw.ellipse(m, (122, 102, 74), (ex - 21, ey - 18, 42, 38))
        pygame.draw.ellipse(m, (36, 30, 24), (ex - 17, ey - 13, 34, 31))
        pygame.draw.ellipse(m, (6, 5, 7), (ex - 13, ey - 8, 26, 24))
        if embers > 0.02:
            glow = (0.5 + 0.5 * math.sin(t * 1.1 + ph)) * embers
            g = pygame.Surface((26, 24), pygame.SRCALPHA)
            pygame.draw.circle(g, (230, 186, 48, int(34 * glow)), (13, 16), 9)
            m.blit(g, (ex - 13, ey - 8), special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.circle(m, (150, 120, 50), (ex, ey + 8), 2)
            if glow > 0.4:
                pygame.draw.circle(m, (255, 218, 96), (ex - 1, ey + 7), 1)
    # no mouth. the wood does not move.
    if tilt_deg:
        m = pygame.transform.rotate(m, tilt_deg)
    surf.blit(m, m.get_rect(center=(int(mx), int(my))))


def _mara_dig_hand(surf, x, y, ang_deg, scale=1.0, palm=False, mirror=False):
    """A dig-ruined hand: thin, knuckles raw, nailbeds dark, dirt in the
    creases. Drawn fingers-up at `ang_deg` 0; rotate for grips."""
    import pygame
    S = 130
    h = pygame.Surface((S, S), pygame.SRCALPHA)
    hx, hy = S // 2, S // 2 + 16
    skin = (162, 152, 140); lo = (114, 104, 94)
    raw = (126, 64, 54); nail = (66, 40, 34); dirt = (76, 66, 55)
    pygame.draw.ellipse(h, skin, (hx - 24, hy - 14, 48, 40))          # the back
    pygame.draw.ellipse(h, lo, (hx - 24, hy - 14, 48, 40), 2)
    for fk in range(4):                                               # fingers, closed rank
        fx = hx - 15 + fk * 10
        fl = 32 + (3 if fk in (1, 2) else -2)
        pygame.draw.line(h, skin, (fx, hy - 9), (fx + 1, hy - 9 - fl), 10)
        if not palm:
            pygame.draw.line(h, lo, (fx + 4, hy - 12), (fx + 5, hy - 6 - fl), 1)
            pygame.draw.circle(h, raw, (fx, hy - 9 - fl + 5), 2)      # raw knuckle
            pygame.draw.line(h, nail, (fx, hy - 9 - fl), (fx + 2, hy - 9 - fl), 2)
    pygame.draw.line(h, skin, (hx - 24, hy + 4), (hx - 33, hy + 18),
                     7 if palm else 10)                               # thumb
    if palm:
        # the dig, written on the palm: creases picked out in dirt, the
        # fingers parted by faint seams, the heel scraped raw
        for fk in range(3):
            fxs = hx - 10 + fk * 10
            pygame.draw.line(h, lo, (fxs, hy - 12), (fxs + 1, hy - 34), 1)
        pygame.draw.arc(h, dirt, (hx - 16, hy - 8, 32, 22), 3.4, 5.9, 2)
        pygame.draw.arc(h, dirt, (hx - 14, hy - 2, 26, 18), 3.5, 5.7, 1)
        pygame.draw.ellipse(h, (110, 52, 44), (hx - 5, hy + 9, 13, 8))
    else:
        pygame.draw.circle(h, raw, (hx - 32, hy + 15), 2)
        pygame.draw.line(h, dirt, (hx - 14, hy + 10), (hx + 12, hy + 12), 2)
    if mirror:
        h = pygame.transform.flip(h, True, False)
    if scale != 1.0:
        n = int(S * scale)
        h = pygame.transform.smoothscale(h, (n, n))
    if ang_deg:
        h = pygame.transform.rotate(h, ang_deg)
    surf.blit(h, h.get_rect(center=(int(x), int(y))))


def draw_mara_tableau(surf, t, state):
    import pygame
    W, H = surf.get_width(), surf.get_height()
    u = _mara_ease(max(0.0, min(1.0, state.get("unmask", 0.0))))
    glance = state.get("glance", 0.0)
    lucid = state.get("lucid", False)
    named = state.get("named", False)

    # -- the nave, cult-dark --
    top = (20, 19, 23); bot = (7, 7, 9)
    for y in range(0, H, 2):
        surf.fill(_lerp(top, bot, y / H), (0, y, W, 2))
    for i in range(5):                                               # stone seams
        yy = int(H * (0.06 + 0.07 * i))
        pygame.draw.line(surf, (30, 28, 33), (0, yy), (W, yy + 2), 1)

    # -- the rite at her back: the Sign, the altar, the rite-holder --
    sgx, sgy = int(W * 0.40), int(H * 0.015)
    breath = 0.5 + 0.5 * math.sin(t * 0.7)
    glow = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(150, 0, -6):
        a = int(26 * (1 - r / 150) * (0.7 + 0.3 * breath))
        pygame.draw.circle(glow, (196, 176, 70, a), (sgx, sgy), r)
    surf.blit(glow, (0, 0))
    _mara_sign_far(surf, sgx, sgy, 95, t)
    # the altar: a low dark block under the Sign, two candle points
    ax0, ay0 = sgx, int(H * 0.235)
    pygame.draw.polygon(surf, (38, 34, 30), [(ax0 - 80, ay0), (ax0 + 80, ay0),
                                             (ax0 + 96, ay0 + 24), (ax0 - 96, ay0 + 24)])
    for dx in (-62, 62):
        fl = 1.0 + 0.3 * math.sin(t * 7.1 + dx) * math.sin(t * 2.3)
        pygame.draw.rect(surf, (130, 122, 104), (ax0 + dx - 2, ay0 - 13, 4, 13))
        pygame.draw.ellipse(surf, (255, 214, 120),
                            (ax0 + dx - 3, ay0 - 13 - int(9 * fl), 6, int(9 * fl)))
        cg = pygame.Surface((160, 130), pygame.SRCALPHA)
        for r in range(64, 0, -6):
            k = 0.16 * (1 - r / 64)
            pygame.draw.circle(cg, (int(255 * k), int(196 * k), int(108 * k), 255),
                               (80, 65), r)
        surf.blit(cg, (ax0 + dx - 80, ay0 - 78), special_flags=pygame.BLEND_RGB_ADD)
    # the rite-holder, bowed at the altar's foot: the one that never pauses
    pygame.draw.ellipse(surf, (30, 26, 30), (ax0 - 22, ay0 + 20, 44, 32))
    pygame.draw.circle(surf, (38, 33, 37), (ax0, ay0 + 24), 11)

    # -- the kneeling rank, seen from behind, backlit --
    stir = 1.0 if named else 0.0
    rnd = random.Random(41)
    for row, (ry, rs, xs) in enumerate([(0.37, 0.66, (-3, -2, -1, 1, 2, 3)),
                                        (0.47, 0.92, (-3, -2, 2, 3))]):
        yy = int(H * ry)
        for k in xs:
            fx2 = int(W * 0.5 + k * W * 0.09 * (1 + row * 0.4)) + rnd.randint(-6, 6)
            hump = int(56 * rs)
            col = _lerp((22, 20, 24), (42, 37, 40), row)
            lift = int(stir * (7 + (abs(k) % 3) * 4) * rs)
            pygame.draw.ellipse(surf, col, (fx2 - int(26 * rs), yy - hump - lift,
                                            int(52 * rs), hump + int(26 * rs)))
            hdx = int(stir * (4 if k > 0 else -4))
            pygame.draw.circle(surf, col, (fx2 + hdx, yy - hump - lift + int(7 * rs)),
                               int(14 * rs))
            pygame.draw.arc(surf, _lerp((52, 44, 32), (72, 60, 42), row),
                            (fx2 - int(14 * rs) + hdx, yy - hump - lift - int(7 * rs),
                             int(28 * rs), int(28 * rs)),
                            0.9, 2.2, 2)                              # candle rim on the hood

    # -- HER: the hood, the coat, the mask that comes away --
    cx = int(W * 0.5)
    cy = int(H * 0.40) + int(2 * math.sin(t * 0.8))
    lean = int(6 * (1.0 if named else 0.0))
    cy += lean
    hood_r = 126
    tt = cy + int(hood_r * 0.62)

    # the hide coat: slighter than the Talk's mass; her shoulders slope
    pygame.draw.polygon(surf, (58, 45, 32), [(cx - 200, tt + 82), (cx - 102, tt + 28),
                                             (cx + 102, tt + 28), (cx + 200, tt + 82),
                                             (cx + 262, H), (cx - 262, H)])
    pygame.draw.polygon(surf, (44, 36, 30), [(cx + 8, tt + 32), (cx + 102, tt + 28),
                                             (cx + 200, tt + 82), (cx + 262, H),
                                             (cx + 22, H)])
    pygame.draw.polygon(surf, (68, 53, 38), [(cx - 200, tt + 82), (cx - 102, tt + 28),
                                             (cx - 64, tt + 48), (cx - 138, H),
                                             (cx - 262, H)])
    for i in range(6):                                               # bone-thread seam
        sy0 = tt + 68 + i * 44
        pygame.draw.line(surf, (150, 138, 112), (cx - 2, sy0), (cx + 2, sy0 + 8), 3)
    for k in range(2):                                               # patch seams
        for j in range(3):
            sy0 = tt + 100 + k * 88 + j * 13
            pygame.draw.line(surf, (150, 138, 112), (cx - 102 + k * 7, sy0),
                             (cx - 94 + k * 7, sy0 + 8), 2)
    # fur collar
    for fx3 in range(cx - 110, cx + 112, 9):
        fh = 12 + (fx3 % 13)
        pygame.draw.line(surf, (112, 93, 64), (fx3, tt + 38), (fx3 + 2, tt + 38 - fh), 3)

    # the deep fur hood
    pygame.draw.ellipse(surf, (74, 61, 42), (cx - hood_r, cy - hood_r - 10,
                                             hood_r * 2, hood_r * 2 + 36))
    pygame.draw.ellipse(surf, (52, 42, 30), (cx - hood_r + 12, cy - hood_r + 2,
                                             hood_r * 2 - 24, hood_r * 2 + 12))
    rnd2 = random.Random(7)
    for _ in range(140):                                             # fur ticks, short on top
        a2 = rnd2.uniform(0, math.pi * 2)
        rr = hood_r - rnd2.randint(0, 10)
        fx4 = cx + int(math.cos(a2) * rr)
        fy = cy + 6 + int(math.sin(a2) * (rr * 0.94))
        ln = rnd2.randint(5, 11)
        if math.sin(a2) < -0.3:
            ln = max(3, ln - 5)
        pygame.draw.line(surf, (112, 93, 64), (fx4, fy),
                         (fx4 + int(math.cos(a2) * ln), fy + int(math.sin(a2) * ln)), 1)
    # the opening: near-black, the face's frame
    pygame.draw.ellipse(surf, (14, 12, 11), (cx - hood_r + 32, cy - hood_r + 24,
                                             hood_r * 2 - 64, hood_r * 2 - 30))

    # the face (revealed behind the lifting wood)
    turn = -18 * glance
    if u > 0.10:
        _draw_mara_face(surf, cx, cy - 4, t, turn, lucid, named)

    # the mask: worn -> pulled down off the face (her eyes come free
    # first) -> carried out of the frame in her hand
    if u < 0.55:
        ph1 = u / 0.55
        mmx = cx + int(8 * ph1)
        mmy = cy - 4 + int(88 * _mara_ease(ph1))
        tilt = -13 * ph1
        embers = max(0.0, 1.0 - ph1 * 1.7)
        _mara_carved_mask(surf, mmx, mmy, tilt, embers, t)
        if u > 0.03:                                                 # her hands on its edges
            grip = _mara_ease(min(1.0, u / 0.16))
            _mara_dig_hand(surf, mmx - 64, mmy + 44 + int(20 * (1 - grip)), -28, 1.05)
            _mara_dig_hand(surf, mmx + 64, mmy + 48 + int(20 * (1 - grip)), 28, 1.05,
                      mirror=True)
    elif u < 1.0:
        ph2 = (u - 0.55) / 0.45
        mmx = cx + int(8 + 250 * _mara_ease(ph2))
        mmy = (cy + 84) + int((H + 130 - (cy + 84)) * _mara_ease(ph2))
        tilt = -13 - 48 * ph2
        _mara_carved_mask(surf, mmx, mmy, tilt, 0.0, t)
        _mara_dig_hand(surf, mmx - 50, mmy + 12, -84 + int(26 * ph2), 1.1)

    # lucid: both hands come up to her chest, palm-up, and she looks down
    # at them ("My hands. Look at my hands.")
    if lucid and u >= 1.0:
        tr = int(1.5 * math.sin(t * 13.0))
        hy0 = cy + 168
        for sgn in (-1, 1):                              # hide sleeves under them
            pygame.draw.polygon(surf, (66, 52, 37),
                                [(cx + sgn * 170, H), (cx + sgn * 180, H - 60),
                                 (cx + sgn * 68, hy0 + 26), (cx + sgn * 26, hy0 + 70),
                                 (cx + sgn * 60, H)])
            pygame.draw.line(surf, (108, 90, 62),
                             (cx + sgn * 68, hy0 + 28), (cx + sgn * 40, hy0 + 62), 4)
        _mara_dig_hand(surf, cx - 70, hy0 + tr, 168, 1.5, palm=True)
        _mara_dig_hand(surf, cx + 70, hy0 + 6 - tr, -168, 1.5, palm=True, mirror=True)

    # named: her fist closes on YOUR coat at the frame's corner
    if named:
        pygame.draw.polygon(surf, (44, 42, 46), [(0, H - 160), (int(W * 0.31), H - 100),
                                                 (int(W * 0.35), H), (0, H)])
        pygame.draw.line(surf, (86, 82, 88), (0, H - 156), (int(W * 0.30), H - 98), 5)
        pygame.draw.line(surf, (28, 26, 28), (0, H - 146), (int(W * 0.29), H - 88), 2)
        # her thin arm, hide-sleeved, from the coat mass to your lapel
        pygame.draw.polygon(surf, (78, 61, 43),
                            [(cx - 176, tt + 110), (cx - 76, tt + 48),
                             (int(W * 0.25), H - 142), (int(W * 0.155), H - 64)])
        pygame.draw.polygon(surf, (52, 42, 31),
                            [(cx - 176, tt + 110), (cx - 136, tt + 80),
                             (int(W * 0.20), H - 92), (int(W * 0.155), H - 64)])
        pygame.draw.line(surf, (150, 138, 112),                      # a seam catches light
                         (cx - 110, tt + 72), (int(W * 0.23), H - 122), 2)
        for fr in range(3):                                          # fur cuff at the wrist
            pygame.draw.line(surf, (108, 90, 62),
                             (int(W * 0.225) - fr * 9, H - 138 + fr * 8),
                             (int(W * 0.245) - fr * 9, H - 152 + fr * 8), 3)
        fx5, fy5 = int(W * 0.205), H - 118
        # the fold of your coat she has pulled up in her fist
        pygame.draw.polygon(surf, (58, 55, 60), [(fx5 - 12, fy5 + 36), (fx5 + 5, fy5 - 22),
                                                 (fx5 + 24, fy5 + 34)])
        pygame.draw.ellipse(surf, (166, 154, 140), (fx5 - 26, fy5 - 17, 60, 40))
        pygame.draw.ellipse(surf, (116, 106, 94), (fx5 - 26, fy5 - 17, 60, 40), 2)
        for fk in range(4):                                          # fingers wrap the fold
            kx = fx5 - 14 + fk * 13
            pygame.draw.line(surf, (166, 154, 140), (kx, fy5 + 3),
                             (kx - 3, fy5 + 32), 11)
            pygame.draw.circle(surf, (198, 188, 172), (kx, fy5 + 3), 6)  # knuckles, white
            pygame.draw.circle(surf, (128, 66, 54), (kx, fy5 + 3), 2)
        pygame.draw.line(surf, (206, 196, 182), (fx5 - 22, fy5 - 12),
                         (fx5 + 28, fy5 - 15), 2)

    # -- the dark leans in --
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    vcx, vcy = cx, cy + 30
    maxr = int(math.hypot(W, H) * 0.62); inner = int(maxr * 0.34)
    for r in range(maxr, inner, -8):
        a = min(235, int(235 * (r - inner) / (maxr - inner)))
        pygame.draw.circle(vig, (0, 0, 0, a), (vcx, vcy), r)
    surf.blit(vig, (0, 0))


def _mara_sign_far(surf, cx, cy, R, t):
    """The Sign's presence on the far apse wall, at distance: broad broken
    jaundiced daub-strokes and the runs off them, breathing in the glow.
    Deliberately abstract (no oval, no sockets): at this size a full glyph
    gestalts into a face, and the altar close-up owns the proper look."""
    import pygame
    rng = random.Random(3)
    pulse = 1.0 + math.sin(t * 0.9) * 0.03
    col = (142, 126, 50); dark = (76, 66, 26)
    # two thin broken arc-strokes, the start of the glyph's sweep, cropped
    for (ox, oy, w0, h0, spans, th) in (
            (-R * 0.9, -R * 0.55, R * 1.8, R * 1.25,
             ((3.4, 4.1), (4.4, 5.2)), 5),
            (-R * 0.55, -R * 0.05, R * 1.3, R * 0.85,
             ((3.7, 4.3), (4.7, 5.1)), 4)):
        rect = (int(cx + ox), int(cy + oy),
                int(w0 * pulse), int(h0 * pulse))
        for a0, a1 in spans:
            pygame.draw.arc(surf, dark, rect, a0, a1, th + 2)
            pygame.draw.arc(surf, col, rect, a0 + 0.05, a1 - 0.05, th)
    # short crossing slashes where the strokes were dragged
    for k in range(3):
        sx0 = cx + int(rng.uniform(-R * 0.8, R * 0.9))
        sy0 = cy + int(rng.uniform(R * 0.1, R * 0.6))
        pygame.draw.line(surf, dark, (sx0, sy0),
                         (sx0 + rng.randint(14, 30), sy0 - rng.randint(6, 16)), 3)
    # the paint runs, off the lowest stroke
    for dx, fl in ((-R * 0.45, 1.0), (R * 0.05, 0.7), (R * 0.5, 0.5)):
        rl = int(R * 0.8 * fl)
        x0 = int(cx + dx); y0 = int(cy + R * 0.55)
        pygame.draw.line(surf, dark, (x0, y0), (x0, y0 + rl), 2)
        pygame.draw.line(surf, col, (x0, y0), (x0, y0 + rl), 1)

