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

1. **Ledger → the PADLOCKED Lodge cellar** *(§1; re-decided 2026-07,
   superseding the front-desk placement below)* — sign the register on
   arrival; the desk **re-read is only a LEAD** (a clean new book; the
   full ones went below). The **cellar key hangs on a nail behind the
   house** (yard walk-over pickup); carrying it turns the padlock on the
   kitchen hatch once; evidence #3 `the_ledger` fires reading the boxed
   **old registers** on the cellar crates. Sable still never points at
   the cellar (flow-guarded). *(2026-06 text, for history: front desk,
   evidence on re-read; cellar loose-panel copy cut.)*
2. **Sable → the most-attuned local** *(§2)* — menace is compulsion, not
   conspiracy; nothing tags him newcomer/recruiter; car talk stays deniable.
3. **Royce has stopped driving out** *(§3)* — given-up past tense; kept *"You
   came IN. How did you come IN?"*
4. **Mrs. Calder → a guest she can't name** *(§4)* — unnameable-guest beat;
   the vanished husband is cut.
5. **Toby → the witness clue** *(§5)* — Toby **followed the night procession
   down the river** to the cult's dug-open ground and saw them go below (D
   rework, 2026-07): the **sole witness** of where they went. His witness
   poses the descent question (a way **no one can follow now** — the grove is
   fold-hidden; only the rite reaches it) and **seeds the school** (the commune
   he watched empty out; the actionable route is the rite). He does not know
   *why* they dig; given the town's state he's sure the evil is down there.
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
> constraint, not a task. **§6b is now DONE** (the three testimony fragments,
> the Mask-only keystone, mining cultists + rite-holder — all in code and
> flow-guarded). **§12 Crane is DONE** (murder-beat polish optional). **§13
> (the calendar sweep around April 14) is DONE.** The one open item is
> **§17 (the ancient altar, 2026-07)**, which lands with the Brimley
> compression pass.
>
> These **author new prose or build new systems**. The hard part is the
> NARRATIVE §1b discipline: cosmic truth arrives **only as sensation** — never
> the word "dimension," never the door explained, the King **lucky not
> omniscient**. Add a `tests/flow.py` guard for every new note that locks a
> canon fact (mirror the existing `the_dream` / `the_case` guards: forbid
> "dimension"/"lure"/"bait"/"the king", assert it never inflates evidence).

### ✅ 6b. The cult's notes → THREE testimony fragments + Mask-only keystone — DONE  *(NARRATIVE §4, §1b; design settled 2026-06)*

**Design settled with the user (this supersedes §6a's single-notebook wrapper
AND the §7 "Mask + notes" keystone).** Two decisions:

1. **The keystone is the Pallid Mask ALONE.** The notes are decoupled from the
   endgame entirely. SPREAD already gated on the Mask item alone (then keyed
   `sigil_rubbing`; renamed `pallid_mask` 2026-07, disk slots migrate); now the
   **Deep Stair** gate (`scenes/well.py`) and the **Threshold seal**
   (`scenes/depths.py`) do too. This makes the fork symmetric and removes a
   soft-lock surface. See §7 (now Mask-only).
2. **The single `playscript` item is retired and replaced by THREE collectible
   lore fragments** (3 new keys; saves are in-memory so no migration). They are
   **pure lore, gate nothing.** Placement: **1 on the critical path**
   (Scriptorium) + **2 optional** (a Works side room, a Depths side room).

**Structure (locked):** the **cult's own voice lives in the item DESCRIPTION**
(flat label `Cultist personal testimony:` + 2 separate quotes, rendered on
their own lines); the **PI's reaction is logged to `notes`** on pickup (never
`evidence`). The aches are **solvable problems** (a debt, an addiction, a
broken back — a longing for a *solution*), never grief/necromancy. The arc
escalates: **a human problem → the bargain → the self dissolved into
obsession.** Approved final text:

- **The Calling** (`cult_calling`, Scriptorium, crit-path)
  - *desc:* "Cultist personal testimony:" / "I had been drinking for eleven
    years. I quit a hundred times and never once stayed quit. Then I dreamed of
    a door, and a voice that said it could take it from me clean. I have not
    touched a drop since I came." / "The bank took the farm in the spring. By
    summer I was dreaming the same dream as a hundred strangers, and every one
    of us was already driving north to the same town."
  - *notes:* "Every hand different. Every one of them grateful. I keep waiting
    for the page where somebody admits they were tricked. It isn't here."
