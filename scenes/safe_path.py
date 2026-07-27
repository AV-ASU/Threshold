"""THE SAFE PATH -- the lit spine the town hangs off (TODO #26, DESIGN.md §14).

The middle of the three layers: **interior -> yard -> SAFE PATH <-> lost
spaces**. A path scene is a wide paved road under civic lamps, and it is the
one part of the outdoors that never lies to you. Its arms go where their signs
say, its geometry never rearranges, and nothing on the asphalt moves when you
look away. Garrick has been saying it since 2026-06: *"Stay on the roads.
People who go off the roads come out wrong-side of where they went in."* This
module is that line made into level geometry.

**The road is safe by its GEOMETRY.** Walk the asphalt anywhere, at any hour,
at any evidence count, and the world cannot take you. That is not lamp
coverage doing the work, it is the shape of the thing: the mouth can only open
within `LOST_EDGE_BAND` of a map edge, an arm's end is an EXIT (and an exit
always beats a mouth, `Game._tick_lost_edge`), and a flank edge has no asphalt
anywhere near it. Step off the shoulder into the dark grass at a flank and it
lets go exactly like any other verge. So the rule the player learns is simple
and true: **the road carries you on, everything beside it does not.**

The LAMPS are therefore not the safety, and there are deliberately few of them
(see the lighting note below). They still do real work -- they are what keeps
the verge's dark off the asphalt at the rim, and standing under one makes you
visible to anything hunting, since stealth reads the same `Scene.lit_at`. And
being ELECTRIC (`street_lamp` is in `Scene._ELECTRIC_KINDS`) they go out with
the gensets, so a blackout takes even that away.

**Shapes.** A path scene is built from ARMS -- a subset of "nesw" -- laid out
around one junction at the scene's centre:

    "ns" / "ew"   an **I**: a straight run, two ways on
    "ne" / "es" / "sw" / "wn"   an **L**: the road turns
    "nse" / "sew" / "ewn" / "wns"   a **T**: a junction, three ways on

Every side WITHOUT an arm is a flank, and every flank is a mouth: it gets a
treeline and a `set_lost_edge` into the biome that flank looks like. That is
the whole connection between the two layers, and it needs no special tile --
the road's own shape decides where you can fall out of the world.

**Not too thin** (maintainer). The carriageway is `2*ROAD_HALF+1` tiles of
asphalt with a dashed centre lane, flanked by `SHOULDER` tiles of gravel on
each side: a nine-tile corridor before you even reach the grass. The old
country lane was a three-tile dirt strip in a twelve-tile scene, which read as
a corridor rather than a road you could stand in the middle of.
"""
import math
import random

from scenes.base import Scene, TILE, scatter_forest_band
from entities.decoration import Decoration

# ---- the road's cross-section, in tiles ---------------------------------
ROAD_HALF = 2        # asphalt half-width -> a 5-tile carriageway
SHOULDER = 2         # gravel shoulder each side -> a 9-tile corridor
LAMP_OFF = ROAD_HALF + SHOULDER      # lamp masts stand at the OUTER edge of
                     # the shoulder, where the right-of-way ends and the grass
                     # starts -- not halfway across the gravel.
LAMP_STEP = 11       # tiles between run PAIRS. Read off the maintainer's own
                     # marks (the lane's pairs sit 11 and 12 tiles either side
                     # of its junction), not chosen.
RIVER_BANK = 3       # tiles of open bank kept clear either side of the water,
                     # so the river is SEEN from the road instead of buried
                     # behind the verge growth
VERGE = 10           # how deep the verge growth reaches in from the map edge.
                     # It has to reach nearly to the road corridor: a shallow
                     # band leaves a wide ring of mown-looking lawn between the
                     # shoulder and the treeline, which reads as a golf course
                     # and, worse, as safe ground. The growth thins as it nears
                     # the road, so the gradient does the work.

# ---- WHERE THE LIGHT GOES, and why there is so little of it ------------
# The first cut lit the carriageway end to end, on the theory that the road's
# safety WAS its lamp coverage. It read like an airport runway, and the theory
# was wrong besides: the mouth can only open within LOST_EDGE_BAND of a map
# edge, an arm's end is an EXIT (which always beats a mouth), and a flank edge
# has no asphalt near it. So the road is safe by its GEOMETRY, and a dark
# stretch in the middle of one is safe too.
#
# That frees the lamps to do the job they are actually good at, which is to
# MEAN something. The pattern is the maintainer's, read off marks drawn on a
# capture and generalised in `_lamp_stations`: corners at a junction, facing
# PAIRS every LAMP_STEP down a run, and the ends of a run left dark. Between
# the pairs the road is black and you walk it faster.
#
# The light still does real work: it is what keeps the verge's dark off the
# asphalt at the rim, it makes you VISIBLE to anything hunting (stealth reads
# the same `lit_at`), and because `street_lamp` is an ELECTRIC fixture a
# genset blackout takes even these away.

_AXIS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}
# What a flank's TREELINE is planted with, and therefore which lost space its
# dark opens on. Keyed by the (solid, passable) char pair a scene passes as
# `verge_char`, so the biome you fall into always matches the wall of growth
# you pushed through -- never corn on this side, pine on the other.
_VERGE_LOST = {
    ("T", "p"): "lost_forest",     # pine
    ("C", "A"): "lost_corn",       # dead standing corn
}
_OPPOSITE = {"n": "s", "s": "n", "e": "w", "w": "e"}


def shape_of(arms):
    """'I' / 'L' / 'T' / 'X' for an arm set (the vocabulary, for docs+tests)."""
    a = set(arms)
    if len(a) == 4:
        return "X"
    if len(a) == 3:
        return "T"
    if len(a) == 2:
        return "I" if _OPPOSITE[list(a)[0]] in a else "L"
    return "-"


class SafePath(Scene):
    """A path scene. Built by `build_path`; kept as a class only so the
    junction centre and the arm set stay queryable (tests, the yard/lost
    wiring, and the look tools all want them)."""

    def __init__(self, key, floor, objects, arms, cx, cy, music="outside"):
        super().__init__(key, floor, object_rows=objects, music=music)
        self.arms = "".join(sorted(arms))
        self.junction = (cx, cy)
        self.is_safe_path = True     # the layer marker (never tricked)


