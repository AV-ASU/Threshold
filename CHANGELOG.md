# THRESHOLD — Changelog

> **This file is history, not canon.** It is the append-only record of how
> the six canon docs (`CLAUDE.md`, `NARRATIVE.md`, `DESIGN.md`, `TODO.md`,
> `DIALOGUE.md`, `VISION.md`) got to their current state, and why past
> decisions were made. **It is explicitly NOT part of HARD RULE #0's
> mandatory-read set** — the six canon docs are written to be
> self-sufficient and current-state-only; you should never need this file
> to understand what IS true today, only to understand *why*, or to look
> up a decision that predates your context. Read it when you're curious
> about the history behind a rule, chasing down when/why something
> changed, or writing a new entry for work you just landed. Never required
> before answering a question about the game.
>
> **Entries are append-only and dated.** Don't edit old entries to keep
> them "current" (that's the six docs' job) — if a past decision was later
> reversed, add a new entry saying so and let the old one stand as the
> historical record. Newest first within each section.
>
> **2026-07 doc restructure (this file's own origin).** Before this split,
> the six canon docs each carried their own change history inline —
> "(2026-07 rework, superseded the 2026-06 placement...)" narration
> threaded through current-state descriptions. That meant HARD RULE #0's
> full-read-every-turn requirement paid the cost of the entire project
> history on every single turn, including a one-line edit, and the cost
> only ever grows. This file exists to carry that history instead, so the
> six docs can shrink toward "current truth, stated once" without losing
> any of the reasoning. See the "Documentation process" section at the
> bottom for the mechanics of the split itself.

---

## Evidence & the case

- **2026-07 — Hettie's memory, the son read, and the "son" tic.** The last
  three off the audit list.

  **Hettie's memory of the girl** lost its preamble ("I'll tell you the one
  thing I know that's worth the telling", a character announcing she is about
  to be important) and its portrait ("Sad around the eyes, and polite with
  it"), which contradicted her own answer to the photograph four lines
  earlier: *"Faces come through this shop. I stopped keeping them."* She
  either retains faces or she does not. What is left is a shopkeeper talking
  about her till: a regular, then not, and the rest of them going quiet at the
  same time as a fact about TRADE rather than a survey of the town, since Vane,
  Toby and Crane already deliver that observation and a fourth flattens all
  four. **The tab now comes out of the BIN under the till** rather than off a
  spike (maintainer's idea): she is not keeping a shrine to the girl, it is
  refuse she has not taken out because nothing leaves this town, refuse
  included, and the evidence stops being presented and starts being found.

  **`theory_son` is cut** with the other case reads. It wrote out the
  connection between the bear's tag and the letter, and "his name breaks her"
  had the PI predicting a scene he has not reached. The bear still detonates;
  that always lived in the ITEM's own text (`effective_desc`), not the book.
  **Nothing in the notebook now solves Mara.** What he writes is the fold, the
  wrong robes read, and the Mask.

  **"son" is Garrick's alone.** It had spread to eight uses across three
  speakers (Vane 3 including the hollow turn, Pell 3, Garrick 4) and was a
  large part of why those three read as interchangeable. Everyone else drops
  it. **Guarded by a new `tests/conventions.py` check** that attributes every
  chosen mode of address to its speaker and fails when one is shared, because
  this drift is invisible one line at a time: each author only ever adds one.
  The check exempts "mister" deliberately, since nobody in Brimley learns the
  PI's name, so it is the correct default in every mouth. Writing it turned up
  the sharing immediately, and it was proven red before commit.

- **2026-07 — The queue: six rulings from the story-audit workshop.**

  **The tab was wrong by a factor of three.** It read "run down most of a
  year"; Mara drove north in the FALL of 1993 and the present is April 1994,
  so her account runs three or four months. Corrected to "autumn through the
  new year" in both the item text and the notebook entry, and the proof moved
  off duration and onto the KIND of purchase (bread, kerosene, lamp oil).

  **"She lived here" is CUT, and it took three more with it.** The maintainer's
  ruling: that is the player's connection to make. Applied consistently it also
  kills `theory_resident`, `theory_came_apart` and `theory_willing`, each of
  which was the conclusion its own evidence had been built to earn, written out
  for the reader. **He never solves Mara on the page now.** What survives in
  his hand is the town: the son, the fold, the wrong robes read, the Mask. Which
  is what the notebook was asked to become at the top of this thread, reached by
  cutting rather than adding.

  **Mara does not walk out of the shop smiling.** The exit smile and Hettie's
  "It was the smiling I minded" are gone. A smile the shopkeeper finds
  disturbing is a visible mark of claiming, and NARRATIVE §2 says there is
  none; it also put the wrongness back on the PEOPLE. And Mara is grieving a
  dead son, not elated. She stopped coming in, the basket sat there, nobody
  clocked anything.

  **"Before the cold" is deleted from the timeline** (`NARRATIVE.md` §3). It
  put the procession underground in the fall, which contradicted Hettie seeing
  Mara in the shop past the new year. The maintainer identified it as detail an
  earlier session invented and wrote into the story bible, where it then got
  cited back at them as canon. Worth recording as a class of problem, not one
  clause: **the canon docs are partly model-authored, so "NARRATIVE.md says" is
  not the same as "the maintainer decided."**

  **THE ONE WATCHER ENTRY.** The Watchers are the whole below-3 threat, they
  open whenever the player is exposed, and the PI's notebook did not contain a
  single word about them. He now writes up the first one he stares out, and
  **never mentions them again for the rest of the run** while they keep coming.
  The silence is the design: an arc where he notices he has stopped being
  frightened is the game announcing that he changed, and a notebook that simply
  stops recording them lets the player notice it instead. He stays confused and
  tired and ordinary; he does not harden. Seeing one and staring it out is ONE
  event, so it fires on the dispel. Five guards, including the silence.

  **"midwestern" is capitalised**, in the Talk's punchline, which is one of
  the most memorable lines in the game.

- **2026-07 — The recruiter: no miracle, no euphoria (maintainer ruling).**
  Vane's one fragment of the *how* was a conversation with a blind congregant
  who had been promised his sight back by the dream, walked into the office
  without a stick, sat down square in the chair, and left smiling. Three
  things wrong with it, and the first is the one that matters:

  **The want was a miracle.** `DESIGN.md` §8 says the machine runs on ORDINARY
  wants, nothing cosmic: a full house, a harvest, a guest at supper, a road
  home. Sight restored was the only physical repair anyone in the fiction was
  ever promised, and it made the door read as a faith healer rather than a
  thing that whispers a bearing to someone in pain. **It was also a visible
  mark** (a blind man navigating perfectly), against the §2 invariant that
  being claimed leaves none, and it used a disability as a spook prop.

  He is now a man whose wife is alive in a county home and does not know his
  face. He used to drive down every Sunday. He stopped, because there is no
  sense in it until the work is finished and he wants her to know him the
  first time she sees him. The want is ordinary, unfixable, and not a repeat
  of Mara's dead child (absence versus presence without recognition). He is
  **wrecked and certain at the same time** rather than radiant: he cried the
  whole way through it and it never got near the part of him that was sure.

  The same pass cut the EUPHORIA TELL wherever it was doing work: he no longer
  leaves smiling, and the congregation are no longer "glad of it." The
  smiling-cultist motif had become the game's shorthand for possession, which
  is the visible mark canon forbids and puts the wrongness back on the PEOPLE
  after the world rot was deliberately relocated onto the PI. Vane calling the
  newcomers "friendly and smiling" and Sable smiling over the photograph both
  stay: one is a lawman describing pleasant strangers, the other is a host
  doing his job.

  Guarded four ways in `tests/flow.py` (the want is his wife and a county
  home, no blindness, no euphoria, wrecked-and-sure), and the euphoria and
  wrecked guards were proven to fail red before commit. Canon updated at
  `NARRATIVE.md` §4 with the reason attached, so the next session cannot
  restore a miracle want by accident.

- **2026-07 — The Casebook becomes the PI's running notebook (maintainer:
  "I hate how it's just a bunch of paper that just gets put randomly in the
  tab").** The Case tab was not a record, it was a filing system. Entries
  rendered sorted by CATEGORY (evidence first, then notes), so the order the
  player saw them in was the order the code declared them rather than the order
  they lived them, and the two pinned surfaces, the Working Theory and the
  Timeline, were recomputed live on every open. The book had no memory:
  whatever the PI used to think was silently replaced by whatever he thought
  now.

  That last part was the real loss, and it was specific to this game.
  `NARRATIVE.md` holds that his written theory is allowed to reason WRONG and
  the game never corrects him (the robes are the ones who could stop this).
  That wrongness was invisible, because the theory edited itself into
  something less wrong before the player could catch it out.

  **Now it is one running document.** Everything he writes down goes in in the
  order he wrote it and stays exactly as written. His CONCLUSIONS are journaled
  once each, at the moment he reaches them (`_THEORY_THOUGHTS`,
  `_tick_theory_notes`), and they render with no heading, because a conclusion
  he jots is a line in the flow rather than a titled find. The wrong robes read
  now sits on its page for the rest of the run, next to the later reads that
  supersede it, and nothing ever says so. Reading the book start to finish is
  watching a man's understanding change.

  **The Timeline is CUT** (maintainer ruling): it re-sorted his finds into
  Mara's chronology, which is exactly the connection the player is supposed to
  make. He writes the dates down as he finds them instead, and the arithmetic
  is theirs. The booking slip's entry gained the date it had always been
  missing ("Dated the eleventh of December") since without it the chronology
  was unreconstructable from the book at all.

  **How it is stored.** `evidence` and `notes` stay two save lists, because
  the King-gate counts one and must not count the other; each entry gets a
  `seq` stamp from the new `Save.next_seq`, and the book merges and orders by
  it. A single merged list would have been the tidier data model and would have
  meant rewriting roughly 130 call sites, nearly all of them test fixtures, for
  no player-visible difference. The split is bookkeeping and never reaches the
  player.

  Consequences worth recording: `_rewrite_note`, added days earlier so the robe
  could revise its own entry after the Talk, is GONE. Under a running document
  the second look is a LATER entry (`clerk_robe_placed`) and the first stays as
  written; the pair, one describing a garment and one recognising it, is the
  record of him learning, and collapsing it into one tidy paragraph erased the
  man who did not know yet. `mc.wrap_lines` was split out of `mc.wrap` so the
  pagination measures with exactly the rules the renderer draws with. The leaf
  was repositioned clear of the tab ribbon, its ruling pitched to the body font
  so his lines sit ON the rules, and the body moved from the case-file mono to
  the same serif ink as Mara's journal, so the two books read as two hands
  rather than a document and a typewriter.

- **2026-07 — The small-detail layer, first four (the schoolhouse and the
  robe).** The discovery catalog showed the surface holding six real finds in
  37 rooms, three of them mandatory. The maintainer's diagnosis of why a
  search verb would not fix that: there is nothing small to find, so searching
  would be busy work over empty containers. Content first, mechanics later or
  never.

  A longer proposed list was cut down to four, and the rejections are the
  useful part of the record. Cut: an attendance register (an object whose only
  job was to announce that time stopped in January, which is the calendar
  TODO #28 had just ordered removed, rebuilt in a school uniform); stacked
  bowls and a folded coat (nobody's, pure atmosphere, and the coat existed
  only to be almost-a-clue); and three red herrings on Pell, Garrick and
  Calder (narrator boxes explaining the inner life of characters who say it
  better themselves in dialogue, and inert by construction, since a dead end
  that resolves into a sad fact costs the player nothing). **The rule the
  survivors share: a find is a physical trace of a specific person doing a
  specific thing, and it is an object rather than an explanation.**

  Shipped:
  - **Toby's desk**, in the pile the cult shoved into the schoolhouse corner.
    His name inked in the lid, a spelling sheet with three words done. It
    records NOTHING in the case by design: the name is the whole beat and the
    player does the rest.
  - **A newcomer's gas receipt** under a schoolhouse cot: Clark Oil, Seymour,
    Wisconsin, July 2 1993, fourteen gallons, cash. A walk-over pickup that
    files a note. It corroborates the one thing Vane could never get out of
    them, that not one could say where they had driven in from, without a word
    of testimony.
  - **The chalkboard's other half.** The board always said the cult's doors
    were drawn "under a child's faded lesson" and the lesson was never
    legible, so the room read as a cult set rather than a school somebody
    moved into. A surviving corner of it now reads first in every pre-rite
    look: a column of addition worked down in a child's hand, the answer
    circled by the teacher.
  - **The robe in Sable's closet, in two stages.** It used to fire one caption
    calling it "a cult robe" before the player had ever seen a cult, which is
    knowledge the speaker cannot have (playtest error class 5, caught by the
    maintainer). Now the first look is a garment: dark, plain, hand-sewn, and
    the only odd thing about it is that it has never been worn. After THE TALK
    has put a robed man's hand on the PI's shoulder, the same closet reads
    differently and the note is REWRITTEN in place rather than filed twice
    (the new `_rewrite_note` helper). The find is the same find; what changed
    is the man looking at it.

  Cut in the same pass, all three placeholder narration that recorded nothing:
  `scarecrow` (the [E] cue and its box gone outright, a scarecrow standing in
  a corn row being scenery rather than an event), `worn_stone` (the headstone
  keeps its two-line look, drops the "A weathered headstone." discovery), and
  `backwoods_note` (the stash keeps its pickup, drops "A small stash.").

- **2026-07 — Vane's menu, cut down and un-gated (the maintainer's pass on the
  pilot).** Reviewing the gate list for Vane, the maintainer cut and reshaped:

  - **The `car` question is CUT.** "We really dgaf about the car." Its fold
    material (nothing with an engine leaves, "It's the town.") moved into the
    town question, where it belongs: the dead engines are a symptom of what is
    happening to Brimley, not an errand about the PI's own vehicle. The fold
    note files from there now, and `_vane_car_told` is retired.
  - **The town question went PRESENT TENSE** — "What's happening to this
    town?" It was "What happened", which framed the seal as finished history
    rather than the thing still happening to the man being asked.
  - **The Ledger share is CUT.** The registers are Sable's thread and pay off
    at that desk (`checkouts`); Vane's trust should turn on Mara's trail, the
    case he is actually being asked to believe in. `share_journal` is now the
    single share, so trust has one clear price.
  - **The recruitment question became "Where are the cultists gathered?"**,
    gated on THE TALK rather than the intro: the PI asks after a hand has
    landed on his shoulder, so he is asking about them as people who are
    *here*, not as history. Vane answers the WHERE honestly (the school, the
    barn, the lodge, and then nothing, because he does not know) and the HOW
    is what he withholds.

  **And the rule the whole menu now follows: trust gates the ANSWER, never
  the QUESTION.** The two trust-gated rows used to vanish from the menu until
  earned. They are askable from the moment their situation exists, and an
  untrusted Vane refuses them in his own voice, saying what would change his
  mind ("Bring me something I can hold"; "Work the case. Come back and show me
  you did"). He is written as a mistrusting man, so the mistrust should be
  something the player *meets*, not an absence they never see. A hidden option
  teaches nothing; a refusal is characterisation, a stated price, and a reason
  to come back. Both rows stay askable until he has actually answered, so a
  refusal is never a lockout, and the grant rides a `("do", ...)` at the end of
  the trusted branch so a refusal can never arm it.

  Left deliberately un-gated: the booking-slip handover on the photograph. The
  maintainer raised whether an untrusting Vane should hand it over at all and
  flagged the soft-lock risk in the same breath; gating it on a share would
  have forced journal-before-slip and broken the "findable in ANY order"
  property `DESIGN.md` §9 holds for the surface trail. The reluctance lives in
  how he gives it instead.

- **2026-07 — The story audit, and the detention night (the investigation-loop
  pilot; `TODO.md` #1).** A story audit aimed at "make investigating feel much
  better" measured the loop instead of describing it, and what it found was
  that there was no loop. Of 31 authored questions across the whole cast,
  **three** opened on something the PI had found, and two of those three were
  the Ledger, which is not case evidence. Every `evidence_maras_*` flag was
  read by nothing but its own re-fire guard and the derived theory/timeline.
  Two of the three surface pieces needed no investigation at all: the journal
  a walk-over in the barn, the record an `[E]` on a filing cabinet. So finding
  and asking were parallel activities that never touched — the case
  accumulated rather than compounding, and once each principal's rows were
  spent the town went inert with nothing left to bring anyone.

  The sharpest instance was the record, which had also quietly stopped
  implementing its own design: `DESIGN.md` §9 specifies the NPC as the **warm
  delivery** (show the photograph, they react and hand it over) with the paper
  world-persistent as the no-soft-lock fallback. The receipt did exactly that
  through Hettie. The record did not — and worse, **Vane's answer to Mara's
  photograph did not mention that he had arrested her.** He takes her picture
  to the window, works it corner to corner, and places her only as "one of the
  new folk," about a woman he personally booked, held overnight and signed a
  slip for four months earlier. That is `DIALOGUE.md` voice rule 5 (knowledge
  the speaker can have) and it threw away the best investigative beat on the
  surface.

  **What shipped (the pilot, scoped to Vane on the maintainer's direction).**
  The photograph is now a recognition: he knows the face, names the December
  night, and goes to the files, handing the slip over mid-exchange through a
  `("do", grant_record)` beat. `grant_record` is the single funnel both ways
  in share, mirroring `grant_receipt`. The office records drawer is demoted to
  the **fallback**, opening only once he is no longer the man behind the desk —
  dead **or hollow**. The hollow case is a real hazard rather than a
  hypothetical: the newspaper (+2) and the preacher's murder (+1) latch the
  turn at `VANE_HOLLOW_AT`, which a player can reach before ever showing him
  the photograph, so without the fallback that ordering would have soft-locked
  the descent. Both are guarded.

  Holding the slip then opens **`the_night`**, his account of the arrest: the
  paper says what he wrote down, this is what he saw, and it files as a
  **statement** note (`the_disturbance`), never counted. Its last beat leaves a
  second witness as a plain stated fact — the man who fetched him sits the
  square all day — and **the lead is never pointed at.** He does not say
  Garrick, and no PI line closes the gap; connecting it is the player's, which
  is the whole difference between investigating and collecting, and the
  opposite move from the revisit-nudges #13b is cutting.

  Also from the audit: **Mara was two different ages.** The case-file intake
  said 26 in both its surfaces while the booking slip said `AGE: 24` on a date
  four months before the present — in the one class of text the game asks the
  player to read as self-evident, and the two are read side by side in the
  Casebook. The maintainer ruled 24; the fact now has one home in
  `NARRATIVE.md` §4 and a guard holds the intake and the slip together.

  **Ruled, not built:** Sable's misdirection (he points at the cold old
  families, Hettie says the warm ones went soonest) stays unresolved in text.
  The audit flagged it as a gap and the maintainer ruled it deliberate and for
  the player to notice, so it is now a standing fence in `TODO.md` against a
  later session "fixing" it.

- **2026-07 — Evidence reworked into Mara's trail (`TODO.md` #22, `DESIGN.md`
  §9, `NARRATIVE.md` §6).** The original model was a "pool of six, any 3"
  evidence set. Run against a rubric (must be Mara's, must be a pickup item,
  must be self-evident, one per room), four of the six failed it: the
  **Ledger** (she was never at the lodge — zero Mara relation), the
  **Preacher** (not Mara, and cult hostility was already proven), the
  **Mask** (needs the cosmology to read, and it's not hers — it's the
  keystone item), and the **Congregation** (Mara is proof, not evidence).
  Worse, "any 3 of 6 is the point of no return" was never true in play: the
  surface set was always mandatory (or Act 1 had no teeth), and the
  underground three drove no mechanic at all (every gate is ≤ 3 — cult
  wakes at 1, King arms at 3, rot caps at `min(3, evidence)`). Half the
  system was inert. Replaced with `CANONICAL_EVIDENCE` = Mara's five-station
  biography (`maras_receipt`, `maras_record`, `maras_journal`, `maras_dig`,
  `maras_room`) — felt it → did it → why → the result. The Ledger and
  Preacher now file as case **notes**; Mara herself is **proof**, not a
  counted beat.
- **2026-07 — The bear + the name-beat landed** alongside the above. New
  item `bear` (Toby's loan, tag reads Sam), optional, never gates, detonates
  once the letter is read. The bear-gated name-beat lets the PI say the
  boy's name to Mara; she seizes him, the rite cracks, and her fate is
  unchanged (2026-07 ruling: she refuses the bear and turns back to the
  dig). Invariant locked: Mara never says the name, only the PI and the tag
  do.
- **2026-07 — The PI rots, not the town (four tiers).** The world rot was
  originally built as townsfolk *converting* — `_convert_local`,
  `_turned_local_dialogue`, `ROT_TURN_LINES`, an `infested=True` body-horror
  overlay. This directly contradicted the story bible ("the wrongness is
  the place, not the people," `NARRATIVE.md` §2) — the whole layer was cut.
  Replaced with a four-tier PI interior register (`_pi_tier`/`_PI_WEATHER`/
  `_pi_framing` in `scenes/dialogue.py`) that colours each principal's
  conversation *framing* by evidence count (0 / 1-2 / 3 / 4+) while the
  NPC's own words never change. The town stays ordinary to the end; the man
  hearing it doesn't.

## World rot & Sheriff Vane

- **2026-07 — Vane's fall made player-driven (`TODO.md` #2a).** Originally
  Vane, like every other local, would auto-convert under the old rot-people
  system. Replaced with a hidden despair/hope ledger (`vane_despair`): the
  PI sharing a real discovery with him is both the hope currency and the
  trust that opens his blind-cultist testimony thread; the preacher's
  murder and the newspaper give are despair acts; net despair at
  `VANE_HOLLOW_AT` latches the hollow turn (no return); a neglect override
  hollows him regardless at 3 evidence if he was never once informed. Once
  hollow, the next office load spawns `_spawn_hunting_sheriff`, a unique
  force-chase threat, "TAKEN INTO CUSTODY" on contact.
- **2026-07 — Corpse persistence: scrapped, then reinstated in a simpler
  form.** An earlier pass removed corpse persistence entirely (no replay,
  no accumulating `mold` decay stage). The 2026-07 ruling reinstated
  persistence in its simplest form: a `dead_locals` save-arg ledger,
  `_apply_dead_locals` lays each killed local's body back down on every
  scene re-entry, no mold stage (corpses draw at 0, a clean fresh kill).
  Cultist bodies are the one exception — they last only the visit, since
  patrols are dynamic spawns and respawn by design.

## Stealth & threat

- **2026-07 — Binary hidden-flag stealth replaced with graded suspicion
  (`DESIGN.md` §12, formerly its own `STEALTH_REWORK.md`).** The old system
  was an on/off `hidden` flag. Replaced with a per-enemy `suspicion` value
  in [0,1] filled by a detection score (`los * distance_falloff *
  facing_cone * concealment`), two cover classes (leaky mobile concealment
  vs. rooted enclosed hides), SEARCH sweeping nearby hides, and a timed
  struggle mini-game on discovery instead of instant capture.
- **2026-07 — First human playtest pass on the stealth rework.** Found four
  faults: hiding spots too rare (23 enclosed hides, nearly all
  underground); corn/tall grass rendered as a flat floor tint (invisible as
  cover); no narrator boxes taught the mechanic (fixed by cutting the
  teach notices instead — wordless cover entry, the visible tuft render +
  audio cues are the only tells); and, confirmed by the numbers, "running
  around the cultist beats hiding" — cultists patrolled *and* chased at 68%
  of the player's walk speed. Landed against it: the speed ladder (King >
  sprint > locked chase > walk > scout), sprint-in-LOS multiplying
  detection score, an arm's-reach contact grab, and +7 surface hides. River
  stones (a noise-distraction throwable), the window-smash and dead-well
  variants, and the under-bridge hide landed in the same pass. **Tuning
  itself (the suspicion fill curve, sweep budget, struggle window) remains
  open** — see `TODO.md` #5.
- **2026-07 — The cult grab softened to two-touch, with a one-time warning
  first.** Originally any grab was an instant CAPTURED. Landed: the first
  cult grab of any run plays as "the Talk" (a courteous warning, not a
  capture, presented as a close-up tableau since the tableau system
  landed — see below); after that, the first grab of an encounter shoves
  the PI free (`_cult_shrug_off`), and only a second grab before reaching a
  safe scene is the capture.
- **2026-07 — The Watchers rehomed as His gaze, then made the below-3
  threat, then made light-driven.** Originally a `GAZE_BIND`
  high-visibility trigger (now retired). Rehomed as "His gaze made
  manifest" and promoted to the primary visibility driver below the
  King-gate: they spawn on a timer while the player is exposed, hold and
  drive visibility up while live, and are cleared by gaze-dispel/axe/round.
  A later pass ("no light = danger," `TODO.md` #21) extended exposure to
  mean *being in the dark* inside non-refuge interiors, with light pools
  and the flashlight as the counter (a Watcher caught in light burns out).
  True refuges (`SAFE_SCENES`, `KING_FREE_SCENES`) stay gaze-free
  throughout every version of this system.
- **2026-07 — Cult liveness pilot (`TODO.md` #23a).** Two scout-only body-
  language beats landed: a shared-clock synchrony pause (every idle scout
  in a room freezes mid-stride together for one breath) and a crossing
  hand-off (two scouts whose rounds cross stop and face each other). Both
  run after detection/suspicion score each tick, so neither ever pauses a
  threat state. Station authoring for the remaining patrolled rooms is
  still open.

## The shadows program (the amalgams)

- **2026-07 -- "If it isn't good, remake it now" (maintainer).** Written into
  `VISION.md` with a pointer from `CLAUDE.md`'s working agreements: when you
  look at a model or a design and judge it not good enough, remake it in the
  same breath instead of handing it over with a caveat. "Reads a bit flat",
  "acceptable for now", "I'd rather judge it in situ" are all the same move --
  shipping work already judged as poor and making the maintainer say so. The
  economics are lopsided: another pass now costs minutes because the
  reference, the preview and the last failed attempt are all still loaded,
  while the same pass after a round trip costs their attention and a full
  context rebuild. A prop that took five exchanges usually took one exchange
  and four caveats that should have been four more iterations. The stated
  exception is a genuine fork between two defensible directions, which is a
  question rather than a caveat.
  Applied immediately to the thing that prompted it. The stoop had been
  handed over the turn before with exactly that hedge -- proportionally
  correct, reads flat, I'd rather see it in situ. Looked at again it was two
  treads and no LANDING, which is a flight of steps rather than a stoop: the
  landing at the door IS the object and the steps are its approach. Remade
  from a fresh reference (36in minimum landing, wider than the door by a foot
  each side, 6-7in rise to 11-12in run) with side cheeks closing the step
  ends so the treads never float. It reads from every heading now.

- **2026-07 -- THE PROP PIPELINE: props became data (maintainer: "the issue
  is the creation process... if this can take us from 5 prompts an object to
  one or two that would be perfect").** Diagnosis first, because the
  individual bugs were symptoms: a prop was a function emitting polygons, so
  every prop re-derived face culling, draw order, shading and world-vs-screen
  placement, and every prop got them wrong independently. Worse, I built the
  shape the primitives made easy rather than the shape the object is -- the
  library was four shapes wide, so a rural mailbox (a tunnel arch) shipped as
  a rectangular prism and a stoop as two slabs, and no amount of bug-fixing
  touched that.
  Four new files. `prim.py` returns FACES rather than pixels, and is wide
  enough to model things: box, plate, arch, cylinder on either axis, prism,
  wedge, revolve. `materials.py` is the one colour table, shading from the
  face's role and how far up it faces, so a cylinder gets its crown-to-belly
  gradient for free and two props meant to be the same cedar are. 
  `assembly.py` holds `Part`/`Assembly` and does culling, depth-sorting and
  shading ONCE for everything -- which makes the old failures inexpressible
  rather than merely fixed. `assemblies.py` declares the props.
  **`references.py` is the piece that changes the hit rate.** The maintainer's
  observation was that the best prop in the game is the one built from a
  reference they handed over, and everything built from my own description of
  it went five revisions. Fetching reference IMAGES turned out to be blocked
  by this environment's egress policy (403 on CONNECT; the proxy README says
  report it rather than route around), but web SEARCH works and carries most
  of the value, because what a photo fixes is shape language and proportion
  and both are written down. The Joroleman mailbox is "a tunnel with an
  arched top and flat front, back and bottom", 23.2 x 11 x 13.4in. A stoop is
  7in rise to 11in run, 48-60in wide. Recording that and checking against it
  in the gate is `tests/conventions.py` check 8.
  It paid immediately, and this is the part worth keeping: on its first run
  the proportion check caught three errors BEFORE anything was rendered -- a
  mailbox measured with its post included, a stoop whose reference axes were
  quoted the way a catalogue quotes them and so was compared ninety degrees
  out, and a woodpile modelled with its logs running along the stack instead
  of across it (a stack runs along a wall with the ends out, so a log lies
  across it). That last one was the actual reason the pile had looked wrong
  through three previous rewrites.
  The four yard props are rebuilt on it. `draw_prop_solid` prefers an
  assembly and falls back to the hand-written function, so the ~80 existing
  props are untouched and convert as they are contacted -- a mass conversion
  would mean re-verifying eighty props by eye, which is the expensive thing
  the rework exists to stop.

- **2026-07 -- `draw_box` was drawing its own back faces (maintainer:
  "occlusion is wrong, I can see inside some logs").** The primitive picked
  which faces to draw from a FIXED world axis -- "near, left, right" measured
  outward from +y -- and drew them unconditionally. That is only correct
  while the camera looks down -y. At other headings it painted the box's back
  over its front and left the real front undrawn, so a box showed a concave
  scoop into its own inside. It affected every box prop (visible on the
  mailbox and the stoop) and it is the reason a woodpile could not be stacked
  out of boxes at all. Faces are now chosen by the CAMERA: each of the four
  vertical faces is kept or dropped by whether its outward normal points at
  the viewer, and the one pointing most toward the viewer takes the shaded
  near colour. A box is convex so the survivors never overlap. Verified
  against the render regression set: identical within tolerance on every
  shipping scene, so the fix corrected the geometry without disturbing what
  was already tuned around it.
  **And a log is its own object now** (`solids.draw_log`, the maintainer's
  call: "just make one log and then create a stack of those"). It is a closed
  cylinder with sawn end caps that draws only the surface facing the viewer,
  and the woodpile is a depth-sorted stack of them. That is what finally made
  the pile occlude honestly, after three failed attempts to fake it from a
  single volume. The stoop's treads were sorted back-to-front for the same
  reason -- drawing them in index order let the upper, further step paint
  over the nearer one, so the flight read as one slab with a notch bitten
  out of it.

- **2026-07 -- `draw_box` could not stack (maintainer: "can't you see that the
  log pile looks wrong?").** It is the primitive every flat-sided prop is
  built from, and it always drew from z=0 to z=h -- there was no way to sit a
  box on top of another one. The woodpile's courses were therefore all
  sitting on the ground in a single layer while their drawn log-ends were
  placed at the heights the courses should have been at, so the ends floated
  above the mass like sparks. The stoop had the same disease from the same
  cause: each "step" was a box from the ground to its own height, making a
  set of nested slabs rather than a flight. `draw_box` gained a `z0` base
  height (defaulting to 0.0, so every existing caller is unchanged) and both
  props now stack.
  Getting there took three wrong turns on the woodpile, all worth recording
  because they are the same mistake at different depths. It was first a
  `draw_solid` body of revolution (a barrel with dots on it), then a
  `draw_box` crate with the ends decorating one face (a table with coins
  spilled beside it), then a stack of real logs whose ends were still
  screen-space `pygame.draw.circle` at a fixed pixel radius -- so they neither
  scaled with the prop nor tilted with the face, and at any size but the one
  they were eyeballed at they were twice the width of the end and hung off
  both sides. The ends are now rings of points built in the END FACE'S OWN
  PLANE and projected one by one, so they foreshorten and skew with it, and
  the row/column count is derived from the stack's dimensions and the log
  diameter rather than chosen.
  The other lesson: it was being judged at 5x magnification, where the flaws
  were obvious but the proportions were not. `--scale` on the preview is how
  to check a prop at the size it actually ships at, which is where silhouette
  is the only thing that survives.

- **2026-07 -- The prop preview was rendering everything flat, and VISION's
  all-directions rule now covers props (maintainer: "it needs to default to
  3D... the vision all directions rule need to be applied for prop
  creation").** `tools/preview_props_sheet.py` built its camera with
  `pitch=55` and never assigned `yaw`, so every prop was drawn dead-on at yaw
  0: one face, no corner, no top. Under that view a real volume and a flat
  card are indistinguishable, which is exactly backwards for the tool whose
  job is telling them apart -- the same defect `capture_facings.py` was
  written for, in a second place. It now TURNTABLES by default, a row of four
  yaws per kind.
  Turning it on immediately failed three of the four brand-new yard props,
  all of which had read fine dead-on: the mailbox's flag, the woodpile's cut
  ends and the stoop's treads were all placed off `cam.yaw` rather than the
  deco's own yaw, so they swung around their objects as the view turned and
  disappeared from half the headings. All three now place in WORLD space,
  and the woodpile's ends are face-culled so you never see them through the
  stack. Two of them were also `draw_solid` bodies of revolution and read as
  a drum apiece (a stoop like a butter-churn lid, a woodpile like a
  perforated barrel); both are `draw_box` now.
  An automatic camera-facing DETECTOR was written and then removed rather
  than shipped: byte-identity across yaws fails because many prop draws use
  unseeded `random` for speckle, and silhouette comparison fails because the
  pitch flatten means even a deliberately camera-locked box changes outline
  as the view turns. It could not be made to fail on a real standee, and a
  check that cannot fail is not a check. The turntable is read by eye, with
  the two failure signatures written down in `VISION.md` next to the rule.

- **2026-07 -- The last two thin roads joined the safe path.**
  `gravel_road_north` was rebuilt outright as a T (14x22 -> 32x36), keeping
  its boarded chop-target alcove, its pines and its crows. `arrival_road` was
  NOT rebuilt: its endless-north illusion is a `_render_band` plus a
  `_treadmill` plus a silent same-scene south loop, none of which a generic
  path builder models, so it kept its machinery and took the cross-section and
  lamp pattern instead -- widened 15 -> 23 tiles so a nine-tile corridor fits,
  with every column derived from `ROAD_C` and the shared constants rather than
  the literals that made it un-widenable before. Its car, sign and directional
  boards moved out onto the verge.
  Two guards fired on the change and only one was a real defect. The crow
  noise-trap's literal column landed inside the widened east tree wall (real,
  fixed). The band-is-landmark-free check tested "no `d` anywhere in the row",
  which was a valid proxy only while dirt appeared solely on the E-W crossing
  -- with dirt shoulders on every row it failed a scene that was still
  correct, so it now tests the two actual landmarks (a full-width dirt row and
  the car footprint) instead of a stand-in for them.
  Verified by walking all 90 lanes of all four path scenes at ev3 in the dark
  (zero falls, zero masts in a road) and by driving `arrival_road`'s own
  machinery: the treadmill still wraps, the south loop still fires, the car
  still answers, and both mouths still lead where they say.

- **2026-07 -- The marked lamp pattern generalised to the whole network.**
  The eight X's on the country lane were decomposed rather than copied, and
  they turned out to encode a consistent rule: a junction is lit at the
  CORNERS between two arms (the poles flank the side road's mouth instead of
  standing in the crossing), a side with no arm takes one centred mast to
  close the fourth side, runs carry FACING PAIRS every 11 tiles out, and the
  ends of a run are left dark. `_lamp_stations` now implements that, which is
  a change of kind as well as spacing -- the old derived rhythm staggered
  poles down alternating shoulders, and the marks are unambiguous that the
  long runs come in twos.
  Checked against the ground truth rather than assumed: the derived pattern
  reproduces four of the maintainer's eight marks exactly, three more within
  one tile, and differs meaningfully only on the short north arm. The lane
  keeps its explicit `lamps=` list either way; `river_road` and `river_bend`
  now follow the rule (10 and 7 masts, five clean pairs down the river run).
  Still on the old thin-road treatment and therefore unlit: `gravel_road_north`
  and `arrival_road`, queued as `TODO.md` #26's path rebuild.

- **2026-07 -- Lamp positions came off a marked-up screenshot, and reading it
  became a tool.** The maintainer drew X's on a capture ("lights on all the
  yellow Xs and nowhere else"); a rhythm placed to match them by eye hit none
  of them. Under the oblique tilt the marks are not eyeballable -- the view is
  yawed and foreshortened, and the same screen row covers very different world
  rows depending on depth. `tools/screen_to_world.py` inverts the projection
  by brute force (project every tile centre through the real camera, take the
  nearest), so a marked screenshot becomes a tile list in one step; `--grid`
  writes the same view with tile coordinates drawn on it, so a scene can be
  discussed in numbers.
  What the marks said once read: masts belong on the OUTER edge of the
  shoulder (not halfway across it), they STAGGER between the two sides rather
  than pairing off across the road, and NOTHING stands at the junction --
  poles flank the crossing instead. So `LAMP_OFF` moved out a tile, the
  junction station was cut, and `build_path` gained a `lamps=` override so a
  scene's lighting can be art-directed outright rather than approximated. The
  country lane's eight are the maintainer's own positions, verified to match
  exactly; the other two scenes keep the re-tuned default.

- **2026-07 -- A lamp post was standing in the middle of the road
  (maintainer, marked on a screenshot).** The junction mast was offset from
  the junction along ONE axis, which is clear of the road only when the scene
  has no arm on the other axis -- so on the T and the L, which have both, it
  was planted squarely in the cross. It now goes DIAGONALLY into a corner
  quadrant (off both carriageways by construction, and where a junction light
  belongs anyway).
  Rather than tune the stride until mid-run stations stopped landing on a
  crossing arm's asphalt too, every station is now pushed outward along its
  own offset until its tile is not asphalt, and dropped if it cannot get
  clear. Placement cannot produce a pole in the road. The maintainer's marks
  also asked for the rhythm back along both shoulders, so the mid-run stride
  tightened (13 masts -> 21 across the three scenes, all on gravel).
  `tests/flow.py` §34 gained the assertion. Proving it could fail took
  stripping all THREE defences (the diagonal, the nudge, and the drop), which
  is the useful result: the builder refuses to emit the defect, and the guard
  is there for any future code path that places a mast by hand.

- **2026-07 -- The streets had way too much light (maintainer), and the claim
  behind them was wrong.** The safe path shipped lit end to end on the stated
  theory that the road's safety WAS its lamp coverage. It read like an airport
  runway, and the theory did not survive being checked: the mouth can only
  open within `LOST_EDGE_BAND` of a MAP EDGE, an arm's end is an EXIT (which
  already beats a mouth), and a flank edge carries no asphalt near it. The
  road is safe by its GEOMETRY, and a dark stretch in the middle of one is
  safe too. Verified by walking every lane of every arm of every path scene
  end to end at ev3 in the dark: 63 lanes, zero falls.
  So the lamps came down to about a third (43 -> 13), and the survivors were
  placed for what they TELL you rather than for coverage: one mast at the
  junction, one at each arm's end, and a rare mid-run pole so a long arm is
  not black end to end. A glow ahead in the dark now means a decision or a way
  out. The junction pair became a single mast as well -- two facing masts read
  as a lit gateway, and this is a county road.
  The light still does real work (it keeps the verge's dark off the asphalt at
  the rim, it makes you visible to anything hunting, and it dies with the
  gensets), so the blackout beat is unchanged. `tests/flow.py` §34's lighting
  check was REPLACED rather than relaxed: instead of asserting every asphalt
  tile sits in a pool, it now drives the walk described above and separately
  asserts the lamps stay sparse. The old check would have passed a road three
  times overlit; the new one fails a road that is actually unsafe. Corrected
  the overstated claim in `DESIGN.md` §14, `CLAUDE.md`, `NARRATIVE.md` §5 and
  the module docstring, all of which had stated lamp coverage as the
  mechanism.

- **2026-07 -- THE SAFE PATH: the lit spine (`TODO.md` #26 step 1,
  `DESIGN.md` §14).** The middle of the three layers, and the last one
  missing after the mouth closed the loop. The maintainer asked for "safe
  paths that lead to yards and the lost paths. T and L and I shaped areas...
  Not too thin... We need the river seen in the safe paths."
  **The design finding is that the layer needed no new rule.** §13's mouth
  only opens on dark, unlit ground, so a road whose lamps cover it end to end
  is already a road the world cannot take you off. That turns the paving, the
  shoulders and the verge from dressing into the mechanism: safe on the
  crown, gone off the shoulder, and -- because `street_lamp` is an ELECTRIC
  fixture -- a genset blackout does not dim the safe path, it OPENS it. It
  also lands Garrick's 2026-06 line ("stay on the roads") as level geometry
  instead of advice.
  `scenes/safe_path.py` builds a scene from ARMS, a subset of "nesw" around
  one junction: two opposite is an I, two adjacent an L, three a T. Five
  lanes of asphalt in a nine-tile corridor answers "not too thin" (the road
  it replaced was a three-tile dirt strip in a twelve-tile scene). Shipping
  network: `country_lane` rebuilt as the T, plus `river_road` (the I, with
  the water off its shoulder the whole way) and `river_bend` (the L, crossing
  on the planks); `gravel_road_north` gained a west turnout so the loop
  closes.
  Two things became RULES rather than per-scene decisions, both because
  authoring them by hand is how they go wrong: every side of a path is a
  mouth with the road exit winning (so the player learns one true rule --
  asphalt carries you on, everything beside it lets go), and WHICH lost space
  a side opens on is derived from what its verge is planted with, so you can
  never push through a wall of dead corn and land in a pine wood.
  New props: `street_lamp` (the town's mercury-vapor head up a galvanized
  highway mast, in both light tables and `_ELECTRIC_KINDS`) and `bridge_rail`
  (a timber parapet). Both were needed rather than wanted -- yard lights left
  84% of the road dark, and a deck without a rail reads under the tilt as a
  brown patch of ground that happens to sit on water. New floor char `"-"`,
  the E-W dashed centre lane, because the existing `"Y"` dash is hardcoded
  vertical and floor tiles cache BY CHAR.
  **Four defects were caught by looking rather than by reading the code,**
  which is the entire argument for the VISION rule: the north arm's gravel
  shoulders painted straight across the east-west carriageway (fixed by
  painting all gravel then all asphalt); the flank fence ran down the middle
  of a carriageway (the arm code's `vertical` flag reused for a
  perpendicular run); the arm-protection bands cleared a bare grass lane
  across the half of every L and T the road never reaches (now derived from
  the tiles the road actually covers); and the verge trees closed over the
  river and buried it, which is the one thing the maintainer explicitly asked
  for.
  Guards, `tests/flow.py` §34: the shape vocabulary is actually used, no
  asphalt tile in any path scene is unlit, every side opens on a lost space,
  the river is wide and blocking and visible from the road, and the deck is
  railed on both lips. The lamp geometry was SWEPT rather than guessed. The
  blackout case is tested end to end and is also the only way to exercise
  exit-beats-mouth (with the lamps burning the road is lit and the gate
  refuses anyway) -- which is how the first version of that test was found to
  be passing for the wrong reason.
  **The yard count, audited for the maintainer:** Brimley has seven enterable
  buildings, grouping by shared frontage into FOUR yards (church+barn,
  shop+school, sheriff+farmhouse, Toby alone) plus the Lodge's existing one.
  The table is in `TODO.md` #26, where the yard layer is now step 1.

- **2026-07 -- The north road out of Brimley was never walkable (bug, found
  while building the safe path).** `Scene.find_exit_at` reads the tile the
  player is STANDING ON, so an exit char that is solid in `OBJECT_DEFS` is an
  exit nobody can take -- no error, no tell, the passage just reads as a wall
  you bump into. Brimley registered its `gravel_road_north` exit as `"R"`,
  which is a solid ROCK char, and had shipped that way; the road out the top
  of town could not be entered on foot. Found by walking the map in a harness
  rather than by reading it, and two more of the same slipped into the new
  path network in the same session before the pattern was obvious. All three
  now use `"^"` (an outdoor_passage, like every other road exit), Brimley's
  passage widened from one tile to three so it does not need threading, and
  `tests/conventions.py` check 7 fails on any solid exit char anywhere.

- **2026-07 — THE MOUTH: the lost-space loop closes (`TODO.md` #26 step 2,
  `DESIGN.md` §13).** The three biome fields had been built and wired into
  nothing: reachable only by loading the scene key directly. This landed the
  entry and the exit, so the loop the ticket describes (interior -> yard ->
  push through the treeline -> fall -> land on the lit island -> leave its
  glow -> hunt the light -> climb out) is walkable end to end.
  **The design problem was where the mouth goes.** Wiring it into Brimley
  would have pre-committed the restructure decision the ticket explicitly
  records as NOT made, so instead the mouth is an opt-in per-scene capability
  (`Scene.set_lost_edge(sides, lost_key)` -> `Scene.lost_edges`, None on
  every other scene). Judging the feel now costs no canon, and each future
  mouth is a deliberate choice about which edge of the authored world stops
  holding. `set_lost_edge` refuses a WRAPPING edge outright: a torus seam has
  no far side to fall off, and the yard's x axis must stay the fold it is.
  **The gate is light, and it cost no new system.** `Game._tick_lost_edge`
  runs from `update_player` right after the wrap clamp (the map edge is
  exactly where the clamp just refused to let them through) and only opens
  when the room is genuinely dark AND the spot unlit. On the surface that
  darkness is the STORM, which already climbs with the evidence count -- so
  at ev0 every bound is the invisible wall it has always been, and the world
  only starts letting go once understanding has put the lights out. A lit
  spot never opens, which quietly makes the yard lights and a carried flame
  real protection instead of decoration. Falling writes a return anchor a few
  strides back INTO the world; reaching the hunted lantern spends it and
  climbs you out where you fell, rather than the old behaviour of chaining
  field to field forever (that chain survives as the no-anchor fallback, so
  previews and tests still walk).
  Shipping mouth: the lodge yard's treeline, N and S. Guarded by
  `tests/flow.py` §32b, whose two load-bearing halves (the light gate, the
  return anchor) were fault-injected to prove they go red.
  Two supporting fixes came out of building it. `Game.scene_gloom()` was
  extracted from `_draw_dark` so the darkness the gate measures IS the
  darkness the player sees, verified behaviour-identical across every scene x
  rot stage. And the lost fields lost their place NAME: the HUD labels every
  scene in the corner from the titlecased key, so a lost field had been
  announcing itself as "Lost Forest" -- the same explaining-away as the
  narrator box the maintainer had already cut. `display_name = ""` is now an
  honoured explicit blank (None still means unset), and
  `tests/conventions.py` check 6 was WIDENED to cover the name alongside the
  words rather than a new check appended beside it.

- **2026-07 — The dark rearranges itself (`TODO.md` #26 step 3, partial).**
  The observer-dependent half of the manipulation layer:
  `LostSpace._tick_reshuffle` moves the field's scatter landmarks when you
  are not looking. The rule it enforces is the one the whole in-between runs
  on -- **what the light touches is TRUE; the dark is not** -- so a prop only
  moves when it is outside your sight cone, unlit, and far off, and only
  lands somewhere also outside the cone, unlit, and not solid. Only GEOMETRY
  lies; the island, the camps, every light, and every threat are exempt by
  construction (the ticket's own fence). The first cut used a fixed-start
  loop and so shuffled the same three props forever; a rotating cursor fixed
  it, measured at 24 of 84 landmarks moved in 20s with zero fence violations.
  Asymmetric return and breathe-with-threat remain open.

- **2026-07 — Forest pond + camp variety (`TODO.md` #26).** The pond island
  was reworked off the tan `d` donut that made its waterline a drawn circle:
  `_pond_r()` meanders the radius with noise, the rim is wet mud, reeds sit
  in clumped stands hugging the bank rather than evenly ringing it, and the
  small `camp_fire` became a `haven_fire` with the lights pulled to the
  water. Island mean brightness 23.1 -> 28.7, p99 51 -> 75. The occupied camp
  gained three flavours chosen by hash (rest / watch / work, crews of 4 / 2 /
  3), verified distinct across nine seeds, so the camp you stumble into is
  not always the one you stumbled into last time.

- **2026-07 — `--bright` was not bright (tooling).** The clean-inspection
  flag on `tools/capture_facings.py` dropped the darkness and the fog but
  left the film GRADE and the sight CONE on, so inspection shots came back
  murky and near-identical to the player view -- which is exactly how a
  geometry defect hides from a look pass. Now it follows VISION's recipe in
  full (mean 46.2 -> 60.1, near-black 11.5% -> 4.9%). The same tool gained
  `--ev N`: a STORM_STAGE_SCENES scene at the default ev0 is full daylight,
  so before this there was no way to LOOK at the darkened surface world the
  game is mostly played in.

- **2026-07 — Lost road: the CASSILDA'S convenience store, done right
  (maintainer art pass, second round).** The road station's building was a
  bland box; reworked into a real Casey's-style convenience STORE
  (maintainer: "your main job is making a building look good... focus on the
  building first"). Building-scale mass with a brick wainscot (mortar courses),
  a cream stucco upper, a full storefront of dead glass under a red awning, a
  recessed double-door entry + a merch window, a flat tar roof with pale coping
  + a rooftop HVAC unit and vent, and a **NEON name across the fascia**. The
  store is named **CASSILDA'S** (`STATION_NAME`) -- a Casey's echo + a King in
  Yellow nod (Cassilda, of the play). Key second-round fixes to maintainer
  feedback: **(1) NO fonts** -- the name is spelled in a procedural neon-TUBE
  alphabet (`_GLYPH` stroke table + `_draw_neon_word`), every letter drawn
  geometry projected onto the wall so it foreshortens with the tilt (the old
  `SysFont`/`_blit_south_band` path was cut); **(2) all four FACES decorated**
  -- the building is drawn face-culled (`_face_vis` per wall by camera yaw), so
  the sides get brick wainscot + clerestory windows + a downpipe and the back
  gets a service door + a meter box + conduit, not a flat blank wall (verified
  front / 3-4 / side / back in an isolated pitch-55 preview); **(3) real
  PUMPS** -- `_draw_fuel_pump` is a proper 1990s dispenser (concrete curb, cream
  cabinet with a red kick panel, an overhanging display head with a dark
  metered window + green digits, a red topper, a hose slung into a nozzle boot
  on the flank), not a plain box; **(4) the roadside `neon_pylon`** was a plain
  board -- replaced (third round, to a maintainer reference photo) with a
  vintage GOOGIE / atomic-age STAR sign: a big bulb-lined yellow star
  (`_neon_bulbs` chase marquee) behind two angled neon banners -- a red one
  reading **CASSILDA'S**, a blue one **GAS FOR LESS** -- drawn with the tube
  alphabet warped onto each banner's angle; its light pool went warm.
  Third-round fixes too: the pump canopy + pumps were split OUT of the store
  solid into a separate `pump_island` deco so they DEPTH-SORT at their own
  position (the store is well north) -- the store no longer sorts on top of its
  own forecourt; and the rooftop "chimney" (a tall dark box) became a low wide
  curbed AC unit with grille fins. The lot was pushed further from the road
  (`road_off` 6.5). Fourth round (in-game readbacks): the elevated neon sign was
  being multiplied to black by the darkness overlay (it sits above its own
  ground light pool -- it read as a bare triangle), so a `_draw_emissive_signs`
  pass now REDRAWS the `neon_pylon` after `_draw_dark` to keep the neon bright
  (and the sign was lowered for framing); the lot pavement now extends one tile
  past the fence (`_in_lot_floor`) so the chain-link sits ON the lot instead of
  floating on dirt; the road's scattered ground-detail weeds (brown decals that
  read as "dirt on the road") were removed on the road biome; and the pump
  island was moved SOUTH, clear of the storefront (the lot extended north to fit).
  NOTE: `CASSILDA'S` / `GAS FOR LESS` are player-facing art
  strings in a prototype wired into nothing; if the lost road is wired in, they
  move into `DIALOGUE.md` per its contract.
- **2026-07 — Lost spaces: three biome FOCAL ISLANDS + a full-effort pass
  (`TODO.md` #26).** The prototype's single corn field grew into three
  biome-parameterized scenes — `lost_corn` / `lost_forest` / `lost_road`
  (`lost_space` kept as a back-compat alias → corn) — each a hand-authored lit
  island in the sea of generation. **Corn** became a real **crop circle**: a
  grass clearing ringed by a near-solid WALL of corn, isolated by an empty moat
  so the circle READS as a circle (the field's scattered corn clumps resume only
  well beyond it), with the abandoned cult camp at the centre and a new wide
  `haven_fire` bonfire whose glow fills the whole ring (the maintainer's note:
  "the fire should protect the entirety of the inside of the circle"); the
  clearing floor is grass, not packed dirt, with grass-tuft + leaf-litter ground
  detailing. **Forest** is a still **pond** — animated `~` water made a barrier
  by a see-over invisible solid (`x`) so you can't wade in — on a mossy bank, lit
  by a fisher's `camp_fire` on the near bank (offset so the player lands behind
  it, not on it) + lanterns on the far shore, dressed with reeds and a low mist,
  framed by dense generated trees. **Road** is a fenced filling-station **lot** built to a
  maintainer sketch: you land under a tall bright **neon pylon** (`neon_pylon`, a
  separate solid carrying the zone light) at the **driveway**; the sealed store +
  its own pump **canopy** over three dead pumps (`gas_station`, a building-scale
  solid, the canopy standing IN FRONT of and lower than the store so it stops
  eating it) sit at the lot's north-west; painted **parking bays** (`parking_bay`
  floor decals) mark the asphalt; a **chain-link fence** (`chain_fence`,
  see-through wire panels, solid `x` tiles) rings the lot with a gap at the
  driveway; and the **winding paved road** runs past the east edge, generated
  river-style (a low-freq value-noise meander PLUS a steady westward drift going
  north, so the endless dashed road trends north-AND-west if you follow it).
  Wrecks stall on the road and in a bay. Flat `R`-tile "rocks" (a plain 2D floor
  disc, a VISION violation) were replaced by a real 3D `boulder` solid (a squat
  faceted shaded stone), used on the forest pond bank + as roadside debris. New
  kinds: `neon_pylon` (+ the light moved here from `gas_station`), `chain_fence`,
  `parking_bay`, `boulder`, all tilt-registered. Two new light kinds —
  `haven_fire` (the crop-circle bonfire) and `gas_station` (the neon glow) —
  were added to `FIXTURE_POOLS` + `Scene._LIGHT_KINDS`, and a new
  `LOST_SPACE_SCENES` gating set gives every lost field a HEAVIER `_draw_dark`
  gloom (150) so the lit island pops against a black sea. Wells and straw dolls
  were pulled from the scatter (they read as Brimley cult props, wrong for the
  liminal fields; maintainer: "No wells or straw dolls here"). Guard:
  `terrain._build_water_bank_edges` now early-outs on a `procedural` scene (the
  pond hand-places its own bank reeds) so the forest doesn't full-scan a
  400-tile field. Still wired into NOTHING in-game — a feel prototype. Full gate
  green. Canon (NARRATIVE §5 / DESIGN §7) UNCHANGED until the restructure is
  decided + wired.
- **2026-07 — The LOST SPACES: a procedural non-repeating in-between (prototype,
  `TODO.md` #26).** Groundwork for the maintainer's Brimley-restructure idea:
  dissolve one-square Brimley into building scenes hung off a dark liminal
  IN-BETWEEN where the fold is FELT (you get lost) rather than told. Two tiers:
  a **safe lit PATH** (the road, no tricks) and the **lost spaces** you fall into
  off a DARK edge — dark fields that GENERATE new ground as you walk
  (backrooms-style: forward never repeats, not the torus wrap), the only way out
  a **light you HUNT** (an exit lantern held 6-20 tiles off, relocating out of
  your sight so it stays findable). Landed as a working prototype:
  `scenes/lost_space.py` (`LostSpace`) — a `Scene` whose `floor`/`objects` are
  generator-backed proxies over a hashed per-tile field, with a huge finite
  `w/h` and the player at CENTRE so collision + sight + the tilt render work
  unchanged and the map edge never enters the window (the engine map found the
  tilt renderer is already a camera-window system and collision/sight route
  through `char_*_at`, so a generator-backed scene needs no engine refactor).
  `nav_path` returns None (straight-line chasers); `DARK_SCENES` member (dark,
  flashlight works); the hunted exit lantern moves live (`lit_at` reads
  positions live). The field is a **hand-made ISLAND in a sea of generation**
  (the maintainer's model): mostly EMPTY ground (dead grass / dirt / mud) with
  sparse corn CLUMPS and scattered uncanny things to find (derelict vehicles,
  lone trees, scarecrows, standing stones, a well, a corn altar) -- emptiness +
  the occasional wrong thing, never a wall of texture. At the centre sits the
  corn biome's FOCAL POINT, an **abandoned cult camp** (the congregation went
  below and left it: a still-burning `camp_fire` ringed by bedrolls + log seats
  on worn dirt), whose fire lights the clearing -- a haven that is lit and
  orienting but NOT a true refuge. The **exit light is held until you leave the
  firelight**: the lit safe-feeling place is a dead end, and you escape by
  walking out into the dark to hunt the way out. Registered as `lost_space`
  but wired into NOTHING in-game (a feel prototype). Guarded: the scene is
  `procedural=True` so smoke skips its flood-fill + full-grid scans (a 400-tile
  field would otherwise hang them), and its grid proxies are bounded so stray
  iteration terminates. Full gate green. The design model + the open decision
  (whether to commit the restructure) live in `TODO.md` #26; canon (NARRATIVE §5
  "one square scene", DESIGN §7 the fold) is UNCHANGED until it is decided + wired.
- **2026-07 — The storm's STAGE: ev-driven surface darkening (`TODO.md` #25,
  LIVE).** The first LIVE slice of the storm-King redesign, and the stage the
  amalgam-cut flood will later fill. The surface world (`STORM_STAGE_SCENES`:
  Brimley + `OUTDOOR_SCENES`) now DARKENS with the evidence count: `_draw_dark`
  runs there too, at a gloom that ramps with the rot stage (`STORM_DARK_GLOOM =
  (0, 44, 92, 138)`). Stage 0 is full day (gloom 0 → early-out, so ev0 is
  byte-identical, `capture_world --diff` clean); by stage 3 it is night, the
  civic yard-lights threading the roads become ISLANDS (the existing lightmap
  clears a pool under each), and the flashlight is enabled outdoors
  (`_flashlight_lit`) so its light-draws-Him double-edge (`VIS_LIT_RISE`)
  applies there too. The whole-frame lightmap multiply darkens the sky for
  free, and the blind-spot sight fog (`_draw_sight_fog`, drawn AFTER
  `_draw_dark`) darkens + thickens with the same stage gloom so the UNSEEN
  region matches the night instead of reading as a bright gray wash over a
  dark town (the blind spot should be the darkest). Framed as world rot's
  LIGHT twin (the ashfall's companion, DESIGN §2):
  *understanding* thinning the veil, NOT a day/night cycle — the "one
  continuous daytime state" invariant holds (no `day_phase`/`day_count`;
  NARRATIVE reconciled). VISUAL + flashlight only; the light/dark COVER split
  and the storm flood are the next slices (`TODO.md` #25). Full gate green.
- **2026-07 — The Mask became a REAL 3D object + the bearer power-up settled
  (dormant, `TODO.md` #25).** A visual pass on the storm-King's Mask. It had
  been a flat billboard (a front card and a back card, foreshortened by a
  horizontal squash) that collapsed to a straight sliver at profile and read
  flat; a stopgap "edge crescent + nose" only made it worse. The maintainer's
  call: "one object that rotates," no swapping between drawings, no nose.
  Rebuilt as **`draw_pallid_3d`** — a single curved SHEET, the FRONT CAP of an
  ellipsoid (semi-axes Rx<Ry, a REAL depth Rz), a bent oval of "paper", NOT a
  closed egg — rotated by `yaw` and projected, so the face, the bent-crescent
  profile (depth Rz, never a flat line and never a solid oval), and the pale
  concave inside seen from behind all fall out of the SAME geometry. (A closed
  ellipsoid was tried first; its dark FAR cap showed at profile and read as a
  solid egg, so the far cap was dropped — the maintainer's "a mask is a bending
  piece of paper.") This SUPERSEDES the earlier sub-player + "always
  camera-facing" rule: the Mask is player-scale and a prop that turns to face
  you or away, respecting the tilted world (the flat `carved_pallid_surface`
  is kept only as the face-art reference; the transient
  `carved_pallid_back_surface` / `_mask_edge_crescent` swap helpers were cut).
  A follow-up pass gave it the 2D look: the carved face (pale plate, deep jagged
  sockets + gold pupils, centre seam, hairline crack) is drawn as 3D-anchored
  overlays on the FRONT face ONLY, so they cull as it turns — **no eyes from
  behind**. BOTH sides render in the pale bone colour, so from behind it reads
  as a mask (its pale concave inside), never a dark half; smoothed (high
  ambient + resolution).
  The **bearer power-up** also settled: the possessed amalgam is simply a
  BIGGER amalgam (`BEARER_SCALE`) wearing the Mask + a crown of ember-cuts
  (`_bearer_crown`) — size is the tell, not a busier body (an earlier chaotic
  version with fused extra bodies, a gold rift, scattered eyes, and big
  reaching arms was cut; the maintainer kept the crown, dropped the arms).
  Still dormant (mask=None for every ordinary amalgam → byte-identical, full
  gate green). Previews `tools/preview_mask_spin.py` (the full spin) +
  `tools/preview_bearer.py`.
- **2026-07 — The storm ENGINE (`systems/storm.py`), dormant.** The second
  slice of the storm-King redesign (`TODO.md` #25): a standalone `Storm` sim
  the game imports nowhere yet. It holds the single migrating Mask bearer (the
  Mask sinks on one unit and rises from another, one storm-wide), units that
  drift toward His **lagged sense** of the player (luck, not omniscience: the
  sense snaps to your true position only every few seconds), and the
  **light-slows-never-burns** rule (a lit unit is slowed to a fraction and
  eases back out of the pool, but is never dispelled — that stays the
  Watchers'). The Mask draws at **player scale** (the maintainer's "the full
  1", revising the earlier sub-player sizing). Preview `tools/preview_storm.py`
  runs it over time (the Mask migrating #5→#2→#0, the flood massing on the
  refuge, the pool staying clear). Integration (real dark-spot anchors off the
  darkening, tilt projection, the catch, retiring THE UNFOLDING) is #25's later
  slices.
- **2026-07 — The Pallid Mask part (the storm-King redesign's first slice,
  dormant).** The maintainer began reworking the King away from THE UNFOLDING
  (`rendering/king_unfold.py`, the 4D everting mass) toward the shadow family's
  apex: the King as a **STORM** with no single body, His attention flooding the
  dark, and the Mask carried through it as a **part**, not a face. Ran as a
  concept loop in scratchpad (v1 floating mask → rejected; masked apex body →
  "just another amalgam"; the mask-as-part with one migrating bearer →
  approved). This slice landed the **art asset only, dormant**:
  `carved_pallid_surface` (the bone↔wood carved-pallid mask, no halo/mouth,
  deep recessed sockets, gold pinprick) + `draw_pallid_mask_part` (it rides
  out of its own cut, held at the rim, **sub-player scale**, **always
  camera-facing** — His regard, the one VISION exception) + a `mask=` kwarg on
  `draw_amalgam_sprite`. It is NEVER dealt by `assemble()`, so every ordinary
  amalgam is byte-identical (full gate green, `capture_world --diff` clean).
  Preview `tools/preview_pallid_part.py`. The storm STATE (one migrating
  bearer, light-slows-not-burns, corn-fills-with-dark, retiring THE UNFOLDING)
  is designed but unbuilt — `TODO.md` #25 carries the locked decisions and the
  build order; canon still describes THE UNFOLDING because that is what ships.
- **2026-07 — The Watcher-variety program landed as THE AMALGAMS**
  (`rendering/amalgam.py`, `AMALGAM_CHANCE`, DESIGN.md §1). The program
  ran as a maintainer-driven concept loop in session scratchpad: a
  15-design "Watcher variants" sheet (rejected: "shapes with eyes"), a
  pivot to motion-first SHADOWS (octopus/cockroach gaits, then chimeras),
  the approved BONELESS STILTER glide rig, a fusion round (portal-stuck /
  goop-of-eyes / mothman seeds), and the PORTAL GUY -- a torso wedged at
  a razor cut, relocating by crawling back through it -- whose BACK view
  (a smoke body with working arms) sparked the breakthrough pitch: **stop
  designing individual shadows; build creatures out of MULTIPLE cuts.**
  ("Fuck creating shadows, we make amalgams now.") The portal guy and the
  earlier one-off designs were retired into the system: a 17-part library
  (9 limbs, 6 body masses, 2 bare apertures), one grammar throughout
  (flesh clipped dead flat against a free-form cut, rim lip on the absent
  side, shroud palette, ember eyes, haze tissue), every part carrying its
  own enter/leave (limbs walk backwards into their cuts -- the portal
  guy's trick generalized; masses breathe themselves shut) and idle
  (breath, weight-shift, drips, drifting eyes). An amalgam is DATA: a
  seeded 3-5 part deal under composition rules (>=1 weight part grounded,
  masses centre, senses high, ALWAYS >=1 eye-bearing part -- an eyeless
  line-up next to the OG Watcher caught the generator truncating the eye
  slot, and the dim-ember tone was brightened to survive game scale).
  Behavior is deliberately untouched (the family contract: every shadow
  acts exactly like the OG Watcher -- spawn rules, hold, gaze/axe/round/
  light dispel); the wiring adds presentation only: `AMALGAM_CHANCE` of
  `_spawn_watcher` manifestations wear the amalgam skin, `npc._birth`
  drives a staggered part-by-part build-out, and the gaze-dispel fraction
  (`npc._gait`) plays the dispel as a PEELING. Blessed-but-open ideas
  live in `TODO.md` #21: per-part beam burn, hold-timer build-out. The
  FRAME idea (one huge empty cut as a super-rare shadow) was pitched and
  retired ("doesn't fit here").

## The King, the Moths, the evidence ladder

- **2026-07 — The Moths were CUT entirely (reverses the addition below).**
  The herald swarm was removed root and branch: the sim
  (`_new_moth`/`_spawn_moths`/`_tick_moth_shed`/`_tick_moth_seek`/
  `_moth_seek_spot`/`_tick_moths`/`_moth_spent`/`_log_moth_note` in
  `rot_mixin`), the art (`rendering/moth.py`, deleted), the `MOTH_*` config
  block and `MOTH_SCENES`, the `game._moth_field` init + the three per-frame
  ticks, the render draw pass, the moth-lamp dark-cover break, the
  `the_moths` case note, and `tests/stealth.py` §9. **Why:** the moths never
  had a home in the fiction (NARRATIVE never named them — they were pure
  mechanic); they doubled the Watchers' "His attention made local" job; and
  they inverted the game's own light metaphor (light draws Him, yet a moth
  is the thing drawn to light). The ladder's telegraph beats survive intact
  as the `the_turning` (ev2) and `the_breath` (ev3) notes; nothing gated on
  moths, so no progression changed. **One consequence:** the moth flare was
  the blackout system's only live trigger. The blackout machinery
  (`_tick_power`/`_genset_down`/`Scene.power_on`/`BLACKOUT_DUR`, DESIGN §6)
  is KEPT as the light-pillar foundation, now trigger-less in play and
  guarded synthetically by `tests/stealth.py` §17 (which drives
  `_genset_down` directly); the gas-genset fuel/failure economy that will
  fire it is deferred (`TODO.md` #21). Docs reconciled: DESIGN §1 ladder,
  CLAUDE.md layout/code-map, TODO #21/#23, DIALOGUE.md Part B,
  creature-design skill.
- **2026-07 — The evidence ladder built out in full.** Ev 0: town reads
  wrong but no cult patrols spawn. Ev 1: cult wakes. Ev 2
  (`KING_TURNS_HEAD_EV`): a telegraph note ("the_turning") — his attention
  finds the player, but he hasn't moved, so ev3 isn't an ambush. Ev 3: the
  roam arms, but a ~25s grace window (`KING_ARM_GRACE`) holds him at
  distance first (`the_breath` note) — the window to reach the lodge for
  the Invitation before the hunt truly begins. This staged telegraph
  (rather than an instant spike at the gate) was a direct response to
  played sessions where crossing 3 evidence felt like an ambush.
- **2026-07 — The Moths added as the King's herald and first flying
  entity** (`rendering/moth.py`, sim in `systems/rot_mixin.py`). They
  persist and stack per room the King lingers in, kindle on approach, and
  flare into a loud, visibility-spiking, cult-converging event if not
  spent in time. First flare files a note, never evidence.

## Close-up tableaux & the dialogue verb

- **2026-07 -- #13b interior-voice trim, first pass.** The maintainer's
  grievance was that "every interaction does something and never leaves the
  player thinking" -- on-screen narrator captions fire on nearly every
  world-prop examine, and several editorialize the conclusion the player was
  meant to draw. Applied the pattern "state the fact and stop" to the three
  clearest caption-only flavor examines (all non-canonical `_evidence` calls
  that write nothing to the book, none flow-guarded): the **dead well** lost
  its dry-well recap + "no way down it if there were" conclusion (the
  bottomless shaft lands alone; the re-read notice still carries the
  no-way-down fact); **`the_burning`** lost the "big enough to stand a family
  around" framing and the "what it burned was not all wood" lead-in (the
  slagged effects in the ash are the tell); **`threshing_floor`** lost the
  "the town's whole harvest, carried down and never carried back up"
  conclusion. `DIALOGUE.md` reconciled; full gate green. The fuller ~30-site
  sweep (procession candles, the ledger re-examine, placeholder one-liners)
  and the decision on the `_REVISIT_NUDGES` remain open per `TODO.md` #13b --
  they are taste calls left for a maintainer read of this pattern first.

- **2026-07 — The ask-questions dialogue verb, piloted then expanded to
  all six principals + the chorus (`TODO.md` #1).** Before this, every NPC
  conversation was a linear press-E counter. Built `ui/conversation.py` (a
  small state machine driven by float-speech `on_complete` chains +
  `dialog.show_choice`), piloted on Mr. Sable, then expanded to Toby,
  Hettie, Vane, Crane, and the chorus (Old Pell, Mrs. Calder, Royce,
  Garrick). Every principal's menu leads with the same two PI-initiated
  openers (introduce himself, show the photograph) since the sealed town
  means news doesn't spread.
- **2026-07 — Close-up examine tableaux built out to all six principal
  seats plus the Talk and the pedestal (`TODO.md` #2b).** Piloted on the
  bedroom writing desk, then landed as the presentation for every
  face-across-a-table principal conversation in order: Sable → Vane →
  Hettie → Crane → Toby → Mara (the last seat, carrying the unmask REVEAL —
  she opens listed as "One of them," masked and hooded among the
  congregation, until the greet beat pulls the mask away). THE TALK
  (the first cult grab) and THE PEDESTAL (the Sign Chamber altar, an
  object close-up rather than a person) shipped in the same arc. A sound
  pass followed (`lean_in` on open, a per-seat room tone) once the
  world-freeze was noticed to have left every close-up in dead air.
- **2026-07 — Tableau-scene environment parity pass (`TODO.md` #2c).** A
  parity audit found the close-ups showed props the walkable scene didn't
  actually carry (Hettie's till, Crane's lectern, Vane's gun cabinet,
  Sable's key rack, Toby's crayon drawings, the altar's mask). Dressed each
  walkable scene to match its close-up, one at a time, VISION-verified.

## The newspaper choice (favor economy pilot)

- **2026-07 — Landed (`TODO.md` #2).** The PI's starting April 14 paper
  became a one-copy, choose-the-recipient gift with six mutually exclusive,
  incommensurable doors (Hettie/cartridges, Royce/batteries+testimony,
  Pell/mercy, Toby/funnies, Sable/the tell of no reaction, Vane/the trap —
  the one recipient whose allocation is tracked as a hidden despair
  consequence rather than pure mood). Never evidence, never gates an
  ending. Pilot for a broader "favor economy" that has not been built past
  this one instance.

## Walls & interior geometry

- **2026-07 — Doors and windows join the thin-slab walls (`_gap_slab`;
  the "glitched door" / "wrong windows" playtest finds).** In slab scenes,
  a door or window tile extruded as a FULL-tile box (its char isn't a wall
  char, so `_wall_slab` returned None) while the wall around it was a
  half-tile slab -- every doorway and window read as a near-black full-tile
  monolith jutting from the thin wall line, with the pane floating on the
  phantom face. New `_gap_slab` carries the flanking walls' band through
  the gap tile; the door lintel, window box, and pane face-plane all take
  it, in the wall's material tint. The flat full-tile window art is skipped
  under tilt in slab scenes (it peeked out past the band as a lit strip at
  the wall's foot), and interior panes now glaze with flat overcast
  daylight instead of the facade's warm lit-from-within amber. Also cut in
  the same sprint: the bedroom's "You wake up." first-step notice (the
  room, the light, and the muffled wake audio already say it).

- **2026-07 -- #4c interior-door rollout COMPLETE; four interiors left whole
  on purpose.** With the shop pilot, the church vestry, the barn, the abandoned
  farmhouse, the sheriff's office, and Toby's closet all doored, the rollout is
  done. The remaining candidates were assessed and deliberately LEFT undivided,
  per the settled principle (the door mechanic completes buildings that ARE
  divided but lack the leaf; it never forces a warren onto an authentic open
  space):
  - **schoolhouse** -- the fiction is a "one-room schoolhouse" the commune
    crammed into as an open dormitory ("they slept all over then"), and the
    chalk-door rite fold stands in the open middle of the floor. A partition
    would fight both the fiction and the rite geometry.
  - **lodge (common room)** -- a deliberately open-plan hotel common room; its
    col-7 counter peninsula replaced a wall on purpose, so re-walling it would
    revert that choice.
  - **lodge_hall** -- already a "hall of rooms": its rooms (the spare room, the
    two guest rooms, the loft) are separate scenes off the corridor, and its
    locked 'l' facade doors are deliberate uncanny dressing (they open onto
    nothing), not real subrooms.
  - **lodge_cellar** -- an authentic single L-shaped storage cellar, "strictly
    a one-way-down room" with no side room to divide.

  The single hotel guest rooms and the PI's bedroom are single rooms by nature.
  TODO #4c's interior-door-rollout half is closed (the wall-material Phase 4 +
  the deferred church-apse shapes remain).

- **2026-07 -- #4c: Toby's closet got a curtain (the refuge, kept gentle).**
  The kid's house was room + closet through an OPEN col-5 gap. Toby's house is
  a SAFE_SCENE refuge, so the leaf is the gentlest in the set: a maroon
  `curtain` (`add_inner_door(5, 3)`), a drape over a child's closet nook where
  a plank door would read too institutional. Shut (its default), the opaque
  drape keeps the closet the BLIND SPOT it is meant to be -- the corn dolls,
  the phantom marks, and the crayon King stay hidden until the player draws it
  back (the shut curtain blocks the sight cone; open passes). The col-5 wall is
  N-S, so it hangs across an E-W doorway. No lighting concern (the refuge stays
  flat-lit). Reachability holds (smoke [10/10]); VISION-verified four facings.

- **2026-07 -- #4c: the sheriff's office rebuilt into FOUR rooms.** First pass
  just doored the existing records gap, but the office still read as "two rooms"
  (maintainer). Redesigned the whole interior on a cross of partition walls into
  four legible spaces: a public FRONT (the entry off the field), Vane's OFFICE
  (his desk + cot, behind a see-over front counter), the back RECORDS room (the
  case board, the payphone, his ammo cabinet, Mara's booking slip), and a
  BOOKING room with the barred holding CELL. Connected by inner doors in VARIED
  walls + kinds: a see-over **`half` counter** (front<->office, the FIRST
  shipping use of that kind), `plank` leaves (office<->records swings E-W,
  records<->booking swings N-S), and the cell's `bars` gate. Every room carries
  its own genset `wall_lamp` + a candle (no dark box). Load-bearing wiring
  preserved: `maras_record` (the booking slip) stays in the records filing table
  and the ammo cache still drops there (world-persistent, no soft-lock), Vane
  still watches from his desk. Grid validated (no diagonal-only joins);
  reachability holds through the door chain (smoke [10/10] flood-fill); LOS
  correct (opaque leaves block shut, the counter + bars see through);
  VISION-verified four facings + real-view dark + a counter close-up.

- **2026-07 -- #4c: the abandoned farmhouse became a four-room warren.** The
  farmhouse was a "box + one side room"; a house warrants real rooms, and
  being abandoned it carries almost no load (just the sealed cellar hatch).
  Quartered it with a cross of partition walls (a col-6 vertical + a row-4
  horizontal meeting at a solid corner) into a KITCHEN (the entry), a PARLOR,
  a BEDROOM, and a BACK ROOM (the hatch), connected by three inner doors in
  varied walls (a curtain over the bedroom, plank leaves elsewhere; the
  kitchen<->parlor door swings E-W, the two cross-wall doors swing N-S).
  Re-dressed per room: the preserves shelf in the kitchen, the open birdcage
  in the parlor, the bed in the bedroom, the hatch in the back room, and a
  candle burning in each (the farmhouse keeps the darker gloom + candles, so
  the division needed a light in every room -- who lit them, in an empty
  house). Reachability holds through the doors (smoke [10/10]);
  VISION-verified four facings + dark.

- **2026-07 -- #4c: the barn divided into a three-room warren.** The barn was
  the flagship "box + one back stall" grievance, but its open floor is the
  commune dormitory ("they slept all over then"), which should stay open.
  Resolved by dividing the UPPER floor with a row-5 partition into a FRONT BAY
  (the entry + racked gear) while keeping the LOWER floor the open dormitory
  (all six bedrolls sit there, the read intact); the old back stall is the
  enclosed WORKROOM (Mara's journal + the sealed hatch). Two `plank` inner
  doors in varied walls: the front-bay door swings N-S (E-W wall), the workroom
  door swings E-W (N-S wall). Both start shut; a shut leaf blocks the sight
  cone, so the workroom is a real back blind spot. The division cut the
  dormitory off from the front-bay lamp, so a second genset wall_lamp was hung
  on the partition to light the sleeping floor. Reachability holds through the
  doors (smoke [10/10], no diagonal-only joins from the new wall);
  VISION-verified four facings + dark.

- **2026-07 -- #4c interior-door rollout continues: the church vestry got
  its swinging leaf.** The church was already nave + vestry + bell-tower,
  but the vestry was reached through an OPEN gap -- no door mechanic. Added
  a `plank` inner door on that gap (`add_inner_door(3, 6)`): shut, it blocks
  the sight cone, so the vestry (the preacher's quarters + the tower stairs)
  is now a real shut-able blind spot a pursuer's line of sight breaks on,
  not just a doorway. It starts closed (the preacher opens his own way
  through on his cot round; the player toggles it with E) and sits in an E-W
  wall, so the leaf swings N-S -- varied from the shop's E-W-swinging
  stockroom/pantry doors. Reachability holds (smoke routes through the gap
  tile); VISION-verified the leaf reads from all facings. Still open per
  `TODO.md` #4c: the barn, sheriff's office, schoolhouse, Toby's house, the
  Lodge interiors.

- **2026-07 -- Wall-material rollout finished: Phase 2 complete + Phase 3
  (the mine as hewn rock).** Wave 3 opted the remaining above-ground
  interiors into `_SLAB_STYLE` (`barn` + `abandoned_farmhouse` = timber,
  `schoolhouse` = plank, `lodge_hall` = plaster, `lodge_cellar` = stone, the
  first stone scene), completing Phase 2 -- every above-ground building
  interior now renders thin material-coloured walls. Phase 3 added the `rock`
  material and `_ROCK_STYLE`/`_ROCK_SCENES` (the 16 Works/Depths/Mara's-cell
  scenes): full-thick (`thick`=1.0) but the rough-outline + prism draw, so
  the hewn walls read irregular, not blocky. Because `thick`=1.0 makes
  `_wall_slab` return full-tile bands AND rock stays OUT of `_SLAB_SCENES`,
  collision/sight/nav read the tile grid UNCHANGED (the roughening is
  draw-only, the mine's stealth footprint untouched). Guarded by
  `tests/stealth.py` §16; every non-slab/non-rock scene stays byte-identical.
- **2026-07 -- Redecoration-audit deferred polish landed, and a render-recipe
  bug that had hidden a defect.** The LOW items from the 17-scene visual audit
  shipped: the bell tower got a bespoke timber bell-stock (a braced trestle,
  not a scaled table box), the schoolhouse cots were jittered off the grid,
  `_draw_hanging_figure` was redrawn as a suspended pendulum body (was a
  standing hooded blob), the lodge missing-flyer/polaroid "wall of the
  vanished" was clustered above the desk (KEPT, not cut -- surface town-dread
  dressing, distinct from the underground read that was cut), and the
  lodge_hall sampler/side-table were re-homed. The barn was also dressed as a
  commune dormitory (six bedrolls + shed belongings, Toby's "they slept all
  over then"). **The catch:** the bell-stock ran every beam E-W (planar in X)
  and collapsed to a thin diagonal stick when viewed edge-on from E/W -- but
  it "passed" a four-facing check because the ad-hoc render script never set
  `camera.yaw` (that copy lives in `_update_look`, which the headless path
  skips), so every "N/E/S/W" capture stayed at yaw 0, the NORTH facing, four
  times. A whole session of "VISION-verified four facings" was really
  north-only. Root-caused, `VISION.md`'s render recipe corrected to spell out
  the `camera.yaw = look.cam_yaw` step (+ a "confirm the room rotates" check),
  the bell-stock rebuilt with a mid-height ledger ring + N-S top caps so it
  carries members in both planes and reads as a frame from every facing, and
  the session's other touched scenes re-swept from genuine four facings (all
  clean; the rest were facing-invariant standees / wall-decos / floor-decals).

- **2026-07 — Four-stage evolution of interior wall rendering, landed
  incrementally on the shop pilot then rolled out.** (1) **Beveled convex
  corners** — chamfered the chunky 90° jut where a partition wall met open
  floor, draw-only. (2) **Thin-slab walls** — walls became real thin-slab
  geometry (not just a draw trick): `_wall_slab` returns the footprint as
  up to two bands, read by collision/sight/nav as well as both draw
  layers, so what the player bumps is what they see. Superseded the bevel
  where both applied. (3) **Rounded corners** — `_rounded_wall_poly`
  fillets free (floor-facing) corners while keeping wall-seam corners
  sharp so runs still connect flush. (4) **Per-material styles**
  (`_WALL_STYLES`: plank/plaster/timber/brick/stone, each with thickness,
  corner round, roughness, and a dark muddy tint) — a room's construction
  now reads from geometry and colour together. Rollout order: shop
  (pilot) → Wave A refuges → the three principal seats (church, sheriff's
  office, lodge) → barn/schoolhouse and the mine still open. A same-session
  rule was added after the shop pilot exposed it: two walls that meet only
  at a diagonal render as disconnected thin stubs under the slab system,
  so `tests/smoke.py` now fails any such layout.
- **2026-07 — Interior doors added as a third door kind (`DESIGN.md`
  §7).** Distinct from fade-doors (scene boundaries) and see-through doors
  (a different scene's room shown through an opening): a swinging leaf on
  a floor gap within one scene, splitting a box building into subrooms. A
  shut leaf blocks both body and sight (so it can break a pursuer's lock);
  most start closed and auto-open for NPCs. Piloted on a full shop
  redesign (an L-shaped floor → stockroom → pantry, two doors deep).
  Rollout to the remaining box-shaped interiors (barn, church, sheriff's
  office, schoolhouse, Toby's house, the Lodge) is still open per
  `TODO.md` #4c.

## Combat feel

- **2026-07 — The axe swing redesigned (TODO #25, landed).** The old
  swing walked a constant-speed 150-degree arc with a faint trail -- a
  windscreen wiper. The redesign maps three phases onto the same prog
  window: a WIND-UP that pulls the head back past the start side and
  lifts it off the shoulder (anticipation), a STRIKE that crosses the
  whole arc in a sharpened smoothstep burst with a bold two-ply motion
  smear (the snap), and a FOLLOW-THROUGH that overshoots and settles.
  Haft reach breathes with the phases. Same signature, same call sites,
  same chop-stun timing (error class 9 untouched); verified on a
  nine-phase headless strip.
- **2026-07 — Swing retune + the axe OBJECT redesigned (maintainer:
  "it's the design of the axe itself").** Retune first: the wind-up cut
  to a ~50ms flick, the smear detached from the live head (joined, it
  read as a bent haft) with its angular spread clamped, and the recover's
  last half blends angle+reach into the held pose so the carry takes over
  with no pop. Then the object: the old bare-line haft + symmetric pale
  wedge (a spade) was replaced by shared `_axe_haft`/`_axe_head` helpers
  used by both `draw_axe_swing` and `draw_axe_held` -- a curved tapered
  haft with a fawn's-foot butt, and a one-silhouette fire-axe head (flat
  squared poll in darker struck steel, waist at the eye, CONCAVE flanks
  flaring to a bit WIDER than the head is long, a bright slightly-convex
  honed edge). Iteration notes that cost renders: straight diverging
  flanks or a lit band at the wide end read as a lampshade/bell; a bit
  longer than wide reads as a funnel. The arc + carry side now MIRROR for
  west-ish facings (`sgn`) so the bit always leads the travel and the
  edge never hangs up-screen (the bowl read), and the carry droops
  `_CARRY_TILT` (~26 degrees) off the facing line so the head sits in
  three-quarter (a dead-level carry pointed the bit straight down-screen,
  the one angle with no profile). Verified on 4-facing held + 8-phase
  swing sheets at 5x and 2x, plus the swing GIF.

## The interiors pilot (2026-07, TODO #24)

- **2026-07 — Wave 2 rollout: the sheriff's office quad.** Six
  separates became two composed objects. The LAWMAN'S WALL (west-wall
  run): his cot with the blanket tucked army-tight and a worn pale
  sit-spot, boots squared toes-out under the frame, the washstand with
  standing water and a hung towel over its rail, the antler rack
  carrying his winter coat (the empty prongs say the hat and belt are
  on him) -- plus the walked line along the run and the washstand's
  drip stain. The LAWMAN'S DESK: the two-tile desk with its modesty
  panel, case files squared, the tin mug on years of rings, the radio
  with grille + dial + antenna at the back corner, the chair yaw-tucked
  half under the working side, boot scuffs where he stands. Footprints
  stamp the old separates' exact tiles. Verified on four-facing +
  clean-inspection sheets.
- **2026-07 — Wave 2 rollout: the shop's stockroom receiving corner.**
  The stockroom's prop soup (two loose crates, a bare table, a barrel)
  merged into ONE `stockroom_corner` ensemble per the rule: a yawed
  crate stack against the west wall, the check table with paper sacks
  and the receiving ledger, the flour barrel with a chalked lid and a
  dropped scoop -- and its wear layer in world space (the dust ghost of
  sold-out stock, the stopped chalk tally on the wall, the shipped twin
  barrel's ring stain, drag scuffs, a dry grain spill). The candle
  stays its OWN deco seated on the check table so it keeps emitting
  (an ensemble must never swallow a light source into dead art). The
  footprint stamps the exact tiles the old separates held, so
  reachability and Hettie's stockroom station are untouched. Verified
  on a four-facing in-room sheet.

- **2026-07 — The lodge pilot COMPLETE (ensembles 2-4 + the host).**
  The dining set (the one set place, the dust-shadow of the second, live
  candle, yaw-tucked chairs, splinted leg); the service bar dressing
  (pitcher, ready tray, towels, the one used glass) with the desk-to-bar
  corner welded into a single front-of-house L; the hearth as a real
  masonry mass (firebox + breast past the eave, mantle + candle, tools,
  log basket, the buck's antlers rehung on the breast, soot + ash).
  Sable's front view got the V shirt-front + smile + watch chain, his
  key rack tripled to the pigeonholed wall of keys with ONE empty hook
  (the PI's room), and a latent fade bug died: the prop occlusion fade
  assumed a generic tall box, so an NPC behind their own counter faded
  it permanently -- furniture now fades against its real spec height.
- **2026-07 — The kitchen wall lands (the first ensemble).** The lodge's
  loose stove + the north-wall ham + scattered kitchen intent composed
  into ONE `SOLID_PROPS` object (`kitchen_wall`): cookstove on legs with
  ember grate, stovepipe climbing past the eave with a wall elbow,
  counter run with pot shelf over, three hung pots, the house ham on the
  shelf hook, a wood crate under the lip. Placed on the west wall over
  'x' see-over stamps (the car pattern); the old raw 'k' stove tile the
  furniture stamp had been hiding was cleared (smoke [9/9] caught it).
  Also scrubbed en route: the capital-H "Hunter" entity (a cut design)
  from the backwoods cabin's display name + docstring.

## The Lodge (2026-07 quality sprint)

- **2026-07 — Sable reachable across his desk (counter-aware talk reach).**
  The NPC-talk check was a bare 40px literal in two places (try_interact +
  the [E] cue); pressed flat against the reception counter the PI still
  stood ~48px from Sable, so E fell through to the register beat and the
  host could never be spoken to from the front. New `NPC_TALK_REACH`
  config default + per-NPC `npc.talk_reach` override; Sable and Hettie
  (the two counter seats) get 56. Flow-guarded (E across the desk front
  opens Sable's tableau).
- **2026-07 — The padlocked cellar hatch is a real volume.** It was only
  the flat 'L' exit tile (playtest error class 7: a raw object tile under
  the tilt); the existing `cellar_hatch` SOLID_PROPS volume is now placed
  over it, with new `padlock` / `open` lid states (the lodge's
  freshly-oiled padlock; the lid swings up once unlocked, synced from the
  `cellar_unlocked` flag on entry). Barn/farmhouse hatches keep the
  nailed-shut cross-board default.
- **2026-07 — Sable's loft room re-laid.** The bed straddled the door
  column at the room's front (error class 8); it moved to the back corner
  under the dormer window (nightstand beside it, washstand down the west
  wall), and the bare south half gained his morning chair + a worn
  off-grid rug. The registry's stale "(locked)" annotation and the door-'1'
  comment were corrected en route.

## Camera & the world's edge

- **2026-07 — Sprite-native camera scale (`TILT_ZOOM` 0.72 → 1.10).** The
  first-five-minutes quality sprint's opening move. The tilt shipped zoomed
  out to 0.72 "to show more world", but sprites draw at fixed pixel size,
  so the zoom-out shrank the WORLD against the BODIES: rooms read cramped,
  props read as noise, and most of the frame was empty void — the
  maintainer's "the world feels too small compared to the player" and "it
  feels low quality" playtest verdicts in one constant. A headless A/B
  (0.72 / 0.90 / 1.00 / 1.15) showed rooms filling the frame and Brimley's
  props resolving into readable objects at ≥1.0; 1.10 shipped (slightly
  past sprite-native, so the world reads a touch larger than the body —
  the requested direction). Side effect: the visible window tightened
  ~47%, which is dread-positive (less information on screen).
- **2026-07 — The void surround: the map's edge composed
  (`scenes/terrain.py`).** Off-map tiles rastered as an endless field of
  `"."` default floor (per-tile jitter + macro shadow = the "checkered
  void" around every interior), and outdoor scenes hard-cut to black past
  their bounds (the maintainer: "all of the space outside the scene is
  black and it takes away from the scene"). The floor raster now skips
  off-map tiles; a new `_void_surround_pass` draws a three-tile rim that
  continues the nearest in-bounds ground under a deepening veil into
  near-black. Also fixed en route: `_draw_neighbor_strips`' skip
  conditions dropped every N/S and E/W edge strip (only diagonal corners
  ever painted), so the seamless-world seam never actually showed the
  neighbor scene's terrain; strips now paint true edge strips, drawn over
  the rim fade where a neighbor exists.

## Terrain & prop read (2026-07 quality sprint)

- **2026-07 — Trees consolidated, un-bound from tiles, and occluding by
  height.** A sprite-by-sprite audit found seven tree sprites and six of them
  failing: the spruce a flat cutout with no light direction, the bare
  deciduous an orange bole ending dead where its leader began, the scrub a
  set of faceted quads with a red pot at its foot (`draw_solid`'s base ring
  and cap on the stem), `bush` a flat floor sticker reading as a lily pad on
  a black pot, `creepy_tree` a camera-facing standee that swivelled to watch
  you, and the cutscene forest no longer closing into a canopy (a regression
  from the previous entry's crown narrowing). Only the skybox treeline
  passed. Three stages, all approved before starting:
  - **One renderer, three species.** `draw_tree_body` with
    `spruce` / `bare` / `brush`, sharing one palette family, one light
    direction and one height model -- which is what makes a stand read as one
    wood rather than a prop shelf. Five separate draws collapse into it,
    including the two decorations.
  - **Real heights.** `render_mixin` keyed EVERY occluder's depth sort and
    fade box at `_TILT_WALL_RISE` (26), counters excepted. A spruce stands
    about 50 and so under-reported the screen it covered; knee-high scrub
    over-reported by triple. Each object reports `tree_height` now.
  - **No privileged layers.** `draw_terrain_tilted` draws the flat layer
    first and returns the upright occluders for the caller to interleave, so
    a `_FLOOR_DECAL_KINDS` decoration could never occlude anything at any
    position. `bush` was one. It is a volume now, in the depth pass.
  - **`tree_footprint` -- the wall contract, for plants.** Authored per tile,
    placed freely inside it, blocking as a round foot, and that one function
    is the single source for the draw AND for collision, sight and nav
    through `Scene._obj_solid_here`. Jitter + foot is bounded under 0.7 of a
    tile so a tree cannot seal a corridor it was never authored into.
  - **Then the walk-through tree was retired entirely** (maintainer, on
    seeing the round feet: "that's perfect and allows for natural gaps for
    the player to slip through so we don't need collision-less trees").
    `p` -- 967 tiles, about half the forest -- existed because full-tile
    square collision makes a stand of trees a wall, so permeability had to
    be authored by hand. With round feet and a point-collided player the
    gaps are a property of the geometry: a band of solid trees still admits
    a straight north crossing at 25-55% of its width, far more diagonally.
    `_TILT_BRUSH_CHARS` is empty now and undergrowth is a `bush` decoration
    placed deliberately. `j` stays passable -- it is a hidden doorway -- and
    draws as an ordinary tree again, which is what made it hidden.
  - Two guards had to follow. `tests/smoke.py`'s reachability flood was
    tile-granular and 4-way, so it called a whole cell solid when most of it
    was clear and could not see a diagonal gap at all; it floods sub-tile
    through `is_solid_at` now in any scene with solid plants. And three
    hand-placed hide spots / noisemakers turned out to be sitting on
    scattered plants that had been harmless while plants were walk-through
    -- `scenes/__init__.py` clears a solid plant under authored content, so
    scatter can never win over a placement again.
  - Tree stature raised on the maintainer's mark-up: the old 40-54 spread
    became 50-64 (a wall is 26). The floor came up rather than the ceiling
    going higher -- the short ones were what read as scrubby.
  - Also: `OBJECT_DEFS` had claimed for some time that `p` is a "passable
    secret tree -- looks identical to T". It renders as low scrub and has
    not looked identical to `T` in a while; the comment was the wrong half
    of the contradiction and now describes what actually ships.

- **2026-07 — Ground and trees redesigned; the black patches in the grass
  found.** The maintainer: "update the design of dirt, grass, trees. They are
  all looking off. Are there black patches in the grass at certain angles."
  There were, from two causes, and both were found by A/B rather than by
  reading:
  - **Marsh mud `;` was the main one.** Base colour (40, 37, 30) -- a brown
    near-black -- sprinkled by the scene builders as ISOLATED SINGLE TILES
    through grass at (46, 58, 44). Tiles are cached BY CHAR, so nothing
    frays a boundary unless it is written to, and only the dirt path had
    been. Each marsh tile was therefore a hard-edged square of a different
    hue two-thirds the value of its surround: a black hole in the lawn. Wet
    ground is now the same ground, greyer, with the darkness coming from the
    puddles drawn on top; and `_build_path_fringe_card` was generalised from
    "the dirt path" to any `_PATCH_CHARS` tile, colouring its lobes from its
    OWN char, so every seam frays.
  - **Trees were double-shadowing.** `_SHADOW_CASTERS` included `T`/`p`, so
    every tree tile blitted a TILE-wide hard-topped gradient onto the tile
    south of it -- flat, in the floor raster, belonging to nothing the
    player can see, and overlapping into rectangles wherever trees are
    dense. Trees already lay their own contact pool.
  - **Dirt was the brightest thing outdoors.** (96, 76, 52) against grass at
    (46, 58, 44): the eye went to the road instead of the town. Now damp
    April earth. Its detail was three 2px rectangles plus, every fifth tile,
    a pale line spanning the FULL tile width at exactly y=16 -- a perfectly
    repeating scratch that becomes a vertical stripe on an E/W facing, the
    same defect the plank floor was fixed for. Replaced with fine grain,
    seated stones and a short scuff on a per-tile ANGLE.
  - **Grass was confetti.** A flat fill plus a handful of 2px rectangles at
    unrelated positions. Now clustered tufts (count and placement varied per
    tile, since a fixed count is its own pattern) and last year's straw mat,
    running mostly DARKER than the base. The first attempt ran them lighter
    and denser and read as lichen; that is recorded in DESIGN §6 as the rule.
  - **The tree redesign went into the wrong function first.** CLAUDE.md said
    trees stand up as `_tilt_standee` billboard cards. They do not and had
    not for some time: every billboard char routes to a volumetric
    `_tilt_tree_solid`, and `_tilt_standee` was reachable from nothing. A
    full canopy rebuild landed in the dead flat path before a render of the
    actual scene showed nothing had changed. `_tilt_standee` is deleted, and
    `tests/conventions.py` check 8c now fails if a billboard char has no live
    dispatch branch. (The flat `_draw_tree` survives -- it is live in the
    cutscene forest -- and kept its improvement.)
  - **The real tree.** Spruce tiers were `draw_solid` bodies of revolution,
    and draw_solid finishes every body with a `lo` ellipse ring at its base
    and a BRIGHTENED filled ellipse across its top; stacked four high that is
    a tree wearing hoops. `_spruce_tier` draws its own saw-toothed skirt
    instead -- drooping branch tips, no lid -- and the bole was thinned from
    a fifth of the tree's spread to a tenth (it had read as a keg standing
    under the branches). The bare deciduous got recursively forking limbs in
    place of single strokes radiating off the leader, and a tapered bole that
    continues into them rather than a capped cylinder, which had made it a
    fence post with nails in it.
  - **`tools/preview_terrain.py`** exists now for the same reason
    `preview_props_sheet.py` does: a floor char judged from a whole-scene
    capture is four pixels among props, actors and shadow, which is how a
    near-black tile in the grass survived. Blocks per char, `--seams` for
    char-vs-char boundaries, `--plants` for what grows on it.

- **2026-07 — The lodge yard dressed, and five props remade doing it.**
  The first real use of the parts-built prop pipeline on a scene, run as the
  maintainer asked for it: look, find, change, apply, judge, repeat. What
  the looking turned up is the entry.
  - **Six props shipped as MAGENTA SQUARES.** Converting a kind to an
    assembly correctly removes it from `SOLID_PROPS`, but `is_solid_prop` —
    the predicate the scene's solid-emit path actually asks — still read
    only the two old tables. So the scene called them flat decals, they fell
    through to `Decoration.draw`, found no `_draw_<kind>` method, and drew
    the unknown-kind placeholder. Conventions check 2 passed throughout: it
    tests the TABLES, and the tables were right. New check 8b asserts the
    predicate instead, and fault-injection confirmed it names the exact four.
  - **`lantern` was the wrong object entirely.** It had been converted as a
    hand-carried hurricane lantern — right name, wrong thing, a third of the
    height — while the unreachable `_draw_lantern_solid` beside it went on
    being the iron POST lamp every scene and both light tables had always
    meant. Its own light data settled it (`FIXTURE_POOLS` src_z 20, arm 0,
    warm, flickering, not electric: a flame directly over its own base at
    eye height). Remodelled as a garden post lantern with a tapered glass
    head; `prim.frustum` was added because a taper had no primitive and had
    been faked with a straight prism, which reads as a tin can. Check 8b now
    also fails a kind left in BOTH tables, since that dead draw is what let
    the disagreement sit unnoticed.
  - **`check_stature` (the size check proportion cannot make).**
    `check_proportion` compares a model against itself, so it is blind to a
    prop built perfectly at the wrong SIZE. The mailbox stood 36 units tall
    — a wall is 26, the player 20 — at a flawless 2.11 : 1 : 1.22, because
    the legibility exaggeration in the model's `k` got applied a second time
    to its post; from three of four facings it read as a bar on a stick.
    Every reference now records `world_h`, and the rule is that a mount
    height is in WORLD units, never the model's `k`. It caught the woodpile
    (8ft, taller than the player) and the fence (player-height posts on a
    wire yard fence) in the same pass.
  - **Variant factories.** `full=`/`axe=`/`gap=` were being passed by the
    scene and silently dropped, while the comments beside them described an
    axe and a gap nobody could see. An `ASSEMBLIES` value may now be a
    factory whose parameters are read from the decoration's kwargs, cached
    per combination. The mail juts out past the door end, the axe stands in
    the block, the fence bay's wire is down.
  - **Palette judged in the scene, not on the card.** `plank`, `concrete`,
    `paper`, `log_cut` and `tin` were set by eye on the preview sheet's
    neutral grey and turned out to be the palest objects in a Darkwood-dark
    yard — the stoop out-read the building it was attached to. Darkened;
    `wire` added because a bright fence strand drew the eye to the least
    important thing in the frame.
  - **`tools/inspect_spot.py`.** The dressing process asks for three
    altitudes and the isolated sheet and whole-scene capture covered only
    the outer two, so the middle one kept being skipped — which is how a
    woodpile got signed off at a magnification where proportion cannot be
    read, and how six magenta squares got called placed. Four facings on a
    named tile, zoomed, `--dark` for the light the player actually meets.
    It has to move `TILT_ZOOM` rather than `camera.scale`, because
    `_update_camera` re-asserts the scale every call — the same class of
    trap as the yaw, and it asserts the zoom took.
  - Placement fixes from the same pass: the woodpile moved against the
    woodshed (a stack in open dirt reads as dumped lumber), and the fence
    laid end to end at the bay's own width instead of every four tiles,
    where 42-unit bays with 86-unit holes read as four abandoned fragments
    rather than a boundary.

- **2026-07 — Plank floors read from E/W; macro shadow tamed.** Boards
  varied only per ROW, so a rotated (E/W) facing showed long uniform
  stripes ("the floor on the east/west looks like straight lines"); the
  board rects also overdrew the new smooth base cells and silently
  dropped the macro shadow indoors. Boards now carry along-the-run grain
  patches + staggered end-joints every ~3 tiles, with the macro shadow
  folded into the board shade. And the macro shadow's amplitude was cut
  (58 → 30 max, gentler curve): the old per-tile stepping read as
  texture, but once smoothed the full-strength blob read as the hard
  shadow of nothing (the playtest's "weird dark patch outside the
  cabin").

- **2026-07 — Solid props fade for occluded actors (the car fix).** The
  per-actor occlusion fade was wired only for wall tiles; the solid-prop
  emit blitted every card at full opacity (despite docstrings claiming
  otherwise), so the car -- the game's largest prop card -- blanketed
  whoever stood behind it. The prop emit now runs the same
  `occluder_alpha_box` fade the walls use. The car's footprint also went
  `'X'` → `'x'` (see-over, the counter precedent): a sedan is waist-high
  and should not carve a black wedge out of the sight cone.
- **2026-07 — The ground stops checkerboarding.** Floor brightness was
  three per-tile constants (base, ±6 whole-tile jitter, one macro-shadow
  alpha), so every variation landed as a hard-edged 32px square.
  `draw_floor` now evaluates sub-tile value noise + the macro shadow per
  8px cell, bilinear across tile corners SHARED with neighbouring tiles,
  so brightness rolls smoothly across tile edges. Cost only on first draw
  (tiles are cached); animated water keeps the flat fill.
- **2026-07 — North-woods April trees.** The old tree was a symmetric
  green body-of-revolution canopy -- summer foliage in a fiction set the
  week the ice went out, and it read as a faceted lampshade ("weird
  shaped trees"). The stand is now ~2/3 boreal SPRUCE (ragged dark cones
  of jittered stacked tiers -- the shape the renderer is genuinely good
  at) and ~1/3 BARE deciduous (trunk + seeded branch strokes, nothing
  leafed). Seasonally true and darker on the skyline.

## The light pillar (2026-07, wave 1)

- **2026-07 — The flashlight opens on the PI's desk.** Moved from the
  woodshed stump to the bedroom desk tableau, beside the pistol: the
  maintainer's light-pillar mandate makes light the game's spine, so the
  player's hand on it starts in the opening close-up (and a PI carries
  his own light; finding it in a shed was always a little false). New
  menu option + close-up art + `desk_flashlight_taken` flag; the
  woodshed keeps the axe.
- **2026-07 — The deep beam-off retired.** `CULT_DARK_SCENES` swallowed
  the flashlight by design ("the dark here is not the kind light
  fixes"), and TODO #21 carried "retire this?" as an open dread
  decision. The maintainer's playtest verdict settled it: it read as
  broken, not dreadful, and a deliberate mechanic that reads as a bug to
  its only player is a bug. Light works everywhere now; the deep keeps
  its deepest gloom tier + the cult's own fires, and the beam stays
  priced (visibility burn). The beam-off notice + HUD line were cut with
  it.

## Lighting

- **2026-07 — The reverse light, moving sources, and the Watcher spawn
  rules (maintainer batch).** Three connected pieces. (1) The
  `dark_pool` deco: an INVISIBLE placed dark source (kwargs `r`,
  `depth`) that SUBTRACTS from the lightmap after every light has
  added, so placed darkness always wins where it contends with a lamp
  -- blackness blacker than ambient, authored exactly where the design
  wants it (pilots: the shop pantry's cult tells, the barn's SE
  corner); the audit draws it as a deep-blue ring. (2) Moving light
  sources are expected: `Scene.light_sources` now caches the emitter
  DECO LIST and readers take positions live, so a carried or swinging
  source gates correctly in the mechanical layer (the visible lightmap
  was already per-frame). (3) The Watcher spawn rules: a Watcher opens
  only at a spot that is DARK (`lit_at`) and holds LINE OF SIGHT to
  the player (`clear_sight_line`) -- never in a sealed room or
  out-of-bounds pocket you cannot answer with your gaze, which kills
  unanswerable accumulation AND delivers lit-rooms-secured for free (a
  room with no dark spot in view of you cannot open anything; a
  blackout un-secures it). Guarded by `tests/stealth.py` §11 (every
  spawn dark + sighted; the sealed pantry opens nothing).
- **2026-07 — The lightmap: darkness composes by accumulation
  (maintainer: "the lights aren't interacting with each other
  properly").** The gloom pass used to punch per-pool alpha holes in a
  dark overlay, painter's-order -- where two pools overlapped, the
  later pool's dim rim overwrote the earlier pool's bright centre, so
  every pendant kept a visible ring seam and adjacent lights never
  combined. Rebuilt as a true lightmap: every source (pools, cone
  fans, the flashlight beam, the player's bubble) ADD-accumulates into
  one luminance field over the room's ambient, and the frame is
  multiplied by it once. Overlapping pools now genuinely brighten
  their shared floor (the school's paired pendant runs pour into a
  continuous band), seams are gone, and the falloff matches the
  colored layer's shape so the whole light field reads as one system.
  Same gloom extremes as before (ambient floor and full-bright centres
  unchanged), cached surfaces, one full-screen MULT.
- **2026-07 — Broken lights: 1-2 dead fixtures per room (maintainer).**
  A `broken=True` fixture kwarg kills the light in every layer at once
  (visible pool, `lit_at` gate, cast shadows, audit coverage -- the
  audit marks it a red X + "(broken)" tag), independent of genset
  power, and the pendant's art shows why: a shattered jagged stub where
  the glass was, the dish knocked askew off the cord line, the dead
  kink in the cord, no sway. Placements: the shop's main-row west +
  mid-row east (Hettie keeps the counter and aisle burning, the ones
  people see); the church's SW pew pendant; the barn run's MIDDLE bulb
  (a dead gap in the dead commune's row); the school's diagonal pair;
  the sheriff's front waiting room (the public face decays first, the
  door lantern still burns). The 90% coverage stays the WIRING's
  design number; live coverage sits at 81-88% with the burnouts, and
  that dark is sanctioned. Guarded by `tests/stealth.py` §17.
- **2026-07 — The row rule: pendants hang on one axis (maintainer:
  "people have lights in a row; lights shouldn't look chaotic").** The
  coverage-driven scatter was re-placed as straight runs at even
  spacing: the shop's three E-W runs (the counter bulb the middle of
  the main row) + one centered fixture per service room; the church's
  2x2 over the pew banks + the vestry single; the barn's run of three
  down the dormitory; the school's two runs of three over the cot
  banks (barracks wiring); the sheriff's north pendant line running
  three cords through two rooms + the south line of three. Coverage
  IMPROVED under the discipline (shop 95 / church 92 / barn 92 /
  school 97 / sheriff 90) -- rows tile a room better than scatter.
  Rule codified in DESIGN §6: props break the grid, wiring obeys it.
- **2026-07 — The drop bulb became a real pendant (maintainer: "those
  need to look like lights, not glowing orbs in space").** The bare
  bulb + halo read as a floating orb at game scale; the rework gives
  the fixture a BODY: a heavier drop cord stepping dark into the
  unrendered height, a steel dish shade (a cone of revolution -- the
  one place a lampshade read is correct), and the bulb glowing UNDER
  the lip so the dark rim always cuts the glow. Unpowered it keeps the
  dish in dead enamel with dark glass, so a blackout shows dead
  fixtures hanging rather than lights that vanished. Verified in-scene
  on N/E facings, powered and blacked out.
- **2026-07 — The 90% coverage rule + the five dim interiors relit.**
  Maintainer mandate: with every light on, >=90% of an indoor room's
  walkable floor sits inside a visible pool; the ~10% dark is chosen.
  `tools/light_audit.py` now MEASURES it (walkable-floor coverage %,
  pool + mechanical, printed on the sheet and stdout, cone-aware), and
  all five `DIM_INTERIOR_SCENES` were relit to the target (shop 92 /
  church 91 / barn 90 / schoolhouse 90 / sheriff's office 90) with
  ceiling `drop_bulb` cords as the workhorse (the maintainer's
  ceiling-source call: textured, never sourceless -- the light-security
  verbs need findable fixtures). The bulb's VISIBLE pool widened to 108
  (a bare bulb floods a room) while its mechanical `_LIGHT_KINDS`
  radius stayed 58, so stealth cover didn't move. Chosen darks: the
  shop pantry, the church's far nave corners, the barn's SE dormitory
  corner, the school's piled-desks corner, the cell's inner corner.
- **2026-07 — The genset power link, first slice (TODO #21
  light-security).** Electric light is LIVE state now: the ELECTRIC
  kinds (`Scene._ELECTRIC_KINDS`) emit only while their scene's power
  is on. `Game._tick_power` drains per-scene `_genset_down` blackout
  timers and stamps `Scene.power_on` + the per-deco `_powered` flag;
  a moth FLARE sets its room's timer (`BLACKOUT_DUR` 45s) -- the moth
  blackout ruling's core, wordless (the lights dying is the tell).
  During a blackout the electric fixtures die in every layer at once:
  no visible pool or fan, no mechanical `lit_at` cover, and the fixture
  art goes dark (wall lamp + drop bulb + yard light draw dead glass;
  the office radio's static crawl and creeping needle stop -- the
  first world-state-through-an-appliance tell). Fire is exempt, so a
  blackout hands the room to the warm accents (the stealth guard
  proves the counter stays lit by the kerosene FLAME while the hooded
  lamp's fan goes dark). Run-state, cleared on New Game; power returns
  on its own. Guarded end to end by `tests/stealth.py` §17. Still open
  in `TODO.md` #21: player restore/switch verbs, the fuel economy,
  decay, lit-rooms-secured.
- **2026-07 — Cone fixtures (light is not only a circle).** A fixture
  deco may carry `cone=(dir_x, dir_y, half_deg)`; the SAME kwarg drives
  all three layers (the maintainer's ask): `_draw_dark` carves + adds a
  world-space projected FAN instead of an ellipse (nested fills stepping
  down in brightness; apex at the fixture), `Scene.light_sources`/
  `lit_at` add the angular test (behind a hooded lamp is honest dark,
  and the stealth shadow-cover gate agrees), the cast-shadow pass skips
  casters outside the fan, and `tools/light_audit.py` outlines the fan.
  Pilot: the shop's east bulkhead lamp aims west into the room, so its
  own wall keeps the dark. Aim further lamps room by room per audit.
- **2026-07 — The shop light pass (the first audit-designed room) +
  `drop_bulb` + the kerosene pool.** First placement pass run through
  `tools/light_audit.py` end to end. New `drop_bulb` fixture (a bare
  bulb on a drop cord, cold family, cord fading up into the unrendered
  dark since interiors show no ceiling; per-placement hang height via
  the `z` kwarg): Hettie's tableau's "one kept bulb burning over the
  counter" made world-real over the till. `kerosene_lamp` joined both
  emitter tables (small warm accent pool; its draw burns a live flame
  everywhere, so a poolless one was a lie) -- the warm-in-cold overlap
  at the counter is the additive-interaction showcase. Placement notes
  that cost captures: the bulb 8px from the kerosene read as one blob
  (moved to the counter's front-centre air), and at z=30 it vanished
  into Hettie's body on the N facing (raised to z=42, above heads).
  Dark chosen on purpose: north aisle, stove corner, office nook,
  stockroom->pantry (candle, then pitch black for the cult tells).
- **2026-07 — Two-family light model + shared fixture table.** Brimley's
  civic light was originally anachronistic (19th-century lampposts);
  replaced with period-correct 1994 electric (cold `yard_light` poles on
  gas `generator`s, since the fold cut the grid). All fire stays warm by
  contrast. `_draw_dark` was generalized to iterate every light-emitting
  decoration through a shared `FIXTURE_POOLS` table instead of
  special-casing `wall_torch`, so any real fixture — including underground
  candles — now casts a visible pool. Pools carry real 3D source height +
  gooseneck offset, blend additively, and cast subtractive shadows.
- **2026-07 — Interior lighting pass, then "no light = danger" Watcher
  extension (`TODO.md` #21, done as "3 then 1").** Explorable non-refuge
  interiors (shop, church, barn, schoolhouse, sheriff's office) became
  `DARK_SCENES` at a lighter gloom, lit by a new period `wall_lamp`
  fixture with candles demoted to accent. Once that shipped, the Watcher
  gaze was extended into those same rooms: being in the dark (outside any
  light pool or the flashlight beam) counts as exposure, and a Watcher
  caught in light burns out. True refuges stayed excluded throughout. The
  moth-triggered blackout and a full "Watchers exist only in the dark"
  rework were sketched in the same design session but were **not built**
  — parked pending a fresh maintainer call (`TODO.md` #21).

## The fold & portals

- **2026-07 — the grove descent became a physical mine shaft (no
  rift-portal, no redundant gate).** The grove's DOWN used to be an
  evidence-gated rift pane over a dead fire: it clarified as evidence
  mounted and the two-press rite tore it open. But the descent was already
  gated UPSTREAM — you can only reach the grove by doing the school rite,
  which needs Sable's Invitation, which he hands over at 3 evidence — so the
  grove re-checking evidence and clarifying a rift was a dead gate (in play
  you never saw it at anything but fully-formed). The rework, per the
  maintainer: make the grove read as the **actual mine mouth** — a black
  void-floor SHAFT collared in timber, the haul rope hanging CUT (the rope
  is cut, canon), ore carts on a rail, spoil heaped, the Sign daubed at the
  lip — and drop the rift entirely. (That first VISUAL was itself redesigned
  across the follow-ups below — well, custom open-pit prop, rock adit — and
  LANDED as a green turf HILL with a stone ADIT cut into it and a unified
  grass-dome roof; the DESCENT mechanic described here is unchanged throughout.)
  `_grove_interact` is now an ungated
  two-press commit at the shaft lip; the second press plays the SAME
  door-dream, and the dream IS the descent — `_finish_rite` sets
  `rite_performed`, and the grove's `on_update` carries the PI straight down
  to `well_bottom` the moment the dream ends (no walk-through-a-pane step).
  The `O` descent fold/exit is gone from the grove; `fold_charge_fn` /
  `exit_gate_fn` now drive only the school pane (the "circle holds"). The
  Mask-keyed shaft-floor return (`well_bottom` up) and the seal/SPREAD logic
  are unchanged. The grove's dead fire + charred ground were cut (nothing
  chars a mine mouth); the effigy crescent + stones now kneel toward the
  shaft. `tests/flow.py` §1 (a)/(d)/(f) rewritten for the physical shaft;
  DIALOGUE.md's grove-rite section + `the_rite` note reconciled; NARRATIVE
  §7 step 5, DESIGN §5/§7, and CLAUDE.md updated (the grove left the
  standing-rift-pane family). Full gate green; VISION-verified (four facings,
  the shaft close-up, the dark graded view).
  - **Follow-up (maintainer feedback: "the hanging bodies, and I don't see
    the entrance"):** the old crop-circle dressing that survived the rework
    read as macabre standing/hanging figures and fought the mine-mouth
    identity, and the shaft was a thin flat black bar. Fix: cut the three
    `standing_stone` monoliths + the `polaroid_wall` nailed-faces (the
    "bodies"), and enlarge the shaft to a 2x2 black void pit with a timber
    headframe over its lip and the cut rope hanging in -- it reads as an
    actual entrance now, not a stain. The empty effigy CHAIRS (not figures)
    stay, kneeling toward the shaft; the haul gear moved clear of the bigger
    pit. VISION-reverified across four facings + the dark view; gate green.
  - **Follow-up 2 (maintainer: "it still doesn't look like a mine" / "on the
    top side"):** a flat black pit in grass never reads as a mine (the
    game's mine is enclosed rock + timber + rails). Rebuilt the mouth as a
    proper ADIT dug into the TOP (north) edge, using the game's real
    mine-adit vocabulary: a ROCK OUTCROP (wall tiles) with a dark tunnel
    MOUTH (`@` void) cut into it, a spanning `shoring_frame` timber SET over
    the mouth (uprights flanking, header passed under -- the Timber Racks'
    grammar), a working YARD dug down to bare dirt in front, ore carts on a
    rail running out, spoil heaped. The descent interact + loom moved to the
    mouth (14, 3); the dialog reconciled (you stand at the mouth of the mine,
    the floor drops into a shaft just inside). NARRATIVE §7 step 5 + the
    docstring updated (adit, not a pit). Reads as a mine from all four
    facings; smoke + full gate green.
  - **Follow-up 3 (maintainer: the adit "looks awful"; "DO NOT REUSE THE
    WELL"; "IT IS THE ENTRANCE TO A MINE. ITS A HOLE OR LIKE GOING INTO A
    CELLER"):** the adit's outdoor `W` rock face rendered as a grey building
    wall, and a borrowed `well`/`cistern_basin` read as the town well. The
    entrance is not a structure -- it is a HOLE you climb down into, like a
    cellar. Built a purpose-made procedural prop, **`descent_pit`**
    (`rendering/props.py _draw_descent_pit_solid` + a flat `_draw_descent_pit`
    fallback in `entities/deco_mine.py`): an open shaft you look down into
    under the tilt -- a dark mouth ringed by jagged thrown-up dug earth, the
    far interior wall a rim->black vertical gradient (the bottomless drop),
    the CUT haul rope hanging into it frayed (NARRATIVE §7, not a climbable
    ladder -- there is no ordinary way down). Its footprint tiles are made
    solid-but-invisible (`x`) so the player stops at the lip; E there is the
    descent. The grove keeps the ore carts (rails turned to E-W haul track so
    they stop reading as a second ladder), spoil, effigy rank. The old
    `W` rock face, the `@` pit, and the winch-well/cistern shaft are all gone.
    NARRATIVE §7 step 5 + DIALOGUE.md + the grove docstring reconciled to the
    open hole; VISION-reverified (magnified + four facings + dark); full gate
    green.
  - **Follow-up 4 (maintainer: "use stone and not dirt for the floor, well a
    transition of the two"):** the mouth is cut into ROCK, so the yard ground
    is now a radial STONE->dirt->grass transition (`_yard_floor`: bare stone
    `_` right at the shaft, a dug-dirt `d` haul apron, then grass, with a
    deterministic per-tile wobble breaking the edge). Also caught + cut a
    stray **`hanging_figure`** the stage-3 world-rot pass was scattering into
    the grove (`systems/rot_mixin.py _rot_decals`): a hanged body reads wrong
    at the cult's own mine mouth ("work without the worker" -- they claim
    people into the hive, they do not hang them) and re-triggered the "hanging
    bodies" note; the grove keeps the rest of the ambient rot (crows, claw
    marks, watching eyes/wounds) and the town/fields keep their hanging
    figures. Docstring reconciled; full gate green.
  - **Follow-up 5 (maintainer: "does that even look good at other angles" /
    "it's too square"):** the `descent_pit` was drawn for the south approach
    (a hard-coded north far-wall) and flattened into a dark rectangle from the
    other facings, and its square box read as man-made. Rewrote
    `_draw_descent_pit_solid` (`rendering/props.py`) to be (a) an IRREGULAR
    ROUND pit -- a 15-point jittered ring, not a rectangle, so it reads as
    something clawed out of the ground; and (b) YAW-AWARE -- each rim segment's
    receding interior wall is drawn only when its midpoint sits above the mouth
    centre on screen (the far arc under the tilt), with the near arc as the
    bright broken lip and the cut rope hung from the farthest point, all picked
    from the projected geometry. So the drop always faces the viewer and the
    hole holds its depth from all four facings (VISION-reverified per facing).
    Full gate green.
  - **Follow-up 6 (maintainer: "the hole is facing the camera and not static
    in the world"):** the yaw-aware pit had CAMERA-locked features -- the cut
    rope hung from the camera-far rim and every wall shaded the same rim->black
    -- so a near-symmetric round hole looked identical from every angle and
    read as billboarding. Re-anchored everything to the WORLD: (a) the outline
    gained world-fixed LOBES (a plain circle projects identically at every yaw;
    the lobes are what you see rotate as you orbit it); (b) a world-fixed light
    direction lights one side of the pit, so its bright side stays put in the
    world instead of following the camera; (c) the cut rope now hangs from a
    fixed world rim point (the north side). The hole now looks genuinely
    different from each facing -- a static object you move around, not a card
    turning to face you. Full gate green.
  - **Follow-up 7 (maintainer: "it still doesn't look good, it doesn't look
    like it fits in our world" -> chose "render the mouth in the game's rock
    vocabulary"):** the whole custom `descent_pit` line was a one-off drawn in
    a visual language nothing else in the game uses (smooth 3D gradient walls),
    so it read as a foreign smudge. CUT the pit prop entirely
    (`_draw_descent_pit_solid` + the flat `_draw_descent_pit` + the SOLID_PROPS
    entry) and rebuilt the mouth from the game's OWN hewn-rock renderer:
    `effigy_grove` joined `scenes/terrain.py _ROCK_STYLE`, so the mouth's `W`
    tiles now render with the exact hewn-rock draw the Works/Depths use (rough
    outline, dark muddy tint) instead of the default grey building wall. The
    mouth is a craggy rock OUTCROP (an irregular W-tile footprint with peaks)
    with a dark ADIT (`@`) cut into its south face, timbered over with a
    `shoring_frame` (a plain decoration so the mouth stays walkable to press E),
    a little bare bedrock at the threshold easing to the dug-dirt haul yard.
    Because it is real wall geometry it is static and correct from every facing
    (adit on approach, solid crag from behind) and it matches the mine it opens
    into by construction. Interact + loom + the two-press dialog moved to the
    adit mouth (dialog back to "a few feet in, the floor drops away into a
    shaft"); NARRATIVE §7 step 5 + DIALOGUE.md + the grove docstring reconciled.
    Full gate green.
  - **Follow-up 8 (maintainer: "put that in the middle and make it shaped like
    a hill green and stone cut into it"):** the grey rock outcrop became a green
    HILL with stone cut into it, centred in the clearing. Needed a per-face wall
    tint so one mound could be grass on top AND stone on the cut faces: added
    `_wall_top_tint_for` + a `top_tint` override in `_WALL_STYLES` (used by both
    the tilt `_extrude_prism` path and the flat `_wall_tile_flat` path), and a
    new **`turf`** material -- cold STONE `tint` on the side/foot faces, GREEN
    grass `top_tint` on the cap. Every existing style omits `top_tint`, so it
    falls back to the side tint and all shipped scenes stay byte-identical. The
    grove's `_ROCK_STYLE` entry switched rock->turf; the mouth is now a radial
    turf mound centred at tile (12,8) with a dark ADIT cut into its SOUTH face
    (the exposed stone cut reads where the grass gives way), the interact/loom/
    spawns/dressing all moved to the centred layout. Still real wall geometry,
    so static + correct from every facing; the mine's own material, so it fits
    the world. Grove docstring + NARRATIVE §7 step 5 + DIALOGUE.md reconciled.
    Full gate green.
  - **Follow-up 9 (maintainer: "make the 'roof' of this cave look like one
    object"):** the turf mound's top was a grid of per-tile caps (each W tile
    draws its own top quad + a dark seam outline). Added a `hill_cap` solid prop
    (`rendering/props.py _draw_hill_cap_solid` + a flat `_draw_hill_cap`
    fallback): ONE domed grass surface drawn over the mound top at the wall-top
    height, sized to the mound centre/radii and keyed after the walls with a
    `depth_bias`, so the hilltop reads as a single rounded object instead of
    tiled caps while the stone side/cut faces below stay the walls'. Placed once
    in the grove over the mound. **Detail pass (maintainer: "that roof lacks
    detail"):** concentric rim->crest rings + a centre bulge for the dome FORM,
    then world-fixed (seeded) DETAIL over it -- soft grass CLUMPS for tonal
    relief, STONES poking through the turf (the hill's own rock showing), dense
    varied grass TUFTS with the odd dry gold tip tying it to the field. All
    seeded so it never crawls and rotates WITH the hill. Full gate green.
- **2026-07 — Portal/fold system consolidated from the retired
  `PORTALS.md`.** Landed the "one phenomenon, two presentations" model
  (doors fade; everything else is the Fold, either shown as a standing
  rift frame or hidden as a silent torus-wrap/relocation lie), the 4D pane
  construction (reusing the King's existing 4D math for the border/peek/
  crossing only, no live 4D simulation), and see-through doors gated by
  the same sight cone the open world uses.
- **2026-07 — The walk-in discovery folds were cut.** Individually
  reachable secret-area folds (the effigy grove's old corn back door, the
  `husk_grove`/`scarecrow_ring` clearings) were removed once the story
  settled that the congregation walked to the grove openly before the
  closing rite claimed everyone at once — there was no honest way for a
  lone tile in the corn to still "discover" a hidden site the whole town
  once walked to in the open. `effigy_grove` survives as the rite-hidden
  clearing, reached only through the school rite's pane.

## The Works, the mine, and cast fiction

- **2026-07 -- #14 level-design half landed: side-dug chambers off the mine
  halls.** Timbered side-chambers were cut off four box/cruciform Works/Depths
  rooms -- the Timber Racks (`well_passage`), the Sorting Hall (`works_sorting`),
  the Kneeling Hall (`depths_hall`), and the Cistern (`works_cistern`) -- each a
  FINISHED store (crates, staged goods, a kept candle, a wall tally) and/or a
  HALF-DUG niche (a low spoil pile, pick gouges, no light), reached through a
  single timbered ADIT off the floor, cut into a sealed wall block clear of the
  patrol lane so the tuned crossings/props/hides stay untouched. The
  octagonal/cavern rooms (Shaft Floor, Scriptorium, Deepest Face, antechamber,
  threshing, Old Stores, stair) were assessed and left as-is (their `_bevel`/
  `_cavern` walls fight clean rectangular cut-ins, and each is already dressed
  as the dig); the cave-mouth adit doors were already done (`door_style="cave"`
  on every `UNDERGROUND_SCENES` room). A follow-up correction pass added the
  Cistern niche's missing spoil pile (the half-dug signature its two sibling
  niches carried) and closed a boxed dead-floor tile in the well_passage store.
  Reachability re-checked per room (smoke flood-fill); full gate green.

- **2026-07 — The killer-cult fiction scrub.** Early scene text implied
  the cult rendered/ate victims (a "Tallow Vats" room, bone-rack furniture,
  a bloodstain layer). All of it was purged once canon settled that the
  cult **claims souls**, not bodies — `works_cistern` (was "Tallow Vats")
  is where the dig broke into the underground river; `the_cells` are bunk
  cells, not captivity; `the_old_stores` replaced a bone vault. Guarded by
  a `tests/flow.py` token scan of the mine scene source so the fiction
  can't silently regress.
- **2026-07 — Time-loop language scrub.** Early lines implied the fold was
  temporal (days repeating). Corrected throughout: the fold is spatial
  only: roads loop, the calendar runs forward and stopped in January.
- **2026-07 — Named the principal locals.** Role-tags ("the Sheriff," "the
  Preacher") became names (Hollis Vane, Rev. Asa Crane, Hettie, Toby, Mr.
  Sable) once it was noted a small town's residents would know each other
  by name.
- **2026-07 — The unnamed "newcomer woman" NPC cut entirely.** An
  unexplained welcomer on the farmhouse path read as noise rather than
  dread; removed outright, along with the people-convert layer she rode
  (later fully superseded by the PI-rot rework above).
- **2026-07 — Carcosa palette re-graded off pale-teal/green onto the
  codified black + dim-gold family** (`TODO.md` #19), matching the SEAL
  ending's reference image. Landed pending a maintainer visual sign-off.
- **2026-07 — `symbol_portal_room` and `diner_gas_station` removed
  outright** once their only access points became dead ends by design (the
  farmhouse hatch nailed shut, the car moved to the lodge yard). Saves are
  in-memory only, so there was no persistence concern in cutting them.

## Brimley geography

- **2026-07 -- #4 outdoor-dread composition, first scene.** The outdoor zone
  is the game's weakest dread (long open sightlines read as a field). Per the
  ticket's "name ONE scene and ONE composition" rule, cornfield_path (the
  60-tile dead-straight E-W road that wraps on both axes) got a corn THROAT:
  standing corn juts from both shoulders at cols 22-24, pinching the road so
  the far half (and the maze/brimley branch at col 30) hides behind the stalks
  until you walk through the gap. Draw + placement only -- the walking lane
  (PATH_ROW) stays open, so collision/nav/reachability are unchanged (smoke
  flood-fill green); the corn is solid cover on the shoulders. Because the
  scene wraps on x, walking the loop returns you past the same throat (the
  "handed back / the town rearranges" uncanny) with no sim change.
  VISION-verified (the pinch reads, the lane stays clear, no error draws; a
  first `scarecrow` landmark attempt was pulled when it rendered as a magenta
  placeholder -- no such draw kind exists). The rest of #4 (more scenes, a fog
  volume, landmark repetition) stays open.

- **2026-07 -- the effigy grove redesigned as a river site.** `effigy_grove`
  (the descent mouth, north of Brimley above the river) rendered as a
  symmetric corn crop circle with no sense of the river the diggers followed
  down to this ground (NARRATIVE §2/§5). A first pass arced a reeded water band
  along the NORTH rim, but a top-edge band reads as a LAKE, so the scene was
  redesigned into a river site. The river now runs the FULL height down the
  EAST side (`river_col`, a bending course that enters the top and leaves the
  bottom; banks auto-reeded by the terrain's own `emit_tilt_water_reeds`, the
  Brimley-river vocabulary), and the clearing is an ASYMMETRIC lobed hollow
  (`_in_clearing`, an atan2-lobed edge rather than a clean ellipse) worked into
  the corn on the near bank, its mud bank (`_in_bank`) meeting the water. The
  dug mouth was moved to FACE the river: the dead fire/descent (the `O` fold +
  `_rite_pos`) sits east of centre, a shoring frame behind it, the spoil hauled
  east in a line to the bank, an ore cart left at the water's edge. The effigy
  ring became a CRESCENT kneeling toward the fire, and the three stones scatter
  through the hollow. The river is bounded top/bottom by the map edge and east
  by corn, and the corn still borders every dry side, so the circle holds (only
  the two folds exit). The fold/rite machinery moved with the fire (the `O`/`M`
  tiles, `_rite_pos`, the loom anchor, the `from_well_bottom` spawn) with the
  evidence-keyed charge/gate logic untouched -- full gate green (flow exercises
  the rite at the new spot), smoke flood-fill + no-diagonal-join green. TODO
  asked "decoration only," but a surface river needs real water tiles to
  auto-reed, so the change includes water/bank terrain kept in the impassable
  border zone (reachability safe). VISION-verified across four facings, close
  vantages, and the dark graded view.

- **2026-07 — Brimley rebuilt from 100x100 to 60x60 (`TODO.md` #18), a
  full reshape, not a scale-down.** The river moved to a central spine
  with a bridge crossing, all seven buildings redistributed around it,
  the well/noticeboard/wheelbarrow gathered into an eastern lodge square.
  Shape stayed a square with the torus wrap + fog rim underneath — nothing
  about the boundary changed, only the redistribution. A follow-up pass
  reoriented every building's door onto the wall facing its adjacent road
  (a natural mix of N/S/E/W instead of a uniform south-facing row).
- **2026-07 — A further river-centered rebuild was approved in concept but
  is not yet built** (`TODO.md` #4b) — the current layout still has 6 of 7
  buildings on one bank.
- **2026-07 — Terrain/reshape megabuilds parked.** A round/organic Brimley
  reshape and a general floor-roll heightfield were both explicitly
  decided against: at the ~55° tilt camera, a crest tall enough to occlude
  a standing figure over a short outdoor sightline is a near-cliff, not a
  gentle hill, so the geometry investment doesn't pay off at this camera
  angle — the tilt + sight-cone + fog rim already buy most of the
  illusion for free. The carved river channel (a controlled trough shape)
  shipped instead as the one heightfield use that dodges the cliff
  problem. See `TODO.md` #8 for what stays parked.

## Save model

- **2026-07 — The floppy save toast.** The evidence autosave wrote the
  disk with no feedback at all (the scribble toast says NOTED, not SAVED,
  and the quiet journal pickup showed nothing). A small procedurally-drawn
  3.5in floppy + "Saved" now fades in under the scribble leaf whenever
  `write_disk()` actually succeeds. Also fixed: `systems/save.py`'s
  docstring still narrated the retired sleep-at-the-cot save model.
- **2026-07 — Spent conversation questions + the menu guard.** E-spam
  through a talk's captions could pick a menu option the player never
  read (the caption→menu chain is synchronous), and re-askable questions
  looked identical to fresh ones. Every finished exchange now marks
  itself asked; spent rows dim in both menu presentations (authored order
  kept — indices are load-bearing for scripted drives); the cursor opens
  on the first fresh row; and tableau menus swallow confirm presses for
  `CONVO_MENU_GUARD` (0.3s) after opening.

- **2026-07 — Save model simplified to one disk slot, autosaved on
  evidence pickup.** Earlier iterations saved at the cot. The current
  model: the cot is a pure REST (heal + visibility cool, no save); the
  only save writer is evidence pickup (`Game._autosave`), snapshotting a
  cooled visibility so a reload never lands in a maxed-out death. A death
  or quit costs progress since the last clue, never the whole run.

## Interaction-logic bug sweep (from the retired `STORY_AUDIT.md`)

- **2026-07 — Every C-tier interaction-logic bug found in the story audit
  was resolved.** `C1` a fast Mara exchange could clobber the lure caption
  (fixed by holding the rite-holder closer while narration is active).
  `C2` a death/quit mid-staging could eat the next run's calling-out
  (`_reset_run_state` now clears `_mara_stage`). `C4` the cellar-key
  pickup gave off dialogue for a plain key (deleted outright, quiet
  walk-over pickup only). `C5` a church "LOGIN terminal" gave an
  always-"ACCESS DENIED" ARG-game tone in a 1994 parsonage (removed
  outright). `C7` "You dream of a doorway" could render outside rite mode,
  contradicting the dream-once canon (gated to rite mode only). `C10`
  Garrick's "days now" beat could fire before the preacher's body was
  found (gated to match Vane's condition). `C12` the hollow sheriff's
  intro sting re-fired on every load (now once per run). `C13` Sable's
  fold reproach could be a lie if the player hadn't actually walked a fold
  (now requires `crossed_a_fold`, not just having heard the note). `C14`
  several dead `[E]` cues with no handler were dropped or given a deadpan
  notice. `C15` the blast's lone-trigger point-of-no-return got an
  explanatory comment (it's deliberate — the fork is spent upstream).
  `C16` the go-back-to-Sable's-desk pointer could be missed by a player
  who never formally greeted him (requirement dropped). `C3` was found to
  be moot on re-verification (the audit's reasoning was wrong — the path
  it worried about is reachable). `C6`/`C8` were unreachable dead code,
  deleted in an earlier sweep; `C9`/`C11` were already resolved before
  this pass. Every fix landed with its own regression guard.
- **2026-07 — The code-health audit's findings were fixed on-branch**,
  down to one deliberate awareness-only item (function-size hotspots — see
  `TODO.md`'s "Standing fences," L5). Everything else that audit raised
  was actioned, not deferred.
- **2026-07 — A Fable prose/tense sweep landed** across every
  ended-arrivals line that had drifted into present tense describing a
  past event (Crane's greet + intro, Sable's "faces came," Vane's "kept to
  their own"), and the narrator-voice "vanished into the corn" line was
  cut everywhere except Crane's own testimony (kept deliberately there —
  it's his fallible impression, in his own mouth, not the narrator
  asserting it).

## Documentation process

- **2026-07 — CLAUDE.md threat section consolidated (the quality sprint's
  doc pass, phase 1).** CLAUDE.md had grown into a second design doc: the
  evidence ladder, the Moths, the Watchers, and the WADE had their ONLY
  full descriptions in the entry point, while the rest of its threat
  section duplicated DESIGN §1/§12 nearly verbatim. The four unique
  blocks moved whole into DESIGN §1 ("The evidence ladder, the Moths,
  the Watchers, the deep-water WADE"); CLAUDE.md's section shrank to a
  pure code map (~15.6k → ~2.7k chars off the every-turn read).
  Remainder (the tableau mega-paragraph and other Layout duplication)
  ticketed in TODO.

- **2026-07 — The six-doc canon consolidated from many per-topic docs.**
  `CAMERA.md`, `PORTALS.md`, `STEALTH_REWORK.md`, `AUDIO.md`, and two audit
  files (`STORY_AUDIT.md`, `CODE_HEALTH_AUDIT.md`) were folded into
  `DESIGN.md`/`NARRATIVE.md`/`TODO.md` and deleted, on the reasoning that
  scattered per-topic docs let canon drift out of sync with itself. Their
  substance is now indexed above under the section it landed in.
  `GAME_CHANGES.md` (a canon-alignment tracker) was folded into `TODO.md`
  the same way.
- **2026-07 — HARD RULE #0 introduced.** Full-doc reads before every
  response were made mandatory after canon broke "repeatedly" under
  lighter-touch approaches (partial reads, reliance on memory, grep-only
  lookups) — a real, recurring failure mode this rule was written to stop.
  A code-review pass the same era ("a new set of eyes") observed that the
  six docs' size had grown enough that the rule's *cost* was becoming
  disproportionate to trivial tasks, and that the docs mixed current-state
  facts with the entire history of how they got that way, meaning full
  reads paid for both every time. This changelog, plus the compaction pass
  that shrank `TODO.md`/`DESIGN.md`/`CLAUDE.md`/`NARRATIVE.md` to
  current-state-only content, is the resulting fix: same full-read
  guarantee over substantially less text. `README.md` was also brought
  under the "docs are part of the change" contract as a thin pointer file
  rather than a second copy of facts that can drift (it had: it described
  a save model two generations out of date, and a controls table missing
  the tilted-camera mouse-look entirely — see the review that prompted
  this pass). An automated `tools/check_canon_keys.py` CI check was added
  the same pass, to catch load-bearing key drift mechanically rather than
  relying solely on a full read catching it.