- **The Bargain** (`cult_bargain`, a Works side room)
  - *desc:* "Cultist personal testimony:" / "My back has been broken nine years.
    He says I will stand straight the day our work is finished. We are nearly
    finished. Soon we can all help ourselves." / "He asks so little of us. Only
    everything, and only the once."
  - *notes:* "They write about the bargain like a debt almost paid off. Not one
    of them can say what they put up for it, only that the last payment is
    close. I never took a confession this happy."
- **The Digging** (`cult_digging`, a Depths side room, deepest)
  - *desc:* "Cultist personal testimony:" / "There are only a few feet of earth
    left between us and the door now. We dig in shifts so the work never stops,
    one hand on the rite, one hand in the dirt. We have only to reach the door."
    / "I do not sleep. I dig. We hold the rite and we dig and we do not stop.
    Almost there. Almost. The door. The door. The door."
  - *notes:* "The last pages stop being sentences. Just the word door, over and
    over, pressed hard enough to tear the paper. Whatever these people used to
    be, the digging finished it."

**New scene content (user request, same pass): ambient NON-REACTIVE cultists.**
- **Mining cultists** — cultists DIGGING in the deep, who **never react to the
  player**: no chase, no grab, and **no gaze / no visibility rise**. Pure
  ambient labor (the obsessive dig made visual; pairs with The Digging).
- **The rite-holder** — a cultist **kneeling at the Sign Chamber altar with the
  Mask**, also fully non-reactive. The closing-rite tableau made present (this
  is the §1b "the rite claims the collective" beat, shown not told).
Both need a passive sprite-only NPC mode that is excluded from the cultist-gaze
visibility tick. (`cult_convert` is gaze-only-passive; these go further: NO
gaze at all.)

**Other unsurfaced-lore beats from the same review (delivery assigned):**
- River as the diggers' road → environmental decal in the water room (no text).
- Townsfolk drain ("so tired lately, the whole town is") → 1-2 locals' idle
  lines; the "Brimley is His battery" feeding, felt never named.