def _paint_arm(floor, objects, w, h, cx, cy, side, shoulders, road_set):
    """Lay one arm from the junction out to the edge.

    Run in TWO passes over all the arms: `shoulders=True` lays every arm's
    gravel, then `shoulders=False` lays every arm's asphalt on top. One pass
    per arm would let the LAST arm's shoulder overwrite an earlier arm's
    carriageway, which puts two strips of gravel straight across the middle of
    a junction (the first cut of the T shipped exactly that). Asphalt always
    wins where two arms meet, which is also how a real junction is surfaced.
    """
    dx, dy = _AXIS[side]
    vertical = dx == 0
    steps = (cy + 1 if side == "n" else h - cy if side == "s"
             else cx + 1 if side == "w" else w - cx)
    lo, hi = ((ROAD_HALF + 1, ROAD_HALF + SHOULDER) if shoulders
              else (0, ROAD_HALF))
    for i in range(steps):
        px, py = cx + dx * i, cy + dy * i
        offs = ([o for o in range(-hi, -lo + 1)] + [o for o in range(lo, hi + 1)]
                if shoulders else list(range(-hi, hi + 1)))
        for off in offs:
            tx = px + (off if vertical else 0)
            ty = py + (0 if vertical else off)
            if not (0 <= tx < w and 0 <= ty < h):
                continue
            if shoulders:
                floor[ty][tx] = "d"
            else:
                # The centre lane is only painted OUTSIDE the junction box: a
                # real crossroads has no line running through it, and a dash
                # crossing another dash reads as a mistake.
                in_junction = (abs(tx - cx) <= ROAD_HALF
                               and abs(ty - cy) <= ROAD_HALF)
                if off == 0 and not in_junction:
                    floor[ty][tx] = "Y" if vertical else "-"
                else:
                    floor[ty][tx] = "P"
            objects[ty][tx] = "."          # the road clears whatever was here
            road_set.add((tx, ty))


def _river_tiles(w, h, river):
    """Yield (tx, ty) of the river channel. `river` is (axis, at, width):
    axis 'v' = a north-south channel centred on column `at`, 'h' = east-west
    on row `at`. The channel MEANDERS -- a ruler-straight river reads as a
    canal, and this one is the artery of the whole nightmare (NARRATIVE §2)."""
    axis, at, width = river
    half = width // 2
    for i in range(h if axis == "v" else w):
        bend = int(round(math.sin(i * 0.17) * 2.0 + math.sin(i * 0.061) * 1.6))
        c = at + bend
        for off in range(-half, half + 1):
            if axis == "v":
                yield (c + off, i)
            else:
                yield (i, c + off)


