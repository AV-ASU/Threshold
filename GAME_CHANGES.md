# THRESHOLD — GAME_CHANGES (canon-alignment TODO)

> **What this is.** The 2026-06 narrative-alignment pass (settled with the
> user) locked a batch of story decisions. `NARRATIVE.md` now reflects the
> **canon**; this file is the **code work** to make the *game* match. Each
> item: the change, the canon reason, the **where** (file:line from the
> 2026-06 audit — verify before editing, lines drift), and acceptance.
>
> **Process (CLAUDE.md "Working agreements"):** cross-check every line
> against `NARRATIVE.md` BEFORE writing; one edit at a time on a shifting
> file; run `compileall` + `tests/smoke.py` + `tests/flow.py` green before
> commit; add a `tests/flow.py` guard when you lock a canon fact.

---

## 1. The Ledger → the Lodge front desk (cut the cellar copy)

**Canon (NARRATIVE §4, §5):** one Ledger, on the **front desk** — the
register Sable has you sign on arrival; the evidence lands when you
**re-read** it. The old cellar copy behind a loose panel is **cut**.

- [ ] **Move evidence #3 to the desk.** Add a front-desk register
  interactable at the Arcadia (the Lodge lobby/`son_room` area). On
  arrival, a light "sign the register" beat; later, **re-reading it** fires
  `_evidence(game, "the_ledger", [...])` (reuse/trim the existing copy).
- [ ] **Cut the cellar ledger.** Remove the loose-panel ledger in
  `basement` — `scenes/house.py` (~`_wall_panel_pos` L610, interactable
  L614, evidence text L717–727).
- [ ] **Cut Sable's cellar pointer** — `scenes/dialogue.py` visit-2 lines
  (~L316–320): *"there's an old guest register down in the cellar. Hatch
  under the kitchen."* Replace with a desk-register nudge or drop.
- [ ] **`basement` scene fate.** With the ledger gone the cellar may be
  empty. Decide: repurpose as atmosphere (the tallow/candle-devotion beat
  in §8 of NARRATIVE already lives near here) or close the hatch. Don't
  leave a dead evidence-less room that still looks like it should hold
  something.
- [ ] **Keep `the_ledger` in `CANONICAL_EVIDENCE`** (`scenes/dialogue.py`
  L18) — only its *location* changes; the evidence key/gate is unchanged.
- [ ] **flow.py guard:** ledger fires from the desk, not the cellar.

## 2. Mr. Sable → the most-attuned **local** (not a newcomer)

**Canon (NARRATIVE §2):** Sable is a **local** — dreamed the door longest,
**subconsciously preparing**, keeps the desk/guests. Menace is
**compulsion, not conspiracy**: certainties he can't explain. He handles
the stranded car **deniably**; the **Sheriff** carries the plain truth.

- [ ] Reframe his characterization comment — `scenes/dialogue.py` (~L288–289
  *"A newcomer who came early and stayed to keep the door"*) → most-attuned
  local.
- [ ] His existing lines mostly survive (they read as compulsion already).
  Make sure nothing tags him a **newcomer/recruiter** or implies he
  *schemes*; lean into "says things he can't account for."
- [ ] If he ever speaks to the car/leaving, keep it **deniable** (no plain
  admission). The Sheriff (Hollis Vane) is the one who says *it's the town*.
- [ ] **flow.py guard:** Sable is a local; no "newcomer" tag on him.

## 3. Royce has **stopped** driving out

**Canon (NARRATIVE §2):** Royce **tried for weeks**, the corn handed him
back every time, the futility **broke him**; he's *stopped*. He still
clings to the one fact he can't square: *you got* **in** — how?

- [ ] Rewrite Royce — `scenes/brimley.py` (~L705–712). Current lines are
  active/present-tense (*"Drove the river road… Came right back"*). Move to
  past tense / given-up. **Keep** *"You came IN. How did you come IN?"*

## 4. Mrs. Calder sets a place for a guest she **can't name**

