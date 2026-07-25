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

# A NOTE ON HOW LIGHT THESE MAY BE. `lift` is added on TOP of the role
# factor, so an upward face lands at roughly (1 + lift) x base -- and under a
# 55-degree camera most of what you see of a low prop IS its top. Several
# materials were first set by eye on the preview sheet's neutral grey card,
# where a value looks reasonable that turns out to be the palest thing in a
# Darkwood-dark yard. Judge a new material in a SCENE, in the dark
# (`tools/inspect_spot.py --dark`), not on the contact sheet.
#            base RGB            lift  what it is
MATERIALS = {
    "cedar":      ((86, 68, 46), 0.34),   # weathered post + rail timber
    "plank":      ((80, 66, 48), 0.22),   # sawn boards, decking, a stoop
    "log_bark":   ((78, 60, 40), 0.38),   # split firewood, round side
    "log_cut":    ((104, 88, 66), 0.16),  # a sawn end, pale against bark
    "tin":        ((80, 82, 88), 0.30),   # galvanised sheet, a mailbox
    "steel":      ((96, 98, 106), 0.26),  # poles, masts, hardware
    "concrete":   ((64, 62, 59), 0.22),   # footings, a poured stoop
    "flag_red":   ((150, 62, 48), 0.22),  # the mailbox signal flag
    "paper":      ((105, 102, 92), 0.14),  # mail, a pinned notice
    "rust":       ((78, 54, 40), 0.28),   # what the town's metal is now
    "iron":       ((54, 54, 62), 0.30),   # black ironwork: a lamp post, a rail
    "wire":       ((62, 56, 48), 0.18),   # fence strand: weathered, NOT bright
    "farm_green": ((72, 80, 64), 0.26),   # faded paint on a working truck
    "glass":      ((46, 58, 60), 0.20),   # unlit panes, a windshield
    # PAINTED SIGNAGE, mid-century roadside. The town's welcome sign is the
    # one object in Brimley allowed to be BRIGHT: a 1960s googie board of the
    # Welcome-to-Fabulous-Las-Vegas family, built when the town still thought
    # it had a future, and now the only colour left on the road. Everything
    # else in this table is a near-black Darkwood surface; these are not, and
    # that contrast IS the read.
    #
    # `lift` stays near zero across the set. These are painted faces on a
    # VERTICAL board -- they do not catch the sky the way bare timber does,
    # and lifting them blew the panel out into a white slab under the 55
    # degree camera, where most of a low prop is its top.
    "sign_field": ((214, 206, 186), 0.03),   # the cream panel
    "sign_paint": ((38, 42, 60), 0.02),      # the lettering, near-black ink
    "sign_accent": ((176, 58, 52), 0.03),    # the coral banner + frame
    "sign_accent_ink": ((238, 230, 208), 0.02),  # cream lettering ON the coral
    "sign_star": ((228, 176, 54), 0.04),     # the atomic starburst, warm yellow
    "sign_steel": ((92, 96, 104), 0.16),     # the splayed legs
    # A LIT pane is not glass with a bright colour, it is a surface that
    # already carries its own light: `lift` near zero keeps the flame from
    # shading darker on the faces that turn away, so the head glows evenly
    # instead of having a dim side.
    "flame_glass": ((255, 186, 108), 0.02),
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
