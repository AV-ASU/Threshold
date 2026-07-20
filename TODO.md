# THRESHOLD — TODO

> A live to-do list of work that is **genuinely still open**. This is now the
> **single** canon-alignment + build tracker: the former `GAME_CHANGES.md` was
> folded in here (2026-07) and deleted, so its open items live below tagged
> `(was GAME_CHANGES §N)` for provenance. `NARRATIVE.md` stays the canon
> source of truth. Built from a verification sweep of every TODO source
> (`NARRATIVE.md` §8) and pruned
> against the 2026-07 build sweep. Each candidate was checked against the
> actual code; **anything already implemented is deleted from this list
> outright** (no "done" archive).
> Cross-check against `NARRATIVE.md` (the facts) and `DIALOGUE.md` (the
> exact spoken lines + narrator boxes) before writing prose; land any
> dialogue/narrator-text change in the code and `DIALOGUE.md` together (the
> `DIALOGUE.md` contract); run the full gate (`python tests/run_all.py`)
> before commit, and add a `tests/flow.py` guard when a new note locks a
> canon fact.

---

> **Model tags** (2026-07): each ticket is marked **[Opus]** (systems
> reasoning, geometry, rendering, correctness) or **[Fable]** (prose, voice,
> atmosphere). A few straddle and say so. Routing hint, not a rule.

## Open work

Grouped by readiness, not source-doc number. **Buildable now** items are
scoped and unblocked; **Blocked on a human** items are built but need
playtesting to finish; **Deferred** items are parked on purpose. Roughly
priority order within each group.

## Buildable now

### 1. **[Fable]** Investigation dialogue verb — the ask-questions layer  *(VERB LANDED 2026-07; principals + chorus all converted — still open: `_REVISIT_NUDGES` for Hettie/Toby/Crane as their case hooks land)*

You play a PI, but the only social verb is press-E-to-advance scripted lines:
every NPC conversation is a linear counter (`old_count`, `kid_count` ...). The
choice engine already exists and works (`ui/dialog.py show_choice`) but is used
in exactly ONE gameplay spot (the Sign Chamber altar fork, `scenes/well.py`
~L890). Build an ask-about-topics layer (the girl / the well / the strangers /
the preacher) with answers gated on evidence found + who is being asked. Makes
the core fantasy active for the first time (NARRATIVE §4: reading the town IS
the investigation). Content + design, not engine work. **Highest value-to-risk
item on the list: engine exists, canon is settled, payoff is the core fantasy.**

