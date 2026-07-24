"""THE LOST SPACES -- procedurally generated, NON-REPEATING backrooms fields
(TODO #26 / the in-between). You fall off a dark edge of the safe world into a
dark liminal field, land at a lit FOCAL POINT (a hand-authored island), and the
only way out is a light you HUNT once you leave that island's glow.

Design (the maintainer's model): a HAND-MADE ISLAND in a SEA OF GENERATION. The
field is mostly EMPTY ground with sparse, uncanny things to find (the backrooms
feeling is emptiness + the occasional wrong thing, never a wall of texture). At
the centre sits the biome's FOCAL ISLAND -- a lit safe-feeling place that is a
dead end. Three biomes, each with its own island and its own light:

  * CORN   -- a CROP CIRCLE: a grass clearing ringed by a full wall of corn,
              with an ABANDONED CULT CAMP and a bonfire at the centre whose glow
              fills the whole circle.
  * FOREST -- a still, pretty POND on a mossy bank, lit by lanterns someone left
              hanging on posts around the water.
  * ROAD   -- a derelict filling STATION you cannot enter, its cold NEON sign
              still buzzing over two dead pumps.

While you stand in the island's light there is no way out; leave the glow and
the EXIT LIGHT (a warm lantern) appears in the dark, held 6-20 tiles off,
relocating out of your sight so it stays findable. You escape the lit dead end
by walking into the dark and hunting the way out.

Architecture (from the engine map): the tilt renderer is already a rolling
window keyed on the camera, and collision/sight route through char_object_at /
char_floor_at which index self.objects / self.floor. So a Scene whose floor /
objects are GENERATOR-backed proxies, with a large finite w/h and the player
spawned at the CENTRE, gets collision + sight + tilt render for free -- the map
edge is hundreds of tiles away and never enters the window. Non-repeating comes
from hashing the world tile coord. Nav is replaced (return None -> straight-line
chase). No re-origin in the prototype (a 400-tile bound is a long walk); the
production build adds per-chunk streaming + silent re-origin for a truly endless
walk (TODO #26).
"""
import math

from scenes.base import Scene, TILE
from entities.decoration import Decoration

# per-biome scatter libraries -- ONLY tilt-safe kinds (SOLID_PROPS volumes or
# grounded STANDEE cards; a kind in neither renders as a flat floor sticker
# under the only shipping camera). Weighted by repetition.
_SCATTER = {
    "corn": ("creepy_tree", "creepy_tree", "creepy_tree", "wheelbarrow",
             "rust_sedan", "rust_wagon", "rust_van", "standing_stone",
             "corn_altar", "tall_grass"),
    "forest": ("creepy_tree", "creepy_tree", "creepy_tree", "creepy_tree",
               "tall_grass", "grass_tuft", "standing_stone", "log_seat"),
    "road": ("rust_sedan", "rust_wagon", "rust_van", "rust_coupe",
             "wheelbarrow", "standing_stone", "creepy_tree", "boulder"),
}
# ground detailing scattered across the lit clearing so the flat floor breaks
# up (small blades + leaf litter). Standees + a floor decal, all tilt-safe.
_GROUND_DETAIL = ("grass_tuft", "grass_tuft", "tall_grass", "leaves")

_EXIT_KIND = "lantern"     # the hunted way-out light (warm, non-electric)

_MIN_EXIT = 6              # tiles: the exit never sits closer (always a hunt)
_MAX_EXIT = 20             # tiles: nor farther (always escapable)
_REACH = 2.2              # tiles: this close to the exit = you climbed out

# per-biome focal + haven geometry (tiles). `haven_r` is how far the island's
# light protects (leave it and the exit hunt begins); `spawn_off` drops the
# player that many tiles SOUTH of the focal centre so they face the island.
_BIOME = {
    "corn":   {"clear_r": 4.5, "ring_w": 2.5, "haven_r": 8.5, "spawn_off": 3.0},
    "forest": {"pond_r": 4.2, "haven_r": 7.0, "spawn_off": 6.5},
    "road":   {"haven_r": 9.5, "spawn_off": 0.6, "road_amp": 8.0,
               "road_half": 2.6, "road_off": 6.5, "road_drift": 0.14},
}