**Canon (NARRATIVE §2):** not a vanished husband — a certainty she can't
explain that **someone is coming**; she doesn't know why she does it.

- [ ] Rewrite Mrs. Calder — `scenes/brimley.py` (~L698–704). Replace the
  *"My husband walked to the highway… I set his plate"* lines with the
  unnameable-guest beat. Drop the husband entirely (his disappearance read
  as *individual descent*, which §1b forbids being perceptible).

## 5. Toby → the clue is **go down the well**

**Canon (NARRATIVE §2):** Toby saw **Mara *and the other cultists*** go
down into the well, in the **procession**, **before the rite** — his
witness is the player's **clue to descend**.

- [ ] Sharpen Toby's account — `scenes/dialogue.py` (~L127–130). Current:
  *"She walked to the well. She climbed down. I saw her."* Add the
  **others/procession** and the **before-the-rite** timing so it reads as
  *the way down is the well.*

## 6. Playscript → the **cult's own notes**

**Canon (NARRATIVE §4, §9):** not "the Play"/liturgy — the congregation's
**own compulsive, unreliable, partial record** of what they feel and think
they understand. It's our **vehicle for buried lore as testimony the game
never confirms.** Keep item key `playscript`; keep the **mask-shaped recess**
on the cover (for the keystone, §7).

- [ ] Reskin the item def — `systems/items.py` (~L58–61): display name +
  description away from "A Yellow Playscript / playscript" toward *the
  cult's notes / journal-of-the-claimed*, **keeping** the mask-recess line.
- [ ] Reskin the pickup fiction — `scenes/well.py` (~L399–408, the
  Scriptorium desk): *"one book is bound and whole…"* → their bound notes
  among the loose copies.
- [ ] Author the **buried lore** into the notes (the longing, the
  compulsion, the dig, the bargain) as **unconfirmed testimony** — never
  the author's voice, never "dimension." Fill during writing.
- [ ] Toby's reaction (`scenes/dialogue.py` ~L132–137, *"That yellow book…
  don't open it where I can see"*) still works; adjust wording if needed.

## 7. Keystone-to-door rework (Mask + notes → the door)

**Canon (NARRATIVE §6, §7, §9):** lifting the **Pallid Mask** (Sign
Chamber) **combines** it with the cult's notes into the single
**keystone**. The **Deep Stair opens to the keystone pressed to the stone
WITHOUT consuming it** (and snaps the rope — point of no return). You
**carry the keystone down** and **spend it at the Threshold door to SEAL.**
Carrying it back out instead is **SPREAD.** *(Current build consumes both
items at the Deep Stair and seals empty-handed — that is the change.)*

- [ ] **Deep Stair** (`works_deepstair`, `scenes/well.py` on_interact):
  stop consuming `playscript` + `sigil_rubbing`. Gate on **having** the
  keystone; open + snap rope (`well_rope_broken`, `deepstair_open`) but
  leave the items in inventory.
- [ ] **Threshold** (`scenes/depths.py build_threshold` on_interact / the
  `threshold` scene): the SEAL press should now **require + consume the
  keystone** (Mask+notes), then `_play_ending("seal_threshold")`. Today it
  seals empty-handed — re-point it at the keystone.
- [ ] **SPREAD** (`_begin_car_escape` → `_play_ending("escape_alone")`)
  already gates on the Sign (`sigil_rubbing`) — confirm it still reads as
  "carry the keystone out," post-rework.
- [ ] **Combine semantics:** decide if Mask+notes literally merge into one
  inventory object or just travel together. Either works; the door needs
  *both* present to seal. Keep keys `playscript` + `sigil_rubbing`.
- [ ] **flow.py guards:** the Deep Stair does NOT consume the keystone; the
  Threshold seal requires it; Spread carries it out.

## 8. Mask = "permission to leave" + the PI's distressed notes (the temptation)

