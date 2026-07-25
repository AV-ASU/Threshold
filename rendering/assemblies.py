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

from rendering import lettering, prim
from rendering.assembly import Assembly, Part
from rendering.materials import shade_for


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


# ------------------------------------------------------------ semi truck
# Reference: an 80s conventional tractor + a 48ft dry van. Royce hauled for
# Brimley for twelve years, so the bare shelves in Hettie's shop are HIS
# stopped deliveries (TODO #12) -- the rig is that fact made an object, and
# it is the largest man-made thing in the town.
def _semi_truck(stripped=True):
    real = (576.0, 102.0, 110.0)
    k = _k(real, 118.0)                  # 118 world units of trailer
    L, W, H = real[0] * k, real[1] * k, real[2] * k
    deck = 48.0 * k                      # trailer floor above the road
    tx = L * 0.5 - 12.0                  # the nose of the box
    wheel_r = 4.2
    parts = [
        # THE BOX. One volume, because a dry van is one volume; the detail
        # that sells it is what is UNDER it, not panel lines on it.
        Part(prim.box(L, W, H), at=(-14.0, 0, deck), mat="rust",
             name="trailer"),
        Part(prim.box(L * 0.98, W * 0.72, 2.4), at=(-14.0, 0, deck - 2.4),
             mat="steel", name="deckrail"),
        # landing gear: the legs it stands on with no tractor under the nose
        *[Part(prim.box(2.2, 2.2, deck - 1.0), at=(tx - 34.0, sy * W * 0.30, 0),
               mat="steel", name=f"gear{sy}") for sy in (1, -1)],
        # the bogie, back under the tail
        *[Part(prim.cyl(r=wheel_r, length=3.4, axis="x"),
               at=(-14.0 - L * 0.36 + ax * 10.0, sy * (W / 2 - 1.6), wheel_r),
               yaw=math.pi / 2, mat="iron", name=f"bogie{ax}{sy}")
          for ax in (0, 1) for sy in (1, -1)],
        # THE TRACTOR: hood out in front of the cab is what makes it a
        # conventional rather than a cab-over, so the silhouette steps DOWN
        # from stack to cab roof to hood.
        Part(prim.box(20.0, W * 0.92, 20.0), at=(tx + 16.0, 0, 7.0),
             mat="farm_green", name="cab"),
        Part(prim.box(9.0, W * 0.62, 8.0), at=(tx + 16.0, 0, 21.0),
             mat="glass", name="windshield"),
        Part(prim.box(22.0, W * 0.80, 11.0), at=(tx + 37.0, 0, 7.0),
             mat="farm_green", name="hood"),
        Part(prim.box(24.0, W * 0.98, 5.0), at=(tx + 26.0, 0, 2.0),
             mat="steel", name="frame"),
        Part(prim.cyl(r=1.5, length=22.0, axis="z"),
             at=(tx + 5.0, W * 0.40, 8.0), mat="steel", name="stack"),
        Part(prim.cyl(r=3.0, length=13.0, axis="x"),
             at=(tx + 26.0, -W * 0.46, 7.0), yaw=math.pi / 2,
             mat="tin", name="fueltank"),
        *[Part(prim.cyl(r=wheel_r, length=3.4, axis="x"),
               at=(tx + 40.0, sy * (W * 0.44), wheel_r),
               yaw=math.pi / 2, mat="iron", name=f"steer{sy}")
          for sy in (1, -1)],
    ]
    drive = [(0, 1), (0, -1), (1, 1), (1, -1)]
    if stripped:
        # PICKED CLEAN. Nothing leaves Brimley, so the rig is a parts shop:
        # the near drive wheels are gone and the rear doors hang open. It has
        # to read as robbed rather than crashed -- everything is still square
        # on its frame, it is simply missing pieces.
        drive = [(0, -1), (1, -1)]
        for sy, ang in ((1, 1.15), (-1, -1.15)):
            parts.append(Part(
                prim.box(1.6, W * 0.48, H * 0.94),
                at=(-14.0 - L * 0.5 - W * 0.20, sy * W * 0.24, deck),
                yaw=sy * ang, mat="rust", name=f"door{sy}"))
    else:
        for sy in (1, -1):
            parts.append(Part(prim.box(1.6, W * 0.48, H * 0.94),
                              at=(-14.0 - L * 0.5, sy * W * 0.24, deck),
                              mat="rust", name=f"door{sy}"))
    parts += [Part(prim.cyl(r=wheel_r, length=3.4, axis="x"),
                   at=(tx + 8.0 - ax * 10.0, sy * (W / 2 - 1.6), wheel_r),
                   yaw=math.pi / 2, mat="iron", name=f"drive{ax}{sy}")
              for ax, sy in drive]
    # NO contact pool. The shared shadow is a circle sized off the prop's
    # LARGEST extent, which on a 177-unit rig lands a black disc wider than
    # the trailer is long. Its own dark underside does the job here.
    return Assembly(*parts)


