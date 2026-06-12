"""The death + Carcosa cutscene art: mask-furnace, mask-yank, the detonation."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_king import (
    _yk_face, _yk_mask, _yk_orb_faces, _yk_orb_glow, _yk_radial,
    _yk_shatter_mask, _yk_spire,
    _YK_GOLD, _YK_HOT, _YK_SHADOW,
)


# ---------------------------------------------------------------------------
# King-in-Yellow death screen -- a furnace of his masks, fire all around.
# ---------------------------------------------------------------------------
def _frand(i):
    """Cheap deterministic [0,1) noise -- no RNG state to disturb."""
    x = math.sin(i * 12.9898) * 43758.5453
    return x - math.floor(x)


def _flame_tongue(surf, bx, by, dx, dy, length, width, ph):
    """One flame licking from base (bx,by) along direction (dx,dy):
    three nested tapering triangles, outer ember -> hot core."""
    pdx, pdy = -dy, dx                            # perpendicular
    sway = math.sin(ph * 3.0) * 0.32

    def tongue(frac_len, frac_w, col):
        tip = (bx + dx * length * frac_len + pdx * sway * width * frac_w,
               by + dy * length * frac_len + pdy * sway * width * frac_w)
        lf = (bx + pdx * frac_w * width * 0.5, by + pdy * frac_w * width * 0.5)
        rt = (bx - pdx * frac_w * width * 0.5, by - pdy * frac_w * width * 0.5)
        pygame.draw.polygon(surf, col,
                            [(int(lf[0]), int(lf[1])), (int(rt[0]), int(rt[1])),
                             (int(tip[0]), int(tip[1]))])
    tongue(1.0, 1.0, (196, 58, 16))
    tongue(0.72, 0.62, (252, 146, 30))
    tongue(0.46, 0.30, (255, 226, 128))


def _cold_fire_pit(surf, cx, cy, R, t):
    """A pit of COLD FIRE -- a shaft of sickly pale-teal/gold flame receding to a
    black throat, that the King's mask opens into. You are dragged down it. The
    'hell' of Carcosa: fire, but wrong and cold."""
    R = int(R)
    if R < 6:
        return
    cx, cy = int(cx), int(cy)
    # the receding shaft: bright cold flame at the rim, darkening into the depth
    for i in range(14, 0, -1):
        f = i / 14.0
        rr = max(2, int(R * f))
        fl = 0.55 + 0.45 * math.sin(t * 8 + i * 0.8)
        c = (int((18 + 66 * f) * fl), int((54 + 150 * f) * fl), int((50 + 120 * f) * fl))
        pygame.draw.ellipse(surf, c, (cx - rr, cy - int(rr * 0.92), 2 * rr, int(rr * 1.84)))
    pygame.draw.ellipse(surf, (3, 5, 6), (cx - int(R * 0.3), cy - int(R * 0.28),
                                          int(R * 0.6), int(R * 0.56)))
    # cold flame tongues licking up around the rim
    for k in range(18):
        a = k * math.tau / 18 + math.sin(t * 2 + k) * 0.05
        bx, by = cx + math.cos(a) * R * 0.92, cy + math.sin(a) * R * 0.84
        fl = R * (0.12 + 0.12 * (0.5 + 0.5 * math.sin(t * 7 + k * 1.6)))
        tx, ty = bx + math.cos(a) * fl, by + math.sin(a) * fl * 0.9
        col = (150, 214, 184) if k % 2 else (206, 204, 130)
        pygame.draw.line(surf, col, (int(bx), int(by)), (int(tx), int(ty)),
                         max(1, int(R * 0.02)))
    # WRITHING FORMS in the deep -- the taken glimpsed in the cold fire,
    # distorted faces winding through the shaft.
    for k in range(6):
        a = k * 1.4 + t * 0.45
        rad = R * (0.45 + 0.18 * math.sin(t * 0.8 + k * 1.7))
        fx = cx + math.cos(a) * rad
        fy = cy + math.sin(a) * rad * 0.86
        rs = max(2, int(R * (0.05 + 0.03 * _frand(k * 3))))
        pygame.draw.ellipse(surf, (52, 92, 78),
                            (int(fx - rs), int(fy - int(rs * 1.1)), rs * 2, int(rs * 2.2)))
        pygame.draw.circle(surf, (4, 6, 7), (int(fx - rs * 0.32), int(fy - rs * 0.2)),
                           max(1, int(rs * 0.25)))
        pygame.draw.circle(surf, (4, 6, 7), (int(fx + rs * 0.32), int(fy - rs * 0.2)),
                           max(1, int(rs * 0.25)))
        # a thin slack mouth, sometimes open
        pygame.draw.line(surf, (4, 6, 7),
                         (int(fx - rs * 0.3), int(fy + rs * 0.45)),
                         (int(fx + rs * 0.3), int(fy + rs * 0.45)),
                         max(1, int(rs * 0.2)))
    # WET SWIRLING streaks -- bright cold-fire lines winding around the shaft,
    # so the flame reads as flowing/wet, not a smooth gradient.
    for k in range(7):
        a0 = k * math.tau / 7 + t * 0.9
        pts = [(int(cx + math.cos(a0 + s * 0.32) * R * (0.85 - s * 0.13)),
                int(cy + math.sin(a0 + s * 0.32) * R * (0.85 - s * 0.13) * 0.88))
               for s in range(6)]
        col = (188, 220, 188) if k % 2 else (220, 212, 140)
        pygame.draw.lines(surf, col, False, pts, max(1, int(R * 0.012)))


def draw_king_death(surf, t):
    """THE KING REVEALED. The distant void you have fled all game finally
    ARRIVES in full: His blazing Carcosa furnace floods the frame, His shattered
    pallid mask commands the centre with the gaze fixed on you, His arms reach
    out and DRAG you into the mask -- which cracks open into a pit of COLD FIRE,
    the hell of Carcosa, that you are hauled down. The dread is recognition: the
    thing that hunted you is here, and it has you. `t` ~ 4.5s (caller holds 5s)."""
    w, h = surf.get_size()
    cx, cy = w // 2, int(h * 0.46)

    def eo(x):
        x = max(0.0, min(1.0, x))
        return 1.0 - (1.0 - x) ** 2.3

    ramp = max(0.0, min(1.0, t / 0.2))
    kindle = eo((t - 0.05) / 0.3)                   # He arrives FAST (~0.05-0.35s)
    behold = max(0.0, min(1.0, (t - 0.05) / 0.55))  # arms grab + gaze locks from the start
    take = eo((t - 1.0) / 1.8)                      # the general surge (scale/grade)
    # Cracks appear EARLY (within ~0.5s of arrival) and spread through the
    # whole approach, then at t~1.45 the mask SNAPS open hard.
    linger = max(0.0, min(1.0, (t - 0.3) / 1.1))    # cracks spread 0.3-1.4
    if t < 1.45:
        crack = 0.35 * linger
    else:
        crack = 0.55 + 0.40 * min(1.0, (t - 1.45) / 0.35)  # SNAP at 1.45
    snap = math.exp(-(((t - 1.45) / 0.07) ** 2))
    # the second face beneath -- a screaming raw visage -- LUNGES the moment
    # the mask snaps, then settles for a beat.
    second = max(0.0, min(1.0, (t - 1.45) / 0.45))
    lunge = math.exp(-(((t - 1.6) / 0.10) ** 2))
    pit_open = (max(0.0, (t - 2.0) / 0.75)) ** 1.15  # the pit blooms from it
    engulf = eo((t - 2.7) / 0.55)                   # the depth swallows you
    flick = 0.85 + 0.12 * math.sin(t * 16.0) + 0.05 * math.sin(t * 37.0)
    fr = 50 + kindle * 140 + behold * 48 + take * 150    # His mask radius: looms + surges
    pres = min(1.0, 0.5 + 0.5 * behold + 0.4 * take)

    scene = pygame.Surface((w, h))
    scene.fill((4, 3, 5))                            # the dark He arrives out of

    # 1. THE CARCOSA FURNACE -- a vast warm realm-glow flooding the frame (FILLED,
    #    never additive, so it stays a furnace, not a flat gold disc).
    fg = (0.30 + 0.70 * kindle) * (1.0 + 0.55 * take) * flick * (1.0 - 0.8 * second)
    _yk_radial(scene, cx, cy + int(fr * 0.1),
               int(min(w, h) * (0.55 + 0.5 * kindle + 0.35 * take)),
               (150, 66, 22), int(74 * fg * ramp), add=False)
    _yk_radial(scene, cx, cy, int(fr * 1.25), (208, 116, 40),
               int(80 * fg * ramp), add=False)

    # 2. His arms LURCH and GRAB at you -- fanned down toward the player, snatching
    #    out in sharp lunges (a quick grab-and-recoil), reaching past the frame.
    dk, gold, hot = (*_YK_SHADOW, 255), (*_YK_GOLD, 255), (*_YK_HOT, 255)
    narm = 8
    for i in range(narm):
        root = i * math.tau / narm
        rx = cx + math.cos(root) * fr * 0.5
        ry = cy + math.sin(root) * fr * 0.5
        aim = root * 0.3 + (math.pi * 0.5) * 0.7 + 0.1 * math.sin(t * 1.5 + i)  # toward you
        ph = (t * 0.7 + i * 0.6) % 1.0
        grab = math.exp(-(((ph - 0.35) / 0.14) ** 2))       # a sharp snatch
        lng = fr * (0.7 + (0.9 + 1.3 * take) * grab)
        _yk_spire(scene, rx, ry, aim, lng, fr, t, i, pres, dk, gold, hot)

    # 3. The taken, glimpsed faintly as soul-orbs adrift in His blaze.
    for i in range(5):
        a = i * 1.4 + t * 0.5
        rad = fr * (1.35 + 0.3 * math.sin(i * 2 + t))
        ox, oy = cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.7
        _yk_orb_glow(scene, ox, oy, fr * 0.13, 0.28 * behold)
        _yk_orb_faces(scene, ox, oy, fr * 0.13, 0.28 * behold, i, t)

    # 4. Light bleeding through the early cracks (fades as the face beneath shows).
    _yk_radial(scene, cx, cy, int(fr * 0.5), _YK_HOT,
               int(70 * linger * (1.0 - second)), add=False)

    # 5. THE SECOND FACE beneath the mask -- a screaming RAW visage (wet red
    #    flesh, not pallid bone, so it reads as something WORSE under the calm
    #    mask), the gaze blazing. Drawn UNDER the pallid mask so it surfaces as
    #    the shards part.
    if second > 0.02:
        # the LUNGE -- it scale-spikes toward the camera the instant it's bared
        fr2 = int(fr * 0.92 * (1.0 + 0.35 * lunge))
        _yk_radial(scene, cx, cy, int(fr2 * 0.85), (70, 16, 14), int(70 * second), add=False)
        face2 = pygame.Surface((w, h), pygame.SRCALPHA)   # _yk_face: the bare face, NO hot halo
        _yk_face(face2, cx, cy, fr2, "scream", True, True)
        red = pygame.Surface((w, h))
        red.fill((230, 70, 50))
        face2.blit(red, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        scene.blit(face2, (0, 0))                          # revealed AS the mask parts

        # VEINS across the raw flesh -- thin wavy dark-red lines, asymmetric.
        for vi in range(9):
            a = vi * 0.82 + (_frand(vi * 3) - 0.5) * 0.4
            x0 = cx + (_frand(vi * 5) - 0.5) * fr2 * 0.6
            y0 = cy + (_frand(vi * 7) - 0.5) * fr2 * 0.5
            pts = [(x0, y0)]
            for s in range(5):
                a2 = a + math.sin(s * 0.8 + vi) * 0.6
                x0 += math.cos(a2) * fr2 * 0.07
                y0 += math.sin(a2) * fr2 * 0.07
                pts.append((x0, y0))
            pygame.draw.lines(scene, (94, 18, 14), False,
                              [(int(x), int(y)) for x, y in pts], 1)
        # BLEEDING TEARS from the eye sockets -- thick black runs sliding down.
        for sgn in (-1, 1):
            ex = cx + sgn * int(fr2 * 0.42)
            ey = cy - int(fr2 * 0.12)
            dlen = int(fr2 * (0.42 + 0.08 * math.sin(t * 3 + sgn)))
            pygame.draw.line(scene, (8, 6, 6),
                             (int(ex), int(ey + fr2 * 0.04)),
                             (int(ex + sgn * fr2 * 0.04), int(ey + fr2 * 0.04) + dlen),
                             max(2, int(fr2 * 0.03)))
        # small hot pupils, slightly washed by the tears
        for sgn in (-1, 1):
            ex = cx + sgn * int(fr2 * 0.42)
            ey = cy - int(fr2 * 0.12)
            _yk_radial(scene, ex, ey, int(fr2 * 0.06), _YK_HOT, int(190 * second))
        # BONE TEETH ringing the screaming maw -- pale wedges pointing inward.
        mw = fr2 * 0.32
        mh = fr2 * 0.42
        mxx, myy = cx, int(cy + fr2 * 0.55)
        nt = 12
        for k in range(nt):
            ang = math.pi + (k + 0.5) * (math.tau / nt)
            tx = mxx + math.cos(ang) * mw * 0.92
            ty = myy + math.sin(ang) * mh * 0.92
            dx, dy = (mxx - tx), (myy - ty)
            tl = math.hypot(dx, dy) or 1
            tip = (int(tx + dx / tl * mh * 0.18), int(ty + dy / tl * mh * 0.18))
            px, py = -dy / tl, dx / tl
            tb1 = (int(tx + px * mh * 0.06), int(ty + py * mh * 0.06))
            tb2 = (int(tx - px * mh * 0.06), int(ty - py * mh * 0.06))
            pygame.draw.polygon(scene, (208, 196, 168), [tb1, tip, tb2])
        # WET DROOL strings sagging from the maw -- thin black strands, swaying.
        for k in range(3):
            dx0 = mxx + (k - 1) * mw * 0.5
            dy0 = myy + mh * 0.55
            sag = fr2 * (0.18 + 0.05 * math.sin(t * 2.2 + k * 1.7))
            mid = (int(dx0 + (k - 1) * 3), int(dy0 + sag * 0.5))
            end = (int(dx0 + (k - 1) * 5), int(dy0 + sag))
            pygame.draw.lines(scene, (10, 7, 8), False,
                              [(int(dx0), int(dy0)), mid, end], 2)

    # THE SNAP -- a hard punctuation when the mask explodes open: blood spatter
    # flying out from the centre, and a brief black-and-red flash.
    if 0.01 < snap or (2.0 <= t <= 2.6):
        sp_age = max(0.0, t - 2.0)
        for k in range(28):
            ang = k * (math.tau / 28) + _frand(k * 5) * 0.4
            v = 360 + 240 * _frand(k * 7 + 1)
            sx = cx + math.cos(ang) * v * sp_age
            sy = cy + math.sin(ang) * v * sp_age + 220 * sp_age * sp_age   # a touch of gravity
            sr = max(1, 3 - int(sp_age * 4))
            if 0 <= sx < w and 0 <= sy < h and sp_age < 0.7:
                pygame.draw.circle(scene, (170, 28, 22), (int(sx), int(sy)), sr + 1)
                pygame.draw.circle(scene, (240, 70, 50), (int(sx), int(sy)), sr)

    # 6. The pallid wail-MASK on top. The cracks spread, then the shards PULL
    #    APART -- flung aside like doors -- baring the face beneath.
    mvis = min(1.0, 0.5 + 0.5 * kindle) * (1.0 - 0.85 * second)  # fades as it opens away
    _yk_shatter_mask(scene, cx, cy, int(fr), mvis,
                     "wail", crack, t, int(fr), aim=math.pi / 2, arms=False)
    # WET SHEEN on the pallid mask -- a thin highlight arc, the bone slick with
    # His blaze (only while the mask is still mostly intact).
    if mvis > 0.55 and crack < 0.25:
        sh = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.arc(sh, (255, 248, 222, int(72 * mvis)),
                        (cx - int(fr * 0.7), cy - int(fr * 0.96),
                         int(fr * 1.4), int(fr * 1.92)),
                        math.pi * 0.92, math.pi * 1.20, max(1, int(fr * 0.025)))
        scene.blit(sh, (0, 0))
    # FRACTURE LINES spreading from the centre during the linger -- thin gold
    # seams of His blaze bleeding through, accumulating just before the snap.
    if 0.02 < linger and t < 2.0:
        n_cracks = 2 + int(7 * linger)
        for c in range(n_cracks):
            a = c * 1.27 + 0.4 + _frand(c * 5) * 0.3
            x0, y0 = float(cx), float(cy)
            pts = [(x0, y0)]
            for s in range(5):
                step = fr * 0.16 * linger
                a2 = a + (_frand(c * 11 + s) - 0.5) * 0.7
                x0 += math.cos(a2) * step
                y0 += math.sin(a2) * step
                pts.append((x0, y0))
            ip = [(int(x), int(y)) for x, y in pts]
            pygame.draw.lines(scene, (30, 22, 14), False, ip, 2)
            pygame.draw.lines(scene, (236, 200, 110), False, ip, 1)
    if second <= 0.05:
        for sgn in (-1, 1):                          # the pallid mask's gaze (until it opens)
            ex = cx + sgn * int(fr * 0.42)
            ey = cy - int(fr * 0.12)
            gz = fr * (0.1 + 0.04 * math.sin(t * 4))
            _yk_radial(scene, ex, ey, int(gz * 2.2), _YK_GOLD,
                       int(70 * (0.4 + 0.6 * behold)), add=False)
            _yk_radial(scene, ex, ey, int(gz), _YK_HOT, int(155 * (0.4 + 0.6 * behold)))

    # 7. THE PIT. The second face's heart yawns into a shaft of COLD FIRE, the
    #    hell of Carcosa, that you are dragged down.
    if pit_open > 0.01:
        pit_r = fr * 0.12 + pit_open * min(w, h) * 0.5
        _cold_fire_pit(scene, cx, cy, pit_r, t)

    # 6. Embers of the furnace streaming up.
    for i in range(40):
        ex = (_frand(i * 2 + 1) * w + math.sin(t * 1.4 + i) * 11) % w
        span = h + 50
        ey = (h + 24 - ((t * (46 + 70 * _frand(i))) + _frand(i * 2 + 2) * span) % span)
        er = 1 + int(2 * _frand(i * 3))
        pygame.draw.circle(scene, (240, 188, 96), (int(ex), int(ey)), er)

    # Vignette -- the dark presses the furnace in from the edges.
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(64):
        a = int(200 * (1 - i / 64) ** 1.4 * ramp)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    scene.blit(vig, (0, 0))

    # Compose: He advances through the behold, the SNAP jolts hard, then the
    # camera dives down the cold-fire pit.
    surf.fill((0, 0, 0))
    z = 1.0 + 0.12 * behold + 1.25 * pit_open + 0.10 * lunge
    shx = int((math.sin(t * 71) * 18 + math.cos(t * 53) * 12) * snap)
    shy = int((math.cos(t * 67) * 14 + math.sin(t * 47) * 10) * snap)
    if z > 1.001:
        zw, zh = int(w * z), int(h * z)
        surf.blit(pygame.transform.smoothscale(scene, (zw, zh)),
                  (-(zw - w) // 2 + shx, -(zh - h) // 2 + shy))
    else:
        surf.blit(scene, (shx, shy))

    # The black-flash on the SNAP: a 1-frame dark-red punctuation as the mask
    # explodes open.
    if snap > 0.4:
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((30, 6, 6, int(230 * snap)))
        surf.blit(fl, (0, 0))

    # SUBLIMINAL FLASH -- for a couple of frames at the snap, a giant distorted
    # screaming face stamps over everything. The eye barely catches it; the
    # animal brain does.
    if 1.435 < t < 1.495:
        big = pygame.Surface((w, h), pygame.SRCALPHA)
        fr3 = int(min(w, h) * 0.46)
        _yk_face(big, cx, cy, fr3, "scream", True, True)
        rd = pygame.Surface((w, h))
        rd.fill((220, 40, 26))
        big.blit(rd, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        big = pygame.transform.smoothscale(big, (int(w * 1.18), int(h * 0.82)))
        surf.blit(big, ((w - big.get_width()) // 2, (h - big.get_height()) // 2))

    # Down the pit -- a cold-fire flicker floods as you are hauled in, then the
    # depth swallows it toward dark (you are inside Carcosa now).
    if engulf > 0.01:
        e = min(1.0, engulf)
        cfl = 0.6 + 0.4 * math.sin(t * 12)
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((int(120 * cfl), int(180 * cfl), int(150 * cfl),
                 int(150 * e)))                      # cold-fire wash
        surf.blit(fl, (0, 0))
        if engulf > 0.6:                             # the depth closes over you
            d = (engulf - 0.6) / 0.4
            bl = pygame.Surface((w, h), pygame.SRCALPHA)
            bl.fill((3, 7, 8, int(165 * min(1.0, d))))
            surf.blit(bl, (0, 0))

    # The grime grade -- warm (His furnace) cooling toward cold-fire as the pit
    # opens and takes you, a cold rot always in the shadows.
    warm = (214, 184, 150)
    cold = (150, 184, 178)
    tint = tuple(int(warm[k] + (cold[k] - warm[k]) * pit_open) for k in range(3))
    _carcosa_post(surf, t, tint=tint, cold=(3, 8, 13))


# ---- The Carcosa tableau: the rite_broken explosion ending --------------
# Distinct from draw_king_death (the King catching YOU). This is the rite
# torn down with the source still open (NARRATIVE §6): the King erupts as a
# TREE OF THE TAKEN -- every branch hung with a face He now wears -- and His
# influence floods DOWN and OUT over the drowned town. A wholly procedural
# homage in the Yellow palette; `t` = seconds since the break (held ~7s).
_CARCOSA_FACEKINDS = ("wail", "vacant", "gaunt", "hollow")


def _carcosa_branch(surf, x, y, ang, length, depth, grow, t, seed, masks,
                    cx0, cy0):
    """One recursive black tendril of the King's tree. Extends with `grow`
    (0..1) so the tree erupts over time, sways on a per-branch phase, and
    drops mask-anchors (x, y, r, seed) of WILDLY varied size along it (never
    piled at the core `cx0,cy0`) for faces drawn on top afterward."""
    if depth <= 0 or length < 6.0:
        return
    L = length * grow
    a = ang + math.sin(t * 0.6 + seed * 0.9) * 0.12
    x2 = x + math.cos(a) * L
    y2 = y + math.sin(a) * L
    pygame.draw.line(surf, (9, 7, 6), (int(x), int(y)), (int(x2), int(y2)),
                     max(2, depth + 1))                       # bold tendrils
    if depth <= 4 and grow > 0.18 and len(masks) < 130 \
            and _frand(seed + 9) > 0.7 \
            and math.hypot(x2 - cx0, y2 - cy0) > 60:          # not at the core
        r = int((3 + depth * 3) * (0.55 + 1.8 * _frand(seed + 11)))  # tiny..big
        masks.append((x2, y2, max(4, r), seed))
    branches = 2 if _frand(seed) > 0.4 else 3
    spread = 0.40 + 0.34 * _frand(seed + 1)
    for k in range(branches):
        na = a + (k - (branches - 1) / 2.0) * spread \
            + (_frand(seed + k + 7) - 0.5) * 0.42              # gnarlier
        _carcosa_branch(surf, x2, y2, na,
                        length * (0.64 + 0.12 * _frand(seed + k + 3)),
                        depth - 1, grow, t, seed * 3 + k + 5, masks, cx0, cy0)


def _carcosa_town(surf, w, h, base_y, t, flood):
    """A drowned gothic skyline along `base_y` with a rippling reflection
    below it, the King's gold light flooding down through and over it."""
    # A low horizon backlight so the skyline silhouettes read -- FILLED with
    # per-pixel alpha (composited, not additive) so it can't blow out into a
    # disc the way _yk_radial does. Brightens toward the waterline.
    bh_ = int(h * 0.26)
    band = pygame.Surface((w, bh_), pygame.SRCALPHA)
    for yy in range(bh_):
        a = int(64 * (yy / bh_) ** 1.6 * flood)
        if a > 0:
            pygame.draw.line(band, (96, 78, 32, a), (0, yy), (w, yy))
    surf.blit(band, (0, base_y - bh_ + 8))
    _yk_radial(surf, w // 2, base_y + 18, int(w * 0.08), _YK_HOT,
               int(9 * flood))     # a small glint on the water
    roofs = []
    x, i = -6, 0
    while x < w + 6:
        bw = 16 + int(30 * _frand(i * 3 + 1))
        bh = 16 + int(52 * _frand(i * 3 + 2))
        steeple = _frand(i * 3 + 5) > 0.78
        roofs.append((x, bw, bh))
        pygame.draw.rect(surf, (5, 5, 8), (x, base_y - bh, bw, bh + 80))
        pygame.draw.polygon(surf, (5, 5, 8),
                            [(x - 2, base_y - bh), (x + bw // 2, base_y - bh - 12),
                             (x + bw + 2, base_y - bh)])
        if steeple:
            sx = x + bw // 2
            pygame.draw.rect(surf, (5, 5, 8), (sx - 3, base_y - bh - 40, 6, 40))
            pygame.draw.polygon(surf, (5, 5, 8),
                                [(sx - 5, base_y - bh - 40), (sx, base_y - bh - 58),
                                 (sx + 5, base_y - bh - 40)])
        x += bw + 2
        i += 1
    for (rx, bw, bh) in roofs:                 # rippling reflection
        dx = int(math.sin(t * 1.1 + rx * 0.05) * 3)
        pygame.draw.rect(surf, (6, 6, 10), (rx + dx, base_y + 2, bw,
                                            int(bh * 0.72)))
    for k in range(7):                          # gold shimmer on the water
        a = int(30 * flood * (1 - k / 7.0) * (0.5 + 0.5 * math.sin(t * 2 + k)))
        if a <= 0:
            continue
        line = pygame.Surface((w, 2), pygame.SRCALPHA)
        line.fill((_YK_GOLD[0], _YK_GOLD[1], _YK_GOLD[2], a))
        surf.blit(line, (0, base_y + 5 + k * 7))


_CARCOSA_GRAIN = None


def _carcosa_post(surf, t, tint=(220, 210, 164), cold=(0, 10, 14)):
    """Darkwood / Fear & Hunger grime applied to the whole cutscene frame so
    nothing reads as clean vector: chunky downsample, a muddy palette multiply
    (`tint`), a cold shadow-tone (`cold`), animated dither-grain, a guttering
    flicker, and crushed edges."""
    w, h = surf.get_size()
    # Chunky downsample -> dirty low-res pixels (F&H grit).
    dw, dh = int(w / 2.5), int(h / 2.5)
    surf.blit(pygame.transform.scale(
        pygame.transform.smoothscale(surf, (dw, dh)), (w, h)), (0, 0))
    # Muddy the palette, but lightly -- keep the sickly highlights bright
    # against the dark (high contrast, not flat mud).
    tn = pygame.Surface((w, h))
    tn.fill(tint)
    surf.blit(tn, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    # Cold counter-tone: lift the shadows toward a sickly bruise-teal (added,
    # so it shows in the darks while the highlights stay warm) -- the Darkwood
    # / F&H dread split between warm light and cold rot.
    if cold != (0, 0, 0):
        cl = pygame.Surface((w, h))
        cl.fill(cold)
        surf.blit(cl, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    grime = pygame.Surface((w, h), pygame.SRCALPHA)
    grime.fill((30, 34, 26, 14))
    surf.blit(grime, (0, 0))
    # Animated dither-grain (built once).
    global _CARCOSA_GRAIN
    if _CARCOSA_GRAIN is None:
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        rg = random.Random(13)
        for _ in range(int(w * h * 0.11)):
            x, y = rg.randint(0, w - 1), rg.randint(0, h - 1)
            if rg.random() < 0.55:
                g.set_at((x, y), (0, 0, 0, rg.randint(40, 95)))
            else:
                g.set_at((x, y), (190, 168, 116, rg.randint(20, 60)))
        _CARCOSA_GRAIN = g
    surf.blit(_CARCOSA_GRAIN, (random.randint(-2, 2), random.randint(-2, 2)))
    # Guttering flicker -- the light stutters (Darkwood).
    if random.random() < 0.10:
        d = pygame.Surface((w, h))
        d.fill((16, 14, 10))
        surf.blit(d, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    # Crushed edge vignette.
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(60):
        a = int(165 * (1 - i / 60) ** 1.6)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    surf.blit(vig, (0, 0))


def _draw_carcosa_axe(surf, hx, hy, ang, k=1.0):
    """The splitting axe mid-swing: a wood handle + a steel wedge head."""
    dx, dy = math.cos(ang), math.sin(ang)
    tail = (int(hx - dx * 200 * k), int(hy - dy * 200 * k))
    pygame.draw.line(surf, (26, 18, 11), (int(hx), int(hy)), tail,
                     max(2, int(9 * k)))
    pygame.draw.line(surf, (76, 54, 31), (int(hx), int(hy)), tail,
                     max(1, int(6 * k)))
    px, py = -dy, dx
    blade = [(int(hx + px * 5 * k), int(hy + py * 5 * k)),
             (int(hx + (dx * 34 + px * 30) * k), int(hy + (dy * 34 + py * 30) * k)),
             (int(hx + (dx * 34 - px * 30) * k), int(hy + (dy * 34 - py * 30) * k)),
             (int(hx - px * 5 * k), int(hy - py * 5 * k))]
    pygame.draw.polygon(surf, (42, 44, 50), blade)
    pygame.draw.polygon(surf, (168, 172, 180), blade, 2)


def _yank_daub(surf, x, y, R, t, seed, bleed=0.0):
    """One painted Sign at cutscene scale -- the cult's crude mask-daub
    (CANON: a broken oval, two thumb-press sockets, NO mouth, paint runs;
    the _draw_yellow_sign grammar). Breathes on a faint gold pulse while
    the rite holds; `bleed` (0..1) kills the glow and sends dark-red runs
    down the wall (the Sign bleeds when the Mask is struck)."""
    rng = random.Random(seed)
    pulse = 1.0 + math.sin(t * 1.1 + seed) * 0.08
    glow = max(0.0, 1.0 - bleed)
    if glow > 0.03:
        _yk_radial(surf, int(x), int(y), int(R * 2.1 * pulse), (206, 188, 84),
                   int((30 + 8 * math.sin(t * 1.1 + seed)) * glow), add=False)
    col = (196, 178, 72)
    dark = (92, 80, 28)
    sock = (6, 5, 4)
    rx = R * rng.uniform(0.66, 0.74)
    ry = R * rng.uniform(0.96, 1.06)
    wd_d = max(2, int(R * 0.085))
    wd_c = max(1, int(R * 0.055))
    n = 16
    pts = []
    for i in range(n):
        a = i / n * math.tau
        w = rng.uniform(-2.4, 2.4) * R / 13.0
        pts.append((x + math.cos(a) * (rx + w), y + math.sin(a) * (ry + w)))
    for i in range(n):
        if rng.random() < 0.78:
            a, b = pts[i], pts[(i + 1) % n]
            pygame.draw.line(surf, dark, a, b, wd_d)
            pygame.draw.line(surf, col, a, b, wd_c)
    sockets = []
    for fx, fy, fr in ((-0.40, -0.25, 0.20), (0.43, -0.18, 0.23)):
        sxp, syp = int(x + rx * fx), int(y + ry * fy)
        srr = max(2, int(R * fr))
        sockets.append((sxp, syp, srr))
        pygame.draw.circle(surf, sock, (sxp, syp), srr)
    # Two paint runs off the chin, one trailing thinner (wet, never dried).
    creep = 1.0 + 0.30 * math.sin(t * 0.13 + seed * 0.7)
    for dx, fl in ((-R * 0.2, 1.0), (R * 0.12, 0.7)):
        rl = rng.randint(int(R * 0.4), int(R * 0.9)) * fl * creep
        y0 = y + ry * 0.9
        pygame.draw.line(surf, dark, (int(x + dx), int(y0)),
                         (int(x + dx), int(y0 + rl)), max(2, int(R * 0.04)))
    # THE BLEED: dark-red wells from the sockets and runs down the wall.
    if bleed > 0.02:
        for j, (sxp, syp, srr) in enumerate(sockets):
            pygame.draw.circle(surf, (96, 18, 14), (sxp, syp),
                               max(2, int(srr * (0.5 + 0.5 * bleed))))
            for k in range(2):
                bx = sxp + (k * 2 - 1) * max(1, srr // 3) + int((_frand(seed + j * 3 + k) - 0.5) * srr)
                ln = int(R * (0.5 + 2.2 * bleed) * (0.7 + 0.5 * _frand(seed + j + k * 7)))
                pygame.draw.line(surf, (96, 18, 14), (bx, syp + srr - 1),
                                 (bx + int((_frand(seed + k) - 0.5) * 6), syp + srr + ln),
                                 max(1, int(R * 0.035)))


def _yank_kneeler(surf, x, y, k, t, seed, lift=0.0):
    """One congregant seen from behind, bowed at the rite -- a near-black
    robed hump with a faint candle-side rim. `lift` (0..1) raises the bowed
    head (the shatter beat: every head in the room comes up as one)."""
    sway = math.sin(t * 0.8 + seed * 1.7) * 0.015 * k
    robe = (11, 9, 13)
    rim = (54, 44, 22)
    bw, bh = int(k * 1.05), int(k * 0.78)
    body = pygame.Rect(0, 0, bw, bh)
    body.center = (int(x + sway), int(y))
    pygame.draw.ellipse(surf, robe, body)
    pygame.draw.arc(surf, rim, body.inflate(2, 2), math.pi * 0.25,
                    math.pi * 0.78, max(1, int(k * 0.04)))
    hr = max(3, int(k * 0.21))
    hy = y - bh * (0.34 + 0.42 * lift)
    hx = x + sway + bw * 0.05 * (1.0 - lift)
    pygame.draw.circle(surf, robe, (int(hx), int(hy)), hr)
    pygame.draw.arc(surf, rim,
                    (int(hx - hr), int(hy - hr), hr * 2, hr * 2),
                    math.pi * 0.2, math.pi * 0.9, 1)


def _yank_candle(surf, x, y, t, seed, out=0.0):
    """A lit altar candle: stub, halo, a guttering flame. `out` (0..1)
    snuffs it -- the flame dies and a smoke wisp curls off the wick (every
    candle in the chamber goes out on the blow)."""
    pygame.draw.rect(surf, (172, 158, 128), (int(x - 3), int(y), 6, 14))
    pygame.draw.rect(surf, (96, 86, 66), (int(x - 3), int(y), 6, 14), 1)
    if out < 0.95:
        fl = (0.7 + 0.3 * math.sin(t * 9 + seed * 2.1)) * (1.0 - out)
        _yk_radial(surf, int(x), int(y - 6), int(26 * fl + 6), (224, 176, 88),
                   int(46 * fl), add=False)
        fh = int(9 * fl) + 2
        pygame.draw.ellipse(surf, (236, 168, 70),
                            (int(x - 3), int(y - 4 - fh), 6, fh + 4))
        pygame.draw.ellipse(surf, (255, 234, 168),
                            (int(x - 1), int(y - 1 - fh // 2), 3, fh // 2 + 2))
    if 0.02 < out:
        # the smoke wisp, rising and dispersing
        wl = int(18 + 26 * out)
        pts = [(int(x + math.sin(t * 3 + seed + s * 0.9) * (2 + s * 1.5 * out)),
                int(y - 6 - s * wl / 4)) for s in range(5)]
        a = int(90 * (1.0 - out))
        if a > 8:
            wisp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(wisp, (120, 118, 124, a), False, pts, 1)
            surf.blit(wisp, (0, 0))


def draw_mask_yank(surf, t):
    """The act that breaks the rite (NARRATIVE §6): you SHATTER the Pallid
    Mask with your splitting axe -- the catastrophic 'tear it down'. Staged
    as the Sign Chamber the player is standing in: the Mask big on its
    pedestal altar, the vast daubed Sign above it with its flanking copies,
    the candle row, the kneeling congregation bowed in the foreground. Dread
    stillness, the axe swings in, the mask bursts, every candle dies, the
    daubs bleed, the kneelers' heads come up as one -- whiting out into the
    blast. `t` = seconds into the act (~3s)."""
    w, h = surf.get_size()
    cx, cy = w // 2, int(h * 0.47)
    impact = 1.6
    sh = max(0.0, t - impact)                      # time since the blow lands
    flare = max(0.0, (t - 2.55) / 0.45)
    shake = min(1.0, sh / 0.3) if sh > 0 else 0.04 * (t / impact)
    shx = int(math.sin(t * 64) * (2 + 20 * shake))
    shy = int(math.cos(t * 70) * (1 + 12 * shake))
    sx, sy = cx + shx, cy + shy
    r = 112                                        # the Mask, altar-piece big
    s = max(0.0, sh - 0.07)                        # time since the shatter
    bleed = min(1.0, s * 1.6)                      # the Sign bleeding out
    out = min(1.0, s * 1.2) if sh > 0 else 0.0     # the candles dying

    surf.fill((9, 8, 11))
    for i in range(7):                             # apse-wall stone seams
        yy = int(h * (0.12 + 0.12 * i)) + (i % 2) * 6
        pygame.draw.line(surf, (16, 14, 18), (0, yy), (w, yy + 4), 1)
    # The floor line + a deep apse shadow behind the altar.
    fy = int(h * 0.80)
    pygame.draw.rect(surf, (7, 6, 9), (0, fy, w, h - fy))
    pygame.draw.line(surf, (15, 13, 17), (0, fy), (w, fy), 2)
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (4, 3, 6, 150),
                        (sx - int(r * 1.7), sy - int(r * 2.1),
                         int(r * 3.4), int(r * 4.0)))
    surf.blit(shadow, (0, 0))
    # The daubed Sign, vast over the altar, flanked by two smaller hands'
    # copies (the scene's own staging: every daub a crude copy of the Mask
    # below it). They bleed when the original is struck.
    _yank_daub(surf, sx, int(h * 0.15) + shy, 84, t, 5, bleed)
    _yank_daub(surf, sx - 312, int(h * 0.18) + shy, 46, t, 11, bleed * 0.8)
    _yank_daub(surf, sx + 308, int(h * 0.17) + shy, 49, t, 23, bleed * 0.8)
    # The pedestal altar the Mask sits on.
    ped_y = sy + int(r * 0.92)
    pygame.draw.rect(surf, (24, 21, 27), (sx - 96, ped_y, 192, 18))
    pygame.draw.rect(surf, (38, 34, 42), (sx - 96, ped_y, 192, 5))
    pygame.draw.polygon(surf, (18, 16, 21),
                        [(sx - 74, ped_y + 18), (sx + 74, ped_y + 18),
                         (sx + 58, fy + 26), (sx - 58, fy + 26)])
    # The candle row along the altar's foot. Every flame dies on the blow.
    for j, dx in enumerate((-226, -148, 148, 226)):
        _yank_candle(surf, sx + dx, ped_y + 6, t, j * 3 + 1, out)
        if out < 0.9:                              # warm pools on the floor
            _yk_radial(surf, sx + dx, ped_y + 16, 40, (160, 118, 52),
                       int(16 * (1.0 - out)), add=False)
    hitstop = 0.07                                 # frozen frames on contact
    if sh <= hitstop:
        # Mask whole. Tremor builds; the axe rears back, HOLDS, then drops.
        trem = int(math.sin(t * 36) * 2 * (t / impact))
        # Swing timeline: enter+cock [0.55,1.05] -> anticipation HOLD
        # [1.05,1.35] -> fast accel drop [1.35,impact].
        cocked = (sx + 264, sy - 224)              # axe held high, upper-right
        contact = (sx + 30, sy - int(r * 0.40))
        if t < 1.05:
            p = max(0.0, (t - 0.55) / 0.5)
            ax = sx + 600 - (600 - 264) * p        # slide in from off-screen
            ay = sy - 224
            hxx, hyy = int(ax), int(ay)
        elif t < 1.35:
            hxx, hyy = cocked                      # the held beat (dread)
            hyy += int(math.sin(t * 30) * 2)       # a small quiver
        else:
            sw = ((t - 1.35) / (impact - 1.35)) ** 2.4   # hard accelerating drop
            hxx = int(cocked[0] + (contact[0] - cocked[0]) * sw)
            hyy = int(cocked[1] + (contact[1] - cocked[1]) * sw)
        ang = math.atan2(contact[1] - cocked[1], contact[0] - cocked[0])
        ms = r * 2 + 26
        msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
        _yk_mask(msurf, ms // 2, ms // 2, r, 1.0, "wail")
        if sh <= 0:
            surf.blit(msurf, msurf.get_rect(center=(sx + trem, sy)))
            _draw_carcosa_axe(surf, hxx, hyy, ang, 1.45)
        else:
            # CONTACT held: axe buried, a hairline crack lights, white spark.
            surf.blit(msurf, msurf.get_rect(center=(sx, sy)))
            crk = [(sx + (_frand(c) - 0.5) * 26, sy - int(r * 1.05) + c * int(r * 0.36))
                   for c in range(7)]
            pygame.draw.lines(surf, (255, 248, 224), False,
                              [(int(a), int(b)) for a, b in crk], 2)
            _draw_carcosa_axe(surf, contact[0], contact[1], ang, 1.45)
            _yk_radial(surf, contact[0], contact[1], 34, (255, 248, 224), 220)
    else:
        # SHATTERED: the mask SPLITS down the strike line into two halves that
        # fall apart under gravity, gore bursts from the socket, debris rains.
        _yk_radial(surf, sx, sy, int(70 + 110 * shake), (150, 30, 22),
                   int(28 + 46 * shake))
        for i in range(5):                         # red bleeding rakes
            a = (i / 5.0) * math.tau + 0.4
            ln = 80 + 260 * min(1.0, s * 1.4)
            pygame.draw.line(surf, (110, 26, 18), (sx, sy),
                             (int(sx + math.cos(a) * ln), int(sy + math.sin(a) * ln)),
                             max(1, int(4 * min(1.0, s * 2))))
        # the two halves of the mask, cleaved down the centre
        ms = r * 2 + 26
        msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
        _yk_mask(msurf, ms // 2, ms // 2, r, 1.0, "wail")
        gap = int(s * 150)
        drop = int(s * s * 560)                    # gravity
        for side, srcx in ((-1, 0), (1, ms // 2)):
            half = msurf.subsurface((srcx, 0, ms // 2, ms)).copy()
            half = pygame.transform.rotozoom(half, -side * s * 30, 1.0)
            surf.blit(half, half.get_rect(center=(
                int(sx + side * (ms * 0.22 + gap)), int(sy + drop))))
        for i in range(11):                        # secondary debris, falling
            a = (i / 11.0) * math.tau + (_frand(i * 5) - 0.5) * 0.5
            d = s * (220 + 240 * _frand(i * 5 + 1))
            px = sx + math.cos(a) * d
            py = sy + math.sin(a) * d - s * 30 + s * s * 460   # arc then fall
            shard = pygame.Surface((48, 48), pygame.SRCALPHA)
            col = (206, 196, 156) if i % 3 else (54, 50, 36)
            pygame.draw.polygon(shard, col, [(24, 5), (41, 36), (8, 34)])
            shard = pygame.transform.rotozoom(
                shard, s * 460 * (1 if i % 2 else -1) + i * 29,
                0.4 + 0.7 * _frand(i * 5 + 2))
            surf.blit(shard, shard.get_rect(center=(int(px), int(py))))
    # The congregation, bowed and oblivious between you and the altar --
    # the only lid on the pot, and you swing over their heads. On the
    # shatter every head comes up as one.
    lift = min(1.0, s * 2.5) if sh > 0 else 0.0
    _yank_kneeler(surf, cx - 240, int(h * 0.92), 130, t, 1, lift)
    _yank_kneeler(surf, cx + 16, int(h * 0.99), 165, t, 2, lift)
    _yank_kneeler(surf, cx + 262, int(h * 0.93), 120, t, 3, lift)
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(56):
        a = int(170 * (1 - i / 56) ** 1.6)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    surf.blit(vig, (0, 0))
    if flare > 0.01:
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((255, 244, 212, int(255 * min(1.0, flare))))
        surf.blit(fl, (0, 0))
    _carcosa_post(surf, t)


def _carcosa_tentacle(surf, px, py, ang, length, t, seed, wobble=1.0,
                      base_w=8, taper=0.0, dark=(9, 8, 11), gold=(150, 120, 50)):
    """A writhing BLACK-GOLD tendril from (px, py): a dark tapering body with a
    gold edge, curling and lashing as it reaches. `base_w` sets its girth at the
    root (big for foreground limbs); `taper` (0..1) keeps a minimum width along
    its length so it reads as a thick limb, not a thread; pass darker colours
    for out-of-focus depth."""
    n = 12
    seg = max(2.0, length / n)
    x, y, a = float(px), float(py), ang
    pts = [(x, y)]
    for i in range(n):
        a += math.sin(t * 2.4 + seed + i * 0.7) * 0.22 * wobble * (0.3 + i / n)
        x += math.cos(a) * seg
        y += math.sin(a) * seg
        pts.append((x, y))
    ip = [(int(a_), int(b_)) for a_, b_ in pts]
    for i in range(n):
        f = (n - i) / n
        wdt = max(1, int(base_w * (f * (1.0 - taper) + taper)))
        pygame.draw.line(surf, gold, ip[i], ip[i + 1], wdt + 2)   # gold edge
        pygame.draw.line(surf, dark, ip[i], ip[i + 1], wdt)       # black core
    pygame.draw.circle(surf, dark, ip[-1], max(1, int(base_w * (0.1 + taper * 0.4))))


def _carcosa_one_rift(surf, px, py, pr, op, t, seed, spread_ang=0.0,
                      ntent=5, tent=True):
    """One torn rift: the gold strike that split it, a dark tear with a hot red
    rim, and (optionally) a fan of BLACK-GOLD TENTACLES lashing out, aimed along
    `spread_ang` (the direction into the world)."""
    pr = int(pr)
    if pr < 4 or op <= 0.03:
        return
    px, py = int(px), int(py)
    pygame.draw.line(surf, (184, 150, 72), (px, py - pr * 3),
                     (int(px + _frand(seed + 5) * 14 - 7), py), max(1, int(2 * op)))
    pygame.draw.ellipse(surf, (4, 4, 7),
                        (px - pr, int(py - pr * 1.3), pr * 2, int(pr * 2.6)))
    pygame.draw.ellipse(surf, (140, 36, 26),
                        (px - pr, int(py - pr * 1.3), pr * 2, int(pr * 2.6)),
                        max(1, int(2 * op)))
    if not tent:
        return
    for k in range(ntent):
        a = spread_ang + (k - (ntent - 1) / 2.0) * 0.42
        _carcosa_tentacle(surf, px, py, a, pr * (2.4 + 2.0 * op), t,
                          seed + k * 3, base_w=max(4, int(pr * 0.22)))


def _carcosa_portal_hands(surf, w, h, cx, cy, spread, surge, t):
    """Deliberate rifts tear open across the dark -- a gold strike splits each,
    then a fan of BLACK-GOLD TENTACLES lashes through. Placed ASYMMETRICALLY and
    erupting at STAGGERED times; their reach grows with `surge` (the climax)."""
    # irregular placement: (x-frac, y-frac, eruption delay, scale)
    slots = [(-0.42, 0.12, 0.00, 1.2), (0.46, -0.04, 0.10, 1.0),
             (-0.30, 0.34, 0.22, 0.8), (0.34, 0.30, 0.30, 0.9),
             (0.50, 0.18, 0.16, 1.1), (-0.48, -0.18, 0.34, 0.7)]
    for i, (fx, fy, delay, scl) in enumerate(slots):
        op = max(0.0, min(1.0, (spread - delay) / 0.40))
        if op <= 0.03:
            continue
        px = cx + fx * w
        py = cy + fy * h
        pr = (30 + 26 * _frand(i * 7 + 2)) * scl * op
        # the tentacles lash inward + the reach surges at the climax
        sa = (math.pi if fx > 0 else 0.0) + (0.4 if fy > 0 else -0.4)
        _carcosa_one_rift(surf, px, py, pr * (1.0 + 0.6 * surge), op, t,
                          i * 7, spread_ang=sa, ntent=4 + (i % 2))


def _carcosa_wound(surf, cx, y, wd, t, inten):
    """The TEAR at ground zero -- a torn horizontal gash blazing red-gold, the
    source the column pours out of (replaces the old floating red dot). It
    pulses, a furnace at the foot of the column."""
    wd = max(6, int(wd))
    ht = max(4, int(wd * 0.30))
    pulse = 0.82 + 0.18 * math.sin(t * 5.0)
    _yk_radial(surf, cx, y, int(wd * 1.6 * pulse), (160, 46, 26),
               int(95 * inten), add=False)
    _yk_radial(surf, cx, y, int(wd * 0.85 * pulse), (210, 90, 40),
               int(110 * inten), add=False)
    _yk_radial(surf, cx, y, int(wd * 0.45), _YK_HOT, int(130 * inten), add=False)
    pygame.draw.ellipse(surf, (8, 4, 6), (cx - wd, y - ht, wd * 2, ht * 2))
    pygame.draw.ellipse(surf, (224, 160, 64),
                        (cx - wd, y - ht, wd * 2, ht * 2), max(1, int(2 + 2 * inten)))
    for k in range(7):                              # gold fissures forking out
        a = (k / 7.0) * math.tau + 0.3
        pygame.draw.line(surf, (160, 116, 46), (cx, y),
                         (int(cx + math.cos(a) * wd * (1.3 + 0.7 * inten)),
                          int(y + math.sin(a) * wd * 0.55)), 1)


def _carcosa_fg_tentacles(surf, w, h, t, grow):
    """Huge, near-black FOREGROUND tentacles sweeping in from the bottom edges
    -- out of focus, they give the catastrophe parallax and scale. `grow` drives
    them reaching further up across the frame."""
    if grow <= 0.02:
        return
    g = max(0.0, min(1.0, grow))
    fg = [((-0.02, 1.00), -math.pi * 0.40, 1, 1.15),    # bottom-left, up-right
          ((1.02, 0.98), -math.pi * 0.62, 7, 1.05),     # bottom-right, up-left
          ((0.50, 1.06), -math.pi * 0.52, 13, 0.85)]    # bottom-centre, up
    for (fx, fy), ang, seed, scl in fg:
        _carcosa_tentacle(surf, int(fx * w), int(fy * h), ang,
                          h * (0.55 + 0.45 * g) * scl, t, seed, wobble=0.5,
                          base_w=int(70 * scl * (0.6 + 0.4 * g)), taper=0.34,
                          dark=(3, 3, 5), gold=(48, 39, 18))


def draw_carcosa(surf, t):
    """rite_broken: His influence DETONATES -- a mushroom cloud of the taken.
    A flash + shockwave + shake at ground zero (the town/well); a stem of
    tendrils and faces PUNCHES upward; it billows into a cap of branching
    tendrils studded with the King's masks, the taken rising through it. Reads
    as both a dead tree and a blast. `t` = seconds since the break."""
    w, h = surf.get_size()

    def eo(x):                                   # ease-out: explosive punch
        x = max(0.0, min(1.0, x))
        return 1.0 - (1.0 - x) ** 2.3
    # --- the 3-beat arc -------------------------------------------------
    # 1. DETONATION (0-1.1): flash + shockwave, the wound tears, column punches.
    # 2. BLOOM (1.1-4.3): the stem churns up, the swarm billows, tentacles erupt.
    # 3. SURGE (4.3-7.0): it lurches toward camera -- the swarm brightens in a
    #    wave, tentacles lash to the edges, shake + light peak, then a whiteout.
    ramp = max(0.0, min(1.0, t / 0.2))
    det = max(0.0, 1.0 - t / 0.5)                 # the detonation flash
    rise = eo((t - 0.05) / 0.75)                  # stem punches up (fast)
    capg = eo((t - 0.45) / 1.9)                   # the swarm billows
    spread = eo((t - 1.1) / 2.4)                  # breach + tentacles widen
    surge = eo((t - 4.3) / 1.9)                   # the climactic lurch
    endflash = max(0.0, (t - 6.6) / 0.40)         # the final whiteout cut
    wave = max(0.0, min(1.0, (t - 0.30) / 2.4))   # gold wash over the town
    flick = 0.92 + 0.06 * math.sin(t * 9.0)
    shake = (max(0.0, 1.0 - t / 0.85)             # the initial jolt...
             + 0.45 * surge * (0.5 + 0.5 * math.sin(t * 40)))  # ...spiking at climax
    shx = int(math.sin(t * 57.0) * 12 * shake)
    shy = int(math.cos(t * 63.0) * 9 * shake)
    kx = w // 2
    gz_y = int(h * 0.86)                          # ground zero (the town/well)
    cap_y = int(h * 0.31)                          # the cap / the crown
    stem_top = int(gz_y - rise * (gz_y - cap_y))
    capR = w * 0.37 * capg * (1.0 + 0.28 * spread) * (1.0 + 0.10 * surge)

    scene = pygame.Surface((w, h))
    scene.fill((4, 4, 7))

    # Backdrop halo, growing with the cap + flaring at the surge (filled, not
    # additive: no sun).
    maxd = math.hypot(w * 0.46, h * 0.44)
    for i in range(24, 0, -1):
        f = i / 24
        rad = int(maxd * f)
        g = (0.45 + 0.55 * capg) * (1.0 + 0.30 * surge)
        col = (min(255, int(58 * (1 - f) ** 1.6 * ramp * flick * g)),
               min(255, int(46 * (1 - f) ** 1.6 * ramp * flick * g)),
               min(255, int(18 * (1 - f) ** 1.6 * ramp)))
        pygame.draw.ellipse(scene, col, (kx - rad, cap_y - int(rad * 0.7),
                                         rad * 2, int(rad * 1.4)))

    # The breach: tentacle-rifts tearing open across the dark, flanking it all.
    if spread > 0.01:
        _carcosa_portal_hands(scene, w, h, kx, cap_y, spread, surge, t)

    # Town at ground zero + the gold wave washing over it.
    _carcosa_town(scene, w, h, int(h * 0.90), t, wave)

    # THE WOUND at ground zero -- the torn gash the column pours out of.
    if spread > 0.01:
        _carcosa_wound(scene, kx, gz_y, 24 + 52 * spread, t,
                       min(1.0, spread + 0.4 * surge))

    # Detonation fireball + an expanding shockwave ring.
    fb = max(0.0, 1.0 - t / 0.7)
    if fb > 0.01:
        _yk_radial(scene, kx, gz_y, int(w * 0.10 * fb), _YK_HOT, int(120 * fb))
    rr = int(t * 760)
    if 0.02 < t < 1.4 and rr < w * 1.4:
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        a = int(150 * max(0.0, 1.0 - t / 1.4))
        pygame.draw.circle(rg, (250, 232, 150, a), (kx, gz_y), rr,
                           max(2, int(14 * (1 - t / 1.4))))
        scene.blit(rg, (0, 0))

    masks = []
    # THE STEM: a THICK, turbulent column of gold glow + dark tendrils + faces
    # churning upward, connecting the wound to the swarm (fills the frame).
    if rise > 0.02:
        col_w = max(10, int(w * 0.075 * (0.7 + 0.3 * capg)))
        gh = max(2, gz_y - stem_top + 4)
        glowcol = pygame.Surface((col_w * 2, gh), pygame.SRCALPHA)
        for xx in range(col_w * 2):
            d = abs(xx - col_w) / col_w
            pygame.draw.line(glowcol, (150, 120, 50, int(72 * (1 - d) ** 1.6)),
                             (xx, 0), (xx, gh))
        scene.blit(glowcol, (kx - col_w, stem_top))
        for j in range(7):                        # dark boiling tendrils, wider
            sx = kx + (j - 3) * int(col_w * 0.42)
            pts = [(int(sx + math.sin(t * 2.2 + s2 * 0.5 + j) * 9),
                    int(gz_y - (gz_y - stem_top) * s2 / 12)) for s2 in range(13)]
            pygame.draw.lines(scene, (9, 7, 6), False, pts, 3)
        for j in range(14):                       # faces churning UP the column
            fp = (t * 0.5 + j * 0.13 + _frand(j * 3)) % 1.0
            fy = gz_y - fp * (gz_y - stem_top)
            if fy >= stem_top - 6:
                fx = kx + (_frand(j * 5 + 1) - 0.5) * col_w * 1.8
                masks.append((fx, fy, 6 + int(8 * _frand(j * 3)), j * 5 + 2))

    # THE CAP: not one dark mass but a SWARM of the taken's little masks,
    # billowing into a broad cloud, held up by a few dark tendrils.
    if capg > 0.02:
        dome_bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(dome_bg, (6, 5, 9, int(120 * capg)),
                            (int(kx - capR * 1.15), int(cap_y - capR * 0.78),
                             int(capR * 2.3), int(capR * 1.35)))
        scene.blit(dome_bg, (0, 0))
        ntr = 8                                   # a few dark tendrils, holding it
        for i in range(ntr):
            frac = (i * 0.618034) % 1.0           # golden -> even fill, no pile
            ang = math.pi + frac * math.pi + (_frand(i * 31 + 3) - 0.5) * 0.22
            _carcosa_branch(scene, kx, cap_y, ang, capR * 0.55, 4, capg, t,
                            i * 17 + 1, masks, kx, cap_y)
        # billowing LOBES so the swarm BOILS like smoke (dense cores, wispy
        # edges) instead of an even scatter of polka-dot faces.
        nlobe = 7
        lobes = []
        for L in range(nlobe):
            u = (L + 0.5) / nlobe
            dome = 1.0 - (2 * u - 1) ** 2
            lcx = kx + (u - 0.5) * capR * 1.7
            lcy = cap_y - capR * (0.10 + 0.34 * dome) + math.sin(t * 0.6 + L) * 5
            lobes.append((lcx, lcy, 0.55 + 0.45 * _frand(L * 3 + 1)))
        nm = 150                                  # a dense swarm of LITTLE masks
        for i in range(nm):
            lcx, lcy, scl = lobes[i % nlobe]
            a = _frand(i * 9 + 6) * math.tau
            rr2 = _frand(i * 9 + 4) ** 0.7        # denser toward each lobe's core
            lx = lcx + math.cos(a) * rr2 * capR * 0.40 * scl
            ly = (lcy + math.sin(a) * rr2 * capR * 0.30 * scl
                  + math.sin(t * 0.8 + i) * 2)
            mr = int(capR * (0.02 + 0.05 * _frand(i * 9 + 5) ** 2) * (0.7 + 0.5 * scl))
            if mr >= 3:
                masks.append((lx, ly, mr, i * 7 + 3))

    # The taken surface in the TOWN too -- it isn't destroyed, it's claimed.
    if wave > 0.5:
        for i in range(3):
            tx = kx + (_frand(i * 7 + 1) - 0.5) * w * 0.7
            masks.append((tx, gz_y - 4 + _frand(i * 7 + 2) * 22,
                          7 + int(5 * _frand(i * 7 + 3)), i * 11 + 50))

    # The taken, in His own mask. A brightness WAVE rolls across them at the
    # surge -- the swarm shrieks awake. Big-to-small so they layer with depth.
    for (mx, my, mr, seed) in sorted(masks[:240], key=lambda m: -m[2]):
        vis = min(1.0, capg * 1.4 + 0.3) * (0.62 + 0.38
                                            * (0.5 + 0.5 * math.sin(t * 1.2 + seed)))
        vis += surge * (0.25 + 0.30 * math.sin(t * 6.0 - mx * 0.012))
        _yk_mask(scene, mx, my, mr, max(0.0, min(1.0, vis)),
                 _CARCOSA_FACEKINDS[seed % 4])

    # Gold embers rising through the column.
    for i in range(22):
        ex = kx + (_frand(i * 2 + 1) - 0.5) * w * (0.2 + 0.55 * capg)
        span = h + 50
        ey = (gz_y - ((t * (60 + 80 * _frand(i)) + _frand(i * 2 + 2) * span)
                      % span))
        er = 1 + int(2 * _frand(i * 3))
        pygame.draw.circle(scene, (240, 214, 140), (int(ex), int(ey)), er)

    # Edge vignette.
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(64):
        a = int(180 * (1 - i / 64) ** 1.5 * ramp)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    scene.blit(vig, (0, 0))

    # Compose: a gentle zoom-IN at the surge sells the lurch toward the camera.
    surf.fill((0, 0, 0))
    if surge > 0.01:
        z = 1.0 + 0.13 * surge
        zw, zh = int(w * z), int(h * z)
        surf.blit(pygame.transform.smoothscale(scene, (zw, zh)),
                  (shx - (zw - w) // 2, shy - (zh - h) // 2))
    else:
        surf.blit(scene, (shx, shy))

    # FOREGROUND tentacles sweep in for parallax/scale (true foreground plane);
    # present through the bloom, lashing further at the surge.
    _carcosa_fg_tentacles(surf, w, h, t, max(spread * 0.7, surge))

    if det > 0.01:                                 # the detonation flash
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((255, 244, 212, int(230 * det)))
        surf.blit(fl, (0, 0))
    if endflash > 0.01:                            # the final whiteout cut
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((255, 248, 230, int(255 * min(1.0, endflash * 1.3))))
        surf.blit(fl, (0, 0))
    _carcosa_post(surf, t)
