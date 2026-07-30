"""THE CORRIDOR FIELD -- the deck (`scenes/lost_pieces.py`) turned into rooms.

One drawn 20x20 piece is one SCENE. Walking out of a mouth crosses into the
next room. The director decides which piece lies beyond a mouth and nothing
else: no shape is ever generated (`DESIGN.md` §13, the maintainer's ruling).

WHAT THIS IS BUILT OUT OF. Nothing here is a new spatial system. Every trick
the field runs is one the game already had, pointed at a new job:

  * `Game.cross_fold` -- the ONE seamless traversal. No fade, no sting,
    stride and screen position preserved. It carries every mouth crossing, so
    walking room to room is walking, not loading. This is the whole reason a
    room can be 20 tiles across and the field still feel continuous.
  * The SAME-SCENE fold (the cornfield maze's relocation) -- the warp panes.
    `cross_fold` to your own key with a destination is silent by
    construction: there is no frame to see, so the room itself is the lie.
  * The SIGHT CONE (`rendering.sight.visible_factor`, the blind-spot buffer)
    -- both shift laws read it. The generated fields move scenery only when
    it is OUT of the cone; the shifting span here moves only when it is IN
    it. Same buffer, opposite sign, and the pair is the point: the field lies
    behind your back and the architecture moves in your face.
  * `terrain.invalidate_tilt_objects()` -- the span is a real edit to the
    room's object grid mid-play, the same call the chopped boards use.
  * The `x` object char (solid, `see_over`) under the `@` void floor -- the
    gap you can see across and cannot cross, out of two chars that already
    existed.
  * `Game._lost_return` -- the anchor `_tick_lost_edge` writes on the way in.
    Reaching the light spends it and puts you back where the world let go.
  * `Scene.lit_at` -- lit ground is pinned. The field is allowed to lie about
    everything except where you have stood and what is lit.

THE TWO SHIFT LAWS.

  WATCHED     a `moving_stair`'s span slides between its sockets while it is
              inside your sight cone and you are not standing on it.
  DISCOVERED  a room you are not in and cannot see may be re-decided, so the
              way back is real and is not the room you walked through. The
              mouth grammar holds through the swap, so the corridor never
              tears.

PINNED, and never re-decided: the room you are in, any room you have stood
in that holds a light, and the room holding the way out.
"""
import math

from scenes.base import Scene, TILE
from entities.decoration import Decoration
from scenes import lost_pieces as LP

# ---- the field's material, per biome ---------------------------------------
# The deck authors SHAPE; this authors MATERIAL. A wall is a stand of trees in
# the forest, a wall of corn in the corn, and a black nothing on the road.
# SMALL vs BIG is not decoration, it is fit. A corridor is two tiles wide and
# a rust hulk is wider than that, so scattering vehicles through corridors
# stacks three of them on one bend and reads as a scrapyard rather than a
# road. Big things are placed only where there is genuinely room around them
# (see `_ROOMY`), which is what makes the gallery and the hub feel like the
# rooms they are drawn as.
BIOMES = {
    "road":   {"floor": "d", "wall": "#", "music": "village",
               "small": ("tin_cans", "glass_litter", "crate_stack",
                         "boulder"),
               "big": ("rust_sedan", "rust_wagon", "rust_van", "rust_coupe")},
    "forest": {"floor": "g", "wall": "T", "music": "village",
               "small": ("grass_tuft", "tall_grass", "log_seat", "leaves"),
               "big": ("creepy_tree", "standing_stone", "boulder")},
    "corn":   {"floor": "g", "wall": "C", "music": "village",
               "small": ("tall_grass", "grass_tuft", "corn_doll",
                         "tin_cans"),
               "big": ("corn_altar", "standing_stone", "wheelbarrow")},
}
_ROOMY = 1      # tiles of open ground on every side before a BIG thing fits

VOID_FLOOR = "@"        # near-black ground
VOID_OBJECT = "x"       # solid, see_over: seen across, never crossed

_EDGE_BAND = 0.9        # tiles: this close to the edge and pressing out
_SPAN_EVERY = 2.4       # seconds between a watched span's moves
_WARP_KIND = "standing_stone"    # what a warp pane stands as, per biome below
_WARP_PROP = {"road": "rust_coupe", "forest": "standing_stone",
              "corn": "corn_altar"}