# ------------------------------------------------------------- seed corn
# Reference: a pallet of 50lb seed-corn sacks, unopened. This is what
# replaced Old Pell's stopped calendar (TODO #28): the calendar said "a man
# who quit marking days" in a generic prop that every room in town also had,
# and the seed says the same thing in HIS language and only his. It is April.
# A corn man's seed is still sewn shut.
def _seed_corn(rows=4):
    real = (30.0, 18.0, 6.0)
    k = _k(real, 11.4)                   # 11.4 world units long
    L, W, H = real[0] * k, real[1] * k, real[2] * k
    pallet_h = 1.5
    parts = [
        # the pallet: boards, not a slab, so it reads as something delivered
        *[Part(prim.box(L * 1.06, W * 0.17, pallet_h * 0.55),
               at=(0, (b - 1.5) * W * 0.30, pallet_h * 0.45),
               mat="pallet", name=f"deck{b}")
          for b in range(4)],
        *[Part(prim.box(L * 0.12, W * 1.02, pallet_h * 0.45),
               at=(sx * L * 0.40, 0, 0), mat="pallet", name=f"bearer{sx}")
          for sx in (1, -1)],
    ]
    for i in range(rows):
        # A full sack BULGES. A six-sided frustum tapering toward its top
        # reads as a stuffed sack; a box reads as a carton, which is the
        # mistaken-identity failure this shape exists to dodge.
        turn = 0.06 if i % 2 else -0.05
        parts.append(Part(
            prim.pillow(L, W, H),
            at=(L * (0.03 if i % 2 else -0.03), W * (0.02 if i % 2 else -0.02),
                pallet_h + i * H * 0.92),
            yaw=turn, mat="sack", name=f"sack{i}"))
        # the sewn end-folds that say SEALED, one at each end of the sack
        for sx in (1, -1):
            parts.append(Part(
                prim.box(L * 0.09, W * 0.46, H * 0.34),
                at=(sx * L * 0.40 + L * (0.03 if i % 2 else -0.03),
                    W * (0.02 if i % 2 else -0.02),
                    pallet_h + i * H * 0.92 + H * 0.30),
                yaw=turn, mat="sack", name=f"seam{i}_{'a' if sx > 0 else 'b'}"))
    return Assembly(*parts)


# ------------------------------------------------------------- town sign
# Reference: the 1959 "Welcome to Fabulous Las Vegas" board and its googie
# family -- a BRIGHT cream panel in a coral frame, a bulb-lined atomic
# STARBURST rising behind it, and two splayed steel legs. The maintainer
# asked for "bright, very 1960-1970, like that sign in Back to the Future",
# and this is that sign's older and more famous cousin: the archetype for a
# roadside board whose whole job is to WELCOME.
#
# It is also the fix for the thing that kept failing. Two earlier cuts were
# weathered farm boards, dark green on dark ground, and the lower two lines
# could not be read at play zoom at either size. Contrast, not scale, was the
# missing ingredient: near-black ink on a cream panel reads where bone on
# municipal green never did, and giving each subordinate line its OWN
# coloured band means it is bounded by its background instead of dissolving
# into the field. In fiction this is the last bright thing in Brimley --
# built when the town still had a future, and still burning out on the road
# with nobody left to read it.
_SIGN_LINES = ("BRIMLEY", "NORTHERNMOST CORN", "EST. 1894")


