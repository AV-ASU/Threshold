"""Character sprites: NPCs, enemies, the player."""
import math
import random
import pygame
from constants import C_BLACK

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


def _cult_eye(surf, x, y):
    pygame.draw.circle(surf, _CVOID, (int(x), int(y)), 1)
    _cult_glow(surf, x, y, 2, 46)
    pygame.draw.circle(surf, _CGOLD, (int(x), int(y)), 1)


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
    fleshy face under the cultist's hood, in the same body-horror register as
    the curse-priest: carved dark eye-voids with a faint His-glint, and a
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
    own form needs to stay legible (the curse-priest)."""
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


def _draw_cultist(surf, x, y, facing, seed, t):
    """Draw the cultist on a private layer, brush it with the Darkwood
    grime pass, then blit it down -- so the grime/shadow read at sprite
    level, not just from the frame grade."""
    LX, LY = 22, 40
    lay = pygame.Surface((44, 66), pygame.SRCALPHA)
    _draw_cultist_raw(lay, LX, LY, facing, seed, t)
    _darkwood_pass(lay, seed)
    surf.blit(lay, (int(x) - LX, int(y) - LY))


def _draw_cultist_raw(surf, x, y, facing, seed, t):
    """Assemble a hide-coat cultist with a seeded carved mask + directional
    facing. Drawn at the game's ~32px sprite scale."""
    rng = random.Random(seed & 0xffff)
    variant = (seed >> 3) % 6
    # A wrong, limping lurch: shoulders rock (lean), the body rises each step
    # (bob) and DRAGS lower on the off-step (hitch), and the ragged hem swings
    # opposite with cloth-lag (sway). Reads as a taken body shambling.
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
    # A fleshy face under the hood -- the mask grafts INTO it (same as the
    # curse-priest), so the cultist reads as a person He's taken, not a void.
    pygame.draw.ellipse(surf, _VP_FLESH, (hcx - 5, hcy - 6, 10, 13))
    pygame.draw.ellipse(surf, _VP_FLESH_LO, (hcx - 5, hcy - 6, 10, 13), 1)
    _cult_mask(surf, hcx, hcy, variant, view, mdir)


_VP_HIDE = (58, 50, 42); _VP_LO = (30, 26, 23); _VP_HI = (92, 82, 64)
_VP_PALE = (222, 212, 186); _VP_PALE_LO = (150, 142, 120); _VP_PIT = (18, 14, 16)
_VP_GT = (196, 150, 42); _VP_GHI = (236, 204, 64)
# Muddy, desaturated -- gore is a dark red-brown (implied, never bright).
_VP_FLESH = (150, 134, 124); _VP_FLESH_LO = (104, 92, 84)
_VP_MOUTH = (28, 16, 16); _VP_TEETH = (150, 142, 124)
_VP_GOR = (84, 46, 40); _VP_GOR_LO = (54, 30, 28)


