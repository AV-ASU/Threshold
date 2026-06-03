# PROMPT — THRESHOLD canon-alignment (execute Phase 1 nonstop; STOP before Phase 2)

> Paste this into a fresh Claude Code session on the THRESHOLD repo. It is
> self-contained. Your job is to make the **game** match the **settled
> canon** that already lives in the docs.

You are continuing **THRESHOLD**, a top-down narrative-horror game in
pygame (every sprite procedural; no art assets). The story canon was just
re-settled with the user. Two docs are your source of truth — **read both
in full before touching code**:

- **`NARRATIVE.md`** — the narrative bible (authoritative; when code and it
  disagree, it wins).
- **`GAME_CHANGES.md`** — the per-task code TODO with `file:line` pointers
  from a recent audit (verify the lines; they drift).

Also skim **`CLAUDE.md`** (dev commands, conventions, the "Working
agreements").

---

## OPERATING RULES — follow exactly

1. **Run nonstop.** Work straight through **every Phase 1 task below**
   without pausing to ask for confirmation between tasks. Where a small
   decision is needed (wording, a flavor line, where to put a desk prop),
   make the sensible default that best fits NARRATIVE.md and keep going.
   Only stop for a genuine fork you cannot resolve from the bible.
2. **HARD STOP at the end of Phase 1. Do NOT begin Phase 2.** Phase 2 is
   listed at the bottom **for context only**. When Phase 1 is complete:
   run the full verify suite, commit, push, post a summary of what changed
   and what's left, and **wait for human review.**
3. **Check every narrative line against `NARRATIVE.md` BEFORE you write
   it.** Quote the bible's intended voice; don't invent canon.
4. **Never write the word "dimension"** or otherwise *explain* the door
   (NARRATIVE §1b discipline). Cosmic truth arrives **only as sensation**.
   Where His POV is felt, it reads as **gleeful luck / recognition** — He
   found exactly the right hand — never omniscient inevitability (§1, "He
   is powerful, not omniscient").
5. **Item KEYS and scene KEYS are load-bearing** (saves + logic depend on
   them). Only **display names and fiction** change. Do **not** rename keys:
   `playscript`, `sigil_rubbing`, `mom_notebook`, `cross`, `the_ledger`,
   `robe`, `unsent_letter`, scene keys, etc.
6. **One edit at a time on a shifting file.** Don't batch many edits into
   one file blindly; for multi-site mechanical changes write a small patch
   script with `assert count == 1` per replacement, then run + verify.
7. **Verify before every commit.** Green required:
   `python -m compileall systems entities scenes rendering ui .`
   then `python tests/smoke.py` then `python tests/flow.py`.
   **Add a `tests/flow.py` guard whenever you lock a canon fact** (e.g.
   ledger fires from the desk; Sable is a local; the Deep Stair does not
   consume the keystone). Headless env is set by the session hook (SDL
   dummy drivers).
8. **Commit in logical chunks** with clear messages as you finish each task
   group; push the working branch. Do not open a PR unless asked.

---

## PHASE 1 — UPDATE EXISTING CONTENT (descriptions, dialogue, item placement)

> All of these **modify, relocate, or cut** existing content. Do every one.
> Cross-reference the matching `GAME_CHANGES.md` item for full detail.

### 1.1 — Ledger → the Lodge front desk (cut the cellar copy)  *(GAME_CHANGES §1)*
- Add a **front-desk register** interactable at the Arcadia lobby; evidence
  #3 `the_ledger` fires on **re-reading** it (reuse/trim the existing copy).
- **Cut** the cellar ledger in `basement` (`scenes/house.py` — loose panel,
  interactable, evidence text).
- **Cut** Sable's "register down in the cellar / hatch under the kitchen"
  line (`scenes/dialogue.py` visit-2).
- Decide the now-empty `basement` scene's fate (repurpose as atmosphere or
  seal the hatch) — don't leave a dead evidence-less room.
- Keep `the_ledger` in `CANONICAL_EVIDENCE`. **Guard:** ledger fires at the
  desk, not the cellar.

### 1.2 — Mr. Sable → the most-attuned **local**  *(GAME_CHANGES §2)*
- Reframe his characterization comment from "a newcomer who came early" to
  the **most-attuned local** (dreamed the door longest, unconsciously kept
  the inn ready; menace is **compulsion, not conspiracy**).
- His lines mostly survive; ensure nothing tags him **newcomer/recruiter**
  or implies he *schemes*. Any car/leaving mention stays **deniable** (the
  Sheriff carries the plain truth). **Guard:** Sable is a local.

### 1.3 — Royce has **stopped** driving out  *(GAME_CHANGES §3)*
- Rewrite Royce (`scenes/brimley.py`) from active ("Drove the river
  road… came right back") to **given-up / broke him**. **Keep** *"You came
  IN. How did you come in?"*

### 1.4 — Mrs. Calder → a guest she **can't name**  *(GAME_CHANGES §4)*
- Replace the husband's-plate lines (`scenes/brimley.py`) with the
  **unnameable-guest** beat (she sets a place, doesn't know why; no vanished
  husband — that read as perceptible individual loss, forbidden by §1b).

### 1.5 — Toby → the clue is **go down the well**  *(GAME_CHANGES §5)*
- Sharpen Toby's account (`scenes/dialogue.py`): he saw **Mara *and the
  other cultists*** descend the well in the **procession**, **before the
  rite** — so it reads as *the way down is the well.*

### 1.6 — Playscript → the **cult's own notes** (RESKIN ONLY)  *(GAME_CHANGES §6, wrapper only)*
- Reskin the item def (`systems/items.py`): display name + description away
  from "A Yellow Playscript" toward **the cult's own notes**, **keeping** the
  mask-shaped-recess line on the cover.
- Reskin the pickup fiction at the Scriptorium desk (`scenes/well.py`).
- Adjust Toby's "that yellow book" reaction wording if needed.
- **Do NOT author the buried-lore *contents* of the notes** — that is Phase
  2. This task is the wrapper/description only.

### 1.7 — Keystone-to-door rework (relocate where the items are spent)  *(GAME_CHANGES §7)*
- **Deep Stair** (`works_deepstair`, `scenes/well.py`): stop **consuming**
  `playscript` + `sigil_rubbing`. Gate on **having** them; open the stair +
  snap the rope (`well_rope_broken`, `deepstair_open`) but leave the items
  in inventory.
- **Threshold** (`scenes/depths.py build_threshold` / the `threshold`
  scene): the SEAL press now **requires + consumes the keystone** (Mask +
  notes), then `_play_ending("seal_threshold")`.
- Decide combine semantics (merge into one object, or travel together) —
  either is fine; the door needs **both** present. Keep both keys.
- Confirm **SPREAD** (`_begin_car_escape`/`escape_alone`) still reads as
  carrying the keystone **out**. **Guards:** stair does NOT consume the
  keystone; Threshold seal **requires** it.

### 1.8 — Awareness-model dialogue sweep  *(GAME_CHANGES §11)*
- Sweep cast dialogue for any line implying claiming is **perceptible** or
  happens by **individual descent** (the Calder husband + the old Tisdale
  "dad went down" line were the offenders). Convert/cult lines may show
  **compulsion-certainty** ("I gave myself… I don't know why I'm sure") but
  must never explain the cosmology. **No visible tell** between claimed and
  unclaimed; visible wrongness is the **rot/folds**, not the people.

---

## END-OF-PHASE-1 GATE

When 1.1–1.8 are done:
1. `compileall` + `tests/smoke.py` + `tests/flow.py` all green (with the new
   guards added).
2. Commit + push the working branch.
3. Post a concise summary: each task's outcome, any default decisions you
   made, anything you couldn't resolve.
4. **STOP. Do not start Phase 2. Wait for human review.**

---

## PHASE 2 — DO NOT START (listed for context only)

These **add new content/systems**; they are out of scope until Phase 1 is
reviewed and approved.

- **2.1 — Author the buried lore inside the cult's notes** *(GAME_CHANGES
  §6, content)* — fragmentary, longing, unreliable *testimony the game never
  confirms*. Never the author's voice; never "dimension."
- **2.2 — Mask = "permission to leave" + escalating distressed PI notes**
  *(GAME_CHANGES §8)* — a narrator/case-note beat on Mask pickup, built up by
  notebook entries (stored as `notes`, not `evidence`) that grow more
  desperate down the descent, tempting SPREAD over going deeper.
- **2.3 — Ashfall infestation layer** *(GAME_CHANGES §9)* — drifting
  pale-yellow ash scaling with `_infest_stage()`, denser near the source,
  **never on the Threshold**.
- **2.4 — Lure-chain unease + the lucky/delighted King** *(GAME_CHANGES
  §10)* — a faint "why did I take this one" notebook touch; where His POV is
  felt, the texture of a vast thing that **got lucky** finding the right
  hand. Never the chain spelled out.
- **2.5 — Rev. Asa Crane dialogue/murder rework** *(GAME_CHANGES §12)* —
  lore unchanged; settle the new presentation **with the user** before
  writing.
