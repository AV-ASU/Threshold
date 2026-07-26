"""THE ASSEMBLED PROPS -- declared as parts, checked against a reference.

Each entry here is DATA (`rendering/assembly.Assembly`), not a draw function,
and each is built to the proportions recorded in `rendering/references.py`.
The two together are the whole point of the rework: a shape you can check
against a fact, made of parts that cannot get culling or draw order wrong.

Units are the game's world units, where a wall rises to about 26 and the
player is roughly 20 tall. Each builder converts the reference's real inches
into those units through one `k` factor, so the RATIO comes from the
reference and only the overall size is a scene decision -- which is exactly
the split that kept going wrong when both were eyeballed together.
"""
import inspect
import math

from rendering import prim
from rendering.assembly import Assembly, Part


def _k(real, target_len):
    """World units per inch, from a reference length and the size we want."""
    return target_len / real[0]


# --------------------------------------------------------------- mailbox
# Reference: Joroleman 1915. A TUNNEL -- arched top, flat front, back and
# bottom -- on a post, flag on the flank. 23.2 x 11 x 13.4in, box floor
# 41-45in up. The version this replaces was a rectangular prism at 1.76 : 1
# : 1.06 against a real 2.11 : 1 : 1.22, which is why it read as a grey
# lozenge on a stick: the arch IS the silhouette.
def _mailbox(full=False):
    real = (23.2, 11.0, 13.4)
    k = _k(real, 13.0)                 # 13 world units long
    w, d = real[0] * k, real[1] * k
    springing = d * 0.42               # the flat sides stop, the vault starts
    rise = real[2] * k - springing
    # THE MOUNT HEIGHT IS IN WORLD UNITS, NOT THE MODEL'S.
    # A prop is drawn a little larger than life so it reads at play zoom, and
    # `k` carries that exaggeration. Deriving the post from `k` applies the
    # exaggeration a SECOND time: at the reference's "post is about 3x the
    # box's own height" this put the box floor at z 27 -- above a WALL, over
    # the head of a 20-tall player -- and from three of four facings the
    # mailbox read as a flat bar on a stick, because the box was too high to
    # see into. Anything that says where a prop sits in the WORLD (a mount, a
    # sill, a tabletop) is measured in world units.
    post_h = 12.5                      # box floor at chest height
    parts = [
        Part(prim.cyl(r=1.15, length=post_h, axis="z"),
             mat="cedar", name="post"),
        Part(prim.arch(w, d, springing, rise=rise),
             at=(0, 0, post_h - 1.0), mat="tin", name="box"),
        # the signal flag, on the FLANK near the door end
        Part(prim.box(0.7, 0.7, 6.0),
             at=(w * 0.26, d * 0.52, post_h + springing * 0.2),
             mat="flag_red", name="flagpost"),
        Part(prim.plate(3.2, 0.4, 2.6),
             at=(w * 0.26 + 1.4, d * 0.52, post_h + springing * 0.2 + 4.0),
             mat="flag_red", name="flag"),
    ]
    if full:
        # NOBODY HAS EMPTIED IT. The mail has to JUT OUT PAST the door end --
        # letters modelled inside the box are geometrically correct and
        # completely invisible, which is what the first cut of this did.
        # The door is the +x end (the flag sits beside it), so the wad
        # straddles x = w/2 and hangs out into open air.
        for i, (out, dy, dz, ang) in enumerate(((0.30, -0.7, 0.26, 0.13),
                                                (0.46, 0.6, 0.50, -0.19),
                                                (0.22, -0.1, 0.72, 0.05))):
            parts.append(Part(
                prim.plate(w * 0.44, d * 0.66, 0.6),
                at=(w * 0.5 + w * out * 0.5, dy,
                    post_h - 1.0 + springing * dz),
                yaw=ang, mat="paper", name=f"mail{i}"))
    return Assembly(*parts)


# ------------------------------------------------------------------ stoop
# Reference: a stoop is the LANDING at the door with steps coming off it.
# The first model was two treads and no landing, which is a flight of steps,
# and it read as slabs lying on grass however correct its rise-to-run was --
# so it was remade rather than shipped with a caveat (VISION, "if it isn't
# good, remake it now"). Side cheeks close the step ends; the nosing shadow
# is what reads as a step at distance.
def _stoop(steps=3):
    rise_in, run_in, wide_in, landing_in = 7.0, 11.0, 60.0, 36.0
    k = 24.0 / wide_in                 # 24 world units wide
    rise, run = rise_in * k, run_in * k
    wide, landing = wide_in * k, landing_in * k
    parts = []
    # THE LANDING: the platform at the door, the thing that makes it a stoop
    top = steps * rise
    parts.append(Part(prim.box(landing, wide, rise * 0.9, z0=top - rise * 0.9),
                      at=(landing / 2 + (steps - 1) * run, 0, 0),
                      mat="plank", name="landing"))
    parts.append(Part(prim.box(landing, wide, top - rise * 0.9),
                      at=(landing / 2 + (steps - 1) * run, 0, 0),
                      mat="concrete", name="landing_base"))
    # THE STEPS, coming down off it toward -x
    for i in range(steps):
        back = i * run
        parts.append(Part(prim.box(run, wide, (i + 1) * rise),
                          at=(back, 0, 0), mat="concrete", name=f"riser{i}"))
        nb = 2
        bw = wide / nb
        for b in range(nb):
            parts.append(Part(
                prim.box(run + rise * 0.34, bw * 0.94, rise * 0.28,
                         z0=(i + 1) * rise - rise * 0.28),
                at=(back - rise * 0.17, (b - (nb - 1) / 2.0) * bw, 0),
                mat="plank", name=f"tread{i}_{b}"))
    # SIDE CHEEKS: the boards closing the step ends, so the treads never
    # float. Without them a flight reads as loose slabs from the side.
    for sgn in (-1, 1):
        parts.append(Part(
            prim.wedge(steps * run, 1.4, steps * rise),
            at=((steps - 1) * run / 2 + run / 2, sgn * (wide / 2 + 0.5), 0),
            yaw=math.pi, mat="plank", name=f"cheek{sgn}"))
    return Assembly(*parts)