def build_path(key, arms, w, h, *, music="outside", river=None,
               verge_char=("T", "p"), lost=(), seed=1994, exits=(),
               spawns=(), fence_flank=None, lamps=None):
    """Build a safe-path scene.

    `arms`      subset of "nesw" -- see the shape vocabulary above.
    `river`     ('v'|'h', at, width) -- a water channel through the scene.
                Where a road arm crosses it the road becomes a BRIDGE.
    `verge_char` (solid, passable) chars for the flank treeline; ('C','A')
                for corn, ('T','p') for pine.
    `lost`      ((sides, lost_scene_key), ...) -- the flanks that are mouths.
    `exits`     ((side, char, target, spawn_id), ...) -- one per arm.
    `spawns`    ((name, side_or_None), ...) -- named at each arm's inner end.
    `lamps`     ((tx, ty), ...) -- place the masts EXACTLY here and nowhere
                else, overriding the derived rhythm. Lamp placement is a thing
                the maintainer art-directs on a screenshot, and a derived
                rhythm that looks reasonable is not the same as the one that
                was asked for; `tools/screen_to_world.py` turns marks on a
                capture into this list. A scene nobody has directed keeps the
                default.
    """
    cx, cy = w // 2, h // 2
    floor = [["g"] * w for _ in range(h)]
    objects = [["."] * w for _ in range(h)]

    # 1. the RIVER first, so the road can bridge it rather than erase it
    river_set = set()
    if river is not None:
        for tx, ty in _river_tiles(w, h, river):
            if 0 <= tx < w and 0 <= ty < h:
                river_set.add((tx, ty))
                floor[ty][tx] = "~"
                # See-over solid (the pond precedent, scenes/lost_space.py):
                # the water blocks the body but not the sight cone, so the far
                # bank is visible across it and the river reads as the barrier
                # the fiction says it is without an invisible wall.
                objects[ty][tx] = "x"
        # a mud bank either side, so the water is not a stripe laid on lawn
        for tx, ty in list(river_set):
            for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = tx + ax, ty + ay
                if (0 <= nx < w and 0 <= ny < h
                        and (nx, ny) not in river_set):
                    floor[ny][nx] = ";"

    # 2. the ROAD, which overwrites the river where it crosses it. Gravel
    #    first for every arm, then asphalt for every arm on top (see
    #    _paint_arm) so a junction is surfaced, not quartered.
    road_set = set()
    for shoulders in (True, False):
        for side in arms:
            _paint_arm(floor, objects, w, h, cx, cy, side, shoulders, road_set)

    # 3. the BRIDGE: every river tile the road took gets planks. This spans the
    #    WHOLE corridor including the gravel shoulders, and the deck is paved
    #    across its full width -- a shoulder is still part of the road, so a
    #    deck that stopped at the asphalt would leave two dirt strips walking
    #    over open water either side of the planks (which is exactly what the
    #    first cut of this shipped).
    bridge = []
    for (tx, ty) in sorted(river_set):
        if floor[ty][tx] in ("P", "Y", "-", "d"):
            floor[ty][tx] = "P" if floor[ty][tx] == "d" else floor[ty][tx]
            bridge.append((tx, ty))
    for (tx, ty) in bridge:
        objects[ty][tx] = "$"

    # 4. the TREELINE on every flank -- the dark past the last lamp
    flanks = [s for s in "nesw" if s not in arms]

    def _dilate(src, r):
        out = set()
        for tx, ty in src:
            for ax in range(-r, r + 1):
                for ay in range(-r, r + 1):
                    out.add((tx + ax, ty + ay))
        return out

    road_dilated = _dilate(road_set, 1)
    river_dilated = _dilate(river_set, RIVER_BANK) if river_set else set()

    def _protected(tx, ty):
        """Ground the verge growth must not touch.

        It is derived from the tiles the road ACTUALLY covers, dilated by one
        so the lamp masts and kerb stay clear. The first cut protected whole
        columns and rows keyed off which arms existed, which on an L or a T
        cleared a lane straight across the half of the scene the road never
        reaches -- a bare grass corridor running off into the trees toward
        nothing, on every non-I path.

        The RIVER is protected out to RIVER_BANK tiles either side as well:
        at full verge density the trees close over the water and bury it, and
        the whole point of routing a path along the river is that you can see
        it from the road."""
        if (tx, ty) in road_dilated:
            return True
        return (tx, ty) in river_dilated

    if flanks:
        # Dense on purpose. The verge is the WALL the road runs between, and
        # at the old 0.52 it read as a thin scatter of weeds on a lawn rather
        # than a field you have to push into. scatter_forest_band's de-clump
        # passes guarantee it stays permeable, so density costs nothing but
        # the look -- and the look is the whole point of a verge you are meant
        # to hesitate before stepping into.
        scatter_forest_band(floor, objects, w, h, depth=VERGE, seed=seed,
                            tree_density=0.78, passable_ratio=0.5,
                            bush_density=0.10,
                            solid_char=verge_char[0],
                            passable_char=verge_char[1],
                            protected=_protected)

    sc = SafePath(key, ["".join(r) for r in floor],
                  ["".join(r) for r in objects], arms, cx, cy, music=music)
    sc._river_tiles = river_set
    sc._bridge_tiles = set(bridge)
    _rail_the_deck(sc, set(bridge), road_set)

    # 5. EXITS at each arm's outer end, spanning the WHOLE corridor -- both
    #    shoulders as well as the asphalt. The arm's edge is also a mouth
    #    (below), and `_tick_lost_edge` lets an exit tile win; if the exit
    #    covered only the carriageway, hugging the shoulder on your way out
    #    would drop you into a lost space instead of carrying you onward.
    #    The road takes you on; the grass beside it takes you.
    for side, ch, target, spawn_id in exits:
        objs = [list(r) for r in sc.objects]
        dx, dy = _AXIS[side]
        for off in range(-(ROAD_HALF + SHOULDER), ROAD_HALF + SHOULDER + 1):
            if dx == 0:
                tx, ty = cx + off, (0 if side == "n" else h - 1)
            else:
                tx, ty = (0 if side == "w" else w - 1), cy + off
            objs[ty][tx] = ch
        sc.objects = objs
        sc.add_exit(ch, target, spawn_id)

    # 6. SPAWNS. `side` names the ARM YOU CAME IN THROUGH, so the spawn sits
    #    two tiles inside THAT edge, on the crown of the road -- you arrive
    #    where you walked in, facing down the road, never straddling the seam
    #    and never standing on the exit tile you would immediately re-trigger.
    sc.set_spawn("default", cx, cy)
    _EDGE_SPAWN = {"w": (2, cy), "e": (w - 3, cy),
                   "n": (cx, 2), "s": (cx, h - 3)}
    for name, side in spawns:
        sc.set_spawn(name, *(_EDGE_SPAWN[side] if side else (cx, cy)))

    # 7. the LAMPS. Poles alternate shoulders every LAMP_STEP tiles so their
    #    pools overlap into one unbroken lit band down the carriageway. This
    #    is the mechanism, not the mood: an unlit stretch of road is a stretch
    #    where the flank's mouth reaches the asphalt.
    stations = ([(tx, ty, "!") for tx, ty in lamps] if lamps is not None
                else _lamp_stations(sc, w, h, cx, cy, arms))
    for tx, ty, _s in stations:
        if sc.floor[ty][tx] in ("P", "Y", "-"):
            raise ValueError(f"{key}: lamp at ({tx},{ty}) stands on the "
                             "carriageway. A mast belongs on the shoulder.")
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "street_lamp"))
    # 8. a busted fence line along one flank shoulder, so the verge reads as
    #    the edge of somebody's field rather than more road
    if fence_flank:
        _fence_flank(sc, w, h, cx, cy, fence_flank, seed)

    # 9. THE MOUTHS. EVERY side of a path is a way out of the world, arms
    #    included: the grass either side of an arm's end is just as dark as a
    #    flank's, and the road exit wins where it is laid (step 5). So the rule
    #    the player learns is the true one -- the asphalt carries you on,
    #    everything beside it lets go.
    #
    #    WHICH biome is a RULE, not a per-scene decision, because the one thing
    #    that must never happen is falling off a wall of dead corn and landing
    #    in a pine wood. A FLANK opens on whatever its verge is planted with;
    #    an ARM's end opens on the endless ROAD, because what you stepped off
    #    was a roadside. `lost=` overrides a specific side when the geography
    #    wants something else.
    auto = {}
    for s in "nesw":
        auto[s] = "lost_road" if s in arms else _VERGE_LOST[verge_char]
    for sides, lost_key in lost:
        for s in sides:
            auto[s] = lost_key
    for s in "nesw":
        sc.set_lost_edge(s, auto[s])
    return sc


