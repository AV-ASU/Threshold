# THRESHOLD — next-session kickoff prompt

> Paste this (or point the assistant at this file) to start the next chat.

---

You are continuing work on **THRESHOLD**, a 1994 narrative-horror game in
Python/pygame (oblique tilted camera, no combat — walk, watch, hide; the only lethal
thing is the King in Yellow). Work on branch **`claude/hopeful-bell-1zI7f`**;
commit and push there as you go.

## First, get oriented
1. **Read `NARRATIVE.md`** — it is the single source of truth: the story,
   the cast and their allegiances, the descent geography, the clue/evidence
   map, both endings, the death states, and the **Art Direction** section
   (§10). Treat it as canon; keep it in sync when decisions change.
2. Internalize the **CORE DESIGN PRINCIPLE** (NARRATIVE.md §10): *break the
   tile lockstep — things should bleed across multiple squares or occupy
   less than one.* When art reads "RimWorld," it's snapping to the grid.

## Workflow / commands
- **Tests (must stay green):** `python tests/smoke.py` — verifies every
  scene builds, spawns are walkable + off exits, and exits resolve.
- **Visual preview (headless):** `python tools/render_scenes.py [keys...]`
  → labelled PNGs in `/tmp/threshold_renders/` with the in-game film grade.
  Read them back to judge the look. `pip install pygame` if the fresh
  container lacks it. ALWAYS render to verify any visual change — you can't
  run the actual game (no display).
- After a change: smoke test → render to eyeball → commit → **push**
  (`git push -u origin claude/hopeful-bell-1zI7f`). Don't skip the push.

## What's already done (this is built + pushed)
- Narrative bible locked (PI hunting **Mara Blaine**; split town; descent
  Brimley → Brimley → the Works → the Depths → the Hive; End-it vs
  Spread-it; cultist-catch = CAPTURED, King-catch = Carcosa).
- **The Works** (7-room Basement Level) built in `scenes/well.py`; well is
  the sole way down, orb gates the deeper stair, rope snaps if you descend
  carrying the orb.
- **Darkwood art pass** in `scenes/base.py` + `entities/decoration.py`:
  muddy desaturated palette, continuous near-black wall mass (no grid
  blocks), wall/contact shadows + light pools, macro floor shadow, the
  bespoke **Yellow Sign**, whole-frame **film grade** (`apply_grade`, wired
  into `systems/game.py:draw_world`).
- **Doors** rebuilt as unconfined entities: opening punched in the wall
  in-tile, the leaf an overflowing late-pass sprite (`draw_scene_doors`)
  that swings from a CORNER out into the room; collision stays on the grid;
  swing varies per door.
- **Brimley** seeded with organic walkable corn-cover (`:`) hide patches.

## Goals (roughly prioritized)
**A. Finish the look (break-the-grid principle):**
- Oversized, OVERLAPPING trees + corn — drawn larger than their tile,
  overhanging neighbours so the canopy/field line is organic. Biggest
  remaining outdoor win; do it in the draw layer so all scenes benefit.
- Continue per-scene **liminal composition** (brimley, then town, cult
  sites, depths): composed emptiness, uncanny repetition, non-orthogonal
  dressing.
- Housekeeping: delete the now-dead door helpers in `scenes/base.py`
  (`_door_open`, `_door_front_closed`, the `draw_object` "door" branch).

**B. Write the story into the game** (`scenes/dialogue.py` is all blank
placeholder right now):
- Real dialogue for the Lodge Clerk, Sheriff, Preacher (innocent → he
  vanishes, body found elsewhere), Store-Owner, Kid, and Mara.
- Rename items to the case in `systems/items.py` (keep KEYS; change display
  names): `polaroid`→Case Photo, `mom_notebook`→Mara's Journal, etc.
- Recast: `son_room` → Mara's room; the Innkeeper → the Lodge Clerk
  (DISPLAY_NAMES + dialogue). Rewrite `README.md` to the PI/sealed-town premise.

**C. Mechanics spine** (`systems/game.py`):
- The **3-evidence King gate** in `_tick_king` (~the visibility>=1.0 spawn):
  spawn the King only at `len(save.arg("evidence")) >= 3`; below that, spawn
  **2 cultists at the entry door** (reuse `_king_anchor`) with a cooldown.
- Net-new endings/deaths: the **CAPTURED** text card (cultist contact) and
  the **Carcosa** fire-and-masks cutscene (King catch — currently routes to
  `_begin_threshold_closure`). End-it (`seal_threshold`) and Spread-it
  (`escape_alone`) ending scripts already exist.
- Wire the 6 evidence pickups to fire `_evidence(...)`; the Preacher
  disappearance event; eventually build **the Hive** (deepest layer).

## Conventions
- Keep `tests/smoke.py` green. Render to verify visuals. Commit in logical
  units with clear messages and push to the branch every time.
- Don't reintroduce the grid: doors/props/foliage should spill past tile
  boundaries; walls stay a continuous mass.
