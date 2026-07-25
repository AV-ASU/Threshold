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


# ------------------------------------------------------------- town sign
# Reference: a 4x8ft painted panel in a battened frame, on two squared posts,
# panel bottom about 3 1/2ft up. The version this replaces was a flat tan
# rectangle on two sticks with its three lines rendered in a SYSTEM FONT and
# blitted at the board's projected centre -- so the words stayed
# screen-horizontal while the board foreshortened, and from the east they
# floated off the plank and hung over the post. It also painted its own BACK:
# the same three lines read perfectly from behind a board the fiction says
# nobody ever painted (the SPREAD ending's drive-out shows "the side they
# never painted"). Both faults are structural here rather than fixed: the
# lettering is an OVERLAY in the panel's own plane, and it is drawn only when
# the panel's front normal faces the viewer.
_SIGN_LINES = ("BRIMLEY", "NORTHERNMOST CORN", "EST. 1894")


def _sign_paint(lines, x0, x1, plane_y):
    """The board's lettering, painted in the panel's plane.

    `lines` is (text, z bottom, z top, brush weight). The paint SHADES with
    the face it sits on -- same material table, same `toward` the renderer
    culled by -- so the letters dim as the board turns away instead of
    staying flat and giving the surface away as a sticker.
    """
    def paint(surf, to_screen, toward_viewer):
        toward = toward_viewer(0.0, -1.0, 0.0)
        if toward <= 0.001:
            return                       # the back of the board is bare
        col = shade_for("sign_paint", "side", 0.0, toward)
        chip = shade_for("sign_field", "side", 0.0, toward)

        def proj(lx, lz):
            return to_screen(lx, plane_y, lz)

        for text, zb, zt, weight in lines:
            lettering.paint_word(surf, proj, text, x0, x1, zb, zt, col,
                                 wear=chip, weight=weight,
                                 seed=sum(ord(c) for c in text))
    return paint


def _town_sign(text="BRIMLEY", welcome=True):
    """A painted board on two posts.

    `welcome` is the town's civic board at the road in: the full 4x8 panel
    carrying all three lines. Without it you get the compact single-word
    wayfinding board, which is what five of this kind's six placements
    actually are. That USED to be inferred from the text reading "BRIMLEY",
    which meant the three directional boards pointing travellers toward town
    each rendered the whole civic welcome board, founding year and all --
    four welcome signs for one town, three of them nowhere near its edge.
    """
    # An 8 x 16ft board: DOUBLE the 4x8 sheet a small sign is cut from, and
    # the size the town's own board actually wants to be. Three lines on a
    # 4x8 left the name 8px high at play zoom with one-pixel strokes, which
    # is a smudge -- a sign nobody can read is not a sign. Doubling the real
    # object rather than inflating a small one keeps the model honest: a
    # 16ft board genuinely stands about twice a wall, so the world size below
    # is close to true scale instead of an exaggeration to be apologised for.
    # The panel holds the same 2:1 either way.
    real = (192.0, 2.0, 96.0)
    if welcome:
        pw = 72.0                            # panel width, world units
        base_z = 10.0                        # bottom edge, about 3 1/2ft up
        post_t, rail_h, stile_w, cap_h = 3.4, 2.8, 2.4, 1.3
        post_in, post_rise = 5.0, 1.0
    else:
        pw = 34.0
        base_z = 12.0
        post_t, rail_h, stile_w, cap_h = 1.9, 1.5, 1.3, 0.75
        post_in, post_rise = 2.2, 0.5
    k = _k(real, pw)
    ph = (real[2] * k) if welcome else 10.0  # a wayfinding board is squatter
    pt = max(0.8, real[1] * k)               # panel thickness
    top_z = base_z + ph
    # THE POSTS ARE MEASURED IN WORLD UNITS, not scaled off `k`: how far a
    # board stands off the ground is a fact about the world, not about the
    # exaggeration baked into the model (the mailbox lesson).
    post_h = top_z + post_rise
    post_x = pw / 2 - post_in                     # inset from the panel ends
    post_y = pt / 2 + post_t / 2                  # the board hangs on the FRONT
    rail_w = pw + rail_h * 0.8
    # the frame stands PROUD of the panel toward the reader; that shadow line
    # is what makes it a board rather than a painted plank
    fy = -(pt / 2) - 0.45
    parts = [
        # TWO plates, not one box, because only ONE side of a board ever gets
        # painted. A single `sign_field` box carries the municipal green on
        # all six faces, so from behind you get a smart green panel instead
        # of the bare weathered plank the fiction is explicit about (the
        # SPREAD ending's drive-out: "the side they never painted").
        Part(prim.box(pw, pt * 0.5, ph), at=(0, -pt * 0.25, base_z),
             mat="sign_field", name="panel_face"),
        Part(prim.box(pw, pt * 0.5, ph), at=(0, pt * 0.25, base_z),
             mat="plank", name="panel_back"),
        Part(prim.box(rail_w, rail_h * 0.8, rail_h), at=(0, fy, top_z - rail_h),
             mat="plank", name="rail_top"),
        Part(prim.box(rail_w, rail_h * 0.7, rail_h * 0.8),
             at=(0, fy, base_z - rail_h * 0.2),
             mat="plank", name="rail_bottom"),
        *[Part(prim.box(stile_w, rail_h * 0.55, ph - rail_h * 2.0),
               at=(sx * (pw / 2 - stile_w / 2 + 0.8), fy + 0.1,
                   base_z + rail_h),
               mat="plank", name=f"stile{sx}")
          for sx in (1, -1)],
        *[Part(prim.box(post_t, post_t, post_h), at=(sx * post_x, post_y, 0),
               mat="cedar", name=f"post{sx}")
          for sx in (1, -1)],
        # a shallow pyramid cap so the post end grain is not left open to the
        # weather, which is both what a builder does and what gives the
        # silhouette its two small peaks
        *[Part(prim.frustum(4, post_t * 0.76, 0.2, cap_h, rot=math.pi / 4),
               at=(sx * post_x, post_y, post_h), mat="cedar", name=f"cap{sx}")
          for sx in (1, -1)],
    ]
    inner = pw / 2 - stile_w - 0.6           # the lettering field, inside the frame
    fz0, fz1 = base_z + rail_h * 0.7, top_z - rail_h * 1.1
    if welcome:
        # Three lines, and the town name is the one you read from a moving
        # car, so it takes half the field. The other two are the town's own
        # boast and its founding year (NARRATIVE §1: est. 1894, the world's
        # northernmost corn town) and sit small under it.
        h = fz1 - fz0
        # The NAME takes half the field. It is the only line anybody reads
        # at speed or at distance; the boast and the year are what you find
        # when you stop, and at play zoom they are honest texture.
        lines = [(_SIGN_LINES[0], fz0 + h * 0.46, fz0 + h * 0.95, 0.17),
                 (_SIGN_LINES[1], fz0 + h * 0.25, fz0 + h * 0.40, 0.24),
                 (_SIGN_LINES[2], fz0 + h * 0.04, fz0 + h * 0.19, 0.24)]
    else:
        lines = [(text, fz0 + (fz1 - fz0) * 0.16,
                  fz0 + (fz1 - fz0) * 0.84, 0.18)]
    return Assembly(*parts, overlay=_sign_paint(lines, -inner, inner,
                                                -(pt / 2) - 0.01))


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
