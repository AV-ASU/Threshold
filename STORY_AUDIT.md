# THRESHOLD — Story & Dialogue Audit (2026-07)

> Read-only audit of every player-facing text and NPC interaction against
> `NARRATIVE.md` (canon) and the CLAUDE.md hard rules. Five parallel passes
> (Brimley surface, Lodge/interiors, underground/descent/endings, systems
> text, UI/cross-cutting sweeps); the highest-severity claims were re-verified
> directly against source. No code was changed. Line numbers are as of this
> audit's commit.

## Resolutions (2026-07, same branch)

Maintainer rulings applied in the follow-up commit:

- **A1 FIXED** — the Mask temptation chains off whichever dialog channel is
  actually live (`scenes/well.py`); `descent_mask` fires again.
- **A2 WAIVED** — nonissue: the mutation/turn layer is being removed, which
  unblocks Toby's warning.
- **A3 FIXED + reworked** — Hettie now keys on `preacher_body_seen`; and per
  the ruling, Crane no longer dies in his church: the doom sends him to the
  river after his flock, the emptied church's river-mud line points there,
  and the body is found on the Brimley riverbank (evidence #4 moved;
  NARRATIVE §2/§4 updated).
- **A4 RESOLVED doc-side** — BREAK stays wordless by design; the locked line
  was removed from NARRATIVE §6 (the cage-for-Him truth belongs to the
  cult's own notes, not the ending).
- **A5 FIXED** — the notebook lead now reads "the river the boy watched."
- **B1 FIXED** — the ageless staff photo is cut (dialogue + lodge cellar
  registration removed).
- **B2 FIXED** — Crane never mentions the underground; he carries only the
  rumor the boy Toby told him (they walked off down the river one night).
- **B3 partly FIXED** — "cut the family off two years ago" deleted from the
  case intake; the Invitation note reads "Since the winter" (Sable received
  the envelope shortly after the seal; NARRATIVE §2 updated); the Deep
  Stair HUD label now reads "the Deepest Face". Remaining B3 items (ledger
  "not one ever signs out" lines, Hettie's January Mara sighting, the
  chalk_deep stair note) await rulings.
- **B4 (partly) + B5 RESOLVED by the MINE RETROFIT (2026-07 ruling: the
  whole underground reads as the cult's dig over old workings; kill every
  killer-cult relic).** `the_ossuary` is the **Old Stores** (bone vault
  purged, `bone_rack` deleted from the furniture registry, shelves of
  tagged gear; the "Clerk's hand" and "leave the body walking" lines are
  gone); `the_cells` are the diggers' **bunk cells** (captivity fiction
  cut); every underground bloodstain/gore decal removed (antechamber,
  threshing "grain mixed with old blood", shaft floor, racks, sorting,
  deepest face); the Sorting Hall's "faces of the vanished" flyer wall
  cut; HUD display names added for the whole underground. Guarded by flow
  §19b. Toby's mouth line (B4 first bullet) still awaits a ruling.

## Verdict in one paragraph

