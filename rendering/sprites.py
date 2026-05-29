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


def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None, threat=None, seed=0, curse=0.0):
    """`blink=True` suppresses eye dots for NPC kinds that have human
    eyes (mom/kid/bandit/policeman). Used by Game.draw to make a single
    NPC's eyes vanish for a single frame -- a subliminal wrongness.
    `gaze=True` lights the watcher's eyes (sees the player). Watchers
    only.
    while the player stands still."""
    if kind == "_invisible":
        return
    if kind == "mom":
        # red dress (desaturated, slightly dirtied), dark bun, apron with
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
    elif kind == "old":
        # Brown coat, hat, beard, cane. The face slot under the hat brim
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
    elif kind == "shopkeep":
        # Blue apron, bald top, glasses. Lenses are now FILLED black
        # instead of outlined -- you can't see his eyes through them, the
        # two black rectangles ARE the eye-read. Subtle and uncanny: every
        # time he turns toward you, you fail to find his gaze.
        pygame.draw.rect(surf, (54, 70, 104), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 190), (x - 6, y, 12, 16))  # apron
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.arc(surf, (40, 28, 22), (x - 8, y - 18, 16, 8), 0, math.pi, 1)  # hair ring
        # Glasses frames + filled black lenses (no eyes visible)
        pygame.draw.rect(surf, (10, 10, 14), (x - 4, y - 13, 3, 2))     # glasses L lens
        pygame.draw.rect(surf, (10, 10, 14), (x + 1, y - 13, 3, 2))     # glasses R lens
        pygame.draw.line(surf, (40, 40, 50), (x - 1, y - 12), (x + 1, y - 12), 1)  # bridge
        # A faint reflection-line on each lens so they read as glass,
        # not eyeholes -- but the reflection is on the WRONG side of
        # each lens (both reflect from the right), which is impossible
        # if the light source is overhead and singular.
        try:
            surf.set_at((x - 2, y - 13), (140, 150, 160))
            surf.set_at((x + 3, y - 13), (140, 150, 160))
        except (IndexError, ValueError):
            pass
    elif kind == "kid":
        # Desaturated yellow tunic; the original bright primary made the
        # kid read as cheerful, which fights the "trailing creep" use.
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
    elif kind == "policeman":
        # Navy uniform, peaked cap, gold badge. Cap-brim shadow falls
        # across the upper face so the eyes sit in a permanent dark
        # band; sunken hollows beneath. On `blink` the eyes become
        # 2x2 voids -- the cop's face goes wrong for a frame.
        pygame.draw.rect(surf, (32, 50, 100), (x - 9, y - 4, 18, 18))   # blue body
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (22, 30, 70), (x - 9, y - 22, 18, 6))    # cap brim
        pygame.draw.rect(surf, (22, 30, 70), (x - 7, y - 28, 14, 7))    # cap crown
        pygame.draw.rect(surf, (140, 50, 50), (x - 7, y - 7, 14, 4))    # collar/tie
        # Cap-brim shadow band across the upper face
        pygame.draw.rect(surf, (50, 40, 50), (x - 6, y - 15, 12, 2))
        # Sunken hollows
        pygame.draw.line(surf, (160, 130, 110), (x - 4, y - 12), (x - 1, y - 12), 1)
        pygame.draw.line(surf, (160, 130, 110), (x + 1, y - 12), (x + 4, y - 12), 1)
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
        # Gold badge on the chest
        pygame.draw.rect(surf, (220, 200, 80), (x - 1, y, 3, 3))
        pygame.draw.rect(surf, C_BLACK, (x - 1, y, 3, 3), 1)
        # Black belt
        pygame.draw.rect(surf, (10, 10, 18), (x - 9, y + 6, 18, 2))
    elif kind == "fisherman":
        # Mustard coat, weathered hat. Hat brim shadows the eyes; an
        # extra small dark line runs across the upper face so the eye
        # area reads as deeply shadowed even in bright scenes. Beard
        # has a damp green-grey cast (algae / pond-water).
        pygame.draw.rect(surf, (140, 112, 76), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (180, 162, 64), (x - 10, y - 22, 20, 4))  # hat brim
        pygame.draw.rect(surf, (180, 162, 64), (x - 7, y - 28, 14, 7))   # crown
        pygame.draw.rect(surf, (160, 170, 150), (x - 6, y - 5, 12, 8))   # beard (damp/mossy)
        # Hat-brim shadow band
        pygame.draw.rect(surf, (50, 40, 28), (x - 6, y - 14, 12, 3))
        if not blink:
            pygame.draw.circle(surf, (200, 200, 220), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (200, 200, 220), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (80, 60, 40), (x - 10, y), (x - 14, y - 10), 2)  # rod
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
        # A Watcher -- the curse made visible. NOT an eye: a tall,
        # ragged, faceless figure that stands at the edge of sight and
        # watches. Only the cursed see them. It is half-there -- it
        # phases on a slow sine, an apparition you can never quite fix
        # on -- and it looms a little nearer over its cycle. Two faint
        # sick pinpricks deep in the cowl are the only colour: the gaze.
        # Look straight at it (gaze=True) and the pinpricks go dark.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        phase = 0.35 + 0.5 * (math.sin(t * 1.1 + x * 0.01) * 0.5 + 0.5)
        loom = math.sin(t * 0.5 + x * 0.02) * 0.5 + 0.5      # 0..1, creeps in
        sway = int(math.sin(t * 0.8 + x * 0.03))
        layer = _pg.Surface((40, 64), _pg.SRCALPHA)
        bx = 20 + sway
        base_y = 60
        h = 38 + int(loom * 8)            # looms taller as it nears
        top = base_y - h
        shroud = (24, 22, 28, 255)
        shroud_lo = (11, 10, 14, 255)
        # Tapered shroud -- narrow shoulders to a wide, torn hem.
        body = [(bx - 4, top + 7), (bx + 4, top + 7),
                (bx + 10, base_y), (bx - 10, base_y)]
        _pg.draw.polygon(layer, shroud, body)
        _pg.draw.polygon(layer, shroud_lo, body, 1)
        # Ragged hem -- torn strips trailing into the dark.
        for hx in range(-9, 10, 3):
            _pg.draw.line(layer, shroud, (bx + hx, base_y - 3),
                          (bx + hx + 1, base_y + 3 + (hx % 3)), 2)
        # Drawn-up hood / faceless head.
        _pg.draw.circle(layer, shroud, (bx, top + 6), 6)
        _pg.draw.circle(layer, shroud_lo, (bx, top + 7), 5)
        # Thin reaching arms hinted down the body.
        _pg.draw.line(layer, shroud_lo, (bx - 4, top + 12), (bx - 8, top + 24), 2)
        _pg.draw.line(layer, shroud_lo, (bx + 4, top + 12), (bx + 8, top + 24), 2)
        # The gaze: two faint sick pinpricks (yellow used ONLY here, a
        # dim light in the dark), unless the player looks straight at it.
        if not gaze:
            g = 110 + int(math.sin(t * 2.0 + x) * 25)
            eye = (g, int(g * 0.85), 38, 255)
            _pg.draw.circle(layer, eye, (bx - 2, top + 6), 1)
            _pg.draw.circle(layer, eye, (bx + 2, top + 6), 1)
            halo = _pg.Surface((40, 64), _pg.SRCALPHA)
            _pg.draw.circle(halo, (60, 52, 22), (bx, top + 6), 7)
            layer.blit(halo, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)
        layer.set_alpha(int(255 * phase))
        surf.blit(layer, (x - 20, y - base_y))
    elif kind == "glitch_npc":
        for _ in range(30):
            ox = random.randint(-9, 9); oy = random.randint(-12, 8)
            col = (random.randint(80,255), random.randint(0,60), random.randint(0,60))
            pygame.draw.rect(surf, col, (x + ox, y + oy, 2, 2))
    else:
        # generic placeholder
        pygame.draw.rect(surf, (200, 200, 200), (x - 8, y - 8, 16, 16))


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None,
                        prone=False):
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
    """THE KING IN YELLOW (see header). `birth` (0..1, already de-None'd by the
    dispatch) drives the rift eruption; `t` animates; `gait` is accepted but the
    float needs no leg cycle. `threat` (0..1, the player's nearness to death)
    drives the calm->frenzy escalation: how many faces erupt, how bright it
    flares, how far and fast the arms haul. It never phases out."""
    global _YK_TRAIL
    R = 22
    intensity = 0.85 if threat is None else max(0.0, min(1.0, threat))
    # How much of the King has bled into the world (0 = dark void, 1 = full
    # blaze). Blooms late so the approach stays dreadful and the blaze is sudden.
    mr = max(0.0, min(1.0, (intensity - _YK_BLOOM_LO) / (_YK_BLOOM_HI - _YK_BLOOM_LO)))
    manifest = mr * mr * (3 - 2 * mr)
    mcx, mcy = x, int(y - 42 + math.sin(t * 1.1) * 3)        # floats above the feet
    bp = 1.0 if birth is None else max(0.0, min(1.0, birth))
    grow = bp * bp * (3 - 2 * bp)                            # body eases in
    valpha = 1.0 if bp >= 1.0 else 0.4 + 0.6 * grow
    # BIRTH: the King flashes into being mid-birth (visible regardless of how
    # near the player is), and the mask ASSEMBLES from scattered shards as it
    # forms -- the exact reverse of how it shatters when it gets mad.
    birth_vis = grow * (1.0 - grow) * 4.0                    # visible while it assembles
    ignite = max(0.0, (0.26 - bp) / 0.26)                   # a quick ignition flash, up front
    # Birth glow is kept low so the loud orb-cloud recedes and the quiet
    # shard-assembly of the mask is what reads -- a coalescing, not a firework.
    show = min(1.0, manifest + 0.5 * birth_vis + ignite)    # existence: threat OR birth
    # Birth runs the shatter in REVERSE: shards converge into the WHOLE mask,
    # always resolving to the calm intact face regardless of threat. Only once
    # fully formed does the threat actually crack it (and bring out the arms).
    # Crack LAGS the bloom: the mask first blooms INTACT (the void face becoming
    # real), and only shatters once it's mostly manifest -- so the calm void face
    # has faded before the shards appear, never a whole-face-behind-shards double.
    if bp >= 1.0:
        cm = max(0.0, (manifest - 0.45) / 0.55)
        crack = cm * cm * (3 - 2 * cm)
    else:
        crack = (1.0 - grow) * 2.2
    arms_on = bp >= 1.0 and crack > 0.05
    dt = t - _YK_LAST[0]
    _YK_LAST[0] = t
    if dt <= 0 or dt > 0.2:
        dt = 0.016
    # Wake reset on a teleport/respawn jump (re-seeds the swivel too).
    if _YK_TRAIL:
        px, py, pt = _YK_TRAIL[-1]
        if (mcx - px) ** 2 + (mcy - py) ** 2 > 70 ** 2 or (t - pt) > 0.45:
            _YK_TRAIL = []
            _YK_PARTS.clear()
            _YK_ACC[0] = 0.0
            _YK_AIM[0] = None
    # BIRTH: it is ASSEMBLING, so soul-orbs are pulled INWARD -- they spawn out
    # at the perimeter and stream toward the mask to form it (not vomited out).
    if bp < 0.55:
        for _ in range(2):
            ang = _YK_PRNG.uniform(0, math.tau)
            dist = _YK_PRNG.uniform(R * 1.6, R * 3.0)
            spd = _YK_PRNG.uniform(50, 130)
            orb = _YK_PRNG.random() < 0.10          # mostly faint motes, few orbs
            _YK_PARTS.append({
                "kind": "orb" if orb else "mote", "seed": _YK_PRNG.randint(0, 999),
                "birth": True,                       # coalescence -> dim, faceless
                "x": mcx + math.cos(ang) * dist, "y": mcy + math.sin(ang) * dist,
                "vx": -math.cos(ang) * spd, "vy": -math.sin(ang) * spd,   # toward the mask
                "age": 0.0, "life": dist / spd,                           # arrives ~as it fades
                "r": _YK_PRNG.uniform(5, 9) if orb else _YK_PRNG.uniform(2, 4)})
    disp = math.hypot(mcx - _YK_TRAIL[-1][0], mcy - _YK_TRAIL[-1][1]) if _YK_TRAIL else 0.0
    _YK_TRAIL.append((mcx, mcy, t))
    _YK_TRAIL = _YK_TRAIL[-5:]
    tvx, tvy = (mcx - _YK_TRAIL[0][0], mcy - _YK_TRAIL[0][1])
    tl = math.hypot(tvx, tvy) or 1.0
    bvx, bvy = -tvx / tl, -tvy / tl
    # The wake of shed soul-orbs only trails once he has AWAKENED (the bloom has
    # begun). While a calm void he is JUST a mask -- no trail, however he drifts.
    awakened = manifest > 0.05
    if awakened:
        _YK_ACC[0] += disp
    else:
        _YK_ACC[0] = 0.0
    while awakened and disp > 0.4 and _YK_ACC[0] >= 12:      # space the orbs along the path
        _YK_ACC[0] -= 12
        _YK_PARTS.append({
            "kind": "orb", "seed": _YK_PRNG.randint(0, 999),
            "x": mcx + _YK_PRNG.uniform(-5, 5), "y": mcy + _YK_PRNG.uniform(-5, 5),
            "vx": bvx * 9 + _YK_PRNG.uniform(-8, 8),
            "vy": bvy * 9 + _YK_PRNG.uniform(-8, 8),
            "age": 0.0, "life": _YK_PRNG.uniform(1.8, 2.8),
            "r": _YK_PRNG.uniform(7, 15)})
        for _ in range(2):
            _YK_PARTS.append({
                "kind": "mote", "seed": 0,
                "x": mcx + _YK_PRNG.uniform(-9, 9), "y": mcy + _YK_PRNG.uniform(-9, 9),
                "vx": bvx * 18 + _YK_PRNG.uniform(-16, 16),
                "vy": bvy * 18 + _YK_PRNG.uniform(-16, 16),
                "age": 0.0, "life": _YK_PRNG.uniform(0.7, 1.2),
                "r": _YK_PRNG.uniform(1.5, 3.0)})
    if len(_YK_PARTS) > 160:
        del _YK_PARTS[:len(_YK_PARTS) - 160]
    keep = []
    for p in _YK_PARTS:
        p["age"] += dt
        fr = p["age"] / p["life"]
        if fr >= 1.0:
            continue
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        keep.append((p, fr, (1.0 - fr) * show))      # a: no trail while it's a dark void
    _YK_PARTS[:] = [p for p, _, _ in keep]
    # Pass 1: lay down ALL the glow particles first...
    for p, fr, a in keep:
        if a <= 0.01:
            continue
        wdim = 0.4 if p.get("birth") else 0.42              # wake dimmed to match the head
        if p["kind"] == "orb":
            _yk_orb_glow(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a * wdim)
        else:
            mr = max(2, p["r"] * (1 - 0.4 * fr))
            _yk_radial(surf, p["x"], p["y"], int(mr * 2.6), _YK_T1, int(60 * a * wdim))  # orange glow
            _yk_radial(surf, p["x"], p["y"], mr, _YK_GOLD, int(150 * a * wdim))
    # ...Pass 2: then every orb's masks on top, so no later glow buries them. Birth
    # orbs stay FACELESS (a quiet coalescence); the wake faces are KEPT -- the
    # implied victims -- but dimmed so the trail sits behind the head.
    for p, fr, a in keep:
        if p["kind"] == "orb" and a > 0.04 and not p.get("birth"):
            _yk_orb_faces(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a * 0.8, p["seed"], t)
    # Faint floating shadow on the ground, far below the mass.
    sh = pygame.Surface((40, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 80), (0, 0, 40, 12))
    surf.blit(sh, (x - 20, y - 4))
    # Body on its own layer.
    L = 170
    layer = pygame.Surface((L, L), pygame.SRCALPHA)
    cx = cy = L // 2
    # Arms swivel smoothly toward the player (facing).
    fxx, fyy = facing if facing != (0, 0) else (0, 1)
    tgt = math.atan2(fyy, fxx)
    if _YK_AIM[0] is None:
        _YK_AIM[0] = tgt
    da_ = (tgt - _YK_AIM[0] + math.pi) % math.tau - math.pi
    _YK_AIM[0] += da_ * min(1.0, dt * 7.0)
    aa = _YK_AIM[0]
    fb = (math.cos(aa) * R * 0.22, math.sin(aa) * R * 0.22)
    va = max(0.05, valpha)
    dark_a = 1.0 - show
    # The PRIMARY mask: one steady face anchored as the "head", turned to track
    # the player. It is the first thing to exist (a pale mask in the void),
    # serene while the King is calm, and the scream the chorus erupts around as
    # it closes -- the same object the whole way, just becoming more real.
    hx = cx + fb[0] * 1.8
    hy = cy - R * 0.12 + fb[1] * 1.8
    # Vacuous void eyes throughout; serene mouth while calm, and a black-weeping
    # wail once it rouses to manifest.
    pmk = ("wail" if intensity >= 0.82 else "vacant") if bp >= 1.0 else "vacant"
    pfr = max(7, int(10 * max(0.3, grow)))
    # Motion sync: it hauls itself toward the aim as an arm completes its
    # stretch -- but only once it exists; dead still while a void.
    arm_speed = 0.32 + 0.4 * intensity                      # slow, deliberate reach
    lunge_env = (math.exp(-((((t * arm_speed) % 1.0) - 0.68) / 0.15) ** 2)
                 + math.exp(-((((t * arm_speed + 0.5) % 1.0) - 0.68) / 0.15) ** 2))
    surge = R * (0.12 + 0.28 * intensity) * grow * manifest * lunge_env
    sxo, syo = int(math.cos(aa) * surge), int(math.sin(aa) * surge)
    # A RARE, narrow white-hot stab -- one slow pulse, near-dark between, so full
    # brightness is a brief punctuation rather than the resting state.
    fph = (t * (0.16 + 0.12 * intensity)) % 1.0
    flare = math.exp(-((fph - 0.5) / 0.045) ** 2)
    # --- VOID form (dominant while far): a still dark mass + a faint pale mask.
    # Fades out by the time the bloom takes hold (show ~0.5), well before the
    # mask cracks -- so the whole calm face is gone before the shards show.
    void_fade = max(0.0, 1.0 - show / 0.5)
    if void_fade > 0.02 and grow > 0.1:
        void = pygame.Surface((L, L), pygame.SRCALPHA)
        _yk_void(void, cx, cy, int(R * max(0.4, grow)))
        # The ashen mask is THE thing watching from the void -- present and
        # readable the whole way (hollow eyes, no scream), just fainter far off
        # and firmer as he nears. Its MOUTH is withheld (mouth=False): a calm,
        # vacant, watching stare, never a shriek while he's still a void. The
        # scream is held for the break, when the mask actually cracks open.
        vmask = 0.6 + 0.18 * intensity
        _yk_mask(void, hx, hy, pfr, vmask, pmk, mouth=False)  # ashen mask, watching
        void.set_alpha(int(235 * void_fade * va))
        # Move with the SAME lurch offset as the manifest layer: the void and
        # the manifest are one head, so they must stay aligned -- otherwise the
        # calm void face and the manifest face read as TWO masks during the
        # crossfade. Surge is ~0 while far (manifest 0), so it's still then.
        surf.blit(void, (mcx - cx + sxo, mcy - cy + syo))
    # --- MANIFEST form (blooms in as it closes, and flashes in at birth).
    if show > 0.01:
        # Golden light SIZED TO THE MASK, sitting inside it -- so it reads as
        # light leaking FROM the mask: hidden when whole, blazing through the
        # cracks as it splits.
        _yk_glow(layer, hx, hy, max(6, int(pfr * 1.2)), t)
        # Birth ignition: a mask-scale white flash up front, before it assembles.
        if ignite > 0.02:
            _yk_radial(layer, hx, hy, int(pfr * (1.0 + 0.7 * ignite)),
                       _YK_WHITE, int(110 * ignite))
        # The white-hot core is a brief PUNCTUATION, not a constant glare: it
        # stabs only as he lunges (the same envelope that hauls the arms), so
        # the body mostly smoulders gold and full brightness stays rare.
        if intensity > 0.6 and flare > 0.04:
            _yk_radial(layer, hx, hy, int(pfr * (0.55 + 0.45 * intensity)), _YK_WHITE,
                       int(78 * (intensity - 0.6) / 0.4 * flare))
        # THE OTHER mask, directly behind -- a screaming face glimpsed through
        # the cracks once the front one splits open. Withheld until the cracks
        # actually open, so the scream is a reveal, not an ever-present chorus.
        _yk_mask(layer, hx, hy, pfr, min(1.0, max(0.0, crack - 0.3) * 1.5), "scream")
        # THE MASK -- our silhouette. Assembles from shards at birth, intact when
        # calm, and splits apart as it rouses -- the grasping arms bursting from
        # the splits and reaching toward the player.
        _yk_shatter_mask(layer, hx, hy, pfr, 0.92, pmk, crack, t, R * max(0.3, grow), aa, arms_on)
        layer.set_alpha(int(255 * va * show))
        surf.blit(layer, (mcx - cx + sxo, mcy - cy + syo))


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
        l = (bx + pdx * frac_w * width * 0.5, by + pdy * frac_w * width * 0.5)
        r = (bx - pdx * frac_w * width * 0.5, by - pdy * frac_w * width * 0.5)
        pygame.draw.polygon(surf, col,
                            [(int(l[0]), int(l[1])), (int(r[0]), int(r[1])),
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
