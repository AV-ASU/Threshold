"""THRESHOLD infestation -- the world rotting as the case is understood.

The evidence-driven decay pass (decals, local convert/mutate, the hunting
sheriff) and the airborne ashfall overlay, extracted from systems/game.py as
an InfestationMixin on the Game class. The mutated/converted/corpse dialogue
helpers travel with it (module-level; _corpse_examine is re-imported by
game.py for _make_corpse). No behavior change; tuning lives in systems.config.
"""
import math
import random

import pygame

from constants import TILE, SCREEN_W, SCREEN_H
from entities.npc import NPC
from entities.decoration import Decoration
from systems.config import *        # noqa: F401,F403


def _corpse_examine(game, npc):
    """E on a local you killed. A flat, dim line -- no absolution, just
    the fact of it lying there. Varies a little on repeat reads."""
    n = game.save.arg("corpse_reads", 0) + 1
    game.save.set_arg("corpse_reads", n)
    name = getattr(npc, "name", "A body")
    if n == 1:
        lines = [f"[c=dim]{name}. Face-down where the round put them. "
                 f"You did this.[/c]"]
    else:
        lines = ["[c=dim]Still here. The cold won't let it keep, and won't "
                 "let it go.[/c]"]
    game.dialog.show(lines, speaker="", voice="blip_soft", portrait="narrator")