def _rail_the_deck(sc, bridge, road_set):
    """Run a timber parapet down both exposed edges of a bridge deck.

    A deck tile's edge is EXPOSED where its neighbour is not road -- which is
    the water either side of the crossing, and never the banks at the deck's
    two ends (those are road, so the rail correctly stops where the bridge
    does). Deriving it from the neighbours rather than the road's axis means
    it works whichever way the river runs and whichever arm crosses it."""
    for (tx, ty) in sorted(bridge):
        for ax, ay in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            if (tx + ax, ty + ay) in road_set:
                continue
            # the parapet sits at the tile's outer lip, running PERPENDICULAR
            # to the way it faces (a rail on the north lip runs east-west)
            sc.add_decoration(Decoration(
                tx * TILE + 16 + ax * (TILE // 2),
                ty * TILE + 16 + ay * (TILE // 2),
                "bridge_rail", run="h" if ay else "v", len=TILE))


def _lamp_stations(sc, w, h, cx, cy, arms):
    """(tx, ty, side) for each lamp mast, in the pattern the maintainer drew.

    THE PATTERN, read off eight X's marked on a capture of the country lane
    (`tools/screen_to_world.py` turned them into tiles) and generalised so
    every road in the network is lit the same way:

    * **THE JUNCTION IS LIT AT ITS CORNERS, never at its centre.** A mast goes
      in each corner that lies BETWEEN TWO ARMS, so the poles flank the mouth
      of the side road rather than standing in the crossing. On a side with no
      arm at all there is nothing to flank, so that shoulder takes a single
      mast on the centreline instead -- it closes the junction's fourth side
      without lighting a road that is not there.
    * **THE RUNS ARE LIT IN PAIRS**, one on each shoulder facing each other,
      every `LAMP_STEP` tiles out from the junction. Pairs rather than a
      stagger: a stagger is what the derived rhythm did before the marks
      arrived, and the marks are unambiguous that the long runs come in twos
      (cols 10 and 33 of the lane both carry a mast on each shoulder).
    * **THE ENDS OF A RUN GO DARK.** The last pair falls where the stride
      falls; nothing is added to light the way out. A road that fades into
      unlit distance is the point.

    Masts sit on the OUTER edge of the shoulder (`LAMP_OFF`), where the
    right-of-way ends and the grass starts.

    **NO MAST EVER STANDS ON THE CARRIAGEWAY.** A lamp post in the middle of
    a road is a thing you would swerve around in a car and walk into on foot,
    and it is the first thing anybody notices. Every station is pushed
    outward until its tile is not asphalt, and dropped if it cannot get
    clear. Guarded by `tests/flow.py` §34.
    """
    out = []
    # 1. THE JUNCTION: corners between two arms, and a single mast centred on
    #    any side that has no arm to flank.
    for a, b, qx, qy in (("n", "e", 1, -1), ("n", "w", -1, -1),
                         ("s", "e", 1, 1), ("s", "w", -1, 1)):
        if a in arms and b in arms:
            out.append((cx + qx * LAMP_OFF, cy + qy * LAMP_OFF, "*"))
    for side in "nesw":
        if side in arms:
            continue
        dx, dy = _AXIS[side]
        out.append((cx + dx * LAMP_OFF, cy + dy * LAMP_OFF, "*"))
    # 2. THE RUNS: a facing PAIR every LAMP_STEP tiles out along each arm.
    for side in sorted(arms):
        dx, dy = _AXIS[side]
        vertical = dx == 0
        steps = (cy + 1 if side == "n" else h - cy if side == "s"
                 else cx + 1 if side == "w" else w - cx)
        for i in range(LAMP_STEP, steps, LAMP_STEP):
            px, py = cx + dx * i, cy + dy * i
            for off in (LAMP_OFF, -LAMP_OFF):
                tx = px + (off if vertical else 0)
                ty = py + (0 if vertical else off)
                if 0 <= tx < w and 0 <= ty < h:
                    out.append((tx, ty, side))
    # OFF THE ROAD, structurally. A station derived from ITS OWN arm's
    # cross-axis can still land on ANOTHER arm's carriageway where the two
    # cross, so rather than tuning the stride until that stops happening,
    # every mast is pushed outward along its own offset until the tile under
    # it is not asphalt. Placement cannot produce a pole in the road.
    seen, uniq = set(), []
    for tx, ty, side in out:
        if not (0 <= tx < w and 0 <= ty < h):
            continue
        ox = 0 if tx == cx else (1 if tx > cx else -1)
        oy = 0 if ty == cy else (1 if ty > cy else -1)
        for _push in range(SHOULDER + 2):
            if sc.floor[ty][tx] not in ("P", "Y", "-"):
                break
            ntx, nty = tx + ox, ty + oy
            if not (0 <= ntx < w and 0 <= nty < h):
                break
            tx, ty = ntx, nty
        if (tx, ty) in seen or sc.floor[ty][tx] in ("P", "Y", "-"):
            continue                  # still stuck on asphalt: drop it
        seen.add((tx, ty))
        uniq.append((tx, ty, side))
    return uniq


def _fence_flank(sc, w, h, cx, cy, side, seed):
    """A busted fence line along ONE flank's outer shoulder, so that verge
    reads as the edge of somebody's field rather than more road.

    The fence runs PERPENDICULAR to the side it is on -- a south fence is a
    line running east-west along the south shoulder. Getting that backwards
    (which the first cut did, by reusing the arm code's `vertical` flag) puts
    a fence straight down the middle of the carriageway."""
    rng = random.Random(seed ^ 0x5f)
    dx, dy = _AXIS[side]
    along_x = dx == 0            # a N/S flank's fence runs along the X axis
    span = w if along_x else h
    for i in range(2, span - 2, 2):
        if rng.random() < 0.3:
            continue                    # gaps: the fence is long past keeping
        if along_x:
            tx, ty = i, cy + dy * (LAMP_OFF + SHOULDER)
        else:
            tx, ty = cx + dx * (LAMP_OFF + SHOULDER), i
        if not (0 <= tx < w and 0 <= ty < h):
            continue
        if sc.char_object_at(tx * TILE + 16, ty * TILE + 16) != ".":
            continue
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "chain_fence",
                                     yaw=0.0 if along_x else math.pi / 2))


# =========================================================================
# THE SHIPPING NETWORK
#
# Three segments east and north of town, one of each shape, forming a loop
# with the two roads that were already there:
#
#     brimley --W-- [country_lane  I ] --E-- arrival_road -- lodge_yard
#                          |  (no arm: both flanks are mouths)
#     brimley --S-- [gravel_road_north] --W-- [river_bend L] --S--
#                                                   |
#                                            [river_road  I ]
#
# `river_road` runs NORTH with the river off its east shoulder the whole way
# (the maintainer's "we need the river seen in the safe paths"), and
# `river_bend` is where the road turns east and CROSSES it on the planks.
# =========================================================================

def build_river_road():
    """The **I**: a straight run north along the water.

    The river is off the east shoulder for the entire length -- close enough
    to hear, far enough that the lamps still own the road. It is the segment
    that makes the safe path legible as a place rather than a corridor: you
    always know which way is downstream, so you always know which way is town.
    The west flank is pine going black, and that flank is the mouth.

    IT IS ALSO WHERE THE PREACHER ENDS UP. The doom takes Reverend Crane out
    of his church and down the water after his flock, and this is the length
    of bank the road runs beside, so this is where the PI finds him. The bank
    also gives STONES (the distraction verb), and a hidden doorway in the
    pines on the west flank goes through to the burn clearing.
    """
    sc = build_path(
        "river_road", "ns", 30, 46,
        river=("v", 22, 3),
        verge_char=("T", "p"),
        exits=(("s", "a", "country_lane", "from_river_road"),
               ("n", "e", "river_bend", "from_river_road")),
        spawns=(("from_country_lane", "s"), ("from_river_bend", "n")),
        seed=1471)
    _river_stones(sc)
    _preacher_bank(sc)
    _clearing_doorway(sc)
    return sc


