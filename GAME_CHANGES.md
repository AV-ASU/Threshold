# THRESHOLD — GAME_CHANGES (canon-alignment TODO)

> **What this is.** The 2026-06 narrative-alignment pass (settled with the
> user) locked a batch of story decisions. `NARRATIVE.md` is the **canon**;
> this file is the remaining **code work** to make the *game* match. Each
> item: the change, the canon reason, the **where** (file:line from the
> 2026-06 audit — verify before editing, lines drift), and acceptance.
>
> **Process (CLAUDE.md "Working agreements"):** cross-check every line
> against `NARRATIVE.md` BEFORE writing; one edit at a time on a shifting
> file; run `compileall` + `tests/smoke.py` + `tests/flow.py` green before
> commit; add a `tests/flow.py` guard when you lock a canon fact.

---

## ✅ Phase 1 — DONE (branch `claude/threshold-phase-1-canon-y6oZT`)

Update-existing-content pass: descriptions, dialogue, item placement.
Implemented + verified (compileall + smoke + flow green; canon guards added).
*Old §-numbers in parens, for cross-reference with older notes.*

1. **Ledger → the Lodge front desk** *(§1)* — sign the register on arrival;
   evidence #3 `the_ledger` fires on **re-read** at the desk. Cellar loose-panel
   copy + Sable's cellar pointer cut; the `basement` scene kept as the
   woodshed-key gate + candle-devotion atmosphere (not a dead room).
2. **Sable → the most-attuned local** *(§2)* — menace is compulsion, not
   conspiracy; nothing tags him newcomer/recruiter; car talk stays deniable.
3. **Royce has stopped driving out** *(§3)* — given-up past tense; kept *"You
   came IN. How did you come IN?"*
4. **Mrs. Calder → a guest she can't name** *(§4)* — unnameable-guest beat;
   the vanished husband is cut.
5. **Toby → the well clue** *(§5)* — Mara **and the other cultists**, in the
   **procession**, **before the rite**, down the **well**.
6a. **Playscript → the cult's own notes — WRAPPER ONLY** *(§6, wrapper)* —
   display name (`The Cult's Notes`) + description + Scriptorium pickup +
   Toby's reaction reskinned; item key `playscript` + save flag kept; the
   **mask-shaped recess** kept. *(The buried-lore CONTENTS are Phase 2 — §6b.)*
7. **Keystone-to-door rework** *(§7)* — the Deep Stair gates on **having** the
   keystone and opens/snaps-rope **without consuming** it; the **Threshold**
   seal now **requires + consumes** the Mask+notes at the door; SPREAD carries
   the Sign out. Guards: stair does not consume; seal requires it.
8. **Awareness-model dialogue sweep** *(§11)* — no perceptible-claiming /
   individual-descent leaks (Calder husband + Tisdale "dad" lines were the
   offenders); compulsion-certainty allowed, cosmology never explained.

> **Minor, deferred (not Phase 2, just noted):** a non-player registry comment
> in `scenes/__init__.py` still calls the schoolhouse "empty since the town's
> children vanished." Reads as stasis, not perceptible claiming, so left as-is;
> scrub the "vanished" framing if you want §1b strictness.

---

## Phase 2 — remaining (adds new content/systems)

> **State (2026-06):** §8 and §9 are DONE (below). §10 is a standing
> constraint, not a task. The genuinely-open work is **§6b buried lore** and
> **§12 Crane** (gated on a design conversation).
>
> These **author new prose or build new systems**. The hard part is the
> NARRATIVE §1b discipline: cosmic truth arrives **only as sensation** — never
> the word "dimension," never the door explained, the King **lucky not
> omniscient**. Add a `tests/flow.py` guard for every new note that locks a
> canon fact (mirror the existing `the_dream` / `the_case` guards: forbid
> "dimension"/"lure"/"bait"/"the king", assert it never inflates evidence).

### 6b. Author the buried lore inside the cult's notes  *(NARRATIVE §4, §9)*

