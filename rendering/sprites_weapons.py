"""Held + firing weapon sprites: the axe and the revolver."""
import math
import random
import pygame
from constants import C_BLACK

# The carried axe droops this far below the facing line (down-screen,
# mirrored with the swing's `sgn`): a dead-level carry pointed the bit
# straight down-screen, the one angle where the head has no profile.
_CARRY_TILT = math.radians(26)


# ---------------------------------------------------------------------------
# Player axe swing -- the one attack, gated on the splitting axe.
# ---------------------------------------------------------------------------
def _axe_haft(surf, ox, oy, hx, hy, lead=1):
    """The haft as a curved, tapered wood polygon (2026-07 axe redesign:
    'the design of the axe itself'). Slim under the head, swelling toward
    the grip, bowed away from the bit side near the grip the way a real
    haft sweeps back into the hands; a fawn's-foot swell closes the butt.
    `lead` names the bit side so the bow bends the other way."""
    dx, dy = hx - ox, hy - oy
    ln = max(1.0, math.hypot(dx, dy))
    px_, py_ = -dy / ln * lead, dx / ln * lead     # unit toward the bit
    bow = ln * 0.06                                 # grip-end sweep-back
    # centreline samples grip -> head, bowed off the bit side at the grip
    ts = (0.0, 0.3, 0.6, 1.0)
    widths = (2.1, 1.7, 1.45, 1.25)
    cl = []
    for t in ts:
        b = bow * (1.0 - t) * (1.0 - t)             # bow dies by the head
        cl.append((ox + dx * t - px_ * b, oy + dy * t - py_ * b))
    left = [(x + px_ * w, y + py_ * w) for (x, y), w in zip(cl, widths)]
    right = [(x - px_ * w, y - py_ * w) for (x, y), w in zip(cl, widths)]
    poly = [(int(x), int(y)) for x, y in left + right[::-1]]
    pygame.draw.polygon(surf, (112, 82, 48), poly)
    pygame.draw.polygon(surf, (58, 40, 24), poly, 1)
    # grain: a dark line chasing the bowed centreline
    pygame.draw.lines(surf, (74, 52, 30), False,
                      [(int(x), int(y)) for x, y in cl], 1)
    # fawn's-foot: the butt swells so the grip end reads held, not cut off
    bx, by = cl[0]
    pygame.draw.circle(surf, (92, 64, 38), (int(bx), int(by)), 2)


def _axe_head(surf, hx, hy, a, lead, s=1.0):
    """The splitting-axe head mounted at (hx, hy) on a haft at angle `a`.
    `lead` (+1/-1) picks which perpendicular side the BIT faces (the edge
    leads the swing). One real silhouette instead of stacked quads: a flat
    poll, a waist at the eye, the cheek flaring to a bit with a raised toe
    and a dropped heel, a concave underside, a bright honed edge with a
    slight bulge, and the haft's wedged end proud through the eye.
    Draw the haft FIRST; the head covers its end."""
    ddx, ddy = math.cos(a), math.sin(a)                  # along the haft
    pdx, pdy = -math.sin(a) * lead, math.cos(a) * lead   # toward the bit

    def P(d_, p_):
        return (int(hx + (ddx * d_ + pdx * p_) * s),
                int(hy + (ddy * d_ + pdy * p_) * s))
    # one continuous silhouette (d = along haft, p = toward the bit). The
    # bit is WIDER along the haft than the head is long, the flanks sweep
    # CONCAVE from a narrow waist out to the toe and heel (straight
    # diverging sides read as a lampshade), and a squared poll steps out
    # behind: the fire-axe profile.
    sil = [(1.9, -4.6), (2.0, -1.0), (2.2, 1.2), (2.5, 4.4),   # poll -> toe
           (5.8, 7.2),
           (-6.4, 7.2),                                        # heel
           (-2.9, 4.6), (-2.4, 1.2), (-2.0, -1.0), (-1.9, -4.6)]
    body = [P(d_, p_) for d_, p_ in sil]
    pygame.draw.polygon(surf, (104, 109, 119), body)
    # the poll a darker struck steel, so the silhouette reads asymmetric
    pygame.draw.polygon(surf, (76, 78, 86),
                        [P(1.9, -4.6), P(-1.9, -4.6), P(-2.0, -1.0), P(2.0, -1.0)])
    # the eye band where the haft mounts
    pygame.draw.line(surf, (34, 30, 26), P(-1.6, 0.2), P(1.8, 0.2), 2)
    pygame.draw.polygon(surf, (42, 44, 50), body, 1)
    if s >= 1.0:
        # one light streak down the cheek, full size only (noise smaller;
        # and never a lit band at the wide end: that is the funnel read)
        pygame.draw.line(surf, (150, 156, 168), P(1.6, 2.6), P(3.6, 5.6), 1)
    # the honed edge: bright, slightly convex (toe -> bulge -> heel); at
    # the carried scale it thins to 1px so the rim never outshines the head
    pygame.draw.lines(surf, (240, 244, 250), False,
                      [P(5.8, 7.7), P(-0.3, 8.6), P(-6.4, 7.7)],
                      2 if s >= 1.0 else 1)


def _axe_swing_angle(prog, sweep):
    """The swing's three phases mapped onto prog 0..1 (2026-07 redesign,
    the old constant-speed sweep read as a windscreen wiper).
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
    # angle + reach into draw_axe_held's exact rest pose (facing plus the
    # carry droop), so the held draw takes over with no pop (the old
    # settle ended at the feet and the carry snapped in level).
    u = (t - 0.5) / 0.5
    u = u * u * (3 - 2 * u)
    return (sweep + (sweep / 2 + _CARRY_TILT - sweep) * u,
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
    # The arc mirrors for west-ish facings (sgn) so the bit always leads
    # the travel AND settles edge-DOWN-screen into the carry: without the
    # mirror a westward carry hung edge-up and read as a bowl.
    sgn = -1 if fx < 0 else 1
    off, reach, lift = _axe_swing_angle(prog, sweep)
    a = base + sgn * (off - sweep / 2)
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
            aa = base + sgn * (aoff - sweep / 2)
            pts.append((int(ox + math.cos(aa) * 21 * rr),
                        int(oy + math.sin(aa) * 21 * rr - ll)))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (222, 226, 232), False, pts[:4], 2)
            if len(pts) >= 5:
                pygame.draw.lines(surf, (142, 140, 136), False, pts[3:], 1)
    # Wood haft under the head, bit facing the direction of travel.
    _axe_haft(surf, ox, oy, hx, hy, lead=sgn)
    _axe_head(surf, hx, hy, a, lead=sgn, s=1.0)


def draw_axe_held(surf, px, py, facing):
    """The splitting axe carried at rest, pointed where the player faces --
    drawn whenever the axe is the active weapon and NOT mid-swing, so the
    equipped weapon always reads (matches draw_revolver_held)."""
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    ox, oy = px + math.cos(base) * 3, py + math.sin(base) * 3
    # Same axe as the swing, carried: a touch smaller so it reads
    # 'in hand' not 'striking'. Same mirrored lead side as the swing so
    # the recover blend hands off without the head flipping, the edge
    # hangs down-screen, and the haft droops off the facing line so the
    # head sits in three-quarter (the level carry had no profile).
    sgn = -1 if fx < 0 else 1
    a = base + sgn * _CARRY_TILT
    R = 17
    hx, hy = ox + math.cos(a) * R, oy + math.sin(a) * R
    _axe_haft(surf, ox, oy, hx, hy, lead=sgn)
    _axe_head(surf, hx, hy, a, lead=sgn, s=0.85)


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