The spine is in excellent shape: the dash hard rule passes repo-wide (AST
sweep of every string literal — zero violations), "dimension" never appears,
the six-beat evidence plumbing is airtight (only `CANONICAL_EVIDENCE` names
ever reach the count), THE TALK / death cards / SPREAD / SEAL text match §6
verbatim, the timeline sweep (April 14 paper, JAN 15 calendars, "since the
new year", summer arrivals, fall for Mara) holds almost everywhere, and the
locked cast names surface correctly in every conversation. What the audit
found instead is a layer of **regressions and stale-draft survivors**: two
canon-mandated beats that can never fire, one beat that fires about a living
man, a handful of timeline lines that contradict the flow-guarded calendar,
and several texts that leak the wrong cosmology (an ageless Sable, a
perceptible claiming, a Crane who knows too much).

---

## A. Broken story beats (fix first)

**A1. The Mask's "permission to leave" beat is DEAD — the SPREAD temptation
keystone never fires.** `scenes/well.py:871` sets
`game.dialog.on_complete = lambda: game._descent_voice("descent_mask")` right
after `_evidence(game, "the_sign", ...)`. But that `_evidence` call routes
through the frameless caption channel (`ui/dialog.py:143-149`: no speaker,
narrator portrait, no on_complete → `narration.begin` and early return), so
the lambda lands on an **inactive** DialogueBox and is silently overwritten by
the next `show()`. `_descent_voice("descent_mask")` is the ONLY call site.
Lost: the on-screen "Carry this, and the town opens... You could just go."
beat AND the note "I want to. God help me, I want to." — the exact §6 canon
beat ("the instant you take it... *with this, the town will let me out*").
Regression from the 2026-07 three-channel dialog rework; `tests/flow.py`
guards the wording, never the firing. (`systems/narrative_mixin.py:367-374`
`_fold_mentioned` shows the correct active-check pattern.)

**A2. Toby's canon school warning is unreachable.** Two independent causes:
(a) the gate at `scenes/dialogue.py:437` checks only the flag
`rite_envelope_given`, so the kill-Sable-and-loot path (which deliberately
does not set the flag, `dialogue.py:1103-1123`) never triggers it — sibling
gates all check `flag or inventory.has("rite_envelope")`; (b) far worse, the
envelope only exists at 3 evidence, and `INFEST_TURN["Toby"] = 3`
(`systems/config.py:602-603`) means `_infest_locals`
(`systems/infest_mixin.py:618-634`) replaces Toby's `dialogue_fn` with
`_turned_local_dialogue` on every scene load at stage 3 — and reaching Toby
from the handoff always crosses a scene load. So the §2-mandated one-shot
*"Don't go in there, mister."* is dead code on every path. (His
`kid_playscript_noticed` beat gated on the underground-only `cult_calling` is
dead the same way.)

**A3. Hettie mourns a living man.** `scenes/dialogue.py:650-657` gates her
one-shot preacher reaction on `preacher_doomed` — which latches the instant
the PI presses Crane, while Crane still stands alive at his lectern (the body
only appears on the next church entry, `villager_houses.py:187-208`). Press
him, walk to the shop, and Hettie says "Heard about the preacher" about a man
you can walk back and talk to; it also spoils evidence #4 and violates the
file's own news-does-not-spread rule. Vane's parallel one-shot is correctly
gated on `preacher_body_seen` (`dialogue.py:838`); Hettie's should be too.
(Related, decide on purpose: Hettie turns at stage 2, so if the murder is the
player's 2nd+ beat the reaction is often lost anyway.)

**A4. The BREAK ending is missing its locked line.** `systems/game.py:2410`:
`"rite_broken": [("", 3.0 + 7.0)]`, comment "PURELY VISUAL". NARRATIVE §6
locks the presentation to *"It was never a cage for you. It was a cage for
Him."* — grep finds that line ONLY in NARRATIVE.md. Either the code regressed
or a later decision never made it back to the bible; NARRATIVE's header
forbids leaving them silently split. (Nit: the hard-cut reuses
`draw_carcosa(..., "spread")` for the BREAK blast, `ui/cutscenes.py:269`.)

**A5. The notebook's evidence lead misdirects at the dead well.**
`systems/narrative_mixin.py:239-241` (`_current_lead`, ev ≥ 1): "The register
at the Lodge, the barn she slept in, **the well the boy watched**." Toby
canonically watched the night procession go down the RIVER (§2, §5; his own
in-game account agrees), and the well was explicitly severed from the descent
and from Toby (`scenes/brimley.py:1186-1193`). The case notebook's one
navigational lead points the player at set-dressing and contradicts the
2026-07 rework.

---

## B. Canon breaks in text

**B1. The ageless Clerk — a second impossible thing.**
`scenes/dialogue.py:1169-1175`: the cellar staff photo carries "a date in the
corner from decades back" / "He has not aged a day." §1b's discipline is ONE
impossible thing; §2 makes Sable a mortal local, merely the most attuned; the
door only woke ~April 1993. An unaging Sable across decades is a second
cosmology and reads as "the people changed" (§1b: the wrongness is the place,
not the people). Recut to something deniable (same desk, same pose, a
resemblance the PI can dismiss).

**B2. Crane knows the congregation is under the ground.**
`scenes/dialogue.py:341-344`: "It kneels under the ground." / "They walked
down willing..." Only Toby witnessed where they went; Vane, the best-informed
local, correctly says "I can't tell you where it GOES." As written Crane
pre-empts Toby's witness beat with knowledge he cannot have. Either rewrite
to unambiguous pulpit metaphor or cut the literal claim.

**B3. Timeline contradictions (several against flow-guarded facts):**
- `scenes/lodge.py:281-283` — case intake: "Cut the family off **two years
  ago**." Locked chain: Mara north fall 1993, "stopped calling home by the
  new year" (the systems-side note at `narrative_mixin.py:286` is correct);
  two years ago also predates the door waking.
- `scenes/dialogue.py:892` — "Sable kept an envelope under the register.
  **A year at least.**" The congregation left it at the fall-1993 procession:
  ~6 months. "A year" is the locked token for the dream and the ledger
  cutoff; don't blur it.
- `scenes/dialogue.py:129-130` and `1022-1024` (+ `lodge.py:840` repeat
  examine) — "The register never shows a checkout. Not one, in years of
  guests." / "Not one ever signs out." Canon (§4, flow-guarded): checkouts
  ran until a year back. The actual Ledger evidence text
  (`lodge.py:852-855`) is correct; these adjacent lines contradict it.
- `scenes/dialogue.py:674-677` — Hettie saw Mara shopping "past the new
  year": Mara went below with the fall procession (§1 timeline; Toby's
  witness agrees). Note: canon itself carries a small seam ("stops calling
  home" listed under mid-January) — worth settling doc-side too.
- `systems/game.py:2334-2336` — the `chalk_deep` NOTE: "The stair shut the
  way behind me when it opened." The Deep Stair is CUT (§9: "there is no
  stair"); the PI just fell through a blasted floor. The on-screen half of
  the beat is fine; the note needs the fall.
- `scenes/base.py:992` — HUD label `"works_deepstair": "the Deep Stair"`.
  The scene KEY must stay; the always-on display name should be "the
  Deepest Face" (§9 Room 7).

**B4. Perceptible-claiming leaks (the exact class the 2026 pass scrubbed):**
- `scenes/dialogue.py:519-521` — Toby: "I tried to lie yesterday. My mouth
  wouldn't." A felt, physical grip; §1b says claiming is never felt. §8
  blessed only "I keep biting my tongue. To check."
- `scenes/dialogue.py:494-495` — "My mom hums a song that doesn't stop. She
  doesn't know she's doing it." Borderline; same leak class, softer.
- `scenes/depths.py:503-504` — Ossuary: "before it learned to leave the body
  walking." The strongest possession-flavored line in the game; defensible
  as the PI's wrong inference, worth a canon look.
- `scenes/well.py:1104-1132` — the Holding Cells' environmental story ("where
  the claimed were kept the first night", child-height marks) implies
  abduction; canon is emphatic nobody was taken.

**B5. The Ossuary labels are "in the Clerk's hand"** (`scenes/depths.py:502`).
Sable never went below — that is his whole §2 arc ("Somebody has to keep the
desk"). Attribute the labels to the congregation.

**B6. Converted-local narration contradicts the renderer.**
`systems/infest_mixin.py:44-45, 61-62` — "The face is Mrs. Calder's. The
voice underneath it is not." But `_convert_local` sets
`sprite_kind = "cultist"` and drops the portrait: on screen she IS a hooded
cultist. §4b gives only the turned RESISTERS their exact bodies, so the text
is what's wrong — acknowledge the robe, or keep her sprite.

**B7. NARRATIVE.md internal fixes needed (doc-side):** §2 blockquote still
says "The Lodge is newcomer-run" (contradicts local-Sable, which the game
text follows); §4b lists Garrick as both convert and turned (code says
turned); the populated Depths (patrols, worn procession route, the Hive one
room from the frame) sit on §5's "never reached the frame" seam — the code
faithfully implements canon's own diagram, but `depths.py:275-287` ("many
more times than once") asserts repeated traffic through rooms the dig
supposedly never broke into.

---

## C. Interaction-logic bugs

- **C1.** The lure-collision caption (`scenes/well.py:627-634`, the one place
  the engineered-chain dread surfaces) runs as a non-modal caption during the
  calling-out; Mara's walk-home rite-holder line (`well.py:845-849`) replaces
  it mid-read on essentially every playthrough (`ui/narration.py:44-50` drops
  unread text).
- **C2.** `_mara_stage` is never cleared in `_reset_run_state`
  (`systems/game.py:430-553`): a run ending mid-staging makes the next run's
  first `works_sign` entry silently eat the calling-out for that visit.
- **C3.** The grove's evidence-meter content is dead: `_grove_enter`'s
  "thread of gold" line and the "not finished forming" refusal
  (`scenes/hidden_folds.py:246-252, 187-190`) gate on ev < 3, but the grove
  is only reachable at 3+; the "clarifies as evidence mounts" fiction (§5)
  now has no player-visible expression.
- **C4.** `scenes/lodge_yard.py:269-273` — the cellar-key narration points at
  "a doorframe... against the boards"; no doorframe exists in the scene (the
  'M' arrival fold it referenced was cut).
- **C5.** The church LOGIN terminal (`scenes/villager_houses.py:14-59`) is
  permanently dead (`user_code` is never set anywhere) and tonally alien
  (ARG leftovers in a 1994 parsonage). Cut or reskin to paper records.
- **C6.** Dead/contradicted machinery in the lodge: `innkeeper_confronted`
  is never set (the blocking-Clerk branch is unreachable,
  `lodge.py:488-537`); comments say the Clerk's bedroom is "locked at first"
  but exit "1" has no gate — the pressed-robe tell is open from minute one
  with no reaction from the watching Sable (`lodge.py:605-615`). Decide:
  lock it or fix the comments.
- **C7.** Flash-mode caption leak: "You dream of a doorway."
  (`ui/cutscenes.py:246-252`) renders during the journal's 0.55s MEMORY
  flash. The flash is a waking memory; present-tense "you dream" is the
  recurrence flavor the flow-guard polices in the note.
- **C8.** Legacy hp-death respawn text survives (`systems/game.py:2857-2876`:
  "You wake on the town square", `world_emptied`); if reachable it
  contradicts the death model (CAPTURED/CUSTODY/Carcosa end the run).
- **C9.** Old Pell is `fold=True` but never describes the fold
  (`scenes/brimley.py:746-764`), so the PI's auto-filed note quotes him
  giving Royce's roads account he never gave
  (`narrative_mixin.py:343-346`).
- **C10.** Elapsed-time claims that break under fast play: Garrick's
  "Nothing out of him for days now" fires on `preacher_doomed`
  (`brimley.py:838-846`, can be minutes old); Vane's "I went over Tuesday
  morning" (`dialogue.py:845`) can precede any possible visit.
- **C11.** Toby's cold-open "You're looking for the lady from the lodge."
  (`dialogue.py:414`) assumes the case before the PI has stated it — against
  the file's own news-does-not-spread rule. Gate on any intro/photo flag or
  reword to what a kid could infer.
- **C12.** The hunting-sheriff intro replays on every stage-3 office entry
  (`infest_mixin.py:513-515`); and the line "I'm supposed to tell you to
  leave, son. I can't say it anymore." reports the failure instead of
  performing the unfinished line (§4b: "says the line he can no longer
  finish").
- **C13.** The PI's fold question ("I walked the road out of town... It set
  me back down past this window", `dialogue.py:1059-1064`) gates only on
  being TOLD about the fold, not on having crossed one — the game can put a
  lie in his mouth.
- **C14.** Silent/dead interact cues: the dresser E-cue with no handler
  (`lodge.py:638` vs `671-684`); Toby's closet drawing announced as
  examinable but no interactable registered (`interiors.py:453-458`); the
  altar's [E] cue after the Mask is taken (`well.py:877-878`); the barn and
  farmhouse sealed hatches play a sound with no "nailed shut from below"
  line (`interiors.py:369`, `villager_houses.py:402-409`).
- **C15.** Flagged tension, intentional per in-file comment: SEAL is a bare
  walk-through at the frame (no confirm) while the blast and grove rite are
  deliberately two-press "never a lone-press point-of-no-return"
  (`depths.py:737-758`). Confirm on purpose.
- **C16.** Missable-by-design signposts worth confirming:
  `_ready_for_the_desk` needs `sable_greeted` at exactly 3;
  `_the_third_thread` needs `crane_greeted` at exactly 2 — players who never
  met them lose the act-break pointers forever.

---

## D. Voice / polish

- Narrator "vanished into the corn" (`villager_houses.py:222-224`) adopts
  Crane's drift-away impression as fact; canon is one night procession, and
  §2 corrects the image for Mara ("not into the corn"). Crane's greet
  ("more every season", `dialogue.py:308`) and Sable's "no end of those this
  past year... They come" (`dialogue.py:942`) keep arrivals in the habitual
  present; arrivals ended before the seal.
- Old Pell: "Cold came in early this year. And it never lifted."
  (`brimley.py:747-750`) — should be last year, and "never lifted" brushes
  weather-stasis against the ice-going-out present.
- Revolver description leaks mechanics: "(3+ evidence)"
  (`systems/items.py:18-22`); also "fires it in the way you're facing."
- Descent interior voice wobbles POV (first person notes vs second person
  on-screen beats, `game.py:2246-2305`).
- Notebook headers from slugs (`ui/notebook_ui.py:19-23`): "Maras Room",
  "Chalk Deep", "Descent Mask", "Showed The Clerk" — dev slugs where the
  case file should read like the PI typed it.
- HUD fall-through labels: "Dark" (the Hive!), "Depths Antechamber",
  "Effigy Grove", "Threshold" (`scenes/base.py:1017` fallback), plus
  `"lodge": "the Inn"` (`base.py:974`) against "Arcadia Lodge" everywhere
  else.
- NPC object names "Clerk"/"Sheriff"/"Preacher" (`lodge.py:509`,
  `villager_houses.py:111, 268`) leak on generic paths (corpse examine:
  "Clerk. Face-down where the round put them.").
- Placeholder texts on cued interactions: "Some old tools."
  (`brimley.py:1219` — the beat's designed contradiction is lost), "A small
  stash.", "A weathered headstone.", "A scarecrow."
  (`threshold_extras.py:17, 468, 1189`), "A key.", "An axe for chopping
  wood." (`items.py:35, 137`).
- Small ones: payphone "your own voice, already mid-sentence"
  (`brimley.py:1228` — the one temporal-uncanny string; make it spatial);
  Sable's "last night"/"tonight" against elapsed play (`dialogue.py:909,
  1009`); the robe "hangs... pressed and folded" (`lodge.py:681`); the
  Invitation's "Sleep where we slept" with no sleep verb at the school
  (`items.py:148`); Mara's "I have never been this close" vs the letter's
  locked "I've never been this close" (`well.py:649` — make the expansion a
  choice or match it); the handoff's "the day they were ready" (canon: HE
  was ready, `dialogue.py:1094`); burn-site "All of their things." vs the
  Sorting Hall cataloguing everything (`interiors.py:141`); Mask desc "So,
  you suspect, does the door in the deep" plants "the door can open"
  (`items.py:49-53`); threshold recognition + "A doorframe with no wall."
  fire at the cave mouth, 13 sight-gated rows before the frame is visible
  (`depths.py:673-692`); lowercase hide notices (`game.py:1817`); "waking
  the dark ." (`render_mixin.py:100`); "midwestern" casing
  (`threat_mixin.py:1040`); Garrick and hollow Vane both call the PI "son";
  two simultaneous Hetties (door + counter); duplicate candle decoration in
  Toby's house (`interiors.py:413, 425`).
- Missing canon clincher: §4's ledger entry promises "your own name, signed
  in tonight, already among them" — the cellar text only gestures at it and
  the desk sign-in is optional; one clause conditioned on `register_signed`
  closes the loop.
- Stale comments that will mislead future edits (dev-only): Deep Stair
  references in `well.py:4-5, 53-54`, `hidden_folds.py:224-225`,
  `depths.py:1-3`; "[E] cue: the Playscript" (`well.py:552`); the lodge
  car-keys/tab comments; the phantom 'M' fold (`lodge_yard.py:117-121`);
  cornfield_path's preacher-patrol note; the farmhouse glitch-wall
  docstring.

## E. Known-open (tracked, not new)

- Watcher bind/dispel notices still read as a bindable side-cult curse
  ("Something has been bound to you", "The curse lifts")
  (`threat_mixin.py:783-789, 901-903`) — NARRATIVE §8 lists the re-point as
  open; the trigger half is already re-pointed.
- Vane's blind-cultist thread is unauthored (TODO #2a).
- Chorus lacks the shared intro/photo openers (TODO #1).
- Deadpan narration pass (TODO #15) covers several of the voice items above.

## F. What was verified clean (so it isn't re-audited)

Dash rule repo-wide; "dimension"/day-night/time-loop/cannibalism/Mistlands/
Village Kid/Innkeeper/playscript/rubbing: zero player-facing hits; evidence
vs notes routing airtight; THE TALK verbatim; death cards per §6; SPREAD and
SEAL scripts locked and dash-free; dream note canon-exact; Royce, Mrs.
Calder, Garrick's road warning, Toby's witness account, Vane's knowledge
boundary, Hettie's paper trade and shelves: all canon-exact; Sable's
compulsion voice, the deniable car split (Sable deflects, Vane carries the
plain truth), the desk lead pointing down without Sable pointing at the
cellar; school rite strictly incense-before-chalk with correct failure
lines; the three testimony fragments verbatim in the congregation's own
voice, gating nothing; the Cistern/tithe recuts hold; the calling-out stages
once with clean flag hygiene (`hive_seen` at the Sign Chamber, case-board
rewrite reading it); the blast requires powder + Mask and consumes only the
powder; the keyed return pane and `descent_sealed` SPREAD lock; the
Threshold walk-through text ("You are standing in the same room."); the Hive
nameless; wade scenes match config; nobody in Brimley knows Walter Blaine.
