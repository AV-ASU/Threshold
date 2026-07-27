"""THRESHOLD world rot -- the world rotting as the case is understood.

The evidence-driven decay pass (decals + the hunting sheriff) and the
airborne ashfall overlay, extracted from systems/game.py as an RotMixin on
the Game class. Since TODO #22c the pass NO LONGER changes the townsfolk
(the town stays ordinary; the rot is the PI's, in the conversation
framing) -- only the corpse dialogue helper travels here now
(_corpse_examine, re-imported by game.py for _make_corpse). Tuning lives
in systems.config.
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


# (The converted-local dialogue, the ROT_TURN line table, and the
# turned-local dialogue were CUT in TODO #22c. The town stays ordinary
# to the end: no local joins on-screen and no resister's voice curdles.
# The world rot is the PI's now, carried by the four-tier conversation
# framing (scenes/dialogue._pi_framing); NARRATIVE §2.)


class RotMixin:
    def _tick_power(self, dt):
        """The genset power link (the light-security loop's first slice,
        TODO #21). `_genset_down` holds per-scene blackout timers; while a
        scene's timer runs its ELECTRIC fixtures are dead in every layer at
        once: `Scene.power_on` gates `lit_at` (mechanical), `_draw_dark`
        skips their pools (visible), and the per-deco `_powered` flag turns
        the fixture art itself dark (a dead lamp draws dark glass, and the
        office radio's dial goes out). Power returns on its own when the
        timer runs out; fire is exempt throughout. No live trigger sets a
        timer yet: the gas-genset failure meant to (TODO #21) is deferred,
        so the mechanism stands ready and is guarded synthetically by the
        stealth section 17 blackout test."""
        down = getattr(self, "_genset_down", None)
        if down is None:
            down = self._genset_down = {}
        for k in list(down):
            down[k] -= dt
            if down[k] <= 0:
                del down[k]
        sc = self.scene
        if sc is None:
            return
        on = sc.key not in down
        if getattr(sc, "power_on", None) != on:
            sc.power_on = on
            for d in sc.decorations:
                if (d.kind in sc._ELECTRIC_KINDS
                        or d.kind == "wrong_radio"):
                    d._powered = on

    # ---- World rot -------------------------------------------------
    def _rot_stage(self):
        """Surface world rot stage 0..3, front-loaded to peak as the
        player commits underground at 3 evidence. Monotonic with the
        evidence count (knowing rots the world, and you can't un-know)."""
        return min(3, self._evidence_count())

    def _ashfall_target(self):
        """How many ash motes the air should hold right now (DESIGN.md §2).
        Zero on the Threshold (the still eye of it) and in safe rooms before
        stage 3; otherwise stage-driven, thicker underground (the source)."""
        if self.scene is None:
            return 0
        key = self.scene.key
        if key == "threshold":
            return 0          # never on the Threshold (1b)
        stage = self._rot_stage()
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

    def _apply_rot(self):
        """Re-derive the world's rot for the freshly-loaded scene from the
        evidence count. Scenes rebuild every load, so this is deterministic
        and additive each time -- never accumulates. Runs after on_enter so
        it can transform the live locals in place."""
        if self.scene is None:
            return
        key = self.scene.key
        surface_stage = self._rot_stage()
        # Stage transition cue: the world rots one step further. Fires
        # on the scene load that lands AFTER an evidence cross (so the
        # audio aligns with the visible decal/ashfall change, not with
        # the case-file beat itself, which has its own chime). Tracked
        # on the Game instance; reset to 0 by _reset_run_state.
        last = getattr(self, "_last_infest_stage", 0)
        if surface_stage > last:
            self._last_infest_stage = surface_stage
            self.audio.play("rot_throb", 0.80)
            self.audio.duck(1.6, depth=0.40)
        underground = key in UNDERGROUND_SCENES
        if underground:
            # Wrong from the first rung: a baseline even at 0 evidence,
            # deepening on the FULL evidence count.
            self._rot_decals(max(1, self._evidence_count()), underground=True)
        elif surface_stage > 0:
            self._rot_decals(surface_stage, underground=False)
        # The town stays ORDINARY to the end (TODO #22c, NARRATIVE §2): the world rot is the INVESTIGATOR'S now, not the
        # townsfolk's. The old people-change (converting peace-makers into
        # cultist sprites, curdling the resisters' dialogue) is CUT; the
        # locals keep their bodies, faces, and voices. Only the PI curdles,
        # and that lives in the conversation framing (the four-tier PI
        # register, scenes/dialogue._pi_framing). The place still rots (the
        # decals above); the people do not.
        # Sheriff Vane's office becomes a unique threat once HE has gone
        # hollow (DESIGN.md §2: the player-driven fall -- the despair ledger
        # latch, or the neglect override read in _vane_is_hollow; the old
        # rot-stage-3 gate is gone) -- unless the player already put Vane
        # down: dead locals stay dead (the ledger normalizes "Sheriff
        # Vane" to "Sheriff"), so a shot Vane never stands back up
        # hollow; his body holds the office.
        if key == "sheriff_office" and self._vane_is_hollow() \
                and not self._local_is_dead("Sheriff"):
            self._spawn_hunting_sheriff()
        # (The stage-2 counter-eater tableau -- a converted "neighbor"
        # calmly eating in the shop -- was CUT with the people-change, TODO
        # #22c: a joined local on display is exactly the town-curdling the
        # rework relocates to the PI. The cult's mundane presence is carried
        # by the enemy patrols now.)
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

        ROT AIR -- the layer escalates with the world rot stage,
        the audible twin of the decal pass: drips at 1, flies at 2,
        whisper + structural groan at 3. Outdoor scenes are carried
        by the wind bed and only gain the rot layers (flies, groan).
        SAFE_SCENES stay clean until stage 3, the same rule as the
        decals. Underground rooms are skipped entirely -- their cues
        are authored per-room in the builders, baseline-rotted from
        the start. Scenes rebuild every load, so the pass is
        deterministic + additive, like the rest of the world rot."""
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
        outdoor = key in OUTDOOR_SCENES or key == "effigy_grove"
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
            sc.add_ambient("rot_throb", 0.12, 14.0, 24.0)

    def _rot_decals(self, stage, underground=False):
        """Scatter escalating world rot decorations on walkable tiles,
        seeded by (scene, stage) so the spread is stable per load. Surface
        scenes (outdoor + the safe rooms at stage 3) and underground
        scenes only -- ordinary interiors are left to their own dressing."""
        key = self.scene.key
        # The effigy grove counts as surface here: it hosts the descent
        # fold, so the rot and the way down escalate on the same dial.
        surface = key in OUTDOOR_SCENES or key == "effigy_grove"
        safe = key in SAFE_SCENES
        if not underground and not surface and not (safe and stage >= 3):
            return
        rng = random.Random((hash(key) ^ (stage * 2654435761)) & 0xffffffff)
        pool = ["phantom_mark", "dead_crow", "watching_wound"]
        if stage >= 2:
            pool += ["claw_marks", "yellow_sign", "gore", "bloodstain"]
        if stage >= 3 and not underground:
            pool += ["corn_doll", "watching_eye"]
            # No hanged body at the effigy grove: it is the cult's own dug
            # mine mouth, "work without the worker" (they claim people into
            # the hive, they do not hang them), and a hanging figure reads
            # wrong at the mouth. The town + fields still get it.
            if key != "effigy_grove":
                pool.append("hanging_figure")
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
            # infection 'updates in memory' when seen; DESIGN.md §10).
            deco._sight_gated = True
            self.scene.add_decoration(deco)
            placed += 1

    # (_rot_locals / _convert_local / _spawn_counter_eater were CUT in TODO
    # #22c. The town stays ordinary to the end: no local is repainted a
    # cultist, no resister's voice curdles, and Mrs. Calder keeps her second
    # place setting -- she never stops waiting. The world rot lives in the
    # PI now, in the conversation framing, scenes/dialogue._pi_framing.)

    def _vane_is_hollow(self):
        """Sheriff Vane's fate gate (DESIGN.md §2; was TODO #2a). True once the hollow turn
        has latched: by the despair ledger (scenes/dialogue._vane_ledger --
        the newspaper and the preacher's murder against the hope the PI
        shared), or by the NEGLECT OVERRIDE evaluated here: the case
        reaches the descent line (VANE_NEGLECT_EVIDENCE canonical beats)
        with fewer than VANE_MIN_INFORMED discoveries ever shared with
        him, and his last hope, that somebody was actually working it,
        dies with the silence. Every share happens across his own desk,
        and entering the office runs this gate first -- so the override
        cannot be dodged by sharing after the fact. Latches the flag
        either way: once hollow, no return."""
        if self.save.flag("vane_hollow"):
            return True
        if (self._evidence_count() >= VANE_NEGLECT_EVIDENCE
                and int(self.save.arg("vane_informed", 0))
                < VANE_MIN_INFORMED):
            self.save.set_flag("vane_hollow", True)
            return True
        return False

    def _spawn_hunting_sheriff(self):
        """The hollow turn: Sheriff Vane's office is no longer a place you visit.
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
        # The intro notice + sting fire ONCE per run (C12): the NPC + the
        # 2.0s hold still stand up on every hollow-office load so the room
        # stays lethal on re-entry, but the announce does not replay.
        if not getattr(self, "_sheriff_announced", False):
            self._sheriff_announced = True
            self.show_notice("Sheriff Vane stands. \"I'm supposed to tell you "
                             "to leave, son. I can't...\"",
                             duration=3.2)
            self.audio.play("sheriff_hunt", 0.85)

    def _tick_sheriff(self, dt):
        """Drive the hollow-Sheriff encounter: hold for the intro beat,
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