# --------------------------------------------------------------- woodpile
# Reference: it is LOGS. The separate pieces and the ragged ends are the
# entire read; every attempt to imply them from one mass failed.
def _woodpile(rows=5, seed=7, axe=False):
    # THE AXES WERE WRONG BEFORE. A stack runs ALONG a wall with the log ends
    # facing out, so a log lies ACROSS the stack: the log axis is the stack's
    # DEPTH (+y, one log long), and the stack extends along +x and up. The
    # old model laid the logs along +x, which made a short chunky raft
    # instead of a wall of ends, and the proportion check caught it at
    # 1.28 : 1 : 1.08 against a real 3.00 : 1 : 1.88.
    # SIZED AGAINST THE PLAYER (20 tall). At LOG 5.0 over six rows the stack
    # stood 27 units -- taller than the player and taller than a wall, which
    # is a barricade, not next winter's firewood. A stack you could rest a
    # hand on is the read.
    LOG = 3.4                          # a split log's diameter
    DEEP = 6.3                         # one log's length -> the stack's depth
    ncol = 6                           # logs along the wall
    parts = []
    for row in range(rows):
        stagger = (row % 2) * (LOG * 0.5)
        for c in range(ncol):
            h = (seed + row * 31 + c * 17)
            x = (c - (ncol - 1) / 2.0) * LOG * 0.98 + stagger
            if abs(x) > (ncol * LOG) / 2.0:
                continue
            ln = DEEP * (0.88 + ((h >> 2) % 5) * 0.05)
            # how far each log is shoved in or out of the face. Kept small:
            # the jitter counts into the stack's DEPTH, and at +/-1.65 it
            # padded W enough on its own to fail the recorded 3.00 : 1 : 1.88.
            shove = (((h >> 5) % 7) - 3) * 0.24
            z = row * LOG * 0.90 + LOG / 2
            parts.append(Part(prim.cyl(r=LOG * 0.47, length=ln, axis="x"),
                              at=(x, shove, z), yaw=math.pi / 2,
                              mat="log_bark", name=f"log{row}_{c}"))
    if axe:
        # THE INTERRUPTED TASK: the chopping block at the end of the stack
        # with the axe still standing in it. The pale sawn top of the block
        # and the haft leaning out of the silhouette are what carry it; a
        # neat stack alone reads as finished work.
        bx = -(ncol * LOG) / 2.0 - LOG * 2.2
        blk_h = LOG * 2.6
        parts.append(Part(prim.cyl(r=LOG * 1.15, length=blk_h, axis="z",
                                   segs=9),
                          at=(bx, 0, 0), mat="log_cut", name="block"))
        # the haft, driven in off-vertical -- an axe stood straight up reads
        # as a fencepost
        parts.append(Part(prim.box(1.15, 1.15, LOG * 3.4),
                          at=(bx + LOG * 0.55, 0, blk_h - LOG * 0.4),
                          yaw=0.30, mat="cedar", name="haft"))
        # THE HEAD IS A VOLUME. Built as a 0.7-deep plate it was a sliver
        # that disappeared at three of four headings -- a real axe head is
        # thin, but a thin thing seen edge-on is nothing, and the tilt only
        # ever shows this one from four ways. Thick enough to hold a lit
        # face, and it sits ABOVE the block against open air rather than
        # against the stack behind it.
        parts.append(Part(prim.box(LOG * 1.5, LOG * 0.62, LOG * 0.95),
                          at=(bx + LOG * 1.05, 0, blk_h + LOG * 2.5),
                          yaw=0.30, mat="steel", name="axe_head"))
        parts.append(Part(prim.wedge(LOG * 0.9, LOG * 0.58, LOG * 0.9),
                          at=(bx + LOG * 1.95, 0, blk_h + LOG * 2.5),
                          yaw=0.30, mat="steel", name="axe_bit"))
    return Assembly(*parts)


