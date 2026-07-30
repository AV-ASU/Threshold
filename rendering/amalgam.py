"""THE AMALGAMS -- the Watcher-family shadows assembled from parts.

A shadow here is not one body: it is 3-5 PARTS, each emerging from its own
free-form CUT (a small aperture in the world, the same grammar at every
part: flesh clipped dead flat against the line, the rim lip on the absent
side, gold motes bleeding off it). Nothing touches anything else -- the
parts hang in formation around one anchor, thin haze threads the only
tissue, and the brain stitches "one creature" out of their synchrony.

Assembly is DATA: `assemble(seed)` deals 3-5 parts from the 22-part
(44 with mirroring)
library under the composition rules (at least one weight-bearing part on
the ground, masses centre, senses high, and ALWAYS at least one
eye-bearing part -- every amalgam watches). A different seed is a
different creature; the same seed always rebuilds the same one.

Behavior is the OG Watcher's, unchanged (spawn rules, hold, gaze/axe/
round/light dispel). What this module adds is presentation only:
- MANIFEST is a staggered build-out (parts enter cut by cut, driven by
  the spawn ramp passed as `birth`);
- the GAZE-DISPEL is a peeling (parts retract into their cuts in reverse,
  driven by the dispel fraction passed as `dispel`);
- IDLE is alive (masses breathe, limbs shift weight, the gut sac drips,
  eyes drift; every cut wanders a pixel around its offset).

Entry point: `draw_amalgam_sprite(surf, x, y, seed, gaze, birth, dispel)`
-- dispatched from `draw_npc_sprite` for `kind == "amalgam"`, feet at
(x, y), half-there phase + after-image like the Watcher. DESIGN.md §1.
"""
import math
import random

import pygame

# The flesh palette. These used to sit at 24/12/6 -- three tones within six
# values of each other, which is no contrast at all, so a part had no INTERIOR:
# outline it and you get a hollow cut-out rather than a body. The range is
# widened so `_lump`'s shading arcs and every VOID crease actually read as
# form. Still near-black against a lit room; it is the SPREAD that was missing,
# not the darkness.
SHROUD = (47, 44, 55)
SHROUD_LO = (21, 19, 25)
VOID = (6, 6, 9)
RIM = (46, 46, 60)
# The APERTURE rim is GOLD, so an amalgam's cuts read as the same portal
# family as the fold / King rift (rendering/portal.py) rather than as a
# separate cold-blue phenomenon -- one grammar for every hole He opens
# (maintainer-approved). RIM above stays cool: it is the FLESH lip
# drawn inside a part, not the hole itself.
CUT_RIM = (150, 116, 40)
CUT_RIM_HOT = (206, 164, 62)
# The visibility halo (see draw_amalgam_sprite). Deliberately dim and barely
# tinted: enough to lift a near-black body off a near-black room, not enough
# to read as the creature emitting light.
# The visibility OUTLINE (see draw_amalgam_sprite).
# The OUTLINE is the whole locator, so it is sized for the DARK SCENE it ships
# in, not for the preview sheet. At 1px of (206,202,196) a live 15-unit storm
# was unfindable: every unit was drawing ~400px, but the shapes did not
# separate from a frame averaging 14 luminance. Neither alpha
# (the blind-spot fog floor) nor the room gloom turned out to be the lever --
# both were tried and measured, and both moved the peak delta by ~1 -- because
# a near-black body simply has no value to spend. The EDGE is the only thing
# that can carry it, which is what the outline was for in the first place.
# The old note here said 2px "reads as cartoon line-art". On the isolated
# contact sheet that is STILL TRUE and worth knowing -- at sheet scale against
# the neutral card the edge swallows the body and the deals read as white line
# drawings. Both judgements are real; they just disagree about which screen
# matters, and the player only ever sees the dark one, where 2px is the
# difference between counting six creatures and finding one. So: width raised,
# COLOUR left at the original bone rather than brightened, which is what keeps
# the sheet's complaint down to a quibble instead of a fair hit. Judge any
# further change in a SCENE, in the dark (tools/capture_storm.py), and glance
# at tools/preview_amalgam.py after to see what it costs.
AMALGAM_EDGE = (206, 202, 196)   # bone; see the colour note in the docstring
AMALGAM_EDGE_W = 2               # px, sized for the dark scene, not the sheet
_EMIT_FLOOR = 90                 # alpha below this is atmosphere, not flesh
# THE GAZE. "Every amalgam watches" is the family's one composition rule
# (assemble), and at the old values you could not find an eye: EMBER was
# (110,88,30), which is dimmer than the gold on the CUTS, so the one thing that
# should read as attention was quieter than the scenery around it. The eye is
# now the brightest warm thing on the creature, with a dark socket under it for
# contrast and a hot core so it reads as lit rather than painted.
# The socket has to be a PIT, i.e. much darker than the flesh around it. At
# (38,29,12) it sat within a few values of SHROUD, so each one read as a small
# brown BERRY stuck on the body, and a deal with several incidental eyes looked
# like a blackberry rather than a creature. Near-black reads as a hole.
EMBER_G = (11, 9, 7)
# The gaze is PALER than gold, on purpose. Gold is the APERTURE colour here
# (CUT_RIM below, and the rift it echoes), and when the eye was gold too the
# two were indistinguishable -- a creature covered in gold specks with no way
# to tell which of them were looking at you. A lit-lamp cream separates the
# GAZE from the HOLE while staying in the same warm family.
EMBER = (238, 208, 126)
# And `dim` has to stay genuinely dim. Most weight/mass parts drop an
# incidental eye at dim=True; brightening those turned a 5-part deal into a
# rash of bright dots that read as a berry cluster rather than a body that
# happens to watch. Only the SENSE parts light up.
EMBER_DIM = (96, 78, 34)
EMBER_HOT = (255, 247, 216)      # the core; skipped when dim or stared at

# ---- THE EYE LANTERN (2026-07, maintainer: "what if the eye acts like a
# pseudo light source ... in practice completely decorative") ---------------
# The amalgam's legibility problem was never alpha and never the room's gloom
# (both were tried and measured to move the peak delta by ~1). A near-black
# body has no VALUE to spend, so the bone outline was carrying the whole job
# alone and the creature read as line-art: a silhouette with nothing inside it.
#
# This puts light INSIDE the silhouette. One guaranteed eyeball part, and a
# point source AT it that brightens the flesh around it with falloff. That is
# the opposite of the blurred halo this family already rejected: a bloom spreads
# brightness evenly and reads as a glowing spirit, while a point source with
# falloff makes some of the body brighter than the rest, which is MODELLING.
# The body stays as black as it ever was everywhere the light does not reach.
#
# IT IS DECORATIVE, AND THAT IS LOAD-BEARING, NOT A PREFERENCE. It must never
# appear in THE LIGHT TABLE (`systems/lights.py`) and must stay invisible to
# `Scene.lit_at`. A real light here would deny other amalgams a spawn spot
# (they open only in the dark), burn its own neighbours (WATCHER_LIGHT_BURN),
# seal the lost-space mouth (a lit edge is a wall), and -- the one that ends
# the system -- a storm unit refuses any step into light, so a flood would
# freeze itself solid walking toward you. Guarded by tests/conventions.py.
EYE_LAMP = (255, 214, 138)       # His light: neither the lamp's warm nor the
                                 # civic cold, so it is never mistaken for
                                 # safety. Sits between EMBER and CUT_RIM.
EYE_LAMP_R = 34                  # px in the 150x104 part space
_LAMP_CACHE = {}


def _lamp_surface(radius, amount):
    """A radial falloff disc, additive, cached by (radius, quantised amount).

    Blitted with BLEND_RGB_ADD, which touches RGB and leaves the destination
    ALPHA alone -- so it can only brighten pixels that are already flesh and
    can never paint a halo into the empty space around the creature. That one
    property is what makes this modelling rather than the glow this family
    threw out.
    """
    key = (radius, round(amount, 2))
    hit = _LAMP_CACHE.get(key)
    if hit is not None:
        return hit
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        f = 1.0 - (r / float(radius))
        f = f * f                                  # inverse-square-ish falloff
        col = (int(EYE_LAMP[0] * f * amount),
               int(EYE_LAMP[1] * f * amount),
               int(EYE_LAMP[2] * f * amount))
        pygame.draw.circle(s, col, (radius, radius), r)
    _LAMP_CACHE[key] = s
    return s

GY = 96                      # the internal floor row of the part space
_GAZE = False                # stared-at: every ember goes dark (family rule)


def _ease(d):
    return d * d * (3 - 2 * d)


def _clamp(v):
    return max(0.0, min(1.0, v))


def _outline(src, col, width=1, strength=1.0):
    """A hard OUTLINE traced around `src`'s silhouette, for a normal blit UNDER
    the sprite: the shape stated in one pixel of `col`, body untouched.

    Bone rather than pure white by default. White is the brightest value in the
    game and pops off a Darkwood-dark room like a sticker outline; bone states
    the edge just as clearly and still belongs to the palette. Gold was the
    other candidate and was rejected on purpose -- gold is the PORTAL language
    here (the rift, the folds, and an amalgam's own cuts all wear it), so
    outlining the whole creature in gold would blur the one distinction the
    family is built on: the holes He opens are gold, the flesh that comes
    through them is not.
    """
    import numpy as _np
    a = pygame.surfarray.array_alpha(src)
    solid = a > _EMIT_FLOOR
    grown = solid.copy()
    for _ in range(max(1, int(width))):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    ring = grown & ~solid
    out = pygame.Surface(src.get_size(), pygame.SRCALPHA)
    out.fill((*col, 0))
    alp = pygame.surfarray.pixels_alpha(out)
    alp[:] = (ring * int(255 * strength)).astype(_np.uint8)
    del alp
    return out


def _with_alpha(s, a):
    """Fade a per-pixel-alpha surface by an overall factor a (0..255)."""
    s = s.copy()
    s.fill((255, 255, 255, max(0, min(255, int(a)))),
           special_flags=pygame.BLEND_RGBA_MULT)
    return s


def _tent(s, pts, w0, w1, col=SHROUD):
    n = 36
    sm = []
    for i in range(n + 1):
        f = i / n
        seg = f * (len(pts) - 1)
        k = min(int(seg), len(pts) - 2)
        lf = seg - k
        ax, ay = pts[k]
        bx, by = pts[k + 1]
        sm.append((ax + (bx - ax) * lf, ay + (by - ay) * lf))
    for i, (px, py) in enumerate(sm):
        r = w0 + (w1 - w0) * (i / n)
        pygame.draw.circle(s, col, (int(px), int(py)), max(1, int(round(r))))


def _lump(s, cx, cy, rx, ry, lo=True):
    if rx < 1 or ry < 1:
        return
    pygame.draw.ellipse(s, SHROUD, (int(cx - rx), int(cy - ry),
                                    int(rx * 2), int(ry * 2)))
    if lo:
        pygame.draw.arc(s, SHROUD_LO, (int(cx - rx), int(cy - ry),
                                       int(rx * 2), int(ry * 2)),
                        math.pi * 1.15, math.pi * 1.95, 2)


def _eye(s, x, y, dim=False, r=1):
    """One ember eye. `dim` is the INCIDENTAL kind and has to stay a pinprick.

    Most weight and mass parts drop a dim eye somewhere on themselves, so a
    typical 5-part deal carries five or six. Drawn as filled discs they pile
    into a cluster of berries stuck to the body -- which is what "something's
    missing / the shapes look weird" turned out to be, once the palette was
    wide enough to see them at all. So the incidental ones are a socket and a
    single lit pixel, and only a SENSE part's eye gets the full lamp.
    """
    if _GAZE:                                    # stared at: every ember dies
        pygame.draw.circle(s, EMBER_G, (int(x), int(y)), r + 2)
        pygame.draw.circle(s, VOID, (int(x), int(y)), r + 1)
        return
    if dim:
        pygame.draw.circle(s, EMBER_G, (int(x), int(y)), r + 1)
        pygame.draw.circle(s, EMBER_DIM, (int(x), int(y)), 1)
        return
    pygame.draw.circle(s, EMBER_G, (int(x), int(y)), r + 2)
    pygame.draw.circle(s, EMBER, (int(x), int(y)), r + 1)
    pygame.draw.circle(s, EMBER_HOT, (int(x), int(y)), max(1, r - 1))


def _haze(s, cx, cy, r, a):
    """One soft blob of the tissue between parts.

    Drawn on a LOCAL surface the size of the blob, not a full-size one. It
    allocated and blitted a whole 150x104 layer per call, and a 22-unit storm
    makes ~230 of these calls a frame -- profiling put `blit` at the top of the
    draw by a wide margin. Same pixels, a fraction of the copying.
    """
    r = max(1, int(r))
    d = r * 2 + 2
    g = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(g, (56, 53, 68, int(a)), (r + 1, r + 1), r)
    s.blit(g, (int(cx) - r - 1, int(cy) - r - 1))


def _clip_half(lay, cx, cy, ang, side):
    """Erase everything on one side of the cut line -- the flesh ends DEAD
    FLAT against its aperture, the whole grammar in one operation."""
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy * side, dx * side
    p0 = (cx - dx * 200, cy - dy * 200)
    p1 = (cx + dx * 200, cy + dy * 200)
    p2 = (p1[0] + nx * 200, p1[1] + ny * 200)
    p3 = (p0[0] + nx * 200, p0[1] + ny * 200)
    pygame.draw.polygon(lay, (0, 0, 0, 0),
                        [(int(a), int(b)) for a, b in (p0, p1, p2, p3)])