def _scream_face(surf, cx, cy, r=3, gold=False):
    """A small fused, screaming face -- one of the people He took, crying out
    from inside the torn body."""
    cx, cy = int(cx), int(cy)
    pygame.draw.ellipse(surf, _VP_FLESH, (cx - r, cy - r, 2 * r, 2 * r + 1))
    pygame.draw.ellipse(surf, _VP_FLESH_LO, (cx - r, cy - r, 2 * r, 2 * r + 1), 1)
    pygame.draw.circle(surf, _VP_PIT, (cx - r // 2 - 1, cy - 1), 1)
    pygame.draw.circle(surf, _VP_PIT, (cx + r // 2, cy - 1), 1)
    pygame.draw.ellipse(surf, _VP_MOUTH, (cx - 1, cy + 1, 3, 3))   # open mouth
    if gold:
        _cult_glow(surf, cx, cy + 1, 2, 44)


def _curse_bloom(lay, bx, by, t, curse):
    """His light is only a faint UNDERLIGHT now -- the flesh leads. A dim glow
    welling deep in the wound, no bright seam, no sparks. Drawn after the
    grime pass so the hint survives, but kept very low so the gore/flesh of
    the writhing wound is what reads, not the gold."""
    bx, by = int(bx), int(by)
    for gy in range(by - 4, by + 8, 4):
        _cult_glow(lay, bx, gy, 2, int(6 + curse * 16))


def _pallid_mask(surf, sx, mcy, view, mdir, bloom):
    """His Pallid Mask -- a clear, carved pale face -- grafted onto the
    priest's head. Reads as a mask first: a defined pale oval, two sunken
    eye-voids, a carved bone-lit edge, a hairline shatter-crack, a blank
    mouth. The graft (the wound where it meets flesh) is the secondary note:
    a dark gore seam down one side and the human socket gone dark. One void
    kindles dim gold from behind as the curse casts."""
    # The flesh/bone head it's grafted onto (shows at the jaw + one side).
    pygame.draw.ellipse(surf, _VP_FLESH, (sx - 7, mcy - 8, 14, 17))
    pygame.draw.ellipse(surf, _VP_FLESH_LO, (sx - 7, mcy - 8, 14, 17), 1)
    # The mask plate -- a clear pale carved face.
    if view == "front":
        mr = pygame.Rect(sx - 6, mcy - 7, 12, 15)
        evs = [(sx - 3, mcy - 1), (sx + 3, mcy - 1)]
    else:                                            # profile: narrower, shifted
        mr = pygame.Rect(sx - 5 + mdir * 2, mcy - 7, 10, 15)
        evs = [(sx + mdir * 2, mcy - 1)]
    pygame.draw.ellipse(surf, _VP_PALE, mr)
    pygame.draw.ellipse(surf, _VP_PALE_LO, mr, 1)
    pygame.draw.line(surf, (236, 228, 208),          # carved bone-lit edge
                     (mr.left + 1, mr.top + 3), (mr.left + 1, mr.bottom - 3), 1)
    pygame.draw.line(surf, _VP_PALE_LO, (sx, mcy - 7), (sx - 1, mcy + 6), 1)  # shatter-crack
    for (ex, ey) in evs:                             # sunken eye-voids
        pygame.draw.circle(surf, _VP_FLESH_LO, (ex, ey + 1), 2)
        pygame.draw.circle(surf, _VP_PIT, (ex, ey), 2)
        pygame.draw.circle(surf, (4, 3, 6), (ex, ey), 1)
    pygame.draw.line(surf, _VP_MOUTH, (sx - 2, mcy + 5), (sx + 2, mcy + 5), 1)  # blank mouth
    # The graft: a gore seam down the right edge + the human socket gone dark.
    pygame.draw.line(surf, _VP_GOR, (mr.right - 1, mcy - 4), (mr.right, mcy + 5), 1)
    pygame.draw.line(surf, _VP_GOR_LO, (mr.left, mcy + 4), (mr.left - 1, mcy + 8), 1)
    if bloom > 0.4 and evs:                           # His light behind the face (faint)
        _cult_glow(surf, evs[0][0], evs[0][1], 2, 10 + int(bloom * 16))


def _draw_curse_priest_raw(surf, x, y, t, facing=(0, 1), curse=0.0):
    """The curse-priest -- a cultist His King has opened and is wearing,
    rendered as SUGGESTION in our muddy register (not a gory totem). ONE
    bold wrong note: the Pallid Mask grafted into a fleshy face (a dark
    graft-seam, the human eye gone to a socket), and a single torn seam down
    the torso with ONE half-submerged face surfacing from the dark. Gore is
    implied by dark torn edges, never bright red; His light is a dim seep
    that wells up the seam as it casts (`curse`). Arms raised in the binding
    cast. Directional: from behind, the split spine + one surfacing face, no
    front face -- so you can read its gaze and break the rite."""
    fx, fy = facing
    if abs(fx) > abs(fy):
        view, mdir = "side", (1 if fx > 0 else -1)
    elif fy < 0:
        view, mdir = "back", 0
    else:
        view, mdir = "front", 0
    lean = int(math.sin(t * 1.2 + x * 0.02))
    rite = math.sin(t * 1.3) * 0.5 + 0.5
    ah = int((0.45 * rite + 0.55 * curse) * 9)
    bloom = curse
    top = y - 17
    sx = x + lean
    # Hunched hide body: lit shoulder rim, fur collar, ragged hem.
    body = [(x - 13, y + 22), (x - 9 + lean, top), (x + 9 + lean, top), (x + 13, y + 22)]
    pygame.draw.polygon(surf, _VP_HIDE, body)
    pygame.draw.polygon(surf, _VP_LO, body, 1)
    pygame.draw.line(surf, _VP_HI, (x - 9 + lean, top + 1), (x - 12, y + 16), 1)
    for fc in range(-9, 10, 2):
        pygame.draw.line(surf, (104, 92, 72), (x + fc, top + 1), (x + fc, top - 2), 1)
    for hx in range(-12, 13, 3):
        pygame.draw.line(surf, _VP_LO, (x + hx, y + 22),
                         (x + hx, y + 22 + random.Random(hx).randint(2, 6)), 2)
    # Arms raised in the binding cast.
    for s in (-1, 1):
        if view == "side" and mdir and s != mdir:
            pygame.draw.line(surf, _VP_HIDE, (x + s * 6, top + 5),
                             (x + s * 10, top - 3 - ah), 2)
            continue
        e1 = (x + s * 8, top + 5); e2 = (x + s * 15, top - 5 - ah)
        hh = (x + s * 17, top - 14 - ah)
        pygame.draw.line(surf, _VP_HIDE, e1, e2, 3)
        pygame.draw.line(surf, _VP_HIDE, e2, hh, 2)
        pygame.draw.line(surf, _VP_LO, e1, e2, 1)
    # A face surfacing from the wound -- `gape` is its mouth, `r` its size.
    def _surface_face(cx, cy, gape=3, r=4):
        cx, cy = int(cx), int(cy)
        pygame.draw.ellipse(surf, _VP_FLESH, (cx - r, cy - r - 1, 2 * r, 2 * r + 2))
        pygame.draw.ellipse(surf, _VP_FLESH_LO, (cx - r, cy - r - 1, 2 * r, 2 * r + 2), 1)
        ex = max(1, r // 2)
        pygame.draw.circle(surf, _VP_PIT, (cx - ex, cy - 2), 1)
        pygame.draw.circle(surf, _VP_PIT, (cx + ex, cy - 2), 1)
        pygame.draw.ellipse(surf, _VP_MOUTH, (cx - 2, cy + 1, 5, max(2, gape)))
        pygame.draw.line(surf, _VP_TEETH, (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
    if view == "back":
        # Back of the masked head: a bone dome + the mask's tie-strap, no face.
        pygame.draw.ellipse(surf, _VP_FLESH_LO, (sx - 6, top - 12, 12, 14))
        pygame.draw.line(surf, (140, 130, 110), (sx - 5, top - 6), (sx + 5, top - 5), 1)
        pygame.draw.line(surf, _VP_GOR, (sx, top + 4), (sx, y + 12), 2)
        _surface_face(sx, top + 16, 3 + int(bloom * 3))
        _cult_glow(surf, sx, top + 14, 2, 14 + int(bloom * 22))
        return
    # The body PEELS open as the curse casts -- the FLESH leads, gold is only
    # a hint. Raw flesh fills the torso; the trapped face strains up out of
    # it; and the hide is pulled back into gore-torn flaps that gape wider as
    # it casts (sp grows). The skin flaps re-cover the sides, so the face is
    # only revealed as the wound opens.
    wob = int(math.sin(t * 4.5) * bloom * 1.6)
    sp = 3 + int(bloom * 5)
    pygame.draw.polygon(surf, _VP_FLESH_LO,                       # raw flesh inside
                        [(sx - 9, top + 6), (sx + 9, top + 6),
                         (sx + 8, y + 12), (sx - 8, y + 12)])
    rise = int(bloom * 5)
    gape = 3 + int(bloom * 5) + (1 if math.sin(t * 5.0) > 0 else 0)
    _surface_face(sx + wob, top + 19 - rise, gape, r=5)          # bigger, straining
    if bloom > 0.35:                                             # gore weeps from the wound
        dl = 4 + int((math.sin(t * 3.0) * 0.5 + 0.5) * 7)
        pygame.draw.line(surf, _VP_GOR, (sx - 1, y + 9), (sx - 1, y + 9 + dl), 2)
        pygame.draw.line(surf, _VP_GOR_LO, (sx + 2, y + 9), (sx + 2, y + 9 + dl - 2), 1)
    for s in (-1, 1):                                           # peeled-back skin flaps
        inner = sx + s * sp + wob
        pygame.draw.polygon(surf, _VP_HIDE,
                            [(inner, top + 6), (sx + s * 13, top + 5),
                             (sx + s * 12, y + 12), (inner, y + 12)])
        for ny in range(top + 8, y + 10, 3):                   # gore-torn jagged edge
            pygame.draw.line(surf, _VP_GOR,
                             (inner - s * random.Random(ny).randint(0, 2), ny),
                             (inner, ny + 1), 1)
    # The Pallid Mask grafted into the head (clear carved face; see helper).
    _pallid_mask(surf, sx, top - 4, view, mdir, bloom)


# Tier-2 (2.5D) head config for the bare human NPC kinds: the front body draws
# as authored, then _npc_view_overlay re-orients the HEAD to the camera view.
# kind -> (head y-offset from y, radius, rear cap/hair colour).
_NPC_HEAD = {
    "townswoman":   (-12, 7, (50, 32, 24)),
    "tisdale_boy":  (-8, 6, (80, 50, 30)),
    "old_townsman": (-12, 7, (40, 28, 16)),
    "hettie":       (-12, 7, (20, 18, 20)),
    "sheriff":      (-12, 7, (70, 52, 36)),
    "royce":        (-12, 7, (130, 52, 44)),
    "preacher":     (-12, 7, (150, 150, 156)),
    "clerk":        (-12, 7, (40, 34, 30)),
}


def _npc_view_overlay(surf, x, y, kind, view):
    """Tier-2 post-pass over a human NPC's front body: 'back' covers the face
    (and eyes) with the rear cap so you see the back of the head; 'left'/'right'
    sweep the cap over the far half for a profile. Only kinds in _NPC_HEAD are
    touched -- masked/hooded/non-human kinds are left alone."""
    cfg = _NPC_HEAD.get(kind)
    if cfg is None:
        return
    hy, r, cap = cfg
    cy = y + hy
    if view == "back":
        pygame.draw.circle(surf, cap, (x, cy), r)
        cap_lo = tuple(int(c * 0.7) for c in cap)
        pygame.draw.rect(surf, cap_lo, (x - 2, cy + r - 2, 4, 2))   # nape
    elif view in ("left", "right"):
        s = 1 if view == "right" else -1
        pygame.draw.circle(surf, cap, (x - (r - 2) * s, cy), r - 1)  # rear covers far eye


def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None, threat=None, seed=0, curse=0.0,
                    view="front"):
    """`blink=True` suppresses eye dots for NPC kinds that have human
    eyes (the named locals -- townswoman, tisdale_boy, sheriff, royce,
    preacher, clerk, hettie, old_townsman). Used by Game.draw to make a
    single NPC's eyes vanish for a single frame -- a subliminal wrongness.
    `gaze=True` lights the watcher's eyes (sees the player). Watchers
    only.
    while the player stands still."""
    if kind == "_invisible":
        return
    if kind == "townswoman":
        # A Brimley woman (Mrs. Calder, the welcoming newcomer, Mara
        # below). Red dress (desaturated, slightly dirtied), dark bun,
        # apron with
        # a faint smudge along the hem so she doesn't read as a fairytale
        # housewife. Eyes sit in shallow hollows so she always looks a
        # little exhausted; on `blink` the dots become 2x2 voids rather
        # than disappearing -- a frame where her face is wrong.
        pygame.draw.rect(surf, (150, 56, 70), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 188), (x - 6, y + 2, 12, 14))  # apron
        pygame.draw.rect(surf, (130, 96, 90), (x - 6, y + 14, 12, 2))    # apron hem stain
        pygame.draw.circle(surf, (228, 198, 168), (x, y - 12), 7)
        pygame.draw.circle(surf, (50, 32, 24), (x - 6, y - 18), 4)  # hair
        pygame.draw.circle(surf, (50, 32, 24), (x + 6, y - 18), 4)
        # Sunken eye hollows (skin-shadow band under the brow)
        pygame.draw.line(surf, (170, 130, 110), (x - 4, y - 11), (x - 1, y - 11), 1)
        pygame.draw.line(surf, (170, 130, 110), (x + 1, y - 11), (x + 4, y - 11), 1)
        if blink:
            # Void frame: oversized black holes where the eyes were.
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
            # Tiny wet glint above each pupil
            try:
                surf.set_at((x - 3, y - 13), (240, 240, 250))
                surf.set_at((x + 1, y - 13), (240, 240, 250))
            except (IndexError, ValueError):
                pass
    elif kind == "old_townsman":
        # The interchangeable old-timers (Old Pell, Garrick, the road
        # pilgrims). Brown coat, hat, beard, cane. The face slot under
        # the hat brim
        # is darkened into a shadow band so two faint pinprick eyes glint
        # from inside the shadow rather than reading as plain face. Beard
        # is now off-white / ash-yellow so he reads as kept-too-long.
        pygame.draw.rect(surf, (78, 60, 42), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (200, 196, 180), (x - 7, y - 5, 14, 6))  # beard (yellowed)
        pygame.draw.rect(surf, (30, 20, 12), (x - 9, y - 22, 18, 4))   # hat brim
        pygame.draw.rect(surf, (30, 20, 12), (x - 6, y - 28, 12, 7))   # crown
        # Hat-brim shadow band across the eyes
        pygame.draw.rect(surf, (60, 40, 30), (x - 6, y - 14, 12, 3))
        # Pinprick eyes inside the shadow
        if not blink:
            pygame.draw.circle(surf, (210, 200, 160), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (210, 200, 160), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (90, 60, 30), (x + 10, y - 4), (x + 10, y + 14), 2)  # cane
    elif kind == "hettie":
        # Hettie -- keeps the shop open, sweeping a step that won't get
        # dirty. A plum housedress under a worn white apron, grey hair
        # pinned in a bun under a kerchief. The uncanny tell is carried
        # over from the old shopkeeper: small spectacles whose lenses are
        # FILLED black -- you can never quite find her eyes behind them --
        # with a reflection-glint on the WRONG (same) side of both lenses,
        # impossible under a single overhead light.
        pygame.draw.rect(surf, (104, 60, 78), (x - 9, y - 2, 18, 18))      # plum dress
        pygame.draw.rect(surf, (206, 200, 192), (x - 6, y + 1, 12, 15))    # apron
        pygame.draw.rect(surf, (150, 120, 130), (x - 6, y + 13, 12, 2))    # apron hem
        pygame.draw.circle(surf, (206, 176, 150), (x, y - 12), 7)          # face
        pygame.draw.rect(surf, (150, 146, 150), (x - 7, y - 19, 14, 5))    # grey hair
        pygame.draw.circle(surf, (150, 146, 150), (x, y - 20), 3)          # bun
        pygame.draw.rect(surf, (120, 70, 88), (x - 7, y - 20, 14, 3))      # kerchief band
        if blink:
            # Void blink: the lenses swallow what little face there was.
            pygame.draw.rect(surf, (4, 2, 6), (x - 5, y - 14, 4, 3))
            pygame.draw.rect(surf, (4, 2, 6), (x + 1, y - 14, 4, 3))
        else:
            pygame.draw.rect(surf, (12, 12, 16), (x - 4, y - 13, 3, 2))    # L lens
            pygame.draw.rect(surf, (12, 12, 16), (x + 1, y - 13, 3, 2))    # R lens
            pygame.draw.line(surf, (40, 40, 50), (x - 1, y - 12), (x + 1, y - 12), 1)  # bridge
            try:
                surf.set_at((x - 2, y - 13), (140, 150, 160))
                surf.set_at((x + 3, y - 13), (140, 150, 160))   # wrong-side glint
            except (IndexError, ValueError):
                pass
    elif kind == "tisdale_boy":
        # Toby Tisdale. Desaturated yellow tunic; the original bright
        # primary made the kid read as cheerful, which fights the use.
        # Hair hangs lower over the brow; the cheek dots used to be
        # freckles, now they sit slightly low and asymmetric so they
        # read as old tear-streaks when you look twice.
        pygame.draw.rect(surf, (172, 156, 70), (x - 7, y, 14, 14))
        pygame.draw.circle(surf, (228, 196, 168), (x, y - 8), 6)
        pygame.draw.rect(surf, (80, 50, 30), (x - 7, y - 13, 14, 5))
        # Long fringe -- a fringe-band lower over the eyes than the hair
        # cap, so the kid always looks like he's peering up through it.
        pygame.draw.rect(surf, (80, 50, 30), (x - 6, y - 9, 12, 2))
        # Sunken eye hollows
        pygame.draw.line(surf, (170, 130, 100), (x - 4, y - 7), (x - 1, y - 7), 1)
        pygame.draw.line(surf, (170, 130, 100), (x + 1, y - 7), (x + 4, y - 7), 1)
        if blink:
            # Void blink: oversized 3x2 black holes that overflow the
            # eye area -- bigger than the head ought to allow.
            pygame.draw.rect(surf, (2, 0, 4), (x - 4, y - 9, 3, 3))
            pygame.draw.rect(surf, (2, 0, 4), (x + 1, y - 9, 3, 3))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 8), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 8), 1)
            try:
                surf.set_at((x - 3, y - 9), (240, 240, 250))
                surf.set_at((x + 1, y - 9), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Cheek marks -- low and asymmetric so the eye reads them as
        # old tear tracks before settling on "freckles".
        pygame.draw.circle(surf, (150, 90, 80), (x - 4, y - 5), 1)
        pygame.draw.circle(surf, (140, 84, 76), (x + 5, y - 4), 1)
    elif kind == "bandit":
        # THRESHOLD: re-skinned as a hooded cultist. Coarse undyed-
        # wool robe (dirty cream) over a dark inner shirt; deep hood
        # casts a shadow across the eyes; faint ash on the hem from
        # the cauldron fire. Used by the patrol_cultist NPCs that
        # appear at higher Pursuer proximity.
        robe       = (170, 156, 130)     # undyed wool
        robe_dark  = (110, 100, 84)      # shadow seam
        inner      = (40, 36, 40)        # shirt under the robe
        skin_dim   = (180, 156, 130)     # face in hood-shadow
        ash        = (60, 54, 50)        # scorched hem
        # Body / robe
        pygame.draw.rect(surf, robe, (x - 9, y - 4, 18, 20))
        pygame.draw.rect(surf, robe_dark, (x - 9, y - 4, 18, 20), 1)
        # Vertical seam
        pygame.draw.line(surf, robe_dark, (x, y - 4), (x, y + 14), 1)
        # Inner shirt peek at the collar
        pygame.draw.rect(surf, inner, (x - 4, y - 4, 8, 3))
        # Head (in hood shadow)
        pygame.draw.circle(surf, skin_dim, (x, y - 12), 7)
        # Hood drape over the head and shoulders
        pygame.draw.rect(surf, robe, (x - 10, y - 22, 20, 10))
        pygame.draw.rect(surf, robe_dark, (x - 10, y - 22, 20, 10), 1)
        # Hood shadow across the eyes -- pure-black band, slightly
        # deeper than skin. The shadow now extends a row lower so it
        # darkens the cheekbones too, killing any "person" read.
        pygame.draw.rect(surf, (4, 2, 6), (x - 7, y - 14, 14, 5))
        if blink:
            # Void blink: yellow pinpricks vanish and a faint pale jaw
            # shape ghosts through the shadow -- the suggestion of teeth
            # / skull where a face ought to be. The mouth-row sits below
            # the shadow band, never visible at rest.
            pygame.draw.line(surf, (180, 168, 152), (x - 4, y - 9), (x + 4, y - 9), 1)
            pygame.draw.line(surf, (140, 128, 112), (x - 3, y - 8), (x + 3, y - 8), 1)
            # Two faint nose-cavity pricks in the shadow band
            pygame.draw.rect(surf, (12, 10, 14), (x - 1, y - 11, 1, 1))
            pygame.draw.rect(surf, (12, 10, 14), (x + 1, y - 11, 1, 1))
        else:
            # Eyes -- two faint pinpricks in the hood shadow
            pygame.draw.circle(surf, (200, 180, 60), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (200, 180, 60), (x + 2, y - 12), 1)
        # Scorched hem
        pygame.draw.rect(surf, ash, (x - 9, y + 14, 18, 2))
    elif kind == "sheriff":
        # Sheriff Hollis Vane -- a local, born here, broken. A tan duty
        # shirt, a brown brimmed hat (not a city cop's peaked cap), a tin
        # star going dull on the chest. The hat brim keeps the eyes in a
        # permanent dark band; stubble along the jaw; a man who hasn't
        # slept since the road stopped going anywhere. Void blink.
        pygame.draw.rect(surf, (120, 104, 76), (x - 9, y - 2, 18, 18))   # tan shirt
        pygame.draw.rect(surf, (96, 82, 58), (x - 9, y + 9, 18, 5))      # belt/trouser line
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)        # face
        pygame.draw.rect(surf, (70, 52, 36), (x - 11, y - 19, 22, 3))    # wide hat brim
        pygame.draw.rect(surf, (86, 66, 44), (x - 6, y - 25, 12, 7))     # hat crown
        # Hat-brim shadow band across the eyes
        pygame.draw.rect(surf, (54, 40, 28), (x - 6, y - 14, 12, 3))
        # Stubble along the jaw
        for sx2 in (-4, 0, 4):
            pygame.draw.circle(surf, (120, 100, 84), (x + sx2, y - 6), 1)
        if blink:
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 14, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 14, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 13), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 13), 1)
            try:
                surf.set_at((x - 3, y - 14), (240, 240, 250))
                surf.set_at((x + 1, y - 14), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Dull tin star on the chest
        pygame.draw.circle(surf, (180, 168, 96), (x - 4, y + 2), 2)
        pygame.draw.circle(surf, (120, 110, 60), (x - 4, y + 2), 2, 1)
    elif kind == "royce":
        # Royce -- drives the river road to the county line and gets handed
        # back into Brimley every time. A working man, no fisherman: a
        # quilted flannel jacket over a pale tee, a faded feed cap, three
        # days of stubble. Cap brim shadows the tired eyes; void blink.
        pygame.draw.rect(surf, (96, 64, 52), (x - 9, y - 2, 18, 18))     # flannel jacket
        pygame.draw.line(surf, (60, 40, 32), (x, y - 2), (x, y + 14), 1) # zip seam
        pygame.draw.rect(surf, (150, 146, 140), (x - 3, y - 2, 6, 8))    # pale tee at collar
        pygame.draw.circle(surf, (198, 170, 146), (x, y - 12), 7)        # face
        pygame.draw.rect(surf, (150, 60, 50), (x - 8, y - 18, 16, 5))    # cap crown (faded red)
        pygame.draw.rect(surf, (120, 48, 40), (x - 9, y - 14, 13, 2))    # cap brim
        # Cap-brim shadow band
        pygame.draw.rect(surf, (60, 44, 34), (x - 6, y - 13, 12, 2))
        for sx2 in (-4, 0, 4):
            pygame.draw.circle(surf, (130, 108, 90), (x + sx2, y - 6), 1)  # stubble
        if blink:
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
    elif kind == "preacher":
        # Reverend Asa Crane -- gaunt, grey, the one who named them from
        # the pulpit. A black cassock, a white clerical collar at the
        # throat, thin grey hair, deep solemn hollows. He reads as already
        # half a ghost. A small pale cross at the breast. Void blink.
        pygame.draw.rect(surf, (30, 28, 34), (x - 9, y - 2, 18, 18))     # black vestment
        pygame.draw.rect(surf, (44, 42, 48), (x + 3, y - 2, 6, 18))      # shadow side
        pygame.draw.rect(surf, (228, 228, 230), (x - 3, y - 2, 6, 4))    # white collar
        pygame.draw.circle(surf, (204, 192, 178), (x, y - 12), 7)        # gaunt face
        pygame.draw.rect(surf, (150, 150, 156), (x - 7, y - 19, 14, 4))  # grey hair
        # Sunken cheeks / hollows
        pygame.draw.line(surf, (150, 120, 104), (x - 5, y - 8), (x - 3, y - 6), 1)
        pygame.draw.line(surf, (150, 120, 104), (x + 5, y - 8), (x + 3, y - 6), 1)
        if blink:
            pygame.draw.rect(surf, (4, 2, 6), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 6), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
        pygame.draw.line(surf, (160, 150, 120), (x + 5, y + 2), (x + 5, y + 8), 1)
        pygame.draw.line(surf, (160, 150, 120), (x + 3, y + 4), (x + 7, y + 4), 1)
    elif kind == "clerk":
        # The Lodge Clerk -- the smiling trap-keeper who never ages. A
        # pressed dark waistcoat over a white shirt, a thin tie, neat
        # side-parted dark hair, a pale unbothered face. The tell: a
        # level smile that never reaches the eyes, and on blink the smile
        # stays while the eyes drop to voids -- the host's face running
        # without him in it.
        pygame.draw.rect(surf, (44, 40, 48), (x - 9, y - 2, 18, 18))     # dark waistcoat
        pygame.draw.rect(surf, (210, 206, 202), (x - 3, y - 2, 6, 16))   # white shirt placket
        pygame.draw.line(surf, (120, 30, 36), (x, y - 2), (x, y + 4), 1) # thin tie
        pygame.draw.circle(surf, (224, 206, 188), (x, y - 12), 7)        # pale face
        pygame.draw.rect(surf, (40, 34, 30), (x - 7, y - 19, 14, 4))     # hair mass
        pygame.draw.line(surf, (60, 52, 46), (x + 2, y - 19), (x + 2, y - 15), 1)  # side part
        if blink:
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
        # The level host's smile (always on)
        pygame.draw.line(surf, (120, 80, 80), (x - 3, y - 7), (x + 3, y - 7), 1)
    elif kind == "guard":
        # Iron helmet + spear. The visor slit is now a deeper, pitch-
        # black void with two faint red glints inside -- you don't see
        # eyes, you see something looking out from inside the helm.
        pygame.draw.rect(surf, (96, 96, 116), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (130, 130, 150), (x - 9, y - 22, 18, 12))  # helmet
        # Visor slit -- pitch black with two pinprick reds
        pygame.draw.rect(surf, (4, 2, 4), (x - 4, y - 14, 8, 4))
        if not blink:
            pygame.draw.circle(surf, (180, 30, 30), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (180, 30, 30), (x + 2, y - 12), 1)
        pygame.draw.line(surf, (60, 40, 25), (x + 12, y - 18), (x + 12, y + 16), 2)
        pygame.draw.polygon(surf, (200, 200, 220),
                            [(x + 12, y - 18), (x + 9, y - 22), (x + 15, y - 22)])
    elif kind == "sheriff_hollow":
        # Sheriff Vane, gone hollow -- the stage-3 unique threat. The
        # lawman's shape is still there (tan shirt, brimmed hat) but the
        # man isn't: the face is a void band with two sick-gold pinpricks,
        # the tin star has curdled into a small Yellow Sign, and a faint
        # jaundice clings to him. He doesn't blink; he doesn't stop.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        pygame.draw.rect(surf, (96, 86, 62), (x - 9, y - 2, 18, 18))    # dimmed tan shirt
        pygame.draw.rect(surf, (74, 66, 46), (x - 9, y + 9, 18, 5))     # belt line
        pygame.draw.circle(surf, (150, 146, 110), (x, y - 12), 7)       # sallow face
        pygame.draw.rect(surf, (54, 40, 28), (x - 11, y - 19, 22, 3))   # hat brim
        pygame.draw.rect(surf, (64, 50, 34), (x - 6, y - 25, 12, 7))    # hat crown
        # Pure-void eye band, two sick-gold pinpricks deep inside.
        pygame.draw.rect(surf, (4, 3, 6), (x - 6, y - 14, 12, 4))
        gl = 0.5 + 0.5 * math.sin(t * 2.2)
        g = int(150 + 80 * gl)
        pygame.draw.circle(surf, (g, int(g * 0.8), 40), (x - 2, y - 12), 1)
        pygame.draw.circle(surf, (g, int(g * 0.8), 40), (x + 2, y - 12), 1)
        # The star curdled into a small Yellow Sign.
        cy = y + 2
        pygame.draw.line(surf, (210, 188, 70), (x - 4, cy - 2), (x - 4, cy + 2), 1)
        pygame.draw.line(surf, (210, 188, 70), (x - 4, cy), (x - 6, cy - 1), 1)
        pygame.draw.line(surf, (210, 188, 70), (x - 4, cy), (x - 2, cy - 1), 1)
        # Jaundice cling -- the fold's sick gold, matching the cult/King.
        wash = _pg.Surface((26, 36), _pg.SRCALPHA)
        wash.fill((168, 142, 56, 46))
        surf.blit(wash, (x - 13, y - 22))
    elif kind == "shadow":
        pygame.draw.rect(surf, (8, 4, 12), (x - 8, y - 4, 16, 18))
        pygame.draw.circle(surf, (8, 4, 12), (x, y - 10), 8)
        pygame.draw.circle(surf, (220, 30, 30), (x - 3, y - 11), 1)
        pygame.draw.circle(surf, (220, 30, 30), (x + 3, y - 11), 1)
    elif kind == "tall_shadow":
        # Tall, THIN smear of darkness. ~2.5x a normal NPC vertically, but
        # narrow enough that it reads as not-quite-human. In lore the
        # figure is a pilgrim of the Yellow King -- which is why the eyes
        # are three jaundiced dots stacked vertically, not a face we
        # recognise.
        # The silhouette now BREATHES on a slow sine: top of the body
        # drifts left/right by a pixel, and the seam wavers. Adds a
        # subliminal "this isn't standing still" cue without changing
        # the silhouette enough to mistake for movement.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        sway = math.sin(t * 0.9) * 1
        body_rect = pygame.Rect(x - 8 + int(sway), y - 50, 16, 64)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-4, -6))
        # Wavering vertical seam
        for sy_step in range(0, 60, 4):
            seam_x = x + int(math.sin(t * 1.3 + sy_step * 0.2) * 1)
            pygame.draw.line(surf, (2, 0, 4),
                             (seam_x, y - 48 + sy_step),
                             (seam_x, y - 48 + sy_step + 4), 1)
        # Three vertical eye dots. One of the three flickers off on a
        # staggered cycle so the row is rarely all lit at the same time
        # -- the eyes never quite "match" each other.
        flicker = int(t * 2.4) % 7
        if flicker != 0:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 42), 1)
        if flicker != 3:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 38), 1)
        if flicker != 5:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 34), 1)
    elif kind == "yellow_king":
        # The King in Yellow -- a floating tear-in-space: a churning clot of
        # gold light packed with the cult's fused faces, arms reaching out to
        # grasp, trailing a wake of glowing soul-orbs. The full drawing, rift
        # birth, and motion live in _draw_king. `birth` (0..1) and `gait` come
        # from the live NPC; when absent (a preview) they loop off the clock so
        # the eruption still shows.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        if birth is None:
            cyc = t % 7.0
            b = min(1.0, cyc / 1.6)            # erupt over ~1.6s
            g = max(0.0, cyc - 1.6) * 7.0      # then drift the rest
        else:
            b = birth
            g = gait if gait is not None else t * 7.0
        _draw_king(surf, x, y, facing, t, b, g, threat)
    elif kind == "black_figure":
        # Pure-black humanoid silhouette, NPC proportions. No eyes, no
        # facial detail -- just the hole-shaped outline of a person.
        # Spawned in the player's house on the 7th re-entry.
        outline = (0, 0, 0)
        # Slight darker-than-black aura behind the body so it reads as
        # absence rather than a flat sprite on dark floors.
        aura = pygame.Surface((30, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (0, 0, 0, 90), (0, 0, 30, 36))
        surf.blit(aura, (x - 15, y - 18))
        # Body
        pygame.draw.rect(surf, outline, (x - 9, y - 4, 18, 18))
        # Head
        pygame.draw.circle(surf, outline, (x, y - 12), 7)
        # Shoulders / cloak hint
        pygame.draw.rect(surf, outline, (x - 11, y - 4, 22, 6))
        # Legs
        pygame.draw.rect(surf, outline, (x - 6, y + 14, 5, 8))
        pygame.draw.rect(surf, outline, (x + 1, y + 14, 5, 8))
    elif kind == "cultist":
        # Stitched animal-hide coat + a carved wooden mask (one of six,
        # chosen per individual by `seed`). Directional: mask front/side,
        # bare fur hood + Sign from behind so you can read its gaze. See
        # _draw_cultist + the mask helpers at the top of this module.
        t = pygame.time.get_ticks() / 1000.0
        _draw_cultist(surf, x, y, facing, seed, t)
    elif kind == "curse_priest":
        # The cult's curse-priest -- binds the Watchers to you. Drawn on a
        # private layer and run through the same Darkwood grime brush as the
        # rank-and-file cultist so the whole cult reads in one register.
        t = pygame.time.get_ticks() / 1000.0
        LX, LY = 26, 48
        lay = pygame.Surface((52, 76), pygame.SRCALPHA)
        _draw_curse_priest_raw(lay, LX, LY, t, facing, curse)
        _darkwood_pass(lay, seed or 7, strength=0.72)  # muddy, but the form reads
        if curse > 0.05:
            lean = int(math.sin(t * 1.2 + LX * 0.02))
            _curse_bloom(lay, LX + lean, LY, t, curse)
        surf.blit(lay, (int(x) - LX, int(y) - LY))
    elif kind == "vessel_avatar":
        # A towering Yellow-King vessel with reaching tentacles. Body is
        # the tall_shadow silhouette enlarged + four wiggling tentacles
        # that point in the `facing` direction (toward the player when
        # in chase). Animated by pygame.time so the wiggle keeps moving
        # even when the figure is mid-lunge.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        body_rect = pygame.Rect(x - 11, y - 56, 22, 72)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-6, -8))
        pygame.draw.line(surf, (2, 0, 4), (x, y - 54), (x, y + 14), 1)
        for ey in (-46, -42, -38):
            pygame.draw.circle(surf, (210, 188, 70), (x, y + ey), 2)
        fx, fy = facing
        for i in range(4):
            phase = t * 6 + i * 1.4
            wiggle = math.sin(phase) * 6
            sway_x = -fy * wiggle
            sway_y = fx * wiggle
            origin = (x + (i - 1.5) * 4, y - 4)
            mid = (origin[0] + fx * 12 + sway_x * 0.5,
                   origin[1] + fy * 12 + sway_y * 0.5)
            tip = (origin[0] + fx * 26 + sway_x,
                   origin[1] + fy * 26 + sway_y)
            pygame.draw.line(surf, (8, 6, 14),
                             (int(origin[0]), int(origin[1])),
                             (int(mid[0]), int(mid[1])), 3)
            pygame.draw.line(surf, (16, 12, 24),
                             (int(mid[0]), int(mid[1])),
                             (int(tip[0]), int(tip[1])), 2)
            pygame.draw.circle(surf, (210, 188, 70),
                               (int(tip[0]), int(tip[1])), 1)
    elif kind == "static_figure":
        pygame.draw.rect(surf, (40, 40, 50), (x - 8, y - 2, 16, 18))
        pygame.draw.circle(surf, (200, 180, 160), (x, y - 10), 7)
        pygame.draw.rect(surf, (30, 25, 20), (x - 8, y - 17, 16, 8))
    elif kind == "doll":
        # Pink-dress doll with X-stitched eyes. Once every ~4 seconds
        # there's a brief frame where the X eyes invert into open
        # round pupils -- the doll is looking at you. The window is
        # ~80ms (one stale frame) so the player questions whether
        # they saw it. Tear streak under the right eye.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        anomaly = (t % 4.0) > 3.92
        pygame.draw.rect(surf, (200, 100, 130), (x - 6, y - 2, 12, 14))
        pygame.draw.circle(surf, (250, 230, 220), (x, y - 9), 6)
        if anomaly:
            # Open black eyes
            pygame.draw.circle(surf, C_BLACK, (x - 3, y - 10), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 3, y - 10), 1)
        else:
            pygame.draw.line(surf, C_BLACK, (x - 4, y - 11), (x - 2, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x - 2, y - 11), (x - 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 2, y - 11), (x + 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 4, y - 11), (x + 2, y - 9), 1)
        # Faint tear streak under the right eye (always visible)
        pygame.draw.line(surf, (180, 130, 140),
                         (x + 3, y - 7), (x + 3, y - 4), 1)
    elif kind == "watcher":
        # A Watcher -- the curse made visible. NOT an eye and NOT a vessel:
        # a tall, too-thin, ragged faceless apparition that stands at the
        # edge of sight. Only the cursed see it. It is half-there -- it
        # phases on a slow sine and leaves a faint after-image you can never
        # fix on -- and it looms a little nearer over its cycle. A deep VOID
        # cowl where a face should be; two dim sick pinpricks deep inside are
        # the only colour (His gaze). Look straight at it (gaze=True) and the
        # pinpricks go dark.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        rng = random.Random(int(x) & 0xffff)
        phase = 0.32 + 0.5 * (math.sin(t * 1.1 + x * 0.01) * 0.5 + 0.5)
        loom = math.sin(t * 0.5 + x * 0.02) * 0.5 + 0.5      # 0..1, creeps in
        sway = int(math.sin(t * 0.8 + x * 0.03) * 2)
        layer = _pg.Surface((40, 72), _pg.SRCALPHA)
        bx = 20 + sway
        base_y = 66
        h = 48 + int(loom * 10)           # looms taller as it nears
        top = base_y - h
        shoulders = top + 9
        shroud = (24, 22, 28, 255)
        shroud_lo = (12, 11, 15, 255)
        void = (6, 6, 9, 255)
        # Ragged, wind-torn shroud: a too-thin tapered silhouette built from
        # jittered edges (seeded -> stable, doesn't boil), peaked into a hood.
        steps = 7
        left, right = [], []
        for i in range(steps + 1):
            fr = i / steps
            yy = shoulders + int(fr * (base_y - shoulders))
            hw = 2 + fr * 6.5 + rng.uniform(-1.4, 1.4) * (0.3 + fr)
            left.append((bx - hw, yy))
            right.append((bx + hw, yy))
        _pg.draw.polygon(layer, shroud, [(bx, top)] + right + left[::-1])
        _pg.draw.polygon(layer, shroud_lo, [(bx, top)] + right + left[::-1], 1)
        # Torn hem: strips trailing into the dark, stirred by the sway.
        for hx in range(-9, 10, 2):
            ln = rng.randint(3, 8)
            dr = int(sway * (hx / 9.0))
            _pg.draw.line(layer, shroud, (bx + hx, base_y - 3),
                          (bx + hx + dr, base_y - 3 + ln), 2)
        # Long, thin, uneven reaching arms hinted down the shroud.
        _pg.draw.line(layer, shroud_lo, (bx - 3, shoulders + 2),
                      (bx - 9 + sway, shoulders + 20), 2)
        _pg.draw.line(layer, shroud_lo, (bx + 3, shoulders + 2),
                      (bx + 8 - sway, shoulders + 25), 2)
        # A faint cold rim down one side so the wrong silhouette reads against
        # the dark without lifting the body out of near-black.
        _pg.draw.line(layer, (46, 46, 60, 255), (int(left[1][0]) + 1, shoulders + 2),
                      (int(left[-2][0]) + 1, base_y - 4), 1)
        # The void cowl: a deep hollow where a face should be, hood-rimmed.
        _pg.draw.ellipse(layer, void, (bx - 5, top + 1, 11, 14))
        _pg.draw.arc(layer, shroud_lo, (bx - 6, top - 1, 13, 17), 0.2, 2.95, 2)
        # The gaze: a faint CONSTELLATION of sick eyes deep in the cowl (His
        # mass-of-eyes, restrained), blinking on staggered phases -- they all
        # wink out if the player looks straight at it.
        if not gaze:
            erng = random.Random((int(x) * 7 + 3) & 0xffff)
            for i in range(6):
                ex = bx + erng.randint(-3, 3)
                ey = top + 7 + erng.randint(-4, 4)
                bl = 0.5 + 0.5 * math.sin(t * 1.6 + i * 1.5 + x)
                if bl < 0.32:
                    continue
                g = int(70 + 48 * bl)
                _pg.draw.circle(layer, (54, 46, 20, 60), (ex, ey), 2)
                _pg.draw.circle(layer, (g, int(g * 0.8), 28, 255), (ex, ey), 1)
        # Half-there: a clear offset after-image, then the figure -- both kept
        # translucent so the background bleeds through (an apparition).
        ox = int(x - 20)
        oy = int(y - base_y)
        layer.set_alpha(int(230 * phase * 0.5))
        surf.blit(layer, (ox - sway * 3 - 1, oy - 2))
        layer.set_alpha(int(230 * phase))
        surf.blit(layer, (ox, oy))
    elif kind == "glitch_npc":
        for _ in range(30):
            ox = random.randint(-9, 9); oy = random.randint(-12, 8)
            col = (random.randint(80,255), random.randint(0,60), random.randint(0,60))
            pygame.draw.rect(surf, col, (x + ox, y + oy, 2, 2))
    else:
        # generic placeholder
        pygame.draw.rect(surf, (200, 200, 200), (x - 8, y - 8, 16, 16))
    # Tier-2: re-orient the head to the camera view (no-op for front + for any
    # kind not in _NPC_HEAD; flat top-down never passes a view).
    if view != "front":
        _npc_view_overlay(surf, x, y, kind, view)


