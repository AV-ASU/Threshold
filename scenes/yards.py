"""THE YARD LAYER -- a household's own ground, read without anybody speaking.

**SAFE PATH -> YARD -> HOUSE** (`DESIGN.md` §15). A yard is the INNERMOST of
the three layers and it is a SCENE: one building in it, a road exit on one
edge, and that building's door on the other side of the ground you cross. Not
a dressed patch of a bigger map -- the walk from the road to somebody's door
IS the layer, and it only exists if it is a place you travel to. `lodge_yard`
and `backwoods_cabin` were already this shape.

A yard's job is to tell you who lives there and what they stopped doing,
before you knock and without a line of dialogue: the seal was January 15 and
it is April, so three months of stasis is sitting in everyone's back garden.
Every edge that is not the road is a §13 MOUTH -- a yard is the last lit
ground before the world stops caring, and the way you came is the only way
that stays true.

TWO THINGS LIVE HERE.

`build_yard_scene` builds the scene: the footprint, the door, the road exit,
the worn track routed AROUND the house, the verge band, and the lot inside it.

`Yard` is the vocabulary you dress that lot with. It is deliberately thin --
it knows the BUILDING's geometry (its footprint, which face the door is in,
and the walkable tile outside it) and nothing else, so every placement is
expressed against that instead of as a tile number somebody has to keep in
their head:

    sc, y = build_yard_scene("shop_yard", door_face="e", ...)
    y.step()
    y.genset(running=True, side="s")
    y.mailbox(14, 10, full=False)
    y.fence("s", at=y.lot[3], gate=y.out[0])

WHAT a yard says stays a per-household decision written out in the scene,
because the whole point of the layer is that the yards DIFFER. A vocabulary
applied evenly says the same thing about every house in town.

WHY THE PLACEMENT ASSERT. Every yard piece goes through `put`, which refuses a
tile that is the building, the door, or the door's approach. That is playtest
error class #8 (a prop across the way in) turned into a build-time failure
instead of something you find by rendering all four facings and noticing. It
fires while the scene is being built, so a bad placement cannot reach a
capture, let alone a player.
"""
import math
import random

from constants import TILE
from entities.decoration import Decoration
from .dialogue import (CALDER_CONVO, ROYCE_CONVO, GARRICK_CONVO,
                       PELL_CONVO)

# Which way you CLIMB, given the wall the door is in. A stoop's local +x is
# the direction of the climb (rendering/references.py), so this is the stoop's
# yaw -- and, negated, the direction the yard runs away from the house in.
_CLIMB = {"s": -math.pi / 2, "n": math.pi / 2, "e": math.pi, "w": 0.0}
# The outward step from a face, in tiles.
_OUT = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}
# Which yaw runs ALONG a face (a fence line, a woodpile against a wall).
_ALONG = {"n": 0.0, "s": 0.0, "e": math.pi / 2, "w": math.pi / 2}

# One fence bay's own width in world units -- `_yard_fence`'s default. Bays
# are laid END TO END at this, never on a tile multiple: spaced every four
# tiles they leave 86-unit holes between 42-unit bays, which reads as four
# abandoned fence FRAGMENTS rather than one line, and a boundary that is
# mostly hole cannot make a gap mean anything.
BAY = 33.0


# ---------------------------------------------------------------- beat gates
# A chorus beat fires when its condition holds. These are module-level and
# NAMED because a lambda defined inside a builder is the one piece of
# behaviour a layout can never refer to (`scenes/layout.py`): everything else
# is either importable or rebuildable from the factory that made it.
def _beat_calder_unlatched(g):
    return g._evidence_count() >= 1


def _beat_royce_throat(g):
    return g._evidence_count() >= 2


def _beat_garrick_quiet(g):
    return g.save.flag("preacher_body_seen")


def _beat_pell_marked(g):
    return g.save.arg("paper_given") == "pell"


def _beat_pell_coal(g):
    return g._evidence_count() >= 1 and g.save.arg("paper_given") != "pell"


