"""The pallid-mask King fallback (when KING_UNFOLD is False), the King FX
wake/particles, and the carved door-mask used by the journal door-dream."""
import math
import random
import pygame
from constants import C_BLACK


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