def _converted_local_dialogue(game, npc):
    """A local who has made their peace and joined. They no longer answer
    as themselves -- they turn toward you and speak with the others'
    mouth. A flat, patient line; no name. Mrs. Calder is the one bespoke
    case: her place-setting thread (the guest she could never name) pays
    off here -- she has stopped waiting. The guest is never named (1b);
    the player draws the line themselves."""
    if getattr(npc, "name", "") == "Mrs. Calder":
        game.dialog.show([
            "[c=dim]She turns toward you, unhurried. The face is Mrs. "
            "Calder's. The voice underneath it is not.[/c]",
            "\"I cleared the table this morning. All that setting and "
            "waiting. There was no need.\"",
            "[c=dim]\"He was never going to come by the road.\"[/c]",
            "[c=dim]She smiles past you, toward the well.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if hasattr(game, "_log_note"):
            game._log_note("calder_table", [
                "Mrs. Calder cleared the extra place. Months of laying it "
                "for a guest she couldn't name, and the day she stopped, "
                "she looked relieved.",
                "I keep starting the thought of who the plate was for. I "
                "keep not finishing it.",
            ])
        return
    lines = [
        "[c=dim]They turn toward you, unhurried. The face is the one you "
        "knew. The voice underneath it is not.[/c]",
        "[c=dim]\"It's easier once you stop trying the doors.\"[/c]",
    ]
    game.dialog.show(lines, speaker="", voice="blip_soft", portrait="narrator")


# Mutated resisters: their flesh has turned, but they talk to you as if
# nothing has. The horror is the GAP -- a flat, mundane, domestic line
# delivered from a face that is now a wound. No cosmic-poetry; they report
# small specifics and don't acknowledge what they've become.
INFEST_MUTATE_LINES = {
    "Hettie": [
        "Truck still comes Thursdays. I unload it myself now.",
        "The driver won't get out of the cab anymore. That's all right. I "
        "manage the crates.",
        "[c=dim]Don't mind me. I've a customer face on. You get used to "
        "putting it on.[/c]",
    ],
    "the Tisdale boy": [
        "Mom set my place at supper. I sat down for it.",
        "[c=dim]It falls right through. I keep trying. She doesn't say "
        "anything.[/c]",
        "I can still talk. Listen. I sound just the same.",
    ],
    "Garrick": [
        "I still know everyone comes up this road. Don't need to look.",
        "[c=dim]Saw you coming a long way off. Didn't need eyes for it.[/c]",
        "You'll want to keep moving, son. I'd point you the way, but my "
        "arm doesn't.",
    ],
    "Old Pell": [
        "Crossed off the 14th this morning. It was already crossed.",
        "[c=dim]So I did it again, over the top. Mine's the heavier line. "
        "You can tell.[/c]",
    ],
}


def _mutated_local_dialogue(game, npc):
    """A resister whose flesh has turned. They speak to you flatly, about
    small ordinary things, from a face that is now a wound -- and never
    acknowledge it. The portrait shows their bespoke infested form."""
    name = getattr(npc, "name", "")
    lines = INFEST_MUTATE_LINES.get(name, [
        "[c=dim]They answer something ordinary, in their own voice. They "
        "do not seem to know what has happened to their face.[/c]",
    ])
    game.dialog.show(lines, speaker=name,
                     voice=getattr(npc, "voice", "blip_low"),
                     portrait=getattr(npc, "portrait", None),
                     infested=True)


class InfestationMixin:
    # ---- the Moths (the King's heralds; MOTH_* config) ----------------
    def _spawn_moths(self):
        """Seed this scene's moths on load (scene-local, rebuilt like
        everything else). Count = evidence (capped) on any open surface
        scene, plus a retinue wherever the King himself currently is --
        including the idle road King, so the arrival road drifts with
        them from the first hour."""
        sc = self.scene
        if sc is None:
            return
        sc._moths = []
        if sc.key not in MOTH_SCENES or sc.key in SAFE_SCENES:
            return
        n = min(MOTH_COUNT_CAP, self._evidence_count())
        rk = getattr(self, "_roam_king", None)
        if rk is not None and rk.get("scene") == sc.key:
            n += MOTH_KING_RETINUE
        if n <= 0:
            return
        rng = random.Random((sum(map(ord, sc.key)) * 131071) ^ 0x5A17)
        px = self.player.x if self.player else sc.w * TILE // 2
        py = self.player.y if self.player else sc.h * TILE // 2
        placed = 0
        for _ in range(n * 30):
            if placed >= n:
                break
            x = rng.uniform(2 * TILE, (sc.w - 2) * TILE)
            y = rng.uniform(2 * TILE, (sc.h - 2) * TILE)
            if sc.is_solid_at(x, y):
                continue
            if math.hypot(x - px, y - py) < MOTH_RADIUS * 2.2:
                continue          # never born already on top of you
            sc._moths.append({
                "x": x, "y": y, "t": rng.uniform(0.0, 6.28),
                "seed": placed * 3 + 1, "state": "drift",
                "kt": 0.0, "ft": 0.0, "wt": 0.0,
                "wx": x, "wy": y, "spread": 0.0, "glow": 0.12,
            })
            placed += 1

    def _tick_moths(self, dt):
        """Drift, kindle, flare. Runs in the threat block (freezes with
        the world). The flare is an ALARM, not an attack: the loud noise
        converges the cult, visibility spikes, and the moth is spent."""
        sc = self.scene
        moths = getattr(sc, "_moths", None) if sc is not None else None
        if not moths:
            return
        p = self.player
        if p is None:
            return
        for m in list(moths):
            m["t"] += dt
            if m["state"] == "flare":
                m["ft"] -= dt
                m["spread"] = 1.0
                m["glow"] = 1.0
                if m["ft"] <= 0.0:
                    moths.remove(m)
                continue
            d = sc.world_dist(m["x"], m["y"], p.x, p.y)
            # the axe pops it quietly (the reward for darting in);
            # a round pops it from range (the shot's own noise applies)
            popped = (p.melee_swing_t > 0 and d < 46)
            if not popped:
                for pr in sc.projectiles:
                    if (pr.alive and sc.world_dist(pr.x, pr.y,
                                                   m["x"], m["y"]) < 14):
                        pr.alive = False
                        pr.hit = True
                        popped = True
                        break
            if popped:
                moths.remove(m)
                self.audio.play("hit", 0.5)
                self.audio.play("bump", 0.4)
                sc.emit_noise(m["x"], m["y"], 0.25, kind="moth_pop")
                continue
            if m["state"] == "drift":
                m["wt"] -= dt
                if (m["wt"] <= 0.0
                        or math.hypot(m["wx"] - m["x"],
                                      m["wy"] - m["y"]) < 12):
                    m["wt"] = random.uniform(2.5, 5.5)
                    if random.random() < MOTH_SEEK_BIAS:
                        ang = random.uniform(0, 6.28)
                        r = random.uniform(70, 170)
                        m["wx"] = p.x + math.cos(ang) * r
                        m["wy"] = p.y + math.sin(ang) * r
                    else:
                        m["wx"] = m["x"] + random.uniform(-260, 260)
                        m["wy"] = m["y"] + random.uniform(-260, 260)
                    m["wx"] = max(TILE, min((sc.w - 1) * TILE, m["wx"]))
                    m["wy"] = max(TILE, min((sc.h - 1) * TILE, m["wy"]))
                dx = m["wx"] - m["x"]
                dy = m["wy"] - m["y"]
                dl = math.hypot(dx, dy) or 1.0
                m["x"] += dx / dl * MOTH_SPEED * dt
                m["y"] += dy / dl * MOTH_SPEED * dt
                m["spread"] = max(0.0, m["spread"] - dt * 1.6)
                m["glow"] = max(0.12, m["glow"] - dt * 0.8)
                if d < MOTH_RADIUS and p.hidden is None:
                    m["state"] = "kindle"
                    m["kt"] = 0.0
                    self.audio.play("low_pulse", 0.5)
            else:                                     # kindle
                if d > MOTH_RADIUS * 1.25 or p.hidden is not None:
                    m["state"] = "drift"              # backed out in time
                    m["wt"] = 0.0
                    continue
                m["kt"] += dt
                f = min(1.0, m["kt"] / MOTH_KINDLE)
                m["spread"] = 0.5 * f
                m["glow"] = 0.12 + 0.88 * f
                if m["kt"] >= MOTH_KINDLE:
                    m["state"] = "flare"
                    m["ft"] = MOTH_FLARE_DUR
                    sc.emit_noise(m["x"], m["y"], 1.0,
                                  kind="moth_flare", reach=MOTH_REACH)
                    if self.visibility < 0.90:
                        self.visibility = min(
                            0.90, self.visibility + MOTH_VIS_SPIKE)
                    self.audio.play("void_sting", 0.75)
                    self.audio.play("low_pulse", 0.6)
                    self._log_moth_note()

    def _log_moth_note(self):
        """The PI's first-flare case note. A NOTE, never evidence (the
        King-gate must not move)."""
        if self.save is None or self.save.flag("moth_note_seen"):
            return
        self.save.set_flag("moth_note_seen", True)
        notes = self.save.arg("notes", [])
        if isinstance(notes, list) and not any(
                isinstance(e, dict) and e.get("name") == "the_moths"
                for e in notes):
            notes.append({"name": "the_moths", "lines": [
                "Something hanging in the air out past the fences. Folded "
                "up like a dead spider, drifting. I took it for a rag on "
                "the wind until it turned against the wind.",
                "I got close and it opened. Lit up gold and screamed, and "
                "every hooded thing in earshot turned my way at once. Then "
                "it was not there anymore.",
                "A moth, then. A moth that works for whatever owns this "
                "town. Keep clear of them or kill them quiet.",
            ]})
            self.save.set_arg("notes", notes)
            if hasattr(self, "_flash_notebook"):
                self._flash_notebook()

    # ---- Infestation -------------------------------------------------
    def _infest_stage(self):
        """Surface infestation stage 0..3, front-loaded to peak as the
        player commits underground at 3 evidence. Monotonic with the
        evidence count (knowing rots the world, and you can't un-know)."""
        return min(3, self._evidence_count())

    def _ashfall_target(self):
        """How many ash motes the air should hold right now (NARRATIVE 4b).
        Zero on the Threshold (the still eye of it) and in safe rooms before
        stage 3; otherwise stage-driven, thicker underground (the source)."""
        if self.scene is None:
            return 0
        key = self.scene.key
        if key == "threshold":
            return 0          # never on the Threshold (1b)
        stage = self._infest_stage()
        if key in SAFE_SCENES and stage < 3:
            return 0          # safe rooms stay clean until it claims them too
        n = ASHFALL_BY_STAGE.get(stage, 0)
        if key in UNDERGROUND_SCENES:
            n = int(n * ASHFALL_SOURCE_MUL) or (1 if stage == 0 else 0)
        # The roaming King's approach thickens the air: a tell of His nearness
        # that builds as he closes (full in your room, partial one room away).
        n += int(getattr(self, "_king_dread", 0.0) * KING_DREAD_ASH)
        return min(ASHFALL_MAX, n)

    def _spawn_ash_mote(self, seeded_y=False):
        """One ash mote in screen space. seeded_y scatters it up the whole
        screen (initial fill); otherwise it starts just above the top edge."""
        depth = random.random()    # 0 far/slow/faint .. 1 near/fast/bright
        return {
            "x": random.uniform(-20, SCREEN_W + 20),
            "y": random.uniform(0, SCREEN_H) if seeded_y else random.uniform(-30, -4),
            "vy": ASHFALL_FALL_MIN + depth * (ASHFALL_FALL_MAX - ASHFALL_FALL_MIN),
            "ph": random.uniform(0, math.tau),
            "sz": 1 if depth < 0.6 else 2,
            "a": int(40 + depth * 92),
        }

    def _tick_ashfall(self, dt):
        """Ease the live mote field toward its stage target and drift it.
        Pure screen-space atmosphere -- no world state, runs behind modals."""
        parts = self._ashfall_parts
        target = self._ashfall_target()
        # Grow/shrink toward the target a few motes per frame so the air
        # thickens and thins smoothly as evidence climbs / scenes change.
        room = ASHFALL_GROW * dt
        if len(parts) < target:
            for _ in range(min(target - len(parts), max(1, int(room)))):
                parts.append(self._spawn_ash_mote(seeded_y=not parts))
        elif len(parts) > target:
            del parts[target:]
        if not parts:
            return
        t = pygame.time.get_ticks() / 1000.0
        for p in parts:
            p["y"] += p["vy"] * dt
            p["x"] += (ASHFALL_WIND + math.sin(t * 0.7 + p["ph"]) * ASHFALL_SWAY) * dt
            if p["y"] > SCREEN_H + 4:
                # recycle off the top with a fresh sideways offset
                p["y"] = random.uniform(-30, -4)
                p["x"] = random.uniform(-20, SCREEN_W + 20)
            elif p["x"] > SCREEN_W + 20:
                p["x"] -= SCREEN_W + 40
            elif p["x"] < -20:
                p["x"] += SCREEN_W + 40

    def _apply_infestation(self):
        """Re-derive the world's rot for the freshly-loaded scene from the
        evidence count. Scenes rebuild every load, so this is deterministic
        and additive each time -- never accumulates. Runs after on_enter so
        it can transform the live locals in place."""
        if self.scene is None:
            return
        key = self.scene.key
        surface_stage = self._infest_stage()
        # Stage transition cue: the world rots one step further. Fires
        # on the scene load that lands AFTER an evidence cross (so the
        # audio aligns with the visible decal/ashfall change, not with
        # the case-file beat itself, which has its own chime). Tracked
        # on the Game instance; reset to 0 by _reset_run_state.
        last = getattr(self, "_last_infest_stage", 0)
        if surface_stage > last:
            self._last_infest_stage = surface_stage
            self.audio.play("infest_throb", 0.80)
            self.audio.duck(1.6, depth=0.40)
        underground = key in UNDERGROUND_SCENES
        if underground:
            # Wrong from the first rung: a baseline even at 0 evidence,
            # deepening on the FULL evidence count.
            self._infest_decals(max(1, self._evidence_count()), underground=True)
        elif surface_stage > 0:
            self._infest_decals(surface_stage, underground=False)
        # Locals turn (convert) or rot (mutate) on the surface.
        if surface_stage > 0:
            self._infest_locals(surface_stage)
        # Sheriff Vane's office becomes a unique threat at stage 3.
        if surface_stage >= 3 and key == "fisherman_cottage":
            self._spawn_hunting_sheriff()
        # The general store from stage 2: one of them eats at Hettie's
        # counter, calm as a lunch hour, while the shelves behind it stand
        # empty (food scarcity, NARRATIVE 8 -- where the town's food goes).
        # Same ambient contract as the depths diggers: idle, NO tag, so the
        # gaze tick never counts it. Pure tableau; it does not look up.
        if surface_stage >= 2 and key == "shop":
            self._spawn_counter_eater()
        # The AIR rots too: schedule the scene's ambient one-shot
        # layer, escalating with the stage.
        self._apply_ambient_air(surface_stage)

    def _apply_ambient_air(self, stage):
        """Schedule the freshly-loaded scene's recurring ambient
        one-shots (Scene.add_ambient). Two ideas stacked:

        LIVING HOUSE -- every wooden interior (music == "home")
        carries a quiet joist creak + a rare knock from evidence 0,
        panned so the house settles from somewhere. The surface
        equivalent of the depths' per-room cues.

        ROT AIR -- the layer escalates with the infestation stage,
        the audible twin of the decal pass: drips at 1, flies at 2,
        whisper + structural groan at 3. Outdoor scenes are carried
        by the wind bed and only gain the rot layers (flies, groan).
        SAFE_SCENES stay clean until stage 3, the same rule as the
        decals. Underground rooms are skipped entirely -- their cues
        are authored per-room in the builders, baseline-rotted from
        the start. Scenes rebuild every load, so the pass is
        deterministic + additive, like the rest of the infestation."""
        sc = self.scene
        key = sc.key
        if sc.music in ("void", "wrong"):
            return
        if key in CREEPY_SCENES:
            # The kid humming somewhere they shouldn't be. Deliberately
            # rare (most visits hear it at most once) -- the card loses
            # its power if it plays like a loop.
            sc.add_ambient("child_hum", 0.30, 50.0, 95.0, pan_spread=0.8)
        if key in UNDERGROUND_SCENES:
            return
        outdoor = key in OUTDOOR_SCENES or key in ("brimley",
                                                   "effigy_grove")
        interior = sc.music == "home"
        rot = stage if (key not in SAFE_SCENES or stage >= 3) else 0
        if interior:
            sc.add_ambient("wood_creak", 0.16, 9.0, 17.0, pan_spread=0.6)
            sc.add_ambient("wood_pop",   0.14, 16.0, 28.0, pan_spread=0.7)
            if rot >= 1:
                sc.add_ambient("drip", 0.20, 8.0, 15.0, pan_spread=0.5)
            if rot >= 2:
                sc.add_ambient("flies", 0.22, 11.0, 20.0, pan_spread=0.8)
        elif outdoor and rot >= 2:
            sc.add_ambient("flies", 0.15, 14.0, 24.0, pan_spread=0.8)
        if (interior or outdoor) and rot >= 3:
            sc.add_ambient("whisper", 0.10, 12.0, 22.0, pan_spread=0.6)
            sc.add_ambient("infest_throb", 0.12, 14.0, 24.0)

    def _infest_decals(self, stage, underground=False):
        """Scatter escalating infestation decorations on walkable tiles,
        seeded by (scene, stage) so the spread is stable per load. Surface
        scenes (outdoor + the safe rooms at stage 3) and underground
        scenes only -- ordinary interiors are left to their own dressing."""
        key = self.scene.key
        # The effigy grove counts as surface here: it hosts the descent
        # fold, so the rot and the way down escalate on the same dial.
        surface = key in OUTDOOR_SCENES or key in ("brimley", "effigy_grove")
        safe = key in SAFE_SCENES
        if not underground and not surface and not (safe and stage >= 3):
            return
        rng = random.Random((hash(key) ^ (stage * 2654435761)) & 0xffffffff)
        pool = ["phantom_mark", "dead_crow", "watching_wound"]
        if stage >= 2:
            pool += ["claw_marks", "yellow_sign", "gore", "bloodstain"]
        if stage >= 3 and not underground:
            pool += ["hanging_figure", "corn_doll", "watching_eye"]
        if underground:
            # Tight corridors: signs and wounds only, never a hanging body.
            pool = ["phantom_mark", "watching_wound", "yellow_sign",
                    "binding_sigil", "gore"]
        # Surface scenes get a heavier spread than the small safe rooms.
        per = 3 if (surface or underground) else 1
        count = stage * per
        spawns = list(self.scene.spawns.values())
        placed = tries = 0
        while placed < count and tries < count * 10:
            tries += 1
            tx = rng.randint(1, max(1, self.scene.w - 2))
            ty = rng.randint(1, max(1, self.scene.h - 2))
            wx, wy = tx * TILE + 16, ty * TILE + 16
            if self.scene.is_solid_at(wx, wy):
                continue
            if any(abs(wx - sx) < 28 and abs(wy - sy) < 28
                   for sx, sy in spawns):
                continue
            deco = Decoration(wx, wy, rng.choice(pool))
            # Phase 4: the rot is a WORLD CHANGE — gated to line of sight under
            # tilt so it reveals only where the player actually looks (the
            # infection 'updates in memory' when seen; CAMERA.md Phase 4).
            deco._sight_gated = True
            self.scene.add_decoration(deco)
            placed += 1

    def _infest_locals(self, stage):
        """Turn or rot the surface locals by name. Converts become passive
        cult (a 'cult_convert' tag -- _tick_cultists counts their gaze but
        they never grab); mutates keep themselves under a wrongness overlay."""
        for n in self.scene.npcs:
            if not getattr(n, "alive", True) or getattr(n, "_is_corpse", False):
                continue
            nm = getattr(n, "name", "")
            cs = INFEST_CONVERT.get(nm)
            ms = INFEST_MUTATE.get(nm)
            if cs is not None and stage >= cs:
                self._convert_local(n)
            elif ms is not None and stage >= ms:
                n._mutated = True
                # Their body has started speaking for the fold; the
                # dialogue curdles to match the overlay.
                n.dialogue_fn = _mutated_local_dialogue
        # Mrs. Calder's outdoor table: once she has joined, the extra
        # place she kept set for the guest she couldn't name is cleared
        # away -- the waiting is over. One setting stays (hers, unused).
        # Her converted dialogue above carries the other half of the beat.
        if (self.scene.key == "brimley"
                and stage >= INFEST_CONVERT.get("Mrs. Calder", 99)):
            settings = [d for d in self.scene.decorations
                        if getattr(d, "kind", "") == "place_setting"]
            for d in settings[1:]:
                self.scene.decorations.remove(d)

    def _convert_local(self, n):
        """A peace-maker, joined. Becomes a masked cultist that watches
        you (raising visibility via the gaze count) but never chases or
        grabs -- passive cult. Their old dialogue is gone."""
        n.sprite_kind = "cultist"
        n.portrait = None
        n.tag = "cult_convert"
        n.movement = "watch"
        n.dialogue_fn = _converted_local_dialogue
        n.no_prompt = False
        n.solid = True
        n._gaze_range = 150
        n._mutated = False

    def _spawn_counter_eater(self):
        """Stage 2+: a convert eating at the store counter (food scarcity,
        NARRATIVE 8 -- the town's food goes where its faith went). Ambient
        tableau on the depths-digger contract: idle, non-solid, no prompt,
        NO tag -- excluded from the gaze tick, never chases, never reacts.
        The tin bowl is part of the pose art (sprites_cultist 'eat')."""
        e = NPC(8 * TILE + 16, 9 * TILE + 16, "A neighbor", "cultist",
                movement="idle", solid=False, no_prompt=True)
        e.facing = (1, 0)                  # in profile, toward the counter
        e.pose = "eat"
        self.scene.add_npc(e)

    def _spawn_hunting_sheriff(self):
        """Stage 3: Sheriff Vane's office is no longer a place you visit.
        Replace the watching Sheriff with the hollow thing he became -- a
        unique, relentless pursuer. He holds for a beat (his last words),
        then comes for you. Reaching you ends the run (the 'sheriff' card).
        You escape by getting back out the door; he's slower than a run."""
        self.scene.npcs = [n for n in self.scene.npcs
                           if getattr(n, "name", "") != "Sheriff"]
        hx, hy = 8 * TILE + 16, 2 * TILE + 16
        s = NPC(hx, hy, "Sheriff Vane", "sheriff_hollow",
                movement="idle", solid=True, speed=0.78, tag="sheriff_hunt")
        s.dialogue_fn = None
        s.facing = (0, 1)
        self.scene.add_npc(s)
        self._sheriff_intro_t = 2.0
        self.show_notice("Sheriff Vane stands. \"I'm supposed to tell you "
                         "to leave, son. I can't say it anymore.\"",
                         duration=3.2)
        self.audio.play("sheriff_hunt", 0.85)

    def _tick_sheriff(self, dt):
        """Drive the stage-3 Sheriff encounter: hold for the intro beat,
        then set him hunting (force-chase), and end the run if he reaches
        the player. No-op in any scene without a sheriff_hunt NPC."""
        if self.scene is None or self.player is None:
            return
        s = next((n for n in self.scene.npcs
                  if getattr(n, "tag", "") == "sheriff_hunt"
                  and getattr(n, "alive", True)), None)
        if s is None:
            return
        intro = getattr(self, "_sheriff_intro_t", 0.0)
        if intro > 0:
            self._sheriff_intro_t = intro - dt
            if self._sheriff_intro_t <= 0:
                s.movement = "chaser"
                s._force_chase = True
                self.audio.play("sheriff_hunt", 0.95)
                self.audio.duck(0.8, depth=0.4)
            return
        d = math.hypot(s.x - self.player.x, s.y - self.player.y)
        if d < 24 and self.player.invuln <= 0:
            self._trigger_death("sheriff")