**Canon (NARRATIVE §6):** taking the Mask triggers a quiet narrator/
case-note beat — *with this, the town will let me out* — pulling toward the
**off-ramp (SPREAD).** It's **built up** by the PI's notes growing steadily
more **distressed** across the descent (he wants out). Going **deeper
instead** is the harder road.

- [ ] **On Mask pickup** (`works_sign`, `scenes/well.py`): fire a
  narrator/PI-note beat conveying *permission/authority to leave* (don't
  copy the example line verbatim — see §6).
- [ ] **Escalating distress:** seed a few case-notebook entries down the
  Works/Depths that build the want-to-leave pressure (stored as `notes`,
  NOT `evidence` — mirror `_log_dream_entry`). Pace them so the Mask's
  "you can go now" lands on a primed player.
- [ ] Make sure the **Spread off-ramp is reachable/legible** at the moment
  of temptation (turn back at the Deep Stair, climb out) so the choice is
  real, not theoretical.

## 9. Ashfall — the infestation made airborne

**Canon (NARRATIVE §4b):** a slow **drifting pale-yellow ashfall** scales
with evidence (light at stage 1 → steady yellow drift at 3), denser near
the source, **never on the Threshold** — the vessel's pressure made
visible, His attention settling on you. (Not snow, not weather.)

- [ ] Add an ashfall overlay driven by `_infest_stage()` (hook near
  `_apply_infestation` / the world draw). Exempt `threshold`. Tune density
  by stage. Procedural (no assets). Preview headlessly before committing.

## 10. The lure chain — felt, never stated

**Canon (NARRATIVE §1):** King → (claimed) **Mara** → her father **Walter**
→ the **marked PI.** Walter real + unwitting. **He is powerful, not
omniscient — He got lucky and was delighted** (opportunism that worked, not
clockwork; keep the seam of chance). **Never stated in-game** — surfaced
only as the PI's unease.

- [ ] Add/keep a faint case-notebook touch: *I couldn't tell you why I took
  this one.* Do **not** spell out the chain anywhere diegetic.
- [ ] Where His POV is ever *felt* (an erupting King, a Watcher fixing on
  you), let it read as **gleeful recognition / luck** — He found exactly the
  right hand — not omniscient inevitability. Never explain; just the texture
  of a vast thing that got *lucky*.

## 11. Awareness model — verify dialogue (no visible tell; cult knew the gist)

**Canon (NARRATIVE §1b):** **no visible difference** between claimed and
unclaimed; visible wrongness = **rot/folds**, not people. The **cult knew
the gist** of its bargain (gave themselves over for the answer), didn't
know/care the rite swept up the oblivious **locals**, who never knew they
were claimed at all.

- [ ] Sweep cast dialogue for lines implying claiming is **perceptible** or
  happens by **individual descent** (the Calder husband and the old Tisdale
  "dad went down" line were the known offenders — latter already cut).
- [ ] Cult/convert lines may show **compulsion-certainty** ("I gave myself…
  I don't know why I'm sure") — but never explain the cosmology.

## 12. Rev. Asa Crane — dialogue/murder rework (lore unchanged)

**Canon (NARRATIVE §2):** unchanged — local dissenter who **names the
cult** from his pulpit, murdered for it (evidence #4, his cross). Only the
**presentation** (his dialogue + the murder beat) is up for a rework.

- [ ] Open: revisit Crane's lines + the `preacher_doomed` → gutted-on-the-
  floor reveal for impact. Settle the new presentation with the user before
  writing. No lore change.

---

## Status / sequencing notes

- **Docs are done** (this session): `NARRATIVE.md` rewritten to the settled
  canon; `CLAUDE.md` pointer added; this file created.
- **None of the code above is implemented yet** — these are the next-session
  tasks. Independent items (1–6, 9–11) can land piecemeal; **7 + 8** are the
  coupled keystone/fork rework and should land together.
- Verify against `NARRATIVE.md` first; keep `tests/flow.py` green and add
  guards as canon facts lock.
