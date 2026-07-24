"""The roaming King in Yellow (KING_PROMPT rework).

The apex, rebuilt from a per-scene spawn-at-visibility-1.0 into ONE persistent,
world-positioned entity. The model, settled in the opening design conversation:

  - IDLE: until the 3-evidence gate he is the regular King at full bloom, far
    down THE road (arrival_road), barely visible by distance, indifferent,
    unreachable. He cannot catch you here. (The idle *render* + the road-grows
    treadmill are a later visual pass; this module owns the behaviour.)
  - SEARCHING: the instant evidence hits the gate he peels off the road and
    roams the surface scene-to-scene, looking for you but not yet locked on. He
    is lucky, not omniscient: he drifts toward where you are with a chance, not
    a certainty, and otherwise wanders.
  - HUNTING: the moment he SEES you (line of sight, not hidden, in range) he
    locks on, visibility climbs fast, and he closes. Reaching you ends the run.
  - Break his sight (cover / a wall) and hunting falls back to SEARCHING; stay
    lost for KING_SEARCH_TIME and searching loosens to a check-one-or-two-rooms
    wander. He NEVER returns to idle once armed.

Movement rules:
  - He travels only his own ground: PASSAGES (outdoor inter-scene seams) and
    FOLDS, never doors/ladders/ropes (those are the player's escape). That set
    is the roam graph below.
  - Never indoors, never a safe room, never the boss arena.
  - In a room he PHASES: walls don't stop him (npc._phase), but he paths the
    floor toward his target so he reads as a predator that ignores architecture,
    not a thing surfacing out of solid wall.

The concrete NPC (the existing `yellow_king` sprite) exists only while he shares
the player's scene; otherwise he is simulated abstractly at scene granularity.
This is the only King; the per-scene spawn-at-vis-1.0 model is gone. The portal
(M2) is built: pinning visibility at 100% tears a rift he folds through.
"""
import math
import random
from collections import deque

from constants import TILE
from entities.npc import NPC
from rendering.sight import los_clear
from systems.config import *        # noqa: F401,F403


# The King's surface adjacency, built once from the scene registry (which
# outdoor scenes connect to which via passages/folds). Module-level so it is
# computed at most once per process, not per frame.
_KING_GRAPH = None