def _clearing_doorway(sc):
    """THE HIDDEN WAY THROUGH, in the pines on the west flank.

    The burn site is a glade off this stretch of bank and there is no road to
    it: what there is is a tree you can walk through (`j`, the passable-tree
    doorway char), somewhere down the dark side of the run. It draws as an
    ordinary trunk, which is the entire reason it stays hidden -- the flank
    is a wall of them.

    Chosen by scan rather than by tile number so it survives a reseed: the
    first solid verge trunk with open ground behind it, a third of the way up
    the run, well away from either arm's exit.
    """
    row = int(sc.h * 0.42)
    for col in range(1, 7):
        if sc.objects[row][col] != "T":
            continue
        if sc.objects[row][col - 1] in (".", "p") or col == 1:
            objs = [list(r) for r in sc.objects]
            objs[row][col] = "j"
            sc.objects = objs
            sc.add_exit("j", "clearing", "from_river_road")
            sc.set_spawn("from_clearing", col + 1, row)
            return


def _river_stones(sc, rows=(6, 14, 22, 30, 38)):
    """The river gives stones. One per listed row, alternating banks, never on
    the deck. Scanned rather than hand-placed because the channel meanders."""
    for i, row in enumerate(rows):
        if not (0 <= row < sc.h):
            continue
        wet = sorted(c for c in range(sc.w) if (c, row) in sc._river_tiles)
        if not wet:
            continue
        c = (min(wet) - 1) if i % 2 == 0 else (max(wet) + 1)
        if not (0 <= c < sc.w):
            continue
        x, y = c * TILE + 16, row * TILE + 16
        if sc.floor[row][c] not in ("~", "@") and not sc.is_solid_at(x, y):
            sc.add_item(x, y, "stone")


def _preacher_bank(sc):
    """THE PREACHER'S END, laid on the bank every entry once he is doomed.

    He leaves his own church to talk his flock home and is found down here,
    never on his own floor (NARRATIVE §5). Walking up on the remains sets
    `preacher_body_seen`, the flag Sheriff Vane's and Garrick's beats read.
    """
    from .dialogue import preacher_body_examine
    from entities.npc import NPC
    # the west bank, a third of the way up: off the shoulder, on the mud,
    # where the road can see him but only if it looks that way.
    row = int(sc.h * 0.62)
    wet = sorted(c for c in range(sc.w) if (c, row) in sc._river_tiles)
    col = (min(wet) - 1) if wet else sc.w - 4
    sc._preacher_bank_pos = (col * TILE + 16, row * TILE + 16)

    def _on_enter(game, scene):
        if not game.save.flag("preacher_doomed"):
            return
        bx, by = scene._preacher_bank_pos
        scene.add_decoration(Decoration(bx - 6, by + 9, "bloodstain"))
        scene.add_decoration(Decoration(bx + 9, by - 6, "gore"))
        scene.add_decoration(Decoration(bx, by, "body"))
        scene.add_npc(NPC(bx, by, "The Preacher", "_invisible",
                          voice="blip_soft", portrait="narrator",
                          dialogue_fn=preacher_body_examine,
                          movement="idle", solid=True, tag="preacher_body"))

    def _on_update(game, scene, dt):
        """Finding the body counts on SIGHT, not only on the E-press: walking
        up on the remains sets `preacher_body_seen`, the flag Sheriff Vane's
        and Hettie's murder one-shots key on (they can never announce a
        killing the player hasn't found)."""
        if (game.save.flag("preacher_doomed")
                and not game.save.flag("preacher_body_seen")):
            bx, by = scene._preacher_bank_pos
            if (abs(game.player.x - bx) < 110
                    and abs(game.player.y - by) < 110):
                game.save.set_flag("preacher_body_seen", True)

    sc.on_enter_fn = _on_enter
    sc.on_update_fn = _on_update


def build_river_bend():
    """The **L**: the road turns east and crosses the water.

    The corner sits on the west bank; the east arm runs out over the planks
    to the north road. Standing at the turn you can see both: the run you
    came up, and the bridge you are about to take. Both flanks are mouths --
    north into the dead corn, west into the pines.

    And UNDER the planks is the one rooted hide on the whole network. The
    town crosses this bridge sooner or later, and while you are tucked
    beneath it whatever crosses knocks on the deck over your head
    (`Game._tick_bridge_knocks`). Dressing, not threat: the searchers up top
    neither know you are down there nor come looking. The dread is hearing
    the place walk over you while you wait it out.
    """
    sc = build_path(
        "river_bend", "se", 36, 32,
        river=("v", 25, 3),
        verge_char=("T", "p"),
        exits=(("s", "a", "river_road", "from_river_bend"),
               ("e", "e", "gravel_road_north", "from_river_bend")),
        spawns=(("from_river_road", "s"), ("from_gravel_road_north", "e")),
        seed=1483)
    sc.add_decoration(Decoration(sc.junction[0] * TILE + 16,
                                 (sc.junction[1] - LAMP_OFF - 2) * TILE + 16,
                                 "creepy_tree"))
    _river_stones(sc, rows=(4, 10, 26, 30))
    _bridge_hide(sc)
    return sc


def _bridge_hide(sc):
    """Cut the mud shelf under the deck's downstream lip and register it.

    Derived from the deck the builder actually laid, so it works whichever
    way the river runs and whichever arm crosses it. The shelf is carved on
    the FAR side of the channel only -- carve the full width and the shelf
    becomes a ford, and the river is meant to be a barrier.
    """
    deck = sorted(getattr(sc, "_bridge_tiles", ()) or ())
    if not deck:
        return
    cols = sorted({t[0] for t in deck})
    rows = sorted({t[1] for t in deck})
    # The deck's LIP is the long side: a road crossing a north-south river
    # spans few columns over many rows, so the lip runs east-west.
    lip_row = rows[-1] + 1
    if not (0 <= lip_row < sc.h):
        return
    wet = sorted(c for c in range(sc.w) if (c, lip_row) in sc._river_tiles)
    if len(wet) < 2:
        return
    shelf = wet[1:]                       # leave the near column as water
    _fl = [list(r) for r in sc.floor]
    _ob = [list(r) for r in sc.objects]
    for c in shelf:
        _fl[lip_row][c] = ";"
        _ob[lip_row][c] = "."
    sc.floor = ["".join(r) for r in _fl]
    sc.objects = ["".join(r) for r in _ob]
    hx, hy = shelf[-1] * TILE + 16, lip_row * TILE + 16
    sc.hide_spots = list(getattr(sc, "hide_spots", []) or [])
    sc.hide_spots.append((hx, hy, "under"))
    sc._bridge_hide_px = (hx, hy)
    sc._bridge_deck_px = (cols[0] * TILE, (cols[-1] + 1) * TILE,
                          rows[0] * TILE, (rows[-1] + 1) * TILE)