# ------------------------------------------------------------- yard fence
# Reference: split cedar posts, two or three SAGGING wire strands. One bay.
# ------------------------------------------------------------- yard gate
# A GATE IS NOT A GAP. The `gap` bay below is the MOUTH -- snapped wire and a
# shoved-over post, a boundary you push THROUGH -- and it belongs where the
# world lets go of you (DESIGN.md §13). Using it as a household's front
# entrance says the opposite of what a kept yard is saying with everything
# else it has: you do not walk into somebody's lot through their broken
# fence. So the way in that a household USES is a hung leaf, and the two are
# different objects with different meanings.
#
# The DIAGONAL BRACE is the tell. It runs UP from the hinge corner, which is
# the direction that carries the leaf's weight; drawn the other way (or left
# off) the leaf reads as a ladder lying against the posts.
def _yard_gate(bay=33.0, seed=5, swing=0.0):
    real = (120.0, 3.5, 44.0)
    LEAF = bay * 0.86
    k = LEAF / real[0]
    THICK, TALL = real[1] * k, real[2] * k
    HANG = bay * 0.5
    # ONLY the hanging post belongs to the gate. The post on the other side
    # of the opening is the next FENCE bay's, which is both what a gate
    # actually is and what stops the catch post from floating in the model
    # the moment the leaf swings clear of it.
    parts = [Part(prim.prism(6, 1.25, 15.5), at=(-HANG, 0, 0), mat="cedar",
                  name="hang_post")]
    c, sn = math.cos(swing), math.sin(swing)

    def leaf(lx, w_, h_, z0, name):
        """A member of the leaf, placed in the LEAF's own frame and swung
        with it, so the frame stays square however far the gate stands open."""
        parts.append(Part(prim.box(w_, THICK, h_, z0=z0),
                          at=(-HANG + lx * c, lx * sn, 0),
                          yaw=swing, mat="plank", name=name))

    # SAGGING OFF SQUARE: an old gate rides low at the latch end, and that
    # droop is most of what says this one has been swung a few thousand times.
    for i, zf in enumerate((0.12, 0.48, 0.90)):
        leaf(LEAF * 0.5, LEAF, TALL * 0.08, TALL * zf - i * 0.18,
             f"leaf_rail{i}")
    for i, lx in enumerate((THICK * 0.9, LEAF - THICK * 0.9)):
        leaf(lx, THICK * 1.8, TALL - i * 0.5, 0.0, f"leaf_stile{i}")
    # THE DIAGONAL BRACE, and it is the tell: it runs UP from the hinge
    # corner, the direction that carries the leaf's weight. Parts yaw about
    # z only, so it is STEPPED -- three short boards climbing hinge-foot to
    # latch-head, which reads as the diagonal at play size and stays a real
    # volume instead of a painted line.
    for i in range(4):
        f = (i + 0.5) / 4.0
        leaf(LEAF * f, LEAF / 4.0 * 0.82, TALL * 0.10,
             TALL * (0.10 + f * 0.74), f"leaf_brace{i}")
    return Assembly(*parts)


def _yard_fence(bay=33.0, seed=3, gap=False):
    # A wire fence is WAIST HIGH. Built at 20 units its posts stood as tall
    # as the player, which reads as a stockade and made the boundary look
    # like something to climb rather than step over. The whole prop is now a
    # uniform 1.3x over life, so the recorded 24 : 1 : 10.5 still holds --
    # scaling ONE axis for legibility is what breaks a proportion.
    parts = []
    for i in (-1, 1):
        lean = ((seed + i) % 5 - 2) * 0.18
        parts.append(Part(prim.prism(6, 0.75, 15.5, rot=lean),
                          at=(i * bay / 2, 0, 0), mat="cedar",
                          name=f"post{i}"))
    # The strands are thin boxes spanning the bay, dropped a little at
    # mid-span so they read as sagging rather than strung. `rust`, not
    # `steel`: bright wire was the single palest thing in a Darkwood-dark
    # yard, and a fence line that out-reads the buildings it borders is
    # drawing the eye to the least important object in the scene.
    for z, sag in ((14.0, 0.7), (9.5, 1.2), (5.0, 1.5)):
        parts.append(Part(prim.box(bay, 0.26, 0.26, z0=0.0),
                          at=(0, 0, z - sag), mat="wire",
                          name=f"wire{int(z)}"))
    if gap:
        # THE WAY THROUGH: the bay whose wire is DOWN. This is the mouth the
        # lost edge sits behind (DESIGN.md §13), so the boundary has to read
        # as something you step over rather than climb.
        #
        # The first version pulled the standing post and re-aimed all three
        # wires at where it used to be. Both posts gone-or-leaning and three
        # strands fanning off one point read as a broom, not a fence: with
        # nothing upright left, there was no fence for the gap to be a gap
        # IN. So both posts stay, one leaning hard, and the WIRES are what
        # failed -- the top two snapped away entirely, the bottom one slack
        # on the ground.
        parts = [p for p in parts
                 if not p.name.startswith("wire") or p.name == "wire5"]
        for p in parts:
            if p.name == "post-1":
                p.yaw = 0.42                    # shoved over by whatever came through
            elif p.name == "wire5":
                p.at = (p.at[0], p.at[1] + 1.0, 0.9)
                p.yaw = -0.06
        # the snapped ends, still on the standing post and hanging
        for i, (z, ang) in enumerate(((13.5, -0.62), (8.6, -0.44))):
            parts.append(Part(prim.box(bay * 0.24, 0.26, 0.26),
                              at=(bay * 0.36, 0.4, z), yaw=ang,
                              mat="wire", name=f"snapped{i}"))
    return Assembly(*parts)