class Yard(object):
    """The ground around one building, and the vocabulary you dress it with.

    `rect` is the building footprint (left, right, top, bot) in tiles,
    inclusive; `face` is the wall its door is in; `out` is the walkable tile
    just outside that door (what `_stamp_building` hands back). `depth` is how
    far the yard reaches out in FRONT of the door and `flank` how far out the
    other three sides -- the front is deeper because the front is what you
    walk up.
    """

    def __init__(self, sc, rect, face, out, depth=4, flank=2, seed=0):
        self.sc = sc
        self.left, self.right, self.top, self.bot = rect
        self.face = face
        self.out = tuple(out)
        self.depth = depth
        self.flank = flank
        self.seed = seed
        # the approach tile: the one square nobody may build on, because it
        # is the only way in
        ox, oy = _OUT[face]
        self.approach = (self.out[0] + ox, self.out[1] + oy)

    # ------------------------------------------------------------ geometry
    def bounds(self):
        """The yard's own tile bounds, deep in front and flanking elsewhere."""
        l, r = self.left - self.flank, self.right + self.flank
        t, b = self.top - self.flank, self.bot + self.flank
        if self.face == "n":
            t = self.top - self.depth
        elif self.face == "s":
            b = self.bot + self.depth
        elif self.face == "e":
            r = self.right + self.depth
        else:
            l = self.left - self.depth
        return (max(0, l), min(self.sc.w - 1, r),
                max(0, t), min(self.sc.h - 1, b))

    def is_building(self, tx, ty):
        return (self.left <= tx <= self.right and self.top <= ty <= self.bot)

    def wall(self, side, along=0.5, out=1):
        """A tile hugging one of the building's walls.

        `along` walks the wall from its low end (0) to its high end (1);
        `out` is how many tiles clear of the wall it stands. This is how a
        genset gets against a gable end or a woodpile against a shed without
        anybody counting tiles.
        """
        if side in ("n", "s"):
            tx = int(round(self.left + along * (self.right - self.left)))
            ty = (self.top - out) if side == "n" else (self.bot + out)
        else:
            ty = int(round(self.top + along * (self.bot - self.top)))
            tx = (self.left - out) if side == "w" else (self.right + out)
        return (tx, ty)

    # ------------------------------------------------------------- placing
    def siding(self, kind, tx, ty, **kw):
        """Hang something on the building's OUTSIDE wall: a `_WALL_DECO` kind,
        which is the one yard piece that is on the house rather than in front
        of it (a chalked door-motif is chalked on the siding).

        The tile is the open one the wall FACES, not the wall itself. A wall
        decoration is drawn at its own position and depth-sorted against the
        walls, so one placed on the wall tile sits inside the wall's own
        volume and is painted over by it -- correct-looking code, nothing on
        screen. `terrain._wall_normal` then reads which side the wall is on
        from these same neighbours.
        """
        if self.is_building(tx, ty):
            raise ValueError(
                "yard %r: %s at (%d,%d) is ON the wall tile. A wall "
                "decoration goes on the open tile the wall faces, or the "
                "wall paints over it." % (self.sc.key, kind, tx, ty))
        if not any(self.is_building(tx + dx, ty + dy)
                   for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
            raise ValueError(
                "yard %r: %s at (%d,%d) has no wall of this building next to "
                "it to hang on" % (self.sc.key, kind, tx, ty))
        d = Decoration(tx * TILE + 16, ty * TILE + 16, kind, **kw)
        self.sc.add_decoration(d)
        return d

    def put(self, kind, tx, ty, ox=16, oy=16, **kw):
        """Place a yard prop at a tile, refusing the three tiles it must not
        take: the building itself, the door, and the door's approach."""
        if self.is_building(tx, ty):
            raise ValueError(
                "yard %r: %s at (%d,%d) is inside the building footprint"
                % (self.sc.key, kind, tx, ty))
        if (tx, ty) in (self.out, self.approach):
            raise ValueError(
                "yard %r: %s at (%d,%d) stands on the way in (the door's "
                "tile or its one approach)" % (self.sc.key, kind, tx, ty))
        d = Decoration(tx * TILE + ox, ty * TILE + oy, kind, **kw)
        self.sc.add_decoration(d)
        return d

    # ---------------------------------------------------------- vocabulary
    def step(self, **kw):
        """A STEP: something between the ground and the door, so going in
        reads as arriving. Sits on the door's own outside tile, climbing in."""
        ox, oy = _OUT[self.face]
        d = Decoration(self.out[0] * TILE + 16 - ox * 6,
                       self.out[1] * TILE + 16 - oy * 6,
                       "stoop", yaw=_CLIMB[self.face], **kw)
        self.sc.add_decoration(d)
        return d

    def genset(self, running=True, side=None, along=0.72, can=True,
               can_tipped=None):
        """THE GENSET, and its state is the household's.

        The grid died with the seal and the town runs on gasoline
        (NARRATIVE §5). Running means a warm work-bulb and a fuel can standing
        beside it: somebody is still keeping the place. Dead means a cold bulb
        and the can empty on its side. `running=False` also passes `broken`,
        which is what BOTH light tables read to stop a fixture emitting, so
        the dark bulb and the dark ground can never disagree.

        It goes against a wall that is NOT the door's -- a genset has to sit
        outside because it breathes, but it does not sit in the doorway.

        `can_tipped` defaults to matching the genset, and is worth setting
        apart where the two disagree: a machine still running beside a can
        already empty is a household about to go dark, and that is a different
        sentence from either half of it.

        **AND THE WINDOWS READ IT.** Lit glass is an assertion that somebody
        is home, and the fiction has buildings that are empty on purpose
        (NARRATIVE §3: the school and the barn the congregation walked out
        of, the farmhouse abandoned in its own name) -- warm panes on those
        quietly unsay the beat you walk in to find. The genset is already the
        household's state, and this town runs on gasoline, so the panes are
        DERIVED from it rather than authored a second time: a machine that is
        running has its lights on, a cold one does not. One source, no way for
        the two to disagree, exactly as `broken` does for the bulb and the
        ground. Guarded by `tests/conventions.py`.
        """
        if side is None:
            side = {"n": "e", "s": "e", "e": "s", "w": "s"}[self.face]
        if can_tipped is None:
            can_tipped = not running
        tx, ty = self.wall(side, along=along)
        self.sc.window_glass = "lit" if running else "dark"
        g = self.put("generator", tx, ty, running=running,
                     broken=not running)
        if can:
            cx, cy = _OUT[side]
            self.put("fuel_can", tx + cx, ty + cy,
                     ox=16 - cx * 4, oy=16 - cy * 4, tipped=can_tipped)
        return g

    def mailbox(self, tx, ty, toward="s", full=True):
        """THE MAIL, out at the road -- exactly where the yard meets the safe
        path. Deliveries stopped with the fold, so a box is either still
        stuffed with January's last one or has hung open ever since.
        `toward` is the side the carrier comes from, which is where its door
        and flag face."""
        return self.put("mailbox", tx, ty, oy=24,
                        yaw=math.atan2(_OUT[toward][1], _OUT[toward][0]),
                        full=full)

    def _line(self, side, at, span):
        """(cross tile, span low, span high) for a boundary run on one side.
        `at` overrides where the line sits, `span` how far it runs; both
        default to the yard's own bounds, which is right until a neighbour's
        wall is in the way and the yard has to stop short of it."""
        l, r, t, b = self.bounds()
        if side in ("n", "s"):
            return ((t if side == "n" else b) if at is None else at,
                    span[0] if span else l, span[1] if span else r)
        return ((l if side == "w" else r) if at is None else at,
                span[0] if span else t, span[1] if span else b)

    def fence(self, side, gap=False, gate=None, seed=None, span=None,
              at=None, kind="yard_fence"):
        """A BOUNDARY THAT IS NOT A WALL: wire on wooden posts along one side
        of the yard. Mechanically this is where a mouth would sit, so it has
        to read as an edge and be pushed through, never climbed -- which is
        why one bay's wire is down by default.

        `gate` is the way in a household USES: a hung timber leaf at that
        tile of the run. `gap` is a different thing and means something else
        -- the bay whose wire is DOWN, a boundary pushed THROUGH, which is
        what a §13 mouth sits behind. Do not reach for `gap` when you want a
        front entrance: walking onto somebody's lot through their broken
        fence says the opposite of everything a kept yard is saying.
        """
        cross, a0, a1 = self._line(side, at, span)
        seed = self.seed if seed is None else seed
        p0, p1 = a0 * TILE, (a1 + 1) * TILE
        n = max(1, int((p1 - p0) / BAY))
        def _bay_at(t):
            return max(0, min(n - 1, int((t * TILE + 16 - p0) / BAY)))
        hole = (n // 2) if gap is True else (-1 if gap is False
                                             else _bay_at(gap))
        gate_bay = -1 if gate is None else _bay_at(gate)
        ew = side in ("n", "s")
        out = []
        for i in range(n):
            a = p0 + (i + 0.5) * BAY
            c = cross * TILE + 20
            px, py = (a, c) if ew else (c, a)
            yaw = 0.0 if ew else math.pi / 2
            if i == gate_bay:
                out.append(self.sc.add_decoration(Decoration(
                    px, py, "yard_gate", seed=seed + i, yaw=yaw, swing=1.05)))
                continue
            out.append(self.sc.add_decoration(Decoration(
                px, py, kind, seed=seed + i, gap=(i == hole), yaw=yaw)))
        return out

    def hedge(self, side, n=9, seed=None, span=None, at=None, gap=None):
        """The other boundary this town builds: an overgrown hedge line where
        the mowing stopped. Same job as the fence and older -- for a
        churchyard or a plot that has been somebody's since before wire.

        A line of picked field STONES was the first version of this and it is
        why the method is a hedge. `boulder` is a fresh-broken rock at
        (92, 92, 100), the palest thing in a Darkwood-dark yard, and nine of
        them in a row read as a parade of little grey tents pulling the eye to
        the least important object on the lot (VISION.md: judge a colour in a
        SCENE, not on the contact sheet). Growth is dark, and it is already
        the thing this game's plant renderer is best at.
        """
        cross, a0, a1 = self._line(side, at, span)
        seed = (self.seed if seed is None else seed) * 17 + 3
        out = []
        for i in range(n):
            # NOT A RULED ROW OF IDENTICAL LUMPS: uneven in size, uneven in
            # spacing, and wandering either side of the line, or it reads as
            # the grid lockstep (playtest error class #8).
            h = (seed + i * 37) % 101
            f = (i + 0.5 + ((h % 7) - 3) * 0.11) / n
            a = (a0 + f * (a1 - a0)) * TILE + 16 + (((h >> 4) % 11) - 5)
            c = cross * TILE + 16 + (((h >> 2) % 13) - 6)
            # THE WAY THROUGH. A boundary the path walks straight into is not
            # a boundary with a gate, it is a boundary somebody forgot to
            # check against the track they had already worn.
            if gap is not None and abs(a - (gap * TILE + 16)) < TILE * 0.8:
                continue
            px, py = (a, c) if side in ("n", "s") else (c, a)
            out.append(self.sc.add_decoration(
                Decoration(px, py, "bush", scale=0.85 + (h % 5) * 0.14,
                           seed=seed + i * 13)))
        return out

    def woodpile(self, side, along=0.5, axe=False, rows=5, out=1, **kw):
        """Firewood STACKED AGAINST something -- a stack standing alone in
        open dirt reads as dumped lumber. `axe` leaves it half split with the
        axe still standing in the round."""
        tx, ty = self.wall(side, along=along, out=out)
        return self.put("woodpile", tx, ty, yaw=_ALONG[side],
                        axe=axe, rows=rows, **kw)

    def washing(self, tx, ty, laundry=4, small=False, seed=None, yaw=0.0):
        """THE LINE. Out since winter, so it hangs stiff. The span is over two
        tiles wide, so it is placed by hand rather than derived from a wall."""
        return self.put("clothesline", tx, ty, laundry=laundry, small=small,
                        seed=self.seed if seed is None else seed, yaw=yaw)

    def crates(self, tx, ty, tarp=False, opened=False, courses=3, seed=None):
        """The deliveries that stopped in January, still where the last truck
        left them."""
        return self.put("crate_stack", tx, ty, tarp=tarp, opened=opened,
                        courses=courses,
                        seed=(self.seed if seed is None else seed))

    def bed(self, tx, ty, tended=False, w=96, h=64, seed=None):
        """A vegetable bed. Turned over in the autumn and never planted, or
        still being kept by somebody who has not given up on April."""
        return self.put("garden_patch", tx, ty, tended=tended,
                        w=w, h=h, seed=(self.seed if seed is None else seed))


# =====================================================================
# THE YARD AS A SCENE
# =====================================================================
# The chain is SAFE PATH -> YARD -> HOUSE, and a yard is its own scene with
# exactly ONE building in it. `lodge_yard` and `backwoods_cabin` were already
# this shape; everything below is that shape made general so the rest of the
# town can be built the same way instead of each one being drawn again.
#
# The scene is small on purpose. A yard is the ground you cross between the
# road and somebody's door -- long enough that arriving is a walk and short
# enough that the walk is not the point. The building sits clear of the
# middle, the road exit spans three tiles (an exit you have to thread is a
# wall), and a worn track runs between the two.

# A yard is a PLACE, not a doorstep with a road attached. The first cut was
# 20x16 and read as a corridor with a house in it; the walk from the gate to
# the door has to be a walk. The scene is still deliberately smaller than the
# camera window -- the black rim beyond the verge is wanted, not a defect, and
# it is what makes a yard feel like a lit clearing with nothing around it.
_YARD_W, _YARD_H = 30, 24
# How deep the scattered verge reaches in from the map edge. Everything
# inside it is the LOT, and the lot stays clear.
_BAND = 3
# Which wall of the scene an exit sits in, and the step INTO the scene from it.
_EDGE_IN = {"n": (0, 1), "s": (0, -1), "e": (-1, 0), "w": (1, 0)}


def build_yard_scene(key, *, door_face, door_char, interior, interior_spawn,
                     path_side, path_char, path_target, path_spawn,
                     w=_YARD_W, h=_YARD_H, building=(8, 6), verge=("T", "p"),
                     music="village", seed=7, band=_BAND):
    """One household's ground: a walled clearing, one building, two ways out.

    Returns `(scene, yard)` -- the scene registered like any other, and a
    `Yard` already bound to the building's geometry so the caller dresses it
    with the vocabulary above instead of counting tiles.

    `door_face` is the wall of the BUILDING its door is in; `path_side` the
    edge of the SCENE the road exit sits in. They are independent: a house
    can front the road or turn its back on it, and which it does is one of
    the things a yard says.
    """
    from .base import Scene, scatter_forest_band

    bw, bh = building
    bl = (w - bw) // 2
    bt = (h - bh) // 2
    # Push the building AWAY from the road, so the yard is in front of it
    # rather than wrapped around it: the ground you cross is the layer.
    ax, ay = _EDGE_IN[path_side]
    bl += ax * 2
    bt += ay * 2
    br, bb = bl + bw - 1, bt + bh - 1

    floor = [["g"] * w for _ in range(h)]
    objects = [["."] * w for _ in range(h)]

    # the building: wall ring, roof inside, one door punched through a face
    for x in range(bl, br + 1):
        objects[bt][x] = objects[bb][x] = "W"
    for y in range(bt + 1, bb):
        objects[y][bl] = objects[y][br] = "W"
        for x in range(bl + 1, br):
            objects[y][x] = "r"
    if door_face in ("n", "s"):
        dtx, dty = (bl + br) // 2, (bt if door_face == "n" else bb)
    else:
        dtx, dty = (bl if door_face == "w" else br), (bt + bb) // 2
    objects[dty][dtx] = door_char
    dx, dy = _OUT[door_face]
    out = (dtx + dx, dty + dy)

    # WINDOWS, in every face that has room for them. A house without windows
    # is a bunker, and the layer's whole promise is that you read a household
    # from OUTSIDE -- which you cannot do through a blank wall. They are also
    # mechanical: a pane is what a thrown stone SMASHES (the loud tier,
    # DESIGN.md §12), and glass on the town's own buildings is what keeps that
    # verb alive now that the one square is gone.
    #
    # Placed a third and two thirds along each run, skipping the corners (a
    # window in a corner tile has two outward faces and reads as a hole) and
    # never the door tile or the tiles either side of it -- a pane beside a
    # doorframe is a sidelight, and this is not that kind of house.
    for _side in "nsew":
        _run = (range(bl + 1, br), range(bl + 1, br),
                range(bt + 1, bb), range(bt + 1, bb))["nsew".index(_side)]
        _run = list(_run)
        if len(_run) < 3:
            continue
        for _f in (0.32, 0.68):
            _i = _run[min(len(_run) - 1, int(len(_run) * _f))]
            if _side in ("n", "s"):
                _wx, _wy = _i, (bt if _side == "n" else bb)
            else:
                _wx, _wy = (bl if _side == "w" else br), _i
            if abs(_wx - dtx) + abs(_wy - dty) <= 1:
                continue
            if objects[_wy][_wx] == "W":
                objects[_wy][_wx] = "i"

    # THE ROAD EXIT, three tiles wide across the middle of its edge
    ex, ey = ((w // 2, 0 if path_side == "n" else h - 1)
              if path_side in ("n", "s")
              else (0 if path_side == "w" else w - 1, h // 2))
    for k in (-1, 0, 1):
        px, py = (ex + k, ey) if path_side in ("n", "s") else (ex, ey + k)
        if 0 <= px < w and 0 <= py < h:
            objects[py][px] = path_char

    # THE TRACK the feet wore between the two, laid on the floor so the
    # ground itself shows the way in.
    #
    # ROUTED, not walked. Two earlier versions stepped greedily from the door
    # toward the gate and refused to enter the house: the first painted a
    # dirt path across the roof whenever the door was in a side wall, and the
    # second stranded the track in the middle of the lot for every layout
    # where the door faces AWAY from the road -- it would walk out, find both
    # candidate steps blocked by the building, and stop. Four of the sixteen
    # door-face x road-side combinations were broken, which is exactly the
    # kind of thing that hides when only one of them has ever been built.
    # A breadth-first search over the tiles that are not the house always
    # finds the way round if there is one, so the router cannot strand it.
    _blocked = set()
    for _by in range(bt, bb + 1):
        for _bx in range(bl, br + 1):
            _blocked.add((_bx, _by))
    _prev, _q = {out: None}, [out]
    while _q:
        _cur = _q.pop(0)
        if _cur == (ex, ey):
            break
        for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _n = (_cur[0] + _dx, _cur[1] + _dy)
            if (_n in _prev or _n in _blocked
                    or not (0 <= _n[0] < w and 0 <= _n[1] < h)):
                continue
            _prev[_n] = _cur
            _q.append(_n)
    _at = (ex, ey) if (ex, ey) in _prev else None
    while _at is not None:
        if objects[_at[1]][_at[0]] == ".":
            floor[_at[1]][_at[0]] = "d"
        _at = _prev[_at]

    # THE LOT is kept ground and the band stops at its line. Left to grow
    # where it liked, the scatter put standing corn in the middle of a
    # household's mown yard, which unsays everything a kept yard is for.
    lot = (band, w - 1 - band, band, h - 1 - band)

    # THE EDGE OF THE LOT: a scattered, permeable band, not a one-tile ring
    # of the verge char. Built as a ring it reads as a FENCE made of corn --
    # a hard rectangle framing the scene -- and it is also a lie about the
    # geometry, since a treeline in this game is something you thread. The
    # same helper the town and the lodge yard use, so a yard's edge is the
    # same kind of thing as every other outdoor edge.
    def _keep_clear(tx, ty):
        if lot[0] <= tx <= lot[1] and lot[2] <= ty <= lot[3]:
            return True                       # THE LOT: kept ground
        if floor[ty][tx] == "d":
            return True                       # the worn track in
        if path_side in ("n", "s"):
            return abs(tx - ex) <= 2          # the gate, and room to aim at it
        return abs(ty - ey) <= 2

    _bushes = []
    scatter_forest_band(floor, objects, w, h, depth=band, seed=seed * 31 + 5,
                        tree_density=0.55, passable_ratio=0.6,
                        bush_density=0.16,
                        solid_char=verge[0], passable_char=verge[1],
                        protected=_keep_clear,
                        place_bush=lambda px, py: _bushes.append((px, py)))

    sc = Scene(key, ["".join(r) for r in floor],
               ["".join(r) for r in objects], music=music)
    for _bx, _by in _bushes:
        sc.add_decoration(Decoration(_bx, _by, "bush"))
    # weeds crowding the foundations, so the wall meets the ground in an
    # overgrown line instead of a cut edge
    _wr = random.Random(seed * 977 + 13)
    for _ in range(14):
        _wx = _wr.randint(bl - 1, br + 1) * TILE + _wr.randint(2, 28)
        _wy = _wr.choice([bt - 1, bb + 1]) * TILE + _wr.randint(2, 28)
        if objects[int(_wy // TILE)][int(_wx // TILE)] == ".":
            sc.add_decoration(Decoration(_wx, _wy, "grass_tuft"))

    def _open(tx, ty):
        return (0 <= tx < w and 0 <= ty < h and objects[ty][tx] == "."
                and floor[ty][tx] != "d")

    # THE LOT GOES ROUGH WHERE NOBODY WALKS. Nothing is mown three months
    # after everybody stopped, and a lot's far corners go over first; what
    # stays short is the ground the household actually crosses. So the grass
    # thickens with DISTANCE from the house and the track, which fills the
    # empty half of a big lot without unsaying "kept" -- the read is a yard
    # somebody keeps the middle of, not a lawn.
    _track = [(qx, qy) for qy in range(h) for qx in range(w)
              if floor[qy][qx] == "d"]

    def _walked(tx, ty):
        """How far this tile is from anything the household uses: the house
        itself (distance to the RECT, not to its corners -- corners put the
        midpoint of a long wall four tiles 'away' from a building it is
        touching) or the worn track."""
        dh = max(bl - tx, 0, tx - br) + max(bt - ty, 0, ty - bb)
        dt = min([abs(tx - qx) + abs(ty - qy) for qx, qy in _track] or [99])
        return min(dh, dt)

    for ty in range(lot[2], lot[3] + 1):
        for tx in range(lot[0], lot[1] + 1):
            if not _open(tx, ty):
                continue
            rough = min(0.85, 0.16 + 0.13 * max(0, _walked(tx, ty) - 1))
            for _ in range(2 if _wr.random() < rough * 0.5 else 1):
                if _wr.random() < rough:
                    sc.add_decoration(Decoration(
                        tx * TILE + _wr.randint(3, 29),
                        ty * TILE + _wr.randint(3, 29),
                        "tall_grass" if _wr.random() < 0.78
                        else "grass_tuft"))

    # AND THE OUTER RING CARRIES THINGS TOO. The scene ends before the camera
    # does, so its edge dissolves into black -- which is wanted, and only
    # works if there is something out there to dissolve. An edge of bare
    # mown grass stopping dead reads as the end of a level; growth thinning
    # into the dark reads as the world going on without you. Every side, so
    # the four facings agree.
    for ty in range(h):
        for tx in range(w):
            inside = (lot[0] <= tx <= lot[1] and lot[2] <= ty <= lot[3])
            if inside or not _open(tx, ty):
                continue
            for _ in range(2):
                if _wr.random() < 0.55:
                    sc.add_decoration(Decoration(
                        tx * TILE + _wr.randint(3, 29),
                        ty * TILE + _wr.randint(3, 29),
                        "tall_grass" if _wr.random() < 0.72 else "bush"))
    sc.skybox_kind = "overcast"
    sc.is_yard = True            # the layer marker, as SafePath.is_safe_path
    sc.add_exit(path_char, path_target, path_spawn)
    sc.set_spawn("default", out[0], out[1])
    if interior is not None:
        sc.add_exit(door_char, interior, interior_spawn)
        sc.set_spawn("from_" + interior, out[0], out[1])
    # interior=None is a FACADE house: the door char is solid ('l'), no
    # interior is modelled, and the yard carries the whole household. A
    # facade door is honest here in a way it would not be in Brimley -- the
    # layer's promise is that you read a household from OUTSIDE.
    sc.set_spawn("from_" + path_target, ex + ax, ey + ay)
    # EVERY EDGE THAT IS NOT THE ROAD IS A MOUTH (DESIGN.md §13). A yard is
    # the last lit ground before the world stops caring: the way you came is
    # the only way that stays true, and walking off the back of somebody's lot
    # in the dark drops you into the in-between. Which field you land in is
    # derived from the verge you pushed through -- never corn on this side and
    # pine on the other -- so it is the same rule the safe path's flanks use.
    from .safe_path import _VERGE_LOST
    _mouths = "".join(sd for sd in "nesw" if sd != path_side)
    sc.set_lost_edge(_mouths, _VERGE_LOST.get(tuple(verge), "lost_forest"))
    yard = Yard(sc, (bl, br, bt, bb), door_face, out,
                depth=3, flank=2, seed=seed)
    # the KEPT rectangle, for the boundary to sit on. `Yard.bounds()` derives
    # a rect from the DOOR's facing, which is not the same thing here: a
    # house can face one way and front the road another.
    yard.lot = lot
    return sc, yard


# ---------------------------------------------------------------------
# THE SHIPPING YARDS. One per building, none shared.
# ---------------------------------------------------------------------

def build_shop_yard():
    """HETTIE'S. The store's own ground, off the store row.

    She is the one person in Brimley still performing normality at full
    volume -- open, lit, swept -- so her yard is the KEPT one, and every
    piece of it is a thing she is still doing on a schedule nobody needs
    any more. The genset runs, the can beside it is full, and the box out
    at the gate is empty because she walks out and empties it every
    morning and nothing has come since January.

    The one thing she is NOT still doing is the delivery, because it was
    never hers: the crates the last truck left are broken open at the side
    of the building where they were dropped, and they will not be
    collected (NARRATIVE §1, the severed supply).
    """
    sc, y = build_yard_scene(
        "shop_yard",
        door_face="e", door_char="D",
        interior="shop", interior_spawn="from_shop_yard",
        path_side="e", path_char="e",
        path_target="store_row", path_spawn="from_shop_yard",
        verge=("C", "A"), building=(9, 6), seed=37)
    # KEPT, and every piece of it is an errand she is still running to a
    # schedule nobody needs. The genset burns and the can beside it is full.
    y.step()
    y.genset(running=True, side="s", along=0.25)
    y.crates(y.right + 2, y.bot, opened=True)
    # The box stands where the yard meets the road, which is the EAST side:
    # the store row runs down that flank, so the carrier came from there.
    y.mailbox(y.right + 3, y.bot, toward="e", full=False)
    # HER GATE, not a hole in her fence: she opens it every morning and it
    # stands open all day, which is the whole of what her yard is saying. It
    # is in the road-side run, level with her door.
    y.fence("e", at=y.lot[1], span=(y.lot[2], y.lot[3]), gate=y.out[1] + 1)
    # and the line RETURNS along both flanks, so the boundary ENCLOSES a lot
    # instead of reading as one ruled line laid down the side
    y.fence("s", at=y.lot[3], span=(y.lot[1] - 6, y.lot[1] - 1), gap=False)
    y.fence("n", at=y.lot[2], span=(y.lot[1] - 6, y.lot[1] - 1), gap=False)
    y.hedge("w", n=7, at=y.left - 3, span=(2, 12))
    # her burn barrel, out where she can see the road from it
    sc.add_decoration(Decoration((y.left - 1) * TILE + 16,
                                 (y.bot + 3) * TILE + 16,
                                 "burn_barrel", seed=62))
    # AND HETTIE IS ON HER STEP. The one exception to "a yard is empty of
    # people", and it is an exception the layer's own rule asks for: the
    # `homebody` mode is somebody who is INSIDE and briefly out, sweeping a
    # step that does not get dirty before ducking back in for a spell (she
    # drops solid and stops being drawn while she is behind the door, and the
    # shop interior holds a Hettie, so walking in finds her there). A store
    # that is still open is a store with its keeper visible at the door, and
    # she is the only household in town still performing that.
    _resident(sc, y.out[0], y.out[1], "Hettie", "hettie", None,
              movement="homebody", radius=34, pages=[
                  "Still open. Always open. The shelves don't empty "
                  "anymore. Have you noticed.",
                  "No deliveries. In a while now. But we manage. We always.",
                  "I keep the lights on. So they know. Someone's keeping "
                  "them on.",
              ])
    return sc


def build_school_yard():
    """THE SCHOOLHOUSE. Canon-empty: this is where the congregation bedded
    down before they went below (NARRATIVE §3), and walking into that
    emptiness is the beat, so the yard has to say it from the gate.

    Everything here is a thing that should have happened in the spring and
    did not. The bed was turned over in the autumn and never planted. The
    genset is cold with its can over. Nobody has walked the ground since
    January, so the grass has the lot -- and the layer does that on its own,
    because the rough growth is seeded against distance from a track that
    barely exists here.
    """
    sc, y = build_yard_scene(
        "school_yard",
        door_face="e", door_char="D",
        interior="schoolhouse", interior_spawn="from_school_yard",
        path_side="w", path_char="e",
        path_target="store_row", path_spawn="from_school_yard",
        verge=("C", "A"), building=(10, 6), seed=53)
    y.step()
    y.genset(running=False, side="n", along=0.7)
    y.bed(y.left + 2, y.bot + 4, tended=False, w=120, h=78)
    y.fence("w", at=y.lot[0], span=(y.lot[2] + 2, y.lot[3] - 2), gap=False)
    y.put("flagpole", y.left - 2, y.top + 1)
    return sc


def build_church_yard():
    """THE CHURCH. Rev. Crane kept this place up until the day he walked down
    to the river after his flock (NARRATIVE §4), so the yard is KEPT and then
    stops mid-sentence: the genset still running for a congregation that is
    under the ground, and the axe still standing in the round.

    The hedge is the churchyard line. It is older than wire and it is the
    boundary a church would actually have.
    """
    sc, y = build_yard_scene(
        "church_yard",
        door_face="s", door_char="D",
        interior="church", interior_spawn="from_church_yard",
        path_side="e", path_char="e",
        path_target="chapel_row", path_spawn="from_church_yard",
        verge=("T", "p"), building=(10, 7), seed=11)
    y.step()
    y.genset(running=True, side="w", along=0.3)
    y.woodpile("n", along=0.35, axe=True, rows=4)
    y.mailbox(y.lot[1] - 1, y.out[1] + 2, toward="e", full=True)
    y.hedge("s", n=13, at=y.lot[3], span=(y.lot[0], y.lot[1]))
    for i, tx in enumerate((y.left + 1, y.left + 4, y.right - 3, y.right)):
        y.put("headstone", tx, y.bot + 3, seed=91 + i * 7)
        y.put("headstone", tx, y.bot + 5, seed=131 + i * 7)
    # THE DOOR THE BELL CALLS THEM TO. Pulling the rope in the tower rings a
    # peal that pulls every cult hunter on the map toward this spot, and the
    # first to reach it stills the rope (`Game._tick_bell`). It is the church
    # door because that is where the rope comes down.
    sc._bell_door = (y.out[0] * TILE + 16, y.out[1] * TILE + 16)
    return sc


def build_barn_yard():
    """THE BARN. The other canon-empty one, and the one a crowd used: the
    congregation slept here (NARRATIVE §3).

    So the yard reads as a place a lot of people used and then all left at
    once. The washing they strung up is still on the line, frozen since
    winter. The genset that kept them warm is cold with the can on its side.
    And the fence has a bay pushed flat rather than a gate, because what went
    through here was not a household on its way to the road.
    """
    sc, y = build_yard_scene(
        "barn_yard",
        door_face="n", door_char="D",
        interior="barn", interior_spawn="from_barn_yard",
        path_side="w", path_char="e",
        path_target="chapel_row", path_spawn="from_barn_yard",
        verge=("T", "p"), building=(11, 7), seed=23)
    y.step()
    y.genset(running=False, side="e", along=0.3)
    y.washing(y.left + 3, y.top - 3, laundry=6, yaw=0.0)
    y.washing(y.left + 3, y.bot + 3, laundry=5, yaw=0.0, seed=29)
    y.fence("w", at=y.lot[0], span=(y.lot[2] + 2, y.lot[3] - 2),
            gap=y.out[1] + 3)
    # ONE TRUCK STAYED. A crowd came here and left in one direction, and the
    # thing nobody drove home sits dead in the weeds behind the barn with its
    # driver's door hanging. The gap under its bed is a rooted hide
    # (DESIGN.md §12): the surface's cover is corn and treeline, and this is
    # one of the two places on the string you can put a roof over yourself.
    _px, _py = y.right + 3, y.bot + 1
    y.put("pickup_truck", _px, _py, door_open=True)
    _objs = [list(r) for r in sc.objects]
    for _c in range(_px - 1, _px + 2):
        if 0 <= _c < sc.w:
            _objs[_py][_c] = "X"
    sc.objects = _objs
    sc.hide_spots = [(_px * TILE + 16, (_py + 1) * TILE + 8, "under")]
    # AND ITS CAB RADIO, which still has power: the one toggleable LURE on
    # the surface (DESIGN.md §12). Turn it on and walk away, and whatever is
    # hunting goes to the music instead of to you -- until the cult reaches
    # it and kills the station.
    # The source sits at the CAB WINDOW, on the walkable tile beside the
    # truck rather than on the truck's own footprint: you reach in to it.
    sc.add_noise_source(
        _px * TILE + 16, (_py - 1) * TILE + 16, "radio", sfx="radio_snatch",
        on_notice="The truck radio catches. A dead station rolls out "
                  "over the yard.",
        off_notice="You kill the radio.",
        silenced_notice="The music stops dead.")
    sc.add_noise_trap((_px - 2) * TILE + 16, (_py + 1) * TILE + 24,
                      "glass", seed=7)
    return sc


def build_sheriff_yard():
    """SHERIFF VANE'S. Still here, still going through it.

    The one yard in town where the machine is RUNNING and the can beside it is
    already empty and on its side. That is the whole man (DESIGN.md §2, his
    ledger and his fall): the lights are on and the fuel is gone. His car is
    slewed at the gate with the driver's door still standing open, because he
    tried the road like everyone did and walked back inside.
    """
    sc, y = build_yard_scene(
        "sheriff_yard",
        door_face="s", door_char="D",
        interior="sheriff_office", interior_spawn="from_sheriff_yard",
        path_side="e", path_char="e",
        path_target="south_row", path_spawn="from_sheriff_yard",
        verge=("C", "A"), building=(10, 7), seed=67)
    y.step()
    y.genset(running=True, side="w", along=0.4, can_tipped=True)
    y.fence("s", at=y.lot[3], span=(y.lot[0], y.lot[1]), gate=y.lot[1] - 4)
    y.put("yard_light", y.right + 2, y.bot + 2)
    return sc


def build_farm_yard():
    """THE ABANDONED FARMHOUSE -- THE WRONG YARD.

    Newcomers took this lot and keep it in a way nobody from Brimley would.
    The crates are squared off too neatly. There is a husk thing propped by
    the step. The door-motif is chalked on the siding where the weather has
    nearly taken it. The bed is dug too deep and the wrong shape for anything
    you would eat.

    The genset is cold because whoever is here does not need the light, and
    that is the tell that separates this from the two empty yards: those are
    dark because nobody is left, this one is dark on purpose.
    """
    sc, y = build_yard_scene(
        "farm_yard",
        door_face="w", door_char="D",
        interior="abandoned_farmhouse", interior_spawn="from_farm_yard",
        # The road is on the WEST: south_row leaves EAST to get here, so the
        # way back has to face west. It read "e" until 2026-07, which made the
        # two scenes both claim to be east of the other and turned the
        # crossing into a sideways teleport -- the one yard on the whole
        # column that broke the pattern (tools/surface_map.py finds this).
        path_side="w", path_char="e",
        path_target="south_row", path_spawn="from_farm_yard",
        verge=("C", "A"), building=(9, 7), seed=79)
    y.step()
    y.genset(running=False, side="n", along=0.65)
    y.crates(y.left - 3, y.bot + 2, courses=3, tarp=True)
    y.crates(y.left - 3, y.bot + 4, courses=2, seed=83)
    y.put("husk_bundle", y.out[0], y.out[1] + 2)
    y.siding("chalk_door_wall", y.left - 1, y.top + 2)
    y.bed(y.right + 3, y.top + 2, tended=False, w=84, h=104, seed=87)
    for i, (dx, dy) in enumerate(((-2, -1), (-3, 1), (-2, 3))):
        y.put("candle", y.out[0] + dx, y.out[1] + dy)
    y.put("yellow_sign", y.out[0] - 1, y.out[1] + 4)
    y.fence("n", at=y.lot[2], span=(y.lot[0], y.lot[1]), gap=False)
    _cult_camp(sc, y.lot[0] + 3, y.lot[3] - 3)
    return sc


def _cult_camp_raise(game, scene):
    if game._evidence_count() < 1:
        return
    cx, cy = scene._camp_pos
    tx, ty = int(cx // TILE), int(cy // TILE)
    rows = [list(r) for r in scene.floor]
    for qy in range(ty - 2, ty + 2):
        for qx in range(tx - 2, tx + 3):
            if (0 <= qy < scene.h and 0 <= qx < scene.w
                    and rows[qy][qx] in (":", ";", "g")):
                rows[qy][qx] = "d"
    scene.floor = ["".join(r) for r in rows]
    scene.add_decoration(Decoration(cx, cy, "camp_fire", seed=71))
    for (dx, dy, kind, sd) in ((-42, -4, "bedroll", 1),
                               (36, -12, "bedroll", 2),
                               (-8, 40, "bedroll", 3),
                               (44, 18, "log_seat", 4),
                               (-44, 22, "log_seat", 5),
                               (10, -40, "log_seat", 6)):
        scene.add_decoration(Decoration(cx + dx, cy + dy, kind, seed=sd))
    scene.add_decoration(Decoration(cx + 48, cy - 34, "lantern"))


def _cult_camp(sc, ctx, cty):
    """THE CAMP the newcomers rest and gather at, raised on entry once the
    cult is awake.

    NOTHING at 0 evidence: the town reads normal (NARRATIVE §2), and a ring
    of bedrolls around a lit fire is not normal. At 1 evidence -- the cult
    awake -- the whole camp is standing: a ground fire, bedrolls, felled-log
    seats, a hung lantern, and the ground under it beaten to dirt, because
    the worn earth is THEIR doing and was not here before them. Rebuilt every
    load. The crew that fills it comes off the scene's cult spawn pool
    (systems/threat_mixin), so it is manned or empty by the same ladder as
    everything else.
    """
    sc._camp_pos = (ctx * TILE + 16, cty * TILE + 16)
    sc.add_cult_station(ctx * TILE + 16, (cty + 1) * TILE + 16,
                        face=(0, -1), dwell=(8.0, 14.0))


    sc.on_enter_fn = _cult_camp_raise


def build_toby_yard():
    """TOBY'S HOUSE. Lived in, and a child lives in it.

    The wood is half split with the axe still standing in the block, because
    the person whose job that was went below in January. The bed by the wall
    is the one tended patch left on the string: somebody here still has to be
    fed. The line has small clothes on it, frozen since winter.
    """
    sc, y = build_yard_scene(
        "toby_yard",
        door_face="s", door_char="D",
        interior="toby_house", interior_spawn="from_toby_yard",
        path_side="e", path_char="e",
        path_target="bank_row", path_spawn="from_toby_yard",
        verge=("T", "p"), building=(9, 6), seed=91)
    y.step()
    y.genset(running=True, side="n", along=0.35)
    y.woodpile("w", along=0.5, axe=True)
    y.washing(y.left + 2, y.bot + 3, laundry=5, small=True, yaw=0.0)
    y.bed(y.right + 3, y.bot + 2, tended=True, w=104, h=70, seed=41)
    y.mailbox(y.lot[1] - 1, y.out[1], toward="e", full=True)
    y.fence("s", at=y.lot[3], span=(y.lot[0], y.lot[1]), gate=y.out[0] + 2)
    return sc


def build_calder_yard():
    """MRS. CALDER'S. She sets a place at supper for a guest she cannot name
    and watches the road it will come up (NARRATIVE §3).

    So the yard is KEPT, and its centrepiece is the table laid out IN THE OPEN
    where the road can see it: two settings, a candle burned down, one chair
    knocked over. Her gate stands open, which is the same gesture as the
    unlatched door she mentions. The house door is a facade -- no interior is
    modelled, and a woman who leaves her door unlatched for a guest is not a
    house you walk into uninvited.
    """
    sc, y = build_yard_scene(
        "calder_yard",
        door_face="w", door_char="D",
        interior="calder_house",
        interior_spawn="from_calder_yard",
        path_side="w", path_char="e",
        path_target="bank_row", path_spawn="from_calder_yard",
        verge=("T", "p"), building=(8, 6), seed=127)
    y.step()
    y.genset(running=True, side="s", along=0.6)
    y.mailbox(y.lot[0] + 2, y.out[1] + 1, toward="w", full=False)
    y.fence("w", at=y.lot[0], span=(y.lot[2] + 1, y.lot[3] - 1),
            gate=y.out[1])
    # THE TABLE, out where the road can see it. Two settings, always.
    tx, ty = y.out[0] - 3, y.out[1] + 3
    sc.add_furniture("table", [(tx, ty)], w=30, h=26)
    y.put("place_setting", tx, ty, ox=10, oy=12)
    y.put("place_setting", tx, ty, ox=24, oy=12)
    y.put("candle", tx, ty, ox=16, oy=2)
    y.put("overturned_chair", tx + 1, ty + 1)
    sc.hide_spots = [(tx * TILE + 16, (ty + 1) * TILE + 16, "under")]
    # THE CULT'S ERRAND HERE is to stand over the table she keeps laying
    # (`Scene.add_cult_station`, the JOBS layer): a hooded figure looking at
    # two settings laid for nobody, which says what it is doing here without
    # a word of it.
    sc.add_cult_station(tx * TILE + 16, (ty + 1) * TILE + 16,
                        face=(0, -1), dwell=(5.0, 9.0))
    return sc


def build_royce_yard():
    """ROYCE'S. He tried to drive out like everyone in town did and the corn
    handed him back, and he has not stopped trying (NARRATIVE §3).

    The car is nosed at the gate, pointed out of town and SHUT: ready to be
    tried again, which is a different sentence from Vane's door left hanging
    open. The genset runs and the can beside it is already empty, because all
    of it goes into the tank.
    """
    sc, y = build_yard_scene(
        "royce_yard",
        door_face="e", door_char="D",
        interior="royce_house",
        interior_spawn="from_royce_yard",
        path_side="e", path_char="e",
        path_target="lane_end", path_spawn="from_royce_yard",
        verge=("C", "A"), building=(8, 6), seed=107)
    y.step()
    y.genset(running=True, side="n", along=0.6, can_tipped=True)
    y.mailbox(y.lot[1] - 1, y.out[1] + 2, toward="e", full=False)
    y.fence("e", at=y.lot[1], span=(y.lot[2] + 1, y.lot[3] - 1),
            gate=y.out[1])
    from .base import dead_cars
    objs = [list(r) for r in sc.objects]
    cars = dead_cars(objs, [(y.out[0] + 2, y.out[1] + 3, "rust_coupe",
                             -1.28, 57, "h")])
    sc.objects = objs
    for d in cars:
        sc.add_decoration(d)
    return sc


def build_garrick_yard():
    """GARRICK'S. The old man who tells you to stay on the roads (NARRATIVE
    §4), which is advice he takes: he gave the lights up and sits out at the
    burn barrel instead.

    So his genset is cold with the can over, and the wood he was splitting
    when he stopped is still in the round. His boundary is a hedge, older than
    wire and older than him.
    """
    sc, y = build_yard_scene(
        "garrick_yard",
        door_face="w", door_char="D",
        interior="garrick_house",
        interior_spawn="from_garrick_yard",
        path_side="w", path_char="e",
        path_target="lane_end", path_spawn="from_garrick_yard",
        verge=("T", "p"), building=(8, 6), seed=149)
    y.step()
    y.genset(running=False, side="s", along=0.7)
    y.woodpile("n", along=0.4, axe=True, rows=3)
    y.hedge("w", n=11, at=y.lot[0], span=(y.lot[2], y.lot[3]), gap=y.out[1])
    sc.add_decoration(Decoration((y.out[0] - 2) * TILE + 16,
                                 (y.out[1] + 2) * TILE + 16,
                                 "burn_barrel", seed=61))
    return sc


# =====================================================================
# THE THREE HOUSES THAT HAD NO INSIDE
# =====================================================================
# Mrs. Calder, Royce and Garrick stood on open ground with no building at
# all, then got yards with FACADE doors -- which left them still standing
# outdoors while their own houses sat sealed. People live in HOUSES. The yard
# is what tells you about a household when nobody is home to say it; it is
# not where the household stands.
#
# So these are small: one room, one resident, one thing in it that says who
# they are. They are not the principals' rooms and they should not try to be.


def _resident(sc, tx, ty, name, kind, convo, movement="idle", pages=None,
              radius=40, beats=()):
    """The household, AT HOME. A person belongs in their house -- the yard is
    what tells you about them when nobody is there to say it, and a resident
    standing out in their own yard does that job for it.

    `pages` instead of `convo` gives the speaker a fixed page list rather than
    the ask verb: the doorstep cameo, not a conversation.

    `beats` is the town REACTING to state (DESIGN.md §2): a list of
    (flag, predicate, pages). On each talk the first beat whose predicate
    holds and whose one-shot flag is unset fires INSTEAD of the conversation
    and sets its flag; afterwards the local falls back to the ask verb.
    """
    from entities.npc import NPC
    from .dialogue import chorus_dialogue, doorstep_voice
    npc = NPC(tx * TILE + 16, ty * TILE + 16, name, kind,
              dialogue_fn=(doorstep_voice(pages) if pages is not None
                           else chorus_dialogue(convo, beats)),
              movement=movement, radius=radius)
    sc.add_npc(npc)


def _small_house(key, yard_key, rows, music="home"):
    """The shared shell: a one-room house whose door goes back to its yard."""
    from .base import Scene
    floor = ["=" * len(rows[0]) for _ in rows]
    sc = Scene(key, floor, rows, music=music)
    sc.add_exit("D", yard_key, "from_" + key)
    return sc


def build_calder_house():
    """MRS. CALDER'S, inside. She sets a place at supper for a guest she
    cannot name (NARRATIVE §3), and the table she lays it on is out in the
    yard where the road can see it -- so what is left in here is the WAITING:
    the second chair pulled out ready, the stove kept in, and a door she
    leaves unlatched because it seemed polite."""
    sc = _small_house("calder_house", "calder_yard", [
        "WWWWWWWWWWWW",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W....D.....W",
        "WWWWWWWWWWWW",
    ])
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_calder_yard", 5, 5)
    sc.add_furniture("stove", [(1, 1)], w=30, h=40)
    sc.add_furniture("table", [(5, 3)], w=30, h=26)
    sc.add_furniture("cot", [(9, 2)], w=30, h=16)
    _resident(sc, 8, 4, "Mrs. Calder", "townswoman", CALDER_CONVO, beats=[
        ("beat_calder_unlatched",
         _beat_calder_unlatched, [
             "Closer now. Whoever the place is set for. An old woman can "
             "feel a knock coming before it lands.",
             "I've started leaving the door unlatched at night. It "
             "seemed... polite.",
         ])])
    sc.add_decoration(Decoration(5 * TILE + 16, 3 * TILE + 6, "candle"))
    # the second setting, laid indoors as well: she does not know which
    # table he will come to
    sc.add_decoration(Decoration(5 * TILE + 10, 3 * TILE + 12,
                                 "place_setting"))
    sc.add_decoration(Decoration(5 * TILE + 24, 3 * TILE + 12,
                                 "place_setting"))
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16,
                                 "overturned_chair"))
    return sc


def build_royce_house():
    """ROYCE'S, inside. Every road out hands you back and he has not stopped
    trying (NARRATIVE §3), so his house is a staging post rather than a home:
    the bed made and not slept in, the lamp left burning by the door, and the
    can he keeps filling standing where he can pick it up on the way out."""
    sc = _small_house("royce_house", "royce_yard", [
        "WWWWWWWWWWWW",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W.....D....W",
        "WWWWWWWWWWWW",
    ])
    sc.set_spawn("default", 6, 5)
    sc.set_spawn("from_royce_yard", 6, 5)
    sc.add_furniture("cot", [(1, 1)], w=30, h=16)
    sc.add_furniture("table", [(8, 2)], w=30, h=26)
    sc.add_decoration(Decoration(8 * TILE + 16, 2 * TILE + 6,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "fuel_can"))
    sc.add_decoration(Decoration(3 * TILE + 16, 5 * TILE + 16, "fuel_can",
                                 tipped=True))
    _resident(sc, 4, 3, "Royce", "royce", ROYCE_CONVO, movement="watch",
              beats=[("beat_royce_throat",
                      _beat_royce_throat, [
                          "You're still here. Course you're still here.",
                          "I keep turning it over. Every road out of Brimley "
                          "hands you back. Except the one that carried you "
                          "in. If a door only opens the one way, mister, it "
                          "isn't a door.",
                          "[c=dim]It's a throat.[/c]",
                      ])])
    return sc


def build_garrick_house():
    """GARRICK'S, inside. He gave the lights up and sits out at the burn
    barrel instead, so the room behind him is cold and dark: the stove out,
    the lamp unlit, and a chair pulled to the window that looks at the road
    he tells everybody to stay on (NARRATIVE §4)."""
    sc = _small_house("garrick_house", "garrick_yard", [
        "WWWWWiWWWWWW",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W...D......W",
        "WWWWWWWWWWWW",
    ])
    sc.set_spawn("default", 4, 5)
    sc.set_spawn("from_garrick_yard", 4, 5)
    sc.add_furniture("stove", [(10, 1)], w=30, h=40)
    sc.add_furniture("cot", [(1, 4)], w=30, h=16)
    sc.add_furniture("table", [(3, 2)], w=30, h=26)
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 6,
                                 "kerosene_lamp", broken=True))
    sc.add_decoration(Decoration(5 * TILE + 16, 1 * TILE + 20,
                                 "overturned_chair"))
    # his chair is at the window that looks at the road he tells everybody to
    # stay on, and so is he
    _resident(sc, 5, 2, "Garrick", "old_townsman", GARRICK_CONVO,
              movement="watch",
              beats=[("beat_garrick_quiet",
                      _beat_garrick_quiet, [
                          "The reverend's gone quiet. Any other week you'd "
                          "hear him clear from here, worked up over "
                          "something or other.",
                          "Nothing out of him for days now. Man spends his "
                          "life raising his voice, then nothing at all.",
                          "You go by and look in on him, son. Somebody "
                          "ought to.",
                      ])])
    return sc


def build_pell_yard():
    """OLD PELL'S, at the dead end of the lane.

    He grew the town's pride, the northernmost corn in the world, and he will
    not look long at the fields that died standing when the fall harvest went
    uncut (NARRATIVE §3). So the corn is the whole yard: the band is deeper
    here than anywhere else on the string and it comes right up to the lot,
    because he has not cut it and will not.

    His yard is the one that is not INTERRUPTED. Everybody else's stopped
    mid-motion in January; his is HELD, deliberately, by a man who says so out
    loud: the genset runs, the can beside it is full, and the calendar is
    nailed up on his own siding with the date he chose to stop on. Nothing
    here is waiting to be finished. That is the point of it.

    The seed crates are the tell that separates held from finished: stacked,
    roped, and never opened, for a planting he is not going to do.
    """
    sc, y = build_yard_scene(
        "pell_yard",
        door_face="n", door_char="D",
        interior="pell_house", interior_spawn="from_pell_yard",
        path_side="n", path_char="e",
        path_target="lane_end", path_spawn="from_pell_yard",
        verge=("C", "A"), building=(8, 6), seed=163, band=5)
    y.step()
    y.genset(running=True, side="e", along=0.5)
    y.crates(y.left - 2, y.bot + 2, courses=3, tarp=True)
    y.crates(y.left - 2, y.bot + 4, courses=2, seed=167)
    # THE CALENDAR, on HIS wall. It has been nailed to the schoolhouse all
    # this time, which was never his building -- he only loiters there.
    y.siding("calendar", y.right + 1, y.top + 2)
    y.mailbox(y.out[0] + 3, y.lot[2], toward="n", full=True)
    y.fence("n", at=y.lot[2], span=(y.lot[0], y.lot[1]), gate=y.out[0])
    return sc


def build_pell_house():
    """OLD PELL'S, inside. One room, and the whole of it is arranged against
    the window: his chair faces the wall, because the fields are out there and
    he will not look at them. The almanac he stopped writing in is on the
    table with the pencil still beside it."""
    sc = _small_house("pell_house", "pell_yard", [
        "WWWWWWWWWWWW",
        "W..........i",
        "W..........W",
        "W..........W",
        "W..........W",
        "W..........W",
        "W....D.....W",
        "WWWWWWWWWWWW",
    ])
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_pell_yard", 5, 5)
    sc.add_furniture("stove", [(1, 1)], w=30, h=40)
    sc.add_furniture("table", [(4, 2)], w=30, h=26)
    sc.add_furniture("cot", [(9, 4)], w=30, h=16)
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 6, "papers"))
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 18,
                                 "kerosene_lamp"))
    # THE CHAIR TURNED AWAY. The window is east, onto his own dead fields;
    # the chair sits between him and it with its back to the glass.
    sc.add_decoration(Decoration(9 * TILE + 16, 1 * TILE + 16,
                                 "overturned_chair"))
    _resident(sc, 3, 4, "Old Pell", "old_townsman", PELL_CONVO,
              movement="idle", beats=[
        # The newspaper's ripple (TODO #2): once the PI has spent the one
        # copy on him, the stopped-calendar line would be a lie -- he picked
        # the pencil back up. The marked beat fires first and the coal beat
        # stands down for good.
        ("beat_pell_marked",
         _beat_pell_marked, [
             "Wrote the date in this morning. April 15, plain as "
             "you like. First one since the winter.",
             "[c=dim]Can't say it did anything. Can't say it "
             "didn't. I'll write tomorrow in tomorrow.[/c]",
         ]),
        ("beat_pell_coal",
         _beat_pell_coal, [
             "You've been digging at it. I can tell. It's on you like "
             "coal dust.",
             "Whatever you're finding out there, don't bring it up my "
             "step. I've got the calendar where I want it. Stopped. Some "
             "of us need it stopped.",
         ]),
    ])
    return sc
