"""PAINTED LETTERING -- words on a prop, drawn as geometry in the prop's
own plane.

The world's other alphabet is the neon TUBE set (`_GLYPH` / `_draw_neon_word`
in `rendering/props.py`), which spells CASSILDA'S on the lost road's filling
station. This is its painted cousin: flat opaque strokes with wear, for a
board somebody lettered with a brush.

**Why it exists at all.** The town's welcome board was the last thing in the
game rendered in a SYSTEM FONT, and the font was only half the problem. A
rasterised word can only be blitted at some screen position, so the lettering
was pasted at the board's projected centre, screen-horizontal, while the
board itself foreshortened away under the 55 degree camera. From the east the
words floated off the plank and hung over the post. That is error class 7
(screen-aligned marks on a world-plane surface), and no amount of choosing a
nicer font fixes it -- the fix is for a letter to BE geometry, laid out in the
surface's own coordinates and projected with it.

So every routine here works in the SURFACE's local coordinates and takes a
`proj(lx, lz) -> screen point` callback, exactly as `_draw_neon_word` does.
Turn the board and the words turn with it; tip it edge-on and they vanish
with it, because they are on it.

**Strokes, not outlines.** A glyph is a list of polylines through a unit box
(u 0..1 left to right, v 0..1 bottom to top), and each polyline is thickened
into ONE filled polygon by offsetting it (`_offset`). One polygon per stroke
rather than one per segment is both cheaper and cleaner: the joins fall out
of the offset instead of needing a patch drawn over every corner.
"""
import math
import random