# ---------------------------------------------------------------- lantern
# Reference: a garden POST LANTERN -- a tapered glass head with a peaked cap
# on a slim iron post. The kind was briefly modelled as a hand-carried
# hurricane lantern, which was the right NAME and the wrong OBJECT: a third
# of the height, sitting on the grass, under a light pool cast from 20 units
# up. FIXTURE_POOLS is what settles it (src_z 20, arm 0, warm, flickering,
# not electric), so the flame goes at z=20 directly over the base and the
# post is sized to put it there.
#
# The head TAPERS. That was the tell the old block-on-a-stick missed, and it
# is why `prim.frustum` exists -- a straight prism here reads as a tin can
# however carefully it is shaded.
def _lantern():
    real = (7.25, 7.25, 17.5)
    k = 5.0 / real[0]                  # 5 world units across at the widest
    head_w = real[0] * k
    head_h = real[2] * k
    R = head_w / 2.0                   # the head's half-width at its widest
    FLAME_Z = 20.0                     # = FIXTURE_POOLS["lantern"] src_z
    base_z = FLAME_Z - head_h / 2.0    # the head straddles the light source
    ROT = math.pi / 4                  # corners front/back, faces to the side

    # `prim.frustum` takes a CIRCUMRADIUS, so a square one placed by half its
    # side is 41% wider than intended. Getting that wrong is what made the
    # first head 3.47 : 1 against a real 2.41 : 1 -- a lit slot rather than a
    # lantern -- and the proportion check is what said so.
    def sq(half_side):
        return half_side / math.cos(math.pi / 4)

    # every z below is a fraction of head_h, so the head spans exactly
    # [base_z, base_z + head_h] and the recorded ratio stays true
    z_collar, z_glass, z_cap, z_fin = 0.0, 0.14, 0.56, 0.86
    return Assembly(
        # THE POST. Cast iron on dark grass is very nearly invisible at a
        # true 3in diameter, so it is drawn stouter than life and TAPERED --
        # a post that narrows as it rises catches a different shade on each
        # facet and reads as a standing object rather than a scratch.
        Part(prim.frustum(8, R * 0.46, R * 0.30, 2.4, rot=ROT),
             mat="iron", name="foot"),
        Part(prim.frustum(8, R * 0.30, R * 0.21, base_z - 2.0 + head_h * 0.10,
                          z0=2.0, rot=ROT),
             mat="iron", name="post"),
        # the fitter the head sits in: WIDER than the post, so the silhouette
        # steps out at the top instead of running straight up
        Part(prim.frustum(4, sq(R * 0.30), sq(R * 0.62),
                          head_h * (z_glass - z_collar),
                          z0=base_z + head_h * z_collar, rot=ROT),
             mat="iron", name="head_collar"),
        # THE GLASS: a square housing tapering inward as it rises. Lit from
        # within, so it carries its own colour rather than taking the sky's.
        Part(prim.frustum(4, sq(R * 0.85), sq(R * 0.70),
                          head_h * (z_cap - z_glass),
                          z0=base_z + head_h * z_glass, rot=ROT),
             mat="flame_glass", name="head_glass"),
        # the astragal bars standing just proud of the panes at the corners,
        # dark against the light -- what makes it read as a lantern and not
        # a glowing block
        *[Part(prim.box(0.30, 0.30, head_h * (z_cap - z_glass) + head_h*0.04),
               at=(math.cos(ROT + i * math.pi / 2) * R * 0.86,
                   math.sin(ROT + i * math.pi / 2) * R * 0.86,
                   base_z + head_h * (z_glass - 0.02)),
               mat="iron", name=f"head_bar{i}")
          for i in range(4)],
        # THE CAP: a peak, not a lid (a frustum run to a point). Its eave is
        # the widest thing on the lamp, which is what the reference measures.
        Part(prim.frustum(4, sq(R), 0.0, head_h * (z_fin - z_cap),
                          z0=base_z + head_h * z_cap, rot=ROT),
             mat="iron", name="head_cap"),
        Part(prim.frustum(8, R * 0.20, R * 0.05, head_h * (1.0 - z_fin),
                          z0=base_z + head_h * z_fin, rot=ROT),
             mat="iron", name="head_finial"),
    )