def _cut_line(s, cx, cy, ang, ln, alpha=1.0, side=1):
    """The cut itself: VOID core on the line, RIM lip offset onto the
    absent side, motes; a partially-open (or dying) cut smokes."""
    if alpha <= 0.02 or ln <= 1:
        return
    dx, dy = math.cos(ang), math.sin(ang)
    p0 = (cx - dx * ln / 2, cy - dy * ln / 2)
    p1 = (cx + dx * ln / 2, cy + dy * ln / 2)
    nx, ny = -dy * side, dx * side
    a = int(255 * alpha)
    # LOCAL surfaces, sized to the cut -- the same fix _haze needed and for the
    # same reason. These two allocated and blitted a full copy of the TARGET
    # surface, and the bearer's crown calls this seven times a frame straight
    # onto the 960x640 screen: measured, the crown alone cost 4.3ms a frame
    # (down to 0.26ms), more than the entire cached body.
    #
    # Diffed against the full-surface version: `_cut_line` itself is identical
    # on 600/600 random cuts, and a composed unit on 1343/1350 (seed x time x
    # birth/dispel). Where they differ it is a handful of gold-bleed pixels, and
    # the LOCAL box is the more accurate of the two both times: pygame clips a
    # line to the target rect BEFORE rasterising it, so a cut near the top of
    # the sprite lost a pixel or two of bleed that a box containing the whole
    # line keeps; and it rasterises a width-2 line as a polygon whose vertices
    # are computed in floats, which at x=900 loses precision that x=30 keeps.
    pad = 22                          # clears the widest gold bleed + width,
                                      # with margin: a tighter box clipped a
                                      # pixel off the odd cut (found by diff)
    half = ln / 2 + pad
    ox, oy = int(cx - half), int(cy - half)
    d_ = int(half * 2) + 2
    g = pygame.Surface((d_, d_), pygame.SRCALPHA)
    pygame.draw.line(g, VOID + (a,), (p0[0] - ox, p0[1] - oy),
                     (p1[0] - ox, p1[1] - oy), 1)

    def lp(f, off):
        return (p0[0] + (p1[0] - p0[0]) * f + nx * off - ox,
                p0[1] + (p1[1] - p0[1]) * f + ny * off - oy)
    pygame.draw.line(g, CUT_RIM + (a,), lp(0.02, 1.5), lp(0.42, 1.5), 2)
    pygame.draw.line(g, CUT_RIM + (a,), lp(0.56, 1.5), lp(0.98, 1.5), 2)
    pygame.draw.line(g, CUT_RIM_HOT + (int(a * 0.75),),
                     lp(0.22, 1.5), lp(0.34, 1.5), 1)
    s.blit(g, (ox, oy))
    # a faint gold bleed off the lip, the rift's glow at aperture size
    gb = pygame.Surface((d_, d_), pygame.SRCALPHA)
    for off, ga in ((2.5, 16), (4.5, 9), (7.0, 4)):
        pygame.draw.line(gb, (*CUT_RIM, int(ga * alpha)),
                         lp(0.05, off), lp(0.95, off), 2)
    s.blit(gb, (ox, oy), special_flags=pygame.BLEND_RGBA_ADD)
    rng = random.Random(int(cx * 7 + cy * 13) & 0xffff)
    for k in range(2):
        mx = cx + nx * rng.uniform(3, 8) + rng.uniform(-2, 2)
        my = cy + ny * rng.uniform(3, 8) + rng.uniform(-2, 2)
        pygame.draw.circle(s, EMBER_G if k == 0 else SHROUD,
                           (int(mx), int(my)), 1)
    if 0.05 < alpha < 0.95:
        _haze(s, cx + nx * 4, cy + ny * 4, 4, (1 - alpha) * 55)
        _haze(s, cx - dx * 5, cy - dy * 5, 3, (1 - alpha) * 40)


def _draw_maybe_flipped(lay, fn, px, py, d, mode, k, flip):
    """Run a part draw, optionally MIRRORED about its own x.

    Doubles the library for free: 22 draw functions cover 44 silhouettes.

    The part renders to its own full-size layer and THAT is flipped, so
    everything it draws mirrors together -- flesh, the clipped cut edge, the rim
    lip, the motes. Flipping a surface mirrors about the SURFACE centre, so the
    result is re-blitted with an offset returning the part's own centre to where
    it started: a point at px lands at W-1-px, so the offset is 2*px - W + 1.
    """
    if not flip:
        fn(lay, px, py, d, mode, k)
        return
    W = lay.get_width()
    tmp = pygame.Surface(lay.get_size(), pygame.SRCALPHA)
    fn(tmp, px, py, d, mode, k)
    lay.blit(pygame.transform.flip(tmp, True, False),
             (int(round(2 * px)) - W + 1, 0))


def _part(s, cx, cy, ang, side, draw_fn):
    lay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    draw_fn(lay)
    _clip_half(lay, cx, cy, ang, side)
    s.blit(lay, (0, 0))


def _cl(d):
    """A part's cut-life from its deploy: opens ahead of the flesh."""
    return min(1.0, 0.35 + 0.8 * d)


# ============================= THE 22 PARTS ==================================
# Each: (surf, x, y, d, mode, k) -- d deploy 0..1, mode "enter"/"idle"/
# "leave", k a continuous 0..1 idle phase. Limbs lead with their extremity
# and walk or fold home; masses inflate, breathe, and can breathe shut.

def f_support_arm(s, x, y, d, mode, k):
    cx, cy = x + 8, y - 54
    gy = GY
    r = _ease(d)
    bend = (0.35 + 0.5 * k) if mode == "idle" else (0.2 if mode == "enter"
                                                    else 0.55)
    hx = cx - 17 * r
    hy = gy - 2 - (3 if (mode == "leave" and d > 0.4) else 0)
    if mode == "leave" and d > 0.4:
        hx += 5                                   # mid backwards-step

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 9 * min(1, r * 1.5), 8 * min(1, r * 1.5))
        _lump(lay, cx - 3 * r, cy + 9 * r, 7 * r, 6 * r, lo=False)
        sh_ = (cx - 2 * r, cy + 6 * r)
        elbow = ((sh_[0] + hx) / 2 - 4 * r, (sh_[1] + gy) / 2 - 9 * bend)
        _tent(lay, [sh_, elbow, (hx + 4, hy - 6), (hx, hy)],
              5.4 * (0.6 + 0.4 * r), 1.8)
        if d > 0.6:
            _lump(lay, (sh_[0] + elbow[0]) / 2, (sh_[1] + elbow[1]) / 2,
                  4, 3, lo=False)                                # the muscle
        if d > 0.35:
            spl = 1.3 if mode == "enter" else (0.6 if mode == "leave" else 1.0)
            for j in range(3):
                _tent(lay, [(hx, hy), (hx - (5 + j * 2) * spl,
                                       hy + 2 + (j % 2))], 2.0, 1.0)
        if d > 0.5:
            _eye(lay, cx - 2, cy + 7, dim=True)
    _part(s, cx, cy, 1.2, -1, dd)
    _cut_line(s, cx, cy, 1.2, 26 * _cl(d), alpha=_cl(d), side=-1)


