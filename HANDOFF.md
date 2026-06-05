# THRESHOLD — handoff for the next chat

**Repo:** `/home/user/Threshold` · **default branch:** `main`

> **Current state lives in `SESSION_STATUS.md`** — read that first. The sections
> below are kept as historical handoff context (canon to preserve, prior arcs).

---

## ⮕ LATEST (2026-06): shippability review → game.py refactor → health pass

Branch `claude/game-shippability-review-B1c5e`. **Code + docs.** In short:
- Fixed fold-pursuit so a chaser follows through hidden-fold groves (no spawns
  there); locked by `tests/fold_pursuit.py`.
- Refactored `systems/game.py` 5163 → 2069 lines into five mixins (config,
  threat, infest, render, narrative) — behavior-preserving, byte-identity
  verified via `tools/capture_world.py`.
- Added `tests/run_all.py` (the full gate) and swept ~550 lines of dead code
  (incl. the superseded `rendering/king3d.py`).
- Only open narrative item: **GAME_CHANGES.md §12 (Rev. Crane)**, design-gated.

Full detail + open items: **`SESSION_STATUS.md`**.

---

## ⮕ EARLIER (2026-06): narrative canon-alignment pass — DOCS only

A long story/canon working session with the user settled a batch of
decisions. **This session changed DOCS, not game code.** What landed:

- **`NARRATIVE.md` rewritten to the settled canon** — the lure chain
  (King→Mara→Walter→PI, felt not stated), the awareness model (no visible
  tell; the cult knew the gist of its bargain, the locals never knew they
  were claimed), the rite as **seal + power-bank**, **Sable = most-attuned
  local**, **Royce stopped driving**, **Mrs. Calder's unnameable guest**,
  **Toby's well-clue**, **Ledger → front desk**, **Playscript = the cult's
  own notes**, the **ashfall** infestation layer, and the **keystone-to-
  door** fork (Mask + notes combine, the Deep Stair opens *without*
  consuming them, the keystone is spent at the **Threshold** to SEAL; carry
  it out = SPREAD; the Mask reads as **"permission to leave,"** built up by
  the PI's **distressed notes**).
- **`CLAUDE.md`** — a Conventions pointer to the above.
- **`GAME_CHANGES.md` (NEW)** — the **code TODO** to make the game match
  the new canon, with file:line references from a fresh audit. **Start
  here next session.** None of it is implemented yet.

Re-audit confirmed: the Works **7-room gauntlet** matches the build; the
Depths has grown to 5 rooms + side-branches (now noted in NARRATIVE §9).

> The section below is the **prior** session's handoff (journal door-dream →
> "He knows you"); kept for reference.

---

## What's DONE this session (the journal door-dream → "He knows you" arc)

1. **Journal door-dream cutscene (NARRATIVE §1b).** Reading Mara's journal
   (`mom_notebook`) a third time fires a ~7s wordless dream
   (`Game._tick_flashback` / `_draw_flashback`):
   - dried-wood doorframe in black; pulsing gold glow pooled at the door's
     **base** (`FLASHBACK_FOCAL_Y`), contained by the frame;
   - faint peeking eyes;
   - an **accelerating swarm** of carved dark-wood masks
     (`_spawn_flashback_masks` + pooled `_build_flashback_pool`) — they clip on
     the jamb and their gold gazes all converge on the player;
   - audio bed `falling_air` (wind + falling) via `Audio.flashback_air()`.
   - Mask art: `door_mask_surface()` in `rendering/sprites.py` (dark wood,
     recessed sockets, no mouth, `gaze`-pointed pupils, `_jag_blob` shapes).
   - Tuning: the `FLASHBACK_*` block in `ui/cutscenes.py`; `_tick_flashback` /
     `_spawn_flashback_masks` now live in `systems/narrative_mixin.py`.

2. **"He knows you" (NARRATIVE §0/§1b).**
   - `Game._log_dream_entry()` writes the dream to save arg **`notes`** (NOT
     `evidence` — that would arm the King-gate). `NotebookUI` shows notes after
     the clues.
   - Real Threshold recognition line in `scenes/depths.py build_threshold`
     `on_enter`: if `flashback_seen`, *"You have stood here before. In sleep."*
     lands before the doorframe beat.

3. **CANON FIX (important):** the PI dreamed the door **once, a year ago, and
   never reached it** — the journal *reminds* him; it is NOT recurring. An
   earlier draft wrongly said "the same dream again / fourth night." Corrected,
   and locked with `tests/flow.py` canon-guards.

4. **Housekeeping:** stale single-mask comments refreshed; `SESSION_STATUS.md`
   added; `tests/flow.py` updated for the new behavior + a new "He knows you"
   section (8 checks); **fixed 3 long-standing stale flow tests** (well moved to
   `_well_pos` col 94/row 13; Kid renamed to "the Tisdale boy") — flow is now
   fully green; **git history cleaned** (squashed two broken `NameError`
   intermediate commits; tree verified byte-identical before force-push).

5. **Docs updated this session:** `CLAUDE.md` (new "journal door-dream" +
   "Working agreements" sections), `NARRATIVE.md` (marked the dream / "He knows
   you" bullets DONE with the authored canon), `SESSION_STATUS.md`, this file.

---

## NEW LORE / CANON to preserve (now in NARRATIVE.md + CLAUDE.md)

- **The PI's dream is singular.** Attuned **exactly once, a year ago**; walked
  up, looked in, **met His eye** for a blip, **never reached** the door; it
  never took root. That rare profile (unclaimed, barely-attuned, *known* to
  Him) is why the fold opens for him alone and why the King's end-hunt is
  personal. NEVER write it as recurring.
- **The dream is the lure, and the lure = the case.** Mara was *answered, not
  deceived* (she found religion, went down the well). The door broadcasts a
  dream tuned to the dreamer's own desire; the PI's numbness made him nearly
  immune — His bait for a numb investigator is *an unsolved case*.
- **Recognition, not threat.** "He knows you" surfaces in the notebook + the
  Threshold line — it is NOT the lethal King reveal.

---

## SUGGESTED NEXT TASKS (from NARRATIVE.md "Surface what's only in the bible")

Pick up here. Cross-check every line against `NARRATIVE.md` BEFORE writing.

1. **Name the principal locals.** Sheriff, Preacher, Store-Owner, etc. — give
   them names/voices consistent with the bible. (Kid already done: Toby
   Tisdale.) Search scenes for generic NPC names ("the ___") and the bible's
   §-tables for intended identities.
2. **Sweep for more village→brimley stale refs.** We found 2 in tests; check
   scene code, comments, and any remaining "village"/old-name references.
3. **Seed the lure across the notebook** (the case-is-bait framing) — small
   diegetic touches per §1b, without over-explaining (truth arrives as
   sensation).
4. **Verify the gun = false-power threshold** matches canon end-to-end
   (<3 evidence kills cultists, 3+ stuns, King unshootable, clean round always
   kills a local) — add a flow.py guard if missing.
5. Anything the user directs — they drive art/feel decisions; show previews
   (PNG/GIF) and iterate.

---

## OPEN / FYI

- Audio is procedurally synthesized; it's verified non-silent/non-clipping but
  has NOT been heard by a human in this environment — flag for the user to
  confirm by ear (`falling_air` bed + the `wrong` stab).
- The dream's swarm timing/feel knobs (`FLASHBACK_RATE_MAX`, `_SWARM_START/
  _PEAK`, `_MASK_FRAMES`, `_FOCAL_Y`) are easy to tune if the user wants
  denser/sparser/faster.