# The painted alphabet. Each glyph is a list of STROKES; each stroke a list
# of (u, v) points in a unit box, v=0 at the baseline. Kept as strokes rather
# than filled outlines so one `weight` sets the whole sign's brush.
GLYPH = {
    " ": [],
    "A": [[(0.06, 0.0), (0.5, 1.0), (0.94, 0.0)], [(0.24, 0.34), (0.76, 0.34)]],
    "B": [[(0.16, 0.0), (0.16, 1.0)],
          [(0.16, 1.0), (0.64, 1.0), (0.84, 0.86), (0.84, 0.68),
           (0.64, 0.52), (0.16, 0.52)],
          [(0.16, 0.52), (0.70, 0.52), (0.90, 0.36), (0.90, 0.16),
           (0.70, 0.0), (0.16, 0.0)]],
    "C": [[(0.90, 0.82), (0.62, 1.0), (0.32, 1.0), (0.10, 0.78),
           (0.10, 0.22), (0.32, 0.0), (0.62, 0.0), (0.90, 0.18)]],
    "D": [[(0.16, 0.0), (0.16, 1.0), (0.58, 1.0), (0.86, 0.74),
           (0.86, 0.26), (0.58, 0.0), (0.16, 0.0)]],
    "E": [[(0.88, 1.0), (0.16, 1.0), (0.16, 0.0), (0.88, 0.0)],
          [(0.16, 0.5), (0.68, 0.5)]],
    "F": [[(0.88, 1.0), (0.16, 1.0), (0.16, 0.0)], [(0.16, 0.52), (0.68, 0.52)]],
    "G": [[(0.90, 0.82), (0.62, 1.0), (0.32, 1.0), (0.10, 0.78),
           (0.10, 0.22), (0.32, 0.0), (0.62, 0.0), (0.90, 0.18),
           (0.90, 0.44), (0.58, 0.44)]],
    "H": [[(0.16, 0.0), (0.16, 1.0)], [(0.84, 0.0), (0.84, 1.0)],
          [(0.16, 0.5), (0.84, 0.5)]],
    "I": [[(0.5, 0.0), (0.5, 1.0)], [(0.24, 1.0), (0.76, 1.0)],
          [(0.24, 0.0), (0.76, 0.0)]],
    "J": [[(0.74, 1.0), (0.74, 0.22), (0.54, 0.0), (0.28, 0.0), (0.12, 0.18)]],
    "K": [[(0.18, 0.0), (0.18, 1.0)], [(0.86, 1.0), (0.18, 0.44)],
          [(0.42, 0.60), (0.88, 0.0)]],
    "L": [[(0.20, 1.0), (0.20, 0.0), (0.86, 0.0)]],
    "M": [[(0.10, 0.0), (0.10, 1.0), (0.5, 0.40), (0.90, 1.0), (0.90, 0.0)]],
    "N": [[(0.16, 0.0), (0.16, 1.0), (0.84, 0.0), (0.84, 1.0)]],
    "O": [[(0.5, 1.0), (0.16, 0.80), (0.16, 0.20), (0.5, 0.0),
           (0.84, 0.20), (0.84, 0.80), (0.5, 1.0)]],
    "P": [[(0.18, 0.0), (0.18, 1.0), (0.66, 1.0), (0.86, 0.84),
           (0.86, 0.64), (0.66, 0.48), (0.18, 0.48)]],
    "Q": [[(0.5, 1.0), (0.16, 0.80), (0.16, 0.20), (0.5, 0.0),
           (0.84, 0.20), (0.84, 0.80), (0.5, 1.0)],
          [(0.58, 0.24), (0.90, 0.0)]],
    "R": [[(0.18, 0.0), (0.18, 1.0), (0.66, 1.0), (0.86, 0.84),
           (0.86, 0.66), (0.66, 0.50), (0.18, 0.50)],
          [(0.52, 0.50), (0.88, 0.0)]],
    "S": [[(0.88, 0.84), (0.62, 1.0), (0.30, 1.0), (0.12, 0.84),
           (0.12, 0.66), (0.30, 0.52), (0.68, 0.48), (0.88, 0.32),
           (0.88, 0.16), (0.68, 0.0), (0.32, 0.0), (0.10, 0.16)]],
    "T": [[(0.5, 0.0), (0.5, 1.0)], [(0.08, 1.0), (0.92, 1.0)]],
    "U": [[(0.16, 1.0), (0.16, 0.22), (0.36, 0.0), (0.64, 0.0),
           (0.84, 0.22), (0.84, 1.0)]],
    "V": [[(0.08, 1.0), (0.5, 0.0), (0.92, 1.0)]],
    "W": [[(0.04, 1.0), (0.26, 0.0), (0.5, 0.60), (0.74, 0.0), (0.96, 1.0)]],
    "X": [[(0.12, 1.0), (0.88, 0.0)], [(0.88, 1.0), (0.12, 0.0)]],
    "Y": [[(0.10, 1.0), (0.5, 0.48)], [(0.90, 1.0), (0.5, 0.48)],
          [(0.5, 0.48), (0.5, 0.0)]],
    "Z": [[(0.12, 1.0), (0.88, 1.0), (0.12, 0.0), (0.88, 0.0)]],
    "0": [[(0.5, 1.0), (0.18, 0.80), (0.18, 0.20), (0.5, 0.0),
           (0.82, 0.20), (0.82, 0.80), (0.5, 1.0)]],
    "1": [[(0.26, 0.78), (0.52, 1.0), (0.52, 0.0)], [(0.22, 0.0), (0.82, 0.0)]],
    "2": [[(0.14, 0.82), (0.34, 1.0), (0.66, 1.0), (0.86, 0.82),
           (0.86, 0.64), (0.14, 0.0), (0.88, 0.0)]],
    "3": [[(0.14, 0.86), (0.36, 1.0), (0.68, 1.0), (0.86, 0.84),
           (0.86, 0.68), (0.60, 0.54), (0.86, 0.38), (0.86, 0.16),
           (0.66, 0.0), (0.34, 0.0), (0.12, 0.14)]],
    "4": [[(0.70, 0.0), (0.70, 1.0), (0.12, 0.30), (0.90, 0.30)]],
    "5": [[(0.86, 1.0), (0.22, 1.0), (0.18, 0.58), (0.60, 0.62),
           (0.86, 0.44), (0.86, 0.18), (0.62, 0.0), (0.30, 0.0), (0.12, 0.14)]],
    "6": [[(0.82, 0.90), (0.56, 1.0), (0.28, 0.86), (0.16, 0.46),
           (0.16, 0.18), (0.42, 0.0), (0.66, 0.0), (0.86, 0.18),
           (0.86, 0.36), (0.66, 0.54), (0.36, 0.54), (0.16, 0.42)]],
    "7": [[(0.12, 1.0), (0.88, 1.0), (0.42, 0.0)]],
    "8": [[(0.5, 0.54), (0.24, 0.68), (0.24, 0.86), (0.5, 1.0),
           (0.76, 0.86), (0.76, 0.68), (0.5, 0.54), (0.20, 0.36),
           (0.20, 0.16), (0.5, 0.0), (0.80, 0.16), (0.80, 0.36), (0.5, 0.54)]],
    "9": [[(0.18, 0.10), (0.44, 0.0), (0.72, 0.14), (0.84, 0.54),
           (0.84, 0.82), (0.58, 1.0), (0.34, 1.0), (0.14, 0.82),
           (0.14, 0.64), (0.34, 0.46), (0.64, 0.46), (0.84, 0.58)]],
    ".": [[(0.46, 0.03), (0.54, 0.03)]],
    "'": [[(0.52, 1.0), (0.44, 0.72)]],
    # An ampersand drawn as one continuous stroke came out as a knot at any
    # size the sign actually gets read at. Nothing in the world uses one
    # today, but a missing glyph is skipped SILENTLY, so leaving it out would
    # quietly drop a character from some future board -- it keeps a simple,
    # legible form instead.
    "&": [[(0.88, 0.0), (0.22, 0.66), (0.22, 0.86), (0.40, 1.0),
           (0.58, 0.86), (0.58, 0.68), (0.14, 0.26), (0.14, 0.12),
           (0.34, 0.0), (0.56, 0.08), (0.72, 0.34)]],
}

