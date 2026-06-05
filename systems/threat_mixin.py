"""THRESHOLD threat model -- the core mechanic, extracted from systems/game.py.

King in Yellow, the watcher-curse, cultist pursuit (incl. the fold/portal
hand-off), the visibility meter + evidence floor, and the death triggers.
These are methods of the Game class, split into a mixin so the orchestrator
stays navigable. They run on the live Game instance (self.scene, self.player,
self.audio, ...) and read tuning from systems.config. No behavior change.
"""
import math
import random

from constants import TILE
from entities.npc import NPC
from scenes import Scene
from rendering.sprites import reset_king_fx
from systems.config import *        # noqa: F401,F403


class ThreatMixin:
    def _tick_cultists(self, dt):
        """Regular cultists roam every outdoor scene (chaser AI: scout,
        chase on sight, search, investigate). Their gaze raises
        visibility while they hold line of sight, and contact spikes it
        -- but they never kill (the King is the only kill). His gaze
        binds the curse: stay exposed in its sightline long enough and a
        permanent curse lands. Safe interiors are
        refuges -- no cultists, and the gaze-pressure lifts."""
        self._gaze_count = 0
        if self.scene is None or self.player is None:
            return
        key = self.scene.key
        # Safe interiors + non-cult scenes host no cult patrol: sweep stray
        # cultists and bail. The one exception is a fold-FOLLOWER -- a pursuer
        # that chased you through the seam into here. It isn't a spawn; it
        # persists and can still reach you (the chase you carried in), but draws
        # no patrol, gaze, or reinforcements. A true refuge (FOLD_REFUGE_SCENES)
        # is gated upstream, so no follower is ever stashed into one.
        if key in SAFE_SCENES or key not in CULTIST_SCENES:
            survivors = []
            for n in self.scene.npcs:
                tag = str(getattr(n, "tag", ""))
                if tag.startswith("cult_") and not getattr(n, "_fold_follower", False):
                    continue                 # stray patrol cultist: sweep it
                survivors.append(n)
            self.scene.npcs = survivors
            hidden = self.player.hidden is not None
            for n in survivors:
                if not getattr(n, "_fold_follower", False):
                    continue
                if getattr(n, "_stun_t", 0) > 0:
                    continue                 # shoved: blind + can't grab
                d = math.hypot(n.x - self.player.x, n.y - self.player.y)
                if d < 22 and not hidden and self.player.invuln <= 0:
                    self._trigger_death("cultist")
                    return
            return
        self._ensure_cultists(key, dt)
        hidden = self.player.hidden is not None
        for n in self.scene.npcs:
            tag = getattr(n, "tag", "")
            if not isinstance(tag, str) or not tag.startswith("cult_"):
                continue
            if getattr(n, "_stun_t", 0) > 0:
                continue                     # shoved: blind + can't grab
            d = math.hypot(n.x - self.player.x, n.y - self.player.y)
            sees = (d < getattr(n, "_gaze_range", 180)) and not hidden
            if sees:
                self._gaze_count += 1
            if tag == "cult_convert":
                # A turned local: passive cult. Their watching raises
                # visibility (counted above) but they never chase, spot,
                # grab, or flank. The fallen town just stares.
                continue
            # Regular cultist: one "they've seen you" beat per fresh
            # spawn. Reaching you is the cult TAKING you -- the CAPTURED
            # card, then the run ends (you feed the hive). Not a kill.
            if sees and not getattr(n, "_has_been_spotted", False):
                n._has_been_spotted = True
                self.audio.play("low_pulse", 0.5)
                self.show_notice("They've seen you.", duration=2.4)
            if d < 22 and not hidden and self.player.invuln <= 0:
                self._trigger_death("cultist")
                return
        self._flank_cultists()

    def _tick_gaze_bind(self, dt):
        """His gaze, binding the curse (NARRATIVE 1b/3). In a GAZE_BIND_SCENES
        scene, staying EXPOSED (not
        hidden) while visibility is high lets His eye fix on you: a timer
        climbs, and crossing GAZE_BIND_TIME binds the first Watcher. Hiding,
        or dropping below GAZE_BIND_VIS, bleeds the timer back -- cover and
        keeping your head down are the only way out. Once cursed, the Watcher
        system (_tick_watchers) owns the swarm; this only lands the seed."""
        if self._cursed:
            self._gaze_bind_t = 0.0
            return
        if (self.scene is None or self.player is None
                or self.scene.key not in GAZE_BIND_SCENES
                or self.scene.key in KING_FREE_SCENES):
            self._gaze_bind_t = 0.0
            return
        exposed = (self.player.hidden is None
                   and self.visibility >= GAZE_BIND_VIS)
        t = getattr(self, "_gaze_bind_t", 0.0)
        if exposed:
            if t == 0.0:
                self.audio.play("low_pulse", 0.6)
                self.show_notice("You feel it find you. Get out of the open.",
                                 duration=3.0)
            t += dt
            if t >= GAZE_BIND_TIME:
                self._apply_curse()
                t = 0.0
        else:
            t = max(0.0, t - dt * 1.5)
        self._gaze_bind_t = t

    def _ensure_cultists(self, key, dt):
        """Keep the current cult scene topped up with CULT_REGULARS roaming
        cultists. Rate-limited so killing one buys a breather, not an instant
        respawn. (The watcher-curse is His own gaze, bound in
        _tick_gaze_bind; NARRATIVE 1b/3.)"""
        self._cult_topup_t -= dt
        if self._cult_topup_t > 0:
            return
        self._cult_topup_t = CULT_TOPUP_INTERVAL
        regulars = [n for n in self.scene.npcs
                    if getattr(n, "tag", "") == "cult_regular"
                    and getattr(n, "alive", True)]
        if len(regulars) < CULT_REGULARS:
            self._spawn_cultist("cult_regular", "cultist",
                                 speed=0.85, gaze_range=180)

    def _flank_cultists(self):
        """When 2+ regular cultists are chasing in an open scene, the
        closest leads a straight chase and the rest peel to perpendicular
        flanks to cut the player off. Tight scenes fall back to a
        straight pile-on."""
        chasers = [n for n in self.scene.npcs
                   if getattr(n, "tag", "") == "cult_regular"
                   and getattr(n, "_cult_state", "") == "chase"]
        if (len(chasers) >= 2
                and self._openness_around(self.player.x,
                                          self.player.y) >= 6):
            chasers.sort(key=lambda n: math.hypot(n.x - self.player.x,
                                                  n.y - self.player.y))
            leader = chasers[0]
            leader._flank_target = None
            for follower in chasers[1:]:
                ldx = self.player.x - leader.x
                ldy = self.player.y - leader.y
                ld = math.hypot(ldx, ldy) or 1.0
                offset = max(60.0, min(160.0, ld * 0.8))
                cand_a = (self.player.x + (-ldy / ld) * offset,
                          self.player.y + (ldx / ld) * offset)
                cand_b = (self.player.x + (ldy / ld) * offset,
                          self.player.y + (-ldx / ld) * offset)
                da = math.hypot(follower.x - cand_a[0],
                                follower.y - cand_a[1])
                db = math.hypot(follower.x - cand_b[0],
                                follower.y - cand_b[1])
                follower._flank_target = cand_a if da < db else cand_b
        else:
            for n in chasers:
                n._flank_target = None

    def _openness_around(self, x, y, ring_r=64):
        """Count how many of 8 ring points around (x,y) are
        walkable. Used to gate group flanking -- in tight
        corridors the perpendicular flank targets land in walls
        and cultists end up stuck, so flanking is suppressed
        when openness < 6/8."""
        if self.scene is None:
            return 0
        n = 0
        for ang_step in range(8):
            ang = ang_step * (math.pi / 4)
            sx = x + math.cos(ang) * ring_r
            sy = y + math.sin(ang) * ring_r
            if not self.scene.is_solid_at(sx, sy):
                n += 1
        return n

    def _build_fold_cache(self):
        """After a scene load, find every SEEN fold in it (direction-gated
        exits) and pre-load the small set of target scenes once. A seen fold
        is drawn as a peek into its target (rendering.folds.draw_fold)."""
        self._folds = []
        scene = self.scene
        if scene is None:
            return
        from rendering.folds import _DIRV
        from scenes import load_scene
        cache = {}
        for ch, direction in scene.exit_directions.items():
            exit_data = scene.exits.get(ch)
            if not exit_data:
                continue
            target_key, spawn_id = exit_data
            pos = scene.find_marker(ch)
            if pos is None:
                continue
            tx, ty = pos
            if target_key not in cache:
                try:
                    cache[target_key] = load_scene(target_key)
                except Exception:
                    continue
            target = cache[target_key]
            # Look through the actual EXIT: aim the peek at the tile the
            # player will arrive on (the target's spawn for this exit's
            # spawn_id), so the peek frames where you'd emerge -- not some
            # arbitrary scene centre. Falls back to the centre if the spawn
            # is missing.
            spawn = target.spawns.get(spawn_id) or target.spawns.get("default")
            if spawn:
                anchor_tile = (int(spawn[0] // TILE), int(spawn[1] // TILE))
            else:
                anchor_tile = (target.w // 2, target.h // 2)
            self._folds.append({
                "normal": _DIRV.get(direction, (0, -1)),
                "target": target,
                "anchor_tile": anchor_tile,
                "fold_px": (tx * TILE + TILE // 2, ty * TILE + TILE // 2),
            })

    def _exit_is_fold(self, exit_data):
        """True if taking this exit is a FOLD or a seamless world-passage --
        the world's wrongness (a direction-gated fold) or its open ground (an
        outdoor-to-outdoor crossing). A mundane fade -- a door, ladder, or
        rope into an interior -- is NOT a fold. Shared by the fold-pursuit
        stash and the fold-watcher roll so both read 'fold' the same way."""
        if self.scene is None or self.player is None:
            return False
        target_scene = exit_data[0]
        ch = self.scene.char_object_at(self.player.x, self.player.y)
        is_fold = ch in self.scene.exit_directions
        cur = self.scene.key
        is_passage = (cur in SEAMLESS_WORLD_SCENES
                      and target_scene in SEAMLESS_WORLD_SCENES)
        return is_fold or is_passage

    def _roll_fold_watcher(self, exit_data):
        """Walking through a fold/portal has a FOLD_WATCHER_CHANCE (1/20) to
        manifest +1 Watcher -- the seed that STARTS the curse cloning. Called
        the instant an exit fires (before the swap); it BINDS the curse, and
        the destination's _tick_watchers then manifests the seed Watcher on
        arrival and begins cloning it. Never fires when the player already
        carries WATCHER_MAX -- that's the ceiling a fold can't push past. A
        SAFE destination is exempt (Watchers are only suppressed there)."""
        if not self._exit_is_fold(exit_data):
            return
        if exit_data[0] in SAFE_SCENES:
            return
        if len(self._watchers) >= WATCHER_MAX:   # already at the ceiling -- no +1
            return
        if random.random() >= FOLD_WATCHER_CHANCE:
            return
        self._cursed = True

    def _note_fold_pursuit(self, exit_data):
        """Called the instant an exit fires, BEFORE the scene swaps. A chase
        carries through PORTALS and FOLDS alike (NARRATIVE §8): if a cultist
        is in active chase within FOLD_PURSUE_RANGE when the player crosses an
        exit, stash that one pursuer so it follows a beat behind, whether the
        exit is a door, ladder, rope, seamless passage, or a hidden fold. Both
        cultist classes count -- the surface NPC chasers AND the underground
        Enemy cultists. The chase carries through a FOLD or seamless PASSAGE, or
        a descent into cult-held ground (underground / a CULTIST_SCENE) -- INCL.
        a hidden-fold grove that hosts no cult of its own: the one chaser you
        brought with you crosses the seam and can still reach you (it does NOT
        make the grove cult territory). The escapes that shake it: a refuge
        (FOLD_REFUGE_SCENES), or a mundane door/ladder/rope into an ordinary
        interior (architecture is the player-only way out)."""
        target_scene, _spawn_id = exit_data
        # A refuge always shakes the chase (the safe houses + Mara's cell).
        if target_scene in FOLD_REFUGE_SCENES:
            self._fold_pursuer = None
            return
        # Otherwise the pursuer follows only where it can reach you on the far
        # side: through a FOLD or seamless PASSAGE (the cult's own wrong-ground,
        # incl. a hidden grove that hosts no cult of its own), or down into
        # cult-held ground -- the underground (Enemy cultists) or a surface
        # CULTIST_SCENE (NPC chasers). A mundane door / ladder / rope into an
        # ordinary interior is the player-only escape: it shakes the chase.
        if not (self._exit_is_fold(exit_data)
                or target_scene in UNDERGROUND_SCENES
                or target_scene in CULTIST_SCENES):
            self._fold_pursuer = None
            return
        hot, hot_d = None, FOLD_PURSUE_RANGE

        def _consider(c):
            nonlocal hot, hot_d
            if (getattr(c, "_cult_state", "") == "chase"
                    and getattr(c, "alive", True)):
                d = math.hypot(c.x - self.player.x, c.y - self.player.y)
                if d <= hot_d:
                    hot, hot_d = c, d

        for n in self.scene.npcs:               # surface NPC chasers
            if getattr(n, "movement", "") == "chaser":
                _consider(n)
        for e in self.scene.enemies:            # underground Enemy cultists
            if getattr(e, "kind", "") == "cultist":
                _consider(e)
        if hot is None:
            self._fold_pursuer = None
            return
        # Just enough to rebuild it on the far side (its TYPE is chosen by the
        # destination in _tick_fold_pursuit, so an underground portal lands an
        # Enemy cultist and a surface one an NPC chaser, each scene's native).
        self._fold_pursuer = {
            "kind": getattr(hot, "sprite_kind", "cultist"),
            "speed": getattr(hot, "speed", 0.85),
            "gaze_range": getattr(hot, "_gaze_range", 180),
            "tag": getattr(hot, "tag", "cult_regular"),
        }

    def _tick_fold_pursuit(self, dt):
        """Spawn the stashed fold-pursuer a beat behind the player, at the
        seam they entered through -- never on top of them. It resumes the
        chase already knowing where the player is (it came through after
        them). Consumed once it fires."""
        if self._fold_pursuer is None or self.player is None:
            return
        info = self._fold_pursuer
        if "entry_tile" not in info:      # stashed but not yet armed by a load
            return
        self._fold_pursuer_grace -= dt
        if self._fold_pursuer_grace > 0:
            return
        et = info.get("entry_tile")
        if not et:
            self._fold_pursuer = None
            return
        sx = et[0] * TILE + TILE // 2
        sy = et[1] * TILE + TILE // 2
        gap = math.hypot(sx - self.player.x, sy - self.player.y)
        # Hold until the player steps off the seam -- unless they dawdle past
        # the force window, in which case the lunge lands anyway.
        if (gap < FOLD_PURSUE_MIN_GAP
                and self._fold_pursuer_grace > -FOLD_PURSUE_FORCE):
            return
        if self.scene.is_solid_at(sx, sy):
            self._fold_pursuer = None
            self._fold_pursuer_grace = 0.0
            return
        if self.scene.key in UNDERGROUND_SCENES:
            # Underground rooms run Enemy cultists (the death-gate keys on
            # Enemy kind=='cultist' in chase) -- so the pursuer that came down
            # after you must be one too, not a surface NPC chaser.
            from scenes.depths import _cultist
            e = _cultist(sx, sy, speed=info["speed"])
            e._cult_state = "chase"
            e._last_seen_pos = (self.player.x, self.player.y)
            self.scene.enemies.append(e)
        else:
            npc = self._spawn_cultist(info["tag"], info["kind"],
                                      speed=info["speed"],
                                      gaze_range=info["gaze_range"],
                                      at=(sx, sy))
            if npc is not None:
                # Mark it a fold-FOLLOWER so a non-cult destination (a hidden
                # grove, an ordinary interior) keeps it alive and lethal --
                # _tick_cultists sweeps stray cultists in such rooms, but spares
                # the one chaser that came through the seam after you.
                npc._fold_follower = True
                npc._cult_state = "chase"
                npc._last_seen_pos = (self.player.x, self.player.y)
        self._fold_pursuer = None
        self._fold_pursuer_grace = 0.0

    def _spawn_cultist(self, tag, kind, speed=0.85, gaze_range=180,
                       movement="chaser", name="", at=None):
        """Plant a cultist. If `at` (x, y) is given and walkable, they enter
        there (the door you came in by -- for reinforcement waves); otherwise
        at the farthest walkable scene corner from the player, so they enter
        from the edges rather than on top of you. Returns the NPC, or None."""
        scene = self.scene
        best = None
        if at is not None:
            ax = at[0] + random.uniform(-12, 12)
            ay = at[1] + random.uniform(-12, 12)
            if not scene.is_solid_at(ax, ay):
                best = (ax, ay)
        if best is None:
            corners = [
                (4 * Scene.TILE, 4 * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, 4 * Scene.TILE),
                (4 * Scene.TILE, (scene.h - 4) * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, (scene.h - 4) * Scene.TILE),
            ]
            best_d = -1.0
            for sx, sy in corners:
                if scene.is_solid_at(sx, sy):
                    continue
                d = math.hypot(sx - self.player.x, sy - self.player.y)
                if d > best_d:
                    best_d, best = d, (sx, sy)
        if best is None:
            return None
        n = NPC(best[0], best[1], name, kind,
                voice="blip_low", portrait=None,
                movement=movement, speed=speed,
                no_prompt=True, solid=False)
        n.tag = tag
        n.dialogue_fn = None
        n._gaze_range = gaze_range
        n._has_been_spotted = False
        self.scene.add_npc(n)
        return n

    def _enemy_sees_player(self):
        """True if any hostile currently has line of sight on the
        player. Hostiles are the patrol/chaser NPCs; their sight
        range matches the chaser AI (180 px). Hiding (corn cover or
        a hide spot) breaks line of sight unconditionally, which is
        what makes cover the player's main tool for shedding threat."""
        if self.scene is None or self.player is None:
            return False
        if self.player.hidden is not None:
            return False
        px, py = self.player.x, self.player.y
        for n in self.scene.npcs:
            if not getattr(n, "alive", True):
                continue
            tag = getattr(n, "tag", None)
            hostile = ((isinstance(tag, str) and tag.startswith("patrol_"))
                       or getattr(n, "movement", None) in ("chaser",
                                                            "stalker"))
            if not hostile:
                continue
            if math.hypot(n.x - px, n.y - py) < 180:
                return True
        return False

    def _tick_visibility(self, dt):
        """The visibility meter [0, 1] -- how visible the player is to
        the King in Yellow. Watchers (spawned by a cultist's curse)
        push it up; hiding bleeds it down. At 1.0 the King materialises
        (see _tick_king); claw it back under 0.90 and he dissolves.

        Heavy curses tip the balance: enough Watchers out-pace even
        hiding -- the spiral toward a King the player can no longer
        shake."""
        if self.scene is None or self.player is None:
            return
        hidden = getattr(self.player, "hidden", None) is not None
        n_watch = len(self._watchers)
        # A burning flashlight marks you. The cost applies everywhere the
        # beam is lit EXCEPT the safe cellar (DIM_SAFE) -- there the light
        # is a free comfort, your one room to read by. Cover can't hide a
        # lit torch, so the rise lands in both branches.
        lit_rise = (VIS_LIT_RISE
                    if (self._flashlight_lit()
                        and self.scene.key not in DIM_SAFE_SCENES)
                    else 0.0)
        if hidden:
            # In cover the cult's gaze breaks; only a lit torch still leaks.
            self.visibility += dt * (lit_rise - VIS_HIDE_BLEED)
        else:
            rise = self._gaze_count * VIS_GAZE + lit_rise
            self.visibility += dt * (rise - VIS_IDLE_DECAY)
        # FLOORS the meter can't bleed below: evidence (the more you
        # understand, the higher your baseline) PLUS each live Watcher of the
        # curse. Capped just under the King so the curse presses you to the
        # edge but stays survivable -- and thus curable by clearing them.
        watcher_floor = n_watch * WATCHER_FLOOR
        self._vis_floor = min(VIS_FLOOR_TOTAL_CAP,
                              self._evidence_floor() + watcher_floor)
        self.visibility = max(self._vis_floor, min(1.0, self.visibility))

    def _evidence_count(self):
        """How many distinct evidence beats have been logged -- the gate
        that arms the King (NARRATIVE §3)."""
        log = self.save.arg("evidence", []) if self.save else []
        return len(log) if isinstance(log, list) else 0

    def _evidence_floor(self):
        """Visibility floor summed from each logged evidence's weight. The
        more of the case you understand, the higher your baseline exposure;
        capped just under unshakeable. Tolerates legacy bare-string entries."""
        log = self.save.arg("evidence", []) if self.save else []
        if not isinstance(log, list):
            return 0.0
        total = sum(e.get("weight", EVIDENCE_FLOOR_DEFAULT)
                    if isinstance(e, dict) else EVIDENCE_FLOOR_DEFAULT
                    for e in log)
        return min(VIS_FLOOR_CAP, total)

    def _tick_king(self, dt):
        """The King in Yellow -- the lethal apex. The instant
        visibility hits 1.0 he materialises at the doorway the player
        entered from and hunts relentlessly; reaching the player ends
        the run (the closure sequence). Drop visibility below 0.90 --
        by hiding -- and he dissolves. Safe rooms never host him."""
        if self.scene is None or self.player is None:
            return
        in_safe = self.scene.key in KING_FREE_SCENES
        if self._reinforce_t > 0:
            self._reinforce_t -= dt
        if self._king is None:
            self.audio.king_tone(False)
            if self.visibility >= 1.0 and not in_safe:
                # Investigating arms the apex: 3+ evidence and a maxed meter
                # bring the King himself; below that, only a cultist wave.
                if self._evidence_count() >= KING_GATE_EVIDENCE:
                    self._spawn_king()
                else:
                    self._muster_reinforcements()
            return
        # He is here. Dissolve if visibility falls or the player
        # reaches a refuge; otherwise check for the catch.
        if self.visibility < 0.90 or in_safe:
            self._despawn_king()
            return
        d = math.hypot(self._king.x - self.player.x,
                       self._king.y - self.player.y)
        # His signature tone loops while he's on screen and swells the closer
        # he gets -- the same nearness curve that cracks the mask open.
        prox = max(0.0, min(1.0, 1.0 - (d - KING_THREAT_NEAR) /
                            (KING_THREAT_FAR - KING_THREAT_NEAR)))
        self.audio.king_tone(True, 0.28 + 0.6 * prox)
        # Don't let the King catch mid-eruption: while _birth ramps
        # 0->1 (~1.2s, npc._yk_update) he can't move, so he mustn't
        # kill either -- that ramp is the player's grace window.
        if d < 24 and getattr(self._king, "_birth", 1.0) >= 1.0:
            self._trigger_death("king")

    def _muster_reinforcements(self):
        """Below the evidence gate, a maxed meter musters a cultist wave at the
        entry the player came in by -- the net tightening, not yet lethal.
        Pulsed on a cooldown so it never floods, and only where the cult can
        actually hold (CULTIST_SCENES); elsewhere the meter just sits maxed."""
        if self._reinforce_t > 0 or self.scene is None:
            return
        if self.scene.key not in CULTIST_SCENES:
            return
        self._reinforce_t = REINFORCE_COOLDOWN
        for _ in range(REINFORCE_COUNT):
            self._spawn_cultist("cult_regular", "cultist",
                                 speed=0.85, gaze_range=180,
                                 at=self._king_anchor)

    def _spawn_king(self):
        """Materialise the King at the entry doorway (_king_anchor),
        falling back to the player's position if no anchor was set."""
        ax, ay = self._king_anchor or (self.player.x, self.player.y)
        king = NPC(ax, ay, "", "yellow_king",
                   movement="chaser", speed=2.4,
                   no_prompt=True, solid=False)
        king.tag = "king"
        king.dialogue_fn = None
        king._birth = 0.0      # 0..1 eruption progress (renderer reads it)
        king._gait = 0.0       # run-cycle phase, advanced by movement
        self.scene.add_npc(king)
        self._king = king
        self.audio.play("void_sting", 0.7)

    def _despawn_king(self):
        if self._king is not None and self.scene is not None:
            try:
                self.scene.npcs.remove(self._king)
            except ValueError:
                pass
        self._king = None
        reset_king_fx()        # drop his trail/particles so they don't bleed on
        self.audio.king_tone(False)

    def _apply_curse(self):
        """Land the watcher-curse. Rather than a permanent escalation it
        BINDS a Watcher to you; it clones (up to WATCHER_MAX) while you stay
        exposed, and each live Watcher raises the visibility FLOOR. Clear
        them all -- stare each down, or put one down with the axe or a round
        -- and the curse lifts. Safe interiors only suppress them."""
        self.audio.play("void_sting", 0.8)
        if not self._cursed:
            self._cursed = True
            self._watcher_clone_t = WATCHER_CLONE_INTERVAL
            self.show_notice("Something has been bound to you. It will not "
                             "stop watching until you make it.", duration=3.8)
            self._spawn_watcher()
        else:
            self.visibility = min(1.0, self.visibility + 0.1)
            self.show_notice("The binding tightens. More will open.",
                             duration=3.0)

    def _tick_watchers(self, dt):
        """The watcher-curse. While cursed a Watcher is bound to the player
        and CLONES (up to WATCHER_MAX) while the player is EXPOSED (in the
        open); each live Watcher raises the visibility floor (in
        _tick_visibility). Safe interiors only suppress them -- they re-form
        on the way out. The curse lifts only when the player clears them all
        (gaze / axe / shot), handled in _dispel_watcher."""
        if self.scene is None or self.player is None:
            return
        # Drop any swept on load/death.
        self._watchers = [w for w in self._watchers if w in self.scene.npcs]
        if not self._cursed:
            if self._watchers:
                self.scene.npcs = [n for n in self.scene.npcs
                                   if getattr(n, "tag", "") != "watcher"]
                self._watchers = []
            return
        if self.scene.key in KING_FREE_SCENES:      # safe room: suppress only
            if self._watchers:
                self.scene.npcs = [n for n in self.scene.npcs
                                   if getattr(n, "tag", "") != "watcher"]
                self._watchers = []
            return
        if not self._watchers:                      # re-form the seed on exit
            self._spawn_watcher()
            self._watcher_clone_t = WATCHER_CLONE_INTERVAL
        # Cloning is EXPOSURE-gated: advances in the open, pauses in cover.
        if self.player.hidden is None and len(self._watchers) < WATCHER_MAX:
            self._watcher_clone_t -= dt
            if self._watcher_clone_t <= 0:
                self._watcher_clone_t = WATCHER_CLONE_INTERVAL
                self._spawn_watcher()
        # Staring one down dissolves it (the cure).
        self._tick_watcher_gaze(dt)

    def _spawn_watcher(self):
        """Manifest one Watcher at a walkable tile a little way off, in a
        random direction around the player. It stands and stares (the
        'watch' movement). A faint breath and a small visibility nudge
        mark the moment it opens its eyes."""
        scene = self.scene
        spot = None
        for _ in range(12):
            ang = random.uniform(0, math.tau)
            r = random.uniform(180, 300)
            wx = self.player.x + math.cos(ang) * r
            wy = self.player.y + math.sin(ang) * r
            if (0 < wx < scene.w * Scene.TILE
                    and 0 < wy < scene.h * Scene.TILE
                    and not scene.is_solid_at(wx, wy)):
                spot = (wx, wy)
                break
        if spot is None:
            return
        w = NPC(spot[0], spot[1], "", "watcher",
                voice="blip_low", portrait="watcher",
                movement="watch", speed=0.0,
                no_prompt=True, solid=False)
        w.tag = "watcher"
        w.dialogue_fn = None
        scene.add_npc(w)
        self._watchers.append(w)
        self.visibility = min(1.0, self.visibility + 0.03)
        self.audio.play("breath", 0.4)

    def _tick_watcher_gaze(self, dt):
        """Holding a Watcher in your gaze (facing it, within range) dissolves
        it over WATCHER_GAZE_DISPEL seconds -- its eyes are already dark while
        looked at. Look away and the progress bleeds back. This is the free
        (but slow, and exposed) way to clear them."""
        p = self.player
        fdx, fdy = p.facing
        for w in list(self._watchers):
            pdx, pdy = w.x - p.x, w.y - p.y
            d = math.hypot(pdx, pdy) or 1.0
            looking = ((pdx / d) * fdx + (pdy / d) * fdy) > 0.55 and d < 360
            gt = getattr(w, "_gaze_dispel_t", 0.0)
            if looking:
                gt += dt
                if gt >= WATCHER_GAZE_DISPEL:
                    self._dispel_watcher(w, reason="gaze")
                    continue
            else:
                gt = max(0.0, gt - dt * 1.5)
            w._gaze_dispel_t = gt

    def _dispel_watcher(self, w, reason="gaze"):
        """Dissolve one Watcher. If it was the last one and we're not merely
        being suppressed by a safe room, the curse lifts (you're cured)."""
        if w in self._watchers:
            self._watchers.remove(w)
        if self.scene is not None and w in self.scene.npcs:
            self.scene.npcs.remove(w)
        self.audio.play("breath" if reason == "gaze" else "void_sting", 0.45)
        if (self._cursed and not self._watchers and self.scene is not None
                and self.scene.key not in KING_FREE_SCENES):
            self._cursed = False
            self.show_notice("The last of the eyes closes. The curse lifts, "
                             "for now.", duration=3.2)

    def _dispel_watcher_in_line(self, p, fx, fy):
        """A round (or the axe arc) puts a Watcher down instantly. The gun
        version: dissolve the nearest Watcher roughly along the facing line.
        Costs the same scarce round the shot already spent, and the report
        still draws the cult -- so it's the fast, loud, costly clear."""
        best, bestd = None, 1e9
        for w in self._watchers:
            pdx, pdy = w.x - p.x, w.y - p.y
            d = math.hypot(pdx, pdy) or 1.0
            if d > 520:
                continue
            if ((pdx / d) * fx + (pdy / d) * fy) < 0.82:   # must be ~in front
                continue
            if d < bestd:
                bestd, best = d, w
        if best is not None:
            self._dispel_watcher(best, reason="shot")

    # A transgression the cult notices -- entering the cult basement,
    # picking up evidence, tripping a trespass camera, being captured,
    # the flashback, the Clerk's confrontation. Spikes visibility by
    # `bump` (a one-off step toward being seen) and latches the
    # `cult_provoked` save flag.
    # NOTE: the flag is currently only a RECORD that provocation
    # happened -- nothing reads it to gate behaviour (cultist gaze
    # already drives visibility in CULTIST_SCENES from the start). It's
    # left as a hook for a future "dormant until provoked" gate; the
    # visibility bump is the live effect.
    def _provoke_cult(self, bump=0.0):
        if not self.save.flag("cult_provoked"):
            self.save.set_flag("cult_provoked", True)
        if bump > 0:
            self.visibility = min(1.0, self.visibility + bump)

    def _trigger_death(self, kind):
        """A pursuer has reached the player. Hand off to the death
        screen: `kind` is 'cultist' (the CAPTURED card -- the cult takes
        you alive for the hive) or 'king' (the King-in-Yellow furnace of
        masks / Carcosa, ~3.5s). Both end the run and return to title. Input
        is locked for the duration via _closure_locked (the shared
        sequence lock). Guarded so it can't re-trigger."""
        if self._death_kind is not None:
            return
        self._death_kind = kind
        self._death_t = 0.0
        self._closure_locked = True
        self.audio.force_silence()
        if kind == "king":
            self.audio.play("void_sting", 0.9)
            self.audio.play("low_pulse", 0.8)
        else:
            self.audio.play("low_pulse", 0.7)

    def _tick_death(self, dt):
        """Hold the death screen, then resolve -- both END the run.
        Cultist: ~2.8s CAPTURED card, then back to title (the cult took
        you for the hive). King: ~3.5s of the mask furnace (Carcosa),
        then back to title, visibility held at 0.40 (never zero)."""
        if self._death_kind is None:
            return
        self._death_t += dt
        if self._death_kind in ("cultist", "sheriff"):
            if self._death_t >= 2.8:
                self._death_kind = None
                self._closure_locked = False
                self.audio.music_muted = False
                self.state = "title"
                self.audio.play_music("threshold_drone")
        else:  # king
            if self._death_t >= 3.8:
                self._death_kind = None
                self._closure_locked = False
                self._despawn_king()          # full teardown: NPC + FX + tone,
                                              # not just nulling the ref
                self.visibility = 0.40        # not zero; never zero
                self.audio.music_muted = False
                self.state = "title"
                self.audio.play_music("threshold_drone")
