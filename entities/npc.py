"""NPC -- talkable, sometimes solid, sometimes wandering."""
import math
import random

from constants import C_WHITE

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
        """Cultist behaviour state machine. Replaces the prior
        two-phase scout/chase dispatch. Transitions between
        SCOUT, CHASE, SEARCH, INVESTIGATE based on LOS and
        broadcast step events. Hunter (_force_chase=True)
        bypasses the machine and walks straight at the player
        every tick -- the apex avatar doesn't search or
        investigate, it closes."""
        import pygame
        # Wrap-aware: chasers compute the shortest distance through
        # the fold so the player can't escape by wrapping.
        dx = scene.world_dx(self.x, player.x)
        dy = scene.world_dy(self.y, player.y)
        d = math.hypot(dx, dy)
        has_los = (d < 180
                   and getattr(player, "hidden", None) is None)
        # Hunter override: ignore the machine, ignore flanking.
        # The avatar's behaviour is dictated by _yk_update for the
        # YK sprite kind; non-YK NPCs with _force_chase set still
        # short-circuit here for parity.
        if self._force_chase:
            self._cult_state = "chase"
            self._step_toward((player.x, player.y), dt, scene)
            return
        # Audio reaction. Fires only in SCOUT (an investigating or
        # searching cultist already has a target and shouldn't
        # rubber-band to every footstep). A fresh, close, loud
        # event kicks them to INVESTIGATE.
        if self._cult_state == "scout":
            evt = getattr(scene, "_last_step_event", None)
            if evt is not None:
                ex, ey, loud, et = evt
                now = pygame.time.get_ticks() / 1000.0
                if (now - et < 0.4
                        and scene.world_dist(self.x, self.y, ex, ey) < 180
                        and loud >= 0.7):
                    self._cult_state = "investigate"
                    self._cult_state_t = 4.0
                    self._last_seen_pos = (ex, ey)
                    self._scout_target = None
        # Promotion to CHASE on LOS, from any state.
        if has_los:
            if self._cult_state != "chase":
                self._cult_state = "chase"
                self._cult_state_t = 0.0
                self._scout_target = None
            # A cultist that locks on blooms into His maw -- but ONLY once
            # the world is corrupt enough (3+ evidence; flagged on the scene
            # by Game each frame). Below that they stay mundane.
            if self.sprite_kind == "cultist":
                self.morph_target = (1.0 if getattr(scene, "_bloom_enabled",
                                                    False) else 0.0)
            self._last_seen_pos = (player.x, player.y)
            target = (self._flank_target if self._flank_target
                      else (player.x, player.y))
            self._step_toward(target, dt, scene)
            return
        # No LOS. Drop flank intent; the leader/follower roles
        # only mean anything when at least one cultist has LOS.
        self._flank_target = None
        # Demotion from CHASE: lost the player. Transition to
        # SEARCH and walk to last-known position.
        if self._cult_state == "chase":
            self._cult_state = "search"
            self._cult_state_t = 6.0
        if self._cult_state == "search":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self._scout_target = None
                self.morph_target = 0.0
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 30:
                self._step_toward((tx, ty), dt, scene)
            else:
                # Arrived at last-known. Mill within ~80 px using
                # the existing scout pick-and-look loop. Cultist
                # reads as "checking the spot" rather than locked.
                self._scout_step(dt, scene)
            return
        if self._cult_state == "investigate":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self._scout_target = None
                self.morph_target = 0.0
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 14:
                self._step_toward((tx, ty), dt, scene)
            else:
                # At the source. Rotate facing on a slow sweep so
                # the cultist visibly scans before giving up.
                ang = (pygame.time.get_ticks() / 1000.0) % math.tau
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # Default: SCOUT.
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
        self._step_toward(self._scout_target, dt, scene)

    def _yk_update(self, dt, scene, player):
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
        # It floats, but doesn't pass through walls: take the full step
        # if clear, else slide along whichever axis is open.
        if not scene.is_solid_at(nx, ny, ignore=self):
            self.x, self.y = nx, ny
        elif not scene.is_solid_at(nx, self.y, ignore=self):
            self.x = nx
        elif not scene.is_solid_at(self.x, ny, ignore=self):
            self.y = ny
        # Pressed against a wall with no progress: swing the heading so
        # it arcs around the obstacle instead of grinding into it.
        if self._yk_stuck_t > 0.5:
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

    def _step_toward(self, target, dt, scene):
        tx, ty = target
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
