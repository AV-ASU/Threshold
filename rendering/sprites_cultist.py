"""Cultist sprite: stitched hide coat + carved wooden mask."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_common import _VP_FLESH, _VP_FLESH_LO, _VP_GOR, _VP_PIT


# ---- Cultist: a stitched animal-hide coat + a carved wooden mask, one of
# six chosen per individual (by seed) so the congregation reads as "everyone
# carved their own." Directional: the mask shows front/side; from behind you
# see only the fur hood + the Sign on the hide (no face), so you can read a
# cultist's gaze and slip behind it. Near-black hide, restrained gold (only
# an eye-glint). Static detail is seeded (stable per cultist); the trudge
# rock/bob is time-driven. ----
_HIDE = (74, 56, 40); _HIDE_LO = (48, 36, 26); _HIDE2 = (92, 72, 50)
_HIDE3 = (40, 33, 28); _FUR = (122, 102, 72); _FUR_LO = (80, 64, 44)
_STITCH = (156, 144, 118); _ANTLER = (150, 138, 112)
_WOOD = (150, 128, 96); _WOOD_LO = (96, 80, 58); _CGRAIN = (70, 58, 42)
_CVOID = (12, 11, 13); _CGOLD = (255, 218, 96)


def _cult_glow(surf, x, y, r=2, a=46):
    g = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(g, (230, 186, 48, a), (r + 1, r + 1), r)
    surf.blit(g, (int(x) - r - 1, int(y) - r - 1),
              special_flags=pygame.BLEND_RGBA_ADD)


def _cult_sign(surf, cx, cy, dim=False, u=1.0):
    col = (120, 104, 44) if dim else (158, 134, 54)
    cx, cy = int(cx), int(cy)
    pygame.draw.line(surf, col, (cx, int(cy - 6 * u)), (cx, int(cy + 5 * u)), 1)
    pygame.draw.line(surf, col, (int(cx - 5 * u), int(cy - 2 * u)),
                     (int(cx + 4 * u), int(cy - 4 * u)), 1)
    pygame.draw.line(surf, col, (int(cx - 4 * u), int(cy + 3 * u)),
                     (int(cx + 5 * u), int(cy + 1 * u)), 1)


def _cult_hide_coat(surf, x, y, top, rng, lean=0, sway=0):
    """Stitched-hide coat: a near-black trapezoid of pelt patches with
    bone-thread seams, a fur collar and a ragged fur hem. `sway` swings the
    hem (cloth lag) opposite the shoulder `lean` for a lurching gait."""
    body = [(x - 9 + sway, y + 16), (x - 6 + lean, top),
            (x + 6 + lean, top), (x + 9 + sway, y + 16)]
    pygame.draw.polygon(surf, _HIDE, body)
    pygame.draw.polygon(surf, _HIDE_LO, body, 1)
    # two pelt patches in varied tone (deer tan / bear dark)
    pygame.draw.polygon(surf, _HIDE3, [(x - 6 + lean, top + 1), (x + 1, top),
                                       (x - 2, top + 9), (x - 7, top + 8)])
    pygame.draw.polygon(surf, _HIDE2, [(x + 1, top + 2), (x + 6 + lean, top + 3),
                                       (x + 8, y + 4), (x, y + 2)])
    # bone-thread seam down the front
    span = max(1, (y + 12 - top))
    for i in range(6):
        sy0 = top + 2 + i * span // 6
        pygame.draw.line(surf, _STITCH, (x - 1, sy0 - 1), (x + 1, sy0 + 1), 1)
    pygame.draw.line(surf, _HIDE2, (x - 4 + lean, top + 2), (x - 7, y + 12), 1)
    # fur collar
    for fx in range(-7, 8, 2):
        pygame.draw.line(surf, _FUR, (x + fx, top + 1), (x + fx, top - 2), 1)
    # ragged fur hem + sparse fur ticks (seeded -> stable); swings with sway
    for hx in range(-8, 9, 3):
        bx = x + hx + sway
        h = rng.randint(2, 5)
        pygame.draw.line(surf, _HIDE_LO, (bx, y + 16), (bx, y + 16 + h), 2)
        pygame.draw.line(surf, _FUR_LO, (bx, y + 16),
                         (bx, y + 16 + rng.randint(1, 2)), 1)
    for _ in range(7):
        tx = x + rng.randint(-7, 7); ty = rng.randint(top + 5, y + 10)
        pygame.draw.line(surf, _FUR_LO, (tx, ty), (tx, ty - 2), 1)


def _cult_mask(surf, cx, cy, variant, view, mdir):
    """A carved WOODEN mask -- one of six unique shapes -- GRAFTED into the
    fleshy face under the cultist's hood: carved dark eye-voids with a faint
    His-glint, and a
    dark gore seam where the wood meets flesh. Only the SHAPE is the
    cultist's own (PALLID/ANTLERED/LONGFACE/SPLIT/GRIMACE/PLANK)."""
    mx = cx + mdir * 2
    eyes = (-2, 2) if view == "front" else (mdir if mdir else 1,)

    def void_eye(ex, ey):                       # carved void + a faint His-glint
        ex, ey = int(ex), int(ey)
        pygame.draw.circle(surf, _VP_PIT, (ex, ey), 2)
        pygame.draw.circle(surf, (4, 3, 6), (ex, ey), 1)
        _cult_glow(surf, ex, ey, 2, 22)
        pygame.draw.circle(surf, (150, 120, 50), (ex, ey), 1)

    def graft_seam():                           # gore where the mask meets flesh
        gx = mx + (4 if view == "front" else mdir * 4)
        pygame.draw.line(surf, _VP_GOR, (gx, cy - 4), (gx - 1, cy + 5), 1)

    if variant == 2:        # LONGFACE -- an elongated wedge
        pts = [(mx - 4, cy - 6), (mx + 4, cy - 6), (mx + 2, cy + 4),
               (mx, cy + 8), (mx - 2, cy + 4)]
        pygame.draw.polygon(surf, _WOOD, pts)
        pygame.draw.polygon(surf, _WOOD_LO, pts, 1)
        pygame.draw.line(surf, _CGRAIN, (mx, cy - 5), (mx, cy + 6), 1)
        for ex in eyes:
            void_eye(mx + ex, cy - 2)
        graft_seam()
        return
    if variant == 5:        # PLANK -- a crude rectangle with an eye-slot
        pygame.draw.rect(surf, _WOOD, (mx - 5, cy - 6, 10, 13))
        pygame.draw.rect(surf, _WOOD_LO, (mx - 5, cy - 6, 10, 13), 1)
        pygame.draw.line(surf, _CGRAIN, (mx - 3, cy - 2), (mx + 3, cy - 2), 1)
        for ex in eyes:
            void_eye(mx + ex, cy)
        graft_seam()
        return
    # ovals: PALLID(0), ANTLERED(1), SPLIT(3), GRIMACE(4)
    if variant == 1:        # deer antlers above the mask
        for sgn in (-1, 1):
            pygame.draw.line(surf, _ANTLER, (mx + sgn * 3, cy - 6),
                             (mx + sgn * 6, cy - 13), 1)
            pygame.draw.line(surf, _ANTLER, (mx + sgn * 4, cy - 9),
                             (mx + sgn * 8, cy - 10), 1)
    mw = 5 if view == "front" else 4
    pygame.draw.ellipse(surf, _WOOD, (mx - mw, cy - 6, mw * 2, 13))
    pygame.draw.ellipse(surf, _WOOD_LO, (mx - mw, cy - 6, mw * 2, 13), 1)
    pygame.draw.line(surf, _CGRAIN, (mx - mw + 1, cy + 1), (mx + mw - 1, cy + 1), 1)
    if variant == 3:        # SPLIT -- a shatter-crack
        pygame.draw.line(surf, _CVOID, (mx, cy - 6), (mx, cy + 6), 1)
    for ex in eyes:
        if variant == 3 and ex == 0:
            continue
        void_eye(mx + ex, cy)
    if variant == 4:        # GRIMACE -- a carved frown
        pygame.draw.arc(surf, _CVOID, (mx - 3, cy + 2, 6, 5), 0.2, 2.9, 1)
    if variant == 0:        # PALLID -- the Sign on the brow
        _cult_sign(surf, mx, cy - 4, u=0.5)
    graft_seam()