# Dominant garment tint per local sprite kind, so a downed local still
# reads as *who* they were (the Sheriff's navy, Hettie's plum) rather
# than an anonymous heap. Falls back to a drab brown.
_CORPSE_TINT = {
    "sheriff":      (32, 50, 100),
    "royce":        (118, 92, 60),
    "hettie":       (118, 70, 92),
    "townswoman":   (150, 56, 70),
    "tisdale_boy":  (172, 156, 70),
    "old_townsman": (78, 60, 42),
    "preacher":     (34, 32, 40),
    "clerk":        (60, 54, 60),
    "cultist":      (150, 140, 120),
}


def _corpse_echo_tisdale_boy(surf, hx, hy, x, y, mold):
    """The lying boy's mouth never stopped -- dropped, his head still hangs
    open as one big gaping maw. At corpse scale this has to be a BOLD shape,
    not teeth: the head end is overdrawn as an oversized dark open mouth with
    a pale jaw rim and gold burning in the throat, gaping wider as the fold
    works him. Distinct at a glance from Hettie's reach."""
    w = 4 + mold                                # the gape widens with the mold
    pygame.draw.ellipse(surf, (236, 230, 220),
                        (hx - w, hy - w // 2 - 1, w * 2, w + 2))   # pale jaw rim
    pygame.draw.ellipse(surf, (6, 3, 4),
                        (hx - w + 1, hy - w // 2, w * 2 - 2, w))   # the dark gape
    pygame.draw.line(surf, (210, 158, 44), (hx, hy - 1), (hx, hy + 1), 1)  # gold throat
    if mold >= 2:                               # a few bold teeth bridge the gape
        for tx in (-w + 2, 0, w - 2):
            pygame.draw.line(surf, (236, 230, 220),
                             (hx + tx, hy - w // 2), (hx + tx, hy + w // 2 - 1), 1)


def _corpse_echo_hettie(surf, hx, hy, x, y, mold):
    """Hettie kept the lights on. Dropped, the arm is still flung out too
    far -- reaching, fingers grown long, an unmistakable silhouette
    stretched toward a switch that isn't there."""
    sgn = -1 if hx < x else 1                   # reach AWAY from the head
    ax = x + sgn * 16
    pygame.draw.line(surf, (198, 170, 146), (x + sgn * 4, y + 5),
                     (ax, y + 9), 2)            # too-long arm, brighter than body
    for fdy in (-4, -1, 2, 5):                   # splayed clutching fingers
        pygame.draw.line(surf, (198, 170, 146),
                         (ax, y + 9), (ax + sgn * 5, y + 9 + fdy), 1)


_CORPSE_ECHO = {
    "tisdale_boy": _corpse_echo_tisdale_boy,
    "hettie": _corpse_echo_hettie,
}


# ---- Corpse infection overlays ----------------------------------------
# When the fold claims a corpse (mold >= 1) it spreads INFECTION through the
# flesh -- gold rot welling up from INSIDE the body, sickly discolour, the
# Yellow Sign branded at full claim. The corruption is warm gold light from
# within (the body still reads as a body); it is NEVER a black void. Each
# overlay is drawn OVER the already-drawn slumped body. NAMED resisters get
# the wound shaped like their living mutation (a gold maw for Toby, a peeled
# Sign-seam for Hettie, gold faces for Garrick); unnamed kinds get the
# generic gold rot. mold is the intensity (1..3).

def _corpse_rot(surf, x, y, mold):
    """Sickly discoloured patches creeping over the flesh -- the meat going
    wrong before the gold breaks through."""
    rot = (92, 96, 44)
    pygame.draw.rect(surf, rot, (x - 9, y + 4, 6, 3))
    if mold >= 2:
        pygame.draw.rect(surf, rot, (x + 3, y - 1, 6, 2))
        pygame.draw.rect(surf, rot, (x - 4, y - 2, 4, 2))


def _corpse_sign(surf, x, y):
    """The Yellow Sign branded into the body at full claim."""
    pygame.draw.line(surf, (252, 222, 112), (x - 3, y + 2), (x + 3, y + 2), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y - 1), (x, y + 5), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y + 2), (x - 2, y), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y + 2), (x + 2, y), 1)


def _corpse_infect_generic(surf, x, y, body, body_lo, mold):
    _corpse_rot(surf, x, y, mold)
    _gold_in_wound(surf, x, y + 2, 3 + mold, 48 + 20 * mold)     # gold welling up a wound
    for vx in (-8, -4, 5, 9)[:1 + mold]:                        # gold veins branching out
        pygame.draw.line(surf, (208, 166, 58),
                         (x, y + 2), (x + vx, y + 2 + (vx % 3) - 1), 1)
    if mold >= 3:
        _corpse_sign(surf, x, y)


def _corpse_claim_tisdale_boy(surf, x, y, body, body_lo, mold):
    # Toby's wound is the maw he became -- but it GLOWS: the fold's gold burns
    # up out of the split flesh, dark meat lips and a few pale teeth framing
    # it. An infected mouth opening down the body, not a black hole.
    _corpse_rot(surf, x, y, mold)
    h = 1 + mold
    _gold_in_wound(surf, x, y + 2, 4 + mold, 78 + 18 * mold)     # gold up the throat
    pygame.draw.rect(surf, (96, 30, 26), (x - 11, y + 1 - h, 23, 1))   # upper meat lip
    pygame.draw.rect(surf, (96, 30, 26), (x - 11, y + 2 + h, 23, 1))   # lower meat lip
    for tx in range(-9, 11, 4):                                  # pale teeth along the lips
        pygame.draw.line(surf, (230, 222, 202),
                         (x + tx, y + 1 - h), (x + tx, y + 2 + h), 1)


def _corpse_claim_hettie(surf, x, y, body, body_lo, mold):
    # Hettie peels open down her length: skin-flaps curl back off a seam that
    # wells gold, the Yellow Sign branded in it. Her reaching-arm echo still
    # lays over the top. Infected glow, not a slit.
    _corpse_rot(surf, x, y, mold)
    _gold_in_wound(surf, x, y + 2, 4 + mold, 60 + 16 * mold)     # gold up the seam
    skin = (212, 182, 156)
    for px in range(-9, 11, 6):                                  # skin-flaps peeling back
        d = 1 + mold
        pygame.draw.polygon(surf, skin, [(x + px, y - 1), (x + px + 4, y - 1),
                                         (x + px + 2, y - 1 - d)])
        pygame.draw.polygon(surf, skin, [(x + px, y + 6), (x + px + 4, y + 6),
                                         (x + px + 2, y + 6 + d)])
    if mold >= 2:
        _corpse_sign(surf, x, y)
    else:
        pygame.draw.line(surf, (250, 210, 92), (x - 7, y + 2), (x + 8, y + 2), 1)


def _corpse_claim_old_townsman(surf, x, y, body, body_lo, mold):
    # Faces strain up through Garrick's flesh, each lit GOLD from within --
    # gold faces surfacing across the body with dark sunken features, more of
    # them as the fold works him. Not black pits.
    _corpse_rot(surf, x, y, mold)
    spots = [(-7, 1), (0, 4), (6, 0), (10, 3), (3, 6), (-4, -1)][:1 + mold * 2]
    for fx, fy in spots:
        cx, cy = x + fx, y + 1 + fy
        _gold_in_wound(surf, cx, cy, 3, 66)                     # the face glows gold
        pygame.draw.circle(surf, (74, 26, 22), (cx - 1, cy - 1), 1)   # sunken eyes
        pygame.draw.circle(surf, (74, 26, 22), (cx + 1, cy - 1), 1)
        pygame.draw.line(surf, (44, 16, 14), (cx - 1, cy + 1), (cx + 1, cy + 1), 1)  # mouth


_CORPSE_CLAIM = {
    "tisdale_boy": _corpse_claim_tisdale_boy,
    "hettie": _corpse_claim_hettie,
    "old_townsman": _corpse_claim_old_townsman,
}


def draw_npc_corpse(surf, x, y, kind, seed=0, mold=0):
    """A local, put down. A horizontal slumped body over a dark blood
    pool -- read as a person on the floor, not a sprite standing. Tinted
    off the kind so the corpse still says who it was. Orientation is
    seeded so a row of bodies doesn't all face the same way.

    `mold` (0..3) is the infestation stage -- the fold claiming the dead.
    The body stays a recognisable body; the fold's INFECTION spreads over
    it as warm gold rot welling up from inside the flesh (never a black
    void): stage 1 a gold wound and sickly discolour, escalating through
    stage 3 where the Yellow Sign is branded into it. Named resisters are
    infected in the shape of their living mutation (`_CORPSE_CLAIM`); others
    get the generic gold rot. Where a character's compulsion should outlast
    them (`_CORPSE_ECHO`) that lays over the top -- their dying act still
    happening on the floor."""
    rng = random.Random(seed)
    body = _CORPSE_TINT.get(kind, (70, 64, 60))
    body_lo = tuple(int(c * 0.65) for c in body)
    skin = (172, 146, 126)
    head_left = rng.random() < 0.5
    hx = x - 13 if head_left else x + 13
    # Blood pool, drawn first so the body lies in it. Offset slightly
    # toward the head end (the wound that dropped them).
    pool = pygame.Surface((44, 26), pygame.SRCALPHA)
    pygame.draw.ellipse(pool, (84, 12, 14, 140), (0, 0, 44, 26))
    pygame.draw.ellipse(pool, (58, 6, 8, 185), (10, 7, 24, 12))
    surf.blit(pool, (x - 22 + (4 if head_left else -4), y - 2))
    # The body always reads as a BODY first -- a slumped flesh torso with an
    # outflung arm. mold 0 is a clean fresh kill. Then, once the fold claims
    # it (mold >= 1), INFECTION spreads OVER the body: gold rot welling up
    # from within the flesh, the Sign branded at full claim -- warm light, not
    # a black void. NAMED resisters get a wound shaped like their living
    # mutation (gold maw / peeled Sign-seam / gold faces); others get the
    # generic gold rot. The dying-compulsion echo lays over the top.
    pygame.draw.rect(surf, body, (x - 11, y - 2, 24, 9))
    pygame.draw.rect(surf, body_lo, (x - 11, y - 2, 24, 9), 1)
    pygame.draw.rect(surf, body_lo, (x - 3, y + 6, 9, 3))   # outflung arm
    if mold >= 1:
        infect = _CORPSE_CLAIM.get(kind, _corpse_infect_generic)
        infect(surf, x, y, body, body_lo, mold)
    # Head lolled to one end.
    pygame.draw.circle(surf, skin, (hx, y + 2), 4)
    pygame.draw.circle(surf, body_lo, (hx, y - 1), 4, 1)   # hair/hat smudge
    # A character's dying compulsion, still acting on the floor.
    echo = _CORPSE_ECHO.get(kind)
    if echo is not None:
        echo(surf, hx, y + 2, x, y, mold)


# ---- Infested resisters (NARRATIVE infestation) -----------------------
# Each MUTATED resister has a bespoke body-horror form -- their flesh
# deforms AND the fold's gold/Sign shows in the wound ("both, fused").
# Authored as a discrete state (no crossfade), drawn OVER the base sprite
# so the person stays recognisable under the wrongness. The SAME
# transformation is authored at portrait scale in ui/dialog.py so the two
# always agree. Keyed by sprite_kind. A slow time throb keeps it alive.
_MEAT = (96, 22, 26); _MEAT_LO = (58, 12, 16); _MEAT_HI = (150, 44, 46)
_WBONE = (222, 214, 196); _WSKIN = (214, 182, 150)
_WGOLD = (236, 204, 64); _WGOLD_HI = (252, 232, 150)


def _gold_in_wound(surf, cx, cy, R, peak=64):
    """Additive gold glow welling up from inside an opened wound."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    for i in range(R, 0, -1):
        a = int(peak * (1 - i / R))
        if a > 0:
            pygame.draw.circle(g, (_WGOLD[0], _WGOLD[1], _WGOLD[2], a),
                               (R + 1, R + 1), i)
    surf.blit(g, (cx - R - 1, cy - R - 1), special_flags=pygame.BLEND_RGBA_ADD)


def _infest_tisdale_boy(surf, x, y, t):
    # The lying boy's mouth won't stop -- and now his whole BODY is the
    # mouth. A maw splits him head to hem: a dark gullet runs the length of
    # him, teeth bridging it the whole way, gold burning in the throat, his
    # eyes shoved to the corners of the cloven head. (Child geometry: head
    # ~y-8, body y..y+14 -- NOT the adult slot.)
    thr = 0.5 + 0.5 * math.sin(t * 2.6)
    hy = y - 8
    gap = 2 + int(2 * thr)                          # the maw flexes open
    _gold_in_wound(surf, x, hy + 3, 3, 30 + int(16 * thr))    # glow under, a halo
    pygame.draw.polygon(surf, _MEAT, [               # the gullet (red flesh, not a void)
        (x - gap, hy - 5), (x + gap, hy - 5),
        (x + gap + 1, y + 13), (x - gap - 1, y + 13)])
    pygame.draw.line(surf, _WGOLD, (x, hy - 3), (x, y + 11), 1)   # gold throat
    for ty in range(-4, 14, 3):                      # teeth bridging it all the way down
        pygame.draw.line(surf, _WBONE, (x - gap, hy + ty), (x + gap, hy + ty), 1)
    pygame.draw.circle(surf, (236, 232, 226), (x - 4, hy - 2), 1)  # eyes shoved out
    pygame.draw.circle(surf, (236, 232, 226), (x + 4, hy - 2), 1)


def _infest_hettie(surf, x, y, t):
    # Her face bloomed open -- and the bloom runs down her. The head splits
    # into a radial petal-star and the torso unzips into a vertical seam with
    # skin-petals curling out along both sides, gold burning up the opening:
    # a flayed flower the length of her. (Adult geometry: head ~y-11, body
    # y-2..y+16. Distinct from Toby's single slot -- this one SPLAYS.)
    thr = 0.5 + 0.5 * math.sin(t * 2.0)
    hy = y - 11
    _gold_in_wound(surf, x, hy, 3, 26 + int(14 * thr))        # glow under, a halo
    span = 5 + 2 * thr
    for k in range(5):                                        # head bloom: five petals
        a = -math.pi / 2 + k * (2 * math.pi / 5)
        tip = (int(x + math.cos(a) * span), int(hy + math.sin(a) * span))
        bx, by = -math.sin(a) * 2, math.cos(a) * 2
        pygame.draw.polygon(surf, _WSKIN,
                            [(int(x + bx), int(hy + by)),
                             (int(x - bx), int(hy - by)), tip])
    pygame.draw.circle(surf, _MEAT, (x, hy), 3)               # raw flesh socket
    pygame.draw.polygon(surf, _MEAT,                          # the body seam unzips
                        [(x - 2, y - 1), (x + 2, y - 1), (x + 1, y + 14), (x - 1, y + 14)])
    for sy in range(2, 15, 4):                                # skin-petals peeling off both sides
        pygame.draw.polygon(surf, _WSKIN, [(x - 2, y + sy), (x - 2, y + sy + 3), (x - 6, y + sy + 1)])
        pygame.draw.polygon(surf, _WSKIN, [(x + 2, y + sy), (x + 2, y + sy + 3), (x + 6, y + sy + 1)])
    pygame.draw.line(surf, _WGOLD, (x, y - 1), (x, y + 13), 1)  # gold up the seam
    pygame.draw.line(surf, _WGOLD, (x, hy - 2), (x, hy + 2), 1)  # the Sign glint
    pygame.draw.line(surf, _WGOLD, (x, hy), (x - 2, hy - 1), 1)
    pygame.draw.line(surf, _WGOLD, (x, hy), (x + 2, hy - 1), 1)


def _infest_old_townsman(surf, x, y, t):
    # (Garrick) skinned featureless -- and faces strain up through the skin
    # all OVER him: the screaming face on the smooth head, and more surfacing
    # through the coat -- eye-pits and open mouths pushing out across the
    # torso, gold burning behind each. The whole man is crawling with faces.
    # (Adult geometry: head ~y-12, body y-2..y+16. Distinct: a CROWD of faces.)
    thr = 0.5 + 0.5 * math.sin(t * 2.2)

    def face(cx, cy, push):
        _gold_in_wound(surf, cx, cy, 2, 20 + int(12 * thr))
        pygame.draw.circle(surf, _MEAT_LO, (cx - 2, cy - 1 - push), 1)   # sunken eye-pits
        pygame.draw.circle(surf, _MEAT_LO, (cx + 2, cy - 1 - push), 1)   # (dark flesh, not void)
        pygame.draw.ellipse(surf, _MEAT_LO, (cx - 1, cy + 1, 3, 3 + push))  # open mouth
        pygame.draw.line(surf, _WGOLD, (cx, cy + 1), (cx, cy + 2 + push), 1)

    hy = y - 12
    push = int(2 * thr)
    pygame.draw.circle(surf, _WSKIN, (x, hy), 6)              # the blank skinned dome
    face(x, hy, push)                                         # the head's screaming face
    face(x - 4, y + 3, push)                                  # more straining through the coat
    face(x + 4, y + 8, 0)
    face(x - 2, y + 13, push)


_INFEST_WORLD = {
    "tisdale_boy": _infest_tisdale_boy,
    "hettie": _infest_hettie,
    "old_townsman": _infest_old_townsman,
}


def draw_infested_overlay(surf, x, y, kind):
    """Drawn OVER a mutated resister's base sprite: their bespoke flesh-
    horror form. Falls back to a generic jaundice + eye-void wash for any
    kind without a dedicated incident."""
    fn = _INFEST_WORLD.get(kind)
    t = pygame.time.get_ticks() / 1000.0
    if fn is not None:
        fn(surf, x, y, t)
        return
    # Generic fallback (unchanged from the old overlay).
    wash = pygame.Surface((26, 36), pygame.SRCALPHA)
    wash.fill((168, 142, 56, 42))
    surf.blit(wash, (x - 13, y - 22))
    pygame.draw.rect(surf, (2, 0, 4), (x - 3, y - 13, 2, 2))
    pygame.draw.rect(surf, (2, 0, 4), (x + 1, y - 13, 2, 2))


def view_from_facing(fx, fy, yaw):
    """Camera-relative sprite view -- 'front' / 'back' / 'left' / 'right' -- for
    an actor facing world (fx, fy) under a camera yawed by `yaw` (Tier-2 / 2.5D
    sprites). The viewer sits below the screen, so an actor facing toward
    screen-bottom shows its FRONT, screen-top its BACK, the sides a profile.
    Four equal 90deg quadrants. At pitch 0 the live game never asks for a view
    (stays flat/front), so this only drives the oblique look mode."""
    th = math.degrees(math.atan2(fy, fx) - yaw)
    th = (th + 180) % 360 - 180
    if 45 <= th < 135:
        return "front"
    if -135 <= th < -45:
        return "back"
    if -45 <= th < 45:
        return "right"
    return "left"


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None,
                        prone=False, view="front"):
    """THRESHOLD: the private investigator, 1994. A long dark wool
    overcoat over a pale collar, dark trousers, scuffed work boots --
    the silhouette of a man who drove here on a case, not a tourist.
    Muted to sit in the graded, desaturated palette. Armor overlays
    are vestigial (combat is gone) but still draw if equipped so old
    saves render cleanly.

    A faint ground-shadow ellipse roots the player in the scene.
    None of the NPCs cast a shadow, by design -- the player is the
    only thing here that's properly *here*."""
    coat    = (56, 52, 56)        # worn dark wool overcoat
    coat_lo = (37, 34, 39)        # coat shadow side / hem
    collar  = (150, 146, 138)     # pale shirt collar
    pants   = (40, 38, 45)        # dark trousers
    boots   = (34, 26, 20)        # scuffed work boots
    skin    = (188, 158, 134)     # muted
    hair    = (52, 40, 30)
    if prone:
        # Lying on the cot. Compress the figure to a horizontal
        # silhouette with a thin blanket overlay. Drawn off-centre
        # so it reads as resting on the bedding rather than on the
        # floor.
        bx = x - 12
        by = y - 2
        # Blanket / quilt
        pygame.draw.rect(surf, (90, 60, 70), (bx, by, 24, 9))
        pygame.draw.rect(surf, (60, 40, 50), (bx, by, 24, 9), 1)
        # Head poking out at one end
        pygame.draw.circle(surf, skin, (bx + 22, by + 4), 4)
        pygame.draw.rect(surf, hair, (bx + 19, by, 7, 4))
        # Eyes closed: a thin dark line
        pygame.draw.line(surf, (40, 30, 24),
                         (bx + 21, by + 4), (bx + 24, by + 4), 1)
        # One boot peeking out the foot end
        pygame.draw.rect(surf, boots, (bx, by + 5, 4, 3))
        return
    # Ground shadow under the boots (drawn first so the body sits on it).
    shadow = pygame.Surface((22, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 22, 8))
    surf.blit(shadow, (x - 11, y + 16))
    # Trousers (legs), under the coat hem.
    pygame.draw.rect(surf, pants, (x - 6, y + 9, 12, 6))
    # The overcoat: a long slab from shoulders to mid-thigh -- the PI
    # silhouette. Shadowed on the right side + along the hem for form.
    pygame.draw.rect(surf, coat, (x - 8, y - 5, 16, 17))
    pygame.draw.rect(surf, coat_lo, (x + 3, y - 5, 5, 17))   # right shadow side
    pygame.draw.rect(surf, coat_lo, (x - 8, y + 9, 16, 3))   # hem shadow
    pygame.draw.line(surf, coat_lo, (x, y - 3), (x, y + 8), 1)  # front seam
    # Head + hair + collar, oriented to the camera-relative VIEW so the PI
    # reads from any angle -- in the follow-cam he's usually seen from BEHIND.
    if view == "back":
        pygame.draw.rect(surf, coat_lo, (x - 3, y - 5, 6, 2))    # dark nape collar
        pygame.draw.circle(surf, skin, (x, y - 12), 7)
        pygame.draw.circle(surf, hair, (x, y - 13), 7)           # back of the skull
        pygame.draw.rect(surf, skin, (x - 2, y - 7, 4, 2))       # neck sliver
    elif view in ("left", "right"):
        s = 1 if view == "right" else -1
        pygame.draw.rect(surf, collar, (x - 3 + s, y - 5, 6, 3))
        pygame.draw.circle(surf, skin, (x + s, y - 12), 7)
        pygame.draw.rect(surf, hair, (x - 7, y - 18, 14, 6))     # top hair
        pygame.draw.circle(surf, hair, (x - 4 * s, y - 13), 5)   # hair swept rearward
        pygame.draw.rect(surf, skin, (x + 6 * s, y - 12, 2, 2))  # nose bump
    else:
        # Pale collar at the throat.
        pygame.draw.rect(surf, collar, (x - 3, y - 5, 6, 3))
        # Head
        pygame.draw.circle(surf, skin, (x, y - 12), 7)
        # Hair across the top
        pygame.draw.rect(surf, hair, (x - 7, y - 18, 14, 6))
    # Boots: walking animation
    leg_off = int(math.sin(walk_phase) * 2)
    pygame.draw.rect(surf, boots, (x - 6, y + 14, 5, 4 + max(0, -leg_off)))
    pygame.draw.rect(surf, boots, (x + 1, y + 14, 5, 4 + max(0, leg_off)))
    # Eyes -- only when the face is toward the camera.
    if view == "back":
        pass
    elif view in ("left", "right"):
        s = 1 if view == "right" else -1
        pygame.draw.circle(surf, C_BLACK, (x + 2 * s, y - 12), 1)   # one eye, profile
    else:
        # Eyes (look in facing direction)
        fx, fy = facing
        eye_y = y - 12 + int(fy * 2)
        eye_dx = int(fx * 2)
        pygame.draw.circle(surf, C_BLACK, (x - 2 + eye_dx, eye_y), 1)
        pygame.draw.circle(surf, C_BLACK, (x + 2 + eye_dx, eye_y), 1)


# ===========================================================================
# THE KING IN YELLOW
#
# A floating tear-in-space: a churning clot of sick-gold light packed with the
# cult's fused faces, broken arms reaching out to grasp, shedding a wake of
# glowing soul-orbs as it drifts -- hell, chasing you. It births by tearing a
# rift open (driven by the NPC's `birth` 0..1), floats and never phases out
# (only the individual masks surface and dissolve), and the reaching arms
# swivel smoothly toward the player. Drawn from draw_npc_sprite's yellow_king
# dispatch as _draw_king(surf, x, y, facing, t, birth, gait).
# ===========================================================================
_YK_TRAIL = []                       # recent mass-centre screen positions
_YK_PARTS = []                       # particle wake: dicts x,y,vx,vy,age,life,r,kind
_YK_LAST = [0.0]                     # last draw time (for particle dt)
_YK_ACC = [0.0]                      # distance accumulator (spaces shed orbs)
_YK_AIM = [None]                     # smoothed arm-aim angle (swivels to player)
_YK_PREV = [None]                    # last mass-centre, for the movement wake


def reset_king_fx():
    """Clear the King's per-manifestation render state (trail, particle
    wake, aim/accumulators). These are module globals so a single King can
    keep frame-to-frame state cheaply -- but they outlive the King NPC, so
    his trail/particles would otherwise bleed from one manifestation (or
    one run) into the next. Game calls this on despawn and on New Game.
    The colour/curve constants below are NOT touched -- they're immutable."""
    _YK_TRAIL.clear()
    _YK_PARTS.clear()
    _YK_LAST[0] = 0.0
    _YK_ACC[0] = 0.0
    _YK_AIM[0] = None
    _YK_PREV[0] = None
_YK_PRNG = random.Random(99)         # own RNG -> never touches the game's stream
_YK_T1, _YK_T2, _YK_T3, _YK_T4 = (140, 96, 22), (196, 150, 42), (236, 198, 66), (252, 226, 120)
_YK_GOLD, _YK_HOT = (236, 204, 64), (252, 226, 120)
_YK_PALE, _YK_WHITE = (248, 232, 150), (255, 248, 224)   # bright gold -> white core
_YK_PIT = (10, 8, 12)
_YK_SHADOW, _YK_SHADOW_HI = (20, 16, 26), (52, 44, 64)   # dark grabbing arms
# Existence curve: the King stays a dark void until threat passes _LO, then the
# light blooms in hard, fully real by _HI -- so most of the approach is dread.
# Pushed late on purpose: the blaze is a brief punctuation at the kill, not the
# bulk of the encounter. Most of the approach lives in the withheld void.
_YK_BLOOM_LO, _YK_BLOOM_HI = 0.6, 0.92
# PALLID mask tones -- sickly bone, jaundiced, cold against the warm light, so a
# dead face reads as it surfaces from the glow. Black voids, not warm sockets.
_YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT = (226, 224, 196), (172, 174, 132), (98, 100, 64), (12, 12, 10)


def _yk_slots():
    """Deterministic swirl params for the faces (own RNG so the global stream the
    game relies on is never touched). Index 0 is the dominant central mask (drawn
    anchored, not orbiting); the rest orbit and erupt around it as it manifests."""
    r = random.Random(20240611)
    faces = [(0.16, 0.0, 0.22, 10, 0.55, 0.0, "scream")]
    for k in ["hollow", "double", "scream", "hollow", "scream"]:
        faces.append((
            r.uniform(0.34, 0.82), r.uniform(0, math.tau), r.uniform(0.30, 0.80),
            r.randint(6, 9), r.uniform(0.5, 1.2), r.uniform(0, 6.28), k))
    return faces


_YK_FACES = _yk_slots()

# --- THE PALLID MASK (the worn face) ---------------------------------------
# The King's silhouette is a serene, weeping porcelain mask: a clean ovoid,
# big black vacuous voids for eyes, black tear-streaks, no mouth. The YELLOW
# does not glow from a warm body any more -- it lives BEHIND the mask, and only
# erupts (gold blazing through the cracks, dark arms reaching) once he rouses.
# Pallid bone tones; the eyes/tears are one pure black so the void reads.
_YK_PORC    = (210, 202, 184)
_YK_PORC_MD = (174, 166, 148)
_YK_PORC_LO = (126, 120, 106)
_YK_PORC_DK = (84, 80, 70)
_YK_HOLLOW  = (4, 4, 6)              # eyes + tears: one pure black void
_YK_DEEP    = (140, 96, 22)         # the Yellow, deepest amber (== _YK_T1)
# How large the King draws relative to the body art (he should loom over the
# player but leave the particle wake room to read). Tuned in-scene against the
# player sprite. The body LAYER is rendered at full internal res then scaled
# down on blit, so geometry stays crisp and the world-space wake reads larger.
_YK_SCALE = 0.75
_YK_SHARDS = None                   # cached fracture geometry (lazy)


def _yk_glow_disc(surf, x, y, r, col, a):
    """Additive soft disc (own helper so the mask FX never disturb the death
    cutscene's _yk_radial tuning). Alpha falls off as the square of radius."""
    r = int(r)
    if r < 1 or a <= 0:
        return
    g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for i in range(r, 0, -1):
        pygame.draw.circle(g, (*col, int(a * (i / r) ** 2)), (r, r), i)
    surf.blit(g, (int(x) - r, int(y) - r), special_flags=pygame.BLEND_RGBA_ADD)


def _yk_fracture(F, n_ang=13, rings=(0.0, 0.46, 1.0)):
    """Radial cracked-plate shards tiling the FxF mask. Each shard: a polygon in
    surface coords + an outward unit vector from the mask centre + a spin sign.
    Cached -- the break pattern is fixed, only how far the shards fly varies."""
    global _YK_SHARDS
    if _YK_SHARDS is not None:
        return _YK_SHARDS
    cx = cy = F / 2
    rng = random.Random(7)           # own RNG -> never touches the game stream
    angs = [i / n_ang * math.tau + rng.uniform(-0.12, 0.12) for i in range(n_ang + 1)]
    rad = F * 0.5
    shards = []
    for i in range(n_ang):
        a0, a1 = angs[i], angs[i + 1]
        for j in range(len(rings) - 1):
            r0 = rings[j] * rad * (1 + rng.uniform(-0.06, 0.06) if j else 0)
            r1 = rings[j + 1] * rad * (1 + rng.uniform(-0.08, 0.08)
                                       if j + 1 < len(rings) - 1 else 1)
            poly = [
                (cx + math.cos(a0) * r0, cy + math.sin(a0) * r0 * 1.12),
                (cx + math.cos(a1) * r0, cy + math.sin(a1) * r0 * 1.12),
                (cx + math.cos(a1) * r1, cy + math.sin(a1) * r1 * 1.12),
                (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1 * 1.12),
            ]
            mx = sum(p[0] for p in poly) / 4 - cx
            my = sum(p[1] for p in poly) / 4 - cy
            ml = math.hypot(mx, my) or 1
            shards.append((poly, (mx / ml, my / ml), rng.choice((-1, 1)) * rng.uniform(0.6, 1.6)))
    _YK_SHARDS = shards
    return shards


def _yk_pallid_face(F, weep, void_deep, gold_seep):
    """The calm pallid mask on an FxF RGBA surface, centred. `weep` lengthens the
    tears, `void_deep` deepens the eye-voids, `gold_seep` leaks the Yellow from
    the eyes and hairline seams as he rouses (0 while serene)."""
    s = pygame.Surface((F, F), pygame.SRCALPHA)
    cx = cy = F // 2
    w, h = int(F * 0.62), int(F * 0.74)
    # ovoid body + soft form shading (light upper-left, shadow lower-right)
    pygame.draw.ellipse(s, _YK_PORC_MD, (cx - w // 2, cy - h // 2, w, h))
    hl = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (*_YK_PORC, 165), (int(-w * 0.16), int(-h * 0.08), w, h))
    s.blit(hl, (cx - w // 2, cy - h // 2))
    sh = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (*_YK_PORC_LO, 130), (int(w * 0.16), int(h * 0.10), w, h))
    s.blit(sh, (cx - w // 2, cy - h // 2))
    pygame.draw.ellipse(s, _YK_PORC_DK, (cx - w // 2, cy - h // 2, w, h), 1)
    g = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(g, (40, 36, 28, 70), (4, int(h * 0.5), w - 8, int(h * 0.5)))
    s.blit(g, (cx - w // 2, cy - h // 2))
    # hairline seams glow as he rouses (the Yellow seeping up through the cracks)
    if gold_seep > 0.01:
        rng = random.Random(3)
        for _ in range(int(6 * gold_seep) + 1):
            a = rng.uniform(0, math.tau); r0 = rng.uniform(2, 5)
            x0 = cx + math.cos(a) * r0; y0 = cy + math.sin(a) * r0
            x1 = cx + math.cos(a) * (w * 0.42); y1 = cy + math.sin(a) * (h * 0.42)
            pygame.draw.line(s, (*_YK_GOLD, int(150 * gold_seep)), (x0, y0), (x1, y1), 1)
    ew, eh = int(8 + 3 * void_deep), int(9 + 4 * void_deep)
    ex = int(w * 0.27)

    def eye(sx):
        if gold_seep > 0.01:
            _yk_glow_disc(s, cx + sx, cy - 3, ew * (1 + gold_seep), _YK_GOLD, int(120 * gold_seep))
        pygame.draw.ellipse(s, _YK_HOLLOW, (cx + sx - ew, cy - 3 - eh, ew * 2, eh * 2))
        pygame.draw.ellipse(s, (0, 0, 0), (cx + sx - ew + 2, cy - 1 - eh, ew * 2 - 4, eh * 2 - 2))
        pygame.draw.ellipse(s, _YK_PORC_DK, (cx + sx - ew, cy - 3 - eh, ew * 2, eh * 2), 1)

    def tear(sx):
        rng = random.Random(sx + 7)
        bx, by = cx + sx, cy - 3 + eh
        x2, y2 = bx, by
        for _ in range(int(10 + 14 * weep)):
            y2 += 1; x2 += rng.randint(-1, 1)
            pygame.draw.line(s, _YK_HOLLOW, (bx, by), (x2, y2), 2)
    eye(-ex); eye(ex); tear(-ex); tear(ex)
    return s


def _yk_reach(surf, ox, oy, ang, length, grab, alpha):
    """One dark grasping limb bursting from behind the mask toward `ang`, with a
    faint gold-lit tip and a clawed end that splays as `grab` rises."""
    seg = 7
    pts = []
    for i in range(seg + 1):
        f = i / seg
        a = ang + math.sin(f * 3.1 + grab * 2) * 0.3 * (1 - f)
        r = length * f
        pts.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
    for wdt, col in ((9, (*_YK_SHADOW, alpha)), (4, (*_YK_SHADOW_HI, int(alpha * 0.7)))):
        for i in range(len(pts) - 1):
            pygame.draw.line(surf, col, pts[i], pts[i + 1], max(1, int(wdt * (1 - i / seg))))
    tx, ty = pts[-1]
    _yk_glow_disc(surf, tx, ty, 5, _YK_DEEP, int(60 * grab))
    for k in range(3):                          # claw splay
        ca = ang + (k - 1) * 0.5
        cl = 6 + 5 * grab
        pygame.draw.line(surf, (*_YK_SHADOW, alpha),
                         (tx, ty), (tx + math.cos(ca) * cl, ty + math.sin(ca) * cl), 2)


def _yk_radial(surf, x, y, R, color, a0, add=True):
    """Soft glowing/fading disc built from concentric circles."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    c = (R + 1, R + 1); st = max(6, R // 2)
    for i in range(st, 0, -1):
        a = int(a0 * (1 - i / st) ** 1.7)
        if a > 0:
            pygame.draw.circle(g, (color[0], color[1], color[2], a), c, int(R * i / st))
    surf.blit(g, (int(x) - R - 1, int(y) - R - 1),
              special_flags=pygame.BLEND_RGBA_ADD if add else 0)


def _yk_glow(layer, cx, cy, R, t):
    """A clot of bright gold light. Orange lives ONLY in the soft aura behind the
    mass, so it reads as the warm outline of the whole silhouette; the bright
    lumpy body is drawn opaque on top, so it never goes orange between its blobs."""
    R = int(R * (1 + 0.06 * math.sin(t * 2.0)))
    # warm orange outline: a broad aura behind everything (shows only at the rim).
    _yk_radial(layer, cx, cy, int(R * 1.95), _YK_T1, 72)
    _yk_radial(layer, cx, cy, int(R * 1.5), _YK_T2, 58)
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    sw = t * 0.6
    ca, sa = math.cos(sw), math.sin(sw)
    # gold body, drawn opaque so it covers the centre. It SMOULDERS gold/pale
    # rather than blazing white -- the white-hot stab is added only on the lunge
    # (the flare punch in _draw_king), so darkness keeps the upper hand.
    for col, scl, grow in [(_YK_T3, 1.06, 3), (_YK_T3, 0.74, 1), (_YK_PALE, 0.36, 0)]:
        for ox, oy in subs:
            rx, ry = ox * ca - oy * sa, ox * sa + oy * ca
            pygame.draw.circle(layer, col,
                               (int(cx + rx * R * 0.6), int(cy + ry * R * 0.9)),
                               int(R * 0.5 * scl) + grow)
    for k in range(4):
        a = sw * 1.6 + k * 1.57
        _yk_radial(layer, cx + math.cos(a) * R * 0.42, cy + math.sin(a) * R * 0.42,
                   int(R * 0.36), _YK_GOLD, 34)
    _yk_radial(layer, cx, cy - 2, int(R * 0.42), _YK_PALE, 30)


# Slot/orb kind vocabulary -> facial expression. The faces read as people:
# a dead, pallid human face surfaces from the light, mostly shrieking.
_YK_EXPR = {"hollow": "gaunt", "crack": "scream", "plain": "calm"}


def _yk_face(m, mx, my, r, expr, detail, mouth=True):
    """A readable human face on mask-surface `m`: pallid oval lit upper-left,
    brow ridge, nose ridge, eyes + an expressive mouth. `detail` gates the
    eyes/brow/nose in as the mask surfaces (so it emerges as a blank pallid
    shape first); `mouth` gates the LOUD features (mouth, tears, crack)
    separately and later -- so a hollow, mouthless STARE precedes the scream."""
    hi, mid, lo, pit = _YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT
    rw, rh = r, int(r * 1.24)                             # a little oblong -- a head, not a ball
    pygame.draw.ellipse(m, lo, (mx - rw + 1, my - rh + 1, 2 * rw, 2 * rh))
    pygame.draw.ellipse(m, mid, (mx - rw, my - rh, 2 * rw, 2 * rh))
    pygame.draw.ellipse(m, hi, (mx - rw + 1, my - rh, max(1, 2 * rw - 2), max(1, 2 * rh - 3)))
    if not detail or r < 3:
        return
    ew = max(1, r // 3)
    eyl = (mx - r * 0.42, my - r * 0.12)
    eyr = (mx + r * 0.42, my - r * 0.12)
    bw = max(1, r // 4)
    pygame.draw.line(m, lo, (int(mx - r * 0.7), int(my - r * 0.45)), (int(mx - r * 0.05), int(my - r * 0.30)), bw)
    pygame.draw.line(m, lo, (int(mx + r * 0.7), int(my - r * 0.45)), (int(mx + r * 0.05), int(my - r * 0.30)), bw)
    pygame.draw.line(m, lo, (int(mx), int(my - r * 0.1)), (int(mx), int(my + r * 0.25)), 1)
    pygame.draw.line(m, hi, (int(mx - 1), int(my - r * 0.1)), (int(mx - 1), int(my + r * 0.2)), 1)
    if expr in ("scream", "gaunt", "vacant", "wail"):    # vacuous void sockets
        if expr in ("vacant", "wail"):                   # deep OBLONG sockets (eye-shaped,
            w2 = max(2, int(ew * 1.7))                   # not round lenses), each holding a
            h2 = max(3, int(ew * 2.5))                   # golden gaze: a single pixel while
            for ex, ey in (eyl, eyr):                    # calm, flaring once angry
                pygame.draw.ellipse(m, pit, (int(ex - w2 / 2), int(ey - h2 / 2), w2, h2))
                if expr == "wail":
                    _yk_radial(m, ex, ey, 2, _YK_HOT, 150)
                try:
                    m.set_at((int(ex), int(ey)), _YK_HOT)
                except (IndexError, ValueError):
                    pass
        else:
            for ex, ey in (eyl, eyr):
                pygame.draw.ellipse(m, pit, (int(ex - ew), int(ey - ew), 2 * ew, int(2.2 * ew)))
    else:
        for ex, ey in (eyl, eyr):
            pygame.draw.line(m, pit, (int(ex - ew), int(ey)), (int(ex + ew), int(ey)), 1)
        if expr == "weep":
            for ex, ey in (eyl, eyr):
                pygame.draw.line(m, hi, (int(ex), int(ey + 1)), (int(ex), int(my + r * 0.6)), 1)
    if not mouth:                                        # hold on the hollow STARE:
        return                                           # mouth/tears/crack withheld
    if expr == "wail":                                   # black tears down the mask
        for ex, ey in (eyl, eyr):
            pygame.draw.line(m, pit, (int(ex), int(ey + ew)),
                             (int(ex + r * 0.06), int(my + r * 0.98)), max(1, r // 5))
    mym = my + r * 0.55
    if expr in ("scream", "wail"):
        pygame.draw.ellipse(m, pit, (int(mx - r * 0.32), int(mym - r * 0.1),
                                     max(2, int(r * 0.64)), max(3, int(r * 0.85))))
    elif expr == "gaunt":
        pygame.draw.ellipse(m, pit, (int(mx - r * 0.28), int(mym - r * 0.05),
                                     max(2, int(r * 0.56)), max(2, int(r * 0.5))))
        pygame.draw.line(m, lo, (int(mx - r * 0.7), int(my)), (int(mx - r * 0.5), int(my + r * 0.4)), 1)
        pygame.draw.line(m, lo, (int(mx + r * 0.7), int(my)), (int(mx + r * 0.5), int(my + r * 0.4)), 1)
    elif expr == "vacant":                               # a gaping, downturned grimace -- :(
        gw = max(3, int(r * 0.52))
        gh = max(3, int(r * 0.5))
        gx, gy = int(mx - gw / 2), int(mym - r * 0.04)
        pygame.draw.ellipse(m, pit, (gx, gy, gw, gh))     # the open gape
        pygame.draw.line(m, pit, (gx + 1, int(gy + gh * 0.2)),               # corners
                         (int(mx - gw * 0.85), int(gy + gh * 0.95)), 1)      # pulled
        pygame.draw.line(m, pit, (gx + gw - 1, int(gy + gh * 0.2)),          # down into
                         (int(mx + gw * 0.85), int(gy + gh * 0.95)), 1)      # a frown
    elif expr == "smile":
        pts = [(mx - r * 0.4, mym - r * 0.1), (mx, mym + r * 0.2), (mx + r * 0.4, mym - r * 0.1)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    elif expr == "weep":
        pts = [(mx - r * 0.4, mym + r * 0.15), (mx, mym - r * 0.1), (mx + r * 0.4, mym + r * 0.15)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    else:
        pygame.draw.line(m, pit, (int(mx - r * 0.3), int(mym)), (int(mx + r * 0.3), int(mym)), 1)
    if expr in ("vacant", "wail"):                       # a jagged fracture down one side --
        crk = [(mx + r * 0.12, my - rh * 0.92), (mx + r * 0.32, my - r * 0.2),
               (mx + r * 0.14, my + r * 0.45), (mx + r * 0.3, my + rh * 0.6)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in crk], 1)


def _yk_mask(surf, cx, cy, r, vis, kind, mouth=True):
    """A dead human FACE surfacing from the light: pallid, translucent (the glow
    reads through it) + a luminous halo, rising (vis->1) and dissolving back into
    the glow (vis->0). 'double' is two faces fused, both shrieking. `mouth=False`
    holds the face on a mouthless stare even after the eyes have resolved."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(3, r // 2)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = r + pad
    detail = vis > 0.35
    if kind == "double":
        off = max(2, r // 2)
        for ddx in (-off, off):
            _yk_face(m, mx + ddx, my, max(2, int(r * 0.78)), "scream", detail, mouth)
    else:
        _yk_face(m, mx, my, r, _YK_EXPR.get(kind, kind), detail, mouth)
    m.set_alpha(int(64 + 156 * vis))
    surf.blit(m, (cx - mx, cy - my))


def _jag_blob(surf, cx, cy, rx, ry, col, seed, n=10, jit=0.36):
    """An irregular dark void -- an ellipse-ish polygon with jittered radii so
    it never reads as a clean oblong or circle. Seeded for a stable shape."""
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        a = (i / n) * math.tau
        jx = rx * (1.0 - jit + 2 * jit * rng.random())
        jy = ry * (1.0 - jit + 2 * jit * rng.random())
        pts.append((int(cx + math.cos(a) * jx), int(cy + math.sin(a) * jy)))
    pygame.draw.polygon(surf, col, pts)


def door_mask_surface(height=120, vis=0.62, gaze=(0.0, 0.0), seed=0):
    """The wrong face the threshold wears, for the journal door-dream's
    mask swarm: a carved DARK-WOOD mask (matches the dried doorframe +
    the cult's own carved masks). Rounded, slightly-imperfect oval with wood
    grain; deep RECESSED eye-sockets -- carved hollows with the gold gaze
    sitting far back in shadow (it looks back at you from inside the wood) --
    and NO MOUTH at all, a blank lower face (the most alien, unsettling
    read). Kept fairly opaque so the wood reads dark even against the doorway
    glow, with a luminous halo around it. Built small + smooth-scaled up so
    it surfaces half-seen. `vis` drives gaze brightness + a little opacity.
    `gaze` (gx, gy in -1..1) shifts the gold pupil within each socket so the
    eyes can POINT -- e.g. toward the camera/player from anywhere on the
    door, so a throng of them all turn to look at you."""
    # dark walnut: (highlight grain, base, shadow, deep split)
    WHI, WMID, WLO, WDK = (124, 90, 52), (84, 58, 34), (50, 34, 20), (26, 17, 10)
    r = 22
    rw, rh = r, int(r * 1.42)                 # rounded oval, taller than wide
    pad = max(6, r // 2 + 8)
    S = (rw + pad) * 2
    Sh = (rh + pad) * 2
    base = pygame.Surface((S, Sh), pygame.SRCALPHA)
    mx, my = S // 2, Sh // 2
    pa = 252                                   # darkwood -> OPAQUE, so the wood
    #                                          # reads dark over the bright glow
    #                                          # (no need to dim the glow itself)
    # luminous gold halo behind the wood
    _yk_radial(base, mx, my, int(rh * 0.84), _YK_HOT, int(42 * vis))
    # rounded carved-wood plate (subtle imperfect edge), lit upper-left
    _jag_blob(base, mx, my, rw + 1, rh + 1, (*WDK, pa), 4, n=30, jit=0.06)
    _jag_blob(base, mx, my, rw, rh - 1, (*WMID, pa), 4, n=30, jit=0.06)
    _jag_blob(base, mx - 1, my - 2, int(rw * 0.86), int((rh - 3) * 0.9),
              (*WHI, int(pa * 0.5)), 4, n=30, jit=0.06)
    # vertical wood grain (kept inside the oval so it never pokes out)
    for gi in range(7):
        gx = int(mx + (gi - 3) / 3.4 * rw * 0.78)
        col = WHI if gi in (2, 5) else WLO
        pts = [(int(gx + math.sin(s * 0.9 + gi) * 1.4),
                int(my - rh * 0.58 + (rh * 1.16) * s / 9)) for s in range(10)]
        pygame.draw.lines(base, (*col, int(pa * 0.55)), False, pts, 1)
    # RECESSED sockets: deep carved hollows (dark -> near-black gradient) with
    # the gold gaze deep at the bottom -- looking back from inside the wood.
    # NO MOUTH (blank lower face).
    gx = max(-1.0, min(1.0, gaze[0]))
    gy = max(-1.0, min(1.0, gaze[1]))
    for dx, dy, sd in ((-0.40, -0.29, 11 + seed), (0.40, -0.30, 27 + seed)):
        ex, ey = int(mx + r * dx), int(my + r * dy)
        for i, (rr, a, c) in enumerate([(0.52, 185, (40, 30, 20)),
                                        (0.40, 215, (24, 18, 12)),
                                        (0.28, 240, (8, 6, 5))]):
            _jag_blob(base, ex, ey, r * rr, r * rr * 1.2, (*c, a),
                      sd + i, n=12, jit=0.22)
        # the gold pupil sits in the socket, shifted by `gaze` so it POINTS --
        # toward the camera from wherever this mask is. Drawn legibly: a soft
        # bloom, a solid gold disc, and a white-hot centre so the aim reads
        # even in a throng of small faces.
        px = int(ex + gx * r * 0.22)
        py = int(ey + 1 + gy * r * 0.22)
        _yk_radial(base, px, py, 4, _YK_HOT, int(150 * vis))   # bloom
        pygame.draw.circle(base, _YK_GOLD, (px, py), max(2, int(r * 0.13)))
        pygame.draw.circle(base, _YK_HOT, (px, py), max(1, int(r * 0.07)))
        try:
            base.set_at((px, py), (255, 252, 236))            # white-hot core
        except (IndexError, ValueError):
            pass
    # one subtle wood split for carved character, clear of the sockets
    crk = [(int(mx + r * 0.54), int(my + r * 0.06)),
           (int(mx + r * 0.72), int(my + r * 0.50)),
           (int(mx + r * 0.52), int(my + rh * 0.60))]
    pygame.draw.lines(base, (*WDK, pa), False, crk, 1)
    # Scale to the target HEIGHT, preserving the tall aspect (don't squash).
    h = max(1, int(height))
    if h != Sh:
        w = max(1, int(S * h / Sh))
        base = pygame.transform.smoothscale(base, (w, h))
    return base


# A shed SOUL-ORB in the wake is drawn in two passes (glow, then faces) so that
# every orb's masks sit on top of every orb's glow, regardless of shed order.
_YK_ORB_KINDS = ("plain", "scream", "hollow", "crack")


def _yk_orb_glow(surf, cx, cy, r, vis):
    """The orb's glowing gold clot (no faces) -- a small copy of the body."""
    if vis <= 0.04:
        return
    _yk_radial(surf, cx, cy, int(r * 2.4), _YK_T1, int(34 * vis))   # warm orange aura
    _yk_radial(surf, cx, cy, int(r * 1.8), _YK_GOLD, int(46 * vis))
    _yk_radial(surf, cx, cy, int(r * 1.05), _YK_T2, int(58 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.62), _YK_T3, int(72 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.32), _YK_T4, int(88 * vis))


def _yk_orb_faces(surf, cx, cy, r, vis, seed, t):
    """The mask(s) floating in the orb -- drawn in the second pass so they read
    over the whole wake of glow, not just their own orb."""
    if vis <= 0.04:
        return
    for k in range(2 if r >= 9 else 1):
        ang = seed * 1.7 + k * 2.4 + t * 1.4
        rad = r * 0.36
        _yk_mask(surf, cx + math.cos(ang) * rad, cy + math.sin(ang) * rad,
                 max(3, int(r * 0.44)), vis * 0.9, _YK_ORB_KINDS[(seed + k) % 4])


def _yk_void(layer, cx, cy, R):
    """The barely-existing form, seen while the King is still far: a void darker
    than the dark, edged in a cold shimmer, and DEAD STILL. The only thing that
    moves or shows a face is the pale mask, drawn over this by the caller."""
    _yk_radial(layer, cx, cy, int(R * 1.4), (58, 62, 86), 50)    # cold shimmer rim
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    for ox, oy in subs:                                          # static lumps -- no swirl
        pygame.draw.circle(layer, (8, 7, 12),
                           (int(cx + ox * R * 0.6), int(cy + oy * R * 0.9)), int(R * 0.58), 0)


def _yk_spire(layer, bx, by, ang, length, R, t, idx, m, dk, gold, hot):
    """One spire of the crown: a bold black/gold bent arm (shoulder -> reflex
    elbow -> grasping claw) rising from the circlet as a crown point. Stable
    (always present -- a crown, not a flicker), with a slow sway and grasp."""
    a = ang + math.sin(t * 0.9 + idx * 1.1) * 0.09
    perp = (-math.sin(a), math.cos(a))
    bend = length * 0.22 * (1 if idx % 2 else -1)
    mid = (bx + math.cos(a) * length * 0.55, by + math.sin(a) * length * 0.55)
    elbow = (mid[0] + perp[0] * bend, mid[1] + perp[1] * bend)
    hand = (bx + math.cos(a) * length, by + math.sin(a) * length)
    ip = [(int(bx), int(by)), (int(elbow[0]), int(elbow[1])), (int(hand[0]), int(hand[1]))]
    w = max(2, int(R * 0.14))
    for px, py in ip:                                            # gold under-glow
        _yk_radial(layer, px, py, w + 1, _YK_GOLD, int(85 * m))
    pygame.draw.lines(layer, gold, False, ip, w + 1)             # gold edge
    pygame.draw.lines(layer, dk, False, ip, w)                   # black core
    grab = 0.4 + 0.45 * (0.5 + 0.5 * math.sin(t * 0.7 + idx * 0.8))
    ha = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])
    fl = length * 0.34
    for fa in (-38, 0, 38):                                      # grasping claw at the tip
        a2 = ha + math.radians(fa) - (1 if fa >= 0 else -1) * grab * 0.7
        tip = (hand[0] + math.cos(a2) * fl, hand[1] + math.sin(a2) * fl)
        pygame.draw.line(layer, dk, (int(hand[0]), int(hand[1])),
                         (int(tip[0]), int(tip[1])), max(1, w - 1))
        try:
            layer.set_at((int(tip[0]), int(tip[1])), hot)
        except (IndexError, ValueError):
            pass


def _yk_shatter_mask(surf, cx, cy, r, vis, kind, crack, t, R, aim=0.0, arms=True):
    """THE SILHOUETTE: the mask. Intact when calm, but as the King rouses it
    CRACKS and splits into shards that drift apart -- the grasping arms burst
    from the splits and span the gaps, the light blazing through the cracks. A
    broken face barely held together by the limbs inside it. `crack` also runs
    in REVERSE at birth (shards converging into the whole mask); `arms` is off
    then, so the birth is a clean assembly with no grasping."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(6, r)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mxc = myc = r + pad
    # The mouth/scream is held back until the mask is genuinely cracking open --
    # the stare comes first, the scream is the late reveal.
    _yk_face(m, mxc, myc, r, _YK_EXPR.get(kind, kind), vis > 0.35, crack > 0.45)
    alpha = int(64 + 156 * vis)
    if crack <= 0.04:                                   # intact mask
        m.set_alpha(alpha)
        surf.blit(m, (cx - mxc, cy - myc))
        return
    n = 7
    n_arms = 4                                               # FEW arms -- deliberate, not a thicket
    dk, gold, hot = (*_YK_SHADOW, 255), (*_YK_GOLD, 255), (*_YK_HOT, 255)
    # A FEW arms root around the mass and reach SLOWLY for the player: a long,
    # deliberate stretch out and an equally slow draw back, each on its own
    # unhurried cycle. The closer it gets (crack -> 1) the further each reaches.
    # Suppressed during the birth assembly.
    for i in range(n_arms if arms else 0):
        rho = i * math.tau / n_arms + 0.5 * math.sin(i * 2.3)    # roots scattered around
        rx = cx + math.cos(rho) * r * 0.55
        ry = cy + math.sin(rho) * r * 0.55
        spd = 0.26 + 0.07 * (i % 3)                              # slow, each a little different
        ph = (t * spd + i * 0.41) % 1.0
        if ph < 0.5:                                             # slow, deliberate reach out
            u = ph / 0.5; lunge = u * u * (3 - 2 * u)
        else:                                                    # slow draw back
            u = (ph - 0.5) / 0.5; lunge = 1.0 - u * u * (3 - 2 * u)
        ln = r * (0.5 + (1.0 + 1.2 * crack) * lunge)             # reaches further up close
        ang = aim + math.sin(i * 1.7) * 0.4                      # each aimed near the player
        _yk_spire(surf, rx, ry, ang, ln, R, t, i, 1.0, dk, gold, hot)
    far = (r + pad) * 1.7
    off = r * 0.7 * crack                                # shards drift apart
    for i in range(n):
        a0 = i * math.tau / n
        bis = a0 + math.pi / n
        a1 = (i + 1) * math.tau / n
        poly = [(mxc, myc),
                (mxc + math.cos(a0) * far, myc + math.sin(a0) * far),
                (mxc + math.cos(bis) * far, myc + math.sin(bis) * far),
                (mxc + math.cos(a1) * far, myc + math.sin(a1) * far)]
        pm = pygame.Surface((S, S), pygame.SRCALPHA)
        pygame.draw.polygon(pm, (255, 255, 255, 255), [(int(x), int(y)) for x, y in poly])
        shard = m.copy()
        shard.blit(pm, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        shard.set_alpha(alpha)
        surf.blit(shard, (int(cx - mxc + math.cos(bis) * off),
                          int(cy - myc + math.sin(bis) * off)))


def _draw_king(surf, x, y, facing, t, birth, gait, threat=None):
    """THE KING IN YELLOW (see header). His silhouette is the serene PALLID MASK
    (a weeping porcelain face, black vacuous voids, no mouth); the Yellow lives
    BEHIND it and only erupts when he rouses. `birth` (0..1) assembles the mask
    from converging shards; `gait` is accepted but unused (the float needs no leg
    cycle); `threat` (0..1, the player's nearness to death) drives the
    calm->frenzy escalation -- the voids deepen and the seams seep gold, then the
    mask SHATTERS and the Yellow blazes through the cracks with dark arms
    reaching. It never phases out. Body art is drawn at full internal resolution
    and scaled by _YK_SCALE on blit, so the world-space particle wake reads large
    against him."""
    sc = _YK_SCALE
    R = 22 * sc
    bp = 1.0 if birth is None else max(0.0, min(1.0, birth))
    grow = bp * bp * (3 - 2 * bp)                          # mask assembles in
    intensity = 0.0 if threat is None else max(0.0, min(1.0, threat))
    mcx, mcy = x, int(y - 42 * sc + math.sin(t * 1.1) * 3 * sc)   # floats, gentle bob
    dt = t - _YK_LAST[0]
    _YK_LAST[0] = t
    if dt <= 0 or dt > 0.2:
        dt = 0.016
    # crack: 0 while assembling / calm; opens once fully born and threat climbs
    # past the midpoint, so the calm weeping mask reads before it ever splits.
    if bp >= 1.0:
        cm = max(0.0, (intensity - 0.5) / 0.5)
        crack = cm * cm * (3 - 2 * cm)
    else:
        crack = 0.0
    void_deep = min(1.0, intensity / 0.5)
    weep = 0.3 + 0.7 * intensity
    gold_seep = max(0.0, (intensity - 0.32) / 0.4) * (1 - crack)   # seam-glow pre-break

    # --- particles (world space): pale-ash + gold sparks, drawn straight to surf
    # so they sit at true scale around the smaller King and read with weight.
    # BIRTH pulls motes INWARD (coalescence); the break vomits sparks outward.
    if bp < 0.6:
        for _ in range(3):
            a = _YK_PRNG.uniform(0, math.tau); d = _YK_PRNG.uniform(R * 1.6, R * 3.2)
            spd = _YK_PRNG.uniform(60, 150)
            _YK_PARTS.append({"kind": "ash", "x": mcx + math.cos(a) * d, "y": mcy + math.sin(a) * d,
                              "vx": -math.cos(a) * spd, "vy": -math.sin(a) * spd,
                              "age": 0.0, "life": d / spd, "r": _YK_PRNG.uniform(2, 4)})
    if crack > 0.1 and _YK_PRNG.random() < crack:
        for _ in range(2):
            a = _YK_PRNG.uniform(0, math.tau); spd = _YK_PRNG.uniform(30, 90) * crack
            gold = _YK_PRNG.random() < 0.5
            _YK_PARTS.append({"kind": "spark" if gold else "ash",
                              "x": mcx + _YK_PRNG.uniform(-6, 6), "y": mcy + _YK_PRNG.uniform(-6, 6),
                              "vx": math.cos(a) * spd, "vy": math.sin(a) * spd - 12,
                              "age": 0.0, "life": _YK_PRNG.uniform(0.6, 1.4), "r": _YK_PRNG.uniform(2, 5)})
    # movement wake: a pale-ash trail drifts off behind him as he moves (always),
    # with gold sparks shaken loose once he has roused.
    if _YK_PREV[0] is not None:
        dx_, dy_ = mcx - _YK_PREV[0][0], mcy - _YK_PREV[0][1]
        disp = math.hypot(dx_, dy_)
        if 0.1 < disp < 60:                       # ignore teleports / respawn jumps
            bvx, bvy = -dx_ / disp, -dy_ / disp
            _YK_ACC[0] += disp
            while _YK_ACC[0] >= 8:
                _YK_ACC[0] -= 8
                _YK_PARTS.append({"kind": "ash",
                                  "x": mcx + _YK_PRNG.uniform(-6, 6), "y": mcy + _YK_PRNG.uniform(-4, 8),
                                  "vx": bvx * 13 + _YK_PRNG.uniform(-7, 7),
                                  "vy": bvy * 13 + _YK_PRNG.uniform(-7, 7) - 5,
                                  "age": 0.0, "life": _YK_PRNG.uniform(0.9, 1.7), "r": _YK_PRNG.uniform(2, 4)})
                if crack > 0.2 and _YK_PRNG.random() < crack:
                    _YK_PARTS.append({"kind": "spark",
                                      "x": mcx + _YK_PRNG.uniform(-5, 5), "y": mcy + _YK_PRNG.uniform(-5, 5),
                                      "vx": bvx * 10 + _YK_PRNG.uniform(-9, 9),
                                      "vy": bvy * 10 + _YK_PRNG.uniform(-9, 9),
                                      "age": 0.0, "life": _YK_PRNG.uniform(0.7, 1.3), "r": _YK_PRNG.uniform(2, 4)})
    else:
        # first frame (or post-reset): seed the wake anchor without a teleport burst.
        pass
    # teleport guard: a big jump (respawn at a new anchor) resets the wake anchor.
    if _YK_PREV[0] is not None:
        if (mcx - _YK_PREV[0][0]) ** 2 + (mcy - _YK_PREV[0][1]) ** 2 > 70 ** 2:
            _YK_PARTS.clear()
            _YK_ACC[0] = 0.0
    _YK_PREV[0] = (mcx, mcy)
    if len(_YK_PARTS) > 220:
        del _YK_PARTS[:len(_YK_PARTS) - 220]
    keep = []
    for p in _YK_PARTS:
        p["age"] += dt
        fr = p["age"] / p["life"]
        if fr >= 1.0:
            continue
        p["x"] += p["vx"] * dt; p["y"] += p["vy"] * dt
        keep.append((p, fr))
    _YK_PARTS[:] = [p for p, _ in keep]
    for p, fr in keep:
        a = 1 - fr
        if p["kind"] == "spark":
            _yk_glow_disc(surf, p["x"], p["y"], p["r"] * 2.4, _YK_HOT, int(150 * a))
        else:
            r = max(1, int(p["r"] * (1 - 0.4 * fr)))
            pygame.draw.circle(surf, (*_YK_PORC, int(150 * a)), (int(p["x"]), int(p["y"])), r)

    # faint floating ground shadow
    sh = pygame.Surface((40, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 40, 12))
    surf.blit(sh, (x - 20, y - 4))

    # arms swivel smoothly toward the player (facing)
    fxx, fyy = facing if facing != (0, 0) else (0, 1)
    tgt = math.atan2(fyy, fxx)
    if _YK_AIM[0] is None:
        _YK_AIM[0] = tgt
    _YK_AIM[0] += ((tgt - _YK_AIM[0] + math.pi) % math.tau - math.pi) * min(1.0, dt * 7.0)
    aa = _YK_AIM[0]

    # The body LAYER is rendered at full internal resolution (RI), then scaled by
    # _YK_SCALE on the final blit -- crisp geometry, and the wake reads larger.
    RI = 22
    F = 180
    cxL = F // 2
    layer = pygame.Surface((F, F), pygame.SRCALPHA)

    if grow < 0.05 and bp < 1.0:
        return

    # YELLOW blaze behind the mask, revealed by the crack -- moody amber/gold,
    # white only as a brief stab (a rare punctuation, not the resting glare).
    if crack > 0.02:
        for r, col, al in ((int(RI * 1.7), _YK_DEEP, 78), (int(RI * 1.05), _YK_GOLD, 95),
                           (int(RI * 0.6), _YK_GOLD, 110)):
            _yk_glow_disc(layer, cxL, cxL, r * (0.5 + crack), col, int(al * crack))
        flare = math.exp(-(((t * 0.5) % 1.0 - 0.5) / 0.06) ** 2)   # one slow white stab
        if flare > 0.05:
            _yk_glow_disc(layer, cxL, cxL, RI * 0.5, _YK_HOT, int(120 * crack * flare))
        if crack > 0.4:                            # a screaming maw through the gap
            pygame.draw.ellipse(layer, (*_YK_HOT, int(200 * (crack - 0.4))),
                                (cxL - 5, cxL + 2, 10, int(6 + 10 * crack)))

    # arms BURST from the shatter seams and reach for the player.
    if crack > 0.05:
        al = int(245 * crack)
        length = RI * (1.8 + 2.0 * crack) * (0.55 + 0.45 * intensity)
        for offa in (-0.95, -0.5, 0.0, 0.5, 0.95):
            ax = cxL + math.cos(aa + offa) * RI * 0.5 * crack
            ay = cxL + 2 + math.sin(aa + offa) * RI * 0.5 * crack
            _yk_reach(layer, ax, ay, aa + offa, length * (1.0 - 0.22 * abs(offa)), crack, al)

    # THE MASK: assemble (birth) / whole (calm) / shatter (frenzy). Rendered at a
    # fixed size MF, centred into the larger arm-holding layer.
    MF = 120
    moff = (F - MF) // 2
    face = _yk_pallid_face(MF, weep, void_deep, gold_seep)

    def blit_shards(spread, spin_amt, alpha):
        for poly, (ux, uy), spin in _yk_fracture(MF):
            shard = face.copy()
            mask = pygame.Surface((MF, MF), pygame.SRCALPHA)
            pygame.draw.polygon(mask, (255, 255, 255, 255), poly)
            shard.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            rot = pygame.transform.rotate(shard, math.degrees(spin) * spin_amt)
            rot.set_alpha(int(alpha))
            layer.blit(rot, (moff + ux * spread - (rot.get_width() - MF) / 2,
                             moff + uy * spread - (rot.get_height() - MF) / 2))

    if bp < 1.0:
        # ASSEMBLY: the shatter run in REVERSE -- shards converge into the whole.
        d = 1.0 - grow
        blit_shards(d * RI * 2.4, d * 0.5, 255 * grow)
    elif crack <= 0.02:
        layer.blit(face, (moff, moff))             # CALM: the whole weeping mask
    else:
        # SHATTER: shards fly out, fading; the Yellow blazes through behind.
        blit_shards(crack * RI * 2.6, crack * 0.55, 255 * (1 - 0.55 * crack))

    if sc != 1.0:
        sw = max(1, int(F * sc))
        layer = pygame.transform.smoothscale(layer, (sw, sw))
        cxL = sw // 2
    surf.blit(layer, (mcx - cxL, mcy - cxL))


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


def _yk_flames(surf, w, h, t, ramp):
    """A wall of fire along the bottom edge plus licks up the sides --
    the furnace burning all around. A bright base glow seats the flames
    so they don't read as floating triangles."""
    # Hot base glow band along the bottom (additive).
    glow = pygame.Surface((w, int(h * 0.22)), pygame.SRCALPHA)
    gh = glow.get_height()
    for i in range(gh):
        a = int(120 * (1 - i / gh) ** 1.5 * ramp)
        pygame.draw.line(glow, (255, 120, 30, a), (0, gh - i), (w, gh - i))
    surf.blit(glow, (0, h - gh), special_flags=pygame.BLEND_RGBA_ADD)
    # Edges: (dir, fixed-coord, span, step, height-scale).
    edges = (
        (0, -1, h, w, 18, 2.05),    # bottom, pointing up   -- the wall
        (1,  0, 0, h, 30, 0.95),    # left, pointing right
        (-1, 0, w, h, 30, 0.95),    # right, pointing left
    )
    for dx, dy, fixed, span, step, scale in edges:
        horizontal = dx != 0
        for s in range(0, span + step, step):
            seed = s * 0.07 + (0 if dx >= 0 else 3.3)
            fh = ((30 + 48 * (0.5 + 0.5 * math.sin(t * 6 + seed))
                   + 24 * math.sin(t * 11 + seed * 2)) * scale * ramp)
            if fh < 4:
                continue
            if horizontal:
                bx, by = fixed, s
            else:
                bx, by = s, fixed
            _flame_tongue(surf, bx, by, dx, dy, fh, step * 1.05, t + seed)



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