def build_country_lane():
    """The **X**: the junction east of town, and the busiest piece of road
    in the game.

    West is the gravel road and the town's streets beyond it, east is the
    arrival road and the Lodge, north is the river run, and SOUTH is the
    corn. It is the first safe path most players walk and the one that
    teaches the layer: a real paved road with a centre line, and last year's
    uncut stand (NARRATIVE §3) standing right up to the shoulder.

    The south arm is the way into the maze, and the way out of it: the corn
    belt hangs off the network HERE, at the one junction the corn already
    grew up to. It came off Brimley when Brimley was retired (DESIGN.md §15),
    and it belongs here better than it belonged there -- the road running out
    into a standing field is a legible thing to be handed, and the field
    handing you back to the same road is the whole joke of the maze.

    Carried over from the old lane: the bootprints of the locals who walked
    east to flag down help and simply stopped, the missing flyer, and the two
    noise traps out on the verge.
    """
    W, H = 42, 34
    sc = build_path(
        "country_lane", "wens", W, H,
        verge_char=("C", "A"),
        exits=(("w", "a", "gravel_road_north", "from_country_lane"),
               ("e", "e", "arrival_road", "from_country_lane"),
               ("n", "^", "river_road", "from_country_lane"),
               ("s", "4", "cornfield_maze", "from_country_lane")),
        spawns=(("from_gravel_road_north", "w"), ("from_arrival_road", "e"),
                ("from_lodge_yard", "e"), ("from_river_road", "n"),
                ("from_cornfield_maze", "s"), ("from_cornfield_path", "s")),
        # ART-DIRECTED (maintainer marked these on a capture; read back with
        # tools/screen_to_world.py). Masts sit on the OUTER shoulder edge and
        # STAGGER between the two sides rather than pairing off across the
        # road, so the lane reads as a county road somebody lit one pole at a
        # time and not as an avenue. Nothing at the junction itself -- two
        # flank it instead, which points at the crossing without standing in
        # it.
        #
        # The south-shoulder middle mast MOVED when the south arm landed: it
        # stood on (21,21), which is the centre column, so the new arm put a
        # lamp post in the middle of the carriageway (`build_path` refuses
        # it, loudly). It is now the pair of corners flanking the new arm's
        # mouth, which is what the pattern does everywhere else.
        lamps=((10, 13), (17, 13), (24, 13), (33, 13),     # north shoulder
               (10, 21), (33, 21),                         # south shoulder
               (17, 21), (25, 21),                         # the south mouth
               (25, 3), (17, 30)),                         # up each long arm
        seed=2028)
    cx, cy = sc.junction

    # THE WALKED-OUT ROAD. The locals who set off east to flag down help left
    # prints along the shoulder that head that way and simply stop, well short
    # of the seam. Kept from the old lane; re-laid onto the new shoulder.
    for i, fx in enumerate(range(cx + 4, cx + 13, 3)):
        sc.add_decoration(Decoration(fx * TILE + 16,
                                     (cy + ROAD_HALF + 1) * TILE + 16,
                                     "mud_footprint"))
    sc.add_decoration(Decoration((cx - 7) * TILE + 16,
                                 (cy + LAMP_OFF + 2) * TILE + 16,
                                 "missing_flyer"))
    # Roadside life, such as it is: crows on the corn, one dead on the asphalt.
    sc.add_decoration(Decoration((cx - 11) * TILE + 8,
                                 (cy - LAMP_OFF - 3) * TILE + 22, "crow"))
    sc.add_decoration(Decoration((cx + 9) * TILE + 8,
                                 (cy + LAMP_OFF + 4) * TILE + 22, "crow"))
    sc.add_decoration(Decoration((cx + 2) * TILE + 16, cy * TILE + 20,
                                 "dead_crow"))
    sc.add_decoration(Decoration((cx - 13) * TILE + 16,
                                 (cy - LAMP_OFF - 4) * TILE + 16,
                                 "creepy_tree"))
    # Noise traps out on the verge, on the cover lanes rather than the road.
    sc.add_noise_trap((cx + 7) * TILE + 16, (cy + LAMP_OFF + 3) * TILE + 16,
                      "plank", seed=25)
    sc.add_noise_trap((cx - 9) * TILE + 16, (cy - LAMP_OFF - 3) * TILE + 16,
                      "cans", seed=26)
    for lx, ly in ((cx - 5, cy + LAMP_OFF + 1), (cx + 6, cy - LAMP_OFF - 1)):
        sc.add_decoration(Decoration(lx * TILE + 16, ly * TILE + 16, "leaves"))
    sc.hide_spots = []
    return sc


# The town's own streets. Brimley is being replaced by a STRING OF HOUSE
# ISLANDS in a sea of spatial manipulation (the maintainer's shape for it), so
# these are the string: ordinary safe paths whose arms end at yards instead of
# at more road. Each street grows L -> T -> X as households land on it, so one
# street serves several doors while every yard behind it stays its own.
#
#   gravel_road_north --E-- [store_row  X] --N-- shop_yard
#                                 |  |E---------- school_yard
#                                 S
#                           [chapel_row X] --W-- church_yard
#                                 |  |E---------- barn_yard
#                                 S
#                            [south_row X] --W-- sheriff_yard
#                                 |  |E---------- farm_yard
#                                 S
#                             [bank_row X] --W-- toby_yard
#                                 |  |E---------- calder_yard
#                                 S
#                             [lane_end T] --W-- royce_yard
#                                    |E---------- garrick_yard


def build_chapel_row():
    """The **X** below the store: the church one way, the barn the other."""
    return build_path(
        "chapel_row", "nswe", 36, 36,
        verge_char=("T", "p"),
        exits=(("n", "4", "store_row", "from_chapel_row"),
               ("s", "^", "south_row", "from_chapel_row"),
               ("w", "e", "church_yard", "from_chapel_row"),
               ("e", "a", "barn_yard", "from_chapel_row")),
        spawns=(("from_store_row", "n"), ("from_south_row", "s"),
                ("from_church_yard", "w"), ("from_barn_yard", "e")),
        seed=2043)