_EXIT_KIND = "lantern"  # the way out, the same warm light the fields use
_EXIT_REACH = 2.2       # tiles: this close to it and you have climbed out
_EXIT_AFTER = 4         # rooms crossed before the way out may be dealt
_SCATTER_PER_ROOM = 5

_OPP = {"n": "s", "s": "n", "e": "w", "w": "e"}
_STEP = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}


def _hash01(*vals):
    h = 2166136261
    for v in vals:
        h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    return ((h >> 8) & 0xffff) / 65535.0



def _roomy(rows, x, y):
    """Is there open ground all round this tile? Then a big thing fits."""
    for dy in range(-_ROOMY, _ROOMY + 1):
        for dx in range(-_ROOMY, _ROOMY + 1):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < LP.SIZE and 0 <= ny < LP.SIZE):
                return False
            if rows[ny][nx] not in LP._WALKABLE:
                return False
    return True


def _pick(cfg, rows, x, y, h):
    lib = cfg["big"] if _roomy(rows, x, y) else cfg["small"]
    return lib[int(h * len(lib)) % len(lib)]


# ============================================================ THE DIRECTOR ==
class LostField:
    """One field: which piece sits in which cell, and what is allowed to move.

    A CELL is a coordinate in the field, not a place. The piece standing in it
    is a decision, and outside the pinned set it is a decision the field is
    free to take again once you cannot see the room it made.
    """

    def __init__(self, root, biome, seed=1):
        self.root = root
        self.biome = biome if biome in BIOMES else "road"
        self.seed = seed & 0x7fffffff
        self.cells = {}          # cell -> (piece_name, orientation index)
        self.gen = {}            # cell -> how many times it has been decided
        # Where a shifting span is parked, per CELL. It lives here and not in
        # the deck because a piece is drawn once and placed many times:writing
        # the moved span back into the deck would slide every other copy of
        # that room at the same instant.
        self.span = {}           # cell -> socket offset
        self.visited = set()     # cells the player has actually stood in
        self.pinned = set()      # cells that may never be re-decided
        self.here = (0, 0)
        self.crossings = 0
        self.exit_cell = None
        self._placements = _placements()
        self.deal((0, 0))

    # ---- keys ----
    def key_for(self, cell):
        if cell == (0, 0):
            return self.root
        return "%s@%d,%d" % (self.root, cell[0], cell[1])

    def cell_for(self, key):
        if key == self.root:
            return (0, 0)
        if "@" not in key:
            return None
        try:
            cx, cy = key.split("@", 1)[1].split(",")
            return (int(cx), int(cy))
        except ValueError:
            return None

    # ---- dealing ----
    def edges_of(self, cell):
        rows = self.rows_at(cell)
        return {s: LP.edge_slots(rows, s) for s in "nesw"} if rows else None

    def rows_at(self, cell):
        got = self.cells.get(cell)
        if got is None:
            return None
        name, orient = got
        rows = _placements()[name][orient]
        at = self.span.get(cell)
        return LP.with_span_at(rows, at) if at is not None else rows

    def deal(self, cell, avoid=None):
        """Choose the piece for one cell, honouring every decided neighbour.

        The constraint IS the geography: for each neighbour already standing,
        the edge this piece shows it must carry the same mouth offsets. A
        piece that cannot satisfy every side is never considered, so the field
        cannot open a corridor into a wall or close the way you came.
        """
        want = {}
        for side, (dx, dy) in _STEP.items():
            nb = (cell[0] + dx, cell[1] + dy)
            n_edges = self.edges_of(nb)
            if n_edges is not None:
                want[side] = n_edges[_OPP[side]]
        legal = []
        for name, rots in self._placements.items():
            if name == avoid:
                continue
            for i, rows in enumerate(rots):
                if all(LP.edge_slots(rows, s) == sl for s, sl in want.items()):
                    legal.append((name, i))
        if not legal and avoid is not None:
            return self.deal(cell, avoid=None)
        if not legal:
            # Nothing in the deck fits. Cannot happen while the deck passes
            # its gate check, and if it ever does the honest answer is a
            # dead end rather than a hole in the world.
            legal = [("deadend_find", 0)]
        fresh = cell not in self.cells
        g = self.gen.get(cell, 0)
        pick = legal[int(_hash01(self.seed, cell[0], cell[1], g,
                                 len(legal)) * len(legal)) % len(legal)]
        self.cells[cell] = pick
        self.gen[cell] = g + 1
        self.span.pop(cell, None)
        # The way out is dealt once you are deep enough in to have earned it,
        # and the room holding it is pinned from that moment: a light never
        # lies, so the way home cannot be somewhere else when you come back.
        if (fresh and self.exit_cell is None and cell != (0, 0)
                and len(self.visited) >= _EXIT_AFTER):
            self.exit_cell = cell
            self.pinned.add(cell)
        return pick

    def ensure(self, cell):
        if cell not in self.cells:
            self.deal(cell)
        return self.cells[cell]

    # ---- the DISCOVERED law ----
    def arrive(self, cell):
        """The player has stepped into a room. Re-decide what they left."""
        self.here = cell
        self.visited.add(cell)
        self.crossings += 1
        # A room you stood in and that was LIT stays put; the rest of what is
        # behind you is fair game once you are a room away from it.
        for done in list(self.cells):
            if done == cell or done in self.pinned:
                continue
            if abs(done[0] - cell[0]) + abs(done[1] - cell[1]) < 2:
                continue
            if done in self.visited and self._room_is_lit(done):
                self.pinned.add(done)
                continue
            was = self.cells[done][0]
            self.deal(done, avoid=was)

    def _room_is_lit(self, cell):
        rows = self.rows_at(cell)
        return bool(rows) and any(LP.LIT in r for r in rows)

    def neighbour(self, cell, side):
        dx, dy = _STEP[side]
        nb = (cell[0] + dx, cell[1] + dy)
        self.ensure(nb)
        return nb