# ----------------------------------------------------------- pickup truck
# Reference: a period half-ton regular cab. The CAB ROOF is the identifying
# part -- the old model had an open-topped body, so it read as a jeep or a
# flatbed. The silhouette steps DOWN twice, cab to bed to hood.
def _pickup_truck():
    real = (194.0, 79.0, 75.0)
    # 55 units long: a real pickup is 2.77x the length of a 70in person, and
    # the player stands 20 units, so 55 is the truck at the world's own
    # scale. It also has to fill the 3-tile invisible 'X' footprint the yard
    # lays under it -- a model shorter than its own collision means bumping
    # into open air a tile away from the bumper.
    k = 55.0 / real[0]
    L, W, H = real[0] * k, real[1] * k, real[2] * k
    # the wheels have to SHOW. At a body sitting 0.9 of a wheel radius up
    # they were buried behind the pan and the truck read as a slab on
    # nothing; a pickup's stance -- wheels proud, a gap of daylight under
    # the bed -- is half of what says truck.
    wheel_r = 4.2
    body_z = wheel_r * 1.15
    pan_h = H * 0.30
    deck = body_z + pan_h                      # where cab, hood and bed sit
    cab_h = H * 0.40
    # The PAINT is the faded farm green the hand-drawn version wore. Losing
    # it to a default rust was a real cost of the conversion: the truck is a
    # working vehicle in a green valley, not a wreck, and the town already
    # has plenty of rust on it.
    return Assembly(
        # the chassis/body pan, which the reference measures
        Part(prim.box(L, W, pan_h, z0=body_z), mat="farm_green", name="body"),
        # the HOOD, lowest of the three masses
        Part(prim.box(L * 0.30, W * 0.94, H * 0.16, z0=deck),
             at=(L * 0.33, 0, 0), mat="farm_green", name="hood"),
        # the CAB, tallest -- with its roof, which is the whole point
        Part(prim.box(L * 0.30, W * 0.94, cab_h, z0=deck),
             at=(L * 0.03, 0, 0), mat="farm_green", name="cab"),
        # the GLASS, standing a hair proud of the cab so it is not swallowed
        # by the panel it sits in. The windshield leans back on the wedge.
        Part(prim.box(L * 0.20, W * 0.98, cab_h * 0.46,
                      z0=deck + cab_h * 0.40),
             at=(L * 0.01, 0, 0), mat="glass", name="side_glass"),
        Part(prim.box(L * 0.03, W * 0.90, cab_h * 0.44,
                      z0=deck + cab_h * 0.42),
             at=(L * 0.175, 0, 0), mat="glass", name="windshield"),
        # THE BED IS WALLS, not a box with a floor laid inside it. Modelled
        # as a solid, its top face is a lid over the whole footprint, and
        # since that lid sits above the floor plate the sort puts the floor
        # in front of it: the truck grew a slab of rust across its back. An
        # open bed has to be open in the GEOMETRY.
        Part(prim.plate(L * 0.38, W * 0.92, 0.6, z0=deck),
             at=(-L * 0.30, 0, 0), mat="rust", name="bed_floor"),
        *[Part(prim.box(L * 0.38, W * 0.07, H * 0.20, z0=deck),
               at=(-L * 0.30, sy * (W * 0.465), 0),
               mat="farm_green", name=f"bed_rail{sy}")
          for sy in (1, -1)],
        Part(prim.box(L * 0.04, W, H * 0.20, z0=deck),
             at=(-L * 0.47, 0, 0), mat="farm_green", name="tailgate"),
        # four wheels
        *[Part(prim.cyl(r=wheel_r, length=3.0, axis="x"),
               at=(sx * L * 0.31, sy * (W / 2 - 0.4), wheel_r),
               yaw=math.pi / 2, mat="iron", name=f"wheel{sx}{sy}")
          for sx in (1, -1) for sy in (1, -1)],
        # held off the ground on its wheels, so it needs the contact pool or
        # it reads as hovering
        shadow=0.62,
    )