def build_south_row():
    """The **X** at the bottom of town: the law one way, the empty farmhouse
    the other. The two yards on it disagree about everything."""
    return build_path(
        "south_row", "nswe", 36, 36,
        verge_char=("C", "A"),
        exits=(("n", "4", "chapel_row", "from_south_row"),
               ("s", "^", "bank_row", "from_south_row"),
               ("w", "e", "sheriff_yard", "from_south_row"),
               ("e", "a", "farm_yard", "from_south_row")),
        spawns=(("from_chapel_row", "n"), ("from_bank_row", "s"),
                ("from_sheriff_yard", "w"), ("from_farm_yard", "e")),
        seed=2047)


def build_bank_row():
    """The **X** on the near bank: the kid's house one way, Mrs. Calder's the
    other, and they are neighbours because the layer says so rather than
    because a map ran out of room."""
    return build_path(
        "bank_row", "nswe", 36, 36,
        verge_char=("T", "p"),
        exits=(("n", "4", "south_row", "from_bank_row"),
               ("s", "^", "lane_end", "from_bank_row"),
               ("w", "e", "toby_yard", "from_bank_row"),
               ("e", "a", "calder_yard", "from_bank_row")),
        spawns=(("from_south_row", "n"), ("from_lane_end", "s"),
                ("from_toby_yard", "w"), ("from_calder_yard", "e")),
        seed=2053)


def build_lane_end():
    """The **X** where the town stops: three lots and no road onward.

    The south arm ends at Old Pell's, and it ends there in every sense -- past
    his gate the string has nothing left on it. The last lit thing before the
    dark takes over is the yard of the man who stopped marking the days.
    """
    return build_path(
        "lane_end", "nwes", 36, 36,
        verge_char=("C", "A"),
        exits=(("n", "4", "bank_row", "from_lane_end"),
               ("w", "e", "royce_yard", "from_lane_end"),
               ("e", "a", "garrick_yard", "from_lane_end"),
               ("s", "^", "pell_yard", "from_lane_end")),
        spawns=(("from_bank_row", "n"), ("from_royce_yard", "w"),
                ("from_garrick_yard", "e"), ("from_pell_yard", "s")),
        seed=2059)


def build_store_row():
    """The **X**: the first of the town's own streets.

    It turns east off the gravel road; the store's gate is north, the school's
    east, and the rest of the string runs on south.
    This is the layer's connective tissue -- SAFE PATH -> YARD -> HOUSE
    (DESIGN.md §15) -- and it is a path like any other, which is the point:
    the walk to somebody's door is on ground that never lies to you, and the
    yard behind the gate is where that stops being true.

    It grows. Each further household on this side of town takes another arm
    (an L becomes a T becomes an X), so the street ends up serving several
    doors while every yard behind it stays its own.

    And it is THE SQUARE: the crossing outside the store is where the town
    kept its public things, so the well, the barrow, the news rack and the
    dead payphone stand here (`_town_square`).
    """
    sc = build_path(
        "store_row", "wnes", 36, 36,
        verge_char=("C", "A"),
        exits=(("w", "4", "gravel_road_north", "from_store_row"),
               ("n", "e", "shop_yard", "from_store_row"),
               ("e", "a", "school_yard", "from_store_row"),
               ("s", "^", "chapel_row", "from_store_row")),
        spawns=(("from_gravel_road_north", "w"), ("from_shop_yard", "n"),
                ("from_school_yard", "e"), ("from_chapel_row", "s")),
        seed=2039)
    _town_square(sc)
    return sc


