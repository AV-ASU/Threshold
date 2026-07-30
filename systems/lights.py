"""THE LIGHT TABLE -- one row per light-emitting kind, read by every layer.

A fixture used to be declared in THREE places that could disagree: its
mechanical pool radius (`Scene._LIGHT_KINDS`), its visible pool
(`FIXTURE_POOLS` in the draw layer), and whether a blackout kills it
(`Scene._ELECTRIC_KINDS`). Nothing tied them together, so a kind could gate
without shining or shine without gating -- and both shipped: `campfire` (the
COLD scorch decal) handed out 80px of stealth cover while casting nothing, and
`burn_barrel` cast a visible pool while giving no cover at all. A conventions
check existed only to catch that drift.

One row fixes it by construction: you cannot add half a light. The three old
names are DERIVED from this table and still exist, so every call site is
unchanged (`Scene._LIGHT_KINDS`, `Scene._ELECTRIC_KINDS`, `FIXTURE_POOLS`).

**`gate` and `pool` are deliberately allowed to differ** and that is the one
thing this table must keep expressible. A bare bulb floods its room visibly
(`drop_bulb` pool 108) while its stealth-cover radius stays tight (gate 58), so
what the player can hide behind does not swell with the glow. Divergence is a
DECISION here, not an accident of two tables.

Fields:
    gate   mechanical pool radius in px -- what `Scene.lit_at` answers, so the
           Watcher spawn/burn gate, the storm's step refusal and the
           lost-space mouth all read it.
    pool   visible pool radius in px -- what `_draw_dark` casts.
    color  the pool's RGB.
    peak   pool brightness at the centre.
    src_z  the source's real world HEIGHT (the pool is a tilt-squashed
           ellipse cast on the floor UNDER the 3D source).
    arm    the gooseneck offset from the mount.
    amp    flicker amplitude.
    spd    flicker speed.
    elec   True if the genset powers it -- it dies in a blackout in all
           layers at once. Fire keeps burning.

`campfire` is deliberately ABSENT: it is the COLD indoor scorch decal ("long
dead but for one last dull ember"). The lit ground fire is `camp_fire`.
"""

LIGHTS = {
    # ---- fire (never electric; burns through a blackout) ----------------
    "wall_torch":    dict(gate=90.0,  pool=102, color=(255, 168, 78),
                          peak=74,  src_z=24, arm=0,  amp=0.18, spd=7.0),
    "brazier":       dict(gate=90.0,  pool=106, color=(255, 150, 56),
                          peak=76,  src_z=12, arm=0,  amp=0.16, spd=6.0),
    "camp_fire":     dict(gate=88.0,  pool=106, color=(255, 158, 60),
                          peak=76,  src_z=4,  arm=0,  amp=0.18, spd=5.0),
    "burn_barrel":   dict(gate=80.0,  pool=94,  color=(255, 150, 56),
                          peak=68,  src_z=16, arm=0,  amp=0.16, spd=6.0),
    # the lost-space CROP-CIRCLE bonfire: a wide, high-peak warm pool filling
    # the whole grass clearing inside the corn ring. Bigger than a cult
    # camp_fire on purpose -- the lit haven you fall into, not a campsite.
    "haven_fire":    dict(gate=200.0, pool=250, color=(255, 156, 58),
                          peak=112, src_z=6,  arm=0,  amp=0.16, spd=4.5),
    "lantern":       dict(gate=60.0,  pool=70,  color=(255, 176, 84),
                          peak=58,  src_z=20, arm=0,  amp=0.10, spd=3.0),
    "candle":        dict(gate=55.0,  pool=44,  color=(255, 178, 92),
                          peak=46,  src_z=6,  arm=0,  amp=0.14, spd=9.0),
    # the brass oil lamp burns a real flame everywhere it is drawn, so it
    # emits everywhere too -- a small WARM accent pool, never a room's light.
    "kerosene_lamp": dict(gate=40.0,  pool=48,  color=(255, 186, 96),
                          peak=44,  src_z=14, arm=0,  amp=0.12, spd=8.0),
    "generator":     dict(gate=42.0,  pool=50,  color=(255, 212, 152),
                          peak=44,  src_z=8,  arm=0,  amp=0.08, spd=5.0),

    # ---- COLD electric (dies with the genset) ---------------------------
    # No warm-lamp cosiness indoors: the civic light is cold blue-white (the
    # "LED" read, delivered in 1994 by fluorescent tube / cold bulb) with a
    # fast shallow shimmer instead of a candle flicker. Fire is a PROP now,
    # never the room's light.
    "wall_lamp":     dict(gate=62.0,  pool=88,  color=(205, 218, 240),
                          peak=62,  src_z=20, arm=3,  amp=0.05, spd=13.0,
                          elec=True),
    # a bare bulb on a drop cord, the ceiling workhorse. The VISIBLE pool is
    # wide (a bare bulb floods its room); the GATE stays tight, so stealth
    # cover does not move with the glow.
    "drop_bulb":     dict(gate=58.0,  pool=108, color=(205, 218, 240),
                          peak=56,  src_z=30, arm=0,  amp=0.06, spd=11.0,
                          elec=True),
    "yard_light":    dict(gate=85.0,  pool=120, color=(200, 222, 255),
                          peak=60,  src_z=44, arm=9,  amp=0.05, spd=2.0,
                          elec=True),
    # the SAFE PATH's highway lamp (DESIGN.md §14): the same cold head as the
    # yard light, up a tall mast with a long gooseneck, throwing far enough
    # that poles every few tiles keep the WHOLE carriageway inside a pool --
    # which is the mechanism, not the mood (an unlit stretch of safe path is
    # a stretch you can fall out of the world on).
    "street_lamp":   dict(gate=150.0, pool=196, color=(200, 222, 255),
                          peak=72,  src_z=78, arm=26, amp=0.04, spd=2.0,
                          elec=True),
    # the derelict station's NEON PYLON: a saturated cold sign-glow (a SIGN
    # is allowed colour where room-light is not), thrown from high on its
    # pole so the pool floods the whole lot you land on. It runs off the
    # station's own dead grid, so it is NOT on the town genset.
    "neon_pylon":    dict(gate=190.0, pool=280, color=(255, 226, 168),
                          peak=104, src_z=96, arm=0,  amp=0.06, spd=15.0),
}

# ---- the three derived views the rest of the code already asks for -------
# Keeping the old names means every call site is unchanged; what is gone is
# the possibility of them disagreeing.

LIGHT_GATE_RADII = {k: v["gate"] for k, v in LIGHTS.items()}

ELECTRIC_KINDS = frozenset(k for k, v in LIGHTS.items() if v.get("elec"))

#: kind -> (radius, color, peak, src_z, arm, flicker_amp, flicker_speed)
FIXTURE_POOLS = {
    k: (v["pool"], v["color"], v["peak"], v["src_z"], v["arm"],
        v["amp"], v["spd"])
    for k, v in LIGHTS.items()
}