# How much width each glyph claims, relative to a full cell. The neon
# alphabet gives every character an equal cell, which is fine for a five
# letter store name and wrong for a sentence: "NORTHERNMOST" set on equal
# cells puts a lake of air either side of every I.
ADVANCE = {" ": 0.55, "I": 0.60, ".": 0.34, "'": 0.32,
           "M": 1.12, "W": 1.14, "1": 0.62}


def _offset(pts, w):
    """A polyline thickened into one closed polygon of width `w`.

    Each vertex is pushed out along the MITRE of its adjoining segments, so
    corners close themselves and a stroke needs a single filled polygon
    instead of a quad per segment plus a patch over every joint.

    The mitre has to be LENGTHENED at a sharp corner (by 1/cos of the half
    angle), or the outside of the turn falls short of where the two edges
    would actually meet and the corner reads as clipped off. Averaging the
    normals without that term is the obvious way to write this and it visibly
    bit the apex off every A, V, W and Y. Clamped, because the exact term
    goes to infinity as a stroke doubles back on itself.
    """
    n = len(pts)
    if n < 2:
        return None
    half = w * 0.5
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        if i == 0:
            dx, dz = pts[1][0] - x, pts[1][1] - z
            ln = math.hypot(dx, dz) or 1.0
            nx, nz, ext = -dz / ln, dx / ln, 1.0
        elif i == n - 1:
            dx, dz = x - pts[i - 1][0], z - pts[i - 1][1]
            ln = math.hypot(dx, dz) or 1.0
            nx, nz, ext = -dz / ln, dx / ln, 1.0
        else:
            ax, az = x - pts[i - 1][0], z - pts[i - 1][1]
            bx, bz = pts[i + 1][0] - x, pts[i + 1][1] - z
            la = math.hypot(ax, az) or 1.0
            lb = math.hypot(bx, bz) or 1.0
            anx, anz = -az / la, ax / la          # the two segment normals
            bnx, bnz = -bz / lb, bx / lb
            mx, mz = anx + bnx, anz + bnz
            ml = math.hypot(mx, mz)
            if ml < 1e-6:                          # a full reversal
                nx, nz, ext = anx, anz, 1.0
            else:
                nx, nz = mx / ml, mz / ml
                # A MITRE LIMIT, or a sharp apex grows a spike instead of a
                # point: the A, M, V, W and 4 all sprouted one several times
                # the brush width out of the top of the letter. Capping the
                # extension bevels the sharpest corners into the small flat a
                # signwriter's brush leaves anyway. The floor cannot go below
                # about 1.42 or square corners (L, E, T) start rounding off.
                ext = min(1.5, 1.0 / max(0.2, nx * anx + nz * anz))
        left.append((x + nx * half * ext, z + nz * half * ext))
        right.append((x - nx * half * ext, z - nz * half * ext))
    return left + right[::-1]


def layout(text):
    """The advance width of `text` in cells, and each glyph's (start, width).

    Split out from the draw so a caller can SIZE a word before committing to
    it -- fitting three lines of different lengths onto one board means
    knowing how wide each will run.
    """
    cells = []
    at = 0.0
    for ch in text:
        w = ADVANCE.get(ch.upper(), 1.0)
        cells.append((at, w))
        at += w
    return at, cells