# -------------------------------------------------------------- generator
# Reference: a period portable open-frame genset. THE CAGE IS THE SILHOUETTE
# -- the hand-written version this replaces was a closed steel box with a
# tank and a bulb on it, which reads as a toolbox somebody left a lamp on.
# An open frame you can see the engine through is what says machine.
#
# `running` is the whole point of the prop in the yard layer (DESIGN.md §14):
# the genset's state IS the household's, readable from the road. Lit bulb =
# somebody is still keeping the place. The scene pairs `running=False` with
# `broken=True`, which is what both light tables already read to stop a
# fixture emitting, so the dark bulb and the dark ground agree.
def _generator(running=True):
    real = (27.0, 21.0, 22.0)
    k = _k(real, 16.0)                 # 16 world units long
    L, W, H = real[0] * k, real[1] * k, real[2] * k
    TUBE = 0.8                         # the roll cage's tube
    hx, hy = L / 2 - TUBE / 2, W / 2 - TUBE / 2
    parts = []
    # The engine and tank have to FILL the cage. Built lean inside a fat
    # frame the whole prop read as an empty crate at play size -- the bars
    # were the only thing with a lit face on them and there was nothing
    # behind them to be bars in front of.
    # THE CAGE. Named `frame_*` because the reference measures the frame:
    # its outer envelope IS the 27 x 21 x 22 the catalogue quotes, and the
    # engine and tank sit inside it.
    for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        parts.append(Part(prim.box(TUBE, TUBE, H),
                          at=(sx * hx, sy * hy, 0), mat="steel",
                          name=f"frame_post{i}"))
    for z0, tag in ((0.0, "lo"), (H - TUBE, "hi")):
        for sy in (1, -1):
            parts.append(Part(prim.box(L, TUBE, TUBE, z0=z0),
                              at=(0, sy * hy, 0), mat="steel",
                              name=f"frame_rail{tag}{sy}"))
        for sx in (1, -1):
            parts.append(Part(prim.box(TUBE, W, TUBE, z0=z0),
                              at=(sx * hx, 0, 0), mat="steel",
                              name=f"frame_end{tag}{sx}"))
    # THE ENGINE, slung inside the cage where you can see it through the bars.
    # `rust` and not `iron`: a warm dark mass behind cold steel bars is what
    # makes the bars read as bars.
    parts.append(Part(prim.box(L * 0.62, W * 0.74, H * 0.46, z0=TUBE),
                      at=(-L * 0.06, 0, 0), mat="rust", name="engine"))
    # the air cleaner + the recoil starter, the two lumps that break the block
    parts.append(Part(prim.cyl(r=W * 0.19, length=W * 0.26, axis="x", segs=10),
                      at=(-L * 0.30, W * 0.16, TUBE + H * 0.36),
                      yaw=math.pi / 2, mat="iron", name="air_cleaner"))
    parts.append(Part(prim.cyl(r=H * 0.17, length=1.6, axis="x", segs=10),
                      at=(L * 0.22, 0, TUBE + H * 0.26),
                      mat="steel", name="recoil"))
    # THE FUEL TANK, across the cage's top rails -- where a genset carries it.
    # Red enamel, the same as the can standing beside it: in a yard where
    # everything else is weathered wood, the fuel is the one coloured thing.
    parts.append(Part(prim.box(L * 0.76, W * 0.72, H * 0.26,
                               z0=H - TUBE - H * 0.26),
                      at=(0, 0, 0), mat="enamel_red", name="tank"))
    parts.append(Part(prim.cyl(r=0.85, length=1.0, axis="z",
                               z0=H - TUBE - 0.1),
                      at=(-L * 0.24, 0, 0), mat="steel", name="fuel_cap"))
    # THE CONTROL PANEL on the +x end, with its outlets
    parts.append(Part(prim.plate(0.7, W * 0.52, H * 0.30, z0=TUBE + H * 0.16),
                      at=(hx - 0.5, 0, 0), mat="steel", name="panel"))
    for i, sy in enumerate((-1, 1)):
        parts.append(Part(prim.box(0.6, 1.5, 1.5,
                                   z0=TUBE + H * 0.22),
                          at=(hx - 0.1, sy * W * 0.13, 0),
                          mat="iron", name=f"outlet{i}"))
    # the stub muffler out the -x end
    parts.append(Part(prim.cyl(r=1.05, length=L * 0.26, axis="x", segs=10),
                      at=(-hx - L * 0.06, W * 0.16, TUBE + H * 0.30),
                      mat="iron", name="muffler"))
    # WHEELS on one end, feet on the other: somebody wheeled this out here
    for i, sy in enumerate((1, -1)):
        parts.append(Part(prim.cyl(r=1.6, length=0.9, axis="x", segs=10),
                          at=(-hx, sy * (W / 2 + 0.3), 1.6),
                          yaw=math.pi / 2, mat="iron", name=f"wheel{i}"))
    # THE WORK LIGHT clamped to the cage, and the household's whole state in
    # one part: lit glass, or dark glass on a genset nobody has fuelled.
    # It is the piece the player actually reads from the road, so it is built
    # to be seen: a stalk clear of the cage, a wide conical shade, and the
    # bulb hanging out of its mouth where the shade cannot hide it.
    stalk_x, stalk_y = hx - 0.4, -hy
    parts.append(Part(prim.box(0.6, 0.6, 3.0, z0=H - 0.4),
                      at=(stalk_x, stalk_y, 0), mat="steel", name="lamp_stalk"))
    parts.append(Part(prim.box(2.6, 0.6, 0.6, z0=H + 2.0),
                      at=(stalk_x - 1.3, stalk_y, 0), mat="steel",
                      name="lamp_arm"))
    # A CONE SHADE HID THE BULB. Under a 55-degree camera you look down INTO
    # a lampshade, so the one part that carries the household's state was
    # occluded by its own reflector from every facing. It is a droplight
    # instead: a small cap with the bulb hanging BELOW and WIDER than it, so
    # the bulb's silhouette clears the cap whichever way the view turns.
    parts.append(Part(prim.frustum(10, 1.45, 0.55, 0.7, z0=H + 1.7),
                      at=(stalk_x - 2.4, stalk_y, 0), mat="tin",
                      name="lamp_cap"))
    parts.append(Part(prim.frustum(9, 0.85, 1.5, 0.7, z0=H + 1.0),
                      at=(stalk_x - 2.4, stalk_y, 0),
                      mat="flame_glass" if running else "glass",
                      name="lamp_bulb"))
    parts.append(Part(prim.frustum(9, 1.5, 0.5, 1.0, z0=H),
                      at=(stalk_x - 2.4, stalk_y, 0),
                      mat="flame_glass" if running else "glass",
                      name="lamp_glass"))
    return Assembly(*parts)


