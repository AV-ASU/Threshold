"""Scene primitives: the Scene class + scene-builder helpers.

The tile definitions and the entire terrain draw layer (flat + tilted)
were split into ``scenes/terrain.py`` (2026-07); this module imports and
RE-EXPORTS every name terrain defines (public and private), so existing
``from scenes.base import <x>`` and ``import scenes.base as _sb`` access
keep resolving unchanged. Scene builders still consume these names."""
import math
import random
import pygame
from constants import SCREEN_W, SCREEN_H, TILE
from scenes import terrain as _terrain
# Re-export EVERY terrain name (including _private ones external modules
# import) into this module's namespace so the facade is transparent.
globals().update({_k: _v for _k, _v in vars(_terrain).items()
                  if not _k.startswith("__")})

_SIGHT_EYE_H = _terrain._SIGHT_EYE_H

_DIRECTION_VECTORS = {
    "north": (0, -1),
    "south": (0, 1),
    "east":  (1, 0),
    "west":  (-1, 0),
}


def scatter_forest_band(floor_ll, objects_l, w, h, *,
                         depth=7, seed=53,
                         tree_density=0.48, tree_floor=0.04,
                         passable_ratio=0.6,
                         blotch_dim=0.22, blotch_corn=0.09,
                         bush_density=0.10,
                         solid_char="T", passable_char="p",
                         protected=None, place_bush=None):
    """Stamp a permeable scattered band around the perimeter of an
    outdoor scene. The wrap mechanic moves the player; this is the
    visual camouflage that hides the transition. Both floor_ll and
    objects_l are mutated in place.

    - Walls (default 'T' solid / 'p' passable trees; pass solid_char +
      passable_char to use corn 'C'/'A' or whatever else) seeded at
      decreasing density from the outer edge inward across `depth`
      tiles. `passable_ratio` of placements are passable so navigation
      is forgiving.
    - Ground blotch: ';' dim grass + ':' corn cover (which hides the
      player) mixed into the open grass in the same band.
    - De-clump pass: any 2x2 block of solid chars gets one corner
      converted to passable so the player is never stopped by a wall.
    - Bushes: `place_bush(x_px, y_px)` is called for each chosen
      decoration position; the floor under each bush is forced to ':'
      so stepping into it hides. Pass a callback that adds the bush
      Decoration to the scene.

    `protected(tx, ty) -> bool` exempts tiles from EVERY pass (walls,
    blotch, bushes). Used for road corridors and spawn approaches.
    """
    rng = random.Random(seed)
    prot = protected or (lambda tx, ty: False)
    # Pass 1 -- walls in objects.
    def _wall_char():
        return passable_char if rng.random() < passable_ratio else solid_char
    for ty in range(h):
        for tx in range(w):
            edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
            if edge_dist >= depth:
                continue
            if objects_l[ty][tx] != ".":
                continue
            if prot(tx, ty):
                continue
            t = edge_dist / depth
            density = tree_density * (1 - t) + tree_floor
            if rng.random() < density:
                objects_l[ty][tx] = _wall_char()
    # Pass 2 -- de-clump: break any 2x2 block of solid walls.
    for ty in range(h - 1):
        for tx in range(w - 1):
            quad = [objects_l[ty][tx], objects_l[ty][tx + 1],
                    objects_l[ty + 1][tx], objects_l[ty + 1][tx + 1]]
            if quad.count(solid_char) == 4:
                cands = [(tx, ty), (tx + 1, ty),
                         (tx, ty + 1), (tx + 1, ty + 1)]
                cx, cy = min(cands,
                             key=lambda p: (p[0] - w / 2) ** 2 +
                                           (p[1] - h / 2) ** 2)
                if not prot(cx, cy):
                    objects_l[cy][cx] = passable_char
    # Pass 3 -- ensure every solid wall has at least one passable
    # orthogonal neighbour; otherwise it's a dead-end clump and gets
    # swapped to passable.
    open_set = (".", passable_char)
    for ty in range(1, h - 1):
        for tx in range(1, w - 1):
            if objects_l[ty][tx] != solid_char:
                continue
            if prot(tx, ty):
                continue
            neighbors = [objects_l[ty - 1][tx], objects_l[ty + 1][tx],
                         objects_l[ty][tx - 1], objects_l[ty][tx + 1]]
            if not any(n in open_set for n in neighbors):
                objects_l[ty][tx] = passable_char
    # Pass 4 -- ground blotch in the same band.
    blotch_rng = random.Random(seed + 1)
    for ty in range(h):
        for tx in range(w):
            edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
            if edge_dist >= depth:
                continue
            if floor_ll[ty][tx] != "g":
                continue
            if prot(tx, ty):
                continue
            t = edge_dist / depth
            falloff = (1 - t)
            roll = blotch_rng.random()
            if roll < blotch_dim * falloff:
                floor_ll[ty][tx] = ";"
            elif roll < (blotch_dim + blotch_corn) * falloff:
                floor_ll[ty][tx] = ":"
    # Pass 5 -- bushes. Scatter them on open ('.') tiles in the band,
    # set the floor under each to ':' (corn cover, hides the player),
    # and call back to add the Decoration.
    if place_bush is not None:
        bush_rng = random.Random(seed + 2)
        for ty in range(h):
            for tx in range(w):
                edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
                if edge_dist >= depth:
                    continue
                if objects_l[ty][tx] != ".":
                    continue
                if prot(tx, ty):
                    continue
                t = edge_dist / depth
                # Lighter falloff than trees -- bushes spread further
                # in so the band has hideable spots even on its inner
                # rim.
                density = bush_density * (1 - 0.5 * t)
                if bush_rng.random() < density:
                    floor_ll[ty][tx] = ":"
                    px = tx * TILE + 16 + bush_rng.randint(-6, 6)
                    py = ty * TILE + 16 + bush_rng.randint(-6, 6)
                    place_bush(px, py)
    return floor_ll, objects_l


