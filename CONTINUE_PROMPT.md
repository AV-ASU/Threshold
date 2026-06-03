# PROMPT — continue THRESHOLD (new chat)

> Paste this to start a fresh chat. You're picking up an in-progress
> collaboration on **THRESHOLD** — story/design work plus a queued
> implementation pass. Everything referenced below is on `main`.

## The project
THRESHOLD — a top-down narrative-horror game in **pygame**, every sprite
**procedural** (no art pipeline). Core loop: stealth/dread (walk, watch,
hide) driven by a **visibility** meter feeding the **King in Yellow**. The
story is the point; the bible is the source of truth.

## Read these first, in order
1. **`NARRATIVE.md`** — the narrative bible (authoritative canon).
2. **`GAME_CHANGES.md`** — the code TODO to make the game match the
   just-settled canon (per-task `file:line` pointers).
3. **`PHASE1_PROMPT.md`** — a ready-to-run execution prompt for Phase 1.
4. **`HANDOFF.md`** (session history) and **`CLAUDE.md`** (dev commands +
   "Working agreements").

## Where we are (2026-06)
A collaborative **narrative canon-alignment pass** just finished. All
decisions are written into `NARRATIVE.md` and merged to `main`. **No game
code has changed yet** — the implementation is queued as Phase 1.

What got settled this pass (all in the bible now):
- **The lure is an engineered chain** — King → (claimed) Mara → her father
  Walter → the marked PI — but **He is powerful, not omniscient: He got
  lucky and was delighted.** Felt, never stated.
- **Awareness model:** no *visible* difference between claimed and
  unclaimed (visible wrongness = the rot/folds); the **cult knew the gist**
  of its bargain, the **locals never knew** they were claimed.
- **The rite seals AND feeds Him** (Brimley is His power-bank); the PI's
  arrival is the first thing that can decide its fate.
- **Cast:** Sable is the **most-attuned local** (not a newcomer); Royce
  **stopped** driving out; Mrs. Calder sets a place for a **guest she can't
  name**; Toby's witness is the **clue to descend the well**.
- **Ledger → the Lodge front desk** (cellar copy cut).
- **Playscript → the cult's own notes** (buried lore as unconfirmed
  testimony); keeps the mask-recess for the keystone.
- **Keystone-to-door fork:** Mask + notes **combine**; the Deep Stair opens
  *without consuming* them; the keystone is carried down and **spent at the
  Threshold to SEAL**; carrying it out = SPREAD. The Mask reads as
  **"permission to leave,"** built on the PI's escalating distressed notes.
- **Ashfall** infestation layer.

## Open decisions the user may want to revisit (do NOT silently resolve)
- **Royce:** canon says he *stopped* driving out. The assistant argued the
  weekly-failed-drive (a Sisyphus image) is stronger and more haunting.
  User has not reversed it — flag it, don't assume.
- **Mrs. Calder:** canon says *unnameable guest* (husband cut for §1b
  consistency). The assistant argued the **husband-lost-to-the-road** is
  better drama *and* arguably canon-compliant (the **fold** ate him —
  spatial, perceptible — not the invisible *claiming*), and that
  "unnameable preparation" now duplicates Sable's beat. Unresolved.
- **Direction:** the canon is deep and self-consistent, but the *in-room
  craft* (the liminal-composition pass, sightlines, the actual moment-to-
  moment feel) keeps getting deferred. The assistant's standing advice:
  before deepening canon further, **build ONE fully-realized scene** to
  test whether the iceberg actually transmits to the player.

## How to continue — ask the user which
- **A. Execute Phase 1** — run `PHASE1_PROMPT.md` (update existing
  dialogue/descriptions/item placement; nonstop; **HARD STOP before Phase
  2**).
- **B. Keep refining canon/design** — continue the collaborative narrative
  work; settle the open decisions above first.
- **C. Prove a scene** — build one fully-realized room (composed emptiness,
  ashfall, Sable's compulsion, the Mask temptation) to test the feel.

## Working style the user expects
- **Collaborative and opinion-wanted.** Give honest assessments including
  disagreement; no flattery. When asked your take on direction, give a real
  one grounded in the actual content.
- **Settle threads, then restate for approval** before changing docs.
- Tone is bleak, ironic, grimdark (Darkwood + Fear & Hunger). The user likes
  dark irony (e.g. a cosmic entity that still has to get *lucky*).
- **Iron rules:** verify narrative against `NARRATIVE.md` before writing;
  **never write "dimension"** or explain the door (truth = sensation); item
  + scene **keys are load-bearing** (only fiction changes); green
  `compileall` + `tests/smoke.py` + `tests/flow.py` before every commit; add
  a flow.py guard when a canon fact locks.
- The user likes artifacts **merged to `main`** so any chat can access them.