# --------------------------------------------------------------- fuel can
# Reference: a NATO-pattern steel jerry can. It is a SLAB -- twice as wide
# as it is deep -- with the tri-handle across the top, and that pair of facts
# is the whole silhouette; a square canister at this size reads as an oil
# drum sitting next to the machine it is supposed to feed.
#
# `tipped` is the yard layer's other half of the genset read: standing means
# somebody still fuels the place, on its side and empty means nobody does.
# Every piece is a cuboid on purpose, so lying it down is a coordinate
# mapping rather than a second model that can drift from the first.
def _fuel_can(tipped=False):
    real = (13.6, 6.6, 18.5)
    k = 8.0 / real[2]                  # 8 world units tall standing
    L, D, H = real[0] * k, real[1] * k, real[2] * k
    parts = []

    def add(w, d, h, cx, cy, cz, mat, name):
        """Place a cuboid by its CENTRE, upright or rolled onto its face.

        Tipped is a +90 degree roll about +x: (y, z) -> (-z, y), then lifted
        so the can rests on its wide face and centred back over its own
        footprint. Doing it here means the ribs, the handles and the spout
        all lie down together and none of them can be forgotten."""
        if tipped:
            w, d, h = w, h, d
            cx, cy, cz = cx, -cz + H * 0.5, cy + D * 0.5
        parts.append(Part(prim.box(w, d, h, z0=-h / 2.0),
                          at=(cx, cy, cz), mat=mat, name=name))

    body_h = H * 0.86
    add(L, D, body_h, 0, 0, body_h / 2.0, "enamel_red", "body")
    # the three ribs pressed down each wide face
    for i, ox in enumerate((-L * 0.28, 0.0, L * 0.28)):
        for j, sy in enumerate((1, -1)):
            add(L * 0.10, 0.34, body_h * 0.78,
                ox, sy * (D / 2.0 + 0.12), body_h / 2.0,
                "enamel_red", f"rib{i}{j}")
    # the raised top pressing the handles stand on
    add(L * 0.86, D * 0.80, H * 0.05, 0, 0, body_h + H * 0.025,
        "enamel_red", "deck")
    # THE TRI-HANDLE: three grips in a row across the top, running across the
    # can's depth. It is the identifying part -- a bare slab with a cap on it
    # is a fuel TANK, not a can somebody carries.
    for i, ox in enumerate((-L * 0.28, 0.0, L * 0.28)):
        add(L * 0.16, D * 0.92, H * 0.07,
            ox, 0, body_h + H * 0.09, "steel", f"handle{i}")
    # the spout at the shoulder, capped
    add(L * 0.17, D * 0.42, H * 0.10, L * 0.36, 0, body_h + H * 0.06,
        "steel", "spout")
    add(L * 0.20, D * 0.48, H * 0.05, L * 0.36, 0, body_h + H * 0.13,
        "enamel_red", "cap")
    return Assembly(*parts)


# ------------------------------------------------------------- clothesline
# Reference: a domestic T-post line. The CROSSARM is what makes it a
# clothesline rather than two fence posts, and the washing has to hang STIFF:
# it has been out since January and it is April (NARRATIVE §1). Frozen cloth
# does not drape -- it stands out off the line like board, which is exactly
# what a flat-sided box does well and what a soft draped shape would have
# needed a primitive nobody has.
def _clothesline(laundry=4, seed=3, small=False):
    real = (240.0, 36.0, 84.0)
    k = 24.0 / real[2]                 # posts 24 world units, over head height
    SPAN, ARM, POST = real[0] * k, real[1] * k, real[2] * k
    parts = []
    for i, sx in enumerate((-1, 1)):
        lean = ((seed + i) % 5 - 2) * 0.05
        parts.append(Part(prim.box(1.6, 1.6, POST),
                          at=(sx * SPAN / 2.0, 0, 0), yaw=lean,
                          mat="cedar", name=f"post{i}"))
        parts.append(Part(prim.box(1.4, ARM, 1.3, z0=POST - 2.2),
                          at=(sx * SPAN / 2.0, 0, 0),
                          mat="cedar", name=f"arm{i}"))
    # THE LINES SAG, and deeper in the middle than at the ends.
    line_y = (-ARM * 0.37, 0.0, ARM * 0.37)
    line_z = []
    for i, ly in enumerate(line_y):
        z = POST - 1.6 - (1.5 if i == 1 else 1.0)
        line_z.append(z)
        parts.append(Part(prim.box(SPAN, 0.24, 0.24),
                          at=(0, ly, z), mat="wire", name=f"line{i}"))
    # WHAT IS PEGGED OUT. Rigid, slightly askew, and hung on the lines rather
    # than floating between them -- the top of each piece sits ON its line.
    for n in range(laundry):
        h = (seed * 7 + n * 41)
        li = n % len(line_y)
        wid = (4.2 if small else 6.6) + (h % 4) * 0.9
        drop = (6.0 if small else 10.0) + ((h >> 2) % 5) * 0.9
        px = (n + 0.5) / laundry * SPAN - SPAN / 2.0 + ((h >> 4) % 3 - 1) * 1.2
        parts.append(Part(
            prim.box(wid, 0.45, drop, z0=line_z[li] - drop),
            at=(px, line_y[li], 0), yaw=((h >> 5) % 5 - 2) * 0.06,
            mat="wool" if n % 3 == 2 else "linen", name=f"washing{n}"))
    return Assembly(*parts)


