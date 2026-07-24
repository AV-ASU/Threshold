"""THE LOST SPACES -- procedurally generated, NON-REPEATING backrooms fields
(TODO #26 / the in-between). You fall off a dark edge of the safe world into a
dark liminal field, land at a lit FOCAL POINT (a hand-authored island), and the
only way out is a light you HUNT once you leave that island's glow.

Design (the maintainer's model): a HAND-MADE ISLAND in a SEA OF GENERATION. The
field is mostly EMPTY ground with sparse corn clumps and scattered uncanny
things to find (the backrooms feeling is emptiness + the occasional wrong thing,
never a wall of texture). At the centre sits the biome's focal point -- for the
CORN field, an ABANDONED CULT CAMP with a still-burning ground fire that lights
the clearing (a haven: lit, orienting, but NOT a true refuge). While you stand
in the firelight there is no way out; leave the glow and the EXIT LIGHT appears
in the dark, held 6-20 tiles off, relocating out of your sight so it stays
findable. The lit safe-feeling place is a dead end; you escape by walking into
the dark.

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

# the corn field's scatter library -- sparse, uncanny, on-world (a dead corn
# town's leavings). Weighted by repetition (lone trees are the commonest).
_SCATTER = ("creepy_tree", "creepy_tree", "creepy_tree", "husk",
            "wheelbarrow", "rust_sedan", "rust_wagon", "rust_van",
            "standing_stone", "scarecrow", "well", "corn_altar", "log_seat")

_EXIT_KIND = "lantern"     # the hunted way-out light (warm, non-electric)

_HAVEN_R = 4               # tiles: the abandoned camp's clear dirt radius
_HAVEN_LIGHT_R = 7.0       # tiles: leave the firelight and the exit hunt begins
_MIN_EXIT = 6              # tiles: the exit never sits closer (always a hunt)
_MAX_EXIT = 20             # tiles: nor farther (always escapable)
_REACH = 2.2               # tiles: this close to the exit = you climbed out


class LostSpace(Scene):
    """A generator-backed, non-repeating dark field with a lit focal island.
    See the module docstring."""

    def __init__(self, key="lost_space", biome="corn", seed=1,
                 size=400, exit_to="lodge_yard", music="village"):
        super().__init__(key, ["."], object_rows=["."], music=music)
        self._seed = seed & 0x7fffffff
        self._biome = biome
        self._exit_to = exit_to
        self.w = self.h = size
        self.procedural = True                    # smoke skips flood/full scans
        self._cx = self._cy = size // 2           # spawn tile (map centre)
        self.floor = _GenGrid(self._floor_at, size)
        self.objects = _GenGrid(self._obj_at, size)
        sx = self._cx * TILE + TILE // 2
        sy = self._cy * TILE + TILE // 2
        self.spawns = {"default": (sx, sy)}
        self.skybox_kind = "void"                 # near-black surround, not sky
        self._sx, self._sy = sx, sy
        self._raise_abandoned_camp(sx, sy)
        self._scatter_things(count=84, radius=70)
        self._exit_light = None                   # spawns only once you leave
        self._hunting = False
        self.on_update_fn = self._tick

    # ---- the abandoned cult camp: the lit FOCAL ISLAND (reuses brimley's) ----
    def _raise_abandoned_camp(self, cx, cy):
        self.add_decoration(Decoration(cx, cy, "camp_fire", seed=71))
        for (dx, dy, kind, sd) in (
                (-42, -4, "bedroll", 1), (36, -12, "bedroll", 2),
                (-8, 40, "bedroll", 3), (44, 18, "log_seat", 4),
                (-44, 22, "log_seat", 5), (10, -40, "log_seat", 6)):
            self.add_decoration(Decoration(cx + dx, cy + dy, kind, seed=sd))
        self.add_decoration(Decoration(cx + 48, cy - 34, "lantern"))

    # ---- the generator: deterministic per world tile, non-repeating ----------
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

    def _in_haven(self, tx, ty):
        return abs(tx - self._cx) <= _HAVEN_R and abs(ty - self._cy) <= _HAVEN_R

    def _corn_here(self, tx, ty):
        # sparse corn CLUMPS: a low-freq gate so corn appears in scattered
        # patches (~6-9 tile blobs) with big EMPTY between -- not a wall of it.
        return self._vnoise(tx * 0.12 + 7, ty * 0.12 + 3, salt=8) > 0.74

    def _floor_at(self, tx, ty):
        if self._in_haven(tx, ty):
            return "d"                    # the camp's worn packed dirt
        if self._corn_here(tx, ty):
            return ":"                    # corn cover (inside a clump)
        # the field is mostly EMPTY ground -- big regions of dead grass / dirt /
        # mud so the nothing still reads varied, not one flat colour.
        g = self._vnoise(tx * 0.05 + 40, ty * 0.05 - 17, salt=3)
        if g > 0.60:
            return "g"                    # dead grass
        if g < 0.36:
            return ";"                    # mud
        return "d"                        # bare dirt (the "patches of nothing")

    def _obj_at(self, tx, ty):
        if self._in_haven(tx, ty):
            return "."                    # clear (the camp decos sit on top)
        if self._corn_here(tx, ty):
            v = self._vnoise(tx * 0.36, ty * 0.36, salt=2) * 0.72 \
                + self._hash01(tx, ty, salt=5) * 0.28
            if v > 0.56:
                return "C"                # solid stalk (weave around)
            if v > 0.36:
                return "A"                # passable stalk (push through)
            return "."
        return "."                        # EMPTY -- the vast majority

    # ---- scattered things to FIND (the exploration; sparse) ------------------
    def _scatter_things(self, count, radius):
        for i in range(count):
            a = self._hash01(i, 777, salt=9) * math.tau
            rr = (_HAVEN_LIGHT_R + 3
                  + self._hash01(i, 313, salt=1) * (radius - _HAVEN_LIGHT_R - 3)) * TILE
            lx = self._sx + math.cos(a) * rr
            ly = self._sy + math.sin(a) * rr
            k = _SCATTER[int(self._hash01(i, 42, salt=4) * len(_SCATTER)) % len(_SCATTER)]
            self.add_decoration(Decoration(lx, ly, k,
                                           seed=(self._seed + i * 17) & 0xffff))

    # ---- the hunted exit light (spawns only OUTSIDE the haven's glow) --------
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
        d_haven = math.hypot(p.x - self._sx, p.y - self._sy)
        if d_haven < _HAVEN_LIGHT_R * TILE:
            self._drop_exit()             # in the firelight: no way out yet
            return
        if self._exit_light is None:      # just left the glow -> the hunt begins
            self._exit_light = Decoration(p.x, p.y, _EXIT_KIND)
            self.add_decoration(self._exit_light)
            self._hunting = True
            self._relocate_exit(game)
        lx, ly = self._exit_light.x, self._exit_light.y
        d = math.hypot(lx - p.x, ly - p.y)
        if d <= _REACH * TILE:            # reached it -> out of the lost space
            game.show_notice("You break free of the field into the light.",
                             duration=2.2)
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


def build_lost_space():
    return LostSpace()