- **VERB BUILT + PILOTED on Mr. Sable (2026-07), organic redesign.** The menu
  options ARE the PI's own first-person spoken lines (not abstract "The X"
  topics you infer), and picking one plays a real EXCHANGE: the PI speaks, the
  NPC answers, each floating over their own head (`ui/float_speech`) while the
  world keeps running; an exchange can branch on an inline choice (show him the
  photo, or don't) with a side effect. Engine: `ui/conversation.Conversation`
  (`open_conversation`) is a small state machine wired entirely through the
  float `on_complete` chain + `dialog.show_choice` callbacks (Game never ticks
  it). A conversation is plain data: a one-time `greet`, then `exchanges` of
  `{key, q, avail, once, beats}`; a beat is `("npc"/"pi", text)` or
  `("ask", prompt, [(label, [beats], on_pick)])`. **The case GROWS the talk:**
  questions gated by `avail` open as evidence is found (Sable's register + her-
  state questions unlock on `the_ledger` / `maras_journal`), and the discovery
  itself NUDGES the PI back, appending his interior line onto the find's
  narration and filing a case NOTE (`_REVISIT_NUDGES` / `_collect_revisit`,
  hooked into `_evidence`; never inflates the evidence count). Wired on Sable
  after the envelope handoff preempt. Guarded by `tests/flow.py` §17c (17
  checks) + the naming guard.

- **EXPANDED to all four remaining principals (2026-07).** Toby / Hettie /
  Vane / Crane each carry their own `*_CONVO` + `open_conversation`, with
  every story-critical one-shot (Hettie's preacher reaction + Mara memory +
  paper trade, Vane's murder-he-can't-report) still VOLUNTEERING itself
  ahead of the menu. Toby is the exception since the 2026-07 rework: his
  witness account is EARNED on the photo exchange (a kid can't know the
  case on sight), and his playscript flinch + school warning were cut as
  structurally unreachable (he turns at 3 evidence; the envelope and the
  cult book only exist at 3). Flow
  polish shipped with it: the **talk-hold** (`scenes/base.py Scene.update` —
  the conversation partner stands and faces the player instead of walking
  their worker route mid-exchange; pursuit exempt), the **earshot guard**
  (`ui/conversation.py _partner_here` — the menu only reopens while both
  parties are still at the talk; walking off ends it quietly), and
  `game._convo` is cleared on scene load / run reset. `_fold_mentioned` grew
  `reflect=False` so a convo exchange (Vane's car answer) can file the fold
  note without hijacking the float's `on_complete` chain — the exchange
  carries the PI's reflection as its own closing beat. New `_REVISIT_NUDGES`:
  `the_preacher` points the PI back at Vane. Guarded by `tests/flow.py` §17d.
  **Still open:** `_REVISIT_NUDGES` entries for Hettie/Toby/Crane as their
  case hooks land.

- ~~**Two guaranteed options on EVERY townsperson (the case's front door).**~~
  **DONE (2026-07), chorus included:** every principal's menu leads with
  the shared pair (`_opener_exchanges`: (1) the PI **introducing himself as a
  private investigator**, (2) **showing Mara's photograph**), intro first,
  photo second, answers per-NPC; greets no longer assume the case is known —
  the PI **initiates** (news does not spread). **The Brimley chorus (Old
  Pell, Mrs. Calder, Royce, Garrick) converted** to `*_CONVO` +
  `chorus_dialogue` (scenes/dialogue.py): the shared pair with short
  per-NPC answers, one or two signature questions each (Pell's corn
  pride, Calder's plate, Royce's roads + his you-got-IN counter-ask,
  Garrick's road warning), the TODO #10 reactive beats still volunteering ahead of
  the menu, and the **fold note moved off the old any-talk trigger onto
  the exchanges that carry the account** (Royce/Garrick `on_ask`,
  `reflect=False`, earned by asking). Guarded by `tests/flow.py` §17e +
  the reworked §16c. **The unnamed "newcomer woman" NPC is CUT from the
  project entirely (maintainer call, 2026-07)** — an unexplained
  welcomer on the farmhouse path read as noise, not dread; she never spawns
  (flow-guarded), and the whole convert layer she rode was later cut
  (TODO #22c).

- **The choice box is SMALL — menu labels are authored short (2026-07).**
  An exchange carries an optional `label` (≤ ~44 chars, flow-guarded): the
  menu shows the label, picking it still floats the full `q` as the PI's
  spoken line. The option panel also sizes to its longest label and sits
  ABOVE the dialog band (`ui/dialog.py _draw_choices`) so it never lies over
  the prompt. And follow-up questions are **EARNED, not ambient**: Hettie's
  "who is they" and Crane's flock question wait on the intro being asked
  (`convo_<id>_intro_asked`); the way-out questions (Hettie, Toby) wait on a
  local having told the PI about the looping roads (`voice_fold_heard`).

- ~~**Pilot beat — the Crane choice**~~ **DONE (2026-07), upgraded to an
  inline `ask` fork in CRANE_CONVO's flock exchange:** press him (he takes
  the naming where they can hear it — `preacher_doomed` latches, his death
  proceeds, and the PI's culpability lands as a NOTE `crane_provoked`) vs
  hold him back (the fire is only banked — the question stays open to press
  later; he is never savable-by-conversion, §1b — the player just decides
  whether HE is the one who points him). The provoke branch feeds the murder
  reveal below. NOTE the behavior change: his doom is no longer an automatic
  visit-2 counter. (**The old `_the_third_thread` stall-breaker was CUT
  with the TODO #22 rework.**) The surface set is now three fixed,
  always-reachable pickups — the receipt (Hettie's shop), the detention
  record (Vane's office), and the journal (the barn), findable in any order —
  so the case can no longer stall waiting on a provoke, and Crane's press/hold
  choice is a pure character beat rather than a gate. The removal is
  flow-guarded. The silently-filed journal beat (`show=False`) still lands
  its revisit nudges.

### 2. **[Fable + Opus]** The newspaper choice — pilot for the favor economy  *(planned with the user 2026-07; the CHOICE LANDED 2026-07 — the broader favor economy stays direction-stage)*

The PI starts with the **April 14, 1994 paper**. It is now a
**choose-the-recipient gift**: a town cut off since January, starved for
word of the outside, one copy — and who you give it to yields **different,
incommensurable** payoffs, and the town **feels** the allocation. This is
the concrete **pilot for the favor economy** (the action-choice half of the
choices pillar, twin to #1's dialogue verb; the full economy table is still
to be drafted).

- ~~**Recipients + payoffs.**~~ **ALL SIX DOORS LANDED (2026-07).** The
  one-copy economy is the inventory itself (`_paper_given` in
  `scenes/dialogue.py`: every `paper` exchange gates on still carrying
  the copy, so the first give closes the rest; the recipient lands in
  save arg `paper_given`, and every allocation files a case NOTE, never
  evidence). The doors: **Hettie** → her offer is a real CHOICE now (the
  volunteered notice ends on trade-or-keep; declining reopens as her
  "About that trade." menu question) paying one load of cartridges;
  **Royce** → his hoarded flashlight batteries (new item `batteries`,
  icon + Tools tab) plus his best road (river road south, two bends past
  the bridge — testimony, filed as a note; seeds #12); **Old Pell** →
  no item, mercy: he pencils today back into his calendar, and his
  stopped-calendar stoop beat SWAPS to the marked one
  (`beat_pell_marked`, `scenes/brimley.py` — he would contradict
  himself otherwise); **Toby** → the funny pages ("Calvin's still in
  it. He didn't stop."; the front page stays out of his house);
  **Sable** → the NULL and the tell (he squares it on the desk,
  unopened; no reward, the chill files as the note); **Vane** → the
  trap (shipped earlier; now records + notes through the same helper).
  Guarded by flow §17g (the one-copy closure, the null, Pell's stoop
  swap, Hettie's offer-not-auto-trade) + the adapted §17c menu count
  and §23(a) trade drive; text in `DIALOGUE.md` Part A + Part B.
- ~~**Vane is a recipient too — and his is a TRAP, not a gift.**~~ **DONE
  (2026-07, shipped with the Vane arc):** the `paper` exchange in
  `VANE_CONVO` (Kurt Cobain dead on the front page reads, to a man who
  wants it all to *end*, as *permission*, not hope) adds
  `VANE_PAPER_DESPAIR` (+2) on the hidden despair ledger — the one
  recipient whose allocation carries a TRACKED consequence, the deliberate
  exception to the "mood, not a meter" fence below. The give-beat
  telegraphs it as mood (the PI's own closing line), no number shown; one
  copy, so giving it to Vane means Hettie (and the recipients above, when
  they land) go without. Guarded by `tests/flow.py` §17f.
- **What's on the page (real April '94):** Kurt Cobain's death is the thematic
  centerpiece (the outside world's own despair, the same wound that took
  Brimley), plus Rwanda and the Bosnia/Goražde NATO strikes. The paper is **not
  a comfort**.
- **Requests variant (same engine):** a local asks for a thing → **fulfill /
  refuse / SUBVERT** (use it another way) → the town feels it.
- **Fences (the choices rules):** rewards are **incommensurable** (no dominant
  pick); **never evidence**; the ripple is **mood, not a meter** (who greets you
  warm vs curt, whose hope you fed or killed); it **never gates an ending**
  (nothing stops the PI but himself); **existing verbs only** (give via E /
  dialog).

### 2b. **[Opus + Fable]** Close-up examine tableaux  *(play-notes feature; COMPLETE 2026-07 -- all six seats + the Talk + the pedestal)*

The diegetic "look at the thing" modal: press `[E]` on a tagged prop and the
world pauses on an animated procedural close-up with a **menu** that mutates it
live (take the gun off the desk, read the case file) and can open readable text
(walking away interrupts). Art in `ui/tableau.py`, state machine in
`systems/tableau_mixin.py` (a `Game` mixin), wired like the flashback cutscene
(`_tableau is not None` freezes the world; `_draw_tableau` paints over
everything; `_tableau_input` owns input). **PILOT LANDED:** the bedroom writing
desk (pistol + case file) replaced the old linear "E takes gun, next E reads
notes." Guarded by `tests/flow.py` §14; player-facing text in `DIALOGUE.md`
Part B.

- **FACE-ACROSS-A-TABLE landed on Mr. Sable (2026-07).** The first principal
  DIALOGUE presented as a tableau: `clerk_dialogue` opens `SABLE_CONVO` inside a
  frozen reception-desk close-up (`_open_sable_tableau`; the conversation runs
  in `ui/conversation` `tableau=True` mode, so its spoken beats render as the
  tableau caption and its question menu as the option panel, `_tableau_caption`
  / `_tableau_choices`) instead of floating over the desk. The close-up is
  reactive: the photograph appears on the register once shown
  (`sable_showed_photo`) and the sealed Invitation once handed over
  (`rite_envelope_given`). Bespoke Sable art (`draw_sable_tableau`, his
  clerk-sprite face given a gloomy pass, dark coat + red tie, key wall, stopped
  clock, register, ceiling-fan shadow). Guarded by `tests/flow.py` §17c (12);
  text in `DIALOGUE.md` Part A (the words) + Part B (the presentation).

- **VANE'S OFFICE landed (2026-07, the second face-across-a-table).**
  `sheriff_dialogue` opens `VANE_CONVO` in the office close-up
  (`_open_vane_tableau`; art `draw_vane_tableau`, derived from his sheriff
  sprite): cold window daylight (Sable's lodge is the warm one), the stopped
  JAN 15 calendar, the cell-bars sliver, the gun cabinet in the back.
  Reactive on TWO axes: his **pose reads the hidden despair ledger** exactly
  as the mood framing line does (`_vane_tableau_state` mirrors
  `_vane_prompt`'s thresholds: neutral squares up, despair turns his head to
  the window, hope leans him in with a forearm on the desk; mood, never a
  number), and the desk carries what the talk earned (the given newspaper
  spread flat, the opened cabinet). The generic conversation-tableau input
  moved to `_convo_tableau_input` (shared by Sable + Vane). Guarded by
  `tests/flow.py` (the Vane-tableau block after the cache guards); text in
  `DIALOGUE.md` Part A + Part B.

- **HETTIE'S COUNTER landed (2026-07, the third seat).** `hettie_dialogue`
  opens `HETTIE_CONVO` in the shop-counter close-up (`_open_hettie_tableau`;
  art `draw_hettie_tableau`, derived from her sprite): the gutted shelves
  with dust-ghosts and the one tin left, the empty till, and her ONE kept
  bulb burning over the counter (the stoop line made light). Her sprite's
  uncanny tell survives the close-up: black-filled spectacle lenses, the
  glint on the same wrong side of both, her "blink" the glints going out.
  Reactive: her idle glances at the door every few seconds (the framing
  line made pose; time-driven in `_draw_hettie_tableau`), Mara's tab leaves
  the spike once the receipt is taken, and the traded newspaper lies open
  after the barter (`_hettie_tableau_state`). Guarded by `tests/flow.py`
  (the Hettie-tableau block after her gate guards); text in `DIALOGUE.md`
  Part A + Part B.

- **CRANE'S LECTERN landed (2026-07, the fourth seat).** `preacher_dialogue`
  opens `CRANE_CONVO` in the chancel close-up (`_open_crane_tableau`; art
  `draw_crane_tableau`, derived from his preacher sprite: black cassock,
  white clerical collar, the small pale cross, gaunt and half a ghost).
  Candled dusk: the plain wall cross, the arched window going out, the
  bell rope dead at the edge, his kept candle stand the only light (the
  hymn board was cut on the maintainer's look). Reactive: his HANDS read the press fork
  exactly as the framing line does (`_crane_tableau_state` mirrors the new
  callable `_crane_prompt`): folded over the lectern while he waits;
  gripping its corners, head forward, once `preacher_doomed` latches (the
  new framing variant "done waiting" landed in DIALOGUE.md with it).
  Guarded by `tests/flow.py` (the Crane-tableau block after the fork
  guards); text in `DIALOGUE.md` Part A + Part B.

- **TOBY'S LITTLE TABLE landed (2026-07, the fifth and last principal
  seat).** `toby_dialogue` opens `TOBY_CONVO` in the close-up
  (`_open_toby_tableau`; art `draw_toby_tableau`, derived from his kid
  sprite: the yellow tunic, the low brown mop, the cheek marks that read as
  old tear-streaks on the second look; child proportions, so the same frame
  holds a smaller person). The one almost-normal room in Brimley: plain
  daylight, crayon drawings taped crooked, the closet door's drawing (C14),
  the toy radio, crayons and his fidgeting hands on the table. Reactive:
  his idle watches the corn line out the window (the framing line made
  pose), the dark procession drawing hangs among the cheerful ones once
  toby_told, and the worried brow slant levels once the PI's promise lands
  (`_toby_tableau_state`). The §26 float guards moved their vehicle to
  Royce (all five principals host tableaux now; the chorus still floats).
  Guarded by `tests/flow.py` (the Toby-tableau block after Crane's); text
  in `DIALOGUE.md` Part A + Part B.

- **THE TALK landed as the grip close-up (2026-07, the tone inversion).**
  `_cult_talk` opens `_open_talk_tableau` (art `draw_talk_tableau`) instead
  of the modal box: no room, no table, no face. The carved mask of his
  sprite fills the frame (hewn irregular oval, the door-dream grammar:
  recessed void sockets with a gold ember far down, the Sign scratched on
  the brow, the graft seam, no mouth), the fur hood, the stitched hide
  coat, and his hand on YOUR shoulder at the frame's corner. He leans in,
  very slowly, the whole time. NOT a Conversation: a scripted caption
  chain (the locked warning lines unchanged) with ONE choice when the PI
  carries the revolver: hold still, or reach for it and find his other
  hand already resting on the wrist ("None of that, now. We're only
  talking."). Escape pages, never aborts (the release, stand-down, grace,
  and note run on every path). Guarded by the reworked flow §28 block +
  the new reach guards; text in `DIALOGUE.md` Part A + Part B.

- **THE PEDESTAL landed (2026-07).** The Sign Chamber altar interact
  (`scenes/well.py`) opens the altar close-up (`_open_altar_tableau`; art
  `draw_altar_tableau`) instead of a modal choice: an OBJECT close-up (the
  desk-tableau family, not a person), but the object is His face. The Pallid
  Mask on the hewn stone (pale drowned-face, black eyeholes, a warm gold
  ember far down in each because it knows your hands), the daubed Yellow Sign
  (the canonical crude-mask brand, matching `_draw_yellow_sign`) breathing on
  the apse wall, the kneeling congregation behind in the cult-dark, two
  candles the only light. The two instincts ride on as the menu, and **BREAK
  is preserved through the close-up**: "Tear it down. End this." →
  `_play_ending("rite_broken")` (the trap, the axe mask-yank + Carcosa
  blast); "Lift the mask." → `_take_mask` (the keystone + the `descent_mask`
  temptation); Escape backs out (the mask stays, re-interactable). Prompt
  trimmed to "The whole machine of it, here in reach." (the close-up shows
  the rest now). Guarded by `tests/flow.py` §3 (+ the §31 tempt guard
  re-pointed at the tableau); text in `DIALOGUE.md` Part B.

- **MARA'S CONFRONTATION landed (2026-07, the last #2b beat -- the REVEAL).**
  `_mara_voice` opens `MARA_CONVO` in the Sign Chamber close-up
  (`_open_mara_tableau`; art `draw_mara_tableau`): she stands out of the
  rank ONE OF THEM (the congregation's carved mask + hood, the Talk's
  grammar but slighter and NEW wood, no graft: the last one in), the rite
  still running at her back (the Sign's daub-strokes, the altar candles,
  the kneeling rank, the rite-holder), and the caption LISTS her as "One
  of them" (`MARA_CONVO["name"]` is a callable listing) until the greet's
  reveal beat (`("do", ...)` -> `_mara_unmask`) pulls the mask down off
  her face and the listing turns to her name: the face from the
  photograph, gone thin. Engine growth shipped with it: conversation
  beats support `("do", fn)` silent side effects and `name` may be a
  callable(game); a scene load now drops a stale tableau alongside the
  convo. Reactive: her idle glances back toward the rite; `mara_lucid`
  raises her bleeding palms; `mara_named` seizes the PI's coat and stirs
  the rank. Escape pages her captions (the reveal cannot be skipped);
  her menu takes it as "Say nothing." Guarded by the reworked flow §24b +
  §28b (the listing flip, the unmask, Escape-pages, the staging end to
  end); text in `DIALOGUE.md` Part A + Part B.

  **#2b is COMPLETE: all six principal seats (Sable / Vane / Hettie /
  Crane / Toby / Mara), the Talk's grip, and the pedestal ship as
  tableaux.**

- **The #2b SOUND PASS landed (2026-07, maintainer call).** The
  world-freeze had left every close-up in dead air (the scene's scheduled
  ambients freeze with the sim): every tableau now opens on `lean_in`
  (the world holding its breath; the old `blip_low` open was a character
  voice blip spent on a cinematic beat) and carries a per-seat ROOM TONE
  looped on the ambient channel while it is up (`Audio.room_tone`,
  `_TABLEAU_TONES`): Sable's fan, Vane's window wind, Hettie's bulb,
  Crane's nave, Toby's corn line, the Talk's breathing behind the wood,
  the pedestal's tritone pressure. Mara's seat stays SILENT by design
  (the authored force_silence; silence is a move). Menu motion borrows
  the dialog band's `cursor`/`confirm`; the unmask gains a quiet
  `low_pulse` under its `wood_creak`. All levels sit under the caption
  blips; loops are seam-crossfaded. Full spec in `DESIGN.md` §11;
  flow-guarded (`_room_tone` set/cleared, the Mara silence). **Needs a
  LISTEN from the maintainer** (levels tuned by waveform, not by ear).

### 2c. **[Opus + Fable]** Tableau ↔ scene environment parity  *(maintainer call 2026-07: "make sure the environment matches details in the tableaus"; COMPLETE)*

Each close-up examine tableau (`ui/tableau.py`, described in `DIALOGUE.md` Part
B) shows specific props the WALKABLE scene should also carry, so the room the
player stands in reads as the room the close-up promised. A parity audit found
the gaps; this pass dresses each walkable scene to match, one at a time, VISION-
verified (four facings + dark), full gate + docs same commit. New man-made props
are `SOLID_PROPS`/`FURNITURE` volumes or `_WALL_DECO` mounts (never standees,
error class #7). The bedroom desk already has full parity (its `writing_desk`
top draws the pistol + case file); it is the model.

- **Hettie's shop — LANDED (2026-07).** New tabletop volumes `cash_register`
  (the empty brass till, amount flag reading nothing) + `bill_spike` (Mara's tab
  curled on the spike by the till), seated on the counter. Matches
  `draw_hettie_tableau`. Bare shelves / one kept bulb / shop door were already
  present.
- **Crane's church — LANDED (2026-07).** New `lectern` SOLID_PROP (the open book
  on a slanted board, brass cross on the column) at the head of the nave, in
  front of the preacher's spot -- the centrepiece of `draw_crane_tableau`; the
  church had only a bare altar table. Added a tall chancel WINDOW (terrain `'i'`
  on the north wall) and the dead BELL ROPE (`rope`) hanging at the west edge.
  Cross + candles + pews were already present.
- **Vane's office — LANDED (2026-07).** Added the cold north WINDOW behind the
  desk (terrain `'i'`), a HOLDING CELL in the SE corner (a `bars` inner-door
  gate + two wall tiles, the empty sliver of cell where Mara was booked), and a
  new `gun_cabinet` FURNITURE volume in the back records room (the glass-front
  arms locker with racked guns + a padlock hasp, the cache he unlocks). Matches
  `draw_vane_tableau`; the JAN 15 calendar + desk were already present.
- **Sable's lodge — LANDED (2026-07).** New `key_rack` `_WALL_DECO` (a
  pigeonhole board of hanging room keys, a couple of hooks empty) behind the
  reception desk -- Sable's "full house" want made an object, the detail
  `draw_sable_tableau` builds the desk around -- and a new `service_bell`
  tabletop volume (brass dome + press button) on the register. The register +
  clock were already present. The CEILING FAN is deferred: no overhead-prop
  path in the tilt renderer (a moving shadow cast on the desk would be the
  faithful option; not built).
- **Toby's house — LANDED (2026-07).** New `crayon_drawing` `_WALL_DECO` (a
  taped child's sheet, `motif` = house / sun / family / corn / the dark
  procession) taped crooked across the north wall -- the one almost-normal room
  in Brimley, and that read is the point (draw_toby_tableau). New `crayons`
  tabletop volume (crayons + a half-drawn sheet) on his table beside the toy
  radio, and a WINDOW (terrain `'i'`) he watches the corn line through. The dark
  PROCESSION drawing joins the cheerful ones once `toby_told` (an on_enter that
  re-adds it each load). The toy radio + closet (with the King drawing) were
  already present.
- **works_sign (Mara / the pedestal) — LANDED (2026-07).** New `altar_mask`
  SOLID_PROP -- the Pallid Mask resting on the altar cap, face-out, pale with a
  warm gold ember in each black socket -- the focal object of both
  `draw_altar_tableau` and `draw_mara_tableau`; the walkable altar was a bare
  stone block. Gated off once taken (`_sign_on_enter` drops the deco). Added a
  wall-mounted `wall_sign` (the crude-mask glyph as a `_WALL_DECO`) daubed on
  the apse wall above the altar so the big Sign hangs on the vertical wall as
  the tableau shows (the flanking `yellow_sign` floor daubs stay). The
  rite-holder was moved off the dead-centre front and made a low `kneel` (it
  was a standing `chant` that both occluded the Mask and contradicted the
  "bowed at the altar's foot" fiction).

**#2c is COMPLETE: all six tableau-bearing walkable scenes (Hettie's shop,
Crane's church, Vane's office, Sable's lodge, Toby's house, the Sign Chamber)
now carry their close-up's specific details; the bedroom desk already had full
parity. New procedural kinds: `cash_register`, `bill_spike`, `service_bell`,
`crayons`, `altar_mask`, `lectern`, `gun_cabinet` (FURNITURE), `key_rack` +
`crayon_drawing` + `wall_sign` (`_WALL_DECO`). Deferred: Sable's ceiling fan
(no overhead tilt path).**

### 3. **[Opus]** Ground heightfield — blind-spot hills  *(DESIGN.md §10; PROTOTYPE landed 2026-07 — floor-roll rewrite + live authoring deferred)*

**PROTOTYPE DONE (behind a preview, dormant).** Built: `Scene.set_ground` /
`Scene.ground_z` (bilinear, 0.0 unopted → dead-flat + pitch-0 byte-identical),
the `_flood`-style `rendering/heightfield.build_heightfield`, the CREST
sight-occlusion (an optional `ground=` term in `sight.los_clear` /
`visible_factor` + `Scene.clear_sight_line`, `SIGHT_EYE_H`) feeding BOTH the
draw gate and the cult AI, `draw_ground_mesh` (a projected floor mesh over the
flat raster, tilt-only) + actor lift by `ground_z`. Movement stays 2D; height is
a passive READ (AI ignores it in v1). Preview `tools/preview_heightfield.py`;
guard `tests/render_smoke.py` [4/4]. **Key finding:** the tilt floor is ONE
affine warp (`_tilt_warp`), not per-tile — so no shipping scene opts in yet, and
two pieces are **deferred**: (a) rolling the whole floor RASTER (needs a
mesh/displaced warp replacing the global affine `_tilt_warp` + a perf pass on
the ~6000-tile bake), and (b) authoring a live Brimley hill + lifting every live
actor project site (safe/dormant until then). *(Original brief kept below.)*

The camera already carries a real height axis (`Camera.project(wx, wy, wz)`,
`z` rises by `sin(pitch)`); the *simulation* is flat XY. Add a per-scene
`ground_z(tx, ty)` sample, authored like the `_flood` water helper. It feeds
ONLY two places: the `wz` passed when projecting the floor + any standee/actor
on it (so ground rolls), and `blocks_sight` (a crest higher than the player's
eye occludes what's beyond it). Movement stays 2D; `player.z` is a passive READ
of the terrain under the feet, used for draw + sight only — no jump, no gravity,
no new collision. Lands directly on the shipped blind-spot vision (`sight.py`):
a hill you can't see over is the same dread primitive as a wall. **Constraints:**
strict no-op at pitch 0 (byte-identity gate, `tools/capture_world.py`), and
AI/pathing ignores height in v1 (cosmetic + sight-only). Prototype on one
Brimley scene behind a preview before wiring.

- **River spike DONE (2026-07):** `heightfield.carve_channel` cuts a sunken
  trough (banks from `build_heightfield`, bed below grade); `draw_ground_mesh`
  shades `~`/`@` bed tiles WET and the bank crest occludes the bed from the
  grade (the sight-pit the WADE routing wants). Preview
  `tools/preview_river_channel.py`; guard `tests/render_smoke.py` [4/4].

- **DECISION (2026-07): the carved channel is the shippable win; the general
  floor-roll + subsidence bowl are PARKED (see Deferred).** A design pass
  concluded the heightfield's payoff (outdoor sight-occlusion) fights its
  geometry at ~55° tilt: a crest tall enough to hide a standing figure over a
  SHORT outdoor sightline is a near-cliff, not a gentle hill, so "natural
  sloped boundary" and "occludes like a wall" are different terrain and a
  general rolling floor mostly reads wrong at this camera. And the tilt camera
  + blind-spot sight-gating already hide the ground geometry, so the illusion
  the roll was buying is largely already bought. The prototype stays DORMANT
  (paid for, byte-identical at pitch 0 — leave it), the carved channel ships (a
  trough is a controlled shape that dodges the cliff problem), and outdoor
  dread now routes through COMPOSITION (#4), not new terrain tech.

- **Deferred siblings (do NOT pull forward without a set-piece that demands
  them):** *3b.* Multi-floor buildings as same-building `cross_fold`s to a
  `lodge_upstairs`-style scene (no fade, stride preserved; the reveal is already
  free from `occlusion.py` + blind-spot gating) — compose shipped tools, do not
  build a continuous floor system. *3c.* Fully continuous traversable z (real
  ramps, actors at arbitrary heights, whole interior visible at once) —
  **deferred indefinitely**: big collision/AI/depth-sort/save lift, strains the
  "no roof over the play area" rule, and the payoff partly fights a game whose
  power is restricted sight.

### 4. **[Fable]** Outdoor dread — the composition pass  *(the outdoor-dread lever; replaces the parked Brimley reshape + terrain megabuilds)*

Open ground is the game's weakest dread zone (long sightlines, reads as an open
field). The 2026-07 design call PARKED the two big-tech answers to this (the
Brimley reshape and the ground floor-roll — see Deferred) because the tilt
camera + blind-spot sight-gating already carry the geometry illusion, and the
honest lever is COMPOSITION with tools already shipped, not new terrain tech.
Attack it on ONE named outdoor scene at a time (this is §10's liminal-
composition pass made concrete):
- **Corn + treeline are the outdoor walls.** Denser stands, winding corn lanes
  that break the long shot, a treeline that closes the rim. Draw + placement
  only; the standee billboards + the `_corn_runs` LOD already exist.
- **Fog / mist volume** between the player and the distance shortens the
  effective sightline directly (the job the subsidence bowl wanted, minus the
  geometry). Rides the skybox/void rim that is already ~80% there.
- **Landmark repetition + same-scene silent folds** (`cross_fold`, DESIGN.md §7,
  draw-only) give the "handed back / the town rearranges" uncanny with no sim
  change (`sight.py` blind-spot draw-gating already runs the sim while drawing
  only the cone).

**To turn into work:** name ONE scene (the Brimley approach road, or the
effigy grove) and the ONE composition it gets (this sightline broken by
this corn lane, this landmark passed twice in fog). Do NOT start against the
abstract goal. Keep the sim Euclidean-honest so stealth distance-falloff + NPC
nav stay true under any presentation lie. **Preserve (load-bearing) if the
scene is Brimley:** it stays ONE square scene (§11 merged village+mistlands on
purpose; do not split, do not reshape); the fold road + Royce/Garrick looping-
roads lines; the well as dread set-dressing (NOT the way down: the descent is
the cult's dug mine at the grove, reached by the rite); all exits/locals/cult stations;
in player-facing text call it a bounded fog-edge / void-ringed town, never
"island."

### 4b. **[Opus]** Brimley river-centered rebuild, both banks  *(concept APPROVED 2026-07 from a top-down layout test; a scoped build, not yet done)*

A top-down look at the current 60x60 Brimley (a markup test in the session
scratchpad) confirmed the walk-sim is REAL: 6 of the 7 buildings sit on the
WEST bank, the whole east half is empty (one lone building + a stranded well),
and the central river is a spine the town does not use. The approved fix is a
**building REDISTRIBUTION** (not a shape/boundary change, so it does NOT
contradict #4's "stays one square"): cluster the 7 buildings tight on BOTH
banks around the central river + bridge so the dead crossings go and the
fog/forest periphery reads as dread, not filler.

- **Flow, from the real topology (do not re-break it):** the player wakes at
  the Arcadia (OFF-MAP, reached via the EAST lodge road, rows 24-26) and enters
  Brimley from the EAST. So the near (east) bank is the first-contact town
  (Shop/Hettie, barn, Toby's house), and the SHERIFF sits on the FAR (west)
  bank, so "Vane is not the first NPC" and "cross the river to reach the law"
  both fall out of geography with no gate. The well stays in the eastern lodge
  square by the entry; the cult camp stays SE; the surface altar (the standing
  stones, #17) reads on the riverbank over the Threshold point.
- **Acceptance test (the maintainer's constraint): everything fits IN SCALE on
  the 60x60 map** at REAL building footprints (not markup boxes), with the cover
  lanes (sightline -> cover -> sightline per bank), NPC/King nav across the
  torus wrap, the fold-road E-W loop, the homebody door anchors, and every
  exit/spawn reconciled, and reachability re-checked with smoke's flood-fill.
- **Reconciles #4/#8:** Brimley STILL stays one square with the torus wrap +
  fog rim (do not split, do not move the boundary); this is a redistribution
  like the #18 pass, NOT the parked round-shape reshape (#8). Verify each
  rebuilt building with VISION four-facing captures.
- Its own build, scoped to run AFTER the conversation/tableau work so two big
  changes are never in the air at once.

### 4c. **[Opus]** Interior doors + the multi-subroom redesign  *(maintainer complaint 2026-07: "all rooms are either a box or that room with the side room"; MECHANIC + SHOP PILOT landed, rollout open)*

The maintainer's grievance: every interior is one open box or a box with a
single side room. The fix has two halves, and the first is done.

- **The MECHANIC landed (2026-07).** A new **interior door** kind (DESIGN.md
  §7 / CLAUDE.md): a swinging leaf on a floor GAP in a wall line WITHIN one
  scene, the tool that splits a building into subrooms. `Scene._inner_doors` +
  `add_inner_door(tx, ty, kind, open=False)`; a shut leaf is solid + blocks
  the sight cone (so it hides the room beyond AND breaks a pursuer's line of
  sight, buying time), open passes both, NPCs route AT it and open their own
  way (`Scene.update`), the player toggles the nearest with E. Kinds: plank /
  bars / half (see-through) / curtain. Draw `rendering.props.draw_inner_door`.
  Guard `tests/stealth.py` §15. Reachability is safe: an inner door sits on a
  `.` gap tile, so smoke's flood-fill routes through it.
- **The SHOP PILOT landed (2026-07).** `build_shop` (`scenes/interiors.py`) is
  rebuilt as a NESTED warren, not a divided box: an L-shaped public shop floor,
  a plank door to a dry-goods STOCKROOM, a second plank door off the BACK of
  the stockroom to a cold PANTRY (two doors deep, a true blind spot for the
  cult tells), and a curtain nook for Hettie's office. Hettie's worker route
  walks her through the stockroom door (the auto-open showcase). Verified live
  (VISION four-facing + the blind-spot chain); full gate green.
- **STILL OPEN: roll the pattern out** to the other box-or-side-room interiors,
  one at a time, each verified live per VISION: the barn (currently the same
  main-floor + one-back-stall pattern), the church, the sheriff's office, the
  schoolhouse, Toby's house (a refuge, so keep it gentle), the Lodge interiors.
  Each is its OWN build (never two big scene changes in the air at once, #4b);
  provenance first (SCENE-DRESSING PROCESS), reachability re-checked with
  smoke's flood-fill, doors mostly CLOSED, varieties that fit context, and
  **doors placed in VARIED walls** (not all in E-W walls facing south -- mix
  side-wall N-S doors that open E-W with E-W-wall doors, error class #8;
  the shop pilot does this).

- **Interior partition CORNER BEVEL landed + rolled out (2026-07, maintainer
  "round that corner" call; DESIGN.md §6, `scenes/terrain.py`).** The chunky 90°
  corner where an interior partition wall juts into a room is chamfered in both
  wall draw layers (`_bevel_corners` -> `_extrude_box` bevel param +
  `_draw_wall_mass` clip); provably orthogonal to the run merge (runs/tees/shell
  stay full-thickness, byte-identical), draw-only. `_BEVEL_SCENES` now covers
  ALL above-ground building interiors (shop, church, barn, schoolhouse,
  sheriff_office, bedroom, clerk/guest rooms, lodge + lodge_hall, toby_house,
  farmhouse, lodge_cellar), each rendered + scanned; never the mine (thick reads
  right) or outdoors (byte-identical, confirmed by capture_world --diff). *(Open
  polish: tune `_BEVEL_INSET` (0.28·TILE) or subdivide to a 2-3 segment arc if
  the maintainer wants a rounder corner than the single 45° chamfer.)*

- **Thin-SLAB walls landed on the shop (2026-07, maintainer "thin the walls /
  walls are no longer tiles / connect them by smoothing it out"; DESIGN.md §6,
  `scenes/terrain.py`).** The step past the bevel, and unlike it, REAL geometry:
  a wall tile becomes a THIN slab (`_SLAB_THICK` = 0.5·TILE) as the UNION of up
  to two BANDS (a vertical band when a wall neighbour is N/S, a horizontal band
  when E/W), so runs, corners (L), tees, crosses, and the shell all meet FLUSH as
  thin walls with no fat junction and no notch. Cross-thickness: floor/wall both
  sides → CENTRE (two-sided partition); one flank off-map → the SHELL, hugging
  the EXTERIOR edge (outer face on the silhouette, no floor lip, thinning
  inward). `_wall_slab(scene, tx, ty)` returns the band-rect list, the single
  source for BOTH draw layers (`_extrude_box` `foot` param looped per band +
  `_draw_wall_mass` union clip) AND the collision/sight/nav predicates
  (`scenes/base.py` `_obj_solid_here`, shared by
  `is_solid_at`/`blocks_sight`/`_nav_solid_at`, point-in-ANY-band, inclusive
  bounds) — so the wall the player bumps and the AI sees IS the thin wall drawn.
  SUPERSEDES the bevel in a slab scene (`_bevel_corners` returns 0 there). Gated
  to `_SLAB_SCENES` (shop was the pilot; Wave A + the three principal seats have
  since opted in, below); every NON-slab, NON-rock scene stays byte-identical
  (capture_world --diff: brimley -- an outdoor scene -- unchanged; the slab + rock
  scenes legitimately differ). Guarded by `tests/stealth.py` §16 (bands thin, shell hugs the
  exterior, junctions connect flush, collision+sight+nav agree); full gate green;
  the shop verified live (VISION four-facing + dark + a top-down footprint
  schematic). **Corners ROUNDED (2026-07, maintainer "rounded corners where the
  walls connect"):** `_rounded_wall_poly` traces the band union to an outline and
  fillets each FREE corner (facing floor) into an arc (`_fillet`, radius
  `_ROUND_R`) while a wall-neighbour SEAM corner stays sharp so tiles connect
  flush; it drives the flat mass + a new 3D `_extrude_prism` (the rounded sibling
  of `_extrude_box`). Building outer corners + partition run-ends read rounded;
  collision/sight/nav keep the square bands (the rounding sits inside the drawn
  face). Verified live all four facings + dark. **No diagonal-only wall joins
  (2026-07, maintainer "add a rule not to have walls like that"):** two walls
  that met only at a diagonal (the corner tile missing) rendered as disconnected
  thin stubs; the shop's stockroom-SE and office-SW corners were closed (a wall
  added at the missing corner tile), and `terrain.diagonal_wall_joins` +
  `tests/smoke.py [10/10]` now FAIL any slab scene with such a join.

**THE ROLLOUT PROGRAM (2026-07, maintainer "apply to other scenes / fully take
advantage"; the shop is the finished reference).** The thin-slab + rounded +
real-geometry wall system is now a general geometry tool (single-source
`_wall_slab`, the `_rounded_wall_poly`/`_fillet` outliner, the `_extrude_prism`
that collision/sight/nav obey). Spend it in phases:

- **Phase 1 -- material foundation.** *(1a LANDED 2026-07.)* `_WALL_STYLES`
  (`{thick, round, rough}`) keyed per scene via `_SLAB_STYLE`, read through
  `_wall_style`; `_SLAB_SCENES` derived from it. So thickness + corner round
  read the CONSTRUCTION (`plank`/`plaster`/`timber`/`stone`) from one table;
  `plank` = the old fixed constants byte-for-byte (shop geometry proven
  identical, full byte-identity gate green). *(1b LANDED 2026-07.)* `rough > 0`
  runs `_roughen`: a seeded PER-TILE jitter on the FREE outline edges (seam
  edges + shared corners kept put, so tiles still connect flush and corners stay
  rounded), draw-only so collision/sight/nav still read the square bands
  (`§16`). `timber`/`stone` now read rough-hewn, not just thicker -- the same
  primitive the mine (Phase 3) reuses. *(1c LANDED 2026-07, maintainer "wider
  variety of colors".)* each style carries a dark muddy `tint` (delta on the
  near-black palette, both draw layers, Darkwood-safe) so a room reads its
  material in COLOUR too: warm-pine plank, pale plaster, red-brown timber,
  rust brick, cold blue-grey stone. Non-slab tint (0,0,0) → byte-identical.
- **Phase 2 -- interior rollout, one scene per build (consumes Phase 1 + grows
  new shape primitives on demand).** Per-scene definition of done: assign a
  style; redesign to multi-subroom (#4c interior doors, varied walls) if it is a
  box; clear diagonal joins (smoke [10/10]); grow the new shapes a room needs
  (round PILLAR from a lone wall tile → a cylinder via the prism; ARCHED
  doorway head; ROUNDED counter/desk); re-tune cover for the thinner walls;
  VISION four-facing + dark; full gate + `--diff`; docs same commit. Waves,
  simplest → richest: **A refuges** *(LANDED 2026-07: bedroom / clerk_room /
  guest_room_a+b = plaster, toby_house = plank; opted into `_SLAB_STYLE`, all
  four facings verified clean, no diagonal joins, gate green, every non-rolled
  scene byte-identical)*, **B explorables** *(ALL LANDED 2026-07: sheriff_office =
  plaster + church = plank with the three principal seats, then barn = timber +
  schoolhouse = plank in Wave 3; the church's curved apse / arched-window SHAPES
  were deferred to Phase 4, the style opt-in shipped without them)*, **C the
  complex** *(ALL LANDED 2026-07: lodge = timber, then lodge_hall = plaster +
  lodge_cellar = stone + abandoned_farmhouse = timber in Wave 3)*. **Phase 2 (all
  above-ground interiors) is now COMPLETE.** *(A/B/C SAFE_SCENES stay flat-lit +
  safe; only geometry + colour change.)*
- **Phase 3 -- the mine reimagined. *(LANDED 2026-07, maintainer "DO phase 3".)***
  A `_ROCK_STYLE` / `_ROCK_SCENES` set (the 16 mine scenes -- Works + Depths +
  Mara's cell) reads the new `rock` material: full-THICK (`thick`=1.0) but the
  rough-outline + prism DRAW, so the hewn walls read irregular/organic, not blocky
  boxes. Because `thick`=1.0 makes `_wall_slab` return full-tile bands AND rock
  stays OUT of `_SLAB_SCENES`, collision/sight/nav read the tile grid UNCHANGED
  (the roughening is draw-only, the mine's stealth footprint untouched); only the
  styled DRAW roughens. `round`=0 so rock breaks sharp + jagged rather than
  filleted; `rough`=3.2 (heavy) + a dark muddy earth `tint`. Guarded by
  `tests/stealth.py §16` (full-tile bands, roughened outline, full-thick
  collision+sight, rock excluded from `_SLAB_SCENES`, shipped scenes read the rock
  style); verified live (well_passage / depths_hall / works_cistern / works_sign,
  four facings + the dark). #14's side-dug chambers (the level-design half) are
  still open, tracked there.
- **Phase 4 -- freeform walls (the north star, "walls are no longer tiles" all
  the way).** A wall SEGMENT primitive (endpoints + thickness + style, off the
  tile grid) in the Scene model; collision/sight/nav read segment geometry; the
  prism already draws it. Unlocks diagonal walls, a curved church apse, a round
  silo/tower. Prototype ONE curved feature first.
- **Cross-cutting (every phase, never its own):** thinner walls occlude LESS →
  re-derive interior cover (the inner doors + furniture carry it, not wall
  thickness), extend `tests/stealth.py §16` as styles/primitives land; VISION
  toward the Darkwood organic read; guards + docs in the same commit.

**The three principal seats LANDED (2026-07, maintainer "Cranes, Vanes, and
Stables places should all be the thinner wall").** `church` = `plank` (its
board walls, matching draw_crane_tableau), `sheriff_office` = `plaster` (pale
institutional), `lodge` = `timber` (the rustic common room, its antler/firewood
dressing). One `_SLAB_STYLE` line each; the new geometry each just gained (the
church chancel windows, the office holding-cell bars + cabinet) reads clean
under the thin walls. All three verified live (VISION four-facing + dark, the
window/door seams checked), no diagonal joins (smoke [10/10]), full gate green.
The bevel is auto-superseded for them (`_bevel_corners` returns 0 on a slab
scene), so their `_BEVEL_SCENES` membership is now inert.

**Wave 3 LANDED (2026-07, maintainer "keep going onto wave 3") -- Phase 2 done.**
The rest of the above-ground interiors opted into `_SLAB_STYLE`: `barn` = timber,
`schoolhouse` = plank, `lodge_hall` = plaster, `lodge_cellar` = **stone** (the
first stone scene: rough cold-grey masonry, fitting a cellar), `abandoned_farmhouse`
= timber. All had zero diagonal-only joins (smoke [10/10] clean, no geometry
fixes needed); each verified live (VISION four-facing + the dark for the gloom
scenes); full gate green. Every above-ground BUILDING interior now renders thin,
material-coloured walls; the mine renders full-thick hewn rock (Phase 3, LANDED
below); only the outdoors stays full-tile.

**Still open:** Phase 4 (freeform off-grid wall segments, unlocking the deferred
curved church apse / arched window); #14's side-dug mine chambers (the
level-design half of Phase 3, the rock DRAW having landed); and the cross-cutting
cover re-tune as styles land.

### 11. **[Fable]** Brimley = the northernmost corn town, est. 1894  *(was GAME_CHANGES §27)*

Brimley **STAYS** northern MN; the corn is town identity — stubborn 1894
founders made it the world's northernmost corn town and got good at it, a
century of pride. **GUARDRAIL:** the corn is a **mundane human feat** (hardy
short-season stock, a river-valley microclimate, skill), **never the door's
doing** — else a second impossible thing AND it breaks the ~1993 door timeline.
Keep the impossible count at one (§1b). Theme: founding hubris rhymes with
crossing the threshold; the dead, uncut April corn reads as their pride rotting.
Surfacing (mundane Americana that curdles): ~~a weathered town sign ("BRIMLEY,
NORTHERNMOST CORN IN THE WORLD, EST. 1894")~~ (LANDED 2026-07: the old-timey
welcome board carries the boast + EST. 1894 in BOTH the intro drive-in sign
(`ui/cutscenes.py _draw_road_sign`) and the in-game welcome sign
(`rendering/props.py _draw_town_sign_solid`, the BRIMLEY variant only;
directional TOWN/WELL signs stay compact) — matching designs. **Still open:**
the SPREAD ending's blank-back BRIMLEY sign (`rendering/spread_drive.py
_sign_back`) was left untouched on purpose; sync it to the new board, see
Optional polish below), ~~a proud local line~~ (LANDED
2026-07: Old Pell is the grower — his PELL_CONVO corn exchange carries the
pride and the uncut-fields grief), county-fair ribbons (no dashes). Keep the §1 April dead-corn note. `NARRATIVE.md` §1 setting
note 2 gets the identity + guardrail.

### 12. **[Fable + Opus]** Royce the trucker + the rusting semi  *(was GAME_CHANGES §28)*

Promote Royce to the man who drove **Brimley's supply run** — the severed
supply line made a person (Hettie's shelves are bare because *his* deliveries
stopped). Fable: a small dialogue nudge (he ran the route, goods in and out).
Opus: place his **picked-clean semi rusting at the town edge** (the town ate
its own last shipment; optional light scavenge, **never evidence**). Reconcile
with his worker job-loop (pacing the road). Royce no longer converts (the
rot-people layer was cut, TODO #22c); he stays an ordinary local.

### 13. **[Fable]** PI theory ladder — the notebook thinks  *(LANDED 2026-07; was GAME_CHANGES §20)*

**DONE.** The case book carries two derived, first-person surfaces pinned
above the clue list (`ui/journal_ui.py`, the merged Casebook's Case tab;
`Game._working_theory` / `_case_timeline` in `systems/narrative_mixin.py`,
guarded by `tests/flow.py` §24d):
- **Working Theory** — a **set-aware** synthesis composed from WHICH clues are
  held, in any order (not a count tier): the read of Mara (taken → willing, the
  pivot needs the dig), the **bear-gated** son thread, the trap ("how do I get
  out?"), the **robes-as-lever** WRONG conclusion the game never corrects, and
  the Mask's SPREAD gravity. Absent threads simply are not there.
- **Timeline** — Mara's life in HER order (barn → store tab → booking → dig →
  letter), dated where the paper gives one and best-guess otherwise, capped by
  the frozen town clock.

The **wrong-space** beats fire from `cross_fold` (`_note_fold_portal` = a visible
pane, awe; `_note_fold_loop` = the SECOND silent loop, the creep), latching
`crossed_a_fold`. The FACT/SOURCE/QUESTION idea from the original brief became
the Timeline (a chronology reads truer than a flat list). Canon locked: the
NARRATIVE invariant "the PI accepts the impossible; he never learns the
mechanism."

**Opening rework (maintainer review):** the old soft-lead line (`_current_lead`)
is **cut from the notebook display** — the direction lives in the case file now,
not a header (the method + its §24c guard linger as dead code; retire both if the
soft-lead is fully abandoned). Theory + timeline are **earned** — pinned only
once they have content — so a fresh run opens on just `the_case`, never an empty
"theory." `the_case` was rewritten as a real case file (`Client:` / `Subject:`
format): minimal intake knowledge (drove north, went silent, trail to Brimley, no
religion or cult on the page), Walter's plea after the PI leveled with him, and
the PI's finisher pride SHOWN not told. The **robes-as-lever** thread now gates on
actually meeting the cult (the grab / their testimony), not the evidence count,
so the notebook never gets ahead of what he has met. First person throughout
(`_PI_WEATHER` too; §23/§24c green). *(Open polish: a scrollable card if the
theory outgrows one page; interior-beat tiering, parked from #22c.)*

### 13b. **[Fable]** Interior voice — quiet the routine reactions  *(maintainer call 2026-07; the Casebook merge landed the structure, this is the copy pass)*

**Structure LANDED (2026-07 Casebook merge, `ui/journal_ui.py`):** Inventory
(I) + Case Notebook (N) are ONE tabbed book now (Case | Tools | Papers), and
the Case tab opens on the **Working Theory pinned first**, so the notebook
READS as an evolving theory rather than a flat pile of reactions. Every
case-book write fires the (now NAMED + enlarged) corner scribble toast, the
one reliable per-write tell. **Still open (the maintainer's actual grievance:
"every interaction does something and never leaves the player thinking"):**
the on-screen PI narrator captions still fire on nearly every world-prop
examine. The census (grouped) for the copy pass:
- **First trim landed (2026-07):** the three clearest "spell out the
  conclusion for you" lines were cut to state-the-fact — `clerk_robe` (dropped
  "the smiling man is one of them"), `lodge_candle_callback` (dropped "part of
  it the whole time"), and the cellar-key pickup (dropped "nobody tends a key
  like this to a door that doesn't matter"). The player draws the inference
  now. The rest of the sweep below is still open.
- **Cut candidates (ROUTINE-REACTION, ~30 sites)** — prop examines that
  editorialize a conclusion: the lodge register/ledger recaps, the well /
  news-rack monologues (the payphone examine and the cellar-key dialog are
  already gone: play-notes cut + C4), headstone + candle
  re-examines, `barrow_tools` / `scarecrow` / `backwoods_note` / `worn_stone`
  / `bell_tower` / `the_burning` / `the_fall` / `threshing_floor` /
  `works_cistern_seen` / `the_doorframe` flavor `_evidence` (these write
  NOTHING to the book — caption only). Trim to a terse factual line (state
  the thing, cut the PI's spelled-out conclusion) or silence, so the player
  draws the inference. **The revisit-nudges** (`_REVISIT_NUDGES`, the
  "I should go back and ask him" appends) are the clearest "the game does the
  thinking for you" — decide with the maintainer whether they go.
- **KEEP (not reactions-to-random-things):** the five CANONICAL_EVIDENCE
  beats, the descent-voice arc (`_DESCENT_VOICE`), the dream, the Mask
  temptation, Mara's calling-out, the fold notes, the threshold recognition,
  and the deliberate atmospheric one-shots that ARE the dread (the frozen
  news rack, the empty church). Cutting
  these would hurt the game.
- Each cut must keep the flow.py guards green (many assert on these
  captions/notes — §16, §17b/c/d, §24) and update the ones whose behavior
  legitimately changes.

### 14. **[Opus]** The Works as a MINE — side-dug rooms, not hallways  *(was GAME_CHANGES §21; fiction + dressing + level-design all substantially DONE 2026-07; octagonal-room chamber calls revisitable)*

Make the Works read as a mining effort: timbered side-chambers dug off the
halls (some finished, some half-dug, the deepest hand-clawed), spoil heaps,
cart ruts, a degradation arc ending at the Deepest Face. A few pockets carry
loot / testimony placement; most is just labor made visible.

- **The FICTION half landed (2026-07, the mine retrofit + killer-cult
  scrub; guarded by flow §19b).** Room identities and text now read as the
  dig over old workings: `the_cells` = the diggers' bunk cells (captivity
  fiction cut), `the_old_stores` = the Old Stores (the bone vault is purged,
  `bone_rack` deleted from the furniture registry), every underground
  bloodstain/gore decal removed (the willing bled nobody), the Sorting
  Hall's "faces of the vanished" flyer wall cut, HUD display names cover
  the whole underground (the Deepest Face, not the cut Deep Stair).
- **The DRESSING half landed too (2026-07 art pass).** New procedural
  kinds, each registered in exactly one tilt set: `spoil_heap` /
  `shoring_frame` / `ore_cart` (SOLID_PROPS), `tally_marks` (wall deco),
  `mine_rail` (floor decal). Placed by mine logic: spoil + the barrow at
  the haul head (Shaft Floor), timber shoring at the gallery mouths and
  down the procession drift (the drift's stone pillars swapped to wood),
  the old workings' rail stubs under the candle line + the seized ore
  cart in a bay, inventory tallies over the Sorting Hall tables, and the
  degradation-arc climax at the Deepest Face (shift tallies by the face,
  unhauled spoil, downed hafts). The grain heap's baked-in "old blood"
  ring was recut to dark chaff (a killer-cult relic in the ART layer).
  The Sign Chamber stays deliberately bare: the one properly FINISHED
  room in the dig.
- **The LEVEL-design half -- ROLLOUT underway (2026-07, "keep going" after
  Phase 3).** Timbered side-chambers dug off the halls, each reached through
  a single ADIT off the floor (distinct from the open bays that already line
  the drifts): a FINISHED store (squared, crates + staged goods + a kept
  candle + a wall tally) and a HALF-DUG niche (a shallow ragged pocket, a low
  spoil pile + pick gouges, no light) -- the finished-vs-abandoned read #14
  asks for. Each cuts into a room's sealed wall block OFF the patrol lane, so
  the tuned crossing / props / hides stay untouched; reuses the shipped mine
  kinds (no new procedural kinds); per room reachability is re-checked (smoke
  [4/10] flood-fill), VISION four-facing + dark verified, full gate green.
  Landed, the four box / cruciform rooms with spare wall blocks: the **Timber
  Racks** (`well_passage`, the pilot, into the two north blocks), the **Sorting
  Hall** (`works_sorting`, the overflow store + a half-dug niche cut clear of
  the tally + taxidermy mounts), the **Kneeling Hall** (`depths_hall`, a
  finished store into the big NW corner stone off the nave, west of the
  crossing trigger), and the **Cistern** (`works_cistern`, a half-dug niche
  clawed into the dry SW corner toward the river). Full gate green each,
  including flow (the hall's kneel set-piece + crossing trigger hold) and
  stealth. **Assessed and NOT cut (existing shape + dressing already carry the
  read):** the octagonal / diamond / cavern rooms -- Shaft Floor (the haul
  head: spoil, barrow, fallen shoring), Scriptorium, Deepest Face (the single
  dead face, intentional), antechamber (the fall zone's old-workings props),
  threshing (a raw bitten cavern, miners at the faces), Old Stores (already a
  gear store), stair (empty by design) -- their `_bevel`/`_cavern` walls fight
  clean rectangular cut-ins and each is already dressed as the dig, so forcing
  a thin niche would be noise. The procession drift's 2-tile bands are too
  shallow for an enclosed chamber (its open bays already exploit that).
  The **cave-mouth ADIT door doors were already done** (`scenes/__init__.py`
  applies `door_style = "cave"` to every `UNDERGROUND_SCENES` room, so every
  mine exit renders as a jagged rock adit with timber shoring and no leaf,
  `scenes/terrain.py`). So the LEVEL-design half of #14 is **substantially
  complete**: the four cuttable rooms carry the "rooms cut off the dig" read,
  the octagonal/cavern rooms carry it by shape + existing dressing, and the
  scene doors are adits. The octagonal-room "not cut" calls are a judgment the
  maintainer can override (force a hand-clawed niche into the Deepest Face,
  etc.) if a stronger dug-everywhere read is wanted.

### 15. **[Fable]** Deadpan narration editing pass  *(was GAME_CHANGES §22)*

Sweep every narrator / world caption to the settled voice: objective, deadpan,
a little curt (the talk-reaction register). Kill aphorism and poetry where it
crept in; keep the sensation-only cosmic rule (§1b). *(The liminal-beat pass —
was GAME_CHANGES §24 — folds into #4 and #7.)*

### 19. **[Opus]** Carcosa palette alignment — one look, every glimpse  *(2026-07 ruling; NARRATIVE §5)*

**LANDED 2026-07 (`claude/opus-tasks-selection` branch) — pending the
maintainer's visual sign-off.** `_cold_fire_pit`
(`rendering/sprites_carcosa.py`) was re-graded off the pale-teal/green
palette into the codified black + dim-gold family: the receding-shaft
gradient, the rim tongues `(150,214,184)`/`(206,204,130)` → muted golds, the
writhing-form ellipse `(52,92,78)` → dark gold-brown, and the wet streaks
`(188,220,188)`/`(220,212,140)` → paler dim golds. The BREAK hard-cut
inherits it through `draw_king_death` / `draw_carcosa("spread")`. The
"cold/wrong fire" now reads through darkness + the writhing/drooling motion,
not hue. Before/after captures rendered; the full `python tests/run_all.py`
gate is green. The one thing left is a maintainer LOOK before it merges (the
call code can't settle). Original brief kept below.

Carcosa's look is codified (NARRATIVE §5): black is the ground note — black
sky, black stars, twin suns low, His gold fire the only light (the rift's
black-gold grammar at cosmic scale); the SEAL tableau is the reference image.
The King-catch furnace and the BREAK blast are off-model: `_cold_fire_pit`
(`rendering/sprites_carcosa.py`) burns pale-TEAL/green — tongues
`(150, 214, 184)` / `(188, 220, 188)`, forms `(52, 92, 78)` — and the BREAK
hard-cut (`draw_carcosa(..., "spread")`, `ui/cutscenes.py`) inherits it.
Re-grade the cold fire into the black + gold family ("fire, but wrong and
cold" must survive the recolor — wrongness by behavior and darkness, not by
hue). Verify with a before/after frame capture at sampled timestamps
(`tests/render_smoke.py` drives every ending) and a look from the maintainer
before it lands.

### 22. **[Opus + Fable]** The Case — evidence as Mara's trail (the big rework)  *(2026-07, settled with the user; canon NARRATIVE §6, design DESIGN.md §9)*

The evidence system is the game's crux (it drives attention, danger, and
the PI's unraveling) and it is currently half-dead: the "pool of six, any
3" never held (the surface three are mandatory, and evidence 4/5/6 gate
NOTHING — every threshold is ≤ 3). Rework it into **Mara's trail**: a
biography reconstructed from carryable, self-evident, Mara-only items.
Canon + design are written; this is the code catch-up. Big — touches
`CANONICAL_EVIDENCE`, the King-gate, the rot mixin, the confrontation,
and the tests. Sequence it:

- **22a. The roster. LANDED (2026-07).** `CANONICAL_EVIDENCE` is now the
  trail: `maras_receipt` (the store tab, Hettie's shop), `maras_record`
  (the booking slip, Vane's office), `maras_journal` (barn), `maras_dig`
  (the Sign in Mara's own hand, the Scriptorium — a room that is not the
  cell), `maras_room` (the unsent letter, her cell). All are **pickup
  items** (new items `receipt` / `detention_record` / `maras_scrawl`). The
  gate re-points for free (the count is `len(save.arg("evidence"))`, and
  `_evidence` only logs canonical names) — no gate-constant edits; the
  **three surface beats** keep the Act-1 ramp reachable above ground.
  `the_ledger` + `the_preacher` now file as case **notes** (`_evidence(...,
  note=True)`); `the_sign` leaves the count (the Mask stays the keystone
  item); **Mara is proof** (`the_congregation` files a note via
  `_log_note`, the calling-out still fires). **World-persistence:** the
  records live in the scene (the shop spike, the office files), not on the
  NPC, so a dead Hettie/Vane can never soft-lock the descent (warm handover
  still rides Hettie's Mara-memory beat). The obsolete `_the_third_thread`
  Crane-provoke stall-breaker was removed (the surface trail needs no
  provoke). Guards: smoke's canonical-wired scan follows the dict; flow §9
  gathers the three surface beats + a world-persistence check (§9b); the
  ledger/sign/preacher/congregation guards flipped to notes/proof. Full
  gate green.

- **22b. The bear + the name. LANDED (2026-07).** New item `bear` (tag
  reads **SAM**; the letter stays "a boy" unnamed, per the 2026-07 ruling,
  so the tag is the ONLY place the name appears besides the PI's mouth).
  Toby **lends** it as a VOLUNTEERED beat, earned by the PI's patience with
  a scared kid (`toby_told` + the `holding_up` reassurance), never
  interrogable; optional, never in `CANONICAL_EVIDENCE`, files a note. On
  the surface it is tender and unexplained; once the PI reads the letter
  (`evidence_maras_room`) its inventory desc **detonates** (dynamic
  `effective_desc`). The **name-beat** (`MARA_CONVO` "name" exchange,
  bear-gated, `ends:True`): the PI says the name, she seizes him, the rite
  cracks, she reveals she has always known the boy is not down there and
  digs on anyway, and **REFUSES the bear** (2026-07 ruling); fate unchanged
  (turns back to the dig). **Invariant guarded** (flow §28c): Mara never
  says the name; only the PI and the tag do. Full gate green. *(Open polish:
  a bespoke bear inventory sprite with a visible tag; the name currently
  lands through the item desc + dialog.)*

- **22c. The PI rots, not the town (four tiers). LANDED (2026-07).** The
  world rot is the INVESTIGATOR'S now (`DESIGN.md` §9; fixes STORY_AUDIT B6,
  NARRATIVE §2). The people-change is CUT: `_convert_local`,
  `_turned_local_dialogue`, `_converted_local_dialogue`, `ROT_TURN_LINES`,
  `_rot_locals`, and the `_spawn_counter_eater` tableau are gone, and
  `ROT_CONVERT` / `ROT_TURN` are removed from config. The town stays
  ordinary to the end (Mrs. Calder never joins and keeps both place
  settings; the resisters keep their voices; the rot DECALS + ambient air
  still run, the place still rots). In their place, a four-tier PI register
  (`scenes/dialogue._pi_tier` / `_PI_WEATHER` / `_pi_framing`) composes the
  PI's deepening interior weather onto each surface principal's conversation
  framing, keyed to evidence (0 / 1-2 / 3 / 4+); the NPC's words never
  change, only the man's read of them (Vane keeps his own mood prompt). Per
  the 2026-07 ruling, the converts' lost gaze pressure is **NOT** re-sourced
  (the cult enemy patrols carry it). Guarded by flow §23 (c)/(c2). *(Open:
  interior-beat tiering inside exchanges, and the theory-ladder notebook
  #13, both left for later.)*

- **Guards:** DONE across 22a-c. smoke's canonical scan follows the dict;
  flow §9/§9b (roster + world-persistence), §28c (bear + name invariant +
  bear-gated ending), §23 (no-people-change rot + four-tier register). Full
  gate green. `DESIGN.md` §3 describes the mechanism generically (unchanged
  by the key swap) and §9 already documents the model, so no §3 edit was
  needed.

**#22 is COMPLETE (22a + 22b + 22c all landed 2026-07).**

### 23. **[Opus + Fable]** Complex behavior for cultists and locals  *(maintainer-approved plan 2026-07; built in pilots)*

The cult AI and the town both deepen, inside hard fences: systemic not
scripted; the people do NOT change (only the cult may act wrong, and only
in cult ways; locals stay mundane and never signal the cosmology); nothing
touches the pacing ratios, the SAFE_SCENES refuge, fold-only pursuit
carry, or the Talk/two-touch gates; no new behavior ships with explanatory
player-facing text (the behavior IS the tell); the King and hollow Sheriff
keep their exemptions.

- **23a. Cult liveness pilot. LANDED (2026-07) except station
  authoring.** Two scout-only beats in `systems/stealth.py`, wired into
  BOTH cult machines (`entities/npc.py` + `entities/enemy.py`); tuning in
  the `CULT_SYNC_*` / `CULT_HANDOFF_*` config block. The **synchrony
  beat** (`sync_pause`): on one shared clock every idle cult scout pauses
  mid-stride at the same instant, one breath, then resumes (the
  claimed-as-one-body wrongness, ambient). The **hand-off**
  (`handoff_step`): two scouts whose rounds cross stop, face each other
  for a silent beat, and part on a long per-actor cooldown. Both run
  AFTER detection/hearing score the tick and never own any state but
  scout: a frozen scout still fills suspicion and still promotes
  (guarded end-to-end by `tests/stealth.py` §12); set-piece kneelers
  keep their scripted stillness. **Still open in 23a:** job-station
  authoring for the patrolled cult rooms that have none (works_sign's
  lone patrol) -- place via the SCENE-DRESSING PROCESS (render first,
  never by name).
- **23b. The town half.** The **yield**: a local a cult patrol passes
  steps off the lane, eyes down, waits, resumes; the cultist never
  acknowledges them (the trapped-WITH-them split staged in pure
  movement, no dialogue). **Mundane witness reactions**: a local who
  sees the drawn gun, a sprint, or a moth axed flinches or hurries
  indoors (rides homebody `_inside`); a kill nearby empties the street
  for the visit. Strictly mundane reactions only, which strengthens
  their ordinariness.
- **23c. The mechanical pieces, sequenced for the #5 tuning pass.** The
  SEARCH **sweep partition** (multiple searchers divide `sweep_points`,
  no duplicate checks); **room posture** (a per-scene calm/uneasy/roused
  int raised by flares, shots, struggles, and found bodies, decaying;
  modulates walk speed, scan time, and sweep budget -- ship OFF-default
  behind config until the human tuning pass absorbs it); the **flank
  call** (a LOCKED chaser pulls at most ONE nearby patrol to a flank
  point; same LOS and suspicion rules, normal search timer, never soft
  omniscience); **object-state investigation** (a left-on noisemaker, an
  opened door, a moth husk: pause at it, mark the room uneasy).
- **23d. Content passes (anytime, Fable).** Fuller local **day-loops**
  on the JOBS `stations` plumbing (Pell to the field edge he doesn't
  look at, Calder to her gate, Royce circling his truck; door-anchor
  honesty rules apply); **disposition framing** read off existing save
  flags (mood, never a meter -- the TODO #2 fences).

## Blocked on a human at the keys

These are BUILT and guarded; what remains cannot be settled from code
inspection and needs a person playing the game.

### 5. **[Opus]** Stealth rework — the TUNING loop  *(FIRST HUMAN PASS LANDED 2026-07)*

The mechanic AND the placement pass are built and guarded
(`tests/stealth.py` + flow §25; see `DESIGN.md §12` for the design
and its status note). **The first human playtest (2026-07) found four
faults and a batch landed against them** (guarded by stealth §13):
1. *"Hiding spots as objects are too rare"* -- CONFIRMED (23 enclosed
   hides in the game, ~all underground; seven of the eight surface
   patrol scenes had zero). Landed: +7 surface hides on EXISTING props
   (under the rust wagon + dead sedan on cornfield_path, under the
   lodge-yard pickup, in the backwoods cordwood stack, under Calder's
   supper table + the dead pickup in brimley, and UNDER THE BRIDGE at
   the town's centre -- the crossers knock on the planks overhead,
   `Game._tick_bridge_knocks`, dressing only). **Still open:** the
   scenes with no honest anchor (graveyard, country_lane,
   gravel_road_north) need a bespoke crawlable prop each, placed via the
   SCENE-DRESSING PROCESS; the cornfield_maze stays hide-free on purpose
   (its terror is exposure in corn).
2. *"Corn / tall grass is invisible"* -- CONFIRMED (`:` cover rendered
   as a flat floor tint). Landed: the tall-grass tuft layer
   (`_tilt_grass_solid`, scenes/terrain.py): every bare `:` tile stands
   up as waist-high dead-straw blades, depth-sorted with the corn so the
   player wades IN. Draw only; collision/sight/cover rules untouched.
3. *"No narrator boxes on stealth entry"* -- landed: both one-shot
   teach notices (corn, shadow) CUT; `hide_enter`/`hide_exit` audio and
   the visible cover are the only tells.
4. *"Running around the cultist beats hiding"* -- CONFIRMED by the
   numbers (cultists moved at 68% of WALK speed). Landed, the three
   economy levers (`CULT_CHASE_MULT` / `CULT_GRAB_REACH` /
   `SUS_SPRINT_MULT`): the locked-chase gear (ladder now King > sprint
   105 > chase 85.5 > walk 84 > scout 57 -- walking away is dead, sprint
   still escapes but drains and winds), the arm's-reach grab (brushing
   an awake cultist fires the grab; Talk/two-touch gates unchanged), and
   sprint-in-LOS multiplying the detection score.

Landed with the pass (2026-07, maintainer-approved): **river stones**,
the proactive distraction verb -- finite walk-over pickups where the
water runs, right-click lobs one, the landing is a placed noise event
that turns idle scouts and never diverts a sighting-born search -- plus
the two approved follow-ons on the same plumbing: **a stone through a
window** (the loud tier: diverts even a search, breaks once, dark +
shard-toothed for the run via the broken_windows ledger; draw only,
never an entrance) and **a stone down the dead well** (the shaft's
rattle routes the square; no bottom ever sounds, wordless). All in
`STONE_*`/`GLASS_*`/`WELL_ECHO_*` config; DESIGN.md §12; stealth §14.
Spitballed and parked for a decision: the crouch stance (after the next
playtest) and the window-vault prototype (one building, look-passed,
last).

What remains proves out only against further play: the new constants'
FEEL, the suspicion fill curve (`SUS_FILL_RATE`), the concealment
factors, the sweep budget, and the struggle window/presses. Also
deferred on purpose: the Pillar-2 **peek** verb (free look under tilt
already carries the information function) and an exit-takes-a-beat
vulnerability window on enclosed hides.

### 6. **[Opus]** Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by default:
the gun goes **stun-only at 3 evidence** with ~14 rounds total per run, so the
main combat verb is removed exactly when danger spikes (agency loss vs
intended dread). There are **no difficulty options**, so the visibility/Watcher
death-spiral hits newcomers and is trivial to experts. Items are gates, not
resources (armor slots return 0). Consider: transforming the stun into a
tactical window rather than a tax, an easy/hard toggle, or light resource
tension — only if it serves the horror, not despite it.

- **Two-touch cult grab LANDED (play-notes 2026-07).** Capture-on-contact
  was softened: after the one-time Talk, the FIRST grab of an encounter shoves
  the PI free (`_cult_shrug_off` — grabbers stagger, he bursts loose with
  `CULT_SHRUG_INVULN` grace), and only a SECOND grab before he reaches a
  SAFE_SCENE is the CAPTURED fail state (`_cult_touch_count`, reset only on a
  safe zone). Directly answers the "nothing you can do once they're on you"
  play-note. Still open here: the gun stun-window and difficulty options.

## Deferred / north star

### 7. **[Fable]** The liminal-composition pass  *(DESIGN.md §4/§10)*

Not a discrete ticket — a standing direction for per-scene level-design polish:
composed emptiness, long sightlines, uncanny repetition. Inherently
iterative. **To turn it into work, name ONE scene and the ONE composition it
gets** (this sightline, this repeated landmark); do not start against the
abstract goal. *(The buildable-now #4 is this pass aimed specifically at
outdoor dread — start there.)*

### 8. Parked — terrain & reshape megabuilds  *(2026-07 design call; do NOT pull forward without a set-piece that demands it AND a fresh decision)*

Cut from active work because their payoff (outdoor sight-occlusion / a sealed
bounded town) fights their cost, and the tilt camera already buys most of the
illusion for free. The cheap replacement is the composition pass (#4). The
DORMANT heightfield prototype + the SHIPPED carved river channel STAY (harmless,
byte-identical at pitch 0); it is the general-purpose builds below that are
parked.

- **Floor-roll warp (was #3d).** Replacing the global affine `_tilt_warp` with a
  height-displaced warp so the whole floor raster rolls. Parked: at ~55° a crest
  tall enough to occlude a standing figure over a short outdoor sightline is a
  near-cliff, not a gentle hill, so a general rolling floor reads wrong at this
  camera; plus a rendering rewrite + a perf pass on the ~6000-tile bake. The
  controlled-shape cases (the carved river trough) already ship without it.
- **Terrain design directions (was #3e).** The sunken-lane cover class, the King
  crest-reveal, terrain-herding toward the well, the deferred peek verb's home.
  All depend on the parked floor-roll and on AI that reads height (v1 ignores
  it). Revisit only if the floor-roll is ever un-parked for a specific set-piece.
- **Brimley reshape (was #4).** Round/organic fog-edge remask + radial
  "handed-back" membrane + subsidence bowl. Parked: **Brimley STAYS a square** —
  the tilt camera + sight cone + fog rim already mean the player never sees a
  corner or a straight edge, so the reshape spent a real build (stressing stealth
  suspicion + King/NPC nav) on an illusion break the camera does not allow. The
  torus wrap + fog rim it wanted to keep "underneath" are already the shipped
  substrate. The one salvaged win (a smaller grid, the actual FPS lever) is split
  out to Optional polish.

### 20. **[Opus + Fable]** Endings redraw with the close-up techniques  *(maintainer thought, 2026-07 — parked, NOT scoped)*

A passing maintainer note after #2b landed: the ending presentations (the
King-catch furnace, SEAL's lines-on-black tableau, SPREAD's drive-out,
BREAK's mask-yank + blast) predate the close-up tableau art pass and could
be redrawn with those techniques (the bespoke portrait register, reactive
state, the corrected edge-dark vignette — note the older seats' shared
vignette loop actually darkens the CENTER; their art was tuned to
compensate, so any redraw should use the corrected ramp from Mara's
frame). Parked on purpose: the endings are approved, flow-guarded
set-pieces (their lines + palettes are canon, NARRATIVE §5/§8), so this is
a re-presentation question, not a gap. Do not start without a fresh
maintainer decision, and land each ending only through a look pass
(VISION.md; `tests/render_smoke.py` drives every ending).

### 21. **[Opus + Fable]** Light-driven dread — the blackout + watcher-in-dark storm  *(design sketch with the maintainer 2026-07; the LIGHTING FOUNDATION landed, the storm is parked)*

**Foundation LANDED (2026-07 lighting pass).** Brimley's civic light is now
period-correct **electric** (cold `yard_light` poles + gas `generator`s
outside each building; the wrong-century civic lanterns are gone), and the
light system is **shared**: `_draw_dark` iterates `FIXTURE_POOLS` across
EVERY emitter (not just `wall_torch`), so any fixture lights the dark it
stands in -- proven by the underground candles now casting real pools
(DESIGN §6; NARRATIVE §5 grid-died-with-the-fold). This is the substrate the
maintainer's blackout idea needs (killable light nodes + a real light
system), teed up but NOT built.

**Interior lighting LANDED too (2026-07, "do 3 then 1" pass 1 of 2).** The
explorable non-refuge interiors (`DIM_INTERIOR_SCENES`: shop, church, barn,
schoolhouse, sheriff's office) are now `DARK_SCENES` at a lighter gloom (72),
lit by the period-electric **`wall_lamp`** (genset bulkhead fixture) with the
old candles/kerosene demoted to accent -- they read dim-lit-by-bulbs with dark
corners (DESIGN §6). The refuge (`SAFE_SCENES`) is deliberately excluded and
stays flat-lit + safe. This is pass 1 ("just fix interior lighting first"); the
Watcher rework below is pass 2 ("no light = danger").

- **Watchers in the dark, scoped. LANDED (2026-07, pass 2 of "3 then 1").**
  The non-refuge interiors (`DIM_INTERIOR_SCENES`) now adopt "no light =
  danger": `WATCHER_OPEN_SCENES` folds them in, and in those rooms
  `_tick_watchers` treats being in the DARK as exposure -- a light POOL
  (`Scene.lit_at`) or the flashlight is the cover, and a Watcher caught in a
  pool / the beam BURNS out (`WATCHER_LIGHT_BURN`, `_tick_watcher_gaze`). The
  true refuges stay gaze-free (`SAFE_SCENES` excluded + `KING_FREE`). Guarded
  by `tests/stealth.py` §11 (rewritten); DESIGN §4/§6, CLAUDE.md reconciled.
  **Still open here:** the "go further" variant (even the refuges lose their
  light-safety) is deliberately NOT built (the refuge is load-bearing); and
  the blackout below is what makes it a *storm*.
- **The moth blackout.** A moth flare knocks out the lights (kill a genset
  node / drop the yard-light pools), the screen dims, and the cult camp
  forms a procession to the flash and fans out to search. Rides the shared
  light system + the existing moth flare (`rot_mixin`) + the procession
  liveness (#23). Needs: a genset→fixtures power link (kill node = pools
  die), a scene-level "blackout" state, and the procession staging.
- **Watchers-in-the-dark.** Rework Watchers so they can open in ANY room
  but only EXIST in the dark; the flashlight (or standing deep in a light
  POOL) is what dispels them -- burn them out by getting lit. Couples with
  the blackout (moths kill the lights → the dark → the Watchers) into "a
  perfect storm." A real rework of `_tick_watchers` (DESIGN §1/§4), not a
  tuning pass; keep the below-3 threat role.
- **Retire the "special darkness" beam-off?** The deep (`CULT_DARK_SCENES`)
  still swallows the flashlight by design (DESIGN §1). The lighting pass
  did NOT change this (the deep is lit by its own ritual fires now, which
  reads well); whether to fully retire the beam-off so light works
  everywhere is the open dread decision here. Do not flip without a
  maintainer call -- it softens a deliberate dread.

All three are gated on a fresh maintainer go (per the 2026-07 discussion
they were design-only). The **capture→King-unleashed** thread and the
**procession-across-scenes** staging were sketched the same session and
sit here too, unscoped.

### 16. **[Opus]** Ship track — packaging  *(was GAME_CHANGES §25)*

Itch-ready build: pyinstaller (or equivalent) one-file win/linux builds,
save-dir sanity, a settings sanity pass, a version stamp. End-stage; do near ship.

### 17. **[Opus + Fable]** The ancient altar — the CAP of the last sealing  *(was GAME_CHANGES §17; rides #18)*

Move the mid-Brimley standing stones to the **riverbank** (over the point the
Threshold sits beneath; keep the worn cult path). Pre-cult dressing: lichened,
weathered, sunken, nothing yellow — reads OLDER than every cult mark. ONE worn
carving that recontextualizes after the player has seen the Sign (matches the
Mask grammar) + a single `notes` beat (never evidence, no cosmology, §1b). Gives
SEAL its precedent without a word. Lands with the compression pass.

### 18. **[Opus]** Brimley compression (60x60)  *(LANDED 2026-07; was GAME_CHANGES §23)*

**DONE.** `scenes/brimley.py` `build_brimley` was rewritten from 100x100 to
**60x60** as a full RESHAPE (not a scale-down): the river moved to col 30 with
the bridge + fold road crossing at rows 24-26, the seven buildings redistributed
around a central west-bank plaza (church + barn north, shop + school
upper-middle, sheriff + farmhouse south) with the kid's house alone on the
narrow east bank, and the well/noticeboard/wheelbarrow gathered into an eastern
lodge square just inside the lodge-road entry. Nothing sits where the old code
put it; everything is KEPT (all 7 buildings + doors, all exits + spawn names, the
well/barrow/news-rack/payphone landmarks, the standing-stone ring, the burn-
clearing entrance, the bridge + whirlpool, all locals + cult stations +
noisemakers, the corn/marsh/forest-band cover). The SHAPE stays a square with the
torus wrap (fold road row 25 E-W, forest N-S) + fog rim underneath. Reconciled
callers: `systems/config.py` OUTDOOR_DECAY brimley tiles re-pointed to the new
building thresholds; `tests/stealth.py` `open_field` + the bell/walls fixtures
moved to the new geometry (semantics unchanged). Full `python tests/run_all.py`
gate green; a tilt capture confirms the arrival view. **This also lands the
Optional smaller-grid perf pass** (the one-time whole-map tilt bake dropped from
~10k tiles to 3,600).

**Follow-up (2026-07): buildings front the street.** Each door was reoriented
onto the wall that faces its adjacent road, a natural MIX rather than all south:
`_stamp_building` now takes a `face` ('n'/'s'/'e'/'w'). Church + sheriff open
EAST onto the central spine; barn + farmhouse open WEST; the shop + school (which
sit right above the E-W fold road) open SOUTH onto that main drag; the kid's
house opens NORTH onto its access road. Spurs, spawn-backs, the bell-door anchor,
the flanking lit windows, the door lanterns, the homebody anchors (Hettie/Pell),
and the farm's cult front-yard all moved to the new faces. The shared door
renderer's `_door_room_dir` (`scenes/terrain.py`, used by BOTH the flat and tilt
draws) was made **roof-aware** (roof = interior) **and window-aware** (a window
is part of the wall line) so a door on ANY face resolves its opening direction
correctly (a census proved it changes only these Brimley doors and is
byte-identical for every other door in the game). A **fold guarantee** was also
added: the forest band's de-clump skips the outermost ring, so a post-pass flips
any wrap-edge tree with no walkable neighbour to a passable look-alike ('p') --
the torus crossing is never blocked by an edge tree, and there is no solid
perimeter wall. **Still open:** the altar move (#17) did NOT ride inside this pass — the
cult standing-stone ring stayed in the open NE field rather than relocating to
the riverbank; #17 remains its own narrative-dressing ticket.

---

## Standing fences (guardrails, not tickets)

- **The lure chain is NEVER stated diegetically** *(was GAME_CHANGES §10)*.
  King → Mara → Walter → PI is felt, not said. The faint unease now lives in the
  `the_dream` and `the_congregation` notes (NOT `the_case`, which the 2026-07
  review rewrote into a clean mundane intake, cutting its old "couldn't say why"
  beat); the "why is a finisher this deep on a nothing-case" disproportion is
  left to be FELT in play, never stated. Do NOT build on any of it. King/Watcher
  moments read as **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing** (#11). Keep the impossible
  count at **one** (§1b): the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).

---

## Optional polish (no canon/lore change; do as time allows)

- **[Opus]** **SPREAD ending sign sync** *(2026-07; deferred with the intro-sign rework, TODO #11)* — the intro drive-in sign and the in-game welcome sign now render the old-timey BRIMLEY board (WELCOME TO / NORTHERNMOST CORN / EST. 1894, POP struck through). The SPREAD ending's drive-OUT shows the **blank back** of that same sign (`rendering/spread_drive.py _sign_back`, "the side they never painted"), which was left untouched. Update `_sign_back` so its board proportions + posts match the new welcome board (the back stays blank/unpainted by design; only the shape needs to agree). Verify with a headless capture of the SPREAD drive-out (`tests/render_smoke.py` drives every ending). Do NOT touch the rest of the ending.
- ~~**[Opus]** **Brimley smaller-grid perf pass**~~ **DONE (2026-07), landed with the full 60x60 reshape (#18).** `w`/`h` cut 100×100 → 60×60 and the 7 buildings + well re-packed, shape + boundary unchanged (square + torus wrap + fog rim stay). The whole-map tilt bake (`scenes/base.py` `_tilt_fullmap`) drops from ~10k tiles to 3,600. Verified with a `tools/capture_world.py` tilt capture + the full `python tests/run_all.py` gate.
- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** *(NARRATIVE.md §4; feeds off the #1 provoke pilot)* — Fable for the reveal writing + staging, Opus for the procedural corpse sprite. Punch up
  the `preacher_doomed` death. ~~(1) New discovery location~~ **DONE
  (2026-07):** the doom sends Crane out of his church (the emptied nave's
  one-shot river-mud line points at the water) and his body is found on the
  **Brimley riverbank** (`_brimley_on_enter` / `_preacher_bank_pos`;
  `preacher_body_seen` sets on walking up, so Vane's + Hettie's one-shots can
  never announce an unfound killing). Still open: (2)
  **Bespoke sprite**: the current corpse is a placeholder medieval knight
  (`_draw_body`: helmet + spear + tabard-grey) — replace with a gutted-preacher
  draw (dark palette, white collar, cross in the mess). (3) Stage the approach
  (wrongness before sight, long sightline). Art only now;
  lore unchanged.
- **[Opus]** **Held-weapon offset per camera yaw** *(was HANDCRAFT_BACKLOG 3b)* — `draw_axe_held` reads at rest; the one remaining note is an eyeball pass on the equipped-weapon offset at every camera yaw so it never floats off the hand. Verify with a tilt capture across yaws.
- **[Fable + Opus]** **The grove reads north of Brimley, the river in view** *(2026-07 canon ruling)* — `effigy_grove` is the mouth of the cult's mine, north of town above the river (NARRATIVE §7), and the congregation walked there openly before the rite hid it; the scene art is still a bare corn crop circle. Dress the rim so the river reads below it (the water in view, the dug mouth framing the descent pane) and the northern placement lands without a line of dialogue. Decoration only; the rite, the gates, and the pane stay exactly as they are. Verify with a `tools/capture_world.py` tilt capture + the full `python tests/run_all.py` gate.
- **[Opus]** **Higher-contrast see-through doors** *(DESIGN.md §7)* — now that the
  aperture's actors are sight-gated, opt in the doors where the
  effect reads strongest: a lit room off a dark hall, the front door onto the
  yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** *(DESIGN.md §1 / `DESIGN.md §7`)* — the King currently looms through the rift only while it *forms*,
  then steps through (intentional per `DESIGN.md §7`). A persistent silhouette
  on the far side of an already-open fold is not built; revisit only if the
  direction changes.
- **[Opus]** **Mine retrofit tail cleanups** *(2026-07 code review; none player-visible)* — (a) cache the `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall cards (well_passage re-projects ~280 points/frame live); (b) fold `_RACK_CHARS` into the shared wall-scan char-set plumbing instead of a third parallel set; (c) the cave `door_style` key list in `scenes/__init__.py` duplicates the `UNDERGROUND_SCENES` gating idea — derive from one source; (d) `husk_bundle` + `pillar` are registered kinds with no placements (keep as reusable art or cut). Verify: `tools/capture_world.py` tilt capture byte-diff + full gate.
- ~~**[Fable + Opus]** **The barn reads lived-in by several people**~~ **DONE (2026-07).** `build_barn` (`scenes/interiors.py`) now lays SIX bedrolls staggered across the main floor (clear of the spawn tile, the col-5 walk to the back stall, and the door approach) with folded `effects_pile` belongings beside a couple and two gear crates -- a commune dormitory (Toby: "They slept all over then. The barn."), not one farmer's cot. Decoration only (floor decals, non-blocking); the `maras_journal` beat + the door-dream + the sealed hatch are untouched. VISION-verified (the dormitory read lands unambiguously) + full gate green.
- **[Opus]** **Redecoration-audit deferred polish** *(2026-07 17-scene visual audit; every MEDIUM+ finding was fixed, these LOW items were deliberately deferred)* — (a) bell tower: ~~a bespoke timber bell-stock frame (A-frame uprights + yoke) instead of the scaled table platform~~ **DONE (2026-07):** new `bell_stock` SOLID_PROP (`rendering/props.py _draw_bell_stock_solid` -- a braced timber trestle: four canted posts to a headstock beam, ledger ties, knee braces, iron gudgeon straps) replaces the `scale=2.0` table box; same 2x2 collision footprint, the bell hangs off the headstock; VISION-verified four facings + dark (reads as a bell frame, not a platform), gate green, stale docstring reconciled. **Still open in (a):** louvered belfry openings instead of the glazed cottage windows (the `'i'` window char renders glazed everywhere, so a belfry louver needs its own window style or a wall-deco louver over the openings -- a small mechanism, deferred); ~~(b) schoolhouse: jitter the 12 grid-locked cots a few px so the dormitory reads crammed, not installed~~ **DONE (2026-07):** each cot is nudged a few px off its tile (DRAW only, seeded per tile; the collision footprint stays tile-locked), so the two banks read shoved-in by hand, not an installed grid; VISION-verified + gate green; (c) hanging_figure legibility: the sprite reads as a standing hooded blob among trees, not a suspended body (graveyard, clearing, backwoods_cabin) — verify/redraw the hang; (d) lodge: cluster the missing-flyer/polaroid "wall of the vanished" above the reception desk instead of interleaving with trophies; (e) lodge_hall: bump the side-table footprint and re-home the corner-crammed sampler; (f) guest_room_a: nudge the buck trophy toward a light source; ~~(g) farmhouse: the "phantom marks on the walls" comment vs floor-decal render (stale comment or wall kind swap)~~ **DONE (2026-07):** resolved as a STALE COMMENT, not a wall swap -- `phantom_mark` is a `_FLOOR_DECAL_KINDS` decal used game-wide (it warps onto the floorboards under the tilt and reads fine there, VISION-checked in the farmhouse), so the farmhouse comment AND the misleading `_draw_phantom_mark` draw-comment ("scratched into a wall") were corrected to say floor. A game-wide wall-deco swap was deliberately NOT done (big blast radius across ~10 scenes; revisit only if the maintainer wants marks up on the walls). All are polish; each needs a capture per VISION.md when it lands.

---

## Process

### R. **[Fable]** Cross-model review gate  *(process; new)*

After an **[Opus]** ticket lands, run a **Fable** review pass before it
merges. This is NOT a code-correctness re-audit (use `/code-review` or a
fresh Opus context for that, since a model self-reviewing its own diff is the
weakest check). Fable judges what it is strongest at for THIS game: **does the
change land the feeling and hold canon.** For a given diff + the running
build it answers:
- Does it read as dread, or as a mechanic showing through? (atmosphere,
  pacing, the tell)
- Does any player-facing string break the no-dashes rule or the
  `NARRATIVE.md` voice?
- Does it contradict a locked canon fact (`NARRATIVE.md`)?
- What is the cheapest change that would make it land harder?

Output is a short verdict + ranked notes, not a rewrite. The value is a
SECOND, independent model looking at the work, so the direction can flip: if
Fable is doing the implementing, an Opus pass reviews it the same way.

---

## Story & dialogue audit — open findings (re-verified 2026-07)

> Folded in from the retired `STORY_AUDIT.md`. The audit's **A** (broken
> beats) and **B** (canon breaks) tiers were resolved on-branch; **B6** and
> the convert half of **B7** are mooted by the TODO #22c people-change cut.
> Every **C** item below was **re-verified against the current tree**
> (2026-07); FIXED/MOOT ones were dropped or marked. The **D** voice/polish
> items are player-facing TEXT (still open); the audit's "stale dev comments"
> item is **DONE** (see the note under D).

### C. Interaction-logic bugs — ALL RESOLVED (2026-07)

The whole C tier is closed. The batch C1, C2, C4, C5, C7, C10, C12, C13,
C14, C15, C16 landed on the `claude/opus-tasks-selection` branch (verified
against the current tree first, then fixed + guarded); the earlier sweep
had already handled C6/C8 (dead code removed) and C9/C11 (dropped), and C3
was MOOT. Kept as a resolution log, not open work.

- **C1. RESOLVED.** `_sign_update` step 4 (`scenes/well.py`) now holds the
  rite-holder closer while `game.narration.active`, so a fast Mara exchange
  no longer clobbers the lure caption (which has no `on_complete`).
- **C2. RESOLVED.** `_reset_run_state` (`systems/game.py`) now clears
  `_mara_stage`, so a death/quit mid-staging can't eat the next run's
  calling-out.
- **C3. MOOT (audit reasoning was wrong).** The `< 3` grove-meter beats
  (`scenes/hidden_folds.py`) are reachable via the ungated `sable_on_death`
  Invitation drop. Residual: on the intended path the gradual fill is never
  seen (an authored-for-an-unreachable-progression smell, not dead code).
- **C4. RESOLVED.** The cellar-key pickup dialog (`scenes/lodge_yard.py`
  `_took`) was deleted outright (superseding the earlier trim that kept the
  key-on-a-nail line): the cellar key is now a quiet walk-over pickup, the
  "Picked up: Cellar Key" HUD notice + chime its only feedback. Maintainer
  call: a key pickup should not give off dialog.
- **C5. RESOLVED.** The church LOGIN terminal (`scenes/villager_houses.py`)
  was removed outright — the `_open_login_terminal` handler, the invisible
  interact NPC, and the CRT prop — killing the always-"ACCESS DENIED" ARG
  tone in a 1994 parsonage. The leftover `C` map marker is blanked to floor.
- **C6. RESOLVED (dead code removed, earlier sweep).** The unreachable
  `blocking_innkeeper` branch and its docstring were deleted; the bedroom is
  intentionally ungated.
- **C7. RESOLVED.** "You dream of a doorway." (`ui/cutscenes.py`) is now
  gated to rite mode, so it no longer renders during the waking memory flash
  (the dream-once canon).
- **C8. RESOLVED (dead code removed, earlier sweep).** The unreachable
  `_on_player_death` respawn path was deleted.
- **C10. RESOLVED.** Garrick's "days now" beat (`scenes/brimley.py`) now
  gates on `preacher_body_seen` (matching Vane), so it can't fire the
  instant Crane is pressed.
- **C12. RESOLVED.** `_spawn_hunting_sheriff` (`systems/rot_mixin.py`) still
  spawns + holds every hollow-office load (the room stays lethal), but the
  intro notice + sting now fire once per run (`_sheriff_announced`), and the
  line trails off ("But I can't ...") instead of reporting the failure.
- **C13. RESOLVED.** The Sable fold reproach (`scenes/dialogue.py`) now
  requires `crossed_a_fold` in addition to the `the_fold_told` note, so the
  first-person "it set me back down" is never a lie (flow guards updated).
- **C14. RESOLVED.** (a) the handler-less dresser `[E]` cue was dropped
  (`scenes/lodge.py`); (b) Toby's closet drawing left as-is (decoration
  only, no false prompt); (c) the altar `[E]` cue is now dropped once the
  Mask is taken (`scenes/well.py` `on_enter_fn`); (d) the barn + farmhouse
  sealed hatches now show a deadpan notice (`scenes/interiors.py`,
  `scenes/villager_houses.py`).
- **C15. RESOLVED (annotated).** `_threshold_seal` (`scenes/depths.py`) got
  the explicit comment that the lone-trigger is DELIBERATE — the
  point-of-no-return fork is spent upstream at the blast, so carrying the
  Mask to the frame IS the commit.
- **C16. RESOLVED.** `_ready_for_the_desk` (`scenes/dialogue.py`) dropped the
  `sable_greeted` requirement (the PI checked in at that desk on arrival), so
  a player who never greeted Sable still gets the go-back-to-the-desk pointer
  at 3 evidence.

*(Earlier: **C9** — Pell no longer `fold=True`; **C11** — Toby's cold-open
is gone, his witness account is photo-earned.)*

### D. Voice / polish (player-facing text — still open)

- ~~Narrator "vanished into the corn" + tense sweep~~ **DONE (both halves,
  re-verified 2026-07 doc audit):** the narrator corn line no longer ships
  anywhere (only Crane's own-voice "drifted out to the corn" remains, which
  stays deliberately: his fallible impression, testimony in his own mouth);
  and the Fable tense sweep fixed every ended-arrivals line (Crane's greet +
  intro + "They all stopped.", Sable's "faces came" + "went the same way",
  Vane's "kept to their own").
- Descent interior voice wobbles POV (first-person notes vs second-person
  on-screen beats, `systems/game.py`).
- ~~Notebook headers from slugs (`ui/notebook_ui.py`): "Maras Room", "Chalk
  Deep", "Descent Mask", "Showed The Clerk" — dev slugs where the case file
  should read like the PI typed it.~~ **MOSTLY DONE (2026-07 Casebook merge):**
  the slug→title map moved to `ui/case_titles.py` (`humanise`, shared by the
  book and the scribble toast) and was expanded to cover the interior beats;
  any unmapped slug still falls back to Title Case, so add authored titles
  there as new beats land.
- HUD fall-through labels: "Dark" (the Hive!), "Depths Antechamber", "Effigy
  Grove", "Threshold" (`scenes/base.py` fallback). *(The `"lodge": "the Inn"`
  mismatch is FIXED 2026-07 with the Lodge expansion: `lodge` now reads
  "Arcadia Lodge".)*
- NPC object names "Clerk"/"Sheriff"/"Preacher" leak on generic paths
  (corpse examine: "Clerk. Face-down where the round put them.").
- Placeholder texts on cued interactions: "A small stash.", "A weathered
  headstone.", "A scarecrow.", "A key.", "An axe for chopping wood."
  *(2026-07 doc audit: "Some old tools." is already gone — the barrow reads
  "Digging tools left in the barrow, rusted over. The edges are still
  bright.", the designed contradiction kept.)*
- Small ones: Sable's "last night"/"tonight" against elapsed play; the robe
  "hangs... pressed and folded"; the Invitation's "Sleep where we slept" with
  no sleep verb at the school; threshold recognition + "A
  doorframe with no wall." fire at the cave mouth, 13 sight-gated rows before
  the frame is visible; lowercase hide notices; "waking the dark ." double
  space; "midwestern" casing; Garrick and hollow Vane both call the PI "son";
  two simultaneous Hetties (door + counter); duplicate candle decoration in
  Toby's house. *(Resolved and dropped from this list, re-verified 2026-07
  doc audit: the payphone beat is cut outright; Mara now says "I've never
  been this close", matching the letter; the handoff note reads "for the day
  he was ready"; the Mask desc's "So, you suspect, does the door in the
  deep" is gone; the burn-site's "All of their things." was rewritten.)*
- Missing canon clincher: §4's ledger entry promises "your own name, signed
  in tonight, already among them" — the cellar text only gestures at it and
  the desk sign-in is optional; one clause conditioned on `register_signed`
  closes the loop.
- ~~Stale dev comments that will mislead future edits.~~ **DONE (2026-07
  comment pass):** the Deep Stair live-descriptions, the `[E] cue: the
  Playscript` / testimony refs, the lodge car-keys/tab comments, the phantom
  'M' fold, the cornfield_path preacher-patrol note, and the farmhouse
  glitch-wall docstring were all corrected — along with every dangling
  citation to a deleted doc (`GAME_CHANGES §N`, `STEALTH_REWORK`,
  `STORY_AUDIT B6`, `HANDCRAFT_BACKLOG`), the dead in-game `F3` references,
  and the C-item lying comments. Accurate "was CUT" provenance notes were left intact. (The legacy scene
  keys and the `sigil_rubbing` save-migration were renamed / removed in the
  follow-up legacy-key pass, per the 2026-07 no-backward-compat ruling.)

### From the code-health audit (retired `CODE_HEALTH_AUDIT.md`)

Every high/medium/low finding from that pass was fixed on-branch; only one
awareness-only item remains: **L5 — complexity hotspots.** The largest
function bodies (`tests/flow.py main`, `scenes/brimley.build_brimley`,
`systems/render_mixin.draw_world`, `rendering/sprites_npc.draw_npc_sprite`,
`rendering/king_unfold.draw_king_unfold`) match the project's deliberate
"one cohesive beat per function" style and sit behind the test gate; listed
so growth stays a choice, not an accident.