# -------------------------------------------------------------- crate stack
# Reference: rough wirebound produce crates. It is separate CRATES: the
# courses have to step and misalign, or the stack reads as one painted box --
# the same failure the woodpile had before its logs became logs.
#
# The reference measures ONE crate, so exactly one part is named `crate` and
# the rest carry their grid position. Naming them all `crate_N` would make
# the check measure the whole stack, which is not a thing anybody has
# dimensions for.
def _crate_stack(courses=3, seed=5, tarp=False, opened=False):
    real = (20.0, 13.0, 12.0)
    k = 14.0 / (real[2] * 3.0)         # three courses stand 14 units
    CL, CD, CH = real[0] * k, real[1] * k, real[2] * k
    parts = []
    top_z = 0.0
    for row in range(courses):
        # the top course of an unopened stack is a single crate, so the
        # silhouette steps in as it rises instead of running up square
        ncol = 1 if row == courses - 1 else 2
        for c in range(ncol):
            h = (seed + row * 29 + c * 13)
            x = (c - (ncol - 1) / 2.0) * (CL + 0.5) + ((h % 5) - 2) * 0.45
            y = ((h >> 3) % 5 - 2) * 0.4
            z = row * CH
            yaw = ((h >> 5) % 7 - 3) * 0.045
            name = "crate" if (row == 0 and c == 0) else f"box_r{row}c{c}"
            if opened and row == courses - 1:
                # THE ONE THAT GOT PULLED DOWN AND OPENED. Built in place at
                # the top of the stack, an open crate reads as a shut one: you
                # look down into it, its inner faces cull away, and what shows
                # through the mouth is the crate underneath. So it comes OFF
                # the stack -- on the ground beside it, walls low, lid leaning
                # where somebody dropped it. That silhouette cannot be
                # mistaken for another course.
                gx, gy = x + CL * 0.80, y - CD * 0.55
                for s, (bw, bd, bx, by) in enumerate((
                        (CL, 0.7, 0.0, CD / 2 - 0.35),
                        (CL, 0.7, 0.0, -CD / 2 + 0.35),
                        (0.7, CD, CL / 2 - 0.35, 0.0),
                        (0.7, CD, -CL / 2 + 0.35, 0.0))):
                    parts.append(Part(prim.box(bw, bd, CH * 0.62, z0=0),
                                      at=(gx + bx, gy + by, 0), yaw=yaw + 0.22,
                                      mat="crate_pine", name=f"open_wall{s}"))
                parts.append(Part(prim.plate(CL * 0.94, CD * 0.9, 0.7,
                                             z0=CH * 0.62),
                                  at=(gx - CL * 0.20, gy + CD * 0.30, 0),
                                  yaw=yaw + 0.55, mat="crate_pine",
                                  name="lid"))
                continue
            parts.append(Part(prim.box(CL, CD, CH, z0=z),
                              at=(x, y, 0), yaw=yaw,
                              mat="crate_pine", name=name))
            # two slat boards proud of the long faces: the gaps between the
            # slats are the surface, and at this size two are enough to read
            for s, sy in enumerate((1, -1)):
                parts.append(Part(
                    prim.box(CL * 0.98, 0.35, CH * 0.22,
                             z0=z + CH * (0.20 if s == 0 else 0.62)),
                    at=(x, y + sy * (CD / 2 + 0.15), 0), yaw=yaw,
                    mat="crate_pine", name=f"slat{row}{c}{s}"))
        top_z = (row + 1) * CH
    if tarp:
        # ROPED DOWN over the top course, not draped: a taut sheet with the
        # rope crossing it. A tarp that hangs would need cloth nobody has.
        parts.append(Part(prim.plate(CL * 1.5, CD * 1.5, 0.5, z0=top_z),
                          at=(0, 0, 0), yaw=0.08, mat="canvas", name="tarp"))
        for i, sx in enumerate((-0.32, 0.34)):
            parts.append(Part(prim.box(0.4, CD * 1.6, 0.4, z0=top_z + 0.4),
                              at=(sx * CL, 0, 0), mat="wire",
                              name=f"tarp_rope{i}"))
    return Assembly(*parts)


# A VALUE here is a finished assembly; a FUNCTION is a variant factory that
# the draw path calls with whichever of the decoration's kwargs it declares
# (`variant()` below). Both are equally declarative -- the factory just lets a
# scene say WHICH mailbox rather than getting the only one.
ASSEMBLIES = {
    "mailbox": _mailbox,
    "stoop": _stoop,
    "woodpile": _woodpile,
    "yard_fence": _yard_fence,
    "yard_gate": _yard_gate,
    "lantern": _lantern(),
    "pickup_truck": _pickup_truck(),
    # the yard layer's vocabulary (DESIGN.md §14)
    "generator": _generator,
    "fuel_can": _fuel_can,
    "clothesline": _clothesline,
    "crate_stack": _crate_stack,
}

# Built variants, keyed by (kind, the kwargs that mattered). An assembly is
# immutable geometry, so one per combination is built once and reused for
# every draw of it -- the same deal the fixed entries above already get.
_VARIANTS = {}


def variant(kind, factory, kw):
    """The assembly for `kind` under a decoration's kwargs.

    Only the parameters the factory actually declares are read, so a scene
    passing something the prop does not know about gets the default rather
    than a TypeError -- and, more usefully, a factory can grow a new variant
    without every existing placement having to change.
    """
    names = [p for p in inspect.signature(factory).parameters]
    picked = tuple(sorted((n, kw[n]) for n in names if n in kw))
    key = (kind, picked)
    asm = _VARIANTS.get(key)
    if asm is None:
        asm = _VARIANTS[key] = factory(**dict(picked))
    return asm


def base(kind):
    """The default assembly for a kind, whether or not it is a factory.
    What `references.py` and `validate()` measure."""
    a = ASSEMBLIES[kind]
    return variant(kind, a, {}) if callable(a) else a
