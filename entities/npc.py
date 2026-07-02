"""NPC -- talkable, sometimes solid, sometimes wandering."""
import math
import random

from constants import C_WHITE
from systems.config import SUS_NOTICE, SUS_SCORE_HOLD
from systems.stealth import (detection_score, update_suspicion,
                             enter_search, sweep_check, hear_noise,
                             react_hold, errand_step, errand_drop)

def sprite_seed_for(x, y):
    """A stable per-actor sprite seed from the spawn position. Draw
    sites used id(self)&0xffff, but CPython ids are 16-byte aligned --
    the low bits were always zero, so seed-derived picks like the
    cultist mask variant ((seed>>3)%6) could only land on EVEN values
    (the antlered, SPLIT, and PLANK masks never spawned). Spawn coords
    are grid-quantized (multiples of 16), which keeps low bits zero
    even after an odd multiply, so a murmur-style finisher folds the
    high bits down. Position-derived, so the byte-identity capture
    stays reproducible."""
    h = (int(x) * 73856093 ^ int(y) * 19349663) & 0xffffffff
    h = ((h ^ (h >> 13)) * 0x5bd1e995) & 0xffffffff
    h ^= h >> 15
    return h & 0xffff


class NPC:
    def __init__(self, x, y, name, sprite_kind, voice="blip_mid",
                 color=C_WHITE, portrait=None, dialogue_fn=None,
                 movement="idle", speed=1.0, radius=64,
                 waypoints=None, home=None, solid=True, tag=None,
                 patrol_pause=1.0, no_prompt=False,
                 hp=30, drops=None, on_kill=None):
        self.x = x; self.y = y
        self.home = home if home else (x, y)
        self.name = name
        self.sprite_kind = sprite_kind
        self.voice = voice
        self.color = color
        self.portrait = portrait or sprite_kind
        self.dialogue_fn = dialogue_fn
        self.movement = movement
        self.speed = speed
        self.radius = radius
        self.waypoints = waypoints or []
        self.wp_idx = 0
        self.solid = solid
        self.tag = tag
        # patrol_pause: seconds the patroller dwells at each waypoint before
        # advancing to the next. Keeps the patrol from looking robotic.
        self.patrol_pause = patrol_pause
        self.patrol_pause_t = 0.0
        # When True, the [E] interact prompt is suppressed even when the
        # player is in range. Used for the "invisible interact NPC" pattern
        # (e.g. the computer terminal hosts a no_prompt NPC at its tile so
        # try_interact() picks it up but the prompt only shows when the
        # decoration's own indicator is up).
        self.no_prompt = no_prompt
        # Stable per-actor sprite seed (see sprite_seed_for above): the
        # fix for id()-alignment locking the cultist mask to even picks.
        self.sprite_seed = sprite_seed_for(x, y)
        self.facing = (0, 1)
        self.move_timer = random.uniform(0, 2)
        self.move_target = None
        self.size = 12
        # Scout state for the chaser AI's wander phase. The patrol
        # picks a random walkable tile within ~10 blocks of its
        # current position, walks there, then pauses to "look
        # around" by rotating its facing before picking the next
        # tile. Player-spotting overrides scout into chase.
        self._scout_target = None
        self._scout_pause_t = 0.0
        self._scout_look_t = 0.0
        # When True, the chaser state machine bypasses SCOUT and
        # walks straight at the player every tick. Currently
        # *unused in flight*: the only patrol that wants this is
        # the Hunter, and the Hunter sprite_kind == "yellow_king"
        # short-circuits to _yk_update before reaching the chaser
        # branch. Field + check are kept as a forward-compatible
        # hook -- a future non-YK apex patrol can flip this on
        # without rewriting the state machine.
        self._force_chase = False
        # Cultist behaviour state machine. Used by the chaser
        # movement branch:
        #   "scout"       -- random walkable tile + look-around
        #   "chase"       -- LOS on player, walk straight at them
        #   "search"      -- lost LOS; walk to last-seen + mill 6s
        #   "investigate" -- heard a loud step; walk to source 4s
        # _cult_state_t holds the remaining seconds for search /
        # investigate states; unused in scout/chase. _last_seen_pos
        # is set on chase ticks (player position) and on
        # investigate triggers (step source); used as the walk
        # target during search/investigate. _flank_target is set
        # externally by Game._flank_cultists when group flanking is
        # active; non-leader cultists walk to it instead of the
        # player while in chase.
        self._cult_state = "scout"
        self._cult_state_t = 0.0
        self._last_seen_pos = None
        self._flank_target = None
        # Per-NPC spotted flag. Each fresh spawn (re-entering a
        # scene) creates a new NPC and resets this -- so the
        # spotted-line beat fires every re-entry, not once per
        # scene per session. Read+set by Game._tick_cultists.
        self._has_been_spotted = False
        self._yk_head = None        # current heading angle (rad); steers
        self._yk_stuck_t = 0.0
        self._yk_last_pos = None
        self._yk_lean = 0.0         # smoothed locomotion 0..1 (travel tell;
                                    # the Unfolding everts forward by this much
                                    # along self.facing -- see king_unfold)
        # Round-14: NPCs are killable. They take damage from the
        # player's attacks (melee or pistol). The cult takes a
        # specific interest in this -- the kill counter feeds the
        # substrate's later evidence files. Non-hostile by default,
        # which means the player's first hit on them is the moral
        # weight; they don't fight back.
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.flash = 0.0
        self.drops = drops or []
        self.on_kill = on_kill
        # Vessel-bloom transform. `morph` (0..1) ramps toward
        # `morph_target`; the renderer (rendering.transform) turns the
        # human sprite into the Yellow-King maw as it rises. The trigger
        # is the chase state below: a cultist that locks on sets
        # morph_target to 1.0, but only once the scene is `_bloom_enabled`
        # (3+ evidence, flagged by Game each frame).
        self.morph = 0.0
        self.morph_target = 0.0
        # Stun timer (player's desperation shove). While > 0 the NPC is
        # frozen -- no movement -- and the cultist tick treats it as
        # blind, so its gaze stops feeding visibility. Buys a breath.
        self._stun_t = 0.0

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        self.flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def update(self, dt, scene, player):
        if not self.alive:
            return
        self.flash = max(0, self.flash - dt)
        if self._stun_t > 0:
            self._stun_t = max(0.0, self._stun_t - dt)
            return                      # frozen: skip all movement/AI
        if self.morph != self.morph_target:
            step = dt / 1.4
            if self.morph < self.morph_target:
                self.morph = min(self.morph_target, self.morph + step)
            else:
                self.morph = max(self.morph_target, self.morph - step)
        if self.sprite_kind == "yellow_king":
            self._yk_update(dt, scene, player)
            return
        if self.movement == "idle":
            return
        if self.movement == "watch":
            dx = player.x - self.x
            dy = player.y - self.y
            d = math.hypot(dx, dy) or 1
            self.facing = (dx / d, dy / d)
            return
        if self.movement == "wander":
            self.move_timer -= dt
            if self.move_timer <= 0 or self.move_target is None:
                self.move_timer = random.uniform(2.0, 4.0)
                ang = random.uniform(0, math.tau)
                r = random.uniform(self.radius * 0.3, self.radius)
                tx = self.home[0] + math.cos(ang) * r
                ty = self.home[1] + math.sin(ang) * r
                self.move_target = (tx, ty)
            self._step_toward(self.move_target, dt, scene)
        elif self.movement == "patrol":
            if not self.waypoints: return
            # If we're paused at a waypoint, count down before moving on.
            if self.patrol_pause_t > 0:
                self.patrol_pause_t -= dt
                return
            tx, ty = self.waypoints[self.wp_idx]
            # Detect arrival within ~6 px (covers float drift), then pause
            # briefly before advancing to the next waypoint.
            if math.hypot(self.x - tx, self.y - ty) < 6:
                self.wp_idx = (self.wp_idx + 1) % len(self.waypoints)
                self.patrol_pause_t = self.patrol_pause
                return
            self._step_toward((tx, ty), dt, scene)
        elif self.movement == "stalker":
            dx = player.x - self.x; dy = player.y - self.y
            d = math.hypot(dx, dy) or 1
            # (dx,dy) points npc->player, so this dot/d is +1 when the
            # player faces away from us and -1 when facing toward us.
            # Advance only while unobserved (or too far to matter).
            facing_away = (player.facing[0] * dx + player.facing[1] * dy) / d > -0.2
            if facing_away or d > 220:
                self._step_toward((player.x, player.y), dt, scene)
        elif self.movement == "follower":
            # THRESHOLD kid-follower. Keeps a small distance behind
            # the player at all times. Doesn't catch up too quickly
            # (looks unnatural) and stops within a comfort zone.
            dx = player.x - self.x; dy = player.y - self.y
            d = math.hypot(dx, dy) or 1
            if d > 28:
                self._step_toward((player.x, player.y), dt, scene)
            else:
                # Within comfort range. Just match the player's facing.
                self.facing = player.facing
        elif self.movement == "homebody":
            self._homebody_tick(dt, scene)
        elif self.movement == "chaser":
            self._cult_tick(dt, scene, player)

    def _homebody_tick(self, dt, scene):
        """A stay-at-home local. Loiters near their own doorstep (the
        NPC's `home`), then steps inside -- vanishing -- for a spell,
        then comes back out and loiters again. The only time you see
        them is going in or out their door. While 'inside' the NPC sets
        `_inside` True and drops `solid`; Game skips drawing it and won't
        let the player talk to it."""
        st = getattr(self, "_hb_state", None)
        if st is None:
            self._hb_state = st = "loiter"
            self._hb_t = random.uniform(3.0, 8.0)
            self._inside = False
            self.move_target = None
        self._hb_t -= dt
        if st == "loiter":
            self.move_timer -= dt
            if self.move_timer <= 0 or self.move_target is None:
                self.move_timer = random.uniform(1.4, 3.0)
                ang = random.uniform(0, math.tau)
                r = random.uniform(self.radius * 0.25, max(8, self.radius))
                self.move_target = (self.home[0] + math.cos(ang) * r,
                                    self.home[1] + math.sin(ang) * r)
            self._step_toward(self.move_target, dt, scene)
            if self._hb_t <= 0:
                self._hb_state = "returning"
                self.move_target = self.home
        elif st == "returning":
            if scene.world_dist(self.x, self.y,
                                self.home[0], self.home[1]) < 8:
                self._hb_state = "inside"
                self._hb_t = random.uniform(4.0, 9.0)
                self._inside = True
                self.solid = False
                self.x, self.y = self.home      # park on the doorstep
            else:
                self._step_toward(self.home, dt, scene)
        elif st == "inside":
            if self._hb_t <= 0:
                self._hb_state = "loiter"
                self._hb_t = random.uniform(5.0, 12.0)
                self._inside = False
                self.solid = True
                self.move_target = None

    def _cult_tick(self, dt, scene, player):
        """Cultist behaviour state machine: SCOUT, CHASE, SEARCH,
        INVESTIGATE. Detection is GRADED (STEALTH_REWORK.md Pillar 1):
        a per-enemy suspicion in [0, 1] fills from the detection score
        (los * distance * facing cone * concealment) and only a FULL
        bar locks the chase -- so there is a real "have they spotted
        me?" window, corn is leaky cover instead of a blackout, and an
        enclosed hide breaks sight entirely (its threat is the CHECK,
        below). Searchers sweep nearby enclosed hides instead of
        milling. Hunter (_force_chase=True) bypasses the machine and
        walks straight at the player every tick -- the apex avatar
        doesn't suspect or search, it closes."""
        import pygame
        # Hunter override: ignore the machine, ignore flanking.
        # The avatar's behaviour is dictated by _yk_update for the
        # YK sprite kind; non-YK NPCs with _force_chase set still
        # short-circuit here for parity.
        if self._force_chase:
            self._cult_state = "chase"
            self._step_toward((player.x, player.y), dt, scene)
            return
        # The graded detection score for this eye, this tick. Walls
        # still occlude absolutely (clear_sight_line inside); corn
        # scales it; an enclosed hide zeroes it. Fill/decay is the
        # shared accumulator (systems/stealth.py) so the two cult
        # machines can never drift.
        score = detection_score(scene, self.x, self.y, self.facing,
                                player, 180.0)
        sus = update_suspicion(self, score, dt)
        self._sus_alert = False
        # Audio reaction (the shared ear, systems/stealth.hear_noise):
        # scouts turn on any fresh loud event; searchers/investigators
        # already hold a target and are only pulled off it by something
        # strictly LOUDER (so they don't rubber-band to every footstep,
        # but a gunshot or the bell re-tasks the whole room).
        hear_noise(self, scene, 180.0)
        # Anything above a chore drops the chore: a cultist pulled off
        # his errand (noise, sighting, search) stands up out of the
        # task pose. The station index survives for the resume.
        if self._cult_state != "scout":
            errand_drop(self)
        # An active CHASE holds while any usable score remains --
        # cover has to actually break the line (a wall, an enclosed
        # hide, or corn at real distance) to shake it. Close-range
        # corn keeps the score above the hold, so diving into stalks
        # at a pursuer's feet no longer erases you.
        if self._cult_state == "chase":
            if score >= SUS_SCORE_HOLD:
                self._suspicion = 1.0
                # A cultist that locks on blooms into His maw -- but ONLY
                # once the world is corrupt enough (3+ evidence; flagged on
                # the scene by Game each frame). Below that they stay mundane.
                if self.sprite_kind == "cultist":
                    self.morph_target = (1.0 if getattr(
                        scene, "_bloom_enabled", False) else 0.0)
                self._last_seen_pos = (player.x, player.y)
                target = (self._flank_target if self._flank_target
                          else (player.x, player.y))
                self._step_toward(target, dt, scene, navigate=True)
                return
            # Lost the line. Drop flank intent and fall into SEARCH --
            # and this searcher HUNTS: it will sweep the enclosed hides
            # around where it last saw you (Pillar 3; the budget scales
            # with the sweep so it isn't abandoned mid-check).
            self._flank_target = None
            enter_search(self, scene)
        # Promotion to CHASE only on a FULL suspicion bar.
        elif sus >= 1.0:
            self._cult_state = "chase"
            self._cult_state_t = 0.0
            self._scout_target = None
            self._just_locked = True
            self._last_seen_pos = (player.x, player.y)
            if self.sprite_kind == "cultist":
                self.morph_target = (1.0 if getattr(scene, "_bloom_enabled",
                                                    False) else 0.0)
            target = (self._flank_target if self._flank_target
                      else (player.x, player.y))
            self._step_toward(target, dt, scene, navigate=True)
            return
        # NOTICE: a scout whose suspicion is climbing stops and turns
        # toward what it half-saw -- the telegraphed "have they spotted
        # me?" window. The renderer reads _sus_alert for the tell.
        if (self._cult_state == "scout" and sus >= SUS_NOTICE
                and score > 0.0):
            dxp = scene.world_dx(self.x, player.x)
            dyp = scene.world_dy(self.y, player.y)
            m = math.hypot(dxp, dyp) or 1.0
            self.facing = (dxp / m, dyp / m)
            self._sus_alert = True
            self._scout_target = None
            return
        if self._cult_state == "search":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self._scout_target = None
                self.morph_target = 0.0
                self._sweep_list = []
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 30:
                self._step_toward((tx, ty), dt, scene, navigate=True)
                return
            # At last-known. Sweep the enclosed hides nearby -- walk to
            # each and CHECK it (shared sweep_check; an occupied hide
            # starts the struggle via scene._hide_check). Only after
            # the sweep runs dry does the searcher fall back to the mill.
            if sweep_check(self, scene, player, dt,
                           lambda hx, hy: self._step_toward(
                               (hx, hy), dt, scene, navigate=True)):
                return
            self._scout_step(dt, scene)
            return
        if self._cult_state == "investigate":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self._scout_target = None
                self.morph_target = 0.0
                self._noise_loud = 0.0
                return
            # The turn-first telegraph: face the sound and hold a beat
            # before walking (the player reads the head turn).
            if react_hold(self, scene, dt):
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 14:
                self._step_toward((tx, ty), dt, scene, navigate=True)
            else:
                # At the source. Rotate facing on a slow sweep so
                # the cultist visibly scans before giving up.
                ang = (pygame.time.get_ticks() / 1000.0) % math.tau
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # Default: SCOUT. Errands first -- the cult has JOBS (scenes
        # declare stations); the random mill only where no work is set.
        if errand_step(self, scene, dt,
                       lambda ex, ey: self._step_toward(
                           (ex, ey), dt, scene, navigate=True)):
            return
        self._scout_step(dt, scene)

    def _scout_step(self, dt, scene):
        """Scout-mode tick: head toward a random walkable tile
        within ~10 blocks, pause to look around on arrival, then
        pick another. Used by the chaser AI when the player isn't
        in sight."""
        # Pause / look-around: rotate facing slowly through a few
        # cardinal directions, no movement.
        if self._scout_pause_t > 0:
            self._scout_pause_t -= dt
            self._scout_look_t -= dt
            if self._scout_look_t <= 0:
                # Pick a new facing every ~0.4s during the pause
                # so the patroller visibly scans the area.
                self._scout_look_t = 0.4
                ang = random.uniform(0, math.tau)
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # No target or arrived: roll a new one.
        if (self._scout_target is None
                or scene.world_dist(self.x, self.y,
                                     self._scout_target[0],
                                     self._scout_target[1]) < 8):
            if self._scout_target is not None:
                # Just arrived -- pause to look.
                self._scout_pause_t = random.uniform(1.2, 2.4)
                self._scout_look_t = 0.0
                self._scout_target = None
                return
            # First-roll: pick a walkable tile within 10 blocks.
            TILE = scene.TILE
            for _ in range(12):
                dxt = random.randint(-10, 10)
                dyt = random.randint(-10, 10)
                tx = int(self.x // TILE) + dxt
                ty = int(self.y // TILE) + dyt
                if not (0 <= tx < scene.w and 0 <= ty < scene.h):
                    continue
                wx = tx * TILE + TILE // 2
                wy = ty * TILE + TILE // 2
                if scene.is_solid_at(wx, wy, ignore=self):
                    continue
                self._scout_target = (wx, wy)
                break
            else:
                # No walkable tile found in 12 tries -- give up
                # this tick, retry next.
                return
        self._step_toward(self._scout_target, dt, scene, navigate=True)

    def _yk_update(self, dt, scene, player):
        # The roaming apex steers toward a target the Game sets:
        # the live player while HUNTING, a last-seen / wander point while
        # SEARCHING (so he doesn't magically home onto a hidden player). With
        # no override he chases the player directly.
        tgt = getattr(self, "_hunt_target", None)
        if tgt is not None:
            pdx = tgt[0] - self.x
            pdy = tgt[1] - self.y
        else:
            pdx = player.x - self.x
            pdy = player.y - self.y
        desired = math.atan2(pdy, pdx)
        # Birth: the King erupts from a cult member over ~1.2s before it
        # can move; _birth ramps 0->1 and the renderer plays the
        # emergence. It still turns to face the player while being born.
        self._birth = min(1.0, getattr(self, "_birth", 0.0) + dt / 1.2)
        # The King steers: its heading turns toward the player at a
        # capped rate, so it sweeps in fluid arcs -- in ANY direction,
        # diagonals included -- instead of snapping along the tile grid.
        # A constant forward drift + a heading always bending toward the
        # player traces a pursuit curve that spirals in.
        head = self._yk_head if self._yk_head is not None else desired
        diff = (desired - head + math.pi) % (2 * math.pi) - math.pi
        turn = 2.6 * dt                       # ~150 deg/s
        diff = max(-turn, min(turn, diff))
        head = (head + diff) % (2 * math.pi)
        self._yk_head = head
        self.facing = (math.cos(head), math.sin(head))
        if self._birth < 1.0:
            return
        step = self.speed * 60 * dt
        if self._yk_last_pos is None:
            self._yk_last_pos = (self.x, self.y)
        moved = math.hypot(self.x - self._yk_last_pos[0],
                           self.y - self._yk_last_pos[1])
        self._yk_stuck_t = (self._yk_stuck_t + dt
                            if moved < step * 0.4 else 0.0)
        self._yk_last_pos = (self.x, self.y)
        nx = self.x + math.cos(head) * step
        ny = self.y + math.sin(head) * step
        if getattr(self, "_phase", False):
            # The roaming apex: a 4D thing walls can't stop. He paths the floor
            # toward his target like anything else, but ignores collision -- where
            # his bulk overlaps a wall he simply exists inside it. Nothing to snag
            # on, so he never gets stuck (the roaming-King rework).
            self.x, self.y = nx, ny
        # It floats, but doesn't pass through walls: take the full step
        # if clear, else slide along whichever axis is open.
        elif not scene.is_solid_at(nx, ny, ignore=self):
            self.x, self.y = nx, ny
        elif not scene.is_solid_at(nx, self.y, ignore=self):
            self.x = nx
        elif not scene.is_solid_at(self.x, ny, ignore=self):
            self.y = ny
        # Pressed against a wall with no progress: swing the heading so
        # it arcs around the obstacle instead of grinding into it.
        if not getattr(self, "_phase", False) and self._yk_stuck_t > 0.5:
            self._yk_head = (head + 2.2 * dt) % (2 * math.pi)
        # Advance the gait phase with distance covered so the run cycle
        # matches the King's speed and freezes when it isn't moving.
        self._gait = getattr(self, "_gait", 0.0) + step * 0.18
        # Locomotion lean: ease a 0..1 magnitude toward 1 while it is
        # actually travelling (covered most of a full step this frame) and
        # back to 0 when pinned on a wall or stalled. The renderer everts
        # the mass forward along self.facing by this much -- a surge that
        # reads as the thing lunging, not just sliding to a new position.
        moving = 1.0 if moved > step * 0.5 else 0.0
        self._yk_lean += (moving - self._yk_lean) * min(1.0, dt * 4.0)

    def _step_toward(self, target, dt, scene, navigate=False):
        tx, ty = target
        # Cover-aware routing (NARRATIVE §8): the cult states bend the target
        # around walls/props (and through folds) via scene.nav_toward. The
        # apex hunter (_force_chase) opts OUT -- it closes in a straight line.
        if navigate:
            tx, ty = scene.nav_toward(self.x, self.y, tx, ty)
        # Wrap-aware so chasers take the shortest path through the fold.
        dx = scene.world_dx(self.x, tx)
        dy = scene.world_dy(self.y, ty)
        d = math.hypot(dx, dy)
        if d < 1: return
        step_x = (dx / d) * self.speed * 60 * dt
        step_y = (dy / d) * self.speed * 60 * dt
        # Per-axis slide: if the full diagonal is blocked, still move
        # along whichever axis is clear so the chaser hugs walls and
        # corners instead of freezing dead against them (matches the
        # Enemy cult-step behaviour).
        moved = False
        if not scene.is_solid_at(self.x + step_x, self.y, ignore=self):
            self.x += step_x; moved = True
        if not scene.is_solid_at(self.x, self.y + step_y, ignore=self):
            self.y += step_y; moved = True
        if moved:
            self.facing = (dx / d, dy / d)
        # Keep coords in the canonical wrapped range.
        from constants import TILE as _T
        if scene.wrap_x:
            self.x %= scene.w * _T
        if scene.wrap_y:
            self.y %= scene.h * _T

    def interact(self, game):
        if self.dialogue_fn:
            self.dialogue_fn(game, self)
