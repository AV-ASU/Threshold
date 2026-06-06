"""Held + firing weapon sprites: the axe and the revolver."""
import math
import random
import pygame
from constants import C_BLACK


# ---------------------------------------------------------------------------
# Player axe swing -- the one attack, gated on the splitting axe.
# ---------------------------------------------------------------------------
def draw_axe_swing(surf, px, py, facing, prog):
    """The splitting axe swung in a flat arc through the facing
    hemisphere. `prog` (0..1) walks the head from the wind-up side
    across the front. Procedural: a wood haft + a steel head, with a
    short motion smear behind the head so the chop reads as motion."""
    prog = max(0.0, min(1.0, prog))
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    sweep = math.radians(150)
    a = base - sweep / 2 + prog * sweep          # current haft angle
    R = 21                                        # haft length
    ox = px + math.cos(base) * 3                  # pivot just ahead of hands
    oy = py + math.sin(base) * 3
    hx, hy = ox + math.cos(a) * R, oy + math.sin(a) * R
    # Motion smear: the recent path of the head, fading behind it.
    smear = []
    for k in range(7):
        aa = base - sweep / 2 + max(0.0, prog - k * 0.06) * sweep
        smear.append((int(ox + math.cos(aa) * R), int(oy + math.sin(aa) * R)))
    if len(smear) >= 2:
        pygame.draw.lines(surf, (208, 204, 196), False, smear, 1)
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