def dead_cars(objects_l, cars):
    """The dead lots: ranks of the abandoned rusted cars. Everyone DROVE
    into Brimley (northern Minnesota; the newcomers came on their own
    wheels and the locals all drive) and nothing with an engine leaves,
    so the cars pool where their drivers finally stopped.

    Stamps the solid footprint and returns the Decorations for the
    caller to add once its Scene exists. Each entry is
    (tx, ty, kind, yaw, seed, axis): the hull is centred on the shared
    edge of two tiles along `axis` ('h' spans (tx,ty)-(tx+1,ty), 'v'
    spans (tx,ty)-(tx,ty+1)), and both tiles are stamped solid invisible
    'X' (the lodge-yard truck convention) so the player bumps on the
    metal -- and, X being sight-blocking, a hull is hard cover. Kinds:
    rust_sedan / rust_wagon / rust_coupe / rust_van (rendering/props.py
    tilt volumes; flat draws in entities/deco_structure.py)."""
    from entities.decoration import Decoration
    h, w = len(objects_l), len(objects_l[0])
    out = []
    for entry in cars:
        tx, ty, kind, yaw, seed, axis = entry[:6]
        # optional 7th element: extra Decoration kwargs (e.g. the barn
        # wagon's {"luggage": True} roof cases)
        extra = entry[6] if len(entry) > 6 else {}
        if axis == "h":
            wx, wy = (tx + 1) * TILE, ty * TILE + 16
            tiles = ((tx, ty), (tx + 1, ty))
        else:
            wx, wy = tx * TILE + 16, (ty + 1) * TILE
            tiles = ((tx, ty), (tx, ty + 1))
        for ox, oy in tiles:
            if 0 <= oy < h and 0 <= ox < w:
                objects_l[oy][ox] = "X"
        out.append(Decoration(wx, wy, kind, seed=seed, yaw=yaw, **extra))
    return out