class LostSpace(Scene):
    """A generator-backed, non-repeating dark field with a lit focal island.
    See the module docstring."""

    def __init__(self, key="lost_corn", biome="corn", seed=1,
                 size=400, exit_to="lodge_yard", music="village"):
        super().__init__(key, ["."], object_rows=["."], music=music)
        self._seed = seed & 0x7fffffff
        self._biome = biome if biome in _BIOME else "corn"
        self._cfg = _BIOME[self._biome]
        self._exit_to = exit_to
        self.w = self.h = size
        self.procedural = True                    # smoke skips flood/full scans
        self._cx = self._cy = size // 2           # focal centre tile (map centre)
        self.floor = _GenGrid(self._floor_at, size)
        self.objects = _GenGrid(self._obj_at, size)
        # the lit island centre (world coords) -- the haven-glow anchor
        self._fx = self._cx * TILE + TILE // 2
        self._fy = self._cy * TILE + TILE // 2
        # the ROAD's meander anchor + the fenced station LOT it sits beside.
        self._road_n0 = 0.0
        self._lot = None
        if self._biome == "road":
            self._road_n0 = self._vnoise(self._cy * 0.035 + 13, 4.0, salt=15)
            # lot rectangle in TILES (x0,x1,y0,y1), west+north of the pylon at
            # the focal; the road runs past its east edge via the driveway.
            self._lot = (self._cx - 9, self._cx + 1, self._cy - 10, self._cy + 2)
        # spawn the player a few tiles south of the island, facing it
        sx = self._fx
        sy = self._fy + int(self._cfg["spawn_off"] * TILE)
        self.spawns = {"default": (sx, sy)}
        self.skybox_kind = "void"                 # near-black surround, not sky
        {"corn": self._build_corn_camp,
         "forest": self._build_forest_pond,
         "road": self._build_road_station}[self._biome]()
        self._scatter_ground_detail()
        self._scatter_things(count=84, radius=72)
        self._exit_light = None                   # spawns only once you leave
        self._hunting = False
        self.on_update_fn = self._tick

    # ================= the focal islands (hand-authored) =====================
    def _build_corn_camp(self):
        """CORN: the abandoned cult camp at the heart of the crop circle. A
        bonfire (the zone's light) with bedrolls and log seats around it."""
        cx, cy = self._fx, self._fy
        self.add_decoration(Decoration(cx, cy, "haven_fire", seed=71, scale=1.5))
        for (dx, dy, kind, sd) in (
                (-46, -6, "bedroll", 1), (40, -14, "bedroll", 2),
                (-10, 44, "bedroll", 3), (50, 22, "log_seat", 4),
                (-52, 26, "log_seat", 5), (14, -46, "log_seat", 6),
                (58, -30, "wheelbarrow", 7), (-60, -34, "corn_altar", 8)):
            self.add_decoration(Decoration(cx + dx, cy + dy, kind, seed=sd))

    def _build_forest_pond(self):
        """FOREST: a still pond on a mossy bank. A fisher's fire someone left
        burning on the near bank throws the light (and reflects in the water),
        with lanterns on posts around the far shore, reeds, and a low mist."""
        cx, cy = self._fx, self._fy
        pr = self._cfg["pond_r"] * TILE
        # the near-bank fire: the zone's warm light, mirrored in the pond. Set
        # to one side of the bank so the player (who lands further back) sees
        # it burning between them and the water, not standing on it.
        self.add_decoration(Decoration(cx - 40, cy + pr + 4, "camp_fire", seed=17))
        # lanterns on stub posts around the far/side banks
        for a in (0.6, 2.1, 4.2):
            lx = cx + math.cos(a) * (pr + 26)
            ly = cy + math.sin(a) * (pr + 26)
            self.add_decoration(Decoration(lx, ly, "lantern", seed=int(a * 40)))
        # reeds + a fallen log + real 3D boulders on the bank
        for i, (dx, dy, kind) in enumerate((
                (-8, -pr - 18, "tall_grass"), (24, -pr - 10, "tall_grass"),
                (pr + 20, 10, "log_seat"), (-pr - 24, -6, "tall_grass"),
                (18, pr + 24, "tall_grass"), (-34, pr + 18, "grass_tuft"),
                (pr + 16, -30, "boulder"), (-pr - 20, 34, "boulder"),
                (pr + 34, -40, "creepy_tree"), (-pr - 40, 28, "creepy_tree"))):
            self.add_decoration(Decoration(cx + dx, cy + dy, kind, seed=i + 20))
        # a breathing mist lying on the water
        self.add_decoration(Decoration(cx, cy, "mist", seed=5,
                                       w=int(pr * 2.2), h=int(pr * 1.6)))

    def _build_road_station(self):
        """ROAD: a fenced filling-station LOT beside the winding road. You land
        under the tall NEON PYLON at the driveway; the sealed store + its pump
        canopy sit at the lot's north-west, parking bays are painted on the
        lot, a chain-link fence rings it (open at the driveway), and wrecks are
        stalled on the road and in a bay."""
        T = TILE
        cx, cy = self._fx, self._fy
        cxi, cyi = self._cx, self._cy

        def W(txo, tyo):                   # tile-offset (from focal) -> world px
            return ((cxi + txo) * T + T // 2, (cyi + tyo) * T + T // 2)

        # the neon pylon = the beacon you spawn under (the driveway corner)
        self.add_decoration(Decoration(cx, cy, "neon_pylon", seed=3))
        # the sealed store building at the lot's north-west
        self.add_decoration(Decoration(*W(-4, -5), "gas_station", seed=4))
        # the pump canopy + pumps as a SEPARATE deco, set SOUTH of the store
        # (clear of the storefront) so it also depth-sorts on its own
        self.add_decoration(Decoration(*W(-4, -1), "pump_island", seed=5))
        # painted parking bays across the open asphalt in front + a car in one
        for i, txo in enumerate((-8, -6, -4, -2)):
            self.add_decoration(Decoration(*W(txo, 1), "parking_bay", seed=i))
        self.add_decoration(Decoration(*W(-6, 1), "rust_wagon", seed=7))
        # wrecks stalled on the road (north up it, and south by the driveway)
        self.add_decoration(Decoration(*W(4, -5), "rust_van", seed=12))
        self.add_decoration(Decoration(*W(3, 6), "rust_sedan", seed=9))
        # the chain-link perimeter fence (skips the driveway gap via _on_fence)
        x0, x1, y0, y1 = self._lot
        for tx in range(x0, x1 + 1):
            for ty in (y0, y1):
                if self._on_fence(tx, ty):
                    self.add_decoration(Decoration(
                        tx * T + T // 2, ty * T + T // 2, "chain_fence",
                        seed=tx * 7 + ty, run="h", len=T))
        for ty in range(y0 + 1, y1):
            for tx in (x0, x1):
                if self._on_fence(tx, ty):
                    self.add_decoration(Decoration(
                        tx * T + T // 2, ty * T + T // 2, "chain_fence",
                        seed=tx * 3 + ty, run="v", len=T))

    # ================= the generator: deterministic per world tile ===========
    def _hash01(self, a, b, salt=0):
        h = ((int(a) & 0xffff) * 73856093) ^ ((int(b) & 0xffff) * 19349663) \
            ^ (salt * 83492791) ^ (self._seed * 2654435761)
        h &= 0xffffffff
        h ^= (h >> 13)
        h = (h * 0x5bd1e995) & 0xffffffff
        h ^= (h >> 15)
        return (h & 0xffffff) / float(0xffffff)

    def _vnoise(self, x, y, salt=0):
        x0, y0 = math.floor(x), math.floor(y)
        fx, fy = x - x0, y - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        v00 = self._hash01(x0, y0, salt)
        v10 = self._hash01(x0 + 1, y0, salt)
        v01 = self._hash01(x0, y0 + 1, salt)
        v11 = self._hash01(x0 + 1, y0 + 1, salt)
        return (v00 * (1 - fx) + v10 * fx) * (1 - fy) \
            + (v01 * (1 - fx) + v11 * fx) * fy

    def _rt(self, tx, ty):
        """distance from the focal centre, in tiles."""
        return math.hypot(tx - self._cx, ty - self._cy)

    def _road_x(self, ty):
        """The winding road's centre COLUMN at row ty (tiles). A smooth
        low-freq value-noise meander (the maintainer's 'generate it like a
        river' idea) PLUS a steady westward drift going north, so the endless
        road trends north-AND-west if you follow it. Runs a few tiles EAST of
        the station lot; the driveway bridges them at the focal row."""
        n = self._vnoise(ty * 0.035 + 13, 4.0, salt=15)
        meander = (n - self._road_n0) * self._cfg["road_amp"]
        drift = self._cfg["road_drift"] * (self._cy - ty)   # north -> west
        return self._cx + self._cfg["road_off"] + meander - drift

    def _in_lot(self, tx, ty):
        x0, x1, y0, y1 = self._lot
        return x0 <= tx <= x1 and y0 <= ty <= y1

    def _in_lot_floor(self, tx, ty):
        # the PAVED area extends one tile beyond the fence on every side, so the
        # chain-link sits ON the lot rather than floating on the dirt outside.
        x0, x1, y0, y1 = self._lot
        return x0 - 1 <= tx <= x1 + 1 and y0 - 1 <= ty <= y1 + 1

    def _in_driveway(self, tx, ty):
        # the paved apron bridging the lot's east edge to the road centreline
        return (self._cy - 1 <= ty <= self._cy + 1
                and self._lot[1] <= tx <= self._road_x(ty) + 0.5)

    def _on_fence(self, tx, ty):
        # the chain-link perimeter, minus the driveway gap on the east edge
        x0, x1, y0, y1 = self._lot
        edge = ((tx in (x0, x1) and y0 <= ty <= y1)
                or (ty in (y0, y1) and x0 <= tx <= x1))
        if tx == x1 and self._cy - 2 <= ty <= self._cy + 1:
            return False                  # the driveway opening
        return edge

    def _building_solid(self, tx, ty):
        # the sealed store block at the lot's north-west (matches the
        # gas_station deco placed at (cx-4, cy-5) tiles; see _build_road_station)
        return (self._cx - 7.3 <= tx <= self._cx - 0.7
                and self._cy - 6.6 <= ty <= self._cy - 3.4)

    def _corn_here(self, tx, ty):
        # sparse corn CLUMPS in the field: a low-freq gate so corn appears in
        # scattered patches with big EMPTY between -- not a wall of it.
        return self._vnoise(tx * 0.12 + 7, ty * 0.12 + 3, salt=8) > 0.75

    def _floor_at(self, tx, ty):
        r = self._rt(tx, ty)
        b = self._biome
        if b == "corn":
            cr = self._cfg["clear_r"]
            rw = self._cfg["ring_w"]
            if r <= cr:
                return "g"                # the crop-circle CLEARING: grass
            if r <= cr + rw:
                return ":"                # the corn RING floor
            # a clean MOAT of empty ground isolates the circle, then the
            # field's scattered corn clumps resume well beyond it.
            if r > cr + rw + 5 and self._corn_here(tx, ty):
                return ":"                # a field corn clump
        elif b == "forest":
            if r <= self._cfg["pond_r"]:
                return "~"                # the POND (animated water)
            if r <= self._cfg["pond_r"] + 1.4:
                return "d"                # muddy bank ring
            gg = self._vnoise(tx * 0.09 + 3, ty * 0.09 - 5, salt=6)
            return "G" if gg > 0.5 else "g"   # mossy forest floor
        elif b == "road":
            # the fenced station LOT + its driveway: paved, extending one tile
            # under/past the fence, gravel at the very rim
            if self._in_lot_floor(tx, ty) or self._in_driveway(tx, ty):
                x0, x1, y0, y1 = self._lot
                if not (x0 <= tx <= x1 and y0 <= ty <= y1) or ty >= y1 - 1:
                    return "d"            # gravel skirt (outside the fence + near edge)
                return "P"               # asphalt lot
            # the WINDING paved road (river-style meander, drifting west north)
            rhalf = self._cfg["road_half"]
            dxr = abs(tx - self._road_x(ty))
            if dxr < 0.7:
                return "Y"                # faded dashed centreline
            if dxr < rhalf:
                return "P"                # asphalt
            if dxr < rhalf + 1.6:
                return "d"                # gravel shoulder
            # off the road: weeds reclaiming the cracked ground (same narrow
            # brightness band as the shared field -- no black mud continents)
            return self._field_floor(tx, ty)
        return self._field_floor(tx, ty)

    def _field_floor(self, tx, ty):
        """The shared EMPTY field ground: dead grass and bare dirt in big soft
        regions, with SMALL scattered wet patches. Mud (';') is deliberately
        rare and small: it is half the luma of dirt, so at field scale it read
        as black HOLES in the world rather than as ground (caught in the first
        honest four-facing look pass). Keep the field's variation inside a
        narrow brightness band and let the LIGHT do the contrast."""
        g = self._vnoise(tx * 0.05 + 40, ty * 0.05 - 17, salt=3)
        # small high-frequency wet patches, not continent-sized mud blobs
        if self._vnoise(tx * 0.22 - 6, ty * 0.22 + 19, salt=11) < 0.24:
            return ";"
        return "g" if g > 0.52 else "d"

    def _obj_at(self, tx, ty):
        r = self._rt(tx, ty)
        b = self._biome
        if b == "corn":
            cr = self._cfg["clear_r"]
            rw = self._cfg["ring_w"]
            if r < 1.3:
                return "X"                # the bonfire footprint (don't stand in it)
            if r <= cr:
                return "."                # clear (camp decos + ground detail on top)
            if r <= cr + rw:
                # the RING: a near-solid WALL of corn you push OUT through (a
                # few passable gaps so the circle can be left anywhere).
                return "A" if self._hash01(tx, ty, salt=5) > 0.84 else "C"
            if r > cr + rw + 5 and self._corn_here(tx, ty):
                v = self._vnoise(tx * 0.36, ty * 0.36, salt=2) * 0.72 \
                    + self._hash01(tx, ty, salt=5) * 0.28
                if v > 0.56:
                    return "C"
                if v > 0.36:
                    return "A"
            return "."
        if b == "forest":
            if r <= self._cfg["pond_r"]:
                return "x"                # water: solid to the body, see over it
            # dark woods: dense tree clumps in the sea, an open bank near the pond
            if r > self._cfg["pond_r"] + 2.2:
                tv = self._vnoise(tx * 0.14 + 2, ty * 0.14 + 9, salt=4)
                if tv > 0.70:
                    return "T" if self._hash01(tx, ty, salt=6) > 0.35 else "p"
            return "."
        if b == "road":
            if self._building_solid(tx, ty):
                return "X"                # the sealed store (can't enter)
            if self._on_fence(tx, ty):
                return "x"                # chain-link: blocks the body, see over
            return "."                    # canopy/pumps/wrecks are 3D decos
        return "."

    # ---- ground detailing in the lit clearing (finite, hash-placed) ---------
    def _scatter_ground_detail(self):
        if self._biome == "road":
            return                        # no scattered weeds on the paved lot/road
        if self._biome == "corn":
            rad = self._cfg["clear_r"] * TILE
        else:
            rad = (self._cfg["pond_r"] + 2.6) * TILE
        n = 34
        for i in range(n):
            a = self._hash01(i, 511, salt=12) * math.tau
            rr = (0.8 + self._hash01(i, 733, salt=13) ** 0.5 * 0.9) * rad
            lx = self._fx + math.cos(a) * rr
            ly = self._fy + math.sin(a) * rr
            if math.hypot(lx - self._fx, ly - self._fy) < 1.4 * TILE:
                continue                  # keep the immediate focal spot clear
            k = _GROUND_DETAIL[int(self._hash01(i, 88, salt=14)
                                   * len(_GROUND_DETAIL)) % len(_GROUND_DETAIL)]
            self.add_decoration(Decoration(lx, ly, k,
                                           seed=(self._seed + i * 13) & 0xffff))

    # ---- scattered things to FIND in the sea (the exploration; sparse) -------
    def _scatter_things(self, count, radius):
        lib = _SCATTER[self._biome]
        inner = self._cfg["haven_r"] + 3
        for i in range(count):
            a = self._hash01(i, 777, salt=9) * math.tau
            rr = (inner + self._hash01(i, 313, salt=1)
                  * (radius - inner)) * TILE
            lx = self._fx + math.cos(a) * rr
            ly = self._fy + math.sin(a) * rr
            k = lib[int(self._hash01(i, 42, salt=4) * len(lib)) % len(lib)]
            self.add_decoration(Decoration(lx, ly, k,
                                           seed=(self._seed + i * 17) & 0xffff))

    # ================= the hunted exit light =================================
    def _relocate_exit(self, game):
        px, py = game.player.x, game.player.y
        aim = getattr(getattr(game, "look", None), "aim", 0.0) or 0.0
        for k in range(24):
            spin = (self._hash01(int(px), int(py) + k, salt=k + 1) - 0.5)
            a = aim + math.pi + spin * math.radians(150)     # well outside the cone
            d = (_MIN_EXIT + 2 + self._hash01(int(py), int(px) + k, salt=k)
                 * (_MAX_EXIT - _MIN_EXIT - 4)) * TILE
            nx, ny = px + math.cos(a) * d, py + math.sin(a) * d
            if not self.is_solid_at(nx, ny):
                self._exit_light.x, self._exit_light.y = nx, ny
                return
        a = aim + math.pi
        d = ((_MIN_EXIT + _MAX_EXIT) / 2) * TILE
        self._exit_light.x, self._exit_light.y = px + math.cos(a) * d, py + math.sin(a) * d

    def _drop_exit(self):
        if self._exit_light is not None:
            try:
                self.decorations.remove(self._exit_light)
            except ValueError:
                pass
            self._exit_light = None
        self._hunting = False

    def _tick(self, game, scene, dt):
        p = game.player
        if p is None:
            return
        haven = self._cfg["haven_r"] * TILE
        d_haven = math.hypot(p.x - self._fx, p.y - self._fy)
        if d_haven < haven:
            self._drop_exit()             # in the island's light: no way out yet
            return
        if self._exit_light is None:      # just left the glow -> the hunt begins
            self._exit_light = Decoration(p.x, p.y, _EXIT_KIND)
            self.add_decoration(self._exit_light)
            self._hunting = True
            self._relocate_exit(game)
        lx, ly = self._exit_light.x, self._exit_light.y
        d = math.hypot(lx - p.x, ly - p.y)
        if d <= _REACH * TILE:            # reached it -> out of the lost space
            # NO narrator box here (maintainer ruling): the lost spaces carry
            # no narration at all. Reaching the light and the world changing
            # around you IS the beat; a caption would explain it away.
            game.cross_fold(self._exit_to)
            return
        if d > _MAX_EXIT * TILE or d < _MIN_EXIT * 0.5 * TILE:
            self._relocate_exit(game)     # drifted -> it moves, unseen

    # ---- infinite-safe overrides --------------------------------------------
    def nav_path(self, *a, **k):
        return None            # no full-grid BFS on an unbounded field


class _GenRow:
    __slots__ = ("_fn", "_ty", "_n")

    def __init__(self, fn, ty, n):
        self._fn = fn
        self._ty = ty
        self._n = n

    def __getitem__(self, tx):
        # BOUNDED on purpose: the engine only indexes inside its own 0<=tx<w
        # guards, so this never raises in play -- but raising outside [0,n)
        # makes any accidental full iteration terminate instead of hanging.
        if not (0 <= tx < self._n):
            raise IndexError(tx)
        return self._fn(tx, self._ty)

    def __setitem__(self, tx, v):
        pass                    # generated ground is read-only (markers unused)

    def __len__(self):
        return self._n


class _GenGrid:
    """A virtual 2D char grid: grid[ty][tx] -> generator(tx, ty). BOUNDED to
    [0,n) so the engine's in-bounds reads hit the generator while any stray
    full-grid iteration terminates (see _GenRow)."""
    __slots__ = ("_fn", "_n")

    def __init__(self, fn, n):
        self._fn = fn
        self._n = n

    def __getitem__(self, ty):
        if not (0 <= ty < self._n):
            raise IndexError(ty)
        return _GenRow(self._fn, ty, self._n)

    def __len__(self):
        return self._n


def build_lost_corn():
    return LostSpace("lost_corn", biome="corn", exit_to="lost_forest")


def build_lost_forest():
    return LostSpace("lost_forest", biome="forest", exit_to="lost_road")


def build_lost_road():
    return LostSpace("lost_road", biome="road", exit_to="lost_corn")


def build_lost_space():
    # back-compat alias: the original single key -> the corn field.
    return LostSpace("lost_space", biome="corn", exit_to="lodge_yard")