def paint_word(surf, proj, text, x0, x1, zb, zt, col, wear=None,
               weight=0.16, seed=0, align="center"):
    """Spell `text` in painted strokes between local x0..x1 and zb..zt.

    `proj(lx, lz) -> (sx, sy)` maps the SURFACE's own coordinates to the
    screen, so the caller decides which plane the paint lies in and the
    letters foreshorten, skew and go edge-on with it.

    `weight` is the brush width as a fraction of cap height. `wear` is the
    colour showing through where the paint has failed; passing None leaves
    the lettering fresh (a sign nobody has had to repaint).
    """
    import pygame
    if not text:
        return
    total, cells = layout(text)
    if total <= 0:
        return
    cap = zt - zb
    span = x1 - x0
    # WHICH WAY IS LEFT TO RIGHT? Ask the projection, never assume.
    #
    # A surface's local +x can run either way across the screen depending on
    # which of its faces is toward the viewer -- for a face whose outward
    # normal is -y, +x runs LEFT, so a word laid out in increasing x comes out
    # as a perfect mirror image. The town board shipped exactly that on the
    # first look pass and read "YELMIRB", which is the same class of failure
    # as the mirror-reversed neon sign in VISION.md.
    #
    # Probing two points and mirroring the whole word about the band's centre
    # fixes letter ORDER and letter SHAPE in one move, and it fixes them for
    # any plane on any prop at any camera angle. That is worth more than a
    # rule written down somewhere: a caller cannot get this wrong, because a
    # caller no longer decides it.
    zmid = (zb + zt) * 0.5
    if proj(x1, zmid)[0] < proj(x0, zmid)[0]:
        _fwd, _mid2 = proj, x0 + x1
        def proj(lx, lz):                                  # noqa: F811
            return _fwd(_mid2 - lx, lz)
    # A short line is set at its natural size and CENTRED rather than
    # stretched to the full width: letters that grow to fill the board give
    # the game away as generated, and a hand-lettered sign centres its lines.
    per = span / total
    natural = cap * 0.72                    # a cell about 3/4 the cap height
    if per > natural:
        per = natural
    used = per * total
    if align == "center":
        x0 = x0 + (span - used) * 0.5
    tw = cap * weight
    rng = random.Random(seed ^ (len(text) * 7919))
    for i, ch in enumerate(text):
        strokes = GLYPH.get(ch.upper())
        if not strokes:
            continue
        at, cw = cells[i]
        gx = x0 + at * per
        gw = cw * per
        # the glyph's unit box, inset so neighbouring letters do not touch
        pad = gw * 0.10
        bx0, bxw = gx + pad, max(0.001, gw - pad * 2)
        for stroke in strokes:
            pts = [(bx0 + u * bxw, zb + v * cap) for (u, v) in stroke]
            poly = _offset(pts, tw)
            if poly is None:
                continue
            pygame.draw.polygon(surf, col, [proj(px, pz) for px, pz in poly])
        if wear is None:
            continue
        # WEAR: chips of the board showing through where the paint has let
        # go. Weathering a sign by fading its colour only makes it look
        # further away; paint fails in FLAKES.
        #
        # A flake bites the EDGE of a stroke, so each chip is pushed out
        # perpendicular to the stroke it eats and kept well under the brush
        # width. The first cut centred them on the stroke at up to 0.85 of
        # that width, which punched clean holes through the middle of every
        # letter: at sign size the lower two lines stopped reading as
        # lettering at all and read as mould. Age has to stay quieter than
        # the thing it is ageing.
        for stroke in strokes:
            if len(stroke) < 2 or rng.random() > 0.5:
                continue
            k = rng.randrange(len(stroke) - 1)
            (u0, v0), (u1, v1) = stroke[k], stroke[k + 1]
            f = rng.uniform(0.2, 0.8)
            cu, cv = u0 + (u1 - u0) * f, v0 + (v1 - v0) * f
            px, pz = bx0 + cu * bxw, zb + cv * cap
            # out along the stroke's own normal, in board units
            dx = (u1 - u0) * bxw
            dz = (v1 - v0) * cap
            dl = math.hypot(dx, dz) or 1.0
            side = 1.0 if rng.random() < 0.5 else -1.0
            px += -dz / dl * tw * 0.44 * side
            pz += dx / dl * tw * 0.44 * side
            r = tw * rng.uniform(0.16, 0.34)
            pygame.draw.polygon(surf, wear, [
                proj(px - r, pz - r * 0.6), proj(px + r * 0.7, pz - r),
                proj(px + r, pz + r * 0.7), proj(px - r * 0.6, pz + r)])