_DW_MULT = {}


def _darkwood_pass(lay, seed, strength=1.0):
    """A grimy Darkwood 'brush over' for a sprite drawn on its own SRCALPHA
    layer: a touch of desaturation, a muddy multiply that crushes the lower
    body into shadow, and seeded grime speckle on the sprite's own pixels
    (stable per individual). Compounds with the frame-wide film grade.
    All passes respect the sprite's alpha, so there's no dark halo.
    `strength` (<1 = gentler) eases the desat/crush for larger sprites whose
    own form needs to stay legible."""
    w, h = lay.get_size()
    try:
        g = pygame.transform.grayscale(lay)
        g.set_alpha(int(46 * strength))
        lay.blit(g, (0, 0))
    except Exception:
        pass
    key = (w, h, round(strength, 2))
    mult = _DW_MULT.get(key)
    if mult is None:
        mult = pygame.Surface((w, h))           # opaque -> alpha preserved
        for yy in range(h):
            f = yy / max(1, h)
            b = 255 - int((41 + 122 * f * f) * strength)   # gentle top -> crushed bottom
            mult.fill((max(0, b - 6), max(0, b - 8), b), (0, yy, w, 1))
        _DW_MULT[key] = mult
    lay.blit(mult, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    rng = random.Random((seed ^ 0x9e37) & 0xffff)
    for _ in range(int(26 * strength)):
        gx, gy = rng.randint(0, w - 1), rng.randint(0, h - 1)
        px = lay.get_at((gx, gy))
        if px.a > 40:
            d = [(14, 12, 14), (34, 30, 28), (74, 66, 52)][rng.randint(0, 2)]
            lay.set_at((gx, gy), (d[0], d[1], d[2], px.a))


def _draw_cultist(surf, x, y, facing, seed, t, pose=None):
    """Draw the cultist on a private layer, brush it with the Darkwood
    grime pass, then blit it down -- so the grime/shadow read at sprite
    level, not just from the frame grade. `pose` swaps the default shamble
    for an ambient set-piece motion ('mine' = digging at the face, 'kneel'
    = the rite-hold at the altar) -- see _draw_cultist_raw."""
    LX, LY = 22, 40
    lay = pygame.Surface((44, 66), pygame.SRCALPHA)
    _draw_cultist_raw(lay, LX, LY, facing, seed, t, pose)
    _darkwood_pass(lay, seed)
    surf.blit(lay, (int(x) - LX, int(y) - LY))


def _draw_cultist_raw(surf, x, y, facing, seed, t, pose=None):
    """Assemble a hide-coat cultist with a seeded carved mask + directional
    facing. Drawn at the game's ~32px sprite scale."""
    rng = random.Random(seed & 0xffff)
    variant = (seed >> 3) % 6
    swing = 0.0
    step = 0.0          # head-lead, only the default shamble sets it nonzero
    if pose == "mine":
        # Digging at the face: the body dips and leans into each strike; the
        # pickaxe (drawn below) arcs from raised-back to struck-down on the
        # same beat. Ambient labour -- these never react to the player.
        ph = t * 2.4 + x * 0.04
        swing = max(0.0, math.sin(ph))
        lean = int(2 + swing * 3)
        hitch = int(swing * 4)
        sway = int(swing * 2)
        top = y - 8 + hitch
    elif pose == "chant":
        # Rite-chant: a slow rhythmic sway, the hem lagging; both arms lift to
        # the Sign (drawn below). Worship, oblivious to the player.
        ph = t * 1.6 + x * 0.05
        lean = int(math.sin(ph) * 3)
        sway = int(math.sin(ph - 0.6) * 3)
        top = y - 9
    elif pose == "kneel":
        # The rite-hold: lowered, still, bowed to the altar. No shamble.
        ph = 0.0
        lean = 0
        sway = 0
        top = y - 4
    elif pose == "eat":
        # Eating at a counter: the body utterly still but for one arm, a
        # slow metronomic loop from the bowl up under the mask's rim and
        # back. It does not hurry. It does not look up. Ambient tableau,
        # same contract as 'mine' -- never reacts to the player.
        ph = t * 1.5 + x * 0.03
        lean = 0
        sway = 0
        top = y - 7
    else:
        # A wrong, limping lurch: shoulders rock (lean), the body rises each
        # step (bob) and DRAGS lower on the off-step (hitch), and the ragged
        # hem swings opposite with cloth-lag (sway). A taken body shambling.
        ph = t * 3.0 + x * 0.02
        step = math.sin(ph)
        lean = int(step * 2)
        bob = int(abs(step) * 2)
        hitch = int(max(0.0, -step) * 2)
        sway = int(math.sin(ph - 0.8) * 2)
        top = y - 10 - bob + hitch
    fx, fy = facing
    if abs(fx) > abs(fy):
        view, mdir = "side", (1 if fx > 0 else -1)
    elif fy < 0:
        view, mdir = "back", 0
    else:
        view, mdir = "front", 0
    _cult_hide_coat(surf, x, y, top, rng, lean, sway)
    if pose == "mine":
        # A pickaxe swung at the face: a wooden haft + a double-pointed iron
        # head, arcing from raised-and-back (windup) to struck-down-front.
        d = mdir if mdir != 0 else 1
        sw = (math.sin(ph) + 1) / 2.0
        piv = (x + d * 2, top + 6)                       # both hands on the haft
        hxw, hyw = x - d * 5, top - 10                    # windup (raised back)
        hxs, hys = x + d * 12, top + 12                   # strike (at the face)
        hx = int(hxw + (hxs - hxw) * sw)
        hy = int(hyw + (hys - hyw) * sw)
        pygame.draw.line(surf, (62, 46, 32), piv, (hx, hy), 2)            # haft
        ddx, ddy = hx - piv[0], hy - piv[1]
        ln = max(1.0, math.hypot(ddx, ddy))
        nx, ny = -ddy / ln, ddx / ln                     # perpendicular to haft
        pygame.draw.line(surf, (150, 152, 160),                          # iron head
                         (int(hx + nx * 4), int(hy + ny * 4)),
                         (int(hx - nx * 4), int(hy - ny * 4)), 2)
    elif pose == "chant":
        # Both arms lifted to the Sign, swaying with the chant.
        lift = int((math.sin(ph) + 1) * 2)
        for sgn in (-1, 1):
            pygame.draw.line(surf, (52, 44, 34),
                             (x + sgn * 3, top + 5),
                             (x + sgn * 6 + sway, top - 7 - lift), 2)
    elif pose == "eat":
        # The off-hand holds a pale tin bowl out at waist height; the
        # spoon-hand loops from the bowl up under the mask's rim and back,
        # dwelling at each end. The only thing moving on the whole figure.
        d = mdir if mdir != 0 else 1
        u = (math.sin(ph) + 1) / 2.0                     # 0 bowl .. 1 mask
        u = u * u * (3 - 2 * u)                          # ease: dwell at ends
        bx_, by_ = x + d * 7, top + 12                   # the held bowl
        pygame.draw.line(surf, (46, 38, 30),
                         (x + d * 2, top + 9), (bx_, by_), 2)      # off arm
        pygame.draw.ellipse(surf, (168, 160, 144),
                            (bx_ - 4, by_ - 2, 9, 5))              # tin bowl
        pygame.draw.ellipse(surf, (70, 56, 40),
                            (bx_ - 2, by_ - 1, 5, 2))              # what's in it
        hx = int(bx_ + ((x + d * 1) - bx_) * u)          # spoon hand's loop
        hy = int(by_ - 1 + ((top + 2) - (by_ - 1)) * u)
        pygame.draw.line(surf, (52, 44, 34),
                         (x + d * 3, top + 6), (hx, hy), 2)        # spoon arm
        pygame.draw.line(surf, (176, 178, 184),
                         (hx, hy), (hx + d * 3, hy + 1), 2)        # the spoon
    # the masked head LEADS the lurch (tips a touch past the shoulders)
    hcx, hcy = x + lean + int(step * 1), top - 1
    pygame.draw.ellipse(surf, (32, 26, 20), (hcx - 7, hcy - 7, 14, 15))   # fur hood
    pygame.draw.arc(surf, _HIDE_LO, (hcx - 7, hcy - 7, 14, 15), 0.3, 2.9, 1)
    for a in range(20, 161, 28):                                          # fur ruff
        r = math.radians(a)
        ex, ey = hcx + math.cos(r) * 7, hcy + math.sin(r) * 7
        pygame.draw.line(surf, _FUR, (ex, ey),
                         (ex + math.cos(r) * 2, ey + math.sin(r) * 2), 1)
    if view == "back":
        # No face: a mask-tie strap across the hood + the Sign on the hide.
        pygame.draw.line(surf, _STITCH, (hcx - 5, hcy), (hcx + 5, hcy + 1), 1)
        _cult_sign(surf, x, top + 14, dim=True, u=0.7)
        if variant == 1:                                                  # antlers from behind
            for sgn in (-1, 1):
                pygame.draw.line(surf, _ANTLER, (hcx + sgn * 3, hcy - 5),
                                 (hcx + sgn * 7, hcy - 13), 1)
        return
    # A fleshy face under the hood -- the mask grafts INTO it, so the cultist
    # reads as a person He's taken, not a void.
    pygame.draw.ellipse(surf, _VP_FLESH, (hcx - 5, hcy - 6, 10, 13))
    pygame.draw.ellipse(surf, _VP_FLESH_LO, (hcx - 5, hcy - 6, 10, 13), 1)
    _cult_mask(surf, hcx, hcy, variant, view, mdir)
