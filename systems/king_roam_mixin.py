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
All of this is gated behind config.KING_ROAM; flip it False and the legacy King
(ThreatMixin._tick_king) runs unchanged. Portals are the next milestone.
"""
import math
import random
from collections import deque

from constants import TILE
from entities.npc import NPC
from rendering.sprites import reset_king_fx
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
            "last_seen": None,         # (x, y) where he last saw you, for searching
            "last_surface": None,      # last surface scene you stood in (path goal)
            "enter_at": "far",         # where the body materialises (away from you)
        }

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
        """Drive the roaming King. Called from Game.step in place of
        _tick_king when KING_ROAM is set."""
        if self.scene is None or self.player is None:
            return
        rk = self._roam_king
        if self.scene.key in KING_ROAM_SCENES:
            rk["last_surface"] = self.scene.key
        # Before the gate: the distant idle idol. A maxed meter still musters a
        # cult wave (the legacy below-gate net), but no King walks yet.
        if not rk["armed"]:
            if self._reinforce_t > 0:
                self._reinforce_t -= dt
            if self._evidence_count() >= KING_GATE_EVIDENCE:
                rk["armed"] = True
                rk["scene"] = KING_ROAM_START
                rk["state"] = "searching"
                rk["search_t"] = 0.0
                rk["hop_t"] = KING_HOP_INTERVAL
            else:
                if (self.visibility >= 1.0
                        and self.scene.key not in KING_FREE_SCENES):
                    self._muster_reinforcements()
                self._king_dread = 0.0
                self.audio.king_tone(False)
                return
        # Armed: concrete in the player's scene, abstract everywhere else. A
        # safe room / dark / threshold can never host him.
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
            self._despawn_roam_king()
        if rk["state"] == "searching":
            rk["search_t"] += dt
            if rk["search_t"] >= KING_SEARCH_TIME:
                rk["state"] = "check_nearby"
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
        self.audio.play("void_sting", 0.7)
        self._roam_king["enter_at"] = "far"

    def _despawn_roam_king(self):
        if self._king is not None and self.scene is not None:
            try:
                self.scene.npcs.remove(self._king)
            except ValueError:
                pass
        self._king = None
        reset_king_fx()
        self.audio.king_tone(False)

    def _king_leave_scene(self):
        """In check-nearby he gives up your room and drifts one scene out."""
        rk = self._roam_king
        graph = self._king_roam_graph()
        nbrs = sorted(graph.get(self.scene.key, ()))
        self._despawn_roam_king()
        if nbrs:
            rk["scene"] = random.choice(nbrs)
        rk["leave_t"] = KING_HOP_INTERVAL
        rk["enter_at"] = "far"

    def _king_far_spot(self):
        """The farthest walkable point from the player among the scene's
        corners + edge mids -- 'a point away from the door'."""
        scene = self.scene
        cands = [(4, 4), (scene.w - 4, 4), (4, scene.h - 4),
                 (scene.w - 4, scene.h - 4),
                 (scene.w // 2, 4), (scene.w // 2, scene.h - 4),
                 (4, scene.h // 2), (scene.w - 4, scene.h // 2)]
        best, bestd = None, -1.0
        for tx, ty in cands:
            sx, sy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
            if scene.is_solid_at(sx, sy):
                continue
            d = math.hypot(sx - self.player.x, sy - self.player.y)
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
        if not KING_ROAM:
            return
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
        """The rift. Pin visibility at 100% for PORTAL_CHARGE_TIME (while he is
        NOT already in your room) and he tears a portal to wherever he stands
        and folds through. Break 100% during the charge and it collapses. Once
        formed, stepping into it jukes you to the room he just left (one-way for
        him); it shuts on the cross. Returns True if a crossing transition
        fired (the caller must then stop touching the old scene)."""
        rk = self._roam_king
        if not rk["armed"]:
            self._portal = None
            self._portal_charge_t = 0.0
            return False
        # Formed: hold it; check for the player stepping through (the juke).
        if self._portal is not None:
            d = math.hypot(self._portal["x"] - self.player.x,
                           self._portal["y"] - self.player.y)
            if self.player.hidden is None and d < PORTAL_CROSS_DIST:
                tgt, spawn = self._portal["target"], self._portal["spawn"]
                self._portal = None          # shuts the instant you cross
                self._portal_charge_t = 0.0
                self.audio.play("void_sting", 0.7)
                self.begin_transition(tgt, spawn)
                return True
            return False
        # Not formed. He can only tear in from ELSEWHERE -- never into a room he
        # already stands in, a refuge, or the boss arena.
        if (rk["scene"] == self.scene.key
                or self.scene.key in KING_FREE_SCENES
                or self.scene.key == "void_boss"):
            self._portal_charge_t = 0.0
            return False
        if self.visibility >= PORTAL_PIN_VIS:
            if self._portal_charge_t == 0.0:
                self.show_notice("The air begins to tear. Get out of sight.",
                                 duration=3.0)
            self._portal_charge_t += dt
            if self._portal_charge_t >= PORTAL_CHARGE_TIME:
                self._tear_portal()
        else:
            self._portal_charge_t = 0.0      # broke 100%: it collapses unformed
        return False

    def _tear_portal(self):
        """Open the rift at a point away from the player, connected to the room
        the King is in, and fold him through to hunt."""
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
        spawn = tgt_scene.spawns.get("default") if tgt_scene else None
        if spawn:
            anchor = (int(spawn[0] // TILE), int(spawn[1] // TILE))
        elif tgt_scene:
            anchor = (tgt_scene.w // 2, tgt_scene.h // 2)
        else:
            anchor = (0, 0)
        self._portal = {
            "x": spot[0], "y": spot[1],
            "target": rk["scene"], "spawn": "default",
            "_scene": tgt_scene, "anchor": anchor, "charge": 1.0,
        }
        self._portal_charge_t = 0.0
        # He folds through to your room and comes for you. The room he LEAVES
        # (portal["target"]) is your escape; he stays on this side.
        rk["scene"] = self.scene.key
        rk["state"] = "hunting"
        rk["last_seen"] = (self.player.x, self.player.y)
        rk["enter_pos"] = spot
        rk["follow_grace"] = PORTAL_EMERGE_GRACE
        self.audio.play("void_sting", 0.9)
        self.show_notice("The air tears open. He is coming through.",
                         duration=3.0)