class KingRoamMixin:
    # ---- persistent state ------------------------------------------------
    def _new_roam_king_state(self):
        """The whole roaming-King record. Survives scene loads (like
        visibility); only _reset_run_state wipes it. Kept as ONE dict so the
        per-run-reset audit (tests/smoke) has a single attribute to track."""
        return {
            "armed": False,            # crossed the 3-evidence gate yet?
            "scene": KING_ROAM_START,  # the scene he currently occupies
            "state": "idle",           # idle | searching | hunting | check_nearby
            "search_t": 0.0,           # seconds since he last had eyes on you
            "hop_t": KING_HOP_INTERVAL,    # cooldown between off-camera scene hops
            "leave_t": KING_HOP_INTERVAL,  # cooldown before he gives up your room
            "follow_grace": 0.0,       # beat-behind delay after following you in
            "arm_grace": 0.0,          # "world holds its breath" after arming (ev3)
            "last_seen": None,         # (x, y) where he last saw you, for searching
            "last_surface": None,      # last surface scene you stood in (path goal)
            "enter_at": "far",         # where the body materialises (away from you)
            "pos": None,               # his EXACT (x, y) in his current scene --
                                       # tracked dynamically so a portal shows
                                       # (and you emerge at) the real spot, no
                                       # brittle per-scene presets
        }

    # ---- the idle state (the receding horizon King) ----------------------
    def _tick_idle_king(self):
        """Before the gate, place the idle King a fixed gap NORTH of the player
        on THE road -- a receding horizon render (not a scene entity): running
        up the treadmill never closes on him. Cleared once armed or off-road;
        the renderer reads _idle_king (world x, y) or None."""
        rk = self._roam_king
        tm = getattr(self.scene, "_treadmill", None) if self.scene else None
        if (rk["armed"] or self._king is not None or self.scene is None
                or self.player is None
                or self.scene.key != KING_ROAM_START
                # only once you're ON the looping band (north of its south edge);
                # the car is off screen by then. In the arrival stretch: no King.
                # `self._king is not None` keeps the distant idol from ever
                # showing alongside the concrete King body (no two Kings at once).
                or (tm is not None and self.player.y >= tm[1])):
            self._idle_king = None
            return
        # The receding horizon: he hangs a FIXED GAP north of the player
        # (recomputed each tick), centred on the road. He is always the same
        # distance ahead up the looping band -- distant, untouchable -- and his
        # screen position holds steady as the band scrolls under you.
        self._idle_king = (7 * TILE + TILE // 2,
                           self.player.y - IDLE_KING_GAP)

    def _nearest_walkable(self, scene, x, y, rings=10):
        """Snap (x, y) to the nearest non-solid tile centre in `scene` (spiral
        out). The King PHASES, so his tracked spot can sit inside a wall/building
        -- this keeps the rift's view + the player's emergence on walkable ground
        instead of stranding them in a wall or a hard-to-reach pocket."""
        if not scene.is_solid_at(x, y):
            return (x, y)
        for r in range(1, rings + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    nx = x + dx * TILE
                    ny = y + dy * TILE
                    if (0 <= nx < scene.w * TILE and 0 <= ny < scene.h * TILE
                            and not scene.is_solid_at(nx, ny)):
                        return (nx, ny)
        return None

    def _king_scene_pos(self, scene_key):
        """A real walkable world point in `scene_key` for the King to stand at
        while he's abstract there -- his default spawn, else the centre. Used so
        a portal shows (and you emerge at) an actual spot, not a hand-preset."""
        from scenes import load_scene
        try:
            sc = load_scene(scene_key)
        except Exception:
            return None
        sp = sc.spawns.get("default")
        if sp:
            return (float(sp[0]), float(sp[1]))
        return (sc.w * TILE / 2.0, sc.h * TILE / 2.0)

    # ---- the graph -------------------------------------------------------
    def _king_roam_graph(self):
        """scene -> set(adjacent surface scenes) reachable by a passage/fold.
        Built once by loading each domain scene and reading its exits: an exit
        whose target is also in the domain is a passage/fold (outdoor->outdoor);
        an exit to anything else is a door/ladder into an interior and is left
        out (the player-only escape)."""
        global _KING_GRAPH
        if _KING_GRAPH is not None:
            return _KING_GRAPH
        from scenes import load_scene
        g = {k: set() for k in KING_ROAM_SCENES}
        for k in KING_ROAM_SCENES:
            try:
                sc = load_scene(k)
            except Exception:
                continue
            for target, _spawn in sc.exits.values():
                if target in KING_ROAM_SCENES and target != k:
                    g[k].add(target)
                    g.setdefault(target, set()).add(k)   # passages are two-way
        _KING_GRAPH = g
        return g

    def _king_roam_step_toward(self, start, goal, graph):
        """BFS the roam graph; return the first neighbour of `start` on a
        shortest path to `goal` (None if unreachable / already there)."""
        if start == goal or start not in graph:
            return None
        prev = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for nb in graph.get(cur, ()):
                if nb not in prev:
                    prev[nb] = cur
                    q.append(nb)
        if goal not in prev:
            return None
        node = goal
        while prev[node] != start:
            node = prev[node]
            if node is None:
                return None
        return node

    # ---- the master tick -------------------------------------------------
    def _tick_king_roam(self, dt):
        """Drive the roaming King. Called every world-sim frame from
        Game.step (the sole King tick)."""
        if self.scene is None or self.player is None:
            return
        self._tick_idle_king()
        rk = self._roam_king
        if self.scene.key in KING_ROAM_SCENES:
            rk["last_surface"] = self.scene.key
        # Before the gate: the distant idle idol. A maxed meter still musters a
        # cult wave (the legacy below-gate net), but no King walks yet.
        if not rk["armed"]:
            if self._reinforce_t > 0:
                self._reinforce_t -= dt
            ev = self._evidence_count()
            # One tier before the roam: he TURNS HIS HEAD toward you -- a single
            # telegraph, no movement yet, so the gate is not an ambush
            # (play-notes ramp). Audio gated by the flag; the note dedups.
            if (ev >= KING_TURNS_HEAD_EV and self.save is not None
                    and not self.save.flag("king_turns_head")):
                self.save.set_flag("king_turns_head", True)
                self.audio.play("low_pulse", 0.7)
                self._log_note("the_turning", [
                    "Something at the end of the north road turned to face "
                    "me. It has not moved. It does not need to yet.",
                    "It knows my face. Like a draft off a door left open "
                    "somewhere behind you.",
                ])
            if ev >= KING_GATE_EVIDENCE:
                rk["armed"] = True
                rk["scene"] = KING_ROAM_START
                rk["state"] = "searching"
                rk["search_t"] = 0.0
                rk["hop_t"] = KING_HOP_INTERVAL
                rk["pos"] = self._king_scene_pos(KING_ROAM_START)
                self._idle_king = None     # the idol gives way to the real King
                # The world holds its breath: he stands far and does NOT close
                # for KING_ARM_GRACE -- the window to reach the lodge for the
                # Invitation before the hunt begins (decouples the spike from
                # progression). Fires once (the arm block is one-shot).
                rk["arm_grace"] = KING_ARM_GRACE
                self.audio.play("void_sting", 0.8)
                self.audio.play("low_pulse", 0.7)
                self._log_note("the_breath", [
                    "The road has gone still, all at once. No wind, no "
                    "birds. The whole town holding its breath.",
                    "I have what I came for. I should not be standing in the "
                    "open when it lets that breath go.",
                ])
            else:
                if (self.visibility >= 1.0
                        and self.scene.key not in KING_FREE_SCENES
                        and ev >= CULT_WAKE_EV):
                    self._muster_reinforcements()
                self._king_dread = 0.0
                self.audio.king_tone(False)
                return
        # The grace after arming: he holds far and does not close, but the
        # dread tell still rises so the player feels the countdown (play-notes).
        if rk["arm_grace"] > 0.0:
            rk["arm_grace"] -= dt
            self._king_roam_dread()
            return
        # Armed + past the grace: concrete in the player's scene, abstract
        # everywhere else. A safe room / dark / threshold can never host him.
        co_located = (rk["scene"] == self.scene.key
                      and self.scene.key not in KING_FREE_SCENES)
        if co_located:
            self._king_roam_in_scene(dt)
        else:
            self._king_roam_abstract(dt)
        self._king_roam_dread()
        if self._tick_portal(dt):
            return                    # the player crossed: a transition fired

    # ---- abstract sim (he is in another scene) ---------------------------
    def _king_roam_abstract(self, dt):
        rk = self._roam_king
        if self._king is not None:        # player left his scene: drop the body
            self._despawn_king()
        if rk["state"] == "hunting":
            # He can't have eyes on you from another scene -- losing the room is
            # losing the scent. Drop the hunt to a search (starts the 2-min cool).
            rk["state"] = "searching"
            rk["search_t"] = 0.0
        if rk["state"] == "searching":
            rk["search_t"] += dt
            if rk["search_t"] >= KING_SEARCH_TIME:
                rk["state"] = "check_nearby"
        # While a rift is FORMING he holds where he is (he's tearing it) so the
        # spot it grows at stays the spot he comes through.
        p = getattr(self, "_portal", None)
        if p is not None and not p.get("formed"):
            return
        rk["hop_t"] -= dt
        if rk["hop_t"] > 0:
            return
        loose = rk["state"] == "check_nearby"
        rk["hop_t"] = KING_HOP_INTERVAL * (1.6 if loose else 1.0)
        graph = self._king_roam_graph()
        here = rk["scene"]
        nbrs = sorted(graph.get(here, ()))
        if not nbrs:
            return
        goal = (self.scene.key if self.scene.key in KING_ROAM_SCENES
                else rk.get("last_surface"))
        nxt = None
        if (not loose and goal and goal != here
                and random.random() < KING_HOP_TOWARD):
            nxt = self._king_roam_step_toward(here, goal, graph)
        if nxt is None:
            nxt = random.choice(nbrs)
        rk["scene"] = nxt
        rk["enter_at"] = "far"
        rk["pos"] = self._king_scene_pos(nxt)     # his exact spot in the new room

    # ---- concrete sim (he shares your scene) -----------------------------
    def _king_roam_in_scene(self, dt):
        rk = self._roam_king
        if self._king is None:
            if rk.get("follow_grace", 0.0) > 0:
                rk["follow_grace"] -= dt          # a beat behind after following
                self.audio.king_tone(True, 0.30)
                return
            self._materialize_roam_king()
            if self._king is None:
                return
        king = self._king
        rk["pos"] = (king.x, king.y)               # his EXACT live position
        sees = self._king_sees_player()
        if sees:
            rk["state"] = "hunting"
            rk["search_t"] = 0.0
            rk["last_seen"] = (self.player.x, self.player.y)
            king._hunt_target = None              # chase the live player
            self.visibility = min(1.0, self.visibility + dt * KING_GAZE_RISE)
        else:
            if rk["state"] == "hunting":
                rk["state"] = "searching"         # lost sight: fall back
                rk["search_t"] = 0.0
            self._king_search_target(rk, king)    # drift to last-seen, then wander
            rk["search_t"] += dt
            if rk["state"] == "searching" and rk["search_t"] >= KING_SEARCH_TIME:
                rk["state"] = "check_nearby"
            if rk["state"] == "check_nearby":
                rk["leave_t"] -= dt               # give up the room, hop out
                if rk["leave_t"] <= 0:
                    self._king_leave_scene()
                    return
        # Proximity tone + the catch (contact, unhidden, after the eruption grace).
        d = math.hypot(king.x - self.player.x, king.y - self.player.y)
        prox = max(0.0, min(1.0, 1.0 - (d - KING_THREAT_NEAR) /
                            (KING_THREAT_FAR - KING_THREAT_NEAR)))
        self.audio.king_tone(True, 0.28 + 0.6 * prox)
        if (sees and self.player.hidden is None and self.player.invuln <= 0
                and d < KING_CATCH_DIST
                and getattr(king, "_birth", 1.0) >= 1.0):
            self._trigger_death("king")

    def _king_sees_player(self):
        """True if the King currently has eyes on the player: not hidden, within
        KING_SEE_RANGE, and no wall between them."""
        king = self._king
        if king is None or self.player.hidden is not None:
            return False
        d = math.hypot(king.x - self.player.x, king.y - self.player.y)
        if d > KING_SEE_RANGE:
            return False
        return los_clear(king.x, king.y, self.player.x, self.player.y,
                         self.scene.blocks_sight)

    def _king_search_target(self, rk, king):
        """While searching in the room, steer toward where he last saw you;
        once he reaches that and finds nothing, wander a far point."""
        ls = rk.get("last_seen")
        if ls is not None:
            if math.hypot(king.x - ls[0], king.y - ls[1]) > TILE * 1.5:
                king._hunt_target = ls
                return
            rk["last_seen"] = None                # reached it: nothing there
        wt = getattr(king, "_wander_target", None)
        if wt is None or math.hypot(king.x - wt[0], king.y - wt[1]) < TILE:
            king._wander_target = self._king_far_spot() or (king.x, king.y)
        king._hunt_target = king._wander_target

    # ---- materialise / despawn / hop -------------------------------------
    def _materialize_roam_king(self):
        """Bring the body into the player's scene at a point AWAY from them (and
        from the door), so he never appears on top of the player. After a portal
        he steps out of the rift instead (enter_pos)."""
        spot = self._roam_king.pop("enter_pos", None) or self._king_far_spot()
        if spot is None:
            return
        # Never stack a second body: clear any stray King NPC + the distant idol
        # before planting the one true King (guards every two-Kings path).
        self.scene.npcs = [n for n in self.scene.npcs
                           if getattr(n, "sprite_kind", "") != "yellow_king"]
        self._idle_king = None
        king = NPC(spot[0], spot[1], "", "yellow_king",
                   movement="chaser", speed=KING_ROAM_SPEED,
                   no_prompt=True, solid=False)
        king.tag = "king"
        king.dialogue_fn = None
        king._birth = 0.0          # eruption grace (renderer + catch read it)
        king._gait = 0.0
        king._phase = True         # walls don't stop him
        self.scene.add_npc(king)
        self._king = king
        self._roam_king["pos"] = (king.x, king.y)
        self.audio.play("void_sting", 0.7)
        self._roam_king["enter_at"] = "far"

    def _king_leave_scene(self):
        """In check-nearby he gives up your room and drifts one scene out."""
        rk = self._roam_king
        graph = self._king_roam_graph()
        nbrs = sorted(graph.get(self.scene.key, ()))
        self._despawn_king()
        if nbrs:
            rk["scene"] = random.choice(nbrs)
        rk["leave_t"] = KING_HOP_INTERVAL
        rk["enter_at"] = "far"

    def _king_far_spot(self):
        """The farthest walkable point from the player among the scene's
        corners + edge mids -- 'a point away from the door' -- but never on
        top of an EXIT: he must not re-form blocking the way the player just
        came through or is about to leave by (play-notes)."""
        scene = self.scene
        cands = [(4, 4), (scene.w - 4, 4), (4, scene.h - 4),
                 (scene.w - 4, scene.h - 4),
                 (scene.w // 2, 4), (scene.w // 2, scene.h - 4),
                 (4, scene.h // 2), (scene.w - 4, scene.h // 2)]
        # Exit tile centres, so a candidate sitting on a door is penalised.
        exits_px = []
        exit_chars = set(getattr(scene, "exits", {}).keys())
        if exit_chars:
            for ty, row in enumerate(scene.objects):
                for tx, ch in enumerate(row):
                    if ch in exit_chars:
                        exits_px.append((tx * TILE + TILE // 2,
                                         ty * TILE + TILE // 2))
        best, bestd = None, -1.0
        for tx, ty in cands:
            sx, sy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
            if scene.is_solid_at(sx, sy):
                continue
            d = math.hypot(sx - self.player.x, sy - self.player.y)
            near_exit = min((math.hypot(sx - ex, sy - ey)
                             for ex, ey in exits_px), default=1e9)
            # Heavy penalty for forming within ~3 tiles of a door, so an
            # exit-corner is chosen only if nothing else is walkable.
            if near_exit < 3 * TILE:
                d -= 5000.0
            if d > bestd:
                bestd, best = d, (sx, sy)
        return best

    # ---- following the player through an exit -----------------------------
    def _note_king_follow(self, exit_data):
        """Called the instant the player takes an exit, before the swap. A King
        concretely in this room, hunting or searching, FOLLOWS through his own
        ground (a passage / fold to another surface scene) and re-forms a beat
        behind on the far side. A door / ladder / rope (target outside the roam
        domain) is the player's escape -- he stays put."""
        rk = self._roam_king
        if not rk["armed"] or self._king is None:
            return
        if rk["state"] not in ("hunting", "searching"):
            return
        target = exit_data[0]
        if target in KING_ROAM_SCENES and target != self.scene.key:
            rk["scene"] = target
            rk["enter_at"] = "far"
            rk["follow_grace"] = FOLD_PURSUE_DELAY

    # ---- the dread tell (one room away) ----------------------------------
    def _king_roam_dread(self):
        """Set _king_dread (read by the ashfall + audio): full when he shares
        your room, a moderate tell when he is exactly one room away (a low tone
        through the wall + thickening ashfall), nothing otherwise."""
        rk = self._roam_king
        if not rk["armed"]:
            self._king_dread = 0.0
            return
        if rk["scene"] == self.scene.key:
            self._king_dread = 1.0            # in the room: tone set in-scene
            return
        graph = self._king_roam_graph()
        if self.scene.key in graph.get(rk["scene"], ()):
            self._king_dread = 0.6            # one room away
            self.audio.king_tone(True, 0.16)
        else:
            self._king_dread = 0.0
            self.audio.king_tone(False)

    # ---- the portal (M2): pin 100% and he folds in ------------------------
    def _tick_portal(self, dt):
        """The rift. Pin visibility at 100% (while he is NOT already in your
        room) and a rift OPENS at once at the spot he'll come through, then GROWS
        over PORTAL_CHARGE_TIME as a visible warning -- you watch it tear and
        him loom through it. Break 100% before it completes and it COLLAPSES.
        When it finishes he folds through; from then on stepping into the rift
        jukes you to the room he just left (one-way; it shuts on the cross).
        Returns True if a crossing transition fired."""
        rk = self._roam_king
        if not rk["armed"]:
            self._portal = None
            self._portal_charge_t = 0.0
            return False
        p = self._portal
        # A FORMED rift (he has come through): hold it; check the juke.
        if p is not None and p.get("formed"):
            d = math.hypot(p["x"] - self.player.x, p["y"] - self.player.y)
            if self.player.hidden is None and d < PORTAL_CROSS_DIST:
                tgt, spawn = p["target"], p["spawn"]
                tpos = p.get("target_pos")
                self._portal = None          # shuts the instant you cross
                self._portal_charge_t = 0.0
                # The crossing is deliberately NOTHING -- no sting, no fade,
                # no facing yank. The frame was the spectacle; stepping
                # through is just walking (cross_fold keeps the stride and
                # the screen position through the swap).
                self.cross_fold(tgt, spawn, dest_pos=tpos)
                return True
            return False
        # A FORMING rift (charging): grow it while pinned, collapse if you break
        # 100% (or step into his room / a refuge) before it completes.
        can = (rk["scene"] != self.scene.key
               and self.scene.key not in KING_FREE_SCENES
               and self.scene.key != "clearing")
        if can and self.visibility >= PORTAL_PIN_VIS:
            if p is None:
                self._open_forming_portal()
                p = self._portal
                if p is None:
                    return False
            self._portal_charge_t += dt
            p["charge"] = max(0.0, min(1.0,
                                       self._portal_charge_t / PORTAL_CHARGE_TIME))
            # The forming rift thickens the air as it grows (a felt warning).
            self._king_dread = max(self._king_dread, 0.4 + 0.6 * p["charge"])
            if p["charge"] >= 1.0:
                self._fold_king_through()
        elif p is not None and not p.get("formed"):
            self._portal = None              # collapsed unformed: the relief
            self._portal_charge_t = 0.0
        else:
            self._portal_charge_t = 0.0
        return False

    def _open_forming_portal(self):
        """Tear the rift open (charge 0) at a spot away from the player, pinned
        to the room + EXACT spot the King is in NOW, so where it grows is where
        he'll come through. He does not cross until it completes."""
        rk = self._roam_king
        spot = self._king_far_spot()
        if spot is None:
            self._portal_charge_t = 0.0
            return
        from scenes import load_scene
        try:
            tgt_scene = load_scene(rk["scene"])
        except Exception:
            tgt_scene = None
        tpos = rk.get("pos")
        if not tpos:
            sp = tgt_scene.spawns.get("default") if tgt_scene else None
            tpos = (float(sp[0]), float(sp[1])) if sp else (
                (tgt_scene.w * TILE / 2.0, tgt_scene.h * TILE / 2.0)
                if tgt_scene else (0.0, 0.0))
        if tgt_scene is not None:               # he phases: snap to walkable
            tpos = self._nearest_walkable(tgt_scene, tpos[0], tpos[1]) or tpos
        anchor = (int(tpos[0] // TILE), int(tpos[1] // TILE))
        # The pane's orientation is FIXED at tear time: it stands across the
        # line to the player (he tears it facing you), and from then on it is
        # an object in the world you can circle, not a billboard that swivels.
        pdx = self.player.x - spot[0]
        pdy = self.player.y - spot[1]
        pln = math.hypot(pdx, pdy) or 1.0
        self._portal = {
            "x": spot[0], "y": spot[1],
            "target": rk["scene"], "spawn": "default", "target_pos": tpos,
            "_scene": tgt_scene, "anchor": anchor, "charge": 0.0, "formed": False,
            "seam_dir": (-pdy / pln, pdx / pln),
        }
        self.audio.play("low_pulse", 0.6)
        self.show_notice("The air begins to tear. Get out of sight.",
                         duration=3.0)

    def _fold_king_through(self):
        """The forming rift completes: the King steps through into your room and
        hunts. The room he LEAVES (portal['target']) is your one-way escape."""
        rk = self._roam_king
        p = self._portal
        p["formed"] = True
        p["charge"] = 1.0
        self._portal_charge_t = 0.0
        spot = (p["x"], p["y"])
        rk["scene"] = self.scene.key
        rk["state"] = "hunting"
        rk["last_seen"] = (self.player.x, self.player.y)
        rk["enter_pos"] = spot
        rk["pos"] = spot
        rk["follow_grace"] = PORTAL_EMERGE_GRACE
        self.audio.play("void_sting", 0.9)
        self.show_notice("The air tears open. He is coming through.",
                         duration=3.0)
