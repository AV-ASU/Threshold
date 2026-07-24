"""Held + firing weapon sprites: the axe and the revolver."""
import math
import random
import pygame
from constants import C_BLACK


# ---------------------------------------------------------------------------
# Player axe swing -- the one attack, gated on the splitting axe.
# ---------------------------------------------------------------------------
def _axe_swing_angle(prog, sweep):
    """The swing's three phases mapped onto prog 0..1 (2026-07 redesign,
    TODO #25: the old constant-speed sweep read as a windscreen wiper).
    WIND-UP (0..0.28): the head pulls BACK past the start side, easing
    out -- the anticipation. STRIKE (0.28..0.55): the whole arc crosses
    in this short window, cubic-fast -- the snap. FOLLOW-THROUGH
    (0.55..1): overshoot past the end, then settle back. Returns
    (angle_off_start, reach_scale, lift_px)."""
    # Retuned (2026-07 "try again"): the first cut gave the wind-up 28%
    # of a 0.34s swing -- laggy on the press, and dead frames bracketed
    # the arc. The cock is a FLICK now (~50ms), the strike is the blur,
    # and the weight lives in the long settle.
    WIND, STRIKE = 0.15, 0.45
    back = math.radians(24)               # pull-back past the start side
    over = math.radians(14)               # overshoot past the end
    if prog < WIND:
        t = prog / WIND
        e = 1 - (1 - t) * (1 - t)                     # ease-out pull
        return (-back * e, 0.78 + 0.05 * e, 4.0 * e)
    if prog < STRIKE:
        t = (prog - WIND) / (STRIKE - WIND)
        e = t * t * (3 - 2 * t)                       # smoothstep snap
        e = e * e * (3 - 2 * e)                       # sharpened: slow-FAST
        return (-back + (sweep + back + over) * e,
                0.83 + 0.27 * e, 4.0 * (1 - e))
    t = (prog - STRIKE) / (1 - STRIKE)
    if t < 0.5:                                       # the weighted settle
        e = 1 - (1 - t / 0.5) ** 2
        return (sweep + over - over * e, 1.10 - 0.18 * e, 0.0)
    # ...then RAISE back to the carry: the last half of the recover blends
    # angle + reach into draw_axe_held's exact rest pose, so the held draw
    # takes over with no pop (the old settle ended at the feet and the
    # carry snapped in level).
    u = (t - 0.5) / 0.5
    u = u * u * (3 - 2 * u)
    return (sweep + (sweep / 2 - sweep) * u,
            0.92 + (17.0 / 21.0 - 0.92) * u, 0.0)


def draw_axe_swing(surf, px, py, facing, prog):
    """The splitting axe swung through the facing hemisphere in three
    phases (wind-up / strike / follow-through, _axe_swing_angle). The
    strike window carries a bold two-ply motion smear; the wind-up
    raises the head off the shoulder. Procedural wood haft + steel
    wedge, dark-edge / lit-core line style."""
    prog = max(0.0, min(1.0, prog))
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    sweep = math.radians(150)
    start = base - sweep / 2
    off, reach, lift = _axe_swing_angle(prog, sweep)
    a = start + off
    R = 21 * reach                                # haft reach breathes
    ox = px + math.cos(base) * 3                  # pivot just ahead of hands
    oy = py + math.sin(base) * 3
    hx, hy = ox + math.cos(a) * R, oy + math.sin(a) * R - lift
    # Motion smear, STRIKE phase only: a DETACHED trail of the head's
    # recent path (never joined to the live head -- joined, it read as a
    # bent haft), bright near the head, fading behind, with the angular
    # spread clamped so it can never bow into a whip.
    if 0.15 <= prog <= 0.62:
        pts = []
        for k in range(1, 9):
            pp = prog - 0.028 * k
            if pp < 0.12:
                break
            aoff, rr, ll = _axe_swing_angle(pp, sweep)
            if off - aoff > math.radians(75):
                break
            aa = start + aoff
            pts.append((int(ox + math.cos(aa) * 21 * rr),
                        int(oy + math.sin(aa) * 21 * rr - ll)))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (222, 226, 232), False, pts[:4], 2)
            if len(pts) >= 5:
                pygame.draw.lines(surf, (142, 140, 136), False, pts[3:], 1)
    # Haft (wood), dark edge under a lit core.
    pygame.draw.line(surf, (70, 48, 28), (int(ox), int(oy)), (int(hx), int(hy)), 4)
    pygame.draw.line(surf, (128, 92, 54), (int(ox), int(oy)), (int(hx), int(hy)), 2)
    # Steel head: a wedge perpendicular at the haft end.
    pdx, pdy = -math.sin(a), math.cos(a)          # perpendicular
    ddx, ddy = math.cos(a), math.sin(a)           # along the haft
    bw, bl = 6, 8                                 # blade half-width, reach
    quad = [
        (hx + pdx * bw, hy + pdy * bw),
        (hx - pdx * bw, hy - pdy * bw),
        (hx + ddx * bl - pdx * (bw - 2), hy + ddy * bl - pdy * (bw - 2)),
        (hx + ddx * bl + pdx * (bw - 2), hy + ddy * bl + pdy * (bw - 2)),
    ]
    quad = [(int(x), int(y)) for x, y in quad]
    pygame.draw.polygon(surf, (170, 176, 186), quad)
    pygame.draw.polygon(surf, (232, 238, 246), quad, 1)
    # Bright leading edge catching the light.
    pygame.draw.line(surf, (245, 248, 252),
                     (int(hx + ddx * bl), int(hy + ddy * bl)),
                     (int(hx + pdx * bw), int(hy + pdy * bw)), 1)


