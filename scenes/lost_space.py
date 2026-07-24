"""THE LOST SPACES -- procedurally generated, NON-REPEATING backrooms fields
(TODO #25 / the in-between). A prototype of the maintainer's model: you fall
off a dark edge of the safe world into a dark field that GENERATES new ground
as you walk (never a wrap, never a repeat), and the only way out is a light you
have to HUNT (the exit lantern stays 6-20 tiles off, relocating out of your
sight if you drift, so it is always escapable and always a search).

Architecture (from the engine map): the tilt renderer is already a rolling
window keyed on the camera, and collision/sight bottom out in char_object_at /
char_floor_at which index self.objects / self.floor. So a Scene whose floor /
objects are GENERATOR-backed proxies, with a large finite w/h and the player
spawned at the centre, gets collision + sight + tilt render for free -- the map
edge is hundreds of tiles away and never enters the window. Non-repeating comes
from hashing the world tile coord: forward is always new ground, back is
consistent. Nav is replaced (return None -> straight-line chase). No re-origin
in the prototype (a 400-tile bound is a long walk and floats are fine there);
the production build adds silent re-origin for a truly endless walk.
"""
import math

from scenes.base import Scene, TILE
from entities.decoration import Decoration

# odd landmarks scattered in the field -- uncanny, not helpful, so the forward
# walk always has SOMETHING to find (variety, the maintainer's #1 ask). All are
# depth-anchored tilt volumes / valid standees (verified against the tilt sets).
_LANDMARK_KINDS = ("standing_stone", "creepy_tree", "pedestal", "birdcage",
                   "corn_altar", "scarecrow", "washstand", "doll")

# the exit light: a WARM, non-electric lantern (always lit, no genset to gate
# it) -- reads as "the way out / safety" against the cold dark field.
_EXIT_KIND = "lantern"

_MIN_EXIT = 6      # tiles: the exit never sits closer than this (always a hunt)
_MAX_EXIT = 20     # tiles: nor farther than this (always escapable)
_REACH = 2.2       # tiles: this close to the lantern = you climbed out


class LostSpace(Scene):
    """A generator-backed, non-repeating dark field. See module docstring."""

    def __init__(self, key="lost_space", biome="corn", seed=1,
                 size=400, exit_to="lodge_yard", music="village"):
        # build a 1x1 placeholder, then swap in the generator proxies
        super().__init__(key, ["."], object_rows=["."], music=music)
        self._seed = seed & 0x7fffffff
        self._biome = biome
        self._exit_to = exit_to
        self.w = self.h = size
        self.procedural = True                    # smoke skips flood/full scans
        self._cx = self._cy = size // 2           # spawn tile (map centre)
        self.floor = _GenGrid(self._floor_at, size)
        self.objects = _GenGrid(self._obj_at, size)
        self.spawns = {"default": (self._cx * TILE + TILE // 2,
                                   self._cy * TILE + TILE // 2)}
        self.skybox_kind = "void"                 # near-black surround, not sky
        # the moving exit light + the odd landmarks
        sx, sy = self.spawns["default"]
        self._exit_light = Decoration(sx + 12 * TILE, sy, _EXIT_KIND)
        self.add_decoration(self._exit_light)
        self._scatter_landmarks(count=44, radius=52)
        self.on_update_fn = self._tick

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

    def _floor_at(self, tx, ty):
        # corn cover everywhere (the player reads as IN the corn), with rare
        # grass clearings where the field thins.
        if self._vnoise(tx * 0.09 + 40, ty * 0.09 - 17, salt=3) > 0.72:
            return "g"
        return ":"

    def _obj_at(self, tx, ty):
        # a small clear apron at the spawn so you don't start buried
        if abs(tx - self._cx) <= 1 and abs(ty - self._cy) <= 1:
            return "."
        # organic clumps of dense corn with winding lanes -- no straight rows
        # to orient by (that is the disorientation). Non-repeating (hashed).
        n = self._vnoise(tx * 0.16, ty * 0.16)
        n += 0.4 * self._vnoise(tx * 0.52 + 11, ty * 0.52 + 7, salt=2)
        v = n * 0.62 + self._hash01(tx, ty, salt=5) * 0.16
        if v > 0.52:
            return "C"        # solid stalk (weave around it)
        if v > 0.34:
            return "A"        # passable stalk (push through it)
        return "."            # open lane

    # ---- odd landmarks -------------------------------------------------------
    def _scatter_landmarks(self, count, radius):
        for i in range(count):
            a = self._hash01(i, 777, salt=9) * math.tau
            r = (_MAX_EXIT + 4 + self._hash01(i, 313, salt=1) * (radius - _MAX_EXIT)) * TILE
            lx = self._cx * TILE + TILE // 2 + math.cos(a) * r
            ly = self._cy * TILE + TILE // 2 + math.sin(a) * r
            kind = _LANDMARK_KINDS[int(self._hash01(i, 42, salt=4) * len(_LANDMARK_KINDS)) % len(_LANDMARK_KINDS)]
            self.add_decoration(Decoration(lx, ly, kind,
                                           seed=(self._seed + i * 17) & 0xffff))

    # ---- the hunted exit light ----------------------------------------------
    def _relocate_exit(self, game):
        """Move the lantern to a fresh spot in the 6-20 tile band, OUTSIDE the
        player's current sight cone, so it never pops into view -- you find it
        by turning, never by watching it teleport."""
        px, py = game.player.x, game.player.y
        aim = getattr(getattr(game, "look", None), "aim", 0.0) or 0.0
        for _ in range(24):
            # a heading well outside the forward cone (aim +/- ~110-250 deg)
            spin = (self._hash01(int(px), int(py) + _, salt=_ + 1) - 0.5)
            a = aim + math.pi + spin * math.radians(150)
            d = (_MIN_EXIT + 2 + self._hash01(int(py), int(px) + _, salt=_)
                 * (_MAX_EXIT - _MIN_EXIT - 4)) * TILE
            nx, ny = px + math.cos(a) * d, py + math.sin(a) * d
            if not self.is_solid_at(nx, ny):
                self._exit_light.x, self._exit_light.y = nx, ny
                return
        # fallback: straight behind, band centre
        a = aim + math.pi
        d = ((_MIN_EXIT + _MAX_EXIT) / 2) * TILE
        self._exit_light.x, self._exit_light.y = px + math.cos(a) * d, py + math.sin(a) * d

    def _tick(self, game, scene, dt):
        if game.player is None:
            return
        px, py = game.player.x, game.player.y
        lx, ly = self._exit_light.x, self._exit_light.y
        d = math.hypot(lx - px, ly - py)
        if d <= _REACH * TILE:                      # reached the light -> out
            game.show_notice("You break out of the corn into the light.",
                             duration=2.2)
            game.cross_fold(self._exit_to)
            return
        if d > _MAX_EXIT * TILE or d < _MIN_EXIT * 0.5 * TILE:
            self._relocate_exit(game)               # drifted -> it moves, unseen

    # ---- infinite-safe overrides --------------------------------------------
    def nav_path(self, *a, **k):
        return None            # no full-grid BFS on an unbounded field; chasers
        #                        fall back to a straight-line slide (fine here)


class _GenRow:
    __slots__ = ("_fn", "_ty", "_n")

    def __init__(self, fn, ty, n):
        self._fn = fn
        self._ty = ty
        self._n = n

    def __getitem__(self, tx):
        # BOUNDED on purpose: the engine only indexes inside its own 0<=tx<w
        # guards, so this never raises in play -- but raising outside [0,n)
        # makes any accidental full iteration terminate instead of running
        # forever (a stray `for ch in row` / `enumerate`).
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