The wrapper is done (§6a). What's left is the **contents**: the
congregation's own compulsive, unreliable, partial record — the longing, the
compulsion, the dig, the bargain — as **unconfirmed testimony the game never
confirms.** Never the author's voice; never "dimension."

- [ ] Author the buried lore as fragmentary, longing, unreliable testimony.
  Surface it where the notes are read/referenced (Scriptorium pickup expands;
  optional re-read beats). Keep it *felt*, never expository.

### ✅ 8. Mask = "permission to leave" + the PI's distressed notes — DONE

Landed in the post-Phase-1 feel/voice pass (confirmed in code, not just docs).

- [x] **On Mask pickup** (`_take_mask`, `scenes/well.py`): the "His face is the
  way OUT" temptation fires off the evidence dialog's completion via
  `_descent_voice("descent_mask")` (a `notes` beat, never `evidence`).
- [x] **Escalating distress:** the PI's interior voice (`_DESCENT_VOICE` /
  `_descent_voice` in `systems/game.py`) seeds the want-to-leave pressure down
  the descent; the Playscript carries the King's pull to take the Sign OUT.
- [x] **Spread off-ramp reachable/legible** at the moment of temptation (turn
  back at the Deep Stair, climb out) — the choice is real, not theoretical.

### ✅ 9. Ashfall — the infestation made airborne — DONE  *(NARRATIVE §4b)*

**Canon:** a slow **drifting pale-yellow ashfall** scales with evidence (light
at stage 1 → steady yellow drift at 3), denser near the source, **never on the
Threshold** — the vessel's pressure made visible, His attention settling on
you. (Not snow, not weather.)

- [x] Screen-space mote field (`_tick_ashfall` / `_draw_ashfall`, `ASHFALL_*`
  constants) driven by `_infest_stage()` via `_ashfall_target()`: zero at stage
  0, light→steady by stage 3, ×1.7 underground (the source), clean in safe
  rooms until stage 3, **never on `threshold`**. Procedural, drawn over the film
  grade so the jaundiced tint reads. Preview: `tools/preview_ashfall.py`.
  Canon-guarded in `tests/flow.py` (§22).

### 10. The lure chain — NOT A TASK, a standing constraint  *(NARRATIVE §1)*

This is **not open work**; it is a fence. The bible is explicit: *"None of this
is ever stated in the game — it is felt only as the PI's own unease in the
notebook: I couldn't tell you why I took this one."* The lone diegetic touch
(`the_case` note) **already exists.** Do **not** "build on it" — the safe
version is one faint unease, never elaborated. There is no King POV to author
(he is the faceless everting mass, no dialogue). Treat this as a guardrail:

- **Never state the chain** (King → Mara → Walter → PI) anywhere diegetic.
- **King/Watcher moments read as luck, not omniscience** — gloating chance, the
  rare break of a vast thing finding exactly the right hand. He is powerful,
  **not** infallible. Keep the seam of chance in any moment His reach is felt.

### 12. Rev. Asa Crane — dialogue/murder rework (lore unchanged)

**Canon (NARRATIVE §2):** unchanged — local dissenter who **names the cult**
from his pulpit, murdered for it (evidence #4, his cross). Only the
**presentation** (his dialogue + the murder beat) is up for a rework.

- [ ] **Settle the new presentation with the user before writing.** Revisit
  Crane's lines + the `preacher_doomed` → gutted-on-the-floor reveal for
  impact. No lore change.

---

## Status / sequencing notes

- **Phase 1 is done + pushed.** Docs (`NARRATIVE.md`, `CLAUDE.md`) already
  reflect the settled canon; this file now tracks only the Phase 2 remainder.
- **Coupling:** §6b is the **PI's interior voice** (the `notes` system); §8 (its
  sibling) already landed, so keep §6b in that same escalating-arc tone. §9
  (ashfall) is done. §12 is gated on a design conversation. §10 is a fence, not
  a ticket. So only §6b + §12 remain.
- Verify against `NARRATIVE.md` first; keep `tests/flow.py` green and add a
  guard as each canon fact locks.