def f_crawl_hand(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 24
    gy = GY
    r = _ease(d)
    reach = (14 + 4 * k) if mode == "idle" else 14 * r + 2

    def dd(lay):
        _lump(lay, cx + 2, cy, 5 * min(1, r * 1.6), 5 * min(1, r * 1.6),
              lo=False)
        wx = cx + reach * 0.6
        tip = (cx + reach, gy - 3)
        _tent(lay, [(cx + 1, cy), (wx, gy - 8 - 2 * k), tip], 4.4, 1.7)
        _lump(lay, tip[0], tip[1] - 1, 3, 2, lo=False)           # knuckles
        spl = 1.2 if mode == "enter" else (0.5 if mode == "leave" else 1.0)
        for j in range(3):
            _tent(lay, [tip, (tip[0] + (5 + j * 2) * spl,
                              gy - (j % 2) - (2 if mode == "leave" else 0))],
                  2.0, 1.0)
    _part(s, cx, cy, 1.05, 1, dd)
    _cut_line(s, cx, cy, 1.05, 20 * _cl(d), alpha=_cl(d), side=1)


def f_leg(s, x, y, d, mode, k):
    cx, cy = x - 2, y - 56
    gy = GY
    r = _ease(d)
    kb = 3 * k if mode == "idle" else 0
    lift = 4 if (mode == "leave" and d > 0.4) else (
        3 if (mode == "enter" and d < 0.75) else 0)
    fx = cx + 5 * r + (4 if (mode == "leave" and d > 0.4) else 0)

    def L(px, py):
        return (cx + (px - cx) * r, cy + (py - cy) * r)

    def dd(lay):
        _lump(lay, cx + 2, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        knee = L(cx + 9, (cy + gy) // 2 - 2 + kb)
        foot = L(fx, gy - 2 - lift)
        _tent(lay, [L(cx, cy + 4), knee,
                    ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2 + 3),
                    foot], 5.0 * (0.6 + 0.4 * r), 2.0)
        _lump(lay, (knee[0] + foot[0]) / 2 - 1, (knee[1] + foot[1]) / 2,
              3 * r, 4 * r, lo=False)                            # the calf
        if d > 0.7 and lift == 0:
            for j in range(2):
                _tent(lay, [foot, (foot[0] + 4 + j * 3, gy - (j % 2))],
                      2.2, 1.2)
    _part(s, cx, cy, 1.2, -1, dd)
    if d > 0.7 and lift == 0:
        g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(g, (0, 0, 0, 40), (int(fx - 8), gy - 4, 16, 7))
        s.blit(g, (0, 0))
    _cut_line(s, cx, cy, 1.2, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_elbow_prop(s, x, y, d, mode, k):
    cx, cy = x + 4, y - 50
    gy = GY
    r = _ease(d)
    settle = 2 * k if mode == "idle" else 0
    ex_ = cx - 10 * r
    ey_ = cy + (gy - 3 - cy) * r + settle

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        _tent(lay, [(cx, cy + 4), (cx - 7 * r, cy + (gy - cy) * r * 0.55),
                    (ex_, ey_)], 5.6 * (0.6 + 0.4 * r), 3.0)
        _lump(lay, ex_, ey_ - 1, 5 * r, (4 - settle * 0.5) * r, lo=False)
        fold = 0.55 if mode == "leave" else (0.7 + 0.3 * r)
        _tent(lay, [(ex_, ey_ - 2), (ex_ + 2, (cy + ey_) / 2 + 4),
                    (cx - 3 * fold, cy + 14 * fold)], 3.4 * r, 1.6)
        if d > 0.6:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(ex_ - 5), int(ey_ - 8), 10, 8), 0.3, 2.8, 1)
            pygame.draw.line(lay, RIM, (int(ex_ - 3), int(ey_ - 4)),
                             (int(ex_ + 2), int(ey_ - 5)), 1)
    _part(s, cx, cy, 1.25, -1, dd)
    _cut_line(s, cx, cy, 1.25, 24 * _cl(d), alpha=_cl(d), side=-1)


def f_reacher(s, x, y, d, mode, k):
    cx, cy = x + 16, y - 52
    gy = GY
    r = _ease(d)
    sweep = -8 + 16 * k if mode == "idle" else 0
    curl = mode == "leave"

    def dd(lay):
        _lump(lay, cx - 1, cy + 2, 6 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        tip = (cx - 40 * r + sweep, gy - 2 - (6 * r if curl else 0))
        _tent(lay, [(cx, cy + 2), (cx - 12 * r, cy + 12 * r),
                    (cx - 22 * r, gy - 8 * r - (gy - cy - 20) * (1 - r)),
                    (cx - 32 * r + sweep * 0.6,
                     gy - 3 - (3 * r if curl else 0)), tip],
              3.4 * (0.6 + 0.4 * r), 1.1)
        if d > 0.5 and not curl:
            for j in range(2):
                _tent(lay, [tip, (tip[0] - 5 - j * 3, gy - (j % 2))],
                      1.6, 1.0)
        if curl:
            _tent(lay, [tip, (tip[0] + 3, tip[1] - 4)], 1.6, 1.0)
        if d > 0.6:
            pygame.draw.line(lay, RIM, (int(cx - 10 * r), int(cy + 9 * r)),
                             (int(cx - 16 * r), int(cy + 14 * r)), 1)
    _part(s, cx, cy, 1.4, -1, dd)
    _cut_line(s, cx, cy, 1.4, 16 * _cl(d), alpha=_cl(d), side=-1)


def f_stump(s, x, y, d, mode, k):
    cx, cy = x - 2, y - 52
    gy = GY
    r = _ease(d)
    tilt = -2 + 4 * k if mode == "idle" else 0
    hike = 6 if (mode == "leave" and d > 0.4) else (
        4 if (mode == "enter" and d < 0.75) else 0)

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        base = (cx + 4 * r + tilt, cy + (gy - 4 - cy) * r - hike)
        _tent(lay, [(cx, cy + 3), (cx + 3 * r + tilt * 0.5,
                                   (cy + base[1]) / 2), base],
              6.0 * (0.6 + 0.4 * r), 3.4)
        _lump(lay, base[0], base[1] + 1, 5 * r, 3 * r, lo=False)
        if d > 0.6:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(base[0] - 5), int(base[1] - 4), 10, 6),
                            3.3, 6.1, 1)
    _part(s, cx, cy, 1.3, -1, dd)
    if d > 0.7 and hike == 0:
        g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(g, (0, 0, 0, 40),
                            (int(cx + 4 * r + tilt - 7), gy - 4, 14, 6))
        s.blit(g, (0, 0))
    _cut_line(s, cx, cy, 1.3, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_finger_fan(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 40
    r = _ease(d)
    n = max(1, int(5 * d + 0.5))
    wave = 0.12 * k if mode == "idle" else 0
    curlm = 0.65 if mode == "leave" else 1.0

    def dd(lay):
        _lump(lay, cx + 1, cy + 2, 4 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        F = ((-0.85, 17), (-0.45, 20), (-0.05, 19), (0.35, 16), (0.75, 12))
        for j, (fa, ln) in enumerate(F[:n]):
            fa += wave * (1 if j % 2 else -1)
            ln = ln * r * curlm
            rooty = cy - 4 + j * 3
            exx = cx + math.cos(fa) * ln
            eyy = rooty + math.sin(fa) * ln + (3 if mode == "leave" else 0)
            _tent(lay, [(cx + 1, rooty),
                        (cx + math.cos(fa) * ln * 0.6,
                         rooty + math.sin(fa) * ln * 0.6 - 2),
                        (exx, eyy), (exx + 2, eyy + 2)], 1.8, 1.0)
    _part(s, cx, cy, 1.1, 1, dd)
    _cut_line(s, cx, cy, 1.1, 18 * _cl(d), alpha=_cl(d), side=1)


def f_tail(s, x, y, d, mode, k):
    cx, cy = x + 10, y - 42
    gy = GY
    r = _ease(d)
    sway = -3 + 6 * k if mode == "idle" else 0
    tiplift = 4 if mode == "leave" else 0

    def L(px, py):
        return (cx + (px - cx) * r, cy + (py - cy) * r)

    def dd(lay):
        _lump(lay, cx - 2, cy + 2, 6 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        _tent(lay, [L(cx, cy + 2), L(cx - 12, gy - 10),
                    L(cx - 22, gy - 3), L(cx - 32 + sway, gy - 2 - tiplift)],
              4.6 * (0.6 + 0.4 * r), 1.0)
    _part(s, cx, cy, 0.9, -1, dd)
    _cut_line(s, cx, cy, 0.9, 20 * _cl(d), alpha=_cl(d), side=-1)


def f_wing_stub(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 48
    r = _ease(d)
    if mode == "enter" and d < 0.5:
        spread = 1.4                              # snaps OPEN first
    elif mode == "leave":
        spread = 0.7
    else:
        spread = 1.0 + 0.12 * k                   # the idle twitch

    def dd(lay):
        _lump(lay, cx + 1, cy + 2, 5 * min(1, r * 1.6), 5 * min(1, r * 1.6),
              lo=False)
        sp = spread * r * 1.3
        pts = [(cx + 2, cy), (cx + 14 * sp, cy - 8 * sp),
               (cx + 20 * sp, cy + 2 * sp), (cx + 15 * sp, cy + 5 * sp),
               (cx + 17 * sp, cy + 10 * sp), (cx + 10 * sp, cy + 8 * sp),
               (cx + 4 * sp, cy + 10 * sp)]
        ipts = [(int(a), int(b)) for a, b in pts]
        pygame.draw.polygon(lay, SHROUD_LO, ipts)
        pygame.draw.lines(lay, VOID, True, ipts, 1)
        if d > 0.5:
            pygame.draw.line(lay, VOID, (int(cx + 4 * sp), cy + 2),
                             (int(cx + 15 * sp), cy - 2), 1)     # membrane rib
            pygame.draw.line(lay, RIM, ipts[1], ipts[2], 1)
    _part(s, cx, cy, 0.8, -1, dd)
    _cut_line(s, cx, cy, 0.8, 16 * _cl(d), alpha=_cl(d), side=-1)


def f_haunch(s, x, y, d, mode, k):
    cx, cy = x, y - 40
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)

    def dd(lay):
        _lump(lay, cx - 4 * sc, cy + 7 * sc, 12 * sc, 10 * sc)
        _lump(lay, cx + 4 * sc, cy + 12 * sc, 9 * sc, 7 * sc, lo=False)
        if sc > 0.5:
            pygame.draw.arc(lay, VOID, (int(cx - 9 * sc), int(cy + 5 * sc),
                                        int(16 * sc), int(9 * sc)),
                            3.5, 5.4, 1)
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(cx - 6 * sc), int(cy + 11 * sc),
                             int(14 * sc), int(8 * sc)), 3.6, 5.6, 1)
        if sc > 0.55:
            _eye(lay, cx - 4 * sc, cy + 9 * sc, dim=True)
    _part(s, cx, cy, 0.45, -1, dd)
    _cut_line(s, cx, cy, 0.45, 26 * _cl(d), alpha=_cl(d), side=-1)


def f_hump(s, x, y, d, mode, k):
    cx, cy = x, y - 46
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)

    def dd(lay):
        _lump(lay, cx - 3 * sc, cy + 5 * sc, 11 * sc, 9 * sc)
        _lump(lay, cx + 6 * sc, cy + 8 * sc, 8 * sc, 6 * sc, lo=False)
        if sc > 0.5:
            pygame.draw.line(lay, RIM, (int(cx - 12 * sc), int(cy + 6 * sc)),
                             (int(cx - 13 * sc), int(cy + 12 * sc)), 1)
    _part(s, cx, cy, 0.3, -1, dd)
    _cut_line(s, cx, cy, 0.3, 24 * _cl(d), alpha=_cl(d), side=-1)


def f_rib_flank(s, x, y, d, mode, k):
    cx, cy = x, y - 42
    br = (1 - k) if mode == "idle" else 0.5       # exhale surfaces the ribs
    sc = _ease(d) * (0.93 + 0.10 * (1 - br))

    def dd(lay):
        _lump(lay, cx - 2 * sc, cy + 8 * sc, 16 * sc, 9 * sc)
        _lump(lay, cx + 8 * sc, cy + 12 * sc, 10 * sc, 6 * sc, lo=False)
        if sc > 0.5:
            ribs = 4 if br < 0.5 else 2
            for j in range(ribs):
                rx_ = cx + (-10 + j * 6) * sc
                pygame.draw.arc(lay, SHROUD_LO,
                                (int(rx_), int(cy + 3 * sc),
                                 int(7 * sc), int(12 * sc)),
                                math.pi * 0.6, math.pi * 1.5, 1)
            pygame.draw.line(lay, RIM, (int(cx - 14 * sc), int(cy + 4 * sc)),
                             (int(cx - 6 * sc), int(cy + 2 * sc)), 1)
        if sc > 0.55:
            _eye(lay, cx + 11 * sc, cy + 9 * sc, dim=True)
    _part(s, cx, cy, 0.35, -1, dd)
    _cut_line(s, cx, cy, 0.35, 30 * _cl(d), alpha=_cl(d), side=-1)


def f_gut_sac(s, x, y, d, mode, k):
    cx, cy = x, y - 62
    r = _ease(d)
    swing = -2 + 4 * k if mode == "idle" else 0
    drawn = 0.6 if mode == "leave" else 1.0       # drawn up on leave
    sag = r * drawn

    def dd(lay):
        _lump(lay, cx - 1, cy + 6 * sag, 7 * r, 6 * r, lo=False)
        _lump(lay, cx + swing, cy + 14 * sag, 9 * r, 10 * sag)
        _lump(lay, cx + 1 + swing, cy + 21 * sag, 6 * r, 6 * sag, lo=False)
        if r > 0.5:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(cx - 7 + swing), int(cy + 12 * sag),
                             14, max(2, int(10 * sag))), 3.4, 5.8, 1)
            pygame.draw.arc(lay, RIM, (int(cx - 5), int(cy + 8 * sag), 8, 6),
                            1.6, 2.9, 1)
        if r > 0.7 and mode == "idle" and k > 0.7:
            _tent(lay, [(cx + 1 + swing, cy + 26 * sag),
                        (cx + 2 + swing, cy + 30 * sag)], 1.6, 1.0)
            _lump(lay, cx + 2 + swing, cy + 31 * sag, 1, 1, lo=False)
    _part(s, cx, cy, 0.1, -1, dd)
    _cut_line(s, cx, cy, 0.1, 20 * _cl(d), alpha=_cl(d), side=-1)


def f_spine_ridge(s, x, y, d, mode, k):
    cx, cy = x - 10, y - 52
    n = max(1, int(4.2 * d))                      # the chain pulls out
    wave = 1.5 * k if mode == "idle" else 0

    def dd(lay):
        pts = [(cx - 2, cy + 4), (cx + 6, cy - 4), (cx + 14, cy - 5),
               (cx + 21, cy + 1), (cx + 26, cy + 10)]
        use = pts[:n + 1]
        _tent(lay, use, 3.0, 1.6)
        for j, (px, py) in enumerate(use[:-1][:n]):
            off = wave * (1 if j % 2 else -1)
            _lump(lay, px, py - 5 + off, 3, 3, lo=False)
            pygame.draw.line(lay, RIM, (int(px - 1), int(py - 9 + off)),
                             (int(px + 1), int(py - 9 + off)), 1)
        if n >= 4:
            _lump(lay, cx + 26, cy + 12, 3, 2, lo=False)
    _part(s, cx, cy, 1.05, 1, dd)
    _cut_line(s, cx, cy, 1.05, 22 * _cl(d), alpha=_cl(d), side=1)


