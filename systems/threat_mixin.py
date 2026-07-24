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
from rendering.king_unfold import reset_king_unfold_fx
from systems.config import *        # noqa: F401,F403
from systems.stealth import (concealment_factor as _conceal_factor,
                             is_enclosed as _is_enclosed,
                             grab_allowed as _grab_allowed)


class ThreatMixin:
    def _tick_cultists(self, dt):
        """Regular cultists roam every outdoor scene (chaser AI: scout,
        chase on sight, search, investigate). Their gaze raises
        visibility while they hold line of sight, and contact spikes it
        -- but they never kill (the King is the only kill). His gaze
        binds the curse: stay exposed in its sightline long enough and a
        permanent curse lands. Safe interiors are
        refuges -- no cultists, and the gaze-pressure lifts."""
        self._gaze_count = 0.0
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
            for n in survivors:
                if not getattr(n, "_fold_follower", False):
                    continue
                if not getattr(n, "alive", True) or getattr(n, "_is_corpse", False):
                    continue                 # a body on the floor can't grab
                if getattr(n, "_stun_t", 0) > 0:
                    continue                 # shoved: blind + can't grab
                d = math.hypot(n.x - self.player.x, n.y - self.player.y)
                if (d < CULT_GRAB_REACH and self.player.invuln <= 0
                        and _grab_allowed(self.player,
                                          getattr(n, "_cult_state", "")
                                          == "chase")):
                    self._trigger_death("cultist")
                    return
            return
        # The cult sleeps until the first find (CULT_WAKE_EV): no patrol
        # spawns at zero evidence -- the town starts merely wrong. Gaze,
        # grabs, and manually spawned cultists (tests, reinforcements)
        # below keep full behaviour either way.
        if self._evidence_count() >= CULT_WAKE_EV:
            self._ensure_cultists(key, dt)
        # Cover WEIGHTS the gaze now instead of blanking it
        # (DESIGN.md §12): corn scales each watching cultist's
        # contribution by SUS_CONCEAL_CORN, an enclosed hide zeroes it.
        conceal = _conceal_factor(self.player)
        for n in self.scene.npcs:
            tag = getattr(n, "tag", "")
            if not isinstance(tag, str) or not tag.startswith("cult_"):
                continue
            if not getattr(n, "alive", True) or getattr(n, "_is_corpse", False):
                continue                     # a body: it can't watch, spot, or grab
            if getattr(n, "_stun_t", 0) > 0:
                continue                     # shoved: blind + can't grab
            d = math.hypot(n.x - self.player.x, n.y - self.player.y)
            w = conceal if d < getattr(n, "_gaze_range", 180) else 0.0
            sees = w >= 1.0                  # plainly in the open, in range
            if w > 0.0:
                self._gaze_count += w
            if tag == "cult_convert":
                # Vestigial: the `cult_convert` tag is never set anymore (the
                # turned-local layer was cut, TODO #22c; guarded dead by
                # tests/flow.py). This branch no longer runs.
                continue
            # Regular cultist: one "they've seen you" beat per fresh
            # spawn. Reaching you is the cult TAKING you -- the CAPTURED
            # card, then the run ends (you feed the hive). Not a kill.
            if sees and not getattr(n, "_has_been_spotted", False):
                n._has_been_spotted = True
                self.audio.play("low_pulse", 0.5)
                self.show_notice("They've seen you.", duration=2.4)
            # Chase-loop cues. _cult_tick sets _just_locked when chase
            # begins (real LOS, not just gaze range) and _just_lost when
            # the player breaks cover and chase drops to search. Both
            # consumed here so the flag is one-shot per tick.
            if getattr(n, "_just_locked", False):
                n._just_locked = False
                pan = self.audio.pan_for_world(n.x, self.player.x)
                dmult = self.audio.distance_attenuation(
                    n.x, n.y, self.player.x, self.player.y)
                self.audio.play("cult_lock", 0.55 * dmult, pan=pan)
                self.audio.duck(0.7, depth=0.4)
            elif getattr(n, "_just_lost", False):
                n._just_lost = False
                pan = self.audio.pan_for_world(n.x, self.player.x)
                dmult = self.audio.distance_attenuation(
                    n.x, n.y, self.player.x, self.player.y)
                self.audio.play("cult_lose", 0.45 * dmult, pan=pan)
            # Contact takes you in the open -- and in CONCEALMENT too,
            # when the cultist has already locked (cover is not armor;
            # an enclosed hide is exempt: its threat is the CHECK/
            # struggle). One gate for every grab site:
            # systems/stealth.py grab_allowed. The reach is
            # CULT_GRAB_REACH now (the stealth economy, TODO #5):
            # brushing past an awake cultist risks the grab.
            if (d < CULT_GRAB_REACH and self.player.invuln <= 0
                    and _grab_allowed(self.player,
                                      getattr(n, "_cult_state", "")
                                      == "chase")):
                self._trigger_death("cultist")
                return
        self._flank_cultists()

    def _tick_chase_cues_enemies(self, dt):
        """Underground Enemy cultists run the same chase state machine
        as surface NPC chasers (entities/enemy.py _cult_tick mirrors
        entities/npc.py). Read their _just_locked / _just_lost flags
        here so the chase loop plays the same cult_lock / cult_lose
        stings underground as on the surface."""
        if self.scene is None or self.player is None:
            return
        for e in self.scene.enemies:
            if getattr(e, "kind", "") != "cultist":
                continue
            if not getattr(e, "alive", True):
                continue
            if getattr(e, "_just_locked", False):
                e._just_locked = False
                pan = self.audio.pan_for_world(e.x, self.player.x)
                dmult = self.audio.distance_attenuation(
                    e.x, e.y, self.player.x, self.player.y)
                self.audio.play("cult_lock", 0.55 * dmult, pan=pan)
                self.audio.duck(0.7, depth=0.4)
            elif getattr(e, "_just_lost", False):
                e._just_lost = False
                pan = self.audio.pan_for_world(e.x, self.player.x)
                dmult = self.audio.distance_attenuation(
                    e.x, e.y, self.player.x, self.player.y)
                self.audio.play("cult_lose", 0.45 * dmult, pan=pan)

    def _tick_struggle(self, dt):
        """The hide-check struggle (DESIGN.md §12). A SEARCHING
        cultist that reaches the enclosed hide the player is in CHECKS it
        (the cult ticks set scene._hide_check); that opens a short mash
        window -- E/SPACE presses count in the event loop. Enough presses
        is the burst-out (_struggle_win); the window running out is the
        grab (the CAPTURED card). Concealment cover (corn) never triggers
        this -- getting found in the stalks just resumes the chase."""
        if self.scene is None or self.player is None:
            return
        # A short post-win swallow window: the player is still mashing
        # when the struggle resolves, and a stray E must not re-enter
        # the hide (try_interact) or advance a dialog mid-panic.
        self._post_struggle_t = max(
            0.0, getattr(self, "_post_struggle_t", 0.0) - dt)
        st = getattr(self, "_struggle", None)
        if st is not None:
            st["t"] -= dt
            if st["t"] <= 0.0:
                self._struggle = None
                self._trigger_death("cultist")
            return
        check = getattr(self.scene, "_hide_check", None)
        if check is None:
            return
        self.scene._hide_check = None
        enemy, hx, hy = check
        if not _is_enclosed(self.player):
            return                      # bolted before the hands came down
        if self._death_kind is not None:
            return
        self._struggle = {"t": STRUGGLE_WINDOW, "presses": 0,
                          "enemy": enemy}
        self.audio.play("cult_lock", 0.8)
        self.audio.duck(0.9, depth=0.45)
        self.show_notice("It looks under. Hands. FIGHT. Mash E.",
                         duration=STRUGGLE_WINDOW)

    def _struggle_win(self):
        """The burst-out: the player tears free of the checking hands.
        A one-time panic sprint, the checker staggers, and the noise
        converges every searcher in earshot -- you won the moment, not
        the room."""
        st = self._struggle
        self._struggle = None
        self._post_struggle_t = 0.5      # swallow the overshoot presses
        if st is None or self.player is None or self.scene is None:
            return
        p = self.player
        p.hidden = None
        if p.hide_origin is not None:
            p.x, p.y = p.hide_origin
            p.hide_origin = None
        p._burst_t = STRUGGLE_BURST_T
        p.invuln = max(getattr(p, "invuln", 0.0), 0.8)
        enemy = st.get("enemy")
        if enemy is not None:
            enemy._stun_t = max(getattr(enemy, "_stun_t", 0.0),
                                STRUGGLE_STUN)
        # The burst is LOUD: a max-loudness noise event pulls every
        # scout in earshot to the spot...
        self.scene.emit_noise(p.x, p.y, 1.0, kind="burst")
        # ...but the step-event channel only wakes SCOUTS (searchers and
        # investigators already own a target and ignore it), so the
        # documented cost of winning -- the room CONVERGES -- is applied
        # directly: every mobile cult hunter in earshot turns on the
        # burst point. Set-piece kneelers (aggro 0 / lock_facing) and
        # apex pursuers keep their own scripts; the stunned checker is
        # skipped (it is still reeling).
        for group in (self.scene.npcs, self.scene.enemies):
            for a in group:
                if a is enemy or not getattr(a, "alive", True):
                    continue
                if getattr(a, "_is_corpse", False):
                    continue
                is_cult = (str(getattr(a, "tag", "")).startswith("cult_")
                           or getattr(a, "kind", "") == "cultist")
                if not is_cult:
                    continue
                if getattr(a, "_force_chase", False):
                    continue
                if (getattr(a, "lock_facing", False)
                        or getattr(a, "aggro", 1) == 0):
                    continue
                if getattr(a, "_cult_state", "") == "chase":
                    continue
                if self.scene.world_dist(a.x, a.y, p.x, p.y) > 220:
                    continue
                a._cult_state = "investigate"
                a._cult_state_t = 4.0
                a._last_seen_pos = (p.x, p.y)
                a.move_target = None
                if hasattr(a, "_scout_target"):
                    a._scout_target = None
        self.audio.play("hide_exit", 0.9)
        self.audio.play("bump", 0.6)
        self.show_notice("You tear free.", duration=1.8)

    # (_tick_gaze_bind retired in the play-notes Watcher rework -- the trigger
    #  is EXPOSURE from WATCHER_WAKE_EV evidence now, owned by _tick_watchers.)

    def _ensure_cultists(self, key, dt):
        """Keep the current cult scene topped up to its roaming target
        (`Scene.cult_target`, else CULT_REGULARS). On the FIRST awake tick
        after a load the scene is PREFILLED straight to target from its
        spawn-point pool (`Scene.cult_spawns`, else the map corners) so a
        cult scene reads populated the moment you enter; after that a killed
        cultist respawns only on the rate-limited breather
        (CULT_TOPUP_INTERVAL). (The Watchers are His own gaze, opened on
        exposure by _tick_watchers; NARRATIVE §4 / DESIGN.md §1.)"""
        target = getattr(self.scene, "cult_target", None) or CULT_REGULARS
        regulars = [n for n in self.scene.npcs
                    if getattr(n, "tag", "") == "cult_regular"
                    and getattr(n, "alive", True)]
        missing = target - len(regulars)
        if missing <= 0:
            return
        if not self._cult_prefilled:
            for _ in range(missing):
                if self._spawn_cultist("cult_regular", "cultist", speed=0.95,
                                       gaze_range=180, from_pool=True) is None:
                    break
            self._cult_prefilled = True
            self._cult_topup_t = CULT_TOPUP_INTERVAL
            return
        self._cult_topup_t -= dt
        if self._cult_topup_t > 0:
            return
        self._cult_topup_t = CULT_TOPUP_INTERVAL
        self._spawn_cultist("cult_regular", "cultist",
                             speed=0.95, gaze_range=180, from_pool=True)

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
        # Drop the through-view buffers for the previous scene's folds/portals.
        # Their cache keys are id()s of dicts that are about to be GC'd.
        try:
            from rendering.portal import clear_through_cache
            clear_through_cache()
        except Exception:
            pass
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
            # Same-scene folds (the maze 'I'/'Q' relocations) are SILENT by
            # canon -- the lie is the world itself, never a visible frame --
            # so they never join the seen-fold list.
            if target_key == scene.key:
                continue
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
                # The exit char, so state-driven folds can be looked up at
                # draw time (Scene.fold_charge_fn keys on it).
                "char": ch,
            })

    def _build_door_views(self):
        """After a scene load, resolve every opted-in SEE-THROUGH door
        (Scene.seethrough_doors, a set of door exit chars) to its built target
        scene + arrival anchor, so scenes.base._draw_doorway can render the room
        beyond through the recess instead of the flat dark doorway. Mirrors
        _build_fold_cache; target scenes are built once per key. A no-op (and
        byte-identical) when the scene opts nothing in."""
        scene = self.scene
        if scene is None:
            return
        scene._door_views = {}
        chars = scene.seethrough_doors
        if not chars:
            return
        from scenes import load_scene
        from scenes.base import _DOOR_CHARS
        cache = {}
        for ty, row in enumerate(scene.objects):
            for tx, ch in enumerate(row):
                if ch not in chars or ch not in _DOOR_CHARS:
                    continue
                exit_data = scene.exits.get(ch)
                if not exit_data:
                    continue
                target_key, spawn_id = exit_data
                if target_key == scene.key:
                    continue                       # a same-scene fold, not a door
                if target_key not in cache:
                    try:
                        cache[target_key] = load_scene(target_key)
                    except Exception:
                        continue
                target = cache[target_key]
                spawn = (target.spawns.get(spawn_id)
                         or target.spawns.get("default"))
                anchor = spawn if spawn else (target.w * TILE // 2,
                                              target.h * TILE // 2)
                scene._door_views[(tx, ty)] = {"target": target,
                                               "anchor_px": anchor}

    def _exit_is_fold(self, exit_data):
        """True if taking this exit is a FOLD or a seamless world-passage --
        the world's wrongness (a direction-gated fold) or its open ground (an
        outdoor-to-outdoor crossing). A mundane fade -- a door, ladder, or
        rope into an interior -- is NOT a fold. Used by the fold-watcher roll
        (His curse-gaze seeds on any fold OR passage). Pursuit no longer uses
        this: a chaser on foot follows only across a direction-gated rift
        fold (play-notes narrowing, see _note_fold_pursuit)."""
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
        SAFE destination is exempt (Watchers are only suppressed there), and
        so is any destination outside WATCHER_OPEN_SCENES (a fold into a
        surface interior binds nothing -- His gaze does not open indoors)."""
        if not self._exit_is_fold(exit_data):
            return
        if (exit_data[0] in SAFE_SCENES
                or exit_data[0] not in WATCHER_OPEN_SCENES):
            return
        if len(self._watchers) >= WATCHER_MAX:   # already at the ceiling -- no +1
            return
        if random.random() >= FOLD_WATCHER_CHANCE:
            return
        self._cursed = True

    def _note_fold_pursuit(self, exit_data):
        """Called the instant an exit fires, BEFORE the scene swaps. A chaser
        follows the player ONLY across a true rift FOLD -- a direction-gated
        pane (play-notes narrowing of DESIGN.md §7): if a cultist is in active
        chase within FOLD_PURSUE_RANGE when the player steps through a fold,
        stash that one pursuer so it follows a beat behind at the seam. Both
        cultist classes count -- the surface NPC chasers AND the underground
        Enemy cultists. Every ORDINARY crossing shakes the chase: a door,
        ladder, rope, a seamless outdoor passage, a road loop, or any non-fold
        target -- a chaser does not cross an ordinary scene boundary. A refuge
        (FOLD_REFUGE_SCENES) is never breached even by a fold."""
        target_scene, _spawn_id = exit_data
        # A same-scene relocation (the maze 'I'/'Q' folds) never touches the
        # stash: no scene load follows, the pursuer is still physically in
        # this room, and the wrap-aware chase AI keeps coming on its own.
        if self.scene is not None and target_scene == self.scene.key:
            return
        # A refuge always shakes the chase (the safe houses + Mara's cell).
        if target_scene in FOLD_REFUGE_SCENES:
            self._fold_pursuer = None
            return
        # A chaser follows ONLY across a true rift FOLD (a direction-gated
        # pane: the descent rite, the King's tears). Every ORDINARY crossing
        # shakes it now -- a door / ladder / rope, a seamless outdoor passage,
        # a road loop, or any non-fold target (play-notes: pursuit is
        # same-scene + rift folds only; this narrows the old passage /
        # UNDERGROUND / CULTIST_SCENE carry, DESIGN.md §7). The Watcher-curse
        # gaze still seeds on any fold OR passage (_exit_is_fold) -- that is
        # His attention reaching across the wrongness, not a cultist on foot.
        ch = (self.scene.char_object_at(self.player.x, self.player.y)
              if self.scene is not None else None)
        if ch is None or ch not in self.scene.exit_directions:
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

    def _spawn_cultist(self, tag, kind, speed=0.95, gaze_range=180,
                       movement="chaser", name="", at=None, from_pool=False):
        """Plant a cultist. If `at` (x, y) is given and walkable, they enter
        there (the door you came in by -- for reinforcement waves). Else if
        `from_pool` and the scene defines `cult_spawns`, they enter at the
        farthest unoccupied pool point from the player (hand-placed spawn
        anchors). Otherwise at the farthest walkable scene corner. Either way
        they enter from a distance, never on top of you. Returns the NPC, or
        None."""
        scene = self.scene
        best = None
        if at is not None:
            ax = at[0] + random.uniform(-12, 12)
            ay = at[1] + random.uniform(-12, 12)
            if not scene.is_solid_at(ax, ay):
                best = (ax, ay)
        if best is None and from_pool:
            pool = getattr(scene, "cult_spawns", None)
            if pool:
                occ = [(n.x, n.y) for n in scene.npcs
                       if str(getattr(n, "tag", "")).startswith("cult_")
                       and getattr(n, "alive", True)]
                cands = []
                for px, py in pool:
                    if scene.is_solid_at(px, py):
                        continue
                    if any(abs(px - ox) < Scene.TILE * 1.5
                           and abs(py - oy) < Scene.TILE * 1.5
                           for ox, oy in occ):
                        continue          # one cultist per point
                    cands.append((px, py))
                if cands:
                    best = max(cands, key=lambda p: scene.world_dist(
                        p[0], p[1], self.player.x, self.player.y))
        if best is None:
            corners = [
                (4 * Scene.TILE, 4 * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, 4 * Scene.TILE),
                (4 * Scene.TILE, (scene.h - 4) * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, (scene.h - 4) * Scene.TILE),
            ]
            best_d = -1.0
            for sx, sy in corners:
                # jitter like the `at` path above: exact corner points
                # gave every corner-spawned cultist one of only FOUR
                # sprite seeds -- the same mask on every respawn
                sx += random.uniform(-12, 12)
                sy += random.uniform(-12, 12)
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

    def _tick_visibility(self, dt):
        """The visibility meter [0, 1] -- how visible the player is to
        the King in Yellow. Watchers (spawned by a cultist's curse)
        push it up; hiding bleeds it down. While the King hunts, holding
        it pinned at 100% tears a portal he folds through (see
        _tick_king_roam); break the pin and the forming rift collapses.

        Heavy curses tip the balance: enough Watchers out-pace even
        hiding -- the spiral toward a King the player can no longer
        shake."""
        if self.scene is None or self.player is None:
            return
        n_watch = len(self._watchers)
        # A burning flashlight marks you. The cost applies everywhere the
        # beam is lit EXCEPT the safe cellar (DIM_SAFE) -- there the light
        # is a free comfort, your one room to read by. Cover can't hide a
        # lit torch, so the rise lands in both branches.
        lit_rise = (VIS_LIT_RISE
                    if (self._flashlight_lit()
                        and self.scene.key not in DIM_SAFE_SCENES)
                    else 0.0)
        # Cover reads GRADED now (DESIGN.md §12). The gaze term
        # (self._gaze_count) arrives already concealment-weighted from
        # _tick_cultists -- corn scales each watcher's contribution, an
        # enclosed hide zeroes it. Only the enclosed hide keeps the old
        # strong bleed; corn is mobile concealment and drains at the
        # plain idle rate, so sitting in the stalks is no longer a
        # visibility eraser -- just a place the gaze mostly misses.
        if _is_enclosed(self.player):
            self.visibility += dt * (lit_rise - VIS_HIDE_BLEED)
        else:
            rise = (self._gaze_count * VIS_GAZE
                    + getattr(self, "_watcher_gaze", 0.0) * WATCHER_GAZE
                    + lit_rise)
            self.visibility += dt * (rise - VIS_IDLE_DECAY)
        # The being-seen RATE the HUD reads (the faucet): human/cult gaze on
        # you THIS second + a lit torch, concealment-weighted the same way.
        # The King's own gaze is NOT counted here (added to visibility in
        # the roam tick) -- the bar reads the cult puzzle, the King stays felt.
        seen_rate = (self._gaze_count * VIS_GAZE
                     + getattr(self, "_watcher_gaze", 0.0) * WATCHER_GAZE
                     + lit_rise)
        self._being_seen = max(0.0, min(1.0, seen_rate / BEING_SEEN_FULL))
        # One-shot teach (TODO #5): the first time eyes really pile on,
        # name what the notched bar is and what breaks it.
        if (self._being_seen >= 0.5 and self.save
                and not self.save.flag("teach_seen")):
            self.save.set_flag("teach_seen", True)
            self.show_notice("Eyes are on you. The notches read how hard. "
                             "Walls, corn, distance break the line.",
                             duration=3.6)
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
        that arms the King (DESIGN.md §1)."""
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
                                 speed=0.95, gaze_range=180,
                                 at=self._king_anchor)

    def _despawn_king(self):
        """Full teardown of the concrete King NPC: remove him from the scene,
        clear his trail/particle FX, and silence his tone. Shared by the roaming
        sim (player leaves his room / he hops out) and the death sequence."""
        if self._king is not None and self.scene is not None:
            try:
                self.scene.npcs.remove(self._king)
            except ValueError:
                pass
        self._king = None
        reset_king_fx()        # drop his trail/particles so they don't bleed on
        reset_king_unfold_fx() # the UNFOLDING's mask-bond state goes with them
        self.audio.king_tone(False)

    def _apply_curse(self):
        """Open the first Watcher of a wave -- His gaze finding the exposed
        investigator (the ambient trigger in _tick_watchers, and the
        fold-crossing seed). Sets the wave live and spawns the seed; it grows
        + holds in _tick_watchers, and clearing it (_dispel_watcher) lifts it
        and sets the grace before the next. The opening line is a one-time
        teach; the void-sting marks every wave."""
        self.audio.play("void_sting", 0.8)
        if not self._cursed:
            self._cursed = True
            self._watcher_clone_t = self._watcher_spawn_interval()
            # No narrator box on a Watcher opening (play-notes) -- the
            # void-sting + the eye itself are the tell.
            self._spawn_watcher()
        else:
            self.visibility = min(1.0, self.visibility + 0.1)

    def _tick_watchers(self, dt):
        """The WATCHERS -- His gaze made manifest, and the below-3 threat
        (play-notes rework). From WATCHER_WAKE_EV evidence, while the player is
        EXPOSED (in the open, not in cover / a safe room), the domain opens
        Watchers on a timer: WATCHER_GRACE before the FIRST of a wave (and
        after clearing one), then the evidence-scaled interval between the
        rest. Each live Watcher HOLDS the exposed player -- driving visibility
        up in _tick_visibility (`_watcher_gaze`), so ignoring them SNOWBALLS.
        Cover pauses the timer and drops the hold; safe rooms suppress them;
        clearing them all (gaze / axe / shot, _dispel_watcher) sets the grace.
        And the gaze only opens under the open sky or in the deep
        (WATCHER_OPEN_SCENES, 2026-07 ruling): no Watcher ever manifests
        inside a surface building -- step through a door and the wave clears,
        step back out and the grace runs before it re-forms."""
        if self.scene is None or self.player is None:
            return
        # Drop any swept on load/death.
        self._watchers = [w for w in self._watchers if w in self.scene.npcs]
        for w in self._watchers:
            # presentation only: the manifest ramp the amalgam build-out
            # reads (draw-side; the threat states never touch it)
            w._birth = min(1.0, getattr(w, "_birth", 1.0) + dt / 2.2)
        key = self.scene.key
        # The domain watches once the thread is pulled -- never in a safe /
        # King-free room, never inside a surface building, never before the
        # first evidence.
        watching = (key not in KING_FREE_SCENES
                    and key in WATCHER_OPEN_SCENES
                    and self._evidence_count() >= WATCHER_WAKE_EV)
        if not watching:
            if self._watchers:
                self.scene.npcs = [n for n in self.scene.npcs
                                   if getattr(n, "tag", "") != "watcher"]
                self._watchers = []
            self._cursed = False
            self._watcher_clone_t = WATCHER_GRACE
            self._watcher_gaze = 0.0
            return
        if key in DIM_INTERIOR_SCENES:
            # "no light = danger" (TODO #21): in these dark rooms the gaze
            # opens where you stand in the DARK. A light POOL (Scene.lit_at,
            # the same shadow-cover gate) or the flashlight is the cover -- the
            # refuge here is the LIT room, not the building. An enclosed hide
            # (under a desk) still counts as cover too.
            lit = (self._flashlight_lit()
                   or self.scene.lit_at(self.player.x, self.player.y))
            exposed = (not lit) and self.player.hidden is None
        else:
            exposed = self.player.hidden is None
        # A wave carried in from a fold (or across a scene) re-forms its seed.
        if self._cursed and not self._watchers:
            self._spawn_watcher()
            self._watcher_clone_t = self._watcher_spawn_interval()
        # Exposure-gated cadence: the grace before the first of a wave, the
        # evidence-scaled interval between the rest. Cover pauses the timer.
        if exposed and len(self._watchers) < WATCHER_MAX:
            self._watcher_clone_t -= dt
            if self._watcher_clone_t <= 0.0:
                if not self._cursed:
                    self._apply_curse()             # first Watcher of the wave
                else:
                    self._spawn_watcher()            # a clone
                self._watcher_clone_t = self._watcher_spawn_interval()
        # Live Watchers HOLD you while you are exposed -> the active visibility
        # climb (read in _tick_visibility). Any cover drops the hold.
        self._watcher_gaze = float(len(self._watchers)) if exposed else 0.0
        # Staring one down dissolves it (the cure).
        self._tick_watcher_gaze(dt)

    def _watcher_spawn_interval(self):
        """Seconds between Watcher spawns, shaved by evidence (the King floods
        them deep) down to WATCHER_SPAWN_MIN."""
        ev = self._evidence_count()
        return max(WATCHER_SPAWN_MIN,
                   WATCHER_SPAWN_BASE - ev * WATCHER_SPAWN_STEP)

    def _spawn_watcher(self):
        """Manifest one Watcher at a walkable tile a little way off, in a
        random direction around the player. It stands and stares (the
        'watch' movement). A faint breath and a small visibility nudge
        mark the moment it opens its eyes.

        The spawn spot obeys two rules (maintainer, 2026-07): it must be
        DARK (a Watcher only exists in the dark -- `Scene.lit_at` is the
        same gate cover reads), and it must hold LINE OF SIGHT to the
        player (`clear_sight_line`), so one can never open in a sealed
        room or out-of-bounds pocket you cannot answer with your gaze.
        The corollary is the light-security promise: a room with no dark
        spot in view of you cannot open ANYTHING -- a fully lit room is
        secured, and a blackout un-secures it."""
        scene = self.scene
        spot = None
        for _ in range(20):
            ang = random.uniform(0, math.tau)
            r = random.uniform(110, 200)   # closer in (play-notes: hard to see far)
            wx = self.player.x + math.cos(ang) * r
            wy = self.player.y + math.sin(ang) * r
            if (0 < wx < scene.w * Scene.TILE
                    and 0 < wy < scene.h * Scene.TILE
                    and not scene.is_solid_at(wx, wy)
                    and not scene.lit_at(wx, wy)
                    and scene.clear_sight_line(wx, wy,
                                               self.player.x, self.player.y)):
                spot = (wx, wy)
                break
        if spot is None:
            return
        # The shadow FAMILY: some of His gaze manifests as the OG Watcher,
        # some as an AMALGAM -- a seeded assembly of parts, each emerging
        # from its own cut (rendering/amalgam.py). Same behavior end to end
        # (this spawn rule, the hold, every dispel); only the flesh differs.
        kind = "amalgam" if random.random() < AMALGAM_CHANCE else "watcher"
        w = NPC(spot[0], spot[1], "", kind,
                voice="blip_low", portrait="watcher",
                movement="watch", speed=0.0,
                no_prompt=True, solid=False)
        w.tag = "watcher"
        w.dialogue_fn = None
        w.sprite_seed = random.randint(1, 99999)   # the assembly deal
        w._birth = 0.0                             # the staggered build-out
        scene.add_npc(w)
        self._watchers.append(w)
        self.visibility = min(1.0, self.visibility + 0.03)
        self.audio.play("watcher_spawn", 0.5)

    def _tick_watcher_gaze(self, dt):
        """Holding a Watcher in your gaze (SEEING it) dissolves it over
        WATCHER_GAZE_DISPEL seconds -- its eyes are already dark while looked
        at. Look away and the progress bleeds back. 'Seeing it' is the same
        forward sight cone the render uses (keyed to the cursor aim, blocked by
        walls), so if it is visibly in front of you it dispels; the flat view
        falls back to a facing dot-product."""
        p = self.player
        cone = None
        if self._tilt_on() and self.scene is not None:
            from rendering.sight import visible_factor
            aim = self.look.aim
            blk = self.scene.blocks_sight
            cone = lambda w: visible_factor(p.x, p.y, aim, w.x, w.y, blk)
        fdx, fdy = p.facing
        scene = self.scene
        flit = self._flashlight_lit()
        for w in list(self._watchers):
            if cone is not None:
                looking = cone(w) > 0.25
            else:
                pdx, pdy = w.x - p.x, w.y - p.y
                d = math.hypot(pdx, pdy) or 1.0
                looking = ((pdx / d) * fdx + (pdy / d) * fdy) > 0.5 and d < 360
            # LIGHT BURNS a Watcher (TODO #21 "no light = danger"): one standing
            # in a light pool -- or caught in the flashlight beam -- dissolves
            # fast, on top of any gaze. The flashlight is how you clear them,
            # and a bright pool is a place His gaze cannot hold you OR them.
            burn = ((scene is not None and scene.lit_at(w.x, w.y))
                    or (flit and looking))
            gt = getattr(w, "_gaze_dispel_t", 0.0)
            if looking or burn:
                gt += dt * (1.0 + (WATCHER_LIGHT_BURN if burn else 0.0))
                if gt >= WATCHER_GAZE_DISPEL:
                    self._dispel_watcher(w, reason="light" if burn else "gaze")
                    continue
            else:
                gt = max(0.0, gt - dt * 1.5)
            w._gaze_dispel_t = gt
            # presentation only: the dispel FRACTION drives the amalgam's
            # peel (parts retract in reverse as you stare it apart)
            w._gait = min(1.0, gt / WATCHER_GAZE_DISPEL)

    def _dispel_watcher(self, w, reason="gaze"):
        """Dissolve one Watcher. If it was the last one and we're not merely
        being suppressed by a safe room, the curse lifts (you're cured)."""
        if w in self._watchers:
            self._watchers.remove(w)
        if self.scene is not None and w in self.scene.npcs:
            self.scene.npcs.remove(w)
        pan = self.audio.pan_for_world(w.x, self.player.x)
        dmult = self.audio.distance_attenuation(
            w.x, w.y, self.player.x, self.player.y)
        self.audio.play("watcher_dispel", 0.55 * dmult, pan=pan)
        if (self._cursed and not self._watchers and self.scene is not None
                and self.scene.key not in KING_FREE_SCENES):
            self._cursed = False
            self._watcher_clone_t = WATCHER_GRACE   # the breather before the next
            # No narrator box on the last eye closing (play-notes) -- the
            # watcher_dispel sound carries it.

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
        sequence lock). Guarded so it can't re-trigger.

        THE TALK (2026-07, settled with the user): the FIRST time the
        cult ever lays hands on the PI it is a warning, not a capture.
        One freebie per run, spent at whichever grab site fires first
        (surface grab, hide-check struggle, underground contact); every
        later cultist grab is the CAPTURED card."""
        if self._death_kind is not None:
            return
        if kind == "cultist" and self.save is not None:
            if not self.save.flag("cult_talk_given"):
                self._cult_talk()
                return
            # Two-touch (play-notes): the first grab of an encounter shoves the
            # PI free; only a SECOND grab before he reaches a safe zone takes
            # him. The cult captures, it does not kill -- one hold is survivable.
            if self._cult_shrug_off():
                return
        self._death_kind = kind
        self._death_t = 0.0
        self._closure_locked = True
        self.audio.force_silence()
        if kind == "king":
            self.audio.play("void_sting", 0.9)
            self.audio.play("low_pulse", 0.8)
        elif kind == "sheriff":
            self.audio.play("custody_bed", 1.0)
        else:
            self.audio.play("captured_bed", 1.0)

    def _cult_shrug_off(self):
        """The two-touch grab (play-notes). The FIRST grab of an encounter is
        a shove, not the end: the grabbers stagger, the PI tears free on a
        burst of speed with a beat of grace. Returns True (handled -- no
        capture) for that first touch; False on the SECOND, so the capture
        proceeds. The count resets only on reaching a safe zone
        (load_scene_now), so a swarm or a corner still takes you."""
        self._cult_touch_count = getattr(self, "_cult_touch_count", 0) + 1
        if self._cult_touch_count >= 2:
            return False                     # second touch -> the capture
        p = self.player
        if p is None:
            return False
        # Tear free: a panic burst, a beat of grace, and a stagger on every
        # near cultist so the shove reads and the burst has room to run.
        p._burst_t = max(getattr(p, "_burst_t", 0.0), STRUGGLE_BURST_T)
        p.invuln = max(getattr(p, "invuln", 0.0), CULT_SHRUG_INVULN)
        if getattr(p, "hidden", None) is not None:      # pulled from a hide
            p.hidden = None
            if getattr(p, "hide_origin", None) is not None:
                p.x, p.y = p.hide_origin
                p.hide_origin = None
        self._struggle = None
        if self.scene is not None:
            grabbers = list(self.scene.npcs) + list(
                getattr(self.scene, "enemies", []))
            for n in grabbers:
                tag = getattr(n, "tag", "")
                is_cult = (getattr(n, "kind", "") == "cultist"
                           or (isinstance(tag, str)
                               and tag.startswith("cult_")))
                if is_cult and math.hypot(n.x - p.x,
                                          n.y - p.y) < CULT_SHRUG_RANGE:
                    n._stun_t = max(getattr(n, "_stun_t", 0.0), STRUGGLE_STUN)
        self.audio.play("cult_lose", 0.7)
        self.show_notice("Hands on you. You tear free.", duration=2.0)
        return True

    def _cult_talk(self):
        """The one warning (the freebie). The hand comes down, the
        courteous line lands, and they let go: the room stands down and
        a short grace window stops the same hand closing again on the
        next frame. Fires from every grab site via _trigger_death. The
        PI files it as a NOTE (never evidence)."""
        self.save.set_flag("cult_talk_given", True)
        p = self.player
        # If the hands came down on a hide, they pull him out of it.
        if p is not None and getattr(p, "hidden", None) is not None:
            p.hidden = None
            if getattr(p, "hide_origin", None) is not None:
                p.x, p.y = p.hide_origin
                p.hide_origin = None
        self._struggle = None
        # The nearest live cult body does the talking.
        speaker = None
        best = 1e9
        if self.scene is not None and p is not None:
            for n in self.scene.npcs:
                tag = getattr(n, "tag", "")
                if not (isinstance(tag, str) and tag.startswith("cult_")):
                    continue
                if (not getattr(n, "alive", True)
                        or getattr(n, "_is_corpse", False)):
                    continue
                d = math.hypot(n.x - p.x, n.y - p.y)
                if d < best:
                    best, speaker = d, n
            for e in self.scene.enemies:
                if getattr(e, "kind", "") != "cultist":
                    continue
                if not getattr(e, "alive", True):
                    continue
                d = math.hypot(e.x - p.x, e.y - p.y)
                if d < best:
                    best, speaker = d, e
        if speaker is not None and p is not None:
            dx, dy = p.x - speaker.x, p.y - speaker.y
            dd = math.hypot(dx, dy) or 1.0
            speaker.facing = (dx / dd, dy / dd)
        self.audio.play("cult_lock", 0.7)
        self.audio.duck(0.8, depth=0.45)

        def _release():
            # They let go: the room stands down, and a grace window
            # covers the first steps away.
            if p is not None:
                p.invuln = max(getattr(p, "invuln", 0.0), 2.0)
            if self.scene is not None:
                for n in self.scene.npcs:
                    tag = getattr(n, "tag", "")
                    if isinstance(tag, str) and tag.startswith("cult_"):
                        n._cult_state = "scout"
                        n._suspicion = 0.0
                for e in self.scene.enemies:
                    if getattr(e, "kind", "") == "cultist":
                        e._cult_state = "scout"
                        e._suspicion = 0.0
            if speaker is not None:
                speaker._stun_t = max(getattr(speaker, "_stun_t", 0.0), 1.0)
            self._log_note("the_talk", [
                "One of them put hands on me today. Told me to go back to "
                "my room. Told me to run.",
                "Well shit, this town really doesn't have a midwestern "
                "welcome at all.",
            ])
            # The reaction lands a beat later, as the world resumes: a
            # frameless caption, not another box.
            self.dialog.show([
                "[c=dim]Well shit, this town really doesn't have a "
                "midwestern welcome at all.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
        # THE TALK is a close-up TABLEAU (#2b, the tone inversion of the
        # principal seats): the carved mask fills the frame, his hand is on
        # your shoulder, and the locked warning lines land as captions. A PI
        # carrying the revolver can reach for it, and learn how far ahead of
        # him the other hand already is. The release above fires when the
        # close-up lets go, on every path.
        self._open_talk_tableau(_release)

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
