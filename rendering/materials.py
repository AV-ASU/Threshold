"""MATERIALS -- the one place a prop's colours come from.

Every prop used to invent its own RGB triples inline. That is why things did
not sit together: two props meant to be the same weathered cedar were two
different browns, and nothing shared a rule for how much darker a side is
than a top. Naming them once fixes the palette AND the shading model at the
same time.

A material is `(base, lift, name)`: `base` is the colour of a face pointing
straight at the viewer, and `lift` is how much a fully upward face brightens.
Faces in between interpolate, so a curved surface gets a smooth crown-to-belly
gradient for free -- which is what makes a cylinder read as round rather than
as a stack of flat strips.

The palette is Darkwood-dark on purpose (`VISION.md`): these are near-black
woods and metals lit by a weak sky, not saturated colour. Add a material
here rather than passing a colour into a prop.
"""

#            base RGB            lift  what it is
MATERIALS = {
    "cedar":      ((86, 68, 46), 0.34),   # weathered post + rail timber
    "plank":      ((96, 78, 56), 0.30),   # sawn boards, decking, a stoop
    "log_bark":   ((78, 60, 40), 0.38),   # split firewood, round side
    "log_cut":    ((150, 126, 92), 0.16),  # a sawn end, pale against bark
    "tin":        ((104, 106, 112), 0.30),  # galvanised sheet, a mailbox
    "steel":      ((96, 98, 106), 0.26),  # poles, masts, hardware
    "concrete":   ((84, 82, 78), 0.24),   # footings, a poured stoop
    "flag_red":   ((150, 62, 48), 0.22),  # the mailbox signal flag
    "paper":      ((150, 146, 132), 0.14),  # mail, a pinned notice
    "rust":       ((92, 62, 44), 0.28),   # what the town's metal is now
    "wood":       ((88, 70, 50), 0.32),   # generic fallback
}

# How much darker each face role sits before the upward lift is added. A
# top catches the sky, a side turns away from it, an end (a cut across a
# length) is flatter still, and an under-face is almost black.
ROLE_SHADE = {
    "top": 1.00,
    "side": 0.78,
    "end": 0.88,
    "under": 0.42,
}


def shade_for(mat, role, nz, toward, tint=None):
    """The colour for one face: material, role, and how far UP it faces.

    `nz` is the face normal's vertical component and `toward` how squarely it
    meets the viewer. Both feed in, so a cylinder's crown is lighter than its
    belly and a face turning away darkens as it goes -- the gradient is what
    reads as curvature."""
    base, lift = MATERIALS.get(mat, MATERIALS["wood"])
    f = ROLE_SHADE.get(role, 0.8)
    f *= 0.86 + 0.14 * min(1.0, max(0.0, toward))
    f += lift * max(0.0, nz)
    r, g, b = base
    if tint:
        r, g, b = r + tint[0], g + tint[1], b + tint[2]
    return (max(0, min(255, int(r * f))),
            max(0, min(255, int(g * f))),
            max(0, min(255, int(b * f))))