def _sign_paint(lines, plane_y, bulbs=None):
    """The sign's artwork: its lettering, and the bulbs around its panel.

    Everything here is drawn in the PANEL's own plane through the prop's
    local-to-screen projector, so it foreshortens and goes edge-on with the
    board. `lines` is (text, x0, x1, z bottom, z top, ink material, weight);
    `bulbs` is a closed outline in panel coordinates to run a bulb string
    around. The paint SHADES with the face it sits on, using the same
    `toward` the renderer culled by, so the whole sign dims together as it
    turns away instead of the artwork staying flat and giving the surface
    away as a sticker.
    """
    def paint(surf, to_screen, toward_viewer):
        import pygame
        toward = toward_viewer(0.0, -1.0, 0.0)
        if toward <= 0.001:
            return                       # the back of the board is bare
        def proj(lx, lz):
            return to_screen(lx, plane_y, lz)
        if bulbs:
            # The bulb string. Mid-century signage is lit by BULBS in a
            # row, not by an even glow, and the row of separate points is
            # the tell -- an edge-lit outline reads as a modern LED strip.
            warm = shade_for("sign_star", "top", 0.4, toward)
            hot = tuple(min(255, c + 46) for c in warm)
            for i, (bx, bz) in enumerate(bulbs):
                px, py = proj(bx, bz)
                r = 2 if (i % 2) else 3
                pygame.draw.circle(surf, warm, (int(px), int(py)), r)
                pygame.draw.circle(surf, hot, (int(px), int(py)), max(1, r - 1))
        for text, x0, x1, zb, zt, ink, weight in lines:
            lettering.paint_word(surf, proj, text, x0, x1, zb, zt,
                                 shade_for(ink, "side", 0.0, toward),
                                 wear=None, weight=weight,
                                 seed=sum(ord(c) for c in text))
    return paint


def _ring(x0, x1, z0, z1, step):
    """Evenly spaced points around a rectangle, for a bulb string."""
    pts = []
    w, h = x1 - x0, z1 - z0
    nx, nz = max(2, int(w / step)), max(2, int(h / step))
    for i in range(nx):
        f = i / nx
        pts.append((x0 + w * f, z0))
        pts.append((x1 - w * f, z1))
    for i in range(nz):
        f = i / nz
        pts.append((x1, z0 + h * f))
        pts.append((x0, z1 - h * f))
    return pts


def sign_legibility(lines, cam_scale=1.10, sin_pitch=0.8191520442889918):
    """How big each line of a sign's lettering actually lands, IN SCREEN
    PIXELS, at play zoom.

    This exists because four rebuilds of the town sign were judged by eye
    from zoomed captures and the maintainer kept, correctly, calling the
    result unreadable. The eye cannot tell 9px from 5px in a magnified crop,
    and the answer was never a matter of taste: at the shipping camera the
    board renders about 143 x 39 pixels, and seventeen characters across it
    is 4.5px each. No alphabet resolves that.

    A vertical face is barely foreshortened here (`sin_pitch`, ~0.82 of the
    horizontal), so WIDTH-PER-CHARACTER is almost always the binding
    constraint, not cap height. Returns (text, cap_px, per_char_px) per line.
    """
    out = []
    for text, x0, x1, zb, zt, _ink, _w in lines:
        total, _cells = lettering.layout(text)
        cap = (zt - zb)
        per = min((x1 - x0) / max(total, 0.001), cap * 0.72)
        out.append((text, cap * cam_scale * sin_pitch, per * cam_scale))
    return out