class Scene:
    TILE = TILE

    def __init__(self, key, floor_rows, object_rows=None, music="home"):
        self.key = key
        self.floor = [list(r) for r in floor_rows]
        self.h = len(self.floor)
        self.w = max(len(r) for r in self.floor) if self.floor else 0
        for i, r in enumerate(self.floor):
            if len(r) < self.w:
                self.floor[i] = r + ["."] * (self.w - len(r))
        if object_rows is None:
            self.objects = [["." for _ in range(self.w)] for _ in range(self.h)]
        else:
            self.objects = [list(r) for r in object_rows]
            for i, r in enumerate(self.objects):
                if len(r) < self.w:
                    self.objects[i] = r + ["."] * (self.w - len(r))
            while len(self.objects) < self.h:
                self.objects.append(["."] * self.w)
        self.music = music
        # If True, the world is toroidal on the matching axis: tile
        # lookups wrap mod self.w / self.h, the camera doesn't clamp,
        # and the player's x / y wrap as well. Used to make a road or
        # a field loop back on itself with no visible transition (the
        # fold). Off by default.
        self.wrap_x = False
        self.wrap_y = False
        # Optional RENDER BAND: a (top_row, bottom_row) tile span that tiles
        # ENDLESSLY toward the north (decreasing y) for rendering ONLY, while
        # everything from top_row south renders once. Used by the arrival road
        # to make a landmark-free forest stretch read as an infinite corridor
        # without wrapping the WHOLE column (which would clone the southern
        # landmarks -- the dead car, the town sign, the dirt crossing -- back
        # into the northern view). Travel north of the band is handled by the
        # separate `_treadmill` loop. None = no band (see render_row). Off by
        # default; only the arrival road sets it.
        self._render_band = None
        # Oblique-camera skybox surround (CAMERA.md Phase 5). None = let the
        # game pick by scene type ("overcast" sallow sky for OUTDOOR_SCENES,
        # near-black "void" for interiors/underground so the horror keeps its
        # dark). A scene builder may pin "overcast"/"void" explicitly to
        # override the heuristic. Unused at pitch 0 (no skybox).
        self.skybox_kind = None
        self.exits = {}
        # Direction-sensitive exit chars: char -> "north"/"south"/etc.
        # If a char is in this dict, find_exit_at only fires the exit
        # when the player's facing matches that compass direction.
        self.exit_directions = {}
        # SEE-THROUGH DOORS (opt-in): a set of door exit chars whose recess
        # shows the ACTUAL room beyond (rendered through the tilt camera) rather
        # than the flat dark doorway. None/empty = every door keeps the legacy
        # dark recess (byte-identical). Game._build_door_views resolves these to
        # built target scenes each load and stashes the result in _door_views.
        self.seethrough_doors = None
        self._door_views = {}
        self.spawns = {"default": (self.w * 16, self.h * 16)}
        self.npcs = []
        self.decorations = []
        # Furniture footprint tile (tx, ty) -> top height, so a tabletop prop
        # placed on that tile can be seated ON the surface (seat_tabletop_props).
        self._surface_tops = {}
        # GROUND HEIGHTFIELD (CAMERA.md Phase 6, blind-spot hills). None = a
        # dead-flat scene: `ground_z` returns 0.0 everywhere, so the floor, the
        # actors, and the sight LOS are all a strict no-op (and pitch 0 is
        # byte-identical). A builder opts in by attaching an (h x w) float grid
        # of per-tile heights (world z, px) via `set_ground` -- authored with
        # rendering.heightfield.build_heightfield, the _flood-style helper.
        self._ground_hf = None
        self.enemies = []
        self.items = []          # list of {x,y,key,qty,on_pickup?}
        self.projectiles = []    # ranged-attack bullets
        self.triggers = []
        # The noise channel (2026-07 sound overhaul): world noises are
        # broadcast through emit_noise onto this small per-frame list
        # (the cult ticks iterate it; events go stale after
        # NOISE_FRESH). _last_step_event stays mirrored for any legacy
        # single-slot reader. _noise_mask is the active dominant source
        # (the bell): (x, y, radius, level, until_ts) -- events quieter
        # than `level` inside `radius` are swallowed while it lives (so
        # loud hides small).
        self._noise_events = []
        self._noise_mask = None
        self._last_step_event = None
        # The noise channel's SIM clock (seconds; Game.step advances it
        # while the world runs). Event freshness and mask expiry key to
        # THIS, not wall time: behind a modal the world freezes and so
        # do the sounds in flight, and the headless harness (which runs
        # sim time far faster than wall time) ages events correctly.
        self._noise_now = 0.0
        # Placed noisemakers (add_noise_trap / add_noise_source):
        # passive traps underfoot and E-toggleable lure sources. All
        # state lives on these dicts, so a scene rebuild resets them.
        self.noise_traps = []
        self.noise_sources = []
        # The cult's errand stations (add_cult_station): scene-local
        # JOBS a scouting cultist walks between. Not patrol routes --
        # per-enemy waypoints stay banned (DESIGN.md §4); this is the
        # town's WORK, and any noise or sighting peels him off it.
        self.cult_stations = []
        # Live door-leaf animations (door_pulse): (tx, ty) -> {open,
        # hold}. Read by the TILT doorway draw only -- the flat pitch-0
        # view keeps its static leaves (byte-identity gate).
        self._door_anim = {}
        # Door LOOK for this scene's exit tiles: "wood" (default -- the
        # framed, hinged surface doors) or "cave" (2026-07, the mine
        # retrofit: a rough rock mouth with timber shoring and NO leaf --
        # a mine adit; set on every underground scene by load_scene).
        # Mechanics are identical either way; this is draw-only.
        self.door_style = "wood"
        self.on_enter_fn = None
        self.on_exit_fn = None
        self.on_interact_fn = None    # called when E pressed and no NPC nearby
        # Points the [E] prompt should hover over for on_interact_fn-driven
        # readables/pickups (the case notebook, the cellar Ledger, the Mask
        # altar...). Without these, scene interactions handled in
        # on_interact_fn had no cue at all and players walked past them.
        # Each entry is (x, y, radius). See Game._draw_interact_prompt.
        self.interactables = []
        self.on_update_fn = None      # called every tick if set: fn(game, scene, dt)
        # Recurring ambient one-shots, ticked by Scene.update. Each
        # entry is [countdown, sfx_name, vol, lo, hi, pan_spread]; see
        # add_ambient. Additive: the depths' per-room cues and the
        # world rot air layer both ride this list, so neither
        # clobbers the other (or on_update_fn).
        self.ambient_cues = []
        self.combat = False
        # Optional human-readable name for HUD display. When None,
        # the HUD falls back to a name lookup (DISPLAY_NAMES below)
        # and finally to titlecasing the scene key. Builders can
        # override for bespoke labels (e.g. "the Cellar").
        self.display_name = None
        # Watcher cameras. Each entry is a dict:
        #   {"x": px, "y": px, "range": px, "_t": 0.0}
        # The Game's _tick_eye_cameras polls them every frame: if
        # the player is unhidden and within `range`, the watcher's
        # `_t` accumulates. At threshold (~2.5 s) the watcher
        # fires a proximity bump + alert audio. Hide breaks line
        # of sight and the timer decays. (No scenes populate this
        # list currently.)
        self.eye_cameras = []

    def world_dx(self, from_x, to_x):
        """Shortest signed x-delta from from_x to to_x respecting
        the scene's wrap_x. Without wrap this is just to_x - from_x;
        with wrap it can be the opposite sign if the wrap is shorter."""
        dx = to_x - from_x
        if self.wrap_x:
            w_px = self.w * TILE
            if dx > w_px / 2:
                dx -= w_px
            elif dx < -w_px / 2:
                dx += w_px
        return dx

    def world_dy(self, from_y, to_y):
        """Shortest signed y-delta respecting wrap_y."""
        dy = to_y - from_y
        if self.wrap_y:
            h_px = self.h * TILE
            if dy > h_px / 2:
                dy -= h_px
            elif dy < -h_px / 2:
                dy += h_px
        return dy

    def render_row(self, ty):
        """Map a requested tile row to the scene row whose CONTENT renders there.

        For a plain scene this is `ty % h` when wrap_y (toroidal column) else
        `ty` unchanged. For a `_render_band` scene (the arrival road) rows NORTH
        of the band (ty < top) tile the anonymous band content endlessly, while
        the band itself and everything south of it render once -- so the looping
        forest stretch reads as an infinite corridor with no southern landmark
        (the dead car, the sign, the dirt crossing) ever cloned into the
        distance. Used by the floor raster + the tilt wall/billboard collector
        so both the ground and the tree walls extend to the vanishing point."""
        band = self._render_band
        if band is not None:
            top, bot = band
            if ty < top:
                span = bot - top
                return top + ((ty - top) % span)
            return ty
        return ty % self.h if self.wrap_y else ty

    def world_dist(self, from_x, from_y, to_x, to_y):
        """Shortest world distance respecting wrap on both axes."""
        import math as _math
        dx = self.world_dx(from_x, to_x)
        dy = self.world_dy(from_y, to_y)
        return _math.hypot(dx, dy)

    # ---- the noise channel (2026-07 sound overhaul) ---------------------
    def emit_noise(self, x, y, loud, kind="step", reach=None):
        """Broadcast a world noise at (x, y) with loudness `loud` [0..1].
        The cult ticks hear it through systems/stealth.hear_noise; events
        stay audible for NOISE_FRESH seconds. A live noise MASK (a
        dominant source like the bell) swallows events quieter than its
        level inside its radius -- SO LOUD IT HIDES SMALL SOUNDS -- and
        the swallowed event never reaches anyone's ears. `reach`
        overrides the LISTENER'S hearing range for this event alone: a
        dominant source (the bell) is audible out to `reach` px no
        matter whose ears; None keeps each listener's own range.
        Returns the event tuple, or None if masked."""
        now = self._noise_now
        m = self._noise_mask
        if m is not None:
            mx, my, mrad, mlevel, muntil = m
            if now > muntil:
                self._noise_mask = None
            elif (loud < mlevel
                    and self.world_dist(x, y, mx, my) <= mrad):
                return None
        # prune stale events so the list never grows past a frame's worth
        self._noise_events = [e for e in self._noise_events
                              if now - e[3] < 0.4]
        evt = (x, y, loud, now, kind, reach)
        self._noise_events.append(evt)
        # legacy single-slot mirror (loudest fresh event wins the slot)
        last = self._last_step_event
        if (last is None or loud >= last[2] or now - last[3] >= 0.4):
            self._last_step_event = (x, y, loud, now)
        return evt

    def set_noise_mask(self, x, y, radius, level, duration):
        """Install the dominant-source mask for `duration` SIM seconds
        (the bell). While it lives, emit_noise swallows anything quieter
        than `level` within `radius` of (x, y). Call again to extend."""
        self._noise_mask = (x, y, radius, level,
                            self._noise_now + duration)

    def clear_noise_mask(self):
        self._noise_mask = None

    def mask_active(self):
        """True while a dominant noise source is masking the room."""
        m = self._noise_mask
        if m is None:
            return False
        if self._noise_now > m[4]:
            self._noise_mask = None
            return False
        return True

    def add_noise_source(self, x, y, kind, loud=0.8, period=1.4,
                         reach=340.0, sfx=None, on_notice=None,
                         off_notice=None, silenced_notice=None):
        """Register a TURN-ON-ABLE noise source (the truck radio, the
        works valve). E toggles it (Game._try_toggle_source); while on,
        Game._tick_noise_sources emits a periodic event at (x, y) --
        loud enough to turn scout heads (0.8 < the searcher pull, so
        it lures patrols without breaking a sighting-born search) and
        carrying its own `reach`. The first mobile cult hunter to
        reach it shuts it off and sweeps around it. Notices are the
        placement's own fiction; the machinery is shared."""
        src = dict(x=x, y=y, kind=kind, on=False, t=0.0, loud=loud,
                   period=period, reach=reach, sfx=sfx,
                   on_notice=on_notice, off_notice=off_notice,
                   silenced_notice=silenced_notice)
        self.noise_sources.append(src)
        self.add_interactable(x, y, 40)
        return src

    def door_pulse(self, tx, ty, hold=0.9, quiet=False):
        """Swing the door leaf at tile (tx, ty) open for `hold` seconds
        (then Game._tick_doors eases it shut). Returns True if this
        pulse OPENED a resting door (the caller plays the door_open
        foley), False if it only extended a swing already live.
        `quiet=True` marks the swing as ALREADY covered by other foley
        (the transition fade plays its own door_open/door_close pair),
        so neither end of it makes a sound of its own."""
        key = (tx % self.w if self.wrap_x else tx,
               ty % self.h if self.wrap_y else ty)
        st = self._door_anim.get(key)
        if st is None:
            self._door_anim[key] = {"open": 0.0, "hold": hold,
                                    "quiet": quiet}
            return True
        st["hold"] = max(st["hold"], hold)
        return False

    # Light-emitting decoration kinds and their mechanical pool radii
    # (px). Mirrors the fixtures _draw_dark renders visibly so what
    # LOOKS lit IS lit to the stealth model.
    _LIGHT_KINDS = {"wall_torch": 90.0, "brazier": 90.0,
                    "campfire": 80.0, "lantern": 60.0, "candle": 55.0}

    def light_sources(self):
        """Cached [(x, y, r)] of the scene's light-emitting decorations
        (see _LIGHT_KINDS). Rebuilt when the decoration count changes
        (world rot adds decals at load; nothing removes lights)."""
        cache = getattr(self, "_light_cache", None)
        if cache is not None and cache[0] == len(self.decorations):
            return cache[1]
        srcs = [(d.x, d.y, self._LIGHT_KINDS[d.kind])
                for d in self.decorations if d.kind in self._LIGHT_KINDS]
        self._light_cache = (len(self.decorations), srcs)
        return srcs

    def lit_at(self, x, y):
        """True when world (x, y) stands inside any light pool -- the
        darkness-concealment gate (a player beside a torch reads as lit
        however dark the room is)."""
        for lx, ly, r in self.light_sources():
            if self.world_dist(x, y, lx, ly) <= r:
                return True
        return False

    def add_cult_station(self, x, y, pose=None, face=None,
                         dwell=(3.0, 6.0)):
        """Register an errand station: a spot where the cult's work
        happens (a basin lip, a sorting table, the stone ring). A
        scouting cultist walks his stations in nearest-first rounds
        (systems/stealth.errand_step), takes up `pose` facing `face`,
        dwells a random spell inside `dwell`, and moves on. Noise and
        sightings always outrank the chore; he resumes after."""
        self.cult_stations.append(dict(x=x, y=y, pose=pose, face=face,
                                       dwell=dwell))

    def add_noise_trap(self, x, y, kind, seed=None):
        """Place a PASSIVE noisemaker underfoot: strewn cans, glass
        litter, a loose plank, a crow that flushes. Stepping into its
        radius fires once (Game._trip_noise_traps): the foley plays and
        the noise event goes out to listening cultists. Leave and
        return (past a short re-arm) to fire it again; the crow is
        one-shot per load (the bird is gone). The matching decoration
        is placed automatically."""
        spec = {
            "cans":  dict(r=20.0, loud=0.75, sfx="cans_rattle",
                          deco="tin_cans"),
            "glass": dict(r=18.0, loud=0.80, sfx="glass_crunch",
                          deco="glass_litter"),
            "plank": dict(r=18.0, loud=0.72, sfx="wood_pop",
                          deco="loose_plank"),
            "crow":  dict(r=55.0, loud=0.75, sfx="crow_flush",
                          deco="crow"),
        }[kind]
        from entities.decoration import Decoration
        d = Decoration(x, y, spec["deco"], seed=seed)
        self.add_decoration(d)
        trap = dict(x=x, y=y, kind=kind, r=spec["r"], loud=spec["loud"],
                    sfx=spec["sfx"], deco=d, inside=False, cool=0.0)
        self.noise_traps.append(trap)
        return trap

    def char_floor_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if self.wrap_y:
            ty %= self.h
        if self.wrap_x:
            tx %= self.w
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.floor[ty][tx]
        return "#"

    def char_object_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if self.wrap_y:
            ty %= self.h
        if self.wrap_x:
            tx %= self.w
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.objects[ty][tx]
        return "#"

    # --- Cover-aware navigation (cultist pursuit, DESIGN.md §4) ----------
    # The cult AI (entities/enemy.py + npc.py) routes AROUND the volumetric
    # cover now standing mid-floor (pillars, pews, cots, basins) via a
    # wrap-aware BFS over a walkable tile grid, while staying a straight shot
    # in the open. Folds are first-class: the grid wraps and the line test
    # crosses the seam, so a chase carries seamlessly THROUGH a fold.
    def _nav_solid_at(self, x_px, y_px):
        """STATIC blocker test for navigation -- walls + furniture only, NOT
        the (moving) NPCs that is_solid_at also counts. Baking live bodies
        into the path grid would leave phantom walls where someone briefly
        stood. Wrap-aware via the char_*_at lookups."""
        return (is_object_solid(self.char_object_at(x_px, y_px))
                or is_floor_solid(self.char_floor_at(x_px, y_px)))

    def nav_grid(self):
        """Cached [h][w] bool grid -- True where a tile centre is walkable.
        Built once per scene instance (objects/floor are static after the
        build pass; world rot only adds non-solid decals + swaps NPCs)."""
        g = getattr(self, "_nav_grid", None)
        if g is None:
            half = TILE // 2
            g = [[not self._nav_solid_at(tx * TILE + half, ty * TILE + half)
                  for tx in range(self.w)] for ty in range(self.h)]
            self._nav_grid = g
        return g

    def nav_clear_line(self, x0, y0, x1, y1, step=10):
        """True if the straight (wrap-aware) segment from (x0,y0) to (x1,y1)
        crosses no static blocker -- the cheap shortcut that keeps motion
        straight in the open and only pays for BFS when cover intervenes."""
        dx = self.world_dx(x0, x1)
        dy = self.world_dy(y0, y1)
        # max(1, ...) so a target within one `step` still samples the
        # endpoint -- otherwise n==0 skips the loop and reports a clear line
        # to a solid tile a few px away.
        n = max(1, int(math.hypot(dx, dy) // step))
        for i in range(1, n + 1):
            if self._nav_solid_at(x0 + dx * i / n, y0 + dy * i / n):
                return False
        return True

    def set_ground(self, heightfield):
        """Attach a ground heightfield: an (h x w) float grid of per-tile
        heights (world z, px), from rendering.heightfield.build_heightfield.
        Pass None to clear it (back to dead-flat)."""
        self._ground_hf = heightfield

    def ground_z(self, x_px, y_px):
        """Terrain height (world z, px) under a world point. 0.0 for a scene
        with no heightfield -- so unopted scenes and pitch 0 are a strict
        no-op. Bilinear over the per-tile grid (values sit at tile CENTRES),
        clamped at the edges, so the surface reads as a smooth swell, not a
        staircase."""
        hf = self._ground_hf
        if hf is None:
            return 0.0
        gx = x_px / TILE - 0.5
        gy = y_px / TILE - 0.5
        x0 = int(math.floor(gx))
        y0 = int(math.floor(gy))
        fx = gx - x0
        fy = gy - y0
        h = len(hf)
        w = len(hf[0]) if h else 0
        if w == 0:
            return 0.0

        def _s(tx, ty):
            tx = 0 if tx < 0 else (w - 1 if tx >= w else tx)
            ty = 0 if ty < 0 else (h - 1 if ty >= h else ty)
            return hf[ty][tx]
        a = _s(x0, y0)
        b = _s(x0 + 1, y0)
        c = _s(x0, y0 + 1)
        d = _s(x0 + 1, y0 + 1)
        top = a + (b - a) * fx
        bot = c + (d - c) * fx
        return top + (bot - top) * fy

    def clear_sight_line(self, x0, y0, x1, y1, step=10):
        """True if the straight (wrap-aware) segment from (x0,y0) to (x1,y1)
        crosses no SIGHT blocker -- walls and solid props occlude; windows and
        floor (water/pits) do NOT (see `blocks_sight`). This is the line-of-
        sight predicate the cult AI uses to decide if it can actually SEE the
        player, not merely sense distance: step behind a wall or a solid prop
        and you break the chase. Distinct from `nav_clear_line` (which treats
        water/pits as solid for pathing); a cultist can see ACROSS a pit it
        cannot walk through, so sight must not reuse the nav predicate.

        On a scene with a ground heightfield a terrain CREST also occludes: a
        hill higher than the eye-to-target sight ray hides what is beyond it
        (CAMERA.md Phase 6). The flat path (no heightfield) is unchanged."""
        dx = self.world_dx(x0, x1)
        dy = self.world_dy(y0, y1)
        n = max(1, int(math.hypot(dx, dy) // step))
        hf = self._ground_hf
        if hf is None:
            for i in range(1, n + 1):
                if self.blocks_sight(x0 + dx * i / n, y0 + dy * i / n):
                    return False
            return True
        ez = self.ground_z(x0, y0) + _SIGHT_EYE_H
        tz = self.ground_z(x1, y1) + _SIGHT_EYE_H
        for i in range(1, n + 1):
            f = i / n
            sx = x0 + dx * f
            sy = y0 + dy * f
            if self.blocks_sight(sx, sy):
                return False
            if self.ground_z(sx, sy) > ez + (tz - ez) * f:
                return False
        return True

    def nav_path(self, fx, fy, tx, ty, max_visit=None):
        """Wrap-aware BFS over the walkable grid. Returns a list of world-
        centre points from the step AFTER the start up to the goal tile, or
        None if unreachable (caller falls back to a straight step).
        8-connected, with no diagonal corner-cutting through a solid."""
        from collections import deque
        g = self.nav_grid()
        w, h = self.w, self.h
        # Explore the whole (small) underground rooms fully; only the big
        # surface maps hit a bound -- there a far blocked goal is rare and a
        # straight fallback is fine. Sized so a reachable goal is never missed
        # in the rooms that actually have mid-floor cover.
        if max_visit is None:
            max_visit = min(w * h, 4000)

        def norm(i, j):
            if self.wrap_x:
                i %= w
            if self.wrap_y:
                j %= h
            return i, j

        def ok(i, j):
            i, j = norm(i, j)
            return 0 <= i < w and 0 <= j < h and g[j][i]

        si, sj = norm(int(fx // TILE), int(fy // TILE))
        gi, gj = norm(int(tx // TILE), int(ty // TILE))
        if (si, sj) == (gi, gj) or not ok(gi, gj):
            return None
        came = {(si, sj): None}
        q = deque([(si, sj)])
        found = False
        while q:
            ci, cj = q.popleft()
            if (ci, cj) == (gi, gj):
                found = True
                break
            if len(came) > max_visit:
                break
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nij = norm(ci + di, cj + dj)
                if nij in came or not ok(*nij):
                    continue
                if di and dj and not (ok(ci + di, cj) and ok(ci, cj + dj)):
                    continue                      # don't cut a solid corner
                came[nij] = (ci, cj)
                q.append(nij)
        if not found:
            return None
        path = []
        cur = (gi, gj)
        half = TILE // 2
        while cur is not None and cur != (si, sj):
            ci, cj = cur
            path.append((ci * TILE + half, cj * TILE + half))
            cur = came[cur]
        path.reverse()
        return path

    def nav_toward(self, fx, fy, tx, ty):
        """Immediate (sx, sy) a pursuer at (fx,fy) should step toward to reach
        (tx,ty) while routing around cover. Straight to the target when the
        line is clear; otherwise the FARTHEST path node still on a clear line
        (string-pulling, so motion arcs smoothly around corners rather than
        zig-zagging tile-to-tile). Returns the target unchanged when no route
        exists -- the caller's per-axis slide then nudges along the wall."""
        if self.nav_clear_line(fx, fy, tx, ty):
            return tx, ty
        path = self.nav_path(fx, fy, tx, ty)
        if not path:
            return tx, ty
        nxt = path[0]
        for p in path:
            if self.nav_clear_line(fx, fy, p[0], p[1]):
                nxt = p
            else:
                break
        return nxt

    def blocks_sight(self, x_px, y_px):
        """True where the tile occludes the player's LINE OF SIGHT (Phase 4
        blind-spot vision, rendering/sight.py). Walls and solid props block;
        windows do NOT (you see through glass), and the floor never blocks
        (water/pits don't hide what's beyond them). Wrap-aware via the
        char_*_at lookups."""
        ch = self.char_object_at(x_px, y_px)
        if ch in _WINDOW_CHARS:
            return False
        od = OBJECT_DEFS.get(ch)
        if od and od.get("see_over"):
            return False           # low enough to see (and be seen) over
        return ch in _WALL_CHARS or is_object_solid(ch)

    def is_solid_at(self, x_px, y_px, ignore=None):
        if is_object_solid(self.char_object_at(x_px, y_px)): return True
        if is_floor_solid(self.char_floor_at(x_px, y_px)): return True
        for npc in self.npcs:
            if npc is ignore or not npc.solid: continue
            # Wrap-aware proximity so NPC blocking still works across a
            # fold seam (raw abs() would miss a body one tile away on
            # the other side of the wrap).
            if (abs(self.world_dx(x_px, npc.x)) < 12
                    and abs(self.world_dy(y_px, npc.y)) < 12):
                return True
        return False

    def find_exit_at(self, x_px, y_px, facing=None):
        """Return the (target_scene, spawn) for the tile at the player
        position, or None. If the exit has a direction requirement and
        the player's facing doesn't match (dot product < 0.6), return
        None -- the tile reads as floor and the player walks over it.
        Used for fold-stitched hidden scenes that only open if you
        approach them from a specific direction."""
        ch = self.char_object_at(x_px, y_px)
        data = self.exits.get(ch)
        if data is None:
            return None
        required_dir = self.exit_directions.get(ch)
        if required_dir and facing is not None:
            vec = _DIRECTION_VECTORS.get(required_dir)
            if vec is not None:
                fx, fy = facing
                dx, dy = vec
                if (dx * fx + dy * fy) < 0.6:
                    return None
        return data

    def add_exit(self, char, target_scene, spawn_id="default",
                 direction=None):
        """Register an exit. `direction` (optional) is one of
        'north', 'south', 'east', 'west' -- the exit fires only when
        the player crosses the tile heading that way. Used for hidden
        fold scenes the player has to stumble into from a specific
        approach."""
        self.exits[char] = (target_scene, spawn_id)
        if direction:
            self.exit_directions[char] = direction

    def set_spawn(self, name, tx, ty):
        self.spawns[name] = (tx * TILE + TILE // 2, ty * TILE + TILE // 2)

    def add_npc(self, npc):
        self.npcs.append(npc)

    def add_decoration(self, deco):
        # A spanning shoring frame is SPLIT into its two uprights, each
        # anchored on its own post, so the tilt depth sort can interleave
        # an actor walking the lane between them (one shared anchor gave
        # the whole set a single depth and the far post popped in front
        # of whoever stood under the beam). The beam rides the +axis
        # post ("b"); broken sets (span<=1) stay whole.
        if (getattr(deco, "kind", None) == "shoring_frame"
                and float(deco.kwargs.get("span", 0.0) or 0.0) > 1
                and "half" not in deco.kwargs):
            from entities.decoration import Decoration
            ang = float(deco.kwargs.get("ang", 0.0) or 0.0)
            s = (getattr(deco, "scale", 1.0) or 1.0)
            hs = float(deco.kwargs["span"]) * s / 2.0
            dx, dy = math.cos(ang), math.sin(ang)
            for tag, sgn in (("a", -1.0), ("b", 1.0)):
                kw = dict(deco.kwargs, half=tag)
                self.decorations.append(
                    Decoration(deco.x + dx * hs * sgn,
                               deco.y + dy * hs * sgn, "shoring_frame",
                               scale=deco.scale, seed=deco.seed, **kw))
            return
        self.decorations.append(deco)

    def seat_tabletop_props(self):
        """Lift each small tabletop prop (candle, lamp, bowl, ledger...) that
        sits on a furniture footprint onto that surface, by tagging it with a
        deco `z` = the furniture top. Without this it draws at the furniture's
        BASE under tilt (floating at floor level beside the desk). Run once after
        the scene is built; idempotent (scenes rebuild each load). An explicit
        `z` already set by the builder is left alone."""
        if not self._surface_tops:
            return
        for d in self.decorations:
            if d.kind not in _TABLETOP_PROP_KINDS:
                continue
            if getattr(d, "kwargs", {}).get("z"):
                continue
            top = self._surface_tops.get((int(d.x // TILE), int(d.y // TILE)))
            if top:
                d.kwargs["z"] = top

    def add_furniture(self, kind, tiles, see_over=False, **kw):
        """Place a sized furniture decoration centred over `tiles` (a
        list of (tx, ty)) and mark those tiles solid + invisible for
        collision -- so furniture can span several tiles (or sit shy
        of one) instead of reading as uniform 1-tile squares. `kw`
        (w, h, seed, color, ...) pass through to the decoration.

        `see_over=True` stamps the SEE-OVER footprint ('x'): still solid, but it
        does not block line of sight, so a low piece (a reception counter, a
        desk) lets whoever stands behind it stay visible over the top."""
        from entities.decoration import Decoration
        from rendering.furniture import is_see_over_furniture, FURNITURE
        if self.objects and isinstance(self.objects[0], str):
            self.objects = [list(r) for r in self.objects]
        xs = [t[0] for t in tiles]
        ys = [t[1] for t in tiles]
        # Low furniture (chairs, tables, counters, beds, crates...) is see-over
        # by default: solid, but you look over it so whoever's behind stays
        # visible. Tall pieces (bookshelf, wardrobe, fireplace) keep blocking.
        footprint = "x" if (see_over or is_see_over_furniture(kind)) else "X"
        # Record each footprint tile's top height so a tabletop prop on it can be
        # seated on the surface (seat_tabletop_props).
        top_h = FURNITURE.get(kind, (0, 0, 0))[2] * (kw.get("scale", 1.0) or 1.0)
        for tx, ty in tiles:
            if 0 <= ty < len(self.objects) and 0 <= tx < len(self.objects[ty]):
                self.objects[ty][tx] = footprint
            self._surface_tops[(tx, ty)] = top_h
        cx = (min(xs) * TILE + (max(xs) + 1) * TILE) // 2
        cy = (min(ys) * TILE + (max(ys) + 1) * TILE) // 2
        deco = Decoration(cx + kw.pop("dx", 0), cy + kw.pop("dy", 0), kind, **kw)
        self.add_decoration(deco)
        return deco

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def add_item(self, x, y, key, qty=1, on_pickup=None):
        self.items.append({"x": x, "y": y, "key": key, "qty": qty, "on_pickup": on_pickup})

    def add_interactable(self, x, y, radius=40):
        """Register a point the [E] prompt should hover over -- for
        readables/pickups resolved in on_interact_fn (which the prompt
        system otherwise can't see)."""
        self.interactables.append((x, y, radius))

    def add_chalk_door(self, x, y, voice=None, seed=0, wall=False):
        """Place a chalk-drawn door (the cult's drawn-door compulsion) AND an
        [E]-examinable point. `wall=False` draws it flat on the FLOOR (a decal
        you'd step down into); `wall=True` hangs it on the nearest perimeter
        WALL. Examining one surfaces the PI's interior voice
        (Game._try_chalk_interact): the FIRST chalk door examined in a scene
        that set `voice` fires that beat; the rest give a brief flat line. Most
        chalk doors are placed voice-less -- they are the creeping VISUAL
        motif; only a few key ones carry a beat."""
        from entities.decoration import Decoration
        kind = "chalk_door_wall" if wall else "chalk_door"
        self.add_decoration(Decoration(x, y, kind, seed=seed))
        if not hasattr(self, "_chalk_doors"):
            self._chalk_doors = []
        self._chalk_doors.append((x, y))
        if voice is not None:
            self._chalk_voice = voice
        self.add_interactable(x, y, 40)

    def scatter_chalk_doors(self, count, seed=0, wall_count=0):
        """Obsessively fill an empty-feeling room with chalk doors -- drawn
        over and over, NONE overlapping. Places `count` floor doors on open
        interior tiles (min spacing) and `wall_count` against perimeter walls.
        These are the creeping VISUAL swarm: examinable (a flat line) but NOT
        [E]-prompted, so they don't spam the prompt. The one door that carries
        a voice beat is added separately via add_chalk_door(voice=...)."""
        import random as _r
        from entities.decoration import Decoration
        rng = _r.Random(seed * 131 + 7)
        W, H = self.w, self.h
        if not hasattr(self, "_chalk_doors"):
            self._chalk_doors = []
        taken = {(int(cx // TILE), int(cy // TILE)) for cx, cy in self._chalk_doors}
        # Keep clear of E-points (the desk/altar/etc.) so a swarmed door never
        # steals another interactable's press.
        inter = {(int(ix // TILE), int(iy // TILE))
                 for ix, iy, _ in self.interactables}

        def is_open(tx, ty):
            if not (1 <= tx < W - 1 and 1 <= ty < H - 1
                    and self.objects[ty][tx] == "."):
                return False
            return not any(abs(tx - ix) + abs(ty - iy) < 2 for ix, iy in inter)

        def place(cands, n, wall):
            laid = 0
            rng.shuffle(cands)
            for tx, ty in cands:
                if laid >= n:
                    break
                if any(abs(tx - ax) + abs(ty - ay) < 2 for ax, ay in taken):
                    continue
                self.add_decoration(Decoration(
                    tx * TILE + 16, ty * TILE + 16,
                    "chalk_door_wall" if wall else "chalk_door",
                    seed=rng.randint(1, 9999)))
                self._chalk_doors.append((tx * TILE + 16, ty * TILE + 16))
                taken.add((tx, ty))
                laid += 1

        floor = [(tx, ty) for ty in range(1, H - 1) for tx in range(1, W - 1)
                 if is_open(tx, ty)]
        # A FLOOR door's art is taller than a tile: require the vertical
        # neighbours open too, or the chalk spills across the wall band
        # and reads as drawn OUTSIDE the room (2026-07 containment fix).
        contained = [(tx, ty) for tx, ty in floor
                     if is_open(tx, ty - 1) and is_open(tx, ty + 1)]
        place(list(contained), count, False)
        if wall_count:
            edge = [(tx, ty) for tx, ty in floor
                    if tx in (1, W - 2) or ty in (1, H - 2)]
            place(edge, wall_count, True)

    def find_marker(self, ch):
        for ty, r in enumerate(self.objects):
            for tx, c in enumerate(r):
                if c == ch:
                    return tx, ty
        return None

    def consume_marker(self, ch):
        pos = self.find_marker(ch)
        if pos:
            tx, ty = pos
            self.objects[ty][tx] = "."
            invalidate_tilt_objects()
            return tx, ty
        return None

    def add_ambient(self, name, vol, lo, hi, pan_spread=0.0):
        """Schedule a recurring ambient one-shot: `name` fires every
        lo..hi seconds (re-rolled per fire) at `vol` with a little
        volume jitter, panned within +-pan_spread so the cue comes
        from somewhere. Additive -- a scene can carry any number of
        these. The depths' per-room cues and the world rot air
        layer both route through here."""
        self.ambient_cues.append(
            [random.uniform(lo, hi), name, vol, lo, hi, pan_spread])

    def update(self, dt, game):
        # The talk-hold: whoever the player is actually TALKING to (the
        # live float-caption speaker, or the partner of an organic
        # conversation, ui/conversation) stands their ground and faces the
        # player instead of walking their route mid-sentence -- a worker
        # can't wander off between an asked question and its answer.
        # Pursuit is exempt on purpose: a chaser mid-hunt and the King
        # never pause for talk.
        held = None
        fs = getattr(game, "float_speech", None)
        if fs is not None and fs.active:
            held = fs.speaker
        convo = getattr(game, "_convo", None)
        if convo is not None and getattr(convo, "active", False):
            # During the PI's own spoken beats the float speaker is the
            # PLAYER -- the partner must stay held through those too, or
            # a worker walks off exactly between the asked question and
            # its answer.
            if held is None or held is game.player:
                held = convo.npc
        if held is not None and (getattr(held, "movement", "") == "chaser"
                                 or getattr(held, "sprite_kind", "")
                                 == "yellow_king"):
            held = None
        for npc in self.npcs:
            if npc is held and npc.alive:
                dx = game.player.x - npc.x
                dy = game.player.y - npc.y
                d = math.hypot(dx, dy) or 1.0
                npc.facing = (dx / d, dy / d)
                continue
            npc.update(dt, self, game.player)
        for d in self.decorations:
            d.update(dt)
        px, py = game.player.x, game.player.y
        for tr in self.triggers:
            if tr.get("once") and tr.get("fired"): continue
            x1, y1, x2, y2 = tr["rect"]
            if x1 <= px <= x2 and y1 <= py <= y2:
                tr["fired"] = True
                tr["fn"](game)
        for cue in self.ambient_cues:
            cue[0] -= dt
            if cue[0] <= 0:
                _, name, vol, lo, hi, spread = cue
                cue[0] = random.uniform(lo, hi)
                pan = random.uniform(-spread, spread) if spread else None
                game.audio.play(name, vol * random.uniform(0.7, 1.0),
                                pan=pan)
        if self.on_update_fn is not None:
            self.on_update_fn(game, self, dt)

    def draw(self, surf, cam_x, cam_y, camera=None):
        if self.wrap_x:
            x0 = int(cam_x // TILE) - 1
            x1 = int((cam_x + SCREEN_W) // TILE) + 2
        else:
            x0 = max(0, int(cam_x // TILE) - 1)
            x1 = min(self.w, int((cam_x + SCREEN_W) // TILE) + 2)
        if self.wrap_y:
            y0 = int(cam_y // TILE) - 1
            y1 = int((cam_y + SCREEN_H) // TILE) + 2
        else:
            y0 = max(0, int(cam_y // TILE) - 1)
            y1 = min(self.h, int((cam_y + SCREEN_H) // TILE) + 2)
        draw_scene_terrain(surf, self, cam_x, cam_y, x0, y0, x1, y1)
        world_w_px = self.w * TILE
        world_h_px = self.h * TILE
        for d in self.decorations:
            d.draw(surf, cam_x, cam_y, camera)
            # Wrap-clones so decorations stay in view across the seam.
            offsets = [(0, 0)]
            if self.wrap_x:
                offsets += [(-world_w_px, 0), (world_w_px, 0)]
            if self.wrap_y:
                offsets += [(0, -world_h_px), (0, world_h_px)]
            if self.wrap_x and self.wrap_y:
                offsets += [(-world_w_px, -world_h_px),
                            (-world_w_px, world_h_px),
                            (world_w_px, -world_h_px),
                            (world_w_px, world_h_px)]
            for dx_off, dy_off in offsets[1:]:
                # legacy path uses the shifted cam; camera path uses the
                # explicit world offset (the clone sits at self.pos + off).
                d.draw(surf, cam_x - dx_off, cam_y - dy_off, camera,
                       wox=dx_off, woy=dy_off)
        draw_scene_doors(surf, self, cam_x, cam_y, x0, y0, x1, y1)


def tile_footstep(ch):
    return floor_step_sound(ch)


def drop_ammo_cache(game, scene, tx, ty, qty, flag):
    """Place a one-time pistol_ammo pickup at tile (tx, ty), gated by a
    save flag so re-entering the scene can't farm infinite rounds. Called
    from a scene's on_enter_fn (needs game.save). Auto-picked on contact."""
    if game.save.flag(flag):
        return
    scene.add_item(tx * TILE + 16, ty * TILE + 16, "pistol_ammo", qty,
                   on_pickup=lambda g: g.save.set_flag(flag, True))


def chest_interact(game, scene, chest_x, chest_y, flag_key, loot,
                   key_required=None, range_px=44):
    """Generic chest interaction. Call from a scene's on_interact_fn
    after a proximity check is acceptable -- this helper does its own
    range check first, so a single on_interact_fn can chain multiple
    chest_interact() calls with early-return.

    Returns True if the chest was just opened (so the caller can
    short-circuit), False otherwise. Loot is a list of item keys; each
    entry is added to the player's inventory and surfaced in the
    notice queue. The chest's decoration is flipped to its `open`
    visual on a successful open."""
    if (abs(game.player.x - chest_x) > range_px
            or abs(game.player.y - chest_y) > range_px):
        return False
    if game.save.flag(flag_key):
        game.show_notice("Empty.")
        return True
    if key_required and not game.player.inventory.has(key_required):
        game.audio.play("door_locked", 0.7)
        game.show_notice("Locked.")
        return True
    game.save.set_flag(flag_key, True)
    from systems.items import ITEM_DEFS
    for item_key in loot:
        game.player.inventory.add(item_key, 1)
        d = ITEM_DEFS.get(item_key, {"name": item_key})
        game.show_notice(f"Got: {d['name']}.")
    game.audio.play("pickup_rare", 0.7)
    # Flip the chest decoration to its open visual.
    for deco in scene.decorations:
        if (deco.kind == "chest"
                and abs(deco.x - chest_x) < 8
                and abs(deco.y - chest_y) < 8):
            deco.kwargs["open"] = True
            break
    return True