_PLACEMENT_CACHE = {}


def _placements():
    """Every drawn piece in its eight orientations, built once.

    Kept as a list per piece rather than a set so an orientation index is a
    stable name for one placement: the director stores (piece, index), and a
    room rebuilt from that pair has to come back the same shape.
    """
    if not _PLACEMENT_CACHE:
        for name, p in LP.DECK.items():
            _PLACEMENT_CACHE[name] = LP.orientations(p["rows"])
    return _PLACEMENT_CACHE


# The live field. One at a time: you are only ever lost in one place, and a
# fresh descent is a fresh field (the way back you learned is spent).
FIELD = None


def field_for(key):
    """The field this scene key belongs to, or None."""
    if FIELD is None or not isinstance(key, str):
        return None
    if key == FIELD.root or key.startswith(FIELD.root + "@"):
        return FIELD
    return None


def is_field_key(key):
    """True for any room key the field owns, live field or not.

    `scenes.load_scene` asks this BEFORE the field exists on a cold load (a
    test, a preview), so it cannot go through `field_for`.
    """
    return isinstance(key, str) and "@" in key and key.startswith("lost_")


# ============================================================== THE ROOM ====
def build_room(key):
    """One cell of the live field as a real Scene.

    Called by `scenes.load_scene` for any `lost_*@x,y` key, and directly for
    the field's root. A room built for a key the live field does not own
    starts a new field there, so a direct load (a preview, a harness) lands in
    a coherent place rather than a blank.
    """
    global FIELD
    fld = field_for(key)
    if fld is None:
        root = key.split("@", 1)[0]
        biome = root.replace("lost_", "") or "road"
        FIELD = LostField(root, biome)
        fld = FIELD
        cell = fld.cell_for(key)
        if cell is not None and cell != (0, 0):
            fld.ensure(cell)
    cell = fld.cell_for(key)
    if cell is None:
        cell = (0, 0)
    fld.ensure(cell)
    return _make(fld, cell)


def enter_field(root, biome, seed=None):
    """Start a new field and hand back its entry room's key.

    Called by the scene builders the mouths already point at, so falling
    through a treeline needs no new plumbing: `Game._tick_lost_edge` crosses
    to `lost_road` exactly as before and gets a corridor instead of a sea.
    """
    global FIELD
    if seed is None:
        seed = 1
    FIELD = LostField(root, biome, seed)
    return FIELD.root


