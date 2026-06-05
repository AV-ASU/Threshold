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
    mouth. A flat, patient line; no name."""
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

    def _infest_decals(self, stage, underground=False):
        """Scatter escalating infestation decorations on walkable tiles,
        seeded by (scene, stage) so the spread is stable per load. Surface
        scenes (outdoor + the safe rooms at stage 3) and underground
        scenes only -- ordinary interiors are left to their own dressing."""
        key = self.scene.key
        surface = key in OUTDOOR_SCENES or key == "brimley"
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
        self.audio.play("low_pulse", 0.6)

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
                self.audio.play("void_sting", 0.6)
            return
        d = math.hypot(s.x - self.player.x, s.y - self.player.y)
        if d < 24 and self.player.invuln <= 0:
            self._trigger_death("sheriff")