def f_eye_bulge(s, x, y, d, mode, k):
    cx, cy = x, y - 52
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)
    eyes_on = (d > 0.75) if mode == "enter" else (d > 0.6)

    def dd(lay):
        _lump(lay, cx - 2 * sc, cy + 5 * sc, 8 * sc, 7 * sc, lo=False)
        _lump(lay, cx + 4 * sc, cy + 9 * sc, 6 * sc, 5 * sc, lo=False)
        if eyes_on:
            dr = (-1.5 + 3 * k) if mode == "idle" else 0
            _eye(lay, cx - 4 * sc + dr, cy + 5 * sc, r=2)
            _eye(lay, cx + 3 * sc, cy + 9 * sc + dr * 0.5, dim=True)
            _eye(lay, cx - 1 * sc, cy + 3 * sc, dim=True)
    _part(s, cx, cy, 0.15, -1, dd)
    _cut_line(s, cx, cy, 0.15, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_vent(s, x, y, d, mode, k):
    cx, cy = x, y - 50
    nsm = max(1, int(11 * d))
    breathe = 1.0 + 0.35 * k if mode == "idle" else 1.0
    for j in range(nsm):
        _haze(s, cx - 1 + (j % 3) * 4 + j, cy + 2 + j * 4 * breathe,
              (5 + j * 0.7) * breathe, max(30, (90 - j * 7) * d))
    _cut_line(s, cx, cy, 1.4, 18 * _cl(d), alpha=_cl(d), side=1)
    rng = random.Random(7)
    for j in range(max(1, int(5 * d))):
        pygame.draw.circle(s, EMBER_G if j % 2 else SHROUD,
                           (int(cx + rng.uniform(-3, 10)),
                            int(cy + 2 + rng.uniform(0, 20))), 1)


def f_ember_pair(s, x, y, d, mode, k):
    cx, cy = x, y - 44
    ang = 1.35
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    w = 3 * _ease(d)
    ln = 10 * (0.5 + 0.5 * d)
    pts = [(cx - dx * ln, cy - dy * ln),
           (cx - dx * ln * 0.4 + nx * w, cy - dy * ln * 0.4 + ny * w),
           (cx + dx * ln * 0.5 + nx * w, cy + dy * ln * 0.5 + ny * w),
           (cx + dx * ln, cy + dy * ln),
           (cx + dx * ln * 0.5 - nx * w, cy + dy * ln * 0.5 - ny * w),
           (cx - dx * ln * 0.4 - nx * w, cy - dy * ln * 0.4 - ny * w)]
    pygame.draw.polygon(s, VOID, [(int(a), int(b)) for a, b in pts])
    pygame.draw.lines(s, RIM, True, [(int(a), int(b)) for a, b in pts], 1)
    blink = (mode == "idle" and k > 0.75)
    if d > 0.5:
        _eye(s, cx - dx * 4, cy - dy * 4, r=2, dim=blink)
        if d > 0.8 or mode != "leave":
            _eye(s, cx + dx * 4, cy + dy * 4, r=2, dim=blink)


def f_eye_lantern(s, x, y, d, mode, k):
    """THE LANTERN EYE -- the one part every amalgam carries.

    A single big eyeball held in a socket of flesh, surfacing from its own cut
    like every other part. It is drawn here as an OBJECT only; the light it
    appears to throw is applied to the composed body in `_compose_unit`, so the
    lit flesh is real pixels of the creature rather than a halo pasted over it.

    It is deliberately the largest, roundest thing on the body: at game scale
    in a dark room the eye is the read, and a round bright disc survives
    distance and the room's gloom better than any amount of edge does.
    """
    cx, cy = x, y - 50
    sc = _ease(d)
    br = k if mode == "idle" else 0.5

    def dd(lay):
        # the socket: flesh cupping the ball, so it is HELD rather than stuck on
        _lump(lay, cx, cy + 3 * sc, 11 * sc, 9.5 * sc, lo=False)
        _lump(lay, cx - 5 * sc, cy + 7 * sc, 5 * sc, 4 * sc)
        if d <= 0.45:
            return
        r = max(2, int(6.2 * sc))
        # the ball, then the iris, then the core. Stared at, the whole thing
        # goes dark like every other ember in the family -- the lantern is not
        # an exception to the one rule the player can act on.
        pygame.draw.circle(lay, VOID, (int(cx), int(cy)), r + 2)
        pygame.draw.circle(lay, RIM, (int(cx), int(cy)), r + 2, 1)
        if _GAZE:
            pygame.draw.circle(lay, EMBER_G, (int(cx), int(cy)), max(1, r - 2))
            return
        pygame.draw.circle(lay, EMBER_G, (int(cx), int(cy)), r + 1)
        pygame.draw.circle(lay, EMBER, (int(cx), int(cy)), r)
        pygame.draw.circle(lay, EYE_LAMP, (int(cx), int(cy)),
                           max(1, int(r * 0.62)))
        pygame.draw.circle(lay, EMBER_HOT, (int(cx), int(cy)),
                           max(1, int(r * (0.24 + 0.10 * br))))
    _part(s, cx, cy, 0.4, 1, dd)
    _cut_line(s, cx, cy, 0.4, 20 * _cl(d), alpha=_cl(d), side=1)


# ---- 2026-07: six more parts (maintainer: "more almg parts?"). The deal was
# already varied as DATA -- 198 distinct combinations in 200 seeds -- but the
# library was only 16, so the same shapes recurred once you had seen a few
# dozen. These widen the vocabulary in the directions it was thinnest: two
# more ways to MEET THE GROUND, two more body masses, two more senses.

def f_hoof(s, x, y, d, mode, k):
    """A short pastern ending in a splayed two-toe hoof, planted hard."""
    cx, cy = x + 4, y - 30
    r = _ease(d)
    gy = GY
    splay = (1.0 + 0.18 * k) if mode == "idle" else (1.35 if mode == "enter"
                                                     else 0.8)

    def dd(lay):
        _lump(lay, cx, cy + 2, 7 * min(1, r * 1.5), 8 * min(1, r * 1.5))
        _tent(lay, [(cx, cy + 6 * r), (cx - 2 * r, gy - 9)], 5.0 * r, 3.4 * r)
        if d > 0.4:
            for sgn in (-1, 1):
                tip = (cx - 2 + sgn * 5 * splay, gy - 1)
                _tent(lay, [(cx - 2 * r, gy - 9), tip], 3.0, 1.6)
                pygame.draw.line(lay, VOID, (int(tip[0]), int(tip[1] - 3)),
                                 (int(tip[0]), int(tip[1])), 1)
        if d > 0.65:
            pygame.draw.line(lay, RIM, (int(cx - 5), int(cy + 8 * r)),
                             (int(cx + 4), int(cy + 6 * r)), 1)
    _part(s, cx, cy, 1.35, -1, dd)
    _cut_line(s, cx, cy, 1.35, 20 * _cl(d), alpha=_cl(d), side=-1)


def f_crutch(s, x, y, d, mode, k):
    """Two thin struts meeting under a padded shoulder: it PROPS rather than
    stands, so the mass above always looks borrowed."""
    cx, cy = x - 4, y - 58
    r = _ease(d)
    gy = GY
    lean = (2.0 * k - 1.0) if mode == "idle" else 0.0

    def dd(lay):
        _lump(lay, cx, cy + 3, 8 * min(1, r * 1.4), 6 * min(1, r * 1.4))
        for sgn in (-1, 1):
            foot = (cx + sgn * (9 + 3 * r) + lean, gy - 1)
            _tent(lay, [(cx + sgn * 2, cy + 6 * r), foot], 2.8 * r, 1.4)
            if d > 0.55:
                pygame.draw.line(lay, VOID,
                                 (int(foot[0] - 3), int(foot[1])),
                                 (int(foot[0] + 3), int(foot[1])), 1)
        if d > 0.7:
            _eye(lay, cx + 1, cy + 4, dim=True)
    _part(s, cx, cy, 0.55, 1, dd)
    _cut_line(s, cx, cy, 0.55, 22 * _cl(d), alpha=_cl(d), side=1)


def f_sack(s, x, y, d, mode, k):
    """A distended sack slung under the mass, swinging a beat behind it."""
    cx, cy = x + 2, y - 58
    r = _ease(d)
    sway = (-3 + 6 * k) if mode == "idle" else 0
    drop = 0.55 if mode == "leave" else 1.0

    def dd(lay):
        _lump(lay, cx, cy + 4, 6 * r, 5 * r, lo=False)
        _lump(lay, cx + sway * 0.4, cy + 13 * drop, 11 * r, 12 * r * drop)
        _lump(lay, cx + sway * 0.7, cy + 23 * drop, 7 * r, 7 * r * drop,
              lo=False)
        if r > 0.5:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(cx - 9 + sway * 0.4), int(cy + 8 * drop),
                             18, max(2, int(14 * drop))), 3.5, 5.9, 1)
            pygame.draw.line(lay, RIM, (int(cx - 6), int(cy + 5)),
                             (int(cx + 5), int(cy + 4)), 1)
        if r > 0.75:
            _eye(lay, cx + sway * 0.5, cy + 20 * drop, dim=True)
    _part(s, cx, cy, 0.2, -1, dd)
    _cut_line(s, cx, cy, 0.2, 24 * _cl(d), alpha=_cl(d), side=-1)


def f_plate(s, x, y, d, mode, k):
    """Overlapping carapace plates that lift and settle as it breathes."""
    cx, cy = x - 2, y - 48
    sc = _ease(d)
    lift = k if mode == "idle" else (1.0 if mode == "enter" else 0.2)

    def dd(lay):
        _lump(lay, cx, cy + 9 * sc, 14 * sc, 9 * sc)
        n = max(1, int(4 * sc))
        for j in range(n):
            py = cy + (2 + j * 5) * sc
            w = (13 - j * 2) * sc
            gap = lift * (1.0 - j / max(1, n)) * 2.2
            rct = (int(cx - w), int(py - 4 * sc - gap),
                   max(2, int(w * 2)), max(2, int(7 * sc)))
            pygame.draw.ellipse(lay, SHROUD, rct)
            pygame.draw.arc(lay, VOID, rct, 3.3, 6.1, 1)
            if j == 0:
                pygame.draw.arc(lay, RIM, rct, 3.5, 5.9, 1)
        if sc > 0.6:
            _eye(lay, cx + 10 * sc, cy + 11 * sc, dim=True)
    _part(s, cx, cy, 0.25, -1, dd)
    _cut_line(s, cx, cy, 0.25, 28 * _cl(d), alpha=_cl(d), side=-1)


def f_cilia(s, x, y, d, mode, k):
    """A fringe of fine filaments, combing the air toward whatever it senses."""
    cx, cy = x, y - 56
    n = max(1, int(9 * d))
    wave = k if mode == "idle" else (0.9 if mode == "enter" else 0.15)

    def dd(lay):
        _lump(lay, cx, cy + 4, 6 * _ease(d), 4 * _ease(d), lo=False)
        for j in range(n):
            fx = cx - 10 + j * 2.6
            ph = math.sin(wave * math.tau + j * 0.8)
            ln = 7 + (j % 3) * 3
            _tent(lay, [(fx, cy + 4), (fx + ph * 3, cy + 4 - ln)], 1.5, 0.8)
        if d > 0.6:
            _eye(lay, cx - 1, cy + 5, dim=True)
    _part(s, cx, cy, 1.5, -1, dd)
    _cut_line(s, cx, cy, 1.5, 18 * _cl(d), alpha=_cl(d), side=-1)


def f_lure(s, x, y, d, mode, k):
    """A stalk carried out ahead of the body with one ember at its tip: the
    part that arrives BEFORE the creature does."""
    cx, cy = x - 6, y - 62
    r = _ease(d)
    reach = r * (1.0 + 0.16 * (k if mode == "idle" else 0.0))
    tipx, tipy = cx + 20 * reach, cy - 12 * reach

    def dd(lay):
        _lump(lay, cx, cy + 3, 5 * min(1, r * 1.6), 5 * min(1, r * 1.6),
              lo=False)
        _tent(lay, [(cx + 2, cy + 2), (cx + 11 * reach, cy - 3 * reach),
                    (tipx, tipy)], 2.6, 1.1)
        if d > 0.45:
            _lump(lay, tipx, tipy, 3.0, 2.6, lo=False)
    _part(s, cx, cy, 0.95, -1, dd)
    if d > 0.5:
        _eye(s, tipx, tipy, r=2)                  # rides OUTSIDE the clip
    _cut_line(s, cx, cy, 0.95, 16 * _cl(d), alpha=_cl(d), side=-1)


WEIGHT = [("leg", f_leg), ("stump", f_stump), ("elbow", f_elbow_prop),
          ("arm", f_support_arm), ("hand", f_crawl_hand),
          ("hoof", f_hoof), ("crutch", f_crutch)]
MASS = [("haunch", f_haunch), ("hump", f_hump), ("rib", f_rib_flank),
        ("gut", f_gut_sac), ("spine", f_spine_ridge),
        ("sack", f_sack), ("plate", f_plate)]
# How far ABOVE its `y` each mass actually draws itself (the `cy = y - N` in
# each function). They range 40..62, so passing every mass the same y0 put some
# bodies a full 22px higher than others -- floating clear of the legs meant to
# be holding them up, by accident rather than intent. assemble() subtracts
# these so it can aim at a BODY HEIGHT instead. Verified against the source by
# tests/conventions.py check 10, because a hand-copied table like this rots
# silently: nothing crashes, bodies just drift.
_MASS_DY = {"haunch": 40, "hump": 46, "rib": 42, "gut": 62, "spine": 52,
            "sack": 58, "plate": 48}
# SENSE[:2] is the ALWAYS-eye-bearing prefix that assemble() draws the first
# sense slot from (every amalgam watches), so new senses append AFTER it.
SENSE = [("eyes", f_eye_bulge), ("pair", f_ember_pair), ("vent", f_vent),
         ("fan", f_finger_fan), ("tail", f_tail), ("wing", f_wing_stub),
         ("cilia", f_cilia), ("lure", f_lure)]


def assemble(seed, extra=0):
    """Deal a creature: 3-5 parts under the composition rules. The prefix
    (weights + masses) caps at 4 so there is ALWAYS room for the first
    sense slot, which is always an eye-bearing part: every amalgam
    watches. Same seed, same creature.

    Returns 5-tuples `(name, fn, x0, y0, flip)`.

    THE BODY IS DEALT FIRST AND THE LEGS FIND IT (2026-07). Before, weight
    parts took fixed offsets off a shared list and masses were placed
    independently, so a leg had no idea where the body was: a wide deal put the
    legs one side and the mass the other, reading as scattered limbs beside an
    unrelated lump. Now the body is placed, and the weight parts distribute
    under IT -- a stance around the mass centroid, widening with leg count.
    They still never TOUCH it (the family rule, module docstring): they reach up
    and stop, and the eye closes that gap like every other one here.

    FLIP doubles the library for free: each part carries a mirror flag, so 22
    draw functions cover 44 silhouettes and a limb on the left is not the same
    shape as the same limb on the right.
    """
    rng = random.Random(seed)
    parts = []

    # 1. THE BODY, so everything else has something to relate to.
    masses = []
    for _ in range(rng.choice((1, 1, 2))):
        nm, fn = rng.choice(MASS)
        mx = rng.randint(-9, 9)
        # Aim at a BODY HEIGHT and convert to the y0 this mass needs
        # (_MASS_DY): the legs rise to about y=42, so a body centre in the
        # mid-40s sits where they reach.
        #
        # SOME FLOATING IS RIGHT (maintainer, 2026-07): a part arrives through
        # its own aperture, so a mass hanging clear of anything holding it is
        # the portal carrying it, not a defect. What was wrong before is that
        # floating happened by ACCIDENT -- from the 22px offset spread above --
        # and happened to nearly every deal. So a body the legs reach is the
        # default, and about a quarter ride high on purpose.
        if rng.random() < 0.26:
            y0 = _MASS_DY.get(nm, 46) + rng.randint(58, 74)
        else:
            y0 = _MASS_DY.get(nm, 46) + rng.randint(42, 56)
        masses.append((nm, fn, mx, y0, rng.random() < 0.5))
    cx = sum(m[2] for m in masses) / float(len(masses))

    # 2. THE LEGS, under the body they carry. One sits below the centroid;
    #    more spread into a stance either side of it.
    nw = rng.choice((1, 2, 2, 3))
    span = 7 + 4 * nw
    offs = [0] if nw == 1 else [-span + 2 * span * i / (nw - 1)
                                for i in range(nw)]
    rng.shuffle(offs)
    for off in offs:
        nm, fn = rng.choice(WEIGHT)
        lx = int(round(max(-26, min(26, cx + off))))
        parts.append((nm, fn, lx, 96 + rng.randint(-8, 2), rng.random() < 0.5))

    parts.extend(masses)
    parts = parts[:4]

    # 3. THE SENSES, high and near the body's own column.
    ns = rng.choice((1, 2, 2))
    for i in range(ns):
        nm, fn = (rng.choice(SENSE[:2]) if i == 0 else rng.choice(SENSE))
        sx = int(round(max(-26, min(26, cx + rng.randint(-11, 11)))))
        parts.append((nm, fn, sx, 96 - rng.randint(12, 32), rng.random() < 0.5))
    out = parts[:5]
    # THE LANTERN, attached to the body and never DEALT -- the same shape of
    # rule the Pallid Mask follows (an extra part no deal can roll). It goes on
    # after the [:5] slice so it displaces nothing and every existing deal is
    # the creature it always was, with an eye added. Placed on the mass column,
    # high, because that is where a head would be if this had one.
    out.append(("eyelamp", f_eye_lantern,
                int(round(max(-26, min(26, cx + rng.randint(-5, 5))))),
                96 - rng.randint(20, 30), rng.random() < 0.5))
    if extra > 0:
        # THE APEX wears its host's deal and adds to it: the Mask
        # "deletes it and becomes it, reusing that amalg's exact parts while
        # adding 2-3 more". A SEPARATE rng so the base deal is untouched --
        # extra=0 must stay byte-identical for every ordinary unit.
        rng2 = random.Random(seed * 31 + 7)
        for i in range(extra):
            nm, fn = rng2.choice(MASS if i % 2 else SENSE)
            ex = int(round(max(-26, min(26, cx + rng2.randint(-14, 14)))))
            out.append((nm, fn, ex,
                        _MASS_DY.get(nm, 46) + rng2.randint(40, 58)
                        if (i % 2) else 96 - rng2.randint(10, 30),
                        rng2.random() < 0.5))
    return out