def _town_sign(text="BRIMLEY", welcome=True):
    """The town's sign.

    `welcome` is the civic board at the road in: the full googie sign with
    the starburst and all three lines. Without it you get the compact
    single-word wayfinding board, which is what five of this kind's six
    placements actually are. That USED to be inferred from the text reading
    "BRIMLEY", which meant the three directional boards pointing travellers
    toward town each rendered the whole civic welcome board, founding year
    and all -- four welcome signs for one town, three of them nowhere near
    its edge.
    """
    # An 8 x 24ft panel. The width is not a style choice, it is arithmetic.
    # MEASURED at play zoom, an 8x16 board renders 80 x 44 SCREEN PIXELS, and
    # "NORTHERNMOST CORN" is seventeen characters: 4.5px each, which no
    # alphabet and no amount of contrast can resolve. Three rebuilds went
    # into styling before anyone counted the pixels. Characters-per-line
    # against panel-width-in-pixels is the whole problem, so the board went
    # WIDE (3:1 rather than 2:1) until the long line cleared 8px a
    # character. `sign_legibility()` below keeps it there.
    real = (288.0, 2.0, 96.0)
    if welcome:
        pw = 130.0                           # panel width, world units
        base_z = 15.0                        # clears the hanging plaque
        frame, leg_t, leg_splay = 2.6, 3.0, 0.20
    else:
        pw = 34.0
        base_z = 12.0
        frame, leg_t, leg_splay = 1.5, 1.9, 0.13
    k = _k(real, pw)
    ph = (real[2] * k) if welcome else 10.0  # a wayfinding board is squatter
    pt = max(0.9, real[1] * k)               # panel thickness
    top_z = base_z + ph
    fy = -(pt / 2) - 0.5                     # the frame stands proud
    parts = [
        # TWO plates, not one box, because only ONE side is the artwork. A
        # single box carries the cream on all six faces, so from behind you
        # get a bright panel instead of the sign's plain back.
        Part(prim.box(pw, pt * 0.5, ph), at=(0, -pt * 0.25, base_z),
             mat="sign_field", name="panel_face"),
        Part(prim.box(pw, pt * 0.5, ph), at=(0, pt * 0.25, base_z),
             mat="sign_steel", name="panel_back"),
        # the coral frame: two rails and two stiles, standing proud
        Part(prim.box(pw + frame * 1.6, frame * 0.7, frame),
             at=(0, fy, top_z - frame * 0.2), mat="sign_accent",
             name="frame_top"),
        Part(prim.box(pw + frame * 1.6, frame * 0.7, frame),
             at=(0, fy, base_z - frame * 0.8), mat="sign_accent",
             name="frame_bottom"),
        *[Part(prim.box(frame, frame * 0.6, ph),
               at=(sx * (pw / 2 + frame * 0.3), fy + 0.1, base_z),
               mat="sign_accent", name=f"frame_stile{sx}")
          for sx in (1, -1)],
        # THE SPLAYED LEGS. Two posts straight down is a farm board; a
        # mid-century sign stands on legs that lean out, which is what
        # `Part.pitch` was added for.
        # Lifted by exactly the amount the lean drops its low corner, or the
        # leg's foot sinks under the ground -- which `validate()` reports and
        # the tilt camera would show as a post growing out of nothing.
        *[Part(prim.box(leg_t, leg_t, base_z + 4.0),
               at=(sx * (pw * 0.26), pt / 2 + leg_t * 0.6,
                   leg_t * 0.5 * math.sin(leg_splay)),
               pitch=sx * leg_splay, mat="sign_steel", name=f"leg{sx}")
          for sx in (1, -1)],
    ]
    plaque_h = ph * 0.30                     # the hanging year-plaque
    if welcome:
        # THE STARBURST, rising behind the panel and clearing its top. An
        # eight-point atomic star is the shape that says 1960s roadside on
        # sight, and it is the sign's silhouette above the board.
        # The star clears the panel's top, but only just: it is the
        # silhouette, not the subject, and the panel has to stay the thing
        # you look at.
        parts.append(Part(prim.star(8, pw * 0.14, pw * 0.055, 1.4),
                          at=(0, pt * 0.55, top_z + pw * 0.012),
                          mat="sign_star", name="star"))
        # the hanging plaque that carries the founding year, so the smallest
        # line gets a panel of its own instead of a strip of the big one
        parts.append(Part(prim.box(pw * 0.46, pt * 0.6, plaque_h),
                          at=(0, 0, base_z - plaque_h - 1.2),
                          mat="sign_accent", name="plaque"))
        # the hanger, BETWEEN the plaque's top and the panel's underside --
        # a plaque swinging under a gap is a floating part, which is exactly
        # what `validate()` exists to catch
        parts.append(Part(prim.box(pw * 0.10, pt * 0.4, 2.0),
                          at=(0, 0, base_z - 1.4),
                          mat="sign_steel", name="plaque_hanger"))
    inner = pw / 2 - frame * 0.9             # the artwork field
    if welcome:
        # THE NAME takes the top two thirds of the panel and is the only
        # line anybody reads at speed. The boast sits under it in cream on
        # the coral band, and the year on its own hanging plaque: each
        # subordinate line bounded by its own colour rather than dissolving
        # into the field, which is what made them unreadable before.
        band0, band1 = base_z + ph * 0.03, base_z + ph * 0.50
        parts.append(Part(prim.box(pw * 0.97, pt * 0.42, band1 - band0),
                          at=(0, -pt * 0.46, band0), mat="sign_accent",
                          name="band"))
        pz0 = base_z - plaque_h - 1.2
        # A HIERARCHY, because the pixels only stretch so far. The town's
        # name is unmistakable, the boast is readable, and the founding year
        # is fine print -- which is what it is on a real sign too. Trying to
        # give all three the same weight is what kept all three small.
        lines = [
            (_SIGN_LINES[0], -inner, inner,
             base_z + ph * 0.56, base_z + ph * 0.97, "sign_paint", 0.17),
            (_SIGN_LINES[1], -inner * 0.97, inner * 0.97,
             base_z + ph * 0.19, base_z + ph * 0.44, "sign_accent_ink", 0.20),
            (_SIGN_LINES[2], -pw * 0.21, pw * 0.21,
             pz0 + plaque_h * 0.24, pz0 + plaque_h * 0.82,
             "sign_accent_ink", 0.20),
        ]
        bulbs = _ring(-pw / 2 - frame * 0.2, pw / 2 + frame * 0.2,
                      base_z - frame * 0.5, top_z + frame * 0.3, pw * 0.075)
    else:
        lines = [(text, -inner, inner, base_z + ph * 0.20,
                  base_z + ph * 0.80, "sign_paint", 0.18)]
        bulbs = None
    asm = Assembly(*parts,
                   overlay=_sign_paint(lines, -(pt / 2) - 0.7, bulbs))
    # the very lines the overlay paints, so a legibility check can never
    # be measuring a layout the sign does not actually draw
    asm.lines = lines
    return asm


# A VALUE here is a finished assembly; a FUNCTION is a variant factory that
# the draw path calls with whichever of the decoration's kwargs it declares
# (`variant()` below). Both are equally declarative -- the factory just lets a
# scene say WHICH mailbox rather than getting the only one.
ASSEMBLIES = {
    "mailbox": _mailbox,
    "stoop": _stoop,
    "woodpile": _woodpile,
    "yard_fence": _yard_fence,
    "lantern": _lantern(),
    "pickup_truck": _pickup_truck(),
    "town_sign": _town_sign,
    "seed_corn": _seed_corn,
    "semi_truck": _semi_truck,
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