def _town_square(sc):
    """THE SQUARE: the town's public things, at the crossing outside the store.

    A town keeps its well, its noticeboard and its telephone where everybody
    passes, which in a place this size is one crossroads. They stand in the
    QUADRANTS between the arms -- open kept grass inside the verge line, clear
    of the carriageway and clear of the shoulder, so the square is a place you
    step aside into rather than something laid across the road.

    Three of the four carry a beat (`on_interact_fn`): the well is dread that
    goes nowhere and a stone over its lip is the loud distraction verb, the
    barrow's cleaned tools are the contradiction that files a note, and the
    news rack holds the seal-day issue. The payphone is silent set-dressing.
    """
    from .dialogue import _evidence
    cx, cy = sc.junction
    off = LAMP_OFF + 1                  # clear of the shoulder and its masts

    # WORN GROUND FIRST. Dropped straight onto the kept grass these read as
    # four objects standing on a lawn -- which is what the first cut of this
    # shipped. A square is ground people have STOOD on: the apron under each
    # cluster is beaten to dirt, and it is what makes the well a place rather
    # than a prop.
    _rows = [list(r) for r in sc.floor]

    def _apron(tx0, tx1, ty0, ty1):
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if (0 <= tx < sc.w and 0 <= ty < sc.h
                        and _rows[ty][tx] == "g"
                        and sc.objects[ty][tx] == "."):
                    _rows[ty][tx] = "d"

    _apron(cx - off - 4, cx - off, cy - off - 3, cy - off)
    _apron(cx + off, cx + off + 3, cy - off - 3, cy - off)
    sc.floor = ["".join(r) for r in _rows]

    # THE WELL -- dread set-dressing, fully SEVERED from the descent: nobody
    # went down HERE. The congregation went down the cult's dug mine out at
    # the grove, reached now only by the rite. This is a dead, dry town well
    # gone wrong: ominous, going nowhere. It stands at the crossing's inner
    # corner, where anyone coming through the junction passes within reach.
    wx, wy = (cx - off - 1) * TILE + 16, (cy - off - 1) * TILE + 16
    sc.add_decoration(Decoration(wx, wy, "well"))
    sc._well_pos = (wx, wy)
    # THE BARROW of "rusted" tools, tipped up against the well's lip where
    # the square's shed used to stand. The tools are still bright at the
    # edges: somebody is keeping them, and nobody in town admits to digging.
    bx, by = (cx - off - 3) * TILE + 16, (cy - off - 1) * TILE + 8
    sc.add_decoration(Decoration(bx, by, "wheelbarrow"))
    sc._barrow_pos = (bx, by)
    sc.add_decoration(Decoration((cx - off - 4) * TILE + 20,
                                 (cy - off - 3) * TILE + 18,
                                 "crate_stack", courses=2, seed=17))
    sc.add_decoration(Decoration((cx - off) * TILE + 24,
                                 (cy - off) * TILE + 10, "leaves"))
    # THE NEWS RACK, on the store's side of the crossing (the north arm is
    # the way up to Hettie's gate), still holding the issue it was last fed,
    # with the dead payphone beside it and the town's own sign over the pair.
    nx, ny = (cx + off + 1) * TILE + 16, (cy - off - 1) * TILE + 16
    sc.add_decoration(Decoration(nx, ny, "news_rack"))
    sc._news_rack_pos = (nx, ny)
    px, py = (cx + off + 2) * TILE + 20, (cy - off - 1) * TILE + 12
    sc.add_decoration(Decoration(px, py, "payphone"))
    sc._payphone_pos = (px, py)
    sc.add_decoration(Decoration((cx + off + 3) * TILE + 16,
                                 (cy - off - 3) * TILE + 16,
                                 "town_sign", text="BRIMLEY"))
    sc.add_decoration(Decoration((cx + off) * TILE + 12,
                                 (cy - off) * TILE + 20, "missing_flyer"))
    sc.add_decoration(Decoration((cx + off + 2) * TILE + 8,
                                 (cy + off) * TILE + 22, "dead_crow"))
    sc.add_decoration(Decoration((cx - off - 2) * TILE + 16,
                                 (cy + off + 1) * TILE + 16, "creepy_tree"))

    def _square_interact(game):
        px_, py_ = game.player.x, game.player.y
        if abs(px_ - wx) < 36 and abs(py_ - wy) < 36:
            if (game.save.flag("well_examined")
                    and game.player.inventory.count("stone") > 0):
                # A stone over the lip: the knocks fall away, the shaft's
                # rattle carries across the square -- and no bottom ever
                # sounds. WORDLESS by design (the missing landing IS the
                # beat; the well stays the bottomless dread it is).
                game.player.inventory.remove("stone", 1)
                game.audio.play("bump", 0.5)
                game._echoes.extend([
                    {"t": 0.35, "x": wx, "y": wy, "vol": 0.34},
                    {"t": 0.80, "x": wx, "y": wy, "vol": 0.22, "emit": True},
                    {"t": 1.45, "x": wx, "y": wy, "vol": 0.12},
                ])
                return
            if not game.save.flag("well_examined"):
                game.save.set_flag("well_examined", True)
                game.audio.play("low_pulse", 0.4)
                game.dialog.show([
                    "[c=dim](You lean over the lip. The shaft drops "
                    "past where any water should be. No glint, no "
                    "bottom, just cold air climbing up out of it.)[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            game.audio.play("low_pulse", 0.4)
            game.show_notice("Cold air climbs out of the dark. No way "
                             "down for you here.")
            return
        if abs(px_ - bx) < 36 and abs(py_ - by) < 36:
            if not game.save.flag("barrow_inspected"):
                game.save.set_flag("barrow_inspected", True)
                _evidence(game, "barrow_tools",
                          "Digging tools left in the barrow, rusted over. "
                          "The edges are still bright.")
            return
        if abs(px_ - nx) < 36 and abs(py_ - ny) < 36:
            game.audio.play("blip_low", 0.4)
            game.dialog.show([
                "A coin rack of newspapers, bleached behind the scratched "
                "plastic. The county weekly.",
                "[c=dim]Dated January 15. Every copy in the stack. Nobody "
                "ever fed it another.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return

    sc.add_interactable(wx, wy, 36)
    sc.add_interactable(bx, by, 36)
    sc.add_interactable(nx, ny, 36)
    sc.on_interact_fn = _square_interact
    # THE CULT'S ERRAND at the square is to look in on the well (the JOBS
    # layer, `Scene.add_cult_station`). It is the same errand they ran when
    # this was the middle of the town map, and it is still the reason a
    # hooded figure is standing at a dry shaft.
    sc.add_cult_station(wx + TILE, wy, face=(-1, 0), dwell=(4.0, 7.0))
    # And the ground around it is not quiet ground: a spilled crate of
    # bottles at the barrow and a strung line of cans in the far verge.
    sc.add_noise_trap(bx - TILE, by + 8, "glass", seed=8)
    sc.add_noise_trap((cx + off + 2) * TILE + 16,
                      (cy + off + 2) * TILE + 16, "cans", seed=9)


def build_gravel_road_north():
    """The **X** north of town: the country lane south, the backwoods north,
    the river bend west and the town's own streets east.

    The last of the old three-tile dirt roads to get the path treatment. It
    keeps its gravel identity -- the shoulders read wider and looser here than
    on the lane, and the pines come right down to them -- but it is the same
    corridor and the same lamp pattern as the rest of the network, because a
    road that is safe in one scene and a footpath in the next teaches nothing.

    Carried over from the thin version: the boarded panel set into the east
    treeline (a chop-target onto a long-looted alcove), the two pines, the
    crows, and the phantom mark on the road.
    """
    W, H = 32, 36
    sc = build_path(
        "gravel_road_north", "nsew", W, H,
        verge_char=("T", "p"),
        exits=(("s", "a", "country_lane", "from_gravel_road_north"),
               ("n", "e", "backwoods_cabin", "from_road"),
               ("w", "^", "river_bend", "from_gravel_road_north"),
               # THE TOWN TURNING. The T became an X when the town's own
               # streets started hanging off the network (DESIGN.md §15):
               # its east flank was the only side of any shipped path with
               # no road already on it.
               ("e", "4", "store_row", "from_gravel_road_north")),
        spawns=(("from_country_lane", "s"), ("from_backwoods_cabin", "n"),
                ("from_river_bend", "w"), ("from_store_row", "e")),
        seed=2031)
    cx, cy = sc.junction
    # THE BOARDED PANEL, still in the east treeline: nailed planks over a
    # long-looted alcove, chopped through with the axe (`q`, Game._chop_at).
    objs = [list(r) for r in sc.objects]
    objs[cy - 6][cx + LAMP_OFF + 3] = "q"
    sc.objects = objs
    sc.add_decoration(Decoration((cx - LAMP_OFF - 3) * TILE + 16,
                                 (cy - 9) * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration((cx + LAMP_OFF + 4) * TILE + 16,
                                 (cy + 7) * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(cx * TILE + 16, (cy - 7) * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration((cx - 3) * TILE + 16, (cy + 4) * TILE + 20,
                                 "dead_crow"))
    sc.add_decoration(Decoration((cx - LAMP_OFF - 2) * TILE + 8,
                                 (cy - 14) * TILE + 22, "crow"))
    sc.add_decoration(Decoration((cx + LAMP_OFF + 2) * TILE + 8,
                                 (cy + 12) * TILE + 22, "crow"))
    sc.hide_spots = []
    return sc
