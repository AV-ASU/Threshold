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
from rendering.sprites_player import draw_player_sprite


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


def _draw_carcosa_axe(surf, hx, hy, ang):
    """The splitting axe mid-swing: a wood handle + a steel wedge head."""
    dx, dy = math.cos(ang), math.sin(ang)
    tail = (int(hx - dx * 200), int(hy - dy * 200))
    pygame.draw.line(surf, (26, 18, 11), (int(hx), int(hy)), tail, 9)
    pygame.draw.line(surf, (76, 54, 31), (int(hx), int(hy)), tail, 6)
    px, py = -dy, dx
    blade = [(int(hx + px * 5), int(hy + py * 5)),
             (int(hx + dx * 34 + px * 30), int(hy + dy * 34 + py * 30)),
             (int(hx + dx * 34 - px * 30), int(hy + dy * 34 - py * 30)),
             (int(hx - px * 5), int(hy - py * 5))]
    pygame.draw.polygon(surf, (42, 44, 50), blade)
    pygame.draw.polygon(surf, (168, 172, 180), blade, 2)


def draw_mask_yank(surf, t):
    """The act that breaks the rite (NARRATIVE §6): you SHATTER the Pallid
    Mask with your splitting axe -- the catastrophic 'tear it down'. Dread
    stillness, the axe swings in, the mask bursts into shards and the Sign
    bleeds, whiting out into the blast. `t` = seconds into the act (~3s)."""
    w, h = surf.get_size()
    cx, cy = w // 2, int(h * 0.46)
    impact = 1.6
    sh = max(0.0, t - impact)                      # time since the blow lands
    flare = max(0.0, (t - 2.55) / 0.45)
    shake = min(1.0, sh / 0.3) if sh > 0 else 0.04 * (t / impact)
    shx = int(math.sin(t * 64) * (2 + 20 * shake))
    shy = int(math.cos(t * 70) * (1 + 12 * shake))
    sx, sy = cx + shx, cy + shy

    surf.fill((9, 8, 11))
    for i in range(7):                             # cellar-wall stone seams
        yy = int(h * (0.12 + 0.12 * i)) + (i % 2) * 6
        pygame.draw.line(surf, (16, 14, 18), (0, yy), (w, yy + 4), 1)
    # The daubed Yellow Sign + the dark socket the mask sits in.
    glyph = [(sx, sy - 96), (sx - 9, sy - 32), (sx - 44, sy - 12),
             (sx - 15, sy + 20), (sx - 28, sy + 76), (sx + 7, sy + 32),
             (sx + 42, sy + 64), (sx + 19, sy + 9), (sx + 50, sy - 26),
             (sx + 11, sy - 28)]
    pygame.draw.lines(surf, (70, 56, 24), False,
                      [(int(a), int(b)) for a, b in glyph], 2)
    pygame.draw.ellipse(surf, (5, 4, 7), (sx - 60, sy - 78, 120, 156))
    hitstop = 0.07                                 # frozen frames on contact
    if sh <= hitstop:
        # Mask whole. Tremor builds; the axe rears back, HOLDS, then drops.
        trem = int(math.sin(t * 36) * 2 * (t / impact))
        # Swing timeline: enter+cock [0.55,1.05] -> anticipation HOLD
        # [1.05,1.35] -> fast accel drop [1.35,impact].
        cocked = (sx + 230, sy - 250)              # axe held high, off upper-right
        contact = (sx + 24, sy - 18)
        if t < 1.05:
            p = max(0.0, (t - 0.55) / 0.5)
            ax = sx + 470 - (470 - 230) * p        # slide in from off-screen
            ay = sy - 250
            hxx, hyy = int(ax), int(ay)
        elif t < 1.35:
            hxx, hyy = cocked                      # the held beat (dread)
            hyy += int(math.sin(t * 30) * 2)       # a small quiver
        else:
            sw = ((t - 1.35) / (impact - 1.35)) ** 2.4   # hard accelerating drop
            hxx = int(cocked[0] + (contact[0] - cocked[0]) * sw)
            hyy = int(cocked[1] + (contact[1] - cocked[1]) * sw)
        ang = math.atan2(contact[1] - cocked[1], contact[0] - cocked[0])
        if sh <= 0:
            ms = 130
            msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
            _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
            surf.blit(msurf, msurf.get_rect(center=(sx + trem, sy)))
            _draw_carcosa_axe(surf, hxx, hyy, ang)
        else:
            # CONTACT held: axe buried, a hairline crack lights, white spark.
            ms = 130
            msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
            _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
            surf.blit(msurf, msurf.get_rect(center=(sx, sy)))
            crk = [(sx + (_frand(c) - 0.5) * 16, sy - 70 + c * 24)
                   for c in range(7)]
            pygame.draw.lines(surf, (255, 248, 224), False,
                              [(int(a), int(b)) for a, b in crk], 2)
            _draw_carcosa_axe(surf, contact[0], contact[1], ang)
            _yk_radial(surf, contact[0], contact[1], 26, (255, 248, 224), 220)
    else:
        # SHATTERED: the mask SPLITS down the strike line into two halves that
        # fall apart under gravity, gore bursts from the Sign, debris rains.
        s = sh - hitstop
        _yk_radial(surf, sx, sy, int(50 + 80 * shake), (150, 30, 22),
                   int(28 + 46 * shake))
        for i in range(5):                         # red bleeding rakes
            a = (i / 5.0) * math.tau + 0.4
            ln = 60 + 200 * min(1.0, s * 1.4)
            pygame.draw.line(surf, (110, 26, 18), (sx, sy),
                             (int(sx + math.cos(a) * ln), int(sy + math.sin(a) * ln)),
                             max(1, int(3 * min(1.0, s * 2))))
        # the two halves of the mask, cleaved down the centre
        ms = 130
        msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
        _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
        gap = int(s * 90)
        drop = int(s * s * 520)                    # gravity
        for side, srcx in ((-1, 0), (1, ms // 2)):
            half = msurf.subsurface((srcx, 0, ms // 2, ms)).copy()
            half = pygame.transform.rotozoom(half, -side * s * 30, 1.0)
            surf.blit(half, half.get_rect(center=(
                int(sx + side * (ms * 0.22 + gap)), int(sy + drop))))
        for i in range(9):                         # secondary debris, falling
            a = (i / 9.0) * math.tau + (_frand(i * 5) - 0.5) * 0.5
            d = s * (180 + 180 * _frand(i * 5 + 1))
            px = sx + math.cos(a) * d
            py = sy + math.sin(a) * d - s * 30 + s * s * 460   # arc then fall
            shard = pygame.Surface((40, 40), pygame.SRCALPHA)
            col = (206, 196, 156) if i % 3 else (54, 50, 36)
            pygame.draw.polygon(shard, col, [(20, 4), (34, 30), (7, 28)])
            shard = pygame.transform.rotozoom(
                shard, s * 460 * (1 if i % 2 else -1) + i * 29,
                0.4 + 0.6 * _frand(i * 5 + 2))
            surf.blit(shard, shard.get_rect(center=(int(px), int(py))))
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


def draw_carcosa(surf, t, mode="spread"):
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


# ---------------------------------------------------------------------------
# The SEAL ending -- the PI and the Mask go THROUGH the door, and the frame
# drinks them both down (NARRATIVE §6). Three drawn acts, then black:
#   1. THE DRINK [0, SEAL_T_WARP): the PI, back to us, walks up into the
#      waiting doorway carrying the keystone; the frame takes them at the
#      threshold, and the gold light drains down after them -- the
#      rite-dream run in reverse (the eyes close, the glow pulls inward)
#      while the way he came grinds shut overhead in three receding jolts.
#   2. THE WARP [SEAL_T_WARP, SEAL_T_MAP): the inversion of the Carcosa
#      detonation -- everything the cult bent is pulled INTO a contracting
#      point, the taken's masks spiralling inward, and the place winks out.
#   3. THE MAP [SEAL_T_MAP, SEAL_T_BLACK): the PI's county map; the roads
#      grow together across where the town stood, the marks and the name
#      fade unwritten. Brimley simply was.
# The act boundaries mirror the seal_threshold script durations in
# systems/game.py (_ENDING_SCRIPTS): lines 1-2 drive act 1, line 3 act 2,
# lines 4-5 act 3; ui/cutscenes.py rides the lines under the visuals as
# captions and lets the last two lines fall through to plain black.
# ---------------------------------------------------------------------------
SEAL_T_WARP = 6.0
SEAL_T_MAP = 9.6
SEAL_T_BLACK = 16.6
SEAL_CLOSE_TS = (3.2, 4.3, 5.4)   # the long fall / the Works / the grove fold


def _seal_clamp(x):
    return max(0.0, min(1.0, x))


def _seal_frame(scene, left, top, dw, dh, post, glow, pulse):
    """The Threshold's dried-oak frame (the dream door made real): two
    too-slight uprights + the lintel, grain + dry cracks, with a warm rim
    where the inside light still catches the jamb."""
    base, grain, splitc = (104, 74, 46), (78, 52, 30), (44, 28, 16)
    rng = random.Random(7)
    for rx, rw, rh, ry in ((left, post, dh, top),
                           (left + dw - post, post, dh, top)):
        pygame.draw.rect(scene, base, (rx, ry, rw, rh))
        for gi in range(3):
            gx = rx + int((gi + 0.5) / 3 * rw) + rng.randint(-1, 1)
            pygame.draw.line(scene, grain, (gx, ry + 2), (gx, ry + rh - 2), 1)
        for _ in range(2):
            cxx = rx + rng.randint(1, max(1, rw - 1))
            y0 = ry + rng.randint(4, max(5, rh // 2))
            y1 = min(ry + rh - 2, y0 + rng.randint(rh // 5, rh // 2))
            pygame.draw.line(scene, splitc, (cxx, y0),
                             (cxx + rng.randint(-1, 1), y1), 1)
    pygame.draw.rect(scene, base, (left, top, dw, post))
    for gi in range(int(dw / 14)):
        gx = left + gi * 14 + 6
        pygame.draw.line(scene, grain, (gx, top + 2), (gx, top + post - 2), 1)
    if glow > 0.01:
        rim = (min(255, int(250 * glow * pulse)),
               min(255, int(206 * glow * pulse)),
               min(255, int(120 * glow * pulse)))
        ox, oy = left + post, top + post
        ow = dw - 2 * post
        bot = top + dh
        pygame.draw.line(scene, rim, (ox, oy), (ox, bot - 1), 1)
        pygame.draw.line(scene, rim, (ox + ow - 1, oy),
                         (ox + ow - 1, bot - 1), 1)
        pygame.draw.line(scene, rim, (ox, oy), (ox + ow - 1, oy), 1)


def _seal_drink(surf, w, h, t):
    """Act 1: the PI and the Mask go THROUGH the door. The dream doorway
    stands waiting in the dark; he walks up into the light carrying the
    keystone, the frame takes them both at the threshold, and the glow
    drains down after them -- the dream run in reverse (the eyes close
    and stay shut) while the way he came seals overhead slab by slab."""
    wp = _seal_clamp(t / 2.7)                      # the walk to the frame
    cross = _seal_clamp((t - 2.7) / 0.6)           # stepping through
    drink = _seal_clamp((t - 3.0) / 2.9)           # the light going with him
    flare = _seal_clamp(1.0 - abs(t - 3.0) / 0.4)  # the frame takes them
    scene = pygame.Surface((w, h))
    scene.fill((7, 6, 9))

    cx = w // 2
    dh = int(h * 0.55)
    dw = int(dh * 0.48)
    post = max(5, dw // 8)
    top = int(h * 0.50 - dh / 2)
    left = cx - dw // 2
    bot = top + dh
    ox, oy = left + post, top + post
    ow, oh = dw - 2 * post, dh - post

    pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * (1.7 - 1.1 * drink)))
    glow = min(1.4, (1.0 - 0.92 * drink) * pulse + 0.9 * flare)

    if ow > 6 and oh > 6:
        inner = pygame.Surface((ow, oh), pygame.SRCALPHA)
        # The glow pools at the door's base where he enters, then recedes
        # DOWN into the threshold after him -- swallowed, not spent.
        fx = ow / 2
        fy = oh * (0.80 + 0.16 * drink)
        steps = 30
        maxr = max(ow, oh) * 0.62 * (1.0 - 0.45 * drink)
        for s_i in range(steps):
            f = s_i / (steps - 1)
            rr = maxr * (1.0 - f)
            a = max(0, min(255, int((6 + 168 * f * f)
                                    * (0.30 + 0.70 * glow))))
            col = (246, 200 + int(38 * f), 70 + int(46 * f), a)
            rect = pygame.Rect(0, 0, max(2, int(rr * 1.5)),
                               max(2, int(rr * 1.62)))
            rect.center = (int(fx), int(fy))
            pygame.draw.ellipse(inner, col, rect)
        # Inflow: motes of the light draining down after him.
        if drink > 0.02:
            for i in range(14):
                u = _frand(i * 7 + 1)
                sx0 = ow * (0.12 + 0.76 * _frand(i * 7 + 2))
                sy0 = oh * (0.45 + 0.50 * u)
                p = (t * (0.5 + 0.5 * u) + _frand(i * 7 + 3)) % 1.0
                px = sx0 + (fx - sx0) * p
                py = sy0 + (fy - sy0) * p
                a = int(150 * p * drink * (1.0 - 0.6 * drink))
                if a > 4:
                    pygame.draw.circle(inner, (250, 226, 140, a),
                                       (int(px), int(py)), 1 + int(p * 2))
        # The eyes close, staggered, and stay shut.
        for ei, (ex, ey, off) in enumerate(((0.36, 0.40, 0.0),
                                            (0.62, 0.54, 1.9),
                                            (0.50, 0.30, 3.7))):
            shut = _seal_clamp((t - 1.2 - ei * 0.9) / 1.1)
            openness = max(0.0, (0.5 + 0.5 * math.sin(t * 2.6 + off * 3))
                           * (1.0 - shut))
            a = int(150 * (0.4 + 0.6 * glow) * (1.0 - shut))
            if a <= 4:
                continue
            exx, eyy = ex * ow, ey * oh
            ew = max(2, int(0.045 * ow))
            eh = max(1, int(ew * 0.62 * max(0.08, openness)))
            gap = ew * 1.5
            for sgn in (-1, 1):
                er = pygame.Rect(0, 0, ew, eh)
                er.center = (int(exx + sgn * gap), int(eyy))
                pygame.draw.ellipse(inner, (230, 222, 190, a), er)
        scene.blit(inner, (ox, oy))

    _seal_frame(scene, left, top, dw, dh, post, 1.0 - 0.9 * drink, pulse)

    # THE PI, back to us, walking up into the opening with the Mask at his
    # side, its gold leaking past the coat. The frame takes him at the
    # threshold: he fades INTO the light, not out of frame.
    if cross < 0.999:
        k = 3.0 - 1.1 * wp                         # walks away; recedes
        feet_y = h * 0.93 + (bot - 4 - h * 0.93) * wp
        card = pygame.Surface((48, 56), pygame.SRCALPHA)
        draw_player_sprite(card, 24, 44, (0, -1), t * 8.0, view="back")
        for rr_i, aa in ((7, 40), (5, 70), (3, 120)):  # the Mask's glow
            pygame.draw.circle(card, (250, 214, 120, aa), (33, 32), rr_i)
        pygame.draw.circle(card, (236, 228, 206, 210), (33, 32), 2)
        spr = pygame.transform.scale(card, (int(48 * k), int(56 * k)))
        spr.set_alpha(int(255 * (1.0 - cross)))
        scene.blit(spr, (int(cx - 24 * k), int(feet_y - 44 * k)))

    # The way you came, grinding shut overhead: three slabs drop across the
    # dark above the frame (the long fall, the Works, then the grove fold,
    # whose light snuffs gold as it thins to nothing).
    bh = int(h * 0.085)
    for i, ct in enumerate(SEAL_CLOSE_TS):
        prog = _seal_clamp((t - ct) / 0.45)
        if prog <= 0.0:
            continue
        prog = 1.0 - (1.0 - prog) ** 2.4
        y = int(-bh * 1.5 + prog * (i * bh + bh * 1.5))
        slab = pygame.Rect(0, min(y, 0) - 2, w,
                           y + bh + 2 - (min(y, 0) - 2))
        pygame.draw.rect(scene, (31, 28, 35), slab)
        for k in range(5):                         # stone seams in the slab
            sx2 = int((k + 0.5) / 5 * w + _frand(i * 9 + k) * 40 - 20)
            pygame.draw.line(scene, (20, 18, 24), (sx2, slab.top),
                             (sx2 + 8, slab.bottom), 1)
        edge = (58, 53, 62)
        if i == 2:
            gl = 1.0 - prog
            edge = (58 + int(170 * gl), 53 + int(140 * gl),
                    62 + int(50 * gl))
        pygame.draw.line(scene, edge, (0, y + bh), (w, y + bh), 2)

    # A jolt on each closure; the view recedes a step from the door each
    # time -- buried by elevation.
    shake = 0.0
    rec = 0.0
    for ct in SEAL_CLOSE_TS:
        if t > ct:
            shake = max(shake, max(0.0, 1.0 - (t - ct) / 0.35))
            rec += 0.030 * _seal_clamp((t - ct) / 0.45)
    shx = int(math.sin(t * 61) * 7 * shake)
    shy = int(math.cos(t * 57) * 5 * shake)
    surf.fill((0, 0, 0))
    if rec > 0.001:
        z = 1.0 - rec
        zw, zh = int(w * z), int(h * z)
        surf.blit(pygame.transform.smoothscale(scene, (zw, zh)),
                  (shx + (w - zw) // 2, shy + (h - zh) // 2))
    else:
        surf.blit(scene, (shx, shy))
    _carcosa_post(surf, t)


def _seal_warp(surf, w, h, wt):
    """Act 2: the warp. The inversion of the Carcosa detonation -- every
    acre the cult bent is pulled INTO the door's point, the doorframe and
    the taken's masks spiralling inward with it, and the place winks out."""
    p = _seal_clamp(wt / 3.6)
    pe = p * p * (3 - 2 * p)                       # smoothstep pull
    cx, cy = w // 2, int(h * 0.50)
    scene = pygame.Surface((w, h))
    scene.fill((4, 4, 7))

    # The gathering point brightens as it takes everything in (filled, not
    # additive: no sun -- same rule as the blast).
    core = 0.25 + 0.75 * pe
    maxd = math.hypot(w * 0.46, h * 0.44) * (1.0 - 0.5 * pe)
    for i in range(20, 0, -1):
        f = i / 20
        rad = max(2, int(maxd * f))
        col = (min(255, int(70 * (1 - f) ** 1.5 * core)),
               min(255, int(56 * (1 - f) ** 1.5 * core)),
               min(255, int(22 * (1 - f) ** 1.5 * core)))
        pygame.draw.ellipse(scene, col, (cx - rad, cy - int(rad * 0.7),
                                         rad * 2, int(rad * 1.4)))

    # The reverse shockwave: a ring CONTRACTING onto the point.
    rr = int(math.hypot(w, h) * 0.55 * (1.0 - pe))
    if rr > 4:
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        a = int(120 * (0.35 + 0.65 * pe))
        pygame.draw.circle(rg, (250, 232, 150, a), (cx, cy), rr,
                           max(2, int(10 * (1.0 - pe))))
        scene.blit(rg, (0, 0))

    # The doorframe itself goes with it: pulled in, twisting as it shrinks.
    if pe < 0.985:
        dh2 = int(h * 0.45)
        dw2 = int(dh2 * 0.48)
        post2 = max(4, dw2 // 8)
        card = pygame.Surface((dw2, dh2), pygame.SRCALPHA)
        _seal_frame(card, 0, 0, dw2, dh2, post2, 0.0, 0.0)
        card = pygame.transform.rotozoom(card, pe * 75,
                                         max(0.03, 1.0 - 0.97 * pe))
        scene.blit(card, card.get_rect(center=(cx, cy)))

    # The taken spiral in with it.
    masks = []
    for i in range(40):
        u = _frand(i * 9 + 1)
        q = _seal_clamp(pe * 1.3 - u * 0.3)
        rad = (0.12 + 0.42 * _frand(i * 9 + 2)) * w * (1.0 - q)
        ang = u * math.tau + q * 2.8 + wt * 0.15
        mxx = cx + math.cos(ang) * rad
        myy = cy + math.sin(ang) * rad * 0.78
        mr = int((4 + 9 * _frand(i * 9 + 3)) * (1.0 - 0.65 * q))
        if mr >= 3 and rad > 8:
            masks.append((mxx, myy, mr, i * 7 + 3))
    for (mxx, myy, mr, seed) in sorted(masks, key=lambda m: -m[2]):
        vis = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(wt * 2.0 + seed))
        _yk_mask(scene, mxx, myy, mr, vis, _CARCOSA_FACEKINDS[seed % 4])

    # Gold streaks wound along the pull.
    for k in range(9):
        a0 = k * math.tau / 9 - wt * 0.9
        pts = []
        for s_i in range(7):
            f = s_i / 6.0
            rad = (0.55 - 0.50 * f) * w * (1.0 - pe) + 6
            ang = a0 + f * 1.8
            pts.append((int(cx + math.cos(ang) * rad),
                        int(cy + math.sin(ang) * rad * 0.78)))
        col = (220, 196, 120) if k % 2 else (160, 130, 60)
        pygame.draw.lines(scene, col, False, pts, 1)

    # Shake grows with the pull; then the wink-out -- a flash CUT to dark
    # (the map act fades up from the black it leaves behind).
    shake = 0.25 + 0.55 * pe
    shx = int(math.sin(wt * 47) * 6 * shake)
    shy = int(math.cos(wt * 53) * 4 * shake)
    surf.fill((0, 0, 0))
    surf.blit(scene, (shx, shy))
    fl = min(_seal_clamp((wt - 3.18) / 0.22), _seal_clamp((3.6 - wt) / 0.12))
    if fl > 0.01:
        fs2 = pygame.Surface((w, h), pygame.SRCALPHA)
        fs2.fill((255, 244, 212, int(235 * fl)))
        surf.blit(fs2, (0, 0))
    _carcosa_post(surf, wt + SEAL_T_WARP)


_SEAL_LABEL_SURF = None


def _seal_town_label():
    """'BRIMLEY' in plain map ink, cached. Returns a blank where the font
    system is unavailable (headless safety)."""
    global _SEAL_LABEL_SURF
    if _SEAL_LABEL_SURF is None:
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            _SEAL_LABEL_SURF = pygame.font.Font(None, 26).render(
                "BRIMLEY", True, (44, 37, 30))
        except Exception:
            _SEAL_LABEL_SURF = pygame.Surface((1, 1), pygame.SRCALPHA)
    return _SEAL_LABEL_SURF


def _seal_map(surf, w, h, mt):
    """Act 3: the county map heals. The town's marks and name fade off the
    paper first; then the roads and the river grow together across where it
    stood, a gold seam dying along the join. Brimley simply was."""
    fade = min(_seal_clamp(mt / 0.6),
               _seal_clamp((SEAL_T_BLACK - SEAL_T_MAP - mt) / 0.8))
    hp = _seal_clamp((mt - 1.2) / 4.2)
    hp = hp * hp * (3 - 2 * hp)
    cx, cy = int(w * 0.52), int(h * 0.48)
    R0 = min(w, h) * 0.30
    void = R0 * (1.0 - hp)

    scene = pygame.Surface((w, h))
    scene.fill((118, 108, 86))                     # lamplit paper
    for i in range(10):                            # blotches + foxing
        bx = int(_frand(i * 5 + 1) * w)
        by = int(_frand(i * 5 + 2) * h)
        br = int(30 + 70 * _frand(i * 5 + 3))
        col = (124, 114, 92) if i % 2 else (110, 100, 80)
        pygame.draw.ellipse(scene, col, (bx - br, by - int(br * 0.6),
                                         br * 2, int(br * 1.2)))
    pygame.draw.line(scene, (100, 92, 74), (int(w * 0.33), 0),
                     (int(w * 0.30), h), 2)        # old fold creases
    pygame.draw.line(scene, (100, 92, 74), (0, int(h * 0.62)),
                     (w, int(h * 0.66)), 2)

    def dist(px, py):
        return math.hypot(px - cx, py - cy)

    def ink_path(pts, col, width):
        # Draw the authored crossing, skipping segments still inside the
        # unhealed void -- the dead ends creep toward each other and meet.
        for a, b in zip(pts, pts[1:]):
            if dist(*a) < void or dist(*b) < void:
                continue
            pygame.draw.line(scene, col, (int(a[0]), int(a[1])),
                             (int(b[0]), int(b[1])), width)

    for (x0, y0, x1, y1, amp) in ((0, h * 0.30, w, h * 0.55, 0.04),
                                  (w * 0.18, 0, w * 0.70, h, -0.05),
                                  (0, h * 0.78, w, h * 0.20, 0.03)):
        pts = []
        for s_i in range(25):
            f = s_i / 24.0
            pts.append((x0 + (x1 - x0) * f,
                        y0 + (y1 - y0) * f + math.sin(f * 6.0) * h * amp))
        ink_path(pts, (54, 48, 40), 3)
    river = []
    for s_i in range(30):
        f = s_i / 29.0
        river.append((w * (0.92 - 0.80 * f),
                      h * (0.06 + 0.90 * f) + math.sin(f * 9.0) * h * 0.03))
    ink_path(river, (62, 68, 74), 4)
    for i in range(120):                           # field hatching creeps in
        hx = _frand(i * 3 + 1) * w
        hy = _frand(i * 3 + 2) * h
        if dist(hx, hy) < void + 6 or _frand(i * 3 + 3) < 0.45:
            continue
        pygame.draw.line(scene, (104, 96, 78), (int(hx), int(hy)),
                         (int(hx + 5), int(hy - 2)), 1)

    # The town, fading off the record before the land closes over it.
    tf = 1.0 - _seal_clamp((mt - 0.7) / 2.2)
    if tf > 0.01:
        layer = pygame.Surface((w, h), pygame.SRCALPHA)
        a = int(255 * tf)
        ink = (40, 34, 27, a)
        for i in range(7):                         # the blocks of the town
            bx2 = cx + int((_frand(i * 11 + 1) - 0.5) * R0 * 1.1)
            by2 = cy + int((_frand(i * 11 + 2) - 0.5) * R0 * 0.8)
            pygame.draw.rect(layer, ink, (bx2, by2, 9, 7), 1)
        pygame.draw.line(layer, ink, (cx - 14, cy - 18), (cx - 14, cy - 6), 2)
        pygame.draw.line(layer, ink, (cx - 18, cy - 14), (cx - 10, cy - 14), 2)
        pygame.draw.circle(layer, ink, (cx + 12, cy + 8), 4, 1)  # the well
        lab = _seal_town_label()
        if lab.get_width() > 2:
            ls = lab.copy()
            ls.set_alpha(a)
            layer.blit(ls, (cx - lab.get_width() // 2, cy + int(R0 * 0.45)))
        scene.blit(layer, (0, 0))

    # A gold seam dying along the join as the edges grow together.
    seam = math.sin(math.pi * hp)
    if 0.02 < hp < 0.999 and seam > 0.02:
        sl = pygame.Surface((w, h), pygame.SRCALPHA)
        for k in range(30):
            ang = k * math.tau / 30 + mt * 0.4
            px = cx + math.cos(ang) * void
            py = cy + math.sin(ang) * void * 0.9
            a = int(80 * seam * (0.5 + 0.5 * math.sin(mt * 3 + k)))
            if a > 3:
                pygame.draw.circle(sl, (235, 200, 110, a),
                                   (int(px), int(py)), 2)
        scene.blit(sl, (0, 0))

    surf.fill((0, 0, 0))
    if fade < 0.999:
        scene.set_alpha(int(255 * fade))
    surf.blit(scene, (0, 0))
    _carcosa_post(surf, mt + SEAL_T_MAP, tint=(230, 222, 200), cold=(0, 5, 7))


def draw_threshold_seal(surf, t):
    """The SEAL ending cutscene (walking through the Threshold doorframe
    with the Mask): the drink, the warp into Carcosa, the map healing over.
    `t` = seconds since the ending began; past SEAL_T_BLACK it holds black
    for the closing lines."""
    w, h = surf.get_size()
    if t < SEAL_T_WARP:
        _seal_drink(surf, w, h, t)
    elif t < SEAL_T_MAP:
        _seal_warp(surf, w, h, t - SEAL_T_WARP)
    elif t < SEAL_T_BLACK:
        _seal_map(surf, w, h, t - SEAL_T_MAP)
    else:
        surf.fill((0, 0, 0))
