# THRESHOLD — Claude guide

THRESHOLD is a narrative-horror game in **pygame**: stealth and dread in a
folded-shut northern-Minnesota corn town, driven by a **visibility** meter that
feeds the **King in Yellow**, the lethal apex pursuer. Two facts shape almost
every change:

- **The camera is a fixed ~55° oblique tilt, and it is the ONLY camera** —
  there is no flat/top-down view. What a change *looks like* depends on that
  tilt (a prop's depth-sort, a wall's occlusion, a door's facing, a decal's
  warp). So you render the scene and LOOK; you never judge the look from the
  code (that is VISION.md's whole job).
- **Every sprite is drawn procedurally** — there is no image-asset pipeline.
  Art work is code in the draw layer, never a file to swap.

> **HARD RULE — no dashes in player-facing text.** Never use em-dashes,
> en-dashes, or `--` as punctuation in anything the player reads (item
> names/descriptions, dialogue, narrator/notice boxes, evidence/notes,
> endings, on-screen labels). Rewrite with a period, comma, colon, or a new
> sentence. Code comments and these docs may still use them. Flow-guarded.

## The canon — five docs own the fiction and the systems

The design, story, and text live in five docs, each with one job. They are the
source of truth, and **your memory of them is stale by default** — they change,
and canon has been broken by answering from a half-remembered version. So:
**before you touch or answer about an area, read the doc that owns it, and
trust the doc over your memory.** One fact lives in ONE home; a detail true in
one doc and stale in another is rot, reconciled on sight.

| Doc | Owns |
|---|---|
| `NARRATIVE.md` | the story bible — premise, lore, cast, place, the evidence trail, the endings, and the canon invariants. What the fiction asserts. |
| `DESIGN.md` | every system + its code map — the threat model, world rot, the fold, the tilt camera, audio, stealth, the Works level, art direction. |
| `DIALOGUE.md` | every word the player reads (spoken lines + narrator boxes), by speaker and by trigger, plus the voice rules. **Contract: a player-facing text change edits the code AND this doc in the SAME commit.** |
| `TODO.md` | the live list of genuinely open work. Not a place for lore. |
| `VISION.md` | the see-it-don't-guess rule and how to capture: render a scene and look before you judge or ship how it looks. |

This file (`CLAUDE.md`) is the sixth — the **map and the rulebook** below: how
to work in the repo, where things live, and the rules you can't derive from the
code.

## Dev commands

```bash
python main.py                 # run (needs a display)
python tests/run_all.py        # THE gate: smoke + flow + stealth + fold_pursuit
                               # + king_roam + render_smoke. Green before every commit.
python -m compileall systems entities scenes rendering ui .   # syntax check (no linter)
```

Single harness (same self-configured SDL dummy drivers, standalone):
`python tests/smoke.py` (scene-builder / spawn / exit / drop-rate) or
`python tests/flow.py` (story-beat integration + canon-guards). Headless work
(web sessions, ad-hoc scripts) wants
`export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=.` — the
session-start hook sets it automatically. To *see* a sprite or animation, use
the `sprite-preview` skill; for a whole scene, `tools/capture_world.py`.

## The map (orientation, not a file index — open the code for detail)

| Where | What's there | Design home |
|---|---|---|
| `main.py` | entry point (`Game().run()`). | |
| `systems/` | the engine. `game.py` is the orchestrator (state machine, `step(dt)`, the update/input loop, scene loading); its big subsystems are **mixins** it inherits (threat, king-roam, rot, render, narrative, tableau). `config.py` holds all gameplay tuning constants + the scene-gating sets, and is star-imported into `game.py`. | DESIGN §1-3, §12 |
| `scenes/` | ~47 scenes in a `SCENE_BUILDERS` registry. A scene = spawns / exits / decorations / npcs / enemies / items + optional `on_enter` / `on_update` / `on_interact` hooks. `base.py` is the Scene model; terrain draw lives in `terrain.py`. | DESIGN §5 (levels), §7 (the fold) |
| `entities/` | `player`; `npc` (movement modes, incl. the surface cult AI and the King); `enemy` (underground cult); `decoration` (per-kind procedural props). | DESIGN §1 |
| `rendering/` | procedural sprites + the tilt camera. `camera.py` is the single world→screen seam. The King is `king_unfold.py`. | DESIGN §10 (camera), §6 (art) |
| `ui/` | the three text channels (modal `dialog`, over-the-head `float_speech`, lower-third `narration`), the Casebook journal, and the close-up examine tableaux. | DIALOGUE.md |

A few modules (`scenes/base`, `rendering/sprites`, `entities/decoration`) are
thin **facades** that re-export from themed siblings, so `from … import X` is
stable — edit the sibling, not the facade.

## Rules you can't derive from the code

- **Tilt-set dispatch — the invisible-prop trap.** Every prop/decoration kind
  must be registered in exactly ONE tilt set: a real `FURNITURE` / `SOLID_PROPS`
  **volume** for anything man-made or solid, a **standee** card only for
  genuinely organic/thin things (trees, grass, an effigy), a **wall-deco**, or a
  **floor decal**. A kind in no set renders as a flat floor stain; a raw
  furniture OBJECT tile (`t`/`b`/`c`/`k`/`f`) is an **invisible solid** under the
  tilt. Use `add_furniture`, never a raw tile. **Preview a new kind before
  placing** (`tools/preview_props_sheet.py`) — never place a kind by its name.
  Guarded by smoke [9/9].
- **Player-facing text clears a higher bar than code** — the DIALOGUE.md voice
  rules: no dashes; state the fact and stop; cosmology only as sensation, never
  named; no game mechanic / verb / evidence-threshold in the fiction; no
  knowledge the speaker can't have; markup (`[c=...]`) never leaks to screen.
  Read them before writing a line.
- **Scene and item keys are load-bearing** (game logic + the single in-session
  save). Rename only by updating every reference in the same change; there is no
  cross-run save to migrate.
- **No day/night cycle** — it was removed; the world reads as one daytime state.
  Don't reintroduce `day_phase` / `day_count`.
- **The scene-gating sets** in `config.py` (`SAFE_SCENES`, `DARK_SCENES`,
  `KING_FREE_SCENES`, `CULTIST_SCENES` …) drive King safety, flashlight
  darkness, spawn logic — check membership there, don't hard-code a scene list.

## Before you call a scene or a line "done" — the playtest error classes

A play-test surfaced each of these as a CLASS, not a one-off: when you touch one,
hunt the whole class rather than fixing a single instance.

1. **Wrong verb** — evidence and pickups are walk-over ground items
   (`scene.add_item`), not `[E]` prompts. `[E]` is only for readables/handoffs
   that run a side effect the auto-pickup path can't.
2. **Wrong beat** — a note/dream/pointer fires on the event the fiction names
   (the door-dream on journal *pickup*, not a re-read; a pointer only after the
   PI has actually met/read the thing).
3. **Mechanics in text** — see the voice rules above.
4. **Over-written captions** — a routine action (a key, a body, a prop) is a
   terse line or nothing; a beat that earns a close-up gets a mini-cutscene, not
   a long unstoppable caption.
5. **Knowledge the speaker can't have** — no line states a fact the player
   hasn't earned or the cosmology the game is built to make them infer.
6. **Raw markup leaking** as literal text on any render path (notebook, toast,
   caption).
7. **Tilt-projection artifacts** — wrong tilt set (above); a portal with a
   reachable back or a floating base; a wall-deco or door that occludes
   dishonestly. Preview first.
8. **Scene-geometry defects** — no npc home/spawn on a door tile or its lone
   approach; a door *replaces* a wall segment (never a hole punched mid-wall);
   no missing walls; no walkable water the fiction calls a barrier; break the
   grid lockstep. **View every room from all four N/E/S/W facings before done**
   (VISION.md).
9. **Threat pacing** — the world's speed is ONE knob (`PACE` in `config.py`,
   applied at each mover's consumption site so ratios stay PACE-invariant). Too
   fast/slow in playtest: tune `PACE`, never a single actor. The apex never
   spawns on the player's exit tile.

The full scene-dressing discipline (provenance, the mistaken-identity test,
verify-at-three-altitudes-then-in-the-dark) lives in **VISION.md** — follow it
before placing a single detail.

## Working agreements (process — learned the hard way)

- **NEVER use `AskUserQuestion`** — it errors out every time and burns a turn.
  When you need the maintainer to choose or clarify, ask in plain text (a short
  numbered list with your recommendation) and stop for the answer.
- **Docs are part of the change, in the SAME commit — not a follow-up.** Touch a
  system → update DESIGN; a canon fact → NARRATIVE; open/landed work → TODO; the
  look or the capture flow → VISION; the layout or a convention → this file. And
  **any player-facing line changes the code AND `DIALOGUE.md` together** (the
  contract). A change isn't done until its docs match it. Before you commit, ask
  which of the docs your diff just made stale, and fix them in the same breath.
- **"Push to main" means MERGE to main** — open the PR and merge it in the same
  action, no second confirmation.
- **Verify before you commit** — compile + `python tests/run_all.py` green
  BEFORE `git commit`/`push`. For rendering/refactor work also run the
  byte-identity gate (`tools/capture_world.py --tag before/after`, then `--diff`).
- **One edit at a time on a shifting file** — don't batch many `Edit`s against
  the same file (early edits move line context and later ones mis-apply). For
  multi-site mechanical changes, write a small patch script with
  `assert count == 1` per replacement, then run and verify.
- `__pycache__/` is gitignored; never commit `.pyc`.