- **Mrs. Calder** → the set place she waits at for a guest she can't name
  ("Is it you? ... No, this could not be for you. I will know Him when He
  comes.").
- **Mr. Sable** → fulfilled while the town dims ("never felt more fulfilled...
  every room spoken for... not one of them seems to be about. Nobody leaves the
  Arcadia.").
- **Mara** → made the named, human face of the anonymous testimony: journal
  carries the late-arrival arc ("I was the last one in... it took me one
  winter... the first thing that ever fit"); hive recognition lands evidence #6
  ("There was never anyone down here to save. I am exactly where I meant to end
  up.").

**Cut from the missing-lore list (already handled, do NOT add text):** the
admits-but-never-releases geometry (the looping world + townspeople), the
Watcher-as-His-gaze (the visibility climb *is* the statement), and Carcosa as
the inside of Him (the death cutscene already is this).

- [x] items.py: retire `playscript`, add the 3 keys (desc above); Mask desc → standalone keystone.
- [x] well.py: Scriptorium gives `cult_calling`; place `cult_bargain`; Deep Stair → Mask only; rite-holder at the altar.
- [x] depths.py: Threshold seal → Mask only; place `cult_digging`; mining cultists.
- [x] notes-log each pickup; move the carrying-haze/leave-pull from playscript to the Mask; repoint the Toby line.
- [x] Calder (set place, hope-then-deflation, never names the guest), Sable
  (fulfilled while the town dims; rooms full but no one about), townsfolk drain
  (Old Pell: the town "drawn out of us, slow"), Mara (hive recognition sharpened
  to the #6 payoff; late-arrival journal page in her cell). All canon-guarded.
- [x] River-as-the-artery, shown environmentally: a WHIRLPOOL in the Brimley
  surface river (the `swallow_hole` decoration: depth rings to black + a draining
  swirl). The river keeps flowing past it, but at that spot it spirals down a
  sink in the bed -- where the surface water drains into the river running under
  the town. The Sump gets the same sink among its pools for depth + an oblique
  on-enter line ("the water goes down, you never hear it land"). NARRATIVE 1b:
  the river is the artery the water, and the diggers, followed down to the door.
- [x] NARRATIVE §4/§6/§7 subtractive edits (Mask-only); flow.py guards (seal works Mask-only; notes not evidence; no "dimension").

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

### ✅ 13. The calendar — reconcile the season around April 14 — DONE

**Canon (2026-06, settled with the user):** the present is **mid-April
1994**. The PI starts with **yesterday's paper, the April 14 issue**
(`systems/save.py` DEFAULT_SAVE; item def in `systems/items.py`; Hettie's
one-shot trade in `scenes/dialogue.py`; the date is flow-guarded in
`tests/flow.py` §23a). See NARRATIVE §1 setting note 3.

**Resolution — the seal is mid-January 1994** (the only month coherent
with "three months since the seal" + April 14 = yesterday). The full
timeline (door wakes ~April '93 → attuned from summer '93 → Mara north
in the fall → rite mid-January '94 → the PI in on April 15, 1994) is
locked in NARRATIVE §1 setting note 3, including the corn note (the
standing corn is last year's uncut stand; never call it green).

**The sweep (all landed):**

- [x] Hettie's till lines: "since the spring"/"since spring" → **"since
  the new year"** (intro + the paper trade, `scenes/dialogue.py`).
- [x] The case note (`systems/narrative_mixin.py _log_case_entry`):
  "Drove north in the spring. Stopped calling home by the thaw." →
  **"Drove north in the fall. Stopped calling home by the new year."**
- [x] Mara's cell journal (`scenes/well.py`): the rest "had been here
  the better part of a year" → **"since the summer"** (agrees with
  Vane's "they started showing up in the summer").
- [x] The threshing tithe (`scenes/depths.py`): dropped "season on
  season" (there has only been the one harvest since the cult came).
- [x] The wall-calendar prop (`entities/decoration.py _draw_calendar`):
  defaults were a stale OCT 4 from the removed day-cycle; every calendar
  in town now shows a stopped **JAN 15** card (the last day anyone
  marked). Stale "advances on each sleep" docstring cut.
- [x] NARRATIVE §1b: "crops grow" → "the ice goes out" (nothing grows
  Jan→Apr in northern Minnesota); the seal named as mid-January.
- [x] Kept as-is (already coherent): the dream/river "a year ago"
  (~April '93), Vane's "summer," the Calling testimony's "the bank took
  the farm in the spring" (spring '93), "a year of hands" (the dig has
  run since summer '93), the Ledger's "months back" sign-outs.
- [x] Flow guards (`tests/flow.py` §23a): the dead "since (the) spring"
  phrasing is locked out of the store dialogue, "since the new year" and
  the case note's "fall"/"new year" are locked in, April 14 stays.

### ✅ 12. Rev. Asa Crane — dialogue settled — DONE (murder-beat polish optional)

**Canon (NARRATIVE §2):** unchanged — local dissenter who **names the cult**
from his pulpit, murdered for it (evidence #4, his cross). Only the
**presentation** was up for a rework.

- [x] **Pulpit condemnation rewritten** (`scenes/dialogue.py` `preacher_dialogue`,
  the 2nd-conversation sermon that sets `preacher_doomed`). Crane condemns them
  as **willing** apostates, not puppets — they kept their free will and *chose*
  the bargain: "They walked down willing, every one, and sold the Lord for the
  easing of some private ache, then climbed back up calling the wound a mercy.
  Foul, the lot of them, and glad of it." Preacher's voice, not exposition (the
  old staccato well-directions were cut — Toby already carries the witness clue).
  Stays religious/moral (he never grasps the cosmic truth; §10 fence held).
- [ ] *(Optional, not requested)* the `preacher_doomed` → gutted-on-the-floor
  reveal could be punched up for impact later. No lore change.

---

### ✅ 14. The descent rework — the rope is CUT; the rite is the way down — DONE  *(2026-06; NARRATIVE §2, §4, §5, §9, §11)*

**Decision.** Act 1 and Act 2 are now separated by a player-performed
descent built on the fold system itself, gated by the evidence count.
The rope (and its woodshed pickup, and the `rope` item key) is cut.

- [x] **The Invitation** (`rite_envelope`, `systems/items.py`): the
  congregation — the Lodge guests who sign in and never out — left an
  envelope at Sable's desk when they went below. At **3 evidence** he hands
  it over (state-gated interjection at the top of `clerk_dialogue`; never
  farmable by repeat visits) + the PI's `the_invitation` NOTE. **Canon
  shift:** Sable holds it *knowingly*; his complicity stays hospitality,
  never scheme (flow-guarded: no recruiter language).
- [x] **The school rite** (`scenes/threshold_extras.py`): chalk on the
  teacher's desk + incense among the cot relics; burn the incense at the
  commune's indoor campfire, then draw the **final, smallest door** on the
  chalkboard → the school↔grove fold opens permanently (`school_door_open`).
- [x] **The grove descent fold** (`scenes/hidden_folds.py`): a rift stands
  over the dead fire in `effigy_grove`, **clarity = evidence count**
  (`fold_charge_fn`, 0.15→1.0), crossable only at 3 (`exit_gate_fn`) →
  lands at `well_bottom`; a symmetric **return pane** stands at the shaft
  floor where the rope hung. The grove was rebuilt as a **crop circle
  deep in the corn** (18×13): the corn itself is the border (an oval
  clearing in solid stalks — the old tree wall + canopy dressing is cut),
  with **three organic standing stones** (seeded `standing_stone` deco,
  solid see-over footprints) around the ring and the nailed-up faces
  moved onto the north-west stone. It now takes infestation decals (the
  rot and the way down escalate on the same dial).
- [x] **The cauldron is removed GAME-WIDE** (it was eat-cult imagery, §1b
  scrub): the prop, its draw code (`entities/decoration.py`), its standee
  entry (`rendering/props.py`), and the old clearing centrepiece. The
  clearing (`void_boss`, `scenes/interiors.py`) is reworked as the **burn
  site**: the dead fire pit where the claimed burned their worldly effects
  before going below (the surface twin of the Sorting Hall's shed lives);
  its flavor beat is `the_burning` (narration only, never evidence).
  Flow-guarded: "cauldron" joins the eat-cult scrub list.
- [x] **The gate keys on EVIDENCE, never visibility** (flow-guarded): the
  grove's charge/gate read `_evidence_count()` (the six canonical beats);
  Watchers raise the visibility *floor* and can never open the way down.
- [x] **Death never seals the descent.** The old rope fiction ("death at
  the shaft floor snaps the rope") silently SOFTLOCKED a run: hp-death
  respawns in bed with flags intact, so the seal made the run
  unwinnable. Cut from `_on_player_death`; the descent seals only at the
  Deep Stair, by choice. (Pursuer-contact deaths still end the run
  outright.) The well art loses its hanging rope too (a frayed stub on
  the winch drum).
- [x] **Mask pickup recognition line** (descent_mask beat): "The origin
  of every half reflection daubed on this town's walls. The pale mask
  hums in your hand." -- the daubs pay off at the altar.
- [x] **The painted Sign is now a MASK** (`_draw_yellow_sign`,
  `entities/decoration.py`): canon says the Sign IS the Pallid Mask ("His
  face made an object", §4 #5), so the daubed glyph (the old three-armed
  curl) is replaced by a crude painted face -- broken oval, two
  thumb-press sockets, NO mouth (the flashback-mask grammar), paint runs
  off the chin. Primitive yet put together; seeded per instance (every
  daub is a different hand); same pulse + sickly light pool. One draw fn,
  so every placement (grove centre, Sign Chamber, Scriptorium, Brimley,
  the infestation pool) updated at once.
- [x] **Engine seams** (`systems/game.py`, `rendering/folds.py`,
  `systems/render_mixin.py`, `systems/threat_mixin.py`): direction-gated
  exits route straight through `cross_fold` (folds are seamless whatever
  scenes they join); scenes may gate exits on game state
  (`Scene.exit_gate_fn`) and drive per-fold formation charge
  (`Scene.fold_charge_fn`).
- [x] **The seal** (`scenes/well.py` Deep Stair): `well_rope_broken` →
  **`descent_sealed`** — pressing the keystone kills the grove fold AND the
  return pane (the fold dies; it never turns one-way — one-way stays the
  King's signature alone, §11).
- [x] **The well demoted** (`scenes/brimley.py`): dread set-dressing — the
  lip worn smooth by a year of hands, no rope, no way to follow. Toby's
  witness beat still points at it; the rite answers it.
- [x] **The Ledger says A YEAR** (`scenes/house.py`): the checkout dates
  stop a year back (same season as the PI's one dream), not "months";
  flow-guarded.
- [x] **Guidance:** the Invitation's text names the school; the
  `the_invitation` case note echoes it; Toby seeds the school from FIRST
  contact (the witness beat: they lived in his school, then walked out in
  a line) and adds the one-shot "don't go in there" warning once the
  envelope is carried (`tisdale_boy_dialogue`). The well's examine answers
  the witness: they went down here, and you never can.
- [x] Flow harness rewritten (`tests/flow.py` beat 1 + Deep Stair beat):
  handoff gating, school rite order, grove gate below/at 3, two-way
  descent, seal kills both panes, no-dash guard on the Invitation.

---

### ✅ 15. The dream-thread + the blast — the Deep Stair is CUT — DONE  *(2026-06; NARRATIVE §1b, §5, §6, §7, §9, §11; PORTALS.md)*

**Decisions (DISCUSS-FIRST settled).** Dreams are CUTSCENES ONLY. The
descent is one-way down; the way home is KEYED to the Mask (never
"one-way" — that stays the King's signature). The Deep Stair never fit a
mine and is cut; the dig never finished (the cult's own testimony), and
the PI finishes it with powder.

- [x] **Two-stage door-dream.** The journal now fires a brief MEMORY
  FLASH (`FLASHBACK_FLASH_DUR` ~0.55s, two flickers, no swarm, no bed —
  the half-dismissed memory surfacing); the FULL dream (door + mask
  swarm, `FLASHBACK_DUR`) plays at the GROVE RITE via `begin_rite_dream`
  (`systems/narrative_mixin.py`). Same dream, two weights; the one-dream
  / a-year / no-recurrence canon is untouched (`_log_dream_entry`
  unchanged). The dream freezes the world sim while it plays.
- [x] **The grove rite** (E at the dead fire, two-press — never a
  lone-press point of no return; re-armed on scene exit): completion
  sets `rite_performed`, `flashback_seen` (so the Threshold recognition
  fires for non-journal players too), opens the THROAT, and logs the
  oblique `the_rite` NOTE ("It knew me. It let me in.") — no banner, no
  "accepted" string, never evidence.
- [x] **The circle holds / the keyed pane.** While `rite_performed` and
  not `descent_sealed`: the grove's maze return + school pane refuse
  (one sensation line, once). The shaft-floor return pane answers only
  the Mask; crossing it up sets `descent_sealed` (the SPREAD lock) and
  the circle releases. SPREAD's surface egress is therefore Mask-gated
  end to end (the car already answers only the Sign).
- [x] **One presentation, one family (throat CUT).** A ground-throat
  variant was prototyped and reverted same-day by direction: the rite's
  open descent is the REGULAR standing rift pane, torn fully open. The
  rite's first press is SENSATION ONLY (no narrator forecast of the
  seal; the seal is discovered when the player tries to leave).
- [x] **The Deep Stair is CUT → the Deepest Face.** `works_deepstair`
  (key kept) is the dig's dead end now. Powder lives in **the Sump**
  (`powder` item, the diggers' store); the blast requires the **Mask in
  hand** (the investigator finishes the sweep before he blows the
  scene), two-press, consumes the powder, sets `depths_breached`, and
  DROPS the PI into `depths_antechamber` — the existing fall-zone text
  ("cut stone, worn smooth by years of feet") now reads as the OLD
  workings the dig broke into. The fall is the one-way step. Flags
  `deepstair_open`/`deepstair_fork_seen` are gone; the Seal/Spread fork
  is **experiential, not a menu** (where you carry His face), with the
  deliberation voices at the fuse.
- [x] Flow harness: rite two-press + cutscene drive, pre-rite crossing
  refusal, circle seal, keyed-pane refusal, Mask egress + SPREAD lock,
  sump powder, mask-gated fuse, blast + keystone-not-consumed.

### ✅ 16. The SPREAD ending — the drive-out cutscene + the CLAIMING — DONE  *(2026-06, directed; NARRATIVE §6 table updated)*

The text-on-black `escape_alone` stills were replaced by a full ~38s
cutscene, and the ending's canon sharpened by direction:

- **The claiming.** The King does not chase the car out — he is already
  IN it: the Mask rides the passenger seat. At the edge of Brimley it
  shifts as if to look at the PI; he gazes into its deep sunken eyes
  (completing the one dream that broke off a year ago, §1b) and is
  **claimed**. What he longed for most — to FEEL, after twenty numb
  years — floods back, and he drives south willing, certain, and His.
  The breach is now a claimed vector, not a passive latent charge.
- **The trailing King is a particle effect only** — a gold wake
  streaming behind the car through the corn, never a body. It cuts off
  at the fold. The crossing itself stays a NON-EVENT (the teleport
  doctrine): the fold's frame sweeps past the windows mid-gaze,
  unwitnessed; the corn simply ends, the rearview goes black.
- **The locked caption script** (7 lines, flow-guarded: the mask-shift
  line, the deep-sunken-eyes line, the closing card "Everyone will
  know.", and the no-dash rule). Durations come from
  `rendering/spread_drive.py SPREAD_BEAT_DURS` so picture and text
  cannot drift.
- **Code:** `rendering/spread_drive.py` (three handcrafted
  compositions: the ignition at the river's edge, the cab interior with
  the bespoke `_pallid_mask`, the open south flooding into colour);
  captions wrap over the picture in `ui/cutscenes._draw_ending`;
  `_tick_spread_audio` (narrative_mixin) runs the opening's
  engine/radio/static bed — the static DIES at the crossing, the radio
  comes back clean south of the fold; render_smoke now drives all three
  authored endings' draw paths.

---

### ✅ 18. Live staging: THE TALK + the calling-out — DONE  *(2026-07, settled with the user)*

Two staged live-action beats from the "characters act in the scene"
direction:

1. **THE TALK.** The FIRST time the cult ever lays hands on the PI it is
   a warning, not a capture. The locked lines (user-authored 2026-07):
   *"Hey. You go back to your hotel room if you know what's good for
   you."* then *"Run."* They let go — the room stands down, a short
   grace window covers the first steps away, and the PI's reaction
   lands as a caption a beat later and files as a NOTE (never
   evidence): *"Well shit, this town really doesn't have a midwestern
   welcome at all."* (a little humor against the grim, by direction).
   One freebie per run, spent at whichever grab site fires first
   (surface grab, hide-check struggle loss, underground contact — all
   routes gate inside `_trigger_death`). Every later grab is the plain
   CAPTURED card. Flow-guarded (§28).
2. **The calling-out (the Sign Chamber).** Mara now kneels among the
   congregation at the Mask's foot (`works_sign`), one more hood in the
   rank. On first entry the kneelers rise one by one and turn to you,
   one says her name at the room, and she stands up out of the rank and
   comes to you for her (unchanged, canon-guarded) exchange — evidence
   #6 lands here now. Then the room folds back to the kneeling. The
   kneelers are set-piece NPCs (no tag: no gaze, no chase; the east
   patrol stays the room's live threat, held off while the room
   performs). The deep hive (`dark`) keeps its congregation, past names
   now. Flow-guarded (§28b); the stealth deaf-kneeler guard reworked.

### 17. The ancient altar — the CAP of the last sealing — OPEN  *(2026-07, settled with the user)*

**Canon (locked).** The standing stones out in the mid-Brimley field (the
cult path off the east lane leads to them, `scenes/brimley.py`) are NOT the
cult's work: they are a **long-forgotten remnant of whoever found the
Threshold before it was lost to history** — the surviving surface **cap of
the LAST sealing**. That is why they must stand **next to the river**: the
river is the artery down to the door (§6b), so the cap sits directly over
the Threshold. The cult's worn path to the stones reads as pilgrimage to a
thing older than them that they only half understand.

**Design intent (implementation lands with the Brimley compression pass):**

- [ ] Move the standing-stones feature to the riverbank (over the point the
  Threshold sits beneath; keep the worn cult path leading to it).
- [ ] Pre-cult dressing: lichened, weathered, sunken — nothing daubed,
  nothing yellow. It must read OLDER than every cult mark in town.
- [ ] ONE worn carving on the stones that recontextualizes after the player
  has seen the Sign (the carving matches the Mask's grammar) — a single
  diegetic note (`notes`, never evidence), no explanation (§1b: sensation,
  not cosmology).
- [ ] It gives the SEAL ending its precedent without a word: the door was
  found once, capped, and lost. The PI's seal repeats it (this time from
  the wrong side); SPREAD breaks the pattern — the first time it ever left.

---

## The 2026-07 design queue (settled in discussion with the user)

> The full remaining worklist toward the $5 ship. Ordered roughly by
> user priority; §17 (the altar) above rides §23.

### ✅ 19. NPC jobs — generic routines for villagers — DONE  *(2026-07)*

The world read as staged because most locals stood where they were
placed. Named locals now carry a small JOB LOOP: walk between 2-3
personal stations, dwell at each facing the work, move on.

- [x] Generic mechanism: NPC movement mode **`"worker"`**
  (`entities/npc.py`) riding the cult's errand machinery
  (`systems/stealth.errand_step`, which now reads a personal
  `actor.stations` list over the scene's shared cult pool). Same
  interruption semantics as the cult's errands; unreachable stations
  are skipped, and a fully blocked route degrades to anchored
  wandering, never a freeze.
- [x] Routes authored where they're seen: **Garrick** (his spot → the
  well lip → the town track), **Royce** (pacing the stretch of road he
  used to drive, standing a long look down it each way), the **store
  Hettie** (counter → the bare goods shelves → the storeroom
  preserves), **Rev. Crane** (lectern → the empty nave → the vestry
  cot). Kept as-is by design: outdoor Hettie + Old Pell (homebody door
  loops ARE their job), Mrs. Calder (the set place is the point, §6b),
  Sable (`watch` — the man who was waiting for you).
- [x] Flow guard §29: Garrick provably walks between stations and
  dwells; the store/church workers carry routes.

### 20. The PI THEORY ladder — the notebook thinks — OPEN

An active "working theory" line in the case notebook that REVISES as
evidence lands: each canonical beat strikes the old theory through and
writes the next (rational → strained → the one he refuses to write).
Shows what he forces himself to accept and how impossible this all is.
Terse FACT / SOURCE / QUESTION entries alongside; never evidence, never
a waypoint.

### 21. The Works as a MINE — side-dug rooms, not hallways — OPEN

The Works must read as a mining effort: timbered side-chambers dug off
the halls (some finished, some half-dug, the deepest hand-clawed),
spoil heaps, cart ruts, the degradation arc ending at the Deepest Face.
Rooms gain dug-out side pockets (a few with loot/testimony placement,
most just labor made visible).

### 22. Deadpan narration editing pass — OPEN

Sweep every narrator/world caption against the settled voice: objective,
deadpan, a little curt (the talk reaction's register). Kill aphorism
and poetry where it crept in; keep sensation-only cosmic rule (§1b).

### 23. Brimley compression (~64x64) + the altar move — OPEN

Brimley is too vast for its substance: compress toward ~64x64 with the
same content density, cleaner road logic, shorter dead walks. §17 (the
ancient altar to the riverbank) ships inside this pass.

### 24. Liminal/eldritch beat pass — OPEN

A handful of quiet wrongness beats (geometry that doesn't add up,
sound with no source, a room that repeats) placed on the surface,
escalating with evidence. Sensation only, never explained (§1b).

### 25. Ship track — packaging — OPEN

Itch-ready build: pyinstaller (or equivalent) one-file builds for
win/linux, save-dir sanity, a settings sanity pass, version stamp.

## Status / sequencing notes

- **Phase 1 is done + pushed.** Docs (`NARRATIVE.md`, `CLAUDE.md`) already
  reflect the settled canon; this file now tracks only the Phase 2 remainder.
- **Coupling:** §6b (the three testimony fragments + Mask-only keystone) is
  DONE and flow-guarded; §8 (the PI's interior voice) and §9 (ashfall) landed
  earlier; §12 (Crane's pulpit condemnation) and §13 (the calendar sweep
  around April 14) are DONE. §10 is a fence, not a ticket. §18 (the talk +
  the calling-out) is DONE.
- **Open queue: §19 → §20 → §21 → §22 → §23 (carries §17) → §24 → §25**
  (plus an optional Crane murder-beat polish).
- Verify against `NARRATIVE.md` first; keep `tests/flow.py` green (run the full
  gate, `python tests/run_all.py`) and add a guard as each canon fact locks.