def draw_axe_held(surf, px, py, facing):
    """The splitting axe carried at rest, pointed where the player faces --
    drawn whenever the axe is the active weapon and NOT mid-swing, so the
    equipped weapon always reads (matches draw_revolver_held)."""
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    ox, oy = px + math.cos(base) * 3, py + math.sin(base) * 3
    R = 17
    hx, hy = ox + math.cos(base) * R, oy + math.sin(base) * R
    # haft (wood): dark edge under a lit core
    pygame.draw.line(surf, (70, 48, 28), (int(ox), int(oy)), (int(hx), int(hy)), 4)
    pygame.draw.line(surf, (128, 92, 54), (int(ox), int(oy)), (int(hx), int(hy)), 2)
    # steel head: a wedge perpendicular at the haft end (resting, smaller than
    # the swing so it reads as 'carried' not 'striking')
    pdx, pdy = -math.sin(base), math.cos(base)
    ddx, ddy = math.cos(base), math.sin(base)
    bw, bl = 5, 7
    quad = [(hx + pdx * bw, hy + pdy * bw),
            (hx - pdx * bw, hy - pdy * bw),
            (hx + ddx * bl - pdx * (bw - 2), hy + ddy * bl - pdy * (bw - 2)),
            (hx + ddx * bl + pdx * (bw - 2), hy + ddy * bl + pdy * (bw - 2))]
    quad = [(int(x), int(y)) for x, y in quad]
    pygame.draw.polygon(surf, (150, 156, 166), quad)
    pygame.draw.polygon(surf, (214, 220, 230), quad, 1)


# ---------------------------------------------------------------------------
# Player revolver -- the sidearm, held and fired (NOT the axe arc).
# ---------------------------------------------------------------------------
def _revolver(surf, ox, oy, base, kick=0.0):
    """A small revolver pointed along `base` from the pivot (ox,oy) at the
    hands. `kick` tips the muzzle up (recoil). Dark steel barrel + cylinder
    bump + a wood grip, in the player's dark-edge / lit-core line style.
    Returns (muzzle_x, muzzle_y, barrel_angle)."""
    a = base - kick                        # recoil tips the barrel up a touch
    ax_, ay_ = math.cos(a), math.sin(a)    # along the barrel
    px_, py_ = -math.sin(a), math.cos(a)   # perpendicular (+ = down-screen)
    # wood grip: short, angled down + back from the pivot
    gx, gy = ox - ax_ * 2 + px_ * 5, oy - ay_ * 2 + py_ * 5
    pygame.draw.line(surf, (40, 28, 20), (int(ox), int(oy)), (int(gx), int(gy)), 4)
    pygame.draw.line(surf, (96, 66, 40), (int(ox), int(oy)), (int(gx), int(gy)), 2)
    # frame + cylinder bump just ahead of the hands
    cx, cy = ox + ax_ * 3, oy + ay_ * 3
    pygame.draw.circle(surf, (50, 52, 58), (int(cx), int(cy)), 3)
    pygame.draw.circle(surf, (104, 108, 116), (int(cx), int(cy)), 3, 1)
    # barrel: cylinder -> muzzle
    mx, my = ox + ax_ * 12, oy + ay_ * 12
    pygame.draw.line(surf, (30, 32, 36), (int(cx), int(cy)), (int(mx), int(my)), 4)
    pygame.draw.line(surf, (122, 126, 134), (int(cx), int(cy)), (int(mx), int(my)), 2)
    # lit top edge of the barrel
    pygame.draw.line(surf, (176, 180, 188),
                     (int(cx - px_ * 1.4), int(cy - py_ * 1.4)),
                     (int(mx - px_ * 1.4), int(my - py_ * 1.4)), 1)
    return mx, my, a


def draw_revolver_held(surf, px, py, facing):
    """The revolver carried in hand, pointed where the player faces -- drawn
    whenever the gun is the active weapon, so you can SEE you're armed."""
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    _revolver(surf, px + math.cos(base) * 4, py + math.sin(base) * 4, base)


def draw_gun_fire(surf, px, py, facing, prog):
    """The revolver firing: a brief muzzle flash + recoil (the gun slides back
    into the hands and the muzzle lifts), instead of the axe arc. `prog` 0->1
    over the shot; the flash lives in the first half."""
    prog = max(0.0, min(1.0, prog))
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    kick = (1.0 - prog) * 0.45             # muzzle lifts on recoil
    recoil = (1.0 - prog) * 3.0            # gun slides back into the hands
    ox = px + math.cos(base) * (4 - recoil)
    oy = py + math.sin(base) * (4 - recoil)
    mx, my, a = _revolver(surf, ox, oy, base, kick=kick)
    flash = max(0.0, 1.0 - prog * 2.0)     # only the first ~half of the shot
    if flash <= 0:
        return
    ax_, ay_ = math.cos(a), math.sin(a)
    tipx, tipy = mx + ax_ * 2, my + ay_ * 2
    r = 3 + flash * 5
    glow = pygame.Surface((int(r * 4), int(r * 4)), pygame.SRCALPHA)
    c = int(r * 2)
    for rr in range(int(r * 2), 0, -1):
        aa = int(130 * flash * (1 - rr / (r * 2)))
        pygame.draw.circle(glow, (255, 232, 156, aa), (c, c), rr)
    surf.blit(glow, (int(tipx - c), int(tipy - c)),
              special_flags=pygame.BLEND_RGB_ADD)
    for s in (-0.45, 0.0, 0.45):           # a few forward spark spikes
        ex, ey = tipx + math.cos(a + s) * (r + 3), tipy + math.sin(a + s) * (r + 3)
        pygame.draw.line(surf, (255, 246, 206),
                         (int(tipx), int(tipy)), (int(ex), int(ey)), 1)