def _make(fld, cell):
    rows = fld.rows_at(cell)
    cfg = BIOMES[fld.biome]
    floor, obj = [], []
    for r in rows:
        f_row, o_row = [], []
        for ch in r:
            if ch == LP.WALL:
                f_row.append(cfg["floor"])
                o_row.append(cfg["wall"])
            elif ch == LP.VOID:
                f_row.append(VOID_FLOOR)
                o_row.append(VOID_OBJECT)
            else:
                f_row.append(cfg["floor"])
                o_row.append(".")
        floor.append("".join(f_row))
        obj.append("".join(o_row))

    sc = Scene(fld.key_for(cell), floor, object_rows=obj, music=cfg["music"])
    # Wordless, like every lost space: the corner label would name the thing
    # the room exists to leave unnamed (conventions check 6).
    sc.display_name = ""
    sc.skybox_kind = "void"
    # NOT AN AUTHORED TILE GRID, so the harnesses that treat one as saveable
    # data skip it (`tests/layouts.py`) the same way they skip the generated
    # fields. A room's layout is the DECK plus the director's (piece,
    # orientation) for its cell; writing the grid down would save a hand of
    # cards as if it were the deck. Reachability, the thing smoke's flood fill
    # would check, is asserted on every drawn piece by conventions check 15
    # and on every dealt seam by `tests/lost_field.py`.
    sc.procedural = True
    sc.cult_target = 0
    sc.hide_spots = []
    sc._field = fld
    sc._cell = cell
    sc._span_t = _SPAN_EVERY
    sc._warp_lock = False
    # Seeded at the room's own centre so the first frame after a crossing has
    # a motion to read (see `_tick_cross`).
    sc._prev_pos = None

    # spawns: one per mouth tile so a crossing lands where it should, plus a
    # centre for a direct load
    open_tiles = [(x, y) for y in range(LP.SIZE) for x in range(LP.SIZE)
                  if rows[y][x] in LP._WALKABLE]
    cx, cy = open_tiles[len(open_tiles) // 2] if open_tiles else (10, 10)
    sc.spawns = {"default": (cx * TILE + TILE // 2, cy * TILE + TILE // 2)}

    _dress(sc, fld, rows, cfg)
    sc.on_update_fn = _room_tick
    return sc


def _dress(sc, fld, rows, cfg):
    """Props: the lights that pin a room, the finds, the warps, the scatter.

    Deliberately thin. The backrooms read is emptiness plus the occasional
    wrong thing, and a corridor whose walls are already a wall of corn does
    not want furniture in it as well.
    """
    sc._warps = []
    sc._exit_light = None
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            wx, wy = x * TILE + TILE // 2, y * TILE + TILE // 2
            if ch == LP.LIT:
                sc.add_decoration(Decoration(wx, wy, "lantern", seed=x * 7 + y))
            elif ch == LP.FIND:
                k = _pick(cfg, rows, x, y, _hash01(fld.seed, x, y))
                sc.add_decoration(Decoration(wx, wy, k, seed=x + y * 13))
            elif ch in (LP.WARP_A, LP.WARP_B):
                sc._warps.append((wx, wy))
                sc.add_decoration(Decoration(
                    wx, wy, _WARP_PROP.get(fld.biome, _WARP_KIND),
                    seed=x * 5 + y))
    # THE WAY OUT. A warm light in a room you had to walk to, and the room is
    # pinned the moment it is dealt, so it is still there when you come back.
    if fld.exit_cell == sc._cell:
        spot = None
        for y in range(LP.SIZE - 1, -1, -1):
            for x in range(LP.SIZE):
                if rows[y][x] == LP.OPEN:
                    spot = (x, y)
                    break
            if spot:
                break
        if spot:
            d = Decoration(spot[0] * TILE + TILE // 2,
                           spot[1] * TILE + TILE // 2, _EXIT_KIND, seed=3)
            sc.add_decoration(d)
            sc._exit_light = d
    # Sparse scatter -- and NOT on any tile the corridor needs. A rust hulk
    # is a solid prop and a corridor is two tiles wide, so a scatter placed
    # by "somewhere open, not near the edge" walls the room off perfectly
    # legally: the piece stays reachable and the ROOM does not. Every
    # candidate is tested by blocking it and re-flooding, which is the same
    # reachability the deck's own check runs.
    free = [(x, y) for y in range(2, LP.SIZE - 2) for x in range(2, LP.SIZE - 2)
            if rows[y][x] == LP.OPEN]
    blocked = set()
    placed = 0
    for i in range(_SCATTER_PER_ROOM * 4):
        if placed >= _SCATTER_PER_ROOM or not free:
            break
        j = int(_hash01(fld.seed, sc._cell[0], sc._cell[1], i, len(free))
                * len(free)) % len(free)
        x, y = free.pop(j)
        if _would_wall_off(rows, blocked | {(x, y)}):
            continue
        blocked.add((x, y))
        placed += 1
        k = _pick(cfg, rows, x, y, _hash01(x, y, i))
        sc.add_decoration(Decoration(x * TILE + TILE // 2,
                                     y * TILE + TILE // 2, k,
                                     seed=(i * 31 + x) & 0xffff))



def _would_wall_off(rows, blocked):
    """True when filling `blocked` costs a mouth the room it could reach.

    The test is per MOUTH, not for the room as a whole: `twin_run` is two
    channels that never meet, so "all mouths reach each other" was never the
    rule. What must hold is that no mouth loses anything it had.
    """
    grid = [list(r) for r in rows]
    for (x, y) in blocked:
        grid[y][x] = LP.WALL
    grid = ["".join(r) for r in grid]
    mouths = LP.mouth_tiles(rows)
    for m in mouths:
        was = {o for o in mouths if o in LP.reachable_from(rows, m)}
        now = {o for o in mouths if o in LP.reachable_from(grid, m)}
        if was != now:
            return True
    return False


# ============================================================== THE TICK ====
def _room_tick(game, sc, dt):
    fld = getattr(sc, "_field", None)
    if fld is None or game.player is None:
        return
    if _tick_exit(game, sc):
        return
    if _tick_warp(game, sc):
        return
    _tick_span(game, sc, dt)
    _tick_cross(game, sc, fld)


def _tick_exit(game, sc):
    """Reach the light and the world takes you back where it let go."""
    d = getattr(sc, "_exit_light", None)
    if d is None:
        return False
    p = game.player
    if math.hypot(d.x - p.x, d.y - p.y) > _EXIT_REACH * TILE:
        return False
    ret = getattr(game, "_lost_return", None)
    if ret is not None:
        game._lost_return = None
        clear_field()
        game.cross_fold(ret[0], dest_pos=(ret[1], ret[2]))
        return True
    return False


def _tick_warp(game, sc):
    """The warp panes: a same-scene fold, which is silent by construction.

    The lock is what keeps it from being a loop: you have to step OFF a pane
    before either one will take you again, or arriving on the partner would
    immediately send you back.
    """
    warps = getattr(sc, "_warps", None)
    if not warps or len(warps) < 2:
        return False
    p = game.player
    near = None
    for i, (wx, wy) in enumerate(warps):
        if math.hypot(wx - p.x, wy - p.y) < TILE * 0.7:
            near = i
            break
    if near is None:
        sc._warp_lock = False
        return False
    if sc._warp_lock:
        return False
    sc._warp_lock = True
    other = warps[(near + 1) % len(warps)]
    game.cross_fold(sc.key, dest_pos=other)
    return True


def _tick_span(game, sc, dt):
    """THE WATCHED LAW: the span moves while you are looking straight at it.

    The generated fields move scenery only when it is OUT of your cone. This
    is the same buffer read the other way, and the inversion is deliberate:
    one of them is the field lying behind your back, and this one is the
    architecture refusing to hold still in front of your face. It never moves
    under you, because a bridge that vanishes from beneath the player is a
    death, not a dread.
    """
    rows = sc._field.rows_at(sc._cell)
    if not rows or not any(LP.SHIFT in r for r in rows):
        return
    sc._span_t -= dt
    if sc._span_t > 0.0:
        return
    sc._span_t = _SPAN_EVERY
    sockets = LP.span_sockets(rows)
    if len(sockets) < 2:
        return
    band = LP._gap_band(rows)
    if band is None:
        return
    across, lo, hi = band
    here = None
    for r in range(LP.SIZE):
        for c in range(LP.SIZE):
            if rows[r][c] == LP.SHIFT:
                here = c if across else r
                break
        if here is not None:
            break
    if here is None:
        return
    p = game.player
    ptx, pty = int(p.x // TILE), int(p.y // TILE)
    span_cells = [(d, a) if across else (a, d)
                  for d in range(lo, hi + 1)
                  for a in range(here, here + LP.MOUTH_W)]
    if (pty, ptx) in span_cells:
        return                       # never out from under them
    from rendering.sight import visible_factor
    look = getattr(game, "look", None)
    heading = getattr(look, "aim", 0.0) if look else 0.0
    mid = span_cells[len(span_cells) // 2]
    mx, my = mid[1] * TILE + TILE // 2, mid[0] * TILE + TILE // 2
    if visible_factor(p.x, p.y, heading, mx, my, sc.blocks_sight) <= 0.0:
        return                       # only ever moves while it is watched
    nxt = [s for s in sockets if s != here]
    sc._span_n = getattr(sc, "_span_n", 0) + 1
    # The move counter is mixed hard before it is hashed. Fed in raw it made
    # the span oscillate between two sockets and visit the third about one
    # time in twelve, which reads as a bridge stuck between two positions
    # rather than one that goes anywhere.
    pick = nxt[int(_hash01(sc._field.seed, sc._cell[0] * 7919,
                           sc._cell[1] * 104729,
                           (sc._span_n * 2654435761) & 0xffffffff, here)
                   * len(nxt)) % len(nxt)]
    sc._field.span[sc._cell] = pick
    _restamp_span(sc, rows, LP.with_span_at(rows, pick))


def _restamp_span(sc, old_rows, new_rows):
    """Write the span's new position into the live object grid.

    A real edit to `Scene.objects` mid-play, so the tilt caches have to be
    told: `invalidate_tilt_objects` is the same call the chopped boards make.
    """
    from scenes.terrain import invalidate_tilt_objects
    cfg = BIOMES[sc._field.biome]
    for y in range(LP.SIZE):
        for x in range(LP.SIZE):
            if old_rows[y][x] == new_rows[y][x]:
                continue
            ch = new_rows[y][x]
            if ch == LP.VOID:
                sc.floor[y][x] = VOID_FLOOR
                sc.objects[y][x] = VOID_OBJECT
            else:
                sc.floor[y][x] = cfg["floor"]
                sc.objects[y][x] = "."
    invalidate_tilt_objects()


def _tick_cross(game, sc, fld):
    """Walk out of a mouth and the next room is already there.

    `cross_fold` keeps the stride and the screen position, and the arrival
    point is the same offset on the facing edge, so the two rooms read as one
    continuous corridor with a seam you cannot find.
    """
    p = game.player
    span = LP.SIZE * TILE
    band = _EDGE_BAND * TILE
    # You go through by WALKING through, never by standing near it. Without
    # this the band is a suction cup: idle a stride from the wall and the room
    # hands you on. `_tick_lost_edge` takes the movement intent as an
    # argument; a scene update only gets dt, so the motion comes from the last
    # frame's position, which also means a shove or a fold arriving on the
    # edge cannot fire it either.
    prev = getattr(sc, "_prev_pos", None)
    sc._prev_pos = (p.x, p.y)
    if prev is None:
        return
    vx, vy = p.x - prev[0], p.y - prev[1]
    side = None
    if p.y < band and vy < 0:
        side = "n"
    elif p.y > span - band and vy > 0:
        side = "s"
    elif p.x < band and vx < 0:
        side = "w"
    elif p.x > span - band and vx > 0:
        side = "e"
    if side is None:
        return
    rows = fld.rows_at(sc._cell)
    tx, ty = int(p.x // TILE), int(p.y // TILE)
    edge_i = tx if side in "ns" else ty
    if not any(s <= edge_i < s + LP.MOUTH_W
               for s in LP.edge_slots(rows, side)):
        return                        # against the wall, not in the mouth
    nb = fld.neighbour(sc._cell, side)
    if side == "n":
        dest = (p.x, span - band * 1.2)
    elif side == "s":
        dest = (p.x, band * 1.2)
    elif side == "w":
        dest = (span - band * 1.2, p.y)
    else:
        dest = (band * 1.2, p.y)
    fld.arrive(nb)
    game.cross_fold(fld.key_for(nb), dest_pos=dest)


# ---- the biome entry points the mouths already name ------------------------
def clear_field():
    """Forget the field. A fresh descent is a fresh place.

    Called when the player climbs out and from `_reset_run_state`, so a New
    Game never walks back into the corridors it left in the last one.
    """
    global FIELD
    FIELD = None


def build_lost_road_field():
    """The room the mouth drops you in, and the room you come back to.

    The registry key IS cell (0, 0), so `Game._tick_lost_edge` crossing to
    `lost_road` needs no new plumbing. It must therefore answer twice with the
    same room: once when the world lets go of you, and again every time the
    corridors bring you back round to where you started. So a new field is
    started only when there is no live one, and leaving is what ends it.
    """
    if FIELD is not None and FIELD.root == "lost_road":
        FIELD.ensure((0, 0))
        return _make(FIELD, (0, 0))
    return build_room(enter_field("lost_road", "road"))
