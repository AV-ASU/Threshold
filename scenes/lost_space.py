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

# the occupied camp: far enough out to be stumbled into while hunting the
# exit, never the light you land in
_CAMP_RING_MIN = 26.0      # tiles from the focal island
_CAMP_RING_MAX = 36.0
_CAMP_STAND = 2.4          # tiles: how far off the flame they stand
_CAMP_WAKE = 24.0          # tiles: crew exists inside this
_CAMP_SLEEP = 34.0         # tiles: released beyond this (hysteresis)

# the lamp-carriers: cultists walking the dark with a light in hand. The
# whole point is that a MOVING warm glow is indistinguishable from the
# stationary warm glow you are hunting, until it moves.
_ROAM_CREW = 2             # carriers abroad in the field at once
_ROAM_MIN = 18.0           # tiles: never spawned closer than this
_ROAM_MAX = 30.0           # tiles: nor farther (they must be SEEN)
_ROAM_RELEASE = 52.0       # tiles: released once you are long gone

# the dark rearranging itself: how often, how much, and the radius inside
# which a landmark is "here" and therefore never moves
_SHUFFLE_EVERY = 2.5       # seconds between passes
_SHUFFLE_MAX = 3           # landmarks relocated per pass (never a whole field)
_SHUFFLE_NEAR = 16.0       # tiles: nothing this close is ever touched

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
        # NO PLACE NAME. Every other scene labels itself in the HUD corner;
        # the default here would have titlecased the key into "Lost Forest",
        # which tells the player exactly what happened to them. A lost space
        # is somewhere with no name you know, and the wordlessness ruling
        # (DIALOGUE.md) covers the corner label the same as a caption.
        self.display_name = ""
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
        self._scatter_decos = []                  # the field's movable landmarks
        self._scatter_ground_detail()
        self._scatter_things(count=84, radius=72)
        self._exit_light = None                   # spawns only once you leave
        self._shuf_t = _SHUFFLE_EVERY
        self._shuf_i = 0                          # rotating reshuffle cursor
        self._hunting = False
        # THE OCCUPIED CAMP (the inversion). Its fire is raised at build time
        # so the glow is out there in the black from the moment you arrive;
        # the CREW is spawned on approach and released when you leave, so a
        # 400-tile field never simulates a crowd. `cult_target = 0` keeps the
        # town's evidence-gated top-up (`_ensure_cultists`) out of the field:
        # this population is the scene's own.
        self.cult_target = 0
        self._camp_pos, self._camp_size = self._raise_occupied_camp()
        self._camp_crew = []
        self._roamers = []                        # (cultist, carried lantern)
        self.on_update_fn = self._tick

    # ============ THE DARK REARRANGES (observer-dependent geometry) ==========
    def _tick_reshuffle(self, game, dt):
        """The field quietly rearranges the things you are not looking at.

        The rule the whole space runs on, and the one it never breaks:
        **what the light touches is TRUE; the dark is not.** So a landmark
        moves only when ALL of these hold:

          * it is OUTSIDE your sight cone (`visible_factor` == 0), so nothing
            is ever seen to move. You do not catch it; you only ever find that
            it is not where you left it.
          * it is UNLIT (`lit_at` false). Anything standing in a light pool is
            fixed, permanently. That is what makes light worth walking toward
            and what keeps the exit lantern, the island, and the camps honest.
          * it is far enough off to be out of mind, and it lands far enough
            off to stay that way.

        THREATS ARE NEVER TOUCHED (the fence, `TODO.md` #26): only scenery
        lies. A cultist blinking across the field would be a different, worse
        game -- and it would break the one-impossible-thing rule, because then
        the space would be doing something the FOLD is not."""
        self._shuf_t -= dt
        if self._shuf_t > 0.0:
            return
        self._shuf_t = _SHUFFLE_EVERY
        p = game.player
        look = getattr(game, "look", None)
        heading = getattr(look, "aim", 0.0) if look else 0.0
        from rendering.sight import visible_factor
        moved = 0
        # Sweep from a ROTATING cursor rather than the head of the list. A
        # fixed start meant the same first-eligible few landmarks teleported
        # over and over while the rest of the field never moved at all -- the
        # opposite of a space that slowly rearranges.
        n = len(self._scatter_decos)
        for off in range(n):
            if moved >= _SHUFFLE_MAX:
                break
            d = self._scatter_decos[(self._shuf_i + off) % n]
            dist = math.hypot(d.x - p.x, d.y - p.y)
            if dist < _SHUFFLE_NEAR * TILE:
                continue                       # too close: it is basically here
            if visible_factor(p.x, p.y, heading, d.x, d.y,
                              self.blocks_sight) > 0.0:
                continue                       # you are looking at it
            if self.lit_at(d.x, d.y):
                continue                       # the light makes it true
            for _try in range(6):
                a = self._hash01(int(d.x) + _try, int(d.y) + moved,
                                 salt=51 + _try) * math.tau
                rr = (_SHUFFLE_NEAR + 4.0 + self._hash01(
                    int(d.y), int(d.x) + _try, salt=61) * 22.0) * TILE
                nx, ny = p.x + math.cos(a) * rr, p.y + math.sin(a) * rr
                if self.is_solid_at(nx, ny):
                    continue
                if visible_factor(p.x, p.y, heading, nx, ny,
                                  self.blocks_sight) > 0.0:
                    continue                   # never land it in your view
                if self.lit_at(nx, ny):
                    continue                   # nor inside a light that would
                    #                            then be lying about it
                d.x, d.y = nx, ny
                moved += 1
                self._shuf_i = (self._shuf_i + off + 1) % n
                break

    # ================= THE OCCUPIED CAMP (the inversion) =====================
    def _raise_occupied_camp(self):
        """A SECOND fire out in the black, and this one is manned.

        The field teaches you that light is orienting: you land in a lit
        haven, and the way out is a light you hunt. This camp spends that
        lesson. From a distance its glow is just another warm light in a dark
        field, indistinguishable from the exit; you close on it because
        closing on light is what the space has trained you to do, and the
        figures standing at it only resolve once you are near enough for them
        to resolve you.

        Placed on a hashed bearing at `_CAMP_RING` tiles: outside the haven
        (so it is never the thing you land in) and inside the wandering you do
        while hunting the exit (so it is genuinely stumbled into).

        Camps come in KINDS, chosen per field by hash, because one camp
        repeated verbatim stops being a discovery the second time you meet it.
        Each kind reads differently at a glance, so what you are walking up on
        is legible before it is dangerous:

          * **rest**  -- bedrolls down, seats pulled in, a bigger crew. They
                         are living here. The most camp-like, the most bodies.
          * **watch** -- no bedding, one seat, a small crew standing. A post,
                         not a home; they are looking outward.
          * **work**  -- a barrow and a heap beside the flame: a dig detail
                         stopped for the night, tools where they dropped them.

        Returns (world centre, crew size)."""
        a = self._hash01(3, 91, salt=21) * math.tau
        r = (_CAMP_RING_MIN + self._hash01(7, 41, salt=22)
             * (_CAMP_RING_MAX - _CAMP_RING_MIN)) * TILE
        cx = self._fx + math.cos(a) * r
        cy = self._fy + math.sin(a) * r
        kind = ("rest", "watch", "work")[
            int(self._hash01(11, 23, salt=28) * 3) % 3]
        # the fire is the lure, so it burns from the start (a camp_fire is in
        # both light tables: it casts a real pool AND gives real cover)
        self.add_decoration(Decoration(cx, cy, "camp_fire", seed=53))
        if kind == "rest":
            dressing = ((-40, -14, "bedroll"), (34, -20, "bedroll"),
                        (6, 40, "bedroll"), (44, 16, "log_seat"),
                        (-46, 20, "log_seat"))
            crew = 4
        elif kind == "watch":
            dressing = ((46, 10, "log_seat"), (-30, 34, "grass_tuft"))
            crew = 2
        else:                                   # work
            dressing = ((-48, -8, "wheelbarrow"), (40, 26, "bedroll"),
                        (30, -34, "log_seat"))
            crew = 3
        for i, (dx, dy, k) in enumerate(dressing):
            self.add_decoration(Decoration(cx + dx, cy + dy, k, seed=i + 30))
        self._camp_kind = kind
        return (cx, cy), crew

    def _tick_camp(self, game):
        """Spawn the camp's crew when the player nears, release them when the
        player is long gone. They are ordinary cult regulars: the standard
        gaze, suspicion, Talk and two-touch grab all apply untouched. The only
        bespoke part is WHERE they come from and when they exist."""
        p = game.player
        cx, cy = self._camp_pos
        d = math.hypot(p.x - cx, p.y - cy)
        live = [n for n in self._camp_crew
                if n in self.npcs and getattr(n, "alive", True)]
        self._camp_crew = live
        if d < _CAMP_WAKE * TILE and len(live) < self._camp_size:
            for i in range(self._camp_size - len(live)):
                a = self._hash01(i, 17, salt=23) * math.tau
                at = (cx + math.cos(a) * _CAMP_STAND * TILE,
                      cy + math.sin(a) * _CAMP_STAND * TILE)
                n = game._spawn_cultist("cult_regular", "cultist",
                                        speed=0.95, gaze_range=180, at=at)
                if n is not None:
                    self._camp_crew.append(n)
        elif d > _CAMP_SLEEP * TILE and live:
            # walked away for good: let the field go quiet again rather than
            # simulate a crew nobody is near
            self.npcs = [n for n in self.npcs if n not in live]
            self._camp_crew = []

    # ================= THE LAMP-CARRIERS (the ambiguous glow) ================
    def _tick_roamers(self, game):
        """Cultists walking the dark with a lantern in hand.

        The field's exit is a warm lantern held 6-20 tiles off. So is this.
        The only thing that tells them apart is that one of them MOVES, and by
        the time you are sure which you are looking at, the question has
        usually answered itself. It also puts the two threats in their proper
        jobs: the Watchers FIND you, the cult CATCHES you.

        The carried light is a real emitter parented to the body -- the
        lightmap reads live deco positions every frame and `light_sources`
        caches the deco LIST rather than positions, so a moving source lights
        and gates correctly with no special case."""
        p = game.player
        # they walk the dark you walk: abroad only once you have left the
        # island's glow and the hunt is on
        hunting = math.hypot(p.x - self._fx, p.y - self._fy) >= \
            self._cfg["haven_r"] * TILE
        live = []
        for npc, lamp in self._roamers:
            gone = (npc not in self.npcs or not getattr(npc, "alive", True)
                    or getattr(npc, "_is_corpse", False))
            far = math.hypot(npc.x - p.x, npc.y - p.y) > _ROAM_RELEASE * TILE
            if gone or far or not hunting:
                if npc in self.npcs and (far or not hunting) and not gone:
                    self.npcs.remove(npc)
                try:
                    self.decorations.remove(lamp)
                except ValueError:
                    pass
                continue
            lamp.x, lamp.y = npc.x, npc.y        # the light rides the body
            live.append((npc, lamp))
        self._roamers = live
        if not hunting:
            return
        for i in range(_ROAM_CREW - len(live)):
            a = self._hash01(int(p.x) + i, int(p.y), salt=31 + i) * math.tau
            d = (_ROAM_MIN + self._hash01(int(p.y) + i, int(p.x), salt=41)
                 * (_ROAM_MAX - _ROAM_MIN)) * TILE
            at = (p.x + math.cos(a) * d, p.y + math.sin(a) * d)
            if self.is_solid_at(*at):
                continue
            npc = game._spawn_cultist("cult_regular", "cultist",
                                      speed=0.95, gaze_range=180, at=at)
            if npc is None:
                continue
            lamp = Decoration(npc.x, npc.y, "lantern", seed=(i * 7) & 0xffff)
            self.add_decoration(lamp)
            self._roamers.append((npc, lamp))

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
        # The near-bank fire: the zone's HAVEN light, and it has to be a
        # haven-class one. Built as a modest `camp_fire` the pond was the only
        # focal island without a real light source (corn has `haven_fire`, the
        # road a `neon_pylon`), and in the player's actual dark view it read
        # as a black pond in a black wood rather than the pretty thing it is
        # meant to be. Set to one side of the bank so the player, landing
        # further back, sees it burning between them and the water.
        self.add_decoration(Decoration(cx - 40, cy + pr - 10, "haven_fire",
                                       seed=17, scale=1.25))
        # lanterns on stub posts around the far/side banks
        for a in (0.6, 2.1, 4.2):
            lx = cx + math.cos(a) * (pr + 10)
            ly = cy + math.sin(a) * (pr + 10)
            self.add_decoration(Decoration(lx, ly, "lantern", seed=int(a * 40)))
        # REEDS ON THE WATERLINE. Scattered singles read as nothing at this
        # scale; reeds grow in stands, so they are placed in clumps that hug
        # the meandering bank (the radius is sampled per bearing, so they sit
        # ON the water's edge wherever it happens to run) with gaps between
        # the stands, never an even fringe.
        n_st = 7
        for s in range(n_st):
            a0 = (s / n_st) * math.tau + self._hash01(s, 5, salt=24) * 0.5
            if self._hash01(s, 9, salt=25) < 0.28:
                continue                        # a bare stretch of bank
            for k in range(2 + int(self._hash01(s, k_ := 3, salt=26) * 4)):
                a = a0 + (k - 1.5) * 0.10
                rr = self._pond_r(self._cx + math.cos(a) * 10,
                                  self._cy + math.sin(a) * 10) * TILE
                rr += (0.5 + self._hash01(s * 9 + k, 2, salt=27) * 0.7) * TILE
                self.add_decoration(Decoration(
                    cx + math.cos(a) * rr, cy + math.sin(a) * rr,
                    "tall_grass", seed=(s * 13 + k) & 0xffff))
        # boulders half in the water, a fallen log, framing trees off the bank
        for i, (dx, dy, kind) in enumerate((
                (pr + 4, -34, "boulder"), (-pr - 10, 30, "boulder"),
                (26, -pr - 6, "boulder"),
                (pr + 22, 12, "log_seat"), (-38, pr + 20, "grass_tuft"),
                (pr + 40, -46, "creepy_tree"), (-pr - 46, 30, "creepy_tree"))):
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

    def _pond_r(self, tx, ty):
        """The pond's radius along the bearing of (tx, ty): the base radius
        pushed in and out by low-frequency noise so the waterline meanders
        like a real pond instead of ringing a perfect circle."""
        a = math.atan2(ty - self._cy, tx - self._cx)
        n = self._vnoise(math.cos(a) * 2.2 + 5, math.sin(a) * 2.2 - 3, salt=19)
        return self._cfg["pond_r"] * (0.82 + 0.36 * n)

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
            # An organic pond, not a disc: the waterline is the radius pushed
            # around by low-frequency noise, and the WET bank that follows it
            # is narrow and ragged (in places the moss runs right to the
            # water). The bank is dark wet mud, never the dry tan dirt it
            # started as -- as `d` it was luma 75, the BRIGHTEST thing in the
            # scene, so a beach-coloured donut read louder than the pond it
            # surrounded.
            pr = self._pond_r(tx, ty)
            if r <= pr:
                return "~"                # the POND (animated water)
            if r <= pr + 0.35 + self._vnoise(tx * 0.5, ty * 0.5, salt=17) * 0.9:
                return ";"                # wet mud at the waterline (always a
                #                           thin rim, ragged in width)
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
            d = Decoration(lx, ly, k, seed=(self._seed + i * 17) & 0xffff)
            self.add_decoration(d)
            # only the FIELD's scatter is allowed to rearrange itself; the
            # island, the camps and every light are fixed by construction
            self._scatter_decos.append(d)

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
        # the manned fire runs wherever you are: its whole job is to be out
        # there in the dark while you are busy hunting a different light
        self._tick_camp(game)
        self._tick_roamers(game)
        self._tick_reshuffle(game, dt)
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
            # You CLIMB OUT where you fell in. The anchor is written by
            # Game._tick_lost_edge, a few strides back from the edge that
            # swallowed you, so the world you return to is the one you lost.
            ret = getattr(game, "_lost_return", None)
            if ret is not None:
                game._lost_return = None
                game.cross_fold(ret[0], dest_pos=(ret[1], ret[2]))
                return
            # No anchor: the field was loaded directly (a preview, a test).
            # Fall through to the static neighbour so the fields still chain.
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