# ===================== THE PALLID MASK -- the 18th part ======================
# His FACE, and NOT the keystone object. Canon: there is exactly one Mask object
# and it is on the cult's altar until the PI lifts it, because the rite buys Him
# one solid thing crossing over and no more (NARRATIVE §2, §6a). What rides a
# shadow here is a SLICE -- the same cross-section of Him as the drifting masks
# in fire -- so it is His face without being a thing anyone could pick up. Same
# carving, same renderer as the keystone's reference art; different kind of
# thing. Do not describe this one as the object.
#
# It is carried in the storm as a part like any other: it surfaces from its own
# free-form CUT, is HELD by the flesh at
# the rim, and only ONE exists storm-wide at a time (the migrating bearer,
# driven by the storm state -- NEVER dealt by assemble(), so every ordinary
# amalgam is untouched). It is a REAL 3D OBJECT: `yaw` turns it a full 360, His
# carved face toward the PI on the near hemisphere and the hollow adzed BACK on
# the far one, foreshortening to a sliver at profile (this SUPERSEDES the older
# always-camera-facing call -- the maintainer wants it to respect the tilted
# world, so it is a prop that turns, not a billboard). It draws at player scale
# (STORM_MASK_R). The timber is a bone<->wood blend: the drowned-white plate
# shape + the cult wood's carved construction (pale plate, centre seam, brow +
# long nose, faint grain, deep recessed sockets with the gold a pinprick far
# back, NO mouth, NO halo); the reverse is the unfinished hollow, adze-gouged,
# a binding cord across it, the eye-holes leaking that same gold from behind.
_PMASK_BONE = {"base": (204, 198, 186), "hi": (228, 222, 208), "lo": (152, 146, 132),
               "grain": (136, 128, 114), "edge": (82, 74, 62)}
_PMASK_WOOD = {"base": (122, 92, 56), "hi": (154, 120, 76), "lo": (82, 60, 38),
               "grain": (58, 40, 24), "edge": (38, 26, 14)}
_PMASK_GOLD = (222, 178, 46)
_PMASK_HOT = (250, 214, 92)


def _pmask_pal(blend):
    b = max(0.0, min(1.0, blend))
    return {k: tuple(int(_PMASK_BONE[k][i] + (_PMASK_WOOD[k][i] - _PMASK_BONE[k][i]) * b)
                     for i in range(3)) for k in _PMASK_BONE}


def _pmask_jag(surf, cx, cy, rx, ry, col, seed, n=26, jit=0.04):
    rng = random.Random(seed)
    pts = [(cx + math.cos(i / n * math.tau) * rx * (1 + rng.uniform(-jit, jit)),
            cy + math.sin(i / n * math.tau) * ry * (1 + rng.uniform(-jit, jit)))
           for i in range(n)]
    pygame.draw.polygon(surf, col, [(int(a), int(b)) for a, b in pts])


def carved_pallid_surface(r, gaze=(0.0, 0.25), blend=0.5, seed=7, ember=1.0):
    """The carved-pallid Mask on its own square surface, centred and face-on.
    `ember` 0..1 guts the gold as the mask sinks back into its cut.

    RETAINED as the flat 2D face-art REFERENCE only: the shipping Mask is the
    3D `draw_pallid_3d` (whose front-hemisphere face echoes this art). Not on
    any live draw path; kept for a possible future texture-map onto the shell."""
    r = max(4, int(r))
    P = _pmask_pal(blend)
    S = int(r * 2.6)
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = S // 2
    rx, ry = r * 0.78, r * 1.05
    plate = pygame.Surface((S, S), pygame.SRCALPHA)
    _pmask_jag(plate, mx, my, rx + 2, ry + 2, P["edge"], seed, jit=0.045)
    _pmask_jag(plate, mx, my, rx, ry, P["base"], seed + 1, jit=0.035)
    hi = pygame.Surface((S, S), pygame.SRCALPHA)
    _pmask_jag(hi, mx - int(r * 0.12), my - int(r * 0.18), rx * 0.8, ry * 0.74,
               (*P["hi"], 130), seed + 2, jit=0.04)
    plate.blit(hi, (0, 0))
    for gi in range(5):
        gx = mx + int((gi - 2) / 2.6 * rx * 0.7)
        pts = [(gx + int(math.sin(k * 0.9 + gi * 2.1) * 1.6),
                int(my - ry * 0.45 + (ry * 1.05) * k / 9)) for k in range(10)]
        pygame.draw.lines(plate, (*P["grain"], 34), False, pts, 1)
    grad = pygame.Surface((S, S), pygame.SRCALPHA)
    for yy in range(S):
        f = max(0.0, (yy - my) / (ry * 1.1))
        v = int(255 - 92 * min(1.0, f))
        pygame.draw.line(grad, (v, v, v, 255), (0, yy), (S, yy))
    plate.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    m.blit(plate, (0, 0))
    pygame.draw.line(m, (*P["grain"], 190), (mx, my - int(ry * 0.88)), (mx, my + int(ry * 0.9)), 2)
    pygame.draw.line(m, (*P["hi"], 110), (mx - 1, my - int(ry * 0.8)), (mx - 1, my + int(ry * 0.4)), 1)
    pygame.draw.arc(m, P["grain"], (mx - int(r * 0.58), my - int(r * 0.5), int(r * 1.16), int(r * 0.5)), 3.35, 6.1, 2)
    pygame.draw.line(m, P["grain"], (mx, my - int(r * 0.16)), (mx - 2, my + int(r * 0.4)), 2)
    pygame.draw.line(m, (*P["hi"], 150), (mx - 3, my - int(r * 0.14)), (mx - 5, my + int(r * 0.34)), 1)
    gx_, gy_ = max(-1, min(1, gaze[0])), max(-1, min(1, gaze[1]))
    pdx, pdy = int(gx_ * r * 0.055), int(gy_ * r * 0.065)
    for sgn in (-1, 1):
        ex = mx + sgn * int(r * 0.38)
        ey = my - int(r * 0.18)
        for i, (rr, c) in enumerate([(0.205, (66, 55, 42)), (0.15, (34, 27, 20)), (0.095, (7, 6, 4))]):
            _pmask_jag(m, ex + i, ey + i, r * rr, r * rr * 1.25, c, seed + 11 + i, n=12, jit=0.16)
        if ember > 0.05:
            px, py = ex + pdx, ey + 2 + pdy
            gs = int(r * 0.34) + 2
            gl = pygame.Surface((gs, gs), pygame.SRCALPHA)
            gr = gs // 2
            pygame.draw.circle(gl, (*_PMASK_GOLD, int(52 * ember)), (gr, gr), max(1, int(r * 0.075)))
            m.blit(gl, (px - gr, py - gr), special_flags=pygame.BLEND_RGBA_ADD)
            gcol = tuple(int((60, 50, 24)[i] + (_PMASK_GOLD[i] - (60, 50, 24)[i]) * ember) for i in range(3))
            pygame.draw.circle(m, gcol, (px, py), max(1, int(r * 0.042)))
            if ember > 0.4:
                pygame.draw.circle(m, _PMASK_HOT, (px, py), max(1, int(r * 0.02)))
    crk = [(mx + int(r * 0.46), my + int(r * 0.08)), (mx + int(r * 0.56), my + int(r * 0.44)),
           (mx + int(r * 0.4), my + int(r * 0.76))]
    pygame.draw.lines(m, P["edge"], False, crk, 2)
    return m


def draw_pallid_3d(surf, cx, cy, r, yaw=0.0, lean=6.0, gaze=(0.0, 0.25),
                   blend=0.5, seed=7, ember=1.0,
                   intent=0.0, strain=0.0, skew=0.0):
    """The Pallid Mask as ONE real 3D object: a single curved SHEET -- the FRONT
    CAP of an ellipsoid (semi-axes Rx < Ry, a REAL depth Rz), a bent oval of
    "paper", NOT a closed egg. `yaw` rotates the whole mesh about the vertical
    axis and projects it, so the carved face, the curved edge-on profile (a bent
    crescent of depth Rz, never a flat line and never a solid oval), and the pale
    concave inside seen from behind ALL fall out of the same geometry -- no swap,
    no billboard, no nose. BOTH sides render in the pale bone colour, so from
    behind it reads as a mask (its inside), never a dark half. The carved FACE
    (pale plate, brow, deep jagged sockets with a gold pinprick, centre seam, a
    hairline crack) is drawn as 3D-anchored overlays on the FRONT face ONLY and
    culls as it turns -- NO eyes from behind. `lean` is a small in-plane roll;
    `gaze` aims the gold; `ember` its life.

    EXPRESSION (`intent`, `strain`, `skew`, all 0..1) -- the apex's face.
    The Mask is a CARVED OBJECT, so it must never emote: a mask that smiles
    is a cartoon. What it does instead is WORK -- the timber itself moving in
    ways timber cannot. There is no mouth and no nose to act with (NARRATIVE
    §6a), so the whole vocabulary is the sockets, the embers, the centre seam and
    the crack:

      intent  it has you. Sockets NARROW to a focused slot, the embers steady
              and brighten. This is the difference between being near a thing
              and being looked at by one.
      strain  it is close, and the face is coming apart to take you: the seam
              gaps open and the crack spreads and lengthens.
      skew    wrongness. The two sockets stop agreeing -- one narrows ahead of
              the other. Cheap, and deeply unpleasant, because a carved face is
              symmetrical by construction and this one is not.

    The caller EASES these (Game._tick_apex), so the face moves continuously
    rather than snapping between states -- fluid is the point; a face that
    changes on a frame reads as a sprite swap."""
    r = max(4, int(r))
    P = _pmask_pal(blend)

    def dk(c, f):
        return tuple(max(0, min(255, int(x * f))) for x in c)

    Rx, Ry, Rz = r * 0.78, r * 1.05, r * 0.42

    def _mask_hem(lx):
        """The lower HEM of the sheet, in face-plane units: how far down the
        mask reaches at horizontal position `lx`.

        It is a HALF-MASK (NARRATIVE §6a, canon, stated twice: "the King's own
        pale half-mask"). It had been modelled as a full oval, and that single
        wrong decision is most of why the object read as a wooden egg -- an
        egg is exactly what a featureless closed oval IS, and no amount of
        shading fixes a silhouette. A half-mask covers brow, eyes and
        cheekbones and STOPS, so the outline itself says "mask" before any
        detail is read, and it stays honest about the canon: there is no
        mouth here because there is no lower face to put one on.

        Deepest at the centre and rising at the temples, with a shallow jag so
        the hem reads as carved and broken rather than die-cut."""
        u = max(-1.0, min(1.0, lx / Rx))
        return Ry * (0.54 - 0.20 * u * u)
    # Ambient is LOW on purpose (2026-07 remake). It was 0.58, which squeezed
    # the whole shell into a 0.58..1.0 value range: a flat tan oval that read as
    # a wooden egg or a river stone, not a carved face. Carving is only legible
    # as light falling ACROSS a form, so the shell needs most of the range.
    amb = 0.20
    Lx, Ly, Lz = -0.38, -0.52, 0.76
    ll = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz)
    Lx, Ly, Lz = Lx / ll, Ly / ll, Lz / ll
    cpsi, spsi = math.cos(yaw), math.sin(yaw)
    lrr = math.radians(lean)
    cl, sl = math.cos(lrr), math.sin(lrr)
    nphi, nth = 34, 56

    def rp(x, y, z):                                          # rotate + roll -> screen
        xr = x * cpsi + z * spsi
        zr = -x * spsi + z * cpsi
        return xr * cl - y * sl, xr * sl + y * cl, zr

    # ---- the shell body: a single curved SHEET (the FRONT cap only) -- a bent
    # oval of paper, NOT a closed egg. BOTH sides are drawn in the pale front
    # colour, so from behind you see its pale concave INSIDE (still reads as a
    # mask), never a dark far cap and never empty ----
    grid = []
    for i in range(nphi + 1):
        phi = math.pi * i / nphi
        sp, cpp = math.sin(phi), math.cos(phi)
        row = []
        for j in range(nth + 1):
            th = 2 * math.pi * j / nth
            st, ct = math.sin(th), math.cos(th)
            x, y, z = Rx * sp * ct, -Ry * cpp, Rz * sp * st
            nx, ny, nz = sp * ct / Rx, -cpp / Ry, sp * st / Rz
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
            nx, ny, nz = nx / nl, ny / nl, nz / nl
            sx, sy, zr = rp(x, y, z)
            row.append((z, sx, sy, zr, nx * cpsi + nz * spsi, ny,
                        -nx * spsi + nz * cpsi, x, y))
        grid.append(row)

    quads = []
    for i in range(nphi):
        for j in range(nth):
            a, b = grid[i][j], grid[i][j + 1]
            c2, e = grid[i + 1][j + 1], grid[i + 1][j]
            zc = (a[0] + b[0] + c2[0] + e[0]) * 0.25
            if zc < 0.0:                                       # FRONT cap only (no
                continue                                       # closed-egg far cap)
            lxq = (a[7] + b[7] + c2[7] + e[7]) * 0.25
            lyq = (a[8] + b[8] + c2[8] + e[8]) * 0.25
            if lyq > _mask_hem(lxq):                           # below the jaw cut
                continue
            nzr = (a[6] + b[6] + c2[6] + e[6]) * 0.25
            nxr = (a[4] + b[4] + c2[4] + e[4]) * 0.25
            nyr = (a[5] + b[5] + c2[5] + e[5]) * 0.25
            face = 1.0 if nzr >= 0.0 else -1.0                 # which side faces us
            lamb = max(0.0, (nxr * Lx + nyr * Ly + nzr * Lz) * face)
            sh = amb + (1 - amb) * lamb
            col = dk(P["base"], sh)                             # pale on BOTH sides
            zavg = (a[3] + b[3] + c2[3] + e[3]) * 0.25
            pts = [(int(cx + a[1]), int(cy + a[2])), (int(cx + b[1]), int(cy + b[2])),
                   (int(cx + c2[1]), int(cy + c2[2])), (int(cx + e[1]), int(cy + e[2]))]
            quads.append((zavg, pts, col))
    quads.sort(key=lambda q: q[0])                            # painter: far first
    for _, pts, col in quads:
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, col, pts, 1)               # cover facet seams

    # ---- the carved FACE, anchored in 3D on the FRONT hemisphere ONLY, so it
    # wraps with the shell and never shows from behind (no eyes on the back) ----
    def shell_pt(lx, ly):
        """Project a point on the oval face-plane onto the front bulge; return
        screen (px, py) + the point's facing (rotated normal z, ~1 head-on)."""
        u, v = lx / Rx, ly / Ry
        s2 = min(1.0, u * u + v * v)
        z = Rz * math.sqrt(max(0.0, 1.0 - s2))
        sx, sy, _zr = rp(lx, ly, z)
        nx, ny, nz = lx / (Rx * Rx), ly / (Ry * Ry), z / (Rz * Rz)
        nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        return cx + sx, cy + sy, (-nx * spsi + nz * cpsi) / nl

    seam = []                                                # the centre seam
    for k in range(13):
        ly = -Ry * 0.78 + k / 12.0 * Ry * 1.30
        if ly > _mask_hem(0.0) - Ry * 0.05:                  # stop at the hem
            break
        px, py, f_ = shell_pt(0.0, ly)
        if f_ > 0.14:
            seam.append((int(px), int(py)))
    if len(seam) >= 2:
        if strain > 0.02:
            # STRAIN opens the seam into a GAP -- the face starting to come
            # apart. Drawn as two lines walking away from the centre line, with
            # true black between, so it reads as a split and not a thicker line.
            off = max(1, int(r * 0.055 * strain))
            for sgn in (-1, 1):
                pygame.draw.lines(surf, P["grain"], False,
                                  [(x + sgn * off, y) for x, y in seam], 2)
            pygame.draw.lines(surf, (2, 2, 2), False, seam,
                              max(1, int(r * 0.045 * strain)))
        else:
            pygame.draw.lines(surf, P["grain"], False, seam, 2)

    brow = []                                                # the brow ridge
    for k in range(-6, 7):
        fr = k / 6.0
        px, py, f_ = shell_pt(fr * Rx * 0.52, -Ry * 0.30 + (fr * fr) * Ry * 0.05)
        if f_ > 0.14:
            brow.append((int(px), int(py)))
    if len(brow) >= 2:
        pygame.draw.lines(surf, dk(P["grain"], 0.85), False, brow, 2)

    # ---- the two sockets. These are the whole face (there is no nose and no
    # mouth, NARRATIVE §6a), so if they do not read as HOLES the object is a
    # pebble with two dots on it -- which is exactly how it shipped. Three
    # things make a hole read, and the old version had none of them: it must be
    # BIG relative to the face, it must go BLACK at the centre rather than
    # dark-brown, and the brow above it must throw a CAST SHADOW down into it.
    gx_, gy_ = max(-1, min(1, gaze[0])), max(-1, min(1, gaze[1]))
    exl, eyl = Rx * 0.46, -Ry * 0.16
    for sgn in (-1, 1):
        px, py, fac = shell_pt(sgn * exl, eyl)
        if fac <= 0.16:                                      # gone past the edge
            continue
        # EXPRESSION: this socket's own narrowing. `skew` splits the two so they
        # disagree -- the left leads, the right lags -- which is the whole trick:
        # a carving is symmetrical by construction, so asymmetry reads as the
        # object being wrong rather than as a face pulling a face.
        squeeze = _clamp(intent + skew * (0.55 if sgn < 0 else -0.55))
        lid = 1.0 - 0.46 * squeeze
        # ~1.8x the old socket: it now occupies the face the way an eye socket
        # in a carved mask does, instead of sitting on it like a drilled pin.
        srx = max(1.5, r * 0.34 * (0.35 + 0.65 * fac))       # compresses toward profile
        sry = max(1.5, r * 0.36 * lid)
        # the orbit RIM first -- a pale raised lip catching light on the
        # outside, which is what tells the eye the middle is sunk below it
        _pmask_jag(surf, px, py - sry * 0.06, srx * 1.16, sry * 1.14,
                   dk(P["base"], 1.07), seed + 5, n=13, jit=0.14)
        # then down the wall of the hole into true black
        for (rr, ccol) in ((1.0, dk(P["grain"], 0.72)), (0.80, (30, 24, 18)),
                           (0.60, (12, 10, 7)), (0.40, (2, 2, 2))):
            _pmask_jag(surf, px, py, srx * rr, sry * rr, ccol,
                       seed + 11 + int(rr * 13), n=12, jit=0.18)
        # the BROW's cast shadow: an arc of dark laid over the TOP of the
        # socket, so the ridge above reads as standing proud of the hole
        sh_r = pygame.Rect(int(px - srx), int(py - sry * 1.02),
                           max(2, int(srx * 2)), max(2, int(sry * 1.15)))
        shl = pygame.Surface((sh_r.w, sh_r.h), pygame.SRCALPHA)
        pygame.draw.ellipse(shl, (0, 0, 0, 132),
                            (0, -int(sh_r.h * 0.30), sh_r.w, int(sh_r.h * 1.3)))
        surf.blit(shl, sh_r.topleft)
        # The gold is an EMBER DOWN A HOLE, never an eyeball. A filled gold disc
        # in a dark socket reads instantly as a cartoon eye (or an owl), which
        # is a worse failure than the pebble it replaced -- so there is no solid
        # pupil here at all. What carries it is a soft ADDITIVE bloom, widest
        # and faintest at the outside, with one tiny hot core: light coming up
        # out of the socket rather than an object sitting in it. The bloom is
        # also what survives at play size, when the socket is a few pixels.
        if ember > 0.05:
            ppx = px + gx_ * r * 0.07 * fac
            ppy = py + gy_ * r * 0.07
            gs = int(r * 0.9) + 2
            gl = pygame.Surface((gs, gs), pygame.SRCALPHA)
            gr = gs // 2
            # intent STEADIES and lifts the ember. A wavering light reads as a
            # dying thing; a pinprick that does not waver while it closes on you
            # reads as attention.
            lift = 1.0 + 0.85 * intent
            for (rr, aa) in ((0.09, 26), (0.055, 44), (0.03, 66)):
                pygame.draw.circle(gl,
                                   (*_PMASK_GOLD,
                                    min(255, int(aa * lift * ember * fac))),
                                   (gr, gr), max(1, int(r * rr)))
            surf.blit(gl, (int(ppx) - gr, int(ppy) - gr), special_flags=pygame.BLEND_RGBA_ADD)
            if ember > 0.4:
                pygame.draw.circle(surf, _PMASK_HOT, (int(ppx), int(ppy)),
                                   max(1, int(r * 0.022)))

    # ---- CHEEK HOLLOWS. A carved face is planes meeting at edges; a smooth
    # bulge is a pebble. Two soft hollows under the sockets give the shell one
    # more plane change below the eyes, which is what stops the lower half
    # reading as blank shell once the sockets are dark.
    for sgn in (-1, 1):
        chx, chy, cfac = shell_pt(sgn * Rx * 0.50, Ry * 0.18)
        if cfac <= 0.20:
            continue
        cw = max(2, int(r * 0.30 * cfac))
        ch = max(2, int(r * 0.34))
        cl_ = pygame.Surface((cw * 2, ch * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(cl_, (0, 0, 0, int(30 * cfac)), (0, 0, cw * 2, ch * 2))
        surf.blit(cl_, (int(chx) - cw, int(chy) - ch))

    crack = []                                               # a hairline crack, lower-right
    for (lx, ly) in ((Rx * 0.30, -Ry * 0.34), (Rx * 0.40, -Ry * 0.02), (Rx * 0.30, Ry * 0.26)):
        px, py, f_ = shell_pt(lx, ly)
        if f_ > 0.14:
            crack.append((int(px), int(py)))
    if len(crack) >= 2:
        pygame.draw.lines(surf, P["edge"], False, crack,
                          max(1, int(1 + r * 0.03 * strain)))
        if strain > 0.35:
            # ...and it RUNS. A crack that only thickens reads as a drawn line
            # getting bolder; one that travels reads as damage happening now.
            run = []
            for k in range(5):
                f = k / 4.0
                lx = Rx * (0.30 + 0.34 * f) * (1.0 + 0.5 * strain)
                ly = Ry * (0.26 + 0.30 * f * strain)
                px2, py2, f_ = shell_pt(lx, ly)
                if f_ > 0.14:
                    run.append((int(px2), int(py2)))
            if len(run) >= 2:
                pygame.draw.lines(surf, P["edge"], False, run, 1)

    # ---- the cut EDGE of the sheet. It is a bent plate of finite thickness,
    # not a soft blob: tracing its silhouette in the dark edge tone reads as
    # the sawn rim and stops the object dissolving into whatever is behind it.
    rim = []
    for k in range(49):                       # over the crown, left to right
        th = math.pi + k / 48.0 * math.pi
        lx, ly = math.cos(th) * Rx * 0.995, math.sin(th) * Ry * 0.995
        if ly > _mask_hem(lx):
            continue
        px, py, _f = shell_pt(lx, ly)
        rim.append((int(px), int(py)))
    hem = []                                  # back along the cut jaw
    for k in range(33):
        lx = Rx * (1.0 - 2.0 * k / 32.0) * 0.985
        ly = min(_mask_hem(lx), Ry * 0.985)
        u = lx / Rx
        if u * u + (ly / Ry) ** 2 > 1.0:      # stay on the shell
            continue
        px, py, _f = shell_pt(lx, ly)
        hem.append((int(px), int(py)))
    outline = rim + hem
    if len(outline) >= 3:
        pygame.draw.lines(surf, dk(P["edge"], 0.85), True, outline,
                          max(1, int(r * 0.045)))


_MASK_PART_CACHE = {}            # composed Mask layers, keyed by their args
_MASK_PART_CACHE_MAX = 32        # the bearer walks through ~12 keys a second


def draw_pallid_mask_part(surf, cx, cy, r, deploy=1.0, gaze=(0.0, 0.3),
                          blend=0.5, seed=7, ang=1.2, side=-1, lean=8.0,
                          yaw=0.0, intent=0.0, strain=0.0, skew=0.0):
    """The Mask as a PART: it rides out of its own cut (`deploy` 0..1) along
    the cut normal, held at the rim by shroud grips. `gaze` (gx, gy in -1..1)
    aims the gold pupils. `yaw` turns it as ONE 3D object (`draw_pallid_3d`) --
    His face, the curved edge-on profile, and the hollow back all fall out of
    the same rotating shell, no swap. Caller enforces one-bearer-at-a-time."""
    d = max(0.0, min(1.0, deploy))
    dx_, dy_ = math.cos(ang), math.sin(ang)
    nx, ny = -dy_ * side, dx_ * side
    # A LOCAL layer, sized to the Mask, not to the target. On the bearer this
    # runs live every frame straight onto the 960x640 screen, and allocating +
    # blitting a full screen copy for a 40px face was the single most expensive
    # draw in the game. r*3.5 clears the shell, its deploy offset and its glow.
    box = int(r * 3.5) + 8
    ox, oy = int(cx) - box, int(cy) - box
    # The clip polygon's local vertices go in the key rather than being
    # re-derived from (cx, cy): int() truncates toward zero, so two positions
    # with the same fractional part can still land a vertex a pixel apart when
    # the un-offset value crosses zero. Keying on the vertices themselves makes
    # that impossible to get wrong.
    p0 = (cx - dx_ * 400, cy - dy_ * 400); p1 = (cx + dx_ * 400, cy + dy_ * 400)
    p2 = (p1[0] - nx * 400, p1[1] - ny * 400); p3 = (p0[0] - nx * 400, p0[1] - ny * 400)
    clip = tuple((int(a) - ox, int(b) - oy) for a, b in (p0, p1, p2, p3))
    # MEMOISED. draw_pallid_3d rasterises ~1250 polygons per call: 5.1ms of a
    # 16ms frame, every frame, for the one bearer -- by a wide margin the most
    # expensive draw left in the game. The layer is a pure function of the
    # arguments once the whole-pixel position is factored out into (ox, oy), so
    # it can simply be remembered. The apex earns the hit because the caller
    # holds its face steady within an animation bucket (`draw_amalgam_sprite`);
    # a tool that varies the face per call gets a fresh key per call and stays
    # honest. Capped and evicted oldest-first, one at a time -- clearing it
    # wholesale is what put the sawtooth back into the unit cache.
    key = (round(cx % 1.0, 3), round(cy % 1.0, 3), r, d, gaze, blend, seed,
           ang, side, lean, yaw, intent, strain, skew, clip)
    lay = _MASK_PART_CACHE.get(key)
    if lay is None:
        lay = pygame.Surface((box * 2, box * 2), pygame.SRCALPHA)
        mcx = cx + nx * r * 0.9 * d
        mcy = cy + ny * r * 0.9 * d
        ember = 0.25 + 0.75 * d
        # the Mask itself -- one rotating 3D shell, rendered onto its own layer
        draw_pallid_3d(lay, mcx - ox, mcy - oy, r, yaw=yaw, lean=lean,
                       gaze=gaze, blend=blend, seed=seed, ember=ember,
                       intent=intent, strain=strain, skew=skew)
        # clip whatever is still INSIDE the cut (the far side of the cut line)
        # so it reads as rising from the slit; everything there ends dead flat
        pygame.draw.polygon(lay, (0, 0, 0, 0), list(clip))
        if len(_MASK_PART_CACHE) >= _MASK_PART_CACHE_MAX:
            _MASK_PART_CACHE.pop(next(iter(_MASK_PART_CACHE)))
        _MASK_PART_CACHE[key] = lay
    surf.blit(lay, (ox, oy))
    # the cut ends peek past the rim; shroud grips hold it on the line
    ln = r * (1.3 + 0.5 * d)
    q0 = (cx - dx_ * ln / 2, cy - dy_ * ln / 2); q1 = (cx + dx_ * ln / 2, cy + dy_ * ln / 2)
    pygame.draw.line(surf, VOID, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), 3)
    off = 2.2
    pygame.draw.line(surf, RIM,
                     (int(q0[0] - nx * off + dx_ * ln * 0.04), int(q0[1] - ny * off + dy_ * ln * 0.04)),
                     (int(q1[0] - nx * off - dx_ * ln * 0.06), int(q1[1] - ny * off - dy_ * ln * 0.06)), 2)
    grng = random.Random(seed + 3)
    for sgn in (-1, 1):
        gx = cx + dx_ * sgn * r * 0.52 + nx * r * 0.05
        gy = cy + dy_ * sgn * r * 0.52 + ny * r * 0.05
        lr = r * grng.uniform(0.15, 0.21)
        pygame.draw.ellipse(surf, SHROUD, (int(gx - lr), int(gy - lr * 0.75), int(lr * 2), int(lr * 1.5)))
        pygame.draw.arc(surf, SHROUD_LO, (int(gx - lr), int(gy - lr * 0.75), int(lr * 2), int(lr * 1.5)), 3.6, 5.9, 2)
    fx_ = cx + nx * r * 0.16; fy2 = cy + ny * r * 0.16; lr = r * 0.13
    pygame.draw.ellipse(surf, SHROUD, (int(fx_ - lr), int(fy2 - lr * 0.7), int(lr * 2), int(lr * 1.4)))
    for k in range(2):
        mxp = cx - nx * grng.uniform(3, 8) + grng.uniform(-2, 2)
        myp = cy - ny * grng.uniform(3, 8) + grng.uniform(-2, 2)
        pygame.draw.circle(surf, EMBER_G if k == 0 else SHROUD, (int(mxp), int(myp)), 1)


# ---- the possessed BEARER (drawn ONLY on the Mask-bearer) -------------------
# When the Mask jumps to an amalgam it POWERS IT UP -- and the power-up is
# SIZE: the bearer is simply a BIGGER amalgam than the ordinary shadows
# (BEARER_SCALE), not a busier one. Its one extra flourish is the CROWN -- an
# arc of ember-cuts (watching apertures) over the Mask. No hitbox; dread only.
BEARER_SCALE = 1.5

# HOW BIG AN ORDINARY AMALGAM DRAWS (maintainer, 2026-07: "make them bigger").
# The body used to render at 0.8 of the part space and no amount of interior
# detail survived it -- the lantern eye measured a peak delta of 96 in
# isolation and still read as a faint dot at 130px in a real dark scene,
# because the whole creature was only a few dozen pixels tall. Legibility here
# is a SIZE problem before it is a lighting one. Multiplies the base 0.8, so
# 1.25 lands the body at full part-space scale; the bearer stacks BEARER_SCALE
# on top of this and stays proportionally the bigger thing.
AMALGAM_SCALE = 1.25


def _bearer_crown(surf, mcx, mcy, mr, power, seed):
    """An arc of ember-cuts over the Mask -- a crown of watching apertures."""
    if power <= 0.05:
        return
    rng = random.Random(seed + 9)
    n = 7
    for i in range(n):
        f = i / (n - 1)
        a = math.pi * (1.12 + 0.76 * f)
        cr = mr * (1.45 + 0.15 * power)
        cx = mcx + math.cos(a) * cr
        cy = mcy + math.sin(a) * cr * 0.85 - mr * 0.35
        dd = power * (0.55 + 0.45 * rng.random())
        _cut_line(surf, cx, cy, a + 1.57, mr * 0.55 * dd, alpha=dd, side=1)
        if dd > 0.4:
            _eye(surf, cx, cy, r=1)


# ---- THE REACH: the apex's grabbing limbs ------------------------
# The apex's second distinguishing feature, after the face, and the maintainer
# picked it over improving the crown for a plain reason: at play size the crown
# is a ring of sparkles you read as ornament, while a limb coming at you is
# read instantly and by everybody.
#
# The two things these are for:
#   1. REACTION. Every other part of every amalgam idles on its own clock and
#      would do the same thing in an empty room. These do not exist unless it
#      has you, they point where you ARE (a screen-space vector, so they aim
#      true under any camera yaw), and they extend as it closes.
#   2. TELEGRAPH. The catch was instant contact -- no wind-up, nothing to read.
#      Now the hands arrive before the body does: full extension IS the last
#      warning, and it is on screen for the seconds before APEX_CATCH_DIST.
#
# They still obey the family grammar. Each grows out of its OWN cut on the body,
# nothing touches anything, and they are drawn into the same layer as the parts
# so the bone outline strokes them too -- they are the creature, not an effect
# laid over it.
REACH_MAX = 46.0                 # local px of full extension
REACH_ARMS = 3                   # odd, so one comes straight down the line


def _reach_anchor(parts):
    """Where the limbs grow FROM: the body's own centre in layer space. Masses
    if the deal has any (they are the trunk), else the mean of everything."""
    ms = [(75 + p[2], p[3] - _MASS_DY[p[0]]) for p in parts if p[0] in _MASS_DY]
    if not ms:
        ms = [(75 + p[2], p[3] - 46) for p in parts]
    # Lifted off the centroid to about where shoulders would be if it had any:
    # arms leaving from the middle of the mass come out through the legs.
    return (sum(a for a, _ in ms) / len(ms),
            sum(b for _, b in ms) / len(ms) - 9.0)


def _reach_limbs(lay, ax, ay, dx, dy, amount, t, seed, n=3):
    """Grow `n` grasping arms from (ax, ay) toward (dx, dy), extended by
    `amount` 0..1. Each arm clutches on its own phase -- a hand that opens and
    closes reads as WANTING, and arms that all clutch together read as one
    machine."""
    if amount <= 0.02:
        return
    W, H = lay.get_size()
    dl = math.hypot(dx, dy) or 1.0
    dx, dy = dx / dl, dy / dl
    # Never claw into the floor or straight out the top of the layer: the reach
    # is a direction the player reads, not a vector that has to be exact.
    dy = max(-0.80, min(0.40, dy))
    dl = math.hypot(dx, dy) or 1.0
    dx, dy = dx / dl, dy / dl
    nx, ny = -dy, dx                                   # across the reach
    rng = random.Random(seed * 977 + 13)

    def cl(px, py):
        return (max(5.0, min(W - 6.0, px)), max(5.0, min(H - 6.0, py)))

    # A reach that comes STRAIGHT AT the camera lands on top of the legs and
    # stops reading as arms at all, which is the one case the tilt makes common
    # (anything north of you reaches down-screen). Two corrections, both cheap:
    # the arms fan wider the more downward the reach is, and every arm arcs UP
    # over the body before it comes down -- which is also just how a thing that
    # is reaching for you moves.
    fan = 1.0 + 0.85 * max(0.0, dy)
    for i in range(n):
        spread = ((i - (n - 1) / 2.0) * 12.0 + rng.uniform(-3, 3)) * fan
        ph = t * (1.5 + 0.35 * i) + i * 2.3 + (seed % 11) * 0.6
        pull = 0.5 + 0.5 * math.sin(ph)
        ext = REACH_MAX * amount * (0.60 + 0.40 * pull)
        arc = 7.0 + 10.0 * amount
        rx, ry = ax + nx * spread * 0.4, ay + ny * spread * 0.4
        mx, my = cl(rx + dx * ext * 0.55 + nx * spread * 0.6,
                    ry + dy * ext * 0.55 + ny * spread * 0.6 - arc)
        tx, ty = cl(rx + dx * ext + nx * spread, ry + dy * ext + ny * spread)
        _tent(lay, [(rx, ry), (mx, my), (tx, ty)], 4.2, 1.4)
        _lump(lay, mx, my, 3.0, 2.4, lo=False)         # the elbow knot
        # THE HAND, and it has to READ as one: a palm and four fingers that
        # CURL. Straight spokes off the wrist looked like a broken twig at play
        # size and the grip was the whole idea, so each finger is a two-segment
        # path that bends inward, and `pull` closes them as the arm draws in.
        _lump(lay, tx, ty, 3.2, 2.6, lo=False)         # the palm
        for j in range(4):
            fa = (j - 1.5) * (0.62 - 0.34 * pull)
            fl = (10.0 - 3.4 * pull) * (0.5 + 0.5 * amount)
            curl = fa + (0.85 + 0.75 * pull) * (1 if fa >= 0 else -1)

            def pt(ang, ln):
                return (dx * math.cos(ang) - dy * math.sin(ang)) * ln, \
                       (dx * math.sin(ang) + dy * math.cos(ang)) * ln
            k1x, k1y = pt(fa, fl * 0.6)
            k2x, k2y = pt(curl, fl * 0.55)
            kx_, ky_ = tx + k1x, ty + k1y
            _tent(lay, [(tx, ty), cl(kx_, ky_),
                        cl(kx_ + k2x, ky_ + k2y)], 2.1, 0.9)
        _cut_line(lay, rx, ry, math.atan2(dy, dx) + math.pi / 2,
                  16 * amount, alpha=0.5 * amount, side=1)


# ---- the per-unit COMPOSE CACHE ------------------------------------------
# A storm unit cost ~2.8ms of a real frame, measured, nearly all of it inside
# this module: 22 units put a frame at 53.3ms (18.8 fps), so the maintainer's
# requested soft cap of 20-25 was unreachable and the cap had to sit at 10.
#
# The way to earn it back is fewer RENDERS, not a braver cap. A unit's whole
# appearance is a pure function of (seed, birth, dispel, gaze, t) -- every part
# draw is deterministic and the only randomness (`_cut_line`'s motes) is seeded
# off position -- so QUANTISING t makes the render cacheable. At UNIT_ANIM_HZ the
# flesh wobbles 12 times a second instead of 60 and each unit re-renders on one
# frame in five. For a creeping shadow the lower cadence is not a loss; if
# anything the slight stutter suits it.
UNIT_ANIM_HZ = 12
_UNIT_CACHE = {}                 # (seed, bearer) -> (state, (surf, dx, dy))
_UNIT_PAD = 5                    # room for the outline + the ghost's offset


def reset_amalgam_cache():
    """Drop the composed-unit cache (scene load, or a palette/tuning change)."""
    _UNIT_CACHE.clear()
    _MASK_PART_CACHE.clear()


def _compose_unit(seed, b, g, gaze, t, bearer, extra=0, reach=None,
                  lamp=0.0):
    """Render ONE unit -- parts, tissue, outline, ghost, body -- into its own
    padded surface. Returns (surface, dx, dy) where (dx, dy) is where to blit it
    relative to the unit's feet. Pure in its arguments, which is what makes the
    cache above safe."""
    global _GAZE
    parts = assemble(seed, extra=extra)
    n = len(parts)
    LW, LH = 150, 104
    lay = pygame.Surface((LW, LH), pygame.SRCALPHA)
    _GAZE = gaze
    rng = random.Random(seed * 7 + 3)
    anc = [(75 + p[2], (p[3] - 40)) for p in parts]
    for i in range(len(anc) - 1):
        a0, b0 = anc[i], anc[i + 1]
        for k in range(3):
            f = k / 2.0
            hx = a0[0] + (b0[0] - a0[0]) * f + rng.uniform(-2, 2)
            hy = a0[1] + (b0[1] - a0[1]) * f + rng.uniform(-2, 2)
            # The threads are the ONLY tissue between parts (module docstring:
            # the brain stitches "one creature" out of them). Kept below
            # _EMIT_FLOOR on purpose: tissue should NOT take an outline, or the
            # parts start touching and "nothing touches" dies with it.
            _haze(lay, hx, hy, 4 + rng.uniform(0, 2.5), 74)
    for idx, (nm, fn, x0, y0, flip) in enumerate(parts):
        if g > 0.0:
            # the peeling: last parts first, each back into its cut
            dg = _clamp((g - (n - 1 - idx) * 0.13) / 0.48)
            d, mode = 1.0 - dg, "leave"
        elif b < 1.0:
            d, mode = _clamp((b - idx * 0.13) / 0.48), "enter"
        else:
            d, mode = 1.0, "idle"
        k = 0.5 + 0.5 * math.sin(t * (0.9 + 0.13 * (idx % 3))
                                 + idx * 1.7 + seed)
        dx_ = math.sin(t * 0.6 + idx * 2.1 + seed) * 1.2
        dy_ = math.cos(t * 0.5 + idx * 1.3) * 1.0
        if d > 0.01:
            _draw_maybe_flipped(lay, fn, 75 + x0 + dx_, y0 + dy_,
                                d, mode, k, flip)
        else:
            # its cut alone, dying
            _cut_line(lay, 75 + x0 + dx_, (y0 + dy_) - 44, 1.2, 10,
                      alpha=0.3, side=1)
    # THE REACH, into the SAME layer as the parts (apex only; `reach` is None
    # for every ordinary unit, so their compose is byte-identical). Drawn last
    # so the arms pass in front of the body they grew out of, and inside the
    # layer so the bone outline strokes them like any other flesh.
    if reach is not None and b >= 1.0 and g <= 0.0:
        rdx, rdy, ramt = reach
        ax, ay = _reach_anchor(parts)
        _reach_limbs(lay, ax, ay, rdx, rdy, ramt, t, seed, n=REACH_ARMS)
    # ---- THE LANTERN'S LIGHT, onto the flesh it stands in ------------------
    # Additive over the assembled parts and BEFORE the outline/ghost/scale, so
    # the lit flesh is composited, scaled and stroked as one body. BLEND_RGB_ADD
    # leaves destination alpha alone, so this can only brighten pixels that are
    # already there -- it cannot paint into the empty space around the creature,
    # which is exactly the failure the blurred halo had.
    #
    # Killed outright while stared at. The lantern obeys the family's one rule
    # (look straight at it and every ember dies) or it would hand the player a
    # creature that is easier to find the harder they look away, which inverts
    # the dispel the whole family is built on.
    if lamp > 0.0 and not gaze:
        for nm, fn, x0, y0, flip in parts:
            if nm != "eyelamp":
                continue
            # its own build-out fades the light in with it: a part still
            # surfacing through its cut is not yet an eye that can shine.
            amt = lamp * (b if b < 1.0 else 1.0) * (1.0 - g)
            if amt <= 0.02:
                break
            gs = _lamp_surface(EYE_LAMP_R, min(1.0, amt))
            lay.blit(gs, (int(75 + x0 - EYE_LAMP_R), int(y0 - 50 - EYE_LAMP_R)),
                     special_flags=pygame.BLEND_RGB_ADD)
            break
    _GAZE = False
    # THE BEARER is simply a BIGGER amalgam -- that size IS the power-up tell.
    sc = 0.8 * AMALGAM_SCALE * (BEARER_SCALE if bearer else 1.0)
    sw, sh = int(LW * sc), int(LH * sc)
    scaled = pygame.transform.scale(lay, (sw, sh))
    base = int(GY * sc) + 2
    phase = 0.42 + 0.45 * (math.sin(t * 1.1 + seed) * 0.5 + 0.5)
    phase *= (1.0 - 0.5 * g)                      # thins as it is stared apart

    pad = _UNIT_PAD
    out = pygame.Surface((sw + pad * 2, sh + pad * 2), pygame.SRCALPHA)
    # ---- THE OUTLINE (maintainer, 2026-07: "can't you just give each sprite a
    # white border pixel? ... The glowing mist isn't good"). A one-pixel stroke
    # around the silhouette, drawn UNDER the body.
    #
    # It replaced a blurred additive halo, and the instinct behind it was
    # right. A bloom has to be BRIGHT to register at all, and brightness spread
    # across a near-black creature reads as a glowing spirit rather than a
    # shadow you can see; every attempt to tune it just traded one failure for
    # the other (too dim to find, or a pale ghost). A stroke costs nothing in
    # VALUE -- the body stays exactly as black as it was, only its edge is
    # stated -- and it stays sharp at small sizes, where a blur is only fog.
    #
    # PRESENTATION ONLY, and it must stay that way: no entry in
    # Scene._LIGHT_KINDS or FIXTURE_POOLS, no pool cast, invisible to lit_at.
    # It cannot deny a Watcher a spawn spot, burn anything, or gate the
    # lost-space mouth. The creature is VISIBLE, not LIT.
    out.blit(_outline(scaled, AMALGAM_EDGE, AMALGAM_EDGE_W), (pad, pad))
    ghost = scaled.copy()
    ghost.set_alpha(int(230 * phase * 0.45))
    out.blit(ghost, (pad - 3, pad - 1))
    scaled.set_alpha(int(230 * phase))
    out.blit(scaled, (pad, pad))
    return out, -(sw // 2) - pad, -base - pad


def draw_amalgam_sprite(surf, x, y, seed=0, gaze=False, birth=None,
                        dispel=None, mask=None, lamp=0.0):
    """Feet at (x, y). `birth` 0..1 is the manifest ramp (parts build out
    staggered); `dispel` 0..1 is the gaze-dispel fraction (parts peel back
    into their cuts in reverse); `gaze` darkens every ember while the
    player stares (the family rule).

    `lamp` 0..1 is how hot THE LANTERN EYE burns -- decorative light thrown
    onto the creature's own flesh, never onto the world and never into the
    light table (see the EYE_LAMP note). Feed it a STATE, not a loop: it is
    meant to be a tell the player learns to read, the way the apex's face
    works, so it should say something true about what the thing is doing.
    Quantised into the cache identity below, because a value that changes
    every frame would re-compose every unit every frame and undo the cache
    the storm's frame budget depends on."""
    t = pygame.time.get_ticks() / 1000.0
    b = 1.0 if birth is None else _clamp(birth)
    g = 0.0 if dispel is None else _clamp(dispel)
    bearer = mask is not None
    # THE APEX wears its host's deal plus 2-3 added parts. It rides in
    # the mask dict so an ordinary unit's call is untouched.
    extra = int(mask.get("extra", 0)) if bearer else 0
    # THE REACH is quantised into the cache identity, because it really is
    # composed into the body -- leave it out and the arms freeze pointing
    # wherever the apex was first composed, which is the one thing they exist
    # not to do. Direction to a tenth is about six degrees, which nobody sees.
    reach = None
    if bearer and mask.get("reach"):
        rd = mask["reach"]
        reach = (round(rd[0], 1), round(rd[1], 1), round(rd[2], 2))
    # THE FACE does not go into the body's compose at all -- the Mask is drawn
    # live at the bottom of this function -- but it is carried in the same
    # cached state so it can be HELD to the animation bucket, exactly like the
    # reach. Held, `draw_pallid_mask_part` sees a stable argument tuple and hits
    # its own memo instead of rasterising 1250 polygons; unheld it cost 5.1ms a
    # frame, the most expensive draw left in the game.
    #
    # GAZE rides in the held tuple too. It is a live unit vector to the player,
    # so leaving it out of the hold would change the memo key every frame and
    # the memo would never hit once -- the same trap as the reach.
    if bearer:
        gz = mask.get("gaze", (0.0, 0.3))
        face = (round(mask.get("intent", 0.0), 2),
                round(mask.get("strain", 0.0), 2),
                round(mask.get("skew", 0.0), 2),
                round(gz[0], 2), round(gz[1], 2))
    else:
        face = ()
    # Quantise the animation clock and cache on it -- see the cache note above.
    #
    # STAGGERED per unit. With one shared clock every unit's bucket rolled over
    # on the SAME frame, so the whole storm re-rendered at once: measured, 22
    # units averaged 28.7ms but spiked to 59ms (17 fps) once per bucket, and the
    # average hid the hitch entirely. Offsetting each unit's phase by its seed
    # spreads those refreshes across the bucket's frames, so the cost per frame
    # is flat instead of a sawtooth. The offset is folded back out of the time
    # handed to _compose_unit, so each unit still animates smoothly in its own
    # phase rather than snapping.
    # HASH the seed, do not modulo it. `seed % 251` mapped nearby seeds to
    # nearly identical offsets, so a batch of units with sequential seeds all
    # rolled over together anyway and the sawtooth survived (measured: 22ms most
    # frames, 51ms every fifth). A multiplicative hash scatters neighbours.
    off = (((seed * 2654435761) & 0xffffffff) % 4096) / 4096.0
    bucket = int(t * UNIT_ANIM_HZ + off)
    # ONE ENTRY PER UNIT, replaced in place. Keying by (bucket, ...) grew the
    # cache until it hit a size limit and was cleared WHOLESALE, at which point
    # every unit missed at once -- so the sawtooth survived the stagger: 22 units
    # still spiked to 51.7ms. Holding a single entry per unit means the cache
    # never exceeds the unit count and nothing is ever mass-invalidated.
    ident = (seed, bearer, extra)
    hit = _UNIT_CACHE.get(ident)
    # THE ARMS HOLD THEIR AIM WITHIN A BUCKET, and so does the face. Both track
    # the player and so change every frame by definition; keying on them raw
    # would re-compose the bearer at the frame rate and undo everything the
    # cache is for (measured on HEAD: a 22-unit storm with an apex ran at 40.8ms
    # a frame). Sampling them on the bucket boundary pins the apex to ONE
    # compose per bucket, exactly like every other unit, and everything moves at
    # UNIT_ANIM_HZ -- the cadence the rest of the body already wobbles at.
    if hit is not None and bearer and hit[0][3] == bucket:
        if reach is not None:
            reach = hit[0][4]
        face = hit[0][5]
    state = (round(b, 2), round(g, 2), bool(gaze), bucket, reach, face,
             round(_clamp(lamp), 1))
    if hit is None or hit[0] != state:
        hit = (state, _compose_unit(seed, b, g, gaze,
                                    (bucket - off) / float(UNIT_ANIM_HZ),
                                    bearer, extra, reach,
                                    lamp=round(_clamp(lamp), 1)))
        _UNIT_CACHE[ident] = hit
    hit = hit[1]
    body, dx, dy = hit
    surf.blit(body, (int(x) + dx, int(y) + dy))
    sc = 0.8 * AMALGAM_SCALE * (BEARER_SCALE if bearer else 1.0)
    sw, sh = int(150 * sc), int(104 * sc)
    base = int(GY * sc) + 2
    # THE BEARER, when the storm passes `mask` (None for every ordinary
    # amalgam, so their draw is byte-identical). The power-up is the BIGGER
    # body drawn above; here we add the Mask itself + His crown of cuts.
    if mask is not None:
        power = _clamp(mask.get("deploy", 1.0))
        # WHOLE PIXELS, like the body blit above. A walking apex has a
        # fractional x, and a fractional position is part of the Mask memo's
        # key -- left alone it changed every frame and the memo never hit once.
        topy = int(y) - base
        # the Mask itself (its own cut + grips), player-scale, a 3D prop by `yaw`
        mr = mask.get("r", max(8, int(sh * 0.17)))
        mcx = int(x) + mask.get("dx", int(sw * 0.04))
        mcy = topy + mask.get("my", int(sh * 0.30))
        # `face` is the BUCKET-HELD expression, not the raw dict values: it is
        # what lets the memo above hit. The easing still runs at the frame rate
        # on the Game side; what is sampled at UNIT_ANIM_HZ is only the draw.
        draw_pallid_mask_part(surf, mcx, mcy, mr,
                              intent=face[0], strain=face[1], skew=face[2],
                              deploy=power, gaze=(face[3], face[4]),
                              blend=mask.get("blend", 0.5),
                              seed=mask.get("seed", 7),
                              lean=mask.get("lean", 8.0), yaw=mask.get("yaw", 0.0))
        # the crown of ember-cuts arcing over the Mask
        _bearer_crown(surf, mcx, mcy - mr * 0.3, mr, power, seed)
