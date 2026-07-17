# THRESHOLD — Dialogue & Narrator Bible

> The fifth canon doc, and the source of truth for **every word the player
> reads**: spoken NPC/PI lines and narrator/world boxes alike. `NARRATIVE.md`
> locks the FACTS the fiction asserts; this file locks the TEXT that delivers
> them. Organized two ways at once: **WHO SAYS WHAT** (Part A, by speaker)
> and **WHAT CAUSES WHAT** (Part B, by trigger).

---

## THE CONTRACT — the code and this doc are ONE

**Read this first, and never break it.**

Every player-facing spoken line and narrator box exists in **two places**:
the code that ships it, and this document. They are **the same text in two
homes.** Therefore:

- **Any change to one is a change to the other, in the SAME commit.** Edit a
  line in `scenes/dialogue.py`, edit it here. Add a beat here first as a
  draft, land it in the code in the same breath. There is no such thing as
  "update the doc later" for dialogue. If you touched a string the player
  reads, this file is part of your diff.
- **A disagreement between the two is a bug (rot), not a nuance.** If the code
  says one thing and this doc says another, someone changed one and not the
  other. Reconcile immediately; treat the drift the way you would treat a
  failing test.
- **The code is what ships; this doc is the review surface and the index.**
  When you can only look at one to answer a question, look at the code. But
  the doc is how a human reads the whole voice at once, so it must stay
  faithful or it is worse than nothing.
- **`tests/flow.py` canon-guards win over both.** Where a guard asserts an
  exact wording (the dream note's "a year", the no-dashes rule, the ending
  captions), the guard is the tie-breaker. Change the line, change the guard,
  change this doc, all together.

If you are ever unsure whether a text edit "needs" a doc edit: it does.

---

## HOW THIS DOC IS ORGANIZED

- **Part A — WHO SAYS WHAT.** Every speaking character, in one place: their
  voice, where their dialogue lives in code, and their beats verbatim
  (greet, the ask-verb exchanges, the volunteered one-shots).
- **Part B — WHAT CAUSES WHAT.** Every narrator / world box by the event
  that fires it: evidence pickups, the descent-voice track, the fold notes,
  the dream, the death cards, prop examines.

**Verbatim convention.** Lines are quoted exactly as the code holds them.
`[c=dim]...[/c]` marks **gray** text (a quiet aside, physical business, the
PI's muttered interior); plain text is **white** (spoken emphasis, the line
that carries the beat). A beat is tagged **(npc)** / **(pi)** / **(narrator)**
/ **(stage)** for the parenthetical business.

**Coverage.** Part A is complete and verbatim for the whole speaking cast.
Part B transcribes the significant boxes verbatim and **indexes** the routine
prop-examine captions by location; those are transcribed as the narrator
sweep (`TODO.md` #13b/#15, Wave 6) reaches them. Until a routine box is
transcribed here, the code is authoritative for its exact words, but the
contract still binds: touch one, update the other.

---

## VOICE RULES (the bar every line clears)

Consolidated from the canon. A new or edited line must pass all of these.

1. **No dashes in player-facing text** (HARD RULE, flow-guarded). No em-dash
   (—), en-dash (–), or double-hyphen (`--`) as punctuation in anything the
   player reads. Rewrite with a period, comma, colon, or a new sentence.
2. **Trust the player. State the fact and stop.** A line names the thing and
   leaves the conclusion, the feeling, and the connection to the player to
   reach *between* the beats. It never spells out the inference it was built
   to earn ("...one of them", "he's still working it", "this is what naming
   them costs"). The player is smart; the dread is theirs to assemble.
3. **Cosmology only as sensation** (NARRATIVE §2). No line STATES the model
   as fact: not a higher dimension, not "the door answers your deepest want"
   delivered as clean exposition, not "what do you want most", not the King
   feeding on attention, not the lure chain (King → Mara → Walter → PI). A
   cultist may express BELIEF in its own voice; it may not confirm the
   mechanism. Vane holds exactly ONE fragment of the *how* (the blind
   cultist's offer) and it stays a hard-won, half-understood piece he
   witnessed, never a lecture.
4. **No mechanics in the fiction.** No line names a game rule, a verb, an
   input, or an evidence threshold ("press again", "kill them quiet", "3
   pieces of evidence", "he's hunting you now"). State the fiction; never the
   system.
5. **Knowledge the speaker can have.** No PI or NPC line assumes a fact the
   player has not earned, and no one states what they could not know.
6. **Gray is not a dumping ground.** `[c=dim]` is for a genuine aside, quiet
   delivery, or physical business. It is NOT where over-written interior
   narration goes to hide. If a gray line is really the answer to the
   question, or the emotional core of the beat, it should be **white**. If a
   gray line only exists to explain the conclusion, it should be **cut**, not
   dimmed.
7. **Deadpan, objective, a little curt** (the settled narrator register).
   Kill aphorism and poetry where it creeps in. A routine action (a key, a
   body, a prop) is a terse line or nothing; a beat that wants a close-up
   earns a mini-cutscene or stays short.
8. **The trailing "So." is a tic — spend it rarely.** A line that ends on a
   lone "So." is the PI declining to say the rest out loud; it lands once.
   Used on every reflection it becomes its own wallpaper (a play-note
   grievance). Vary the deadpan sign-off: a hard stop, a different beat, or
   nothing at all. At most a couple across the whole game.
9. **Markup never leaks.** `[c=...]`, `[/c]`, and every style token is
   stripped on every render path (notebook, scribble toast, caption). Never
   printed literally.

---

# PART A — WHO SAYS WHAT

The whole speaking cast. Character facts live in `NARRATIVE.md §4`; this is
the words.

## The shared openers — the PI initiates
Every principal's menu leads with the same two PI lines (`_opener_exchanges`
in `scenes/dialogue.py`; `_INTRO_Q` / `_PHOTO_Q`). The PI introduces himself
and names the case cold: news does not spread in a sealed town, so nobody
knows who he is or what he wants until he says it. The NPC's per-character
answers follow each and are quoted under that character below ("Opener
intro:" / "Opener photo:").
- **Intro** (menu label "I'm a private investigator."):
  - (pi) "I'm a private investigator, out of Minneapolis. I was hired to find a woman named Mara Blaine. She was last heard from headed to Brimley."
- **Photo** (menu label "Have you seen this woman?"):
  - (pi) "I want you to look at a photograph. Have you seen this woman?"
  - (pi) "(You hold her photograph out.)"

## Mr. Sable — the Lodge clerk
- **Voice:** `blip_low`. **Code:** `scenes/dialogue.py` `SABLE_CONVO`,
  `sable_on_death`, `clerk_dialogue`. **Who:** local, the most-attuned of
  them, the lucky one (NARRATIVE §4). Genteel host, funereal undertow, never
  gives the girl up; points suspicion at the "unfriendly" old families (the
  trap). He checked the PI in the night before, so every exchange resumes an
  acquaintance. Framing carries the PI four-tier weather (`_pi_framing`).
- **Presentation (2026-07):** `clerk_dialogue` opens `SABLE_CONVO` inside a
  frozen close-up **tableau** (`_open_sable_tableau`, `tableau=True`), not as
  float-speech over the desk. The world holds; the spoken beats render as the
  tableau caption and the menu as its option panel. The words are identical
  either way (below); only the presentation changed. See Part B "The close-up
  examine tableaux."
- **Greet** (`sable_greeted`):
  - (npc) "Up early. You came in late off the north road. I put you down in the book as staying a while."
- **Exchange `mara`** — "I'm looking for someone." / "I'm looking for a woman named Mara Blaine. Is that a name you know, Mr. Sable?"
  - (npc) "Mara. No, I cannot say I know the name. But I have had the pleasure of hosting a great many guests these past months. You are welcome to look over the register any time you like."
  - (npc) "You will mean one of the new folk, I expect. We had no end of those this past year. They came like they had heard something worth the drive."
  - (npc) "And I was glad of every one. This town was drying up before they came. I had every room full. You should have seen this house with every window lit."
  - (pi) "And the rest of Brimley feels the same?"
  - (npc) "Ah. There you have it. Not everyone has been so warm. Some of the old families have gone as cold as our root cellar about the newcomers."
  - (npc) "I would mind who you take your questions to, friend. Not everyone here wishes a stranger well. I do. You remember that."
  - (ask) "Show him her photograph?"
    - **Slide the photo across the desk** → (pi) "(You lay her photo on the register.)" / (npc) "(He looks at it a good while, then hands it back.) No. A pretty thing, but no. I could not put a name or a room to her. So many faces came through that door." *(sets `sable_showed_photo`; confirms only that he does not know her)*
    - **Keep it in your coat** → (pi) "(You leave it where it is.)" / (npc) "No matter. Ask around, if you must. Start with the friendly ones. There are fewer of those than you would think."
- **Exchange `cellar`** — "What's in your cellar?" / "What do you keep down in that cellar of yours? Mind if I take a look?" *(sets `sable_cellar_permission`)*
  - (npc) "The cellar? Storage, mostly. Old registers, a broken chair or two. Nothing down there worth hiding from a guest."
  - (npc, only if the PI does not already have the cellar key) "Shoot. I seem to have misplaced the key. If you find it, you are welcome to take a look."
- **Exchange `car`** — "Is there a mechanic in town?" / "My car won't start. Turns over and won't catch. Is there anyone in town who could take a look at it?" *(sets `sable_car_asked`; the closing hospitality plants the road warning in plain sight, and `the_fold` quotes it back)*
  - (npc) "A mechanic? No, nothing like that in Brimley now, and it would do you no good if there were."
  - (npc) "The car is not broken, friend."
  - (pi) "What do you mean, not broken? It turns over and dies at the step."
  - (npc) "Only that I have seen it before. Now and then a guest's car went the same way, and never once have I seen one put right."
  - (npc) "A man quits asking why, after a time. I am long past it, and it is no trouble to me. Needn't be to you either."
  - (npc) "You have a good bed and a standing welcome. The roads are not going anywhere. Stay as long as you need."
- **Exchange `checkouts`** (avail: read the Ledger) — "The checkouts stop a year back." / "I read your old registers. Guests used to settle up and leave. The dates stop a year back. Since then everyone signs in and nobody signs out."
  - (npc) "(The pleasant look does not shift.) Do they not? Fancy that. I never was much of a hand with the paperwork."
  - (npc) "They will not have gone far. Nobody does. It is a restful town, friend. People stay. It is the one thing I can promise a guest."
- **Exchange `the_fold`** (avail: heard the fold named AND walked it; the reply branches on `sable_car_asked`) — "The road out brought me back." / "I walked the road out of town. Followed it two hours, due west. It set me back down past this window."
  - **if he said it** (the car exchange planted the warning): (npc) "I told you the roads were not going anywhere. You heard a man being hospitable. I meant it plainly."
  - **if he never did** (the mechanic was never asked after): (npc) "So you walked it. The roads are not going anywhere, friend. They never were."
  - (npc) "There is no call to be cross about it. You are safe here. Safer than out there."
- **Exchange `the_way_down`** (avail: 3 evidence, no envelope yet) — "You've been holding something for me." / "You've kept something back from me since I walked in. I'll take it now."
  - (npc) "You are past pretending to be a guest now, I think. All right."
  - (npc) "(He lays a long envelope on the desk. Wax seal, the Sign pressed into it. He handles it like a room key.)"
  - (npc) "My guests left it at the desk when they went below. It was meant for me. They wanted me to come down after them, and they meant it kindly."
  - (npc) "But I never wanted what they went to find. I wanted a full house, friend, and I had one. Take it. Somebody has to keep the desk."

## Sheriff Hollis Vane — the last holdout
- **Voice:** `blip_gruff`. **Code:** `scenes/dialogue.py` `VANE_CONVO`,
  `sheriff_dialogue`, `_vane_*` helpers. **Who:** local, claimed but never
  attuned; the town's one real investigator, chasing the *how*. Hopeful but
  mistrusting. His fate is player-driven (the despair/hope ledger, DESIGN.md
  §2). **Mood prompt** (`_vane_prompt`, reads the ledger, never a number):
  despair ≥ 2 → "Vane is looking at the window, not at you. It takes him a
  moment to come back."; hope ≤ -1 → "Vane hooks a chair out with his boot
  and nods at it. As close to a welcome as this office gets."; else → "Vane
  waits you out, thumbs in his belt."
- **Presentation (2026-07):** `sheriff_dialogue` opens `VANE_CONVO` inside a
  frozen close-up **tableau** (`_open_vane_tableau`, `tableau=True`): his
  office in cold window light, and his POSE reads the same ledger the mood
  prompt does (neutral squares up; despair turns his head to the window;
  hope leans him in, a forearm on the desk). The preacher one-shot still
  volunteers itself as a plain beat first. The words are identical either
  way (below). See Part B "The close-up examine tableaux."
- **Greet** (`vane_greeted`):
  - (npc) "Sheriff Vane. That's the whole welcome I've got left."
  - (npc) "Nobody comes up that north road anymore. Then you. So you'll forgive me if I look at you a while before I decide anything."
- **Opener intro:**
  - (npc) "A detective. Hired and paid, all the way up here."
  - (npc) "The ones who came before you walked in friendly and smiling too. Every last one of them. You understand my position."
  - (pi) "If I were one of them, would I be standing in the law's office announcing myself?"
  - (npc) "No. No, they never had questions. That's the one thing you've got going for you."
  - (npc) "I'd head home if I were you. I'm supposed to say that."
- **Opener photo:**
  - (npc) "(He takes it to the window light and works it corner to corner, a lawman's look.)"
  - (npc) "The new folk came in numbers and they kept to their own. She'd have been one of them."
  - (npc) "They filled the school, the barn, the lodge. Then one night those rooms were empty, all at once. Wherever your girl is, that's the direction."
- **Exchange `car`** — "My car died the night I drove in." (files the fold note, no chained reflection)
  - (npc) "Won't start. Won't ever. Nothing with an engine leaves Brimley."
  - (pi) "Engines don't all quit at once. Somebody got to it."
  - (npc) "Nobody touched your car. I know how that sounds. I've watched men tear three trucks down to the block hunting the part that failed. There is no part."
  - (npc) "[c=dim]It's the town.[/c]"
  - (pi) "[c=dim]He said it flat.[/c]"
- **Exchange `town`** — "What happened to this town?" (dynamic beats, `_vane_town_beats`: Vane's lived arc, then a reaction that branches on whether the PI already knows the seal)
  - (npc) "Brimley was dying before any of this. Half the town gone south for work, storefronts boarded up. Some weeks the phone never rang once."
  - (npc) "Then last summer the strangers started coming up the north road, and they didn't stop. More than we had beds for. Polite, every one. Kept to their own. Not one could tell me where they'd driven in from, or why they'd want a dead town like this."
  - (npc) "I kept waiting on the trouble strangers bring. It never came. Something quieter did. The trucks stopped running. The mail stopped. And the road out stopped taking anybody anywhere."
  - (npc) "You need to get out of here. We all do. No one has been able to leave in months."
  - **first time** (has not learned the seal yet; marks the fold heard): (pi) "Wait. What are you saying, Sheriff? No one has left?" / (npc) "Not a soul, not since the winter. They try. I tried, more times than I'll admit to a stranger. Every road out of Brimley turns you around and sets you back at that well." / (npc) "You'll learn that yourself soon enough. Everybody does."
  - **already knows** (heard the roads loop / walked one / re-asking): (pi) "Then you tell me how, Sheriff. Every road out, every engine, a whole town that can't leave. It's not right. How?" / (npc) "You think I haven't stood right where you're standing and asked that, every night for a year? I don't have a how for you. Just this badge, and a list of folks I can't help."
- **Exchange `share_journal`** (avail: intro asked + journal found; hope + trust) — "I found Mara's journal."
  - (npc) "Say the first part again. The same door. All of them."
  - (pi) "All of them. And she didn't write like a prisoner. She wrote like a woman nearly home."
  - (npc) "A year I've been asking this town for one honest page. You walk in off a dead road and hand me her whole hand."
  - (npc) "That's the first real piece of work anybody has brought through that door since it all shut. I won't forget you did."
  - (pi) "[c=dim]Something in him let go a notch.[/c]"
- **Exchange `share_ledger`** (avail: intro asked + Ledger read) — "The lodge registers are wrong."
  - (npc) "Now that is evidence. Paper with dates on it. God, I have missed paper with dates on it."
  - (npc) "I never got past that desk. Sable smiles, the whole building goes polite, and you walk out without whatever you came in for."
  - (npc) "Keep pulling threads like that and this town might finally owe somebody the truth. Watch who sees you pull them."
  - (pi) "[c=dim]He wrote it down.[/c]"
- **Exchange `paper`** (avail: intro asked + carries newspaper) — "I brought yesterday's newspaper." (despair lever, +VANE_PAPER_DESPAIR)
  - (npc) "(He takes it in both hands, careful, like something that might go out.)"
  - (npc) "(He spreads it flat on the desk and stands over the front page a long time.)"
  - (npc) "Kurt Cobain. Huh."
  - (npc) "I drove down to the Cities to see him play, before all this. Stood at the back. Best night I had that whole year."
  - (pi) "Sheriff?"
  - (npc) "He had every road out of every town, that man. The whole world open. And he shut the door on it from the inside."
  - (npc) "So it isn't just here. That's what a front page is for, I guess. Telling you the weather's the same all over."
  - (npc) "Thank you for the paper, son. Go on home now. (He doesn't look up from the page again.)"
  - (pi) "[c=dim]I meant it as a kindness. Walking out, I couldn't remember why I thought it would land as one.[/c]"
- **Exchange `how`** (avail: intro asked + at least one share, the trust gate) — "How were the newcomers gathered?" — his one card, the honest *how* fragment (NARRATIVE §4).
  - (npc) "I asked that question every night for a year. What I've got is one conversation. I'll spend it on you."
  - (npc) "After the rooms emptied, one of them came back up the road to this office. Blind. Born blind, he said. Walked in without a stick and sat down square in that chair."
  - (npc) "No name. I asked twice. He sat there lit up like a man warming his hands at a stove. Said the dream had promised him his eyes. Said when the work is finished he'll open them, and they'll work."
  - (pi) "He wasn't there to confess anything. He was there to fetch you."
  - (npc) "He made the offer. Told me to name the thing I want most in this world, and come with him, and it would be waiting. I put him out. He thanked me for my time and he left smiling."
  - (npc) "You don't talk a hundred strangers onto one road. They weren't tricked. Every one of them was going toward something, and glad of it."
  - (npc) "What it was, who was holding it out, I never got closer than that chair. That's the piece that keeps my lights on at night."
- **Exchange `cache`** (avail: intro asked + at least one share, the trust gate; once; sets `vane_gave_cache` and drops the office ammo) — "Am I on my own out there?" / "If this goes the way it's been going, I'll be out there alone. Is there anything you can put in my hand, Sheriff?"
  - (npc) "Protection. That's a thing this office used to hand out."
  - (npc) "I've got no deputies, no cell that holds, and a law nobody up here answers to anymore. What I've got is a cabinet in the back. Shells, and a spare piece I kept oiled for no reason I could name."
  - (npc) "Take what you need. It won't help you against what took this town. But it'll make you feel like it might, and some nights that's the whole of the job."
  - (pi) "[c=dim]He unlocks the cabinet and steps back. The last thing the law here has to give.[/c]"
- **On leave** (`vane_on_leave`, once):
  - (npc) "Hey. If you do find her, don't bring her by the office. There's no report worth filing anymore."
  - (npc) "Just get her out. If you find a way that works, that is. And then you come tell me what it was."
- **One-shot: the preacher** (`sheriff_dialogue`, avail: body found + met him; +VANE_DESPAIR_ACT):
  - "They killed the preacher."
  - "He named them from his pulpit. Then he walked down to the water to fetch his flock home. They left him on the bank for us to find."
  - "I didn't write a report. Who would I send it to."
  - "[c=dim]He doesn't say the Reverend's name. Nobody in town has.[/c]"

## Hettie — the store, quiet resister
- **Voice:** `blip_high`. **Code:** `scenes/dialogue.py` `HETTIE_CONVO`,
  `hettie_dialogue`, `grant_receipt`. **Who:** local, quiet resister; her
  value is what she risks saying. Warm handover of Mara's store tab.
- **Presentation (2026-07):** `hettie_dialogue` opens `HETTIE_CONVO` inside a
  frozen close-up **tableau** (`_open_hettie_tableau`, `tableau=True`): the
  gutted shop behind her counter, her one kept bulb burning over it, and her
  idle glancing at the door (the framing line made pose). The one-shots (the
  preacher, the Mara memory, the trade) still volunteer as plain beats
  first. The words are identical either way (below). See Part B "The
  close-up examine tableaux."
- **Greet** (`hettie_greeted`):
  - (npc) "We're open. Lord knows why, but we're open."
  - (npc) "There's nothing on the shelves worth your money. If it's talk you want, keep your voice down. In here."
- **Opener intro:**
  - (npc) "A missing girl. And you came HERE after her."
  - (npc) "[c=dim]Can't help you. Not the way you want. Shelves are bare. Till's been empty since the new year. Nobody buys. Nobody sells.[/c]"
  - (npc) "I'll say this much. Then nothing. Don't go where they tell you it's safe. I've got a family. Look around."
- **Opener photo** (avail: memory not yet volunteered; sets `hettie_saw_photo`):
  - (npc) "(She looks. Not long. Long enough.)"
  - (npc) "Faces come through this shop. I stopped keeping them."
- **Exchange `safe`** (avail: intro asked) — "Who is 'they'?"
  - (npc) "You haven't gone quiet. Like the others. Good. Then listen once."
  - (npc) "Don't trust the easy ones. The first to make peace, they went the soonest."
  - (npc) "That's the whole answer you're getting to that."
- **Exchange `others`** (avail: saw photo or volunteered memory) — "Others came asking before me."
  - (npc) "I sold to the girl too. And the ones before her."
  - (npc) "None of them came back to buy again. You're the first."
- **Exchange `way_out`** (avail: heard the fold) — "Is there a way out?"
  - (npc) "(She glances at the door before she speaks.)"
  - (npc) "If you find the way out. The real one. You don't owe this town a goodbye. Just go."
- **One-shot: the preacher** (avail: body found + met her):
  - "Heard about the preacher. I won't be saying his prayers in here. Don't ask me to."
- **One-shot: the Mara memory** (avail: shown the photo; hands over the tab, `grant_receipt`):
  - "Your girl. I'll tell you the one thing I know that's worth the telling."
  - "She used to come in here. Matches, canned milk. Counted her change twice, every time, like it mattered. Sad around the eyes, and polite with it."
  - "Then one day past the new year she set her basket down half filled and walked out smiling. Left the basket on the counter. I never saw her again."
  - "[c=dim]It was the smiling I minded.[/c]"
  - (if tab not yet lifted) "[c=dim]She works a curled slip off the spike by the till and sets it on the counter, turned toward you. Her tab for the girl. Matches, canned milk, week on week.[/c]"
- **One-shot: the newspaper trade** (avail: met her, carries newspaper):
  - "[c=dim]Her eyes stop on the newspaper folded in your coat pocket. She goes very still.[/c]"
  - "What's the date on that. The date."
  - "[c=dim]You show her. April 14. Yesterday. You bought it before the drive north.[/c]"
  - "Yesterday's. We haven't had a paper through here since the trucks stopped."
  - "Leave it on the counter and take what's under it. The till's been empty since the new year. The shelf under it hasn't."
  - "[c=dim]One load of cartridges across the counter. She's already reading yesterday's news like a letter from someone she'd given up on.[/c]"
- **On leave** (`hettie_on_leave`, once):
  - (npc) "(She shakes her head, just slightly. She has said too much already.)"

## Rev. Asa Crane — the preacher
- **Voice:** `blip_low`. **Code:** `scenes/dialogue.py` `CRANE_CONVO`,
  `preacher_dialogue`, `_crane_provoked`. **Who:** local, innocent dissenter;
  names the cult from his pulpit. His doom is the player's choice (press or
  hold). **Framing prompt** (`_crane_prompt`, reads the fork, never the
  system): at rest → "Crane waits, hands folded over the lectern."; once
  the press has latched (`preacher_doomed`) → "Crane stands square at the
  lectern, done waiting."
- **Presentation (2026-07):** `preacher_dialogue` opens `CRANE_CONVO` inside
  a frozen close-up **tableau** (`_open_crane_tableau`, `tableau=True`): the
  chancel behind his lectern in candled dusk, and his HANDS reading the fork
  the way the framing line does (folded over the lectern, or gripping its
  corners once pressed). The bell one-shot still volunteers as a plain beat
  first. The words are identical either way (below). See Part B "The
  close-up examine tableaux."
- **Greet** (`crane_greeted`):
  - (npc) "Another new face. Strangers off the highway were all that came to Brimley this past year, more every season. And not one of them left."
- **Opener intro:**
  - (npc) "I never trusted it. They arrived too easy, like something held the door. Then they went quiet, drifted out to the corn, and they didn't come back."
  - (npc) "A young woman came through in the fall. Bright thing, full of questions, like you. She's one of them now, whatever they are. That who you're after?"
- **Opener photo:**
  - (npc) "(He looks, and his mouth goes tight.)"
  - (npc) "I know her. She sat my pews twice, early on, right at the back. I remember thinking, there's one with her eyes still open."
  - (npc) "[c=dim]Then she stopped coming. They all stopped.[/c]"
- **Exchange `flock`** (avail: intro asked, not doomed) — "Tell me about the new folk."
  - (npc) "There's a flock in this town that kneels in no church of mine. Where they kneel now, I couldn't tell you."
  - (npc) "All I have is a rumor. The boy Toby swears he watched them walk off down the river one night. Nobody has seen them since."
  - (npc) "They weren't taken. They walked off willing, and sold the Lord to ease their own aches."
  - (ask) "He is working himself hot. The next words go somewhere they can be heard."
    - **Press him. Names carry.** → (pi) "Somebody should say it where they can hear. You're the only one in this town still willing." / (npc) "I preach it plain, and spare no sinner. The sheriff hears every word, and never once takes communion." / (npc) "Let them come for an old man. I've buried better than the thing they kneel to." *(`_crane_provoked`)*
    - **Hold him back. It is not worth his life.** → (pi) "Keep it inside these walls, Reverend. In this town the ones who go quiet are the loud ones." / (npc) "(A long breath goes out of him.) You sound like a man who means it. All right. Inside these walls. For now." / (pi) "[c=dim]For now. He's only banking the fire.[/c]"
- **One-shot: the bell** (`preacher_dialogue`, avail: bell rung + met him):
  - "That was you in my tower. The bell has not swung in years. Nobody left worth calling."
  - "They heard it, though. Down that road, something always does."
- **On leave** (`crane_on_leave`, once):
  - (npc) "I've said what I've said. Go on now, and watch the road."
- **Provoke note** (`_crane_provoked`, case note): "[c=dim]I wound the old man up and pointed him at them. He wanted pointing. That is what I will tell myself.[/c]"

## Toby — the kid, innocent witness
- **Voice:** `blip_kid`. **Code:** `scenes/dialogue.py` `TOBY_CONVO`,
  `toby_dialogue`. **Who:** local child; the sole witness of where the
  procession went. Witness EARNED on the photo. Lends the bear.
- **Presentation (2026-07):** `toby_dialogue` opens `TOBY_CONVO` inside a
  frozen close-up **tableau** (`_open_toby_tableau`, `tableau=True`): his
  room across the little table, the one almost-normal room in Brimley, his
  idle watching the corn line out the window (the framing line made pose).
  The bear one-shot still volunteers as a plain beat first. The words are
  identical either way (below). See Part B "The close-up examine tableaux."
- **Greet** (`toby_greeted`):
  - (npc) "You're not from here. I'd have seen you before."
  - (npc) "What are you doing, mister?"
- **Opener intro:**
  - (npc) "A detective. For real? Like on the TV."
  - (npc) "Nobody here would hire one. Asking questions is what you stop doing, if you live here."
  - (pi) "Well. I'm asking. And I don't mind talking to you."
  - (npc) "I know. Don't tell my mom."
- **Opener photo** (sets `toby_told`):
  - (npc) "That's her. She came in after all the others did. The last one. Folks thought the strangers were done coming, and then her car came up the road alone."
  - (npc) "They slept all over then. The barn. The lodge. My school too, in rows, right where we do our letters."
  - (npc) "Then one night they all went down. A whole line of them in the dark, along the river to where the ground is broke open. I followed."
  - (npc) "They climbed into it. Under the field. She never came back up. None of them did. I saw where they go."
  - (npc) "You can't walk there. I looked in the daytime, and the field just put me back."
  - (npc) "[c=dim]Keep her picture put away. Some of them look at what you carry.[/c]"
- **Exchange `home`** — "Anything strange at home?"
  - (npc) "My mom hums a song that doesn't stop. She doesn't know she's doing it."
- **Exchange `church`** — "Do you go by the church much?"
  - (npc) "I don't walk past the church anymore."
  - (npc) "[c=dim]The door is open. They left it open.[/c]"
- **Exchange `way_out`** (avail: heard the fold) — "If I find a way out, I'll come get you."
  - (npc) "If you find a way out, don't tell me."
  - (npc) "[c=dim]I tried to lie yesterday. My mouth wouldn't.[/c]"
- **Exchange `holding_up`** (avail: `toby_told`) — "You holding up okay, kid?"
  - (npc) "Do you know what's wrong here, mister? Nobody will tell me."
  - (pi) "Not all of it. But I'm going to find out, and I'm going to make it stop."
  - (npc) "Am I gonna be okay?"
  - (pi) "You're gonna be okay. I promise. When I'm done, I'll come back for you."
  - (npc) "[c=dim]Okay. I believe you.[/c]"
- **One-shot: the bear** (`toby_dialogue`, avail: `toby_told` + reassured):
  - "[c=dim]He digs in his coat and holds something out with both hands. A stuffed bear, worn soft, a name stitched on the tag.[/c]"
  - "The lady gave it to me. The one in your picture. She said she couldn't keep it and she couldn't throw it out."
  - "It's the only toy in the whole town. If you find her... give it back? She should have it."
  - "[c=dim](You take a bear from a boy, and you promise. You do not let yourself read the name on the tag. Not yet.)[/c]"

## The Brimley chorus — Old Pell, Mrs. Calder, Royce, Garrick
- **Code:** `scenes/dialogue.py` `PELL_CONVO` / `CALDER_CONVO` /
  `ROYCE_CONVO` / `GARRICK_CONVO`, `chorus_dialogue`; reactive stoop beats in
  `scenes/brimley.py`. Locals describe **failure, never pattern** about the
  roads (§4). Each carries the shared opener pair + one or two signature
  questions. **Royce (blip_mid):**
  - Intro tail: (npc) "The finding I can't speak to. The driving home I can. Ask me about the roads sometime. Ask me what they do."
  - `roads` — "What do the roads do?": (npc) "I drove it. River road, county line, every road out of Brimley. Same as everybody in this town with a set of keys. The corn handed me back every time." / (npc) "Same bend. Same bridge. Same town coming up in the windshield. And I'd swear to you on anything I never turned the wheel." / (npc) "[c=dim]I gave it up. Everybody did. There's no out to drive to.[/c]" / (pi) "[c=dim]Said flat. No fear left in it.[/c]"
  - `how_in` (avail: roads asked) — "Something on your mind?": (npc) "You came IN. That's what's on my mind. That road only ever hands a man BACK, and it carried you in easy as Sunday." → ask:
    - **Tell him the truth** → (pi) "I drove up at night. Radio went to static past the county line, and the road just drove. There was nothing to it." / (npc) "(Something goes out of him.) Nothing to it. Every driver in this town tried that same drive till they quit. For you it just drove." / (npc) "[c=dim]Then it wanted you in, mister. I'd chew a while on what that means for getting out.[/c]"
    - **Give him nothing** → (pi) "Same as anybody drives anywhere. I wasn't paying attention." / (npc) "Wasn't paying attention. (He laughs, and there's no fun in it.) No. I don't suppose you were." / (npc) "[c=dim]Sure you weren't. (He looks back down the road.) Nobody drives that road easy. Nobody but you.[/c]"
- **Garrick (blip_mid):** greet "Seen you already, son. Door to door, both banks. I sit this square most of the day. Everything in Brimley crosses it sooner or later." Intro tail: (npc) "[c=dim]The Sheriff will tell you to head on home. He knows you can't. He can't either.[/c]"
  - `roads` — "Any safe way around this town?": (npc) "Stay on the roads. People who go off the roads come out wrong-side of where they went in. I've watched it happen to better walkers than you." / (npc) "And don't put your faith in a road going where it went last week. Make for the county line and you'll be back at this well by supper." / (npc) "[c=dim]Go on home, son. ...Oh. Right. None of us can.[/c]"
- **Old Pell (grower, the corn pride + uncut-fields grief), Mrs. Calder (the plate for a guest she can't name):** their `PELL_CONVO` / `CALDER_CONVO` beats carry the shared opener + signature questions; their reactive stoop lines live in `scenes/brimley.py` (`beat_pell_coal`, `beat_calder_unlatched`, Calder greet). Key stoop beats:
  - Pell: "Whatever you're finding out there, don't bring it up my step. I've got the calendar where I want it. Stopped. Some of us need it stopped."
  - Calder greet: "No. No, it couldn't be you. Forgive an old woman her hoping."
  - Calder: "I've started leaving the door unlatched at night. It seemed... polite."
  - Royce stoop: "I keep turning it over. Every road out of Brimley hands you back. Except the one that carried you in. If a door only opens the one way, mister, it isn't a door."
  - Garrick stoop (preacher): "Nothing out of him for days now. Man spends his life raising his voice, then nothing at all." / "You go by and look in on him, son. Somebody ought to."
  - Hettie stoop: "I keep the lights on. So they know. Someone's keeping them on."

## Mara — the confrontation
- **Voice:** `blip_mid`. **Code:** `scenes/well.py` `MARA_CONVO`,
  `_mara_voice`, `_sign_update` / `_call_out` (the calling-out staging).
  **Who:** the quarry, already turned; proof, not a counted beat. She never
  says the boy's name (invariant, flow §28c). The calling-out fires on first
  entry; the exchange opens whatever the player asks.
- **Presentation (2026-07):** `_mara_voice` opens `MARA_CONVO` inside a
  frozen close-up **tableau** (`_open_mara_tableau`, `tableau=True`), the
  last of the seats, with the REVEAL: she opens as ONE OF THEM (the carved
  mask and hood of the congregation fill the frame) and the caption **LISTS
  her as "One of them"** until the greet's unmask beat lifts the mask away;
  from then on the listing reads "Mara". Her first line lands from behind
  the wood. Escape PAGES her captions (the reveal cannot be walked out of
  mid-line); only her menu takes Escape as "Say nothing." The words are
  identical either way (below). See Part B "The close-up examine tableaux."
- **Greet** (`mara_confront_greeted`; the second beat is the reveal's stage
  caption, landed as the mask comes away):
  - (npc, listed "One of them") "My father sent you. Of course he did. He never could let a thing stay lost."
  - (npc, the listing turns "Mara") "[c=dim]She lifts the mask away. The face from the photograph, gone thin.[/c]"
  - (npc) "Tell him what I told him at the start. I'm not lost. I've never been this close."
  - (npc) "[c=dim]I was not taken. I was answered, and I went to it gladly.[/c]"
- **Exchange `leave`** — "Come with me.":
  - (npc) "Out."
  - (npc) "Nobody leaves, mister. Nobody has left since the winter. You have walked the roads by now. You know it better than the ones who quit trying."
  - (npc) "And why would I go. He is right there. A few feet of earth, and he is right there."
- **Exchange `way_out`** — "How do I get out?":
  - (npc) "There isn't. We can't. None of us can."
  - (npc) "It is not a wall, mister. A wall has a far side. Every way out of this town is a way further in."
  - (npc) "Go home, while the town still lets you think you can."
- **Exchange `father`** (ends the confrontation; sets `mara_lucid`) — "Your father is waiting.":
  - (npc) "My father."
  - (npc) "[c=dim]He used to wait up. However late I came home. He never said a word about it, but the kitchen light would be on.[/c]"
  - (npc) "The light."
  - (npc) "It went out. It just went out. All this time there was a light at the bottom of the dig, under a door, like a house where somebody is waiting up. I could see it with my eyes open. I am looking right at where it was."
  - (npc) "My hands. Look at my hands. When did I eat, mister. What day is it, outside."
  - (npc) "You are real. You came from outside. What am I doing down here."
  - (pi) "Come home. Come with me, right now, and don't look back."
  - (npc) "[c=dim]Home.[/c]"
  - (npc) "Say what is up there for me. Out loud. Say what I go back to."
  - (npc) "Nothing. It happened, and up there it stays happened, every morning, forever. Down here it is not finished happening. Down here he is still coming."
  - (npc) "There is no out, mister. Not for me. Only deeper."
  - (npc) "[c=dim]Tell my father I was happy here. Tell him whatever makes him stop.[/c]"
- **Exchange `name`** (avail: carries the bear; ends; sets `mara_named`) — "Say the boy's name." / "You would have been a good mother to him, Mara. To Sam.":
  - (npc) "[c=dim]She goes still in a way the kneeling ones do not. Something behind her face tears loose.[/c]"
  - (npc) "Don't. You don't get to carry that name down here and set it down in front of me."
  - (npc) "[c=dim]Her hand closes on your coat, hard. Down the aisle the rank stirs all at once, like one body turning over in its sleep. The air pulls tight.[/c]"
  - (pi) "[c=dim](You hold out the bear. The tag toward her, the name toward her.)[/c]"
  - (npc) "[c=dim]She looks at it the way you would look at your own hand if it came off in the dark. She does not take it. She cannot make her arms cross the space.[/c]"
  - (npc) "Put it away. Put it AWAY."
  - (npc) "You think I don't know. You think I clawed my way down into this dark because I believe he is here, waiting up for me."
  - (npc) "He is not here. He was never anywhere. I knew it the day they laid him in my arms already gone, and I know it now, with my hands in this dirt."
  - (npc) "But while I am still going down toward something, he is still somewhere ahead of me. Stop digging and he is nowhere at all. That is what you are asking me to put down. Not the dig. Him."
  - (npc) "So keep your bear. I will go back down to the only place he is still coming."
  - (npc) "[c=dim]She lets go of your coat, turns, and kneels back into the rank. The chamber settles, as though nothing rose.[/c]"

## The cult (THE TALK) & the hollow Sheriff
- **THE TALK** (`systems/threat_mixin.py` `_cult_talk` +
  `_open_talk_tableau`, the first grab of a run). **Presented as the grip
  close-up tableau (2026-07)**: the carved mask fills the frame and the
  beats land as its captions; Escape pages, it never aborts (you do not
  walk out of the grip). The beats, in order:
  - (stage) "[c=dim]The hand lands on your shoulder before you hear him
    coming. The grip is friendly. Nothing else about it is.[/c]"
  - (npc) "\"Hey. You go back to your hotel room if you know what's good
    for you.\""
  - **the one choice** (only if the PI carries the revolver; otherwise the
    beats run straight through). Prompt: "He waits, hand where it landed."
    - **Hold still.** → (pi) "(You hold still.)"
    - **Reach for the revolver.** → (pi) "(Your hand starts for your coat.
      His other hand is already on your wrist. Resting there. That is all
      it does.)" / (npc) "None of that, now. We're only talking." *(the
      close-up shows the second hand on the wrist)*
  - (npc) "\"Run.\""
  - Then the release (the room stands down, the grace window, the filed
    note `the_talk`) and the PI's reaction as the world resumes:
    "[c=dim]Well shit, this town really doesn't have a midwestern welcome
    at all.[/c]"
- **Hollow Vane** (`systems/rot_mixin.py` `_spawn_hunting_sheriff`, once per
  run): notice + "Sheriff Vane stands. \"I'm supposed to tell you to leave,
  son. I can't...\"" (the line he can no longer finish).

---

# PART B — WHAT CAUSES WHAT (narrator & world boxes)

Narrator/world text keyed to the event that fires it. The FIVE canonical
evidence beats and the descent-voice track are the load-bearing set; the rest
are dread one-shots and prop examines.

## Evidence pickups (the five canonical + the notes)
Fired by `_evidence(game, name, ...)` in `scenes/dialogue.py`; the log excerpt
IS the case entry. Canonical (count toward the King-gate): `maras_receipt`
(shop tab, Hettie), `maras_record` (booking slip, office), `maras_journal`
(barn, fires the door-dream on pickup), `maras_dig` (the Sign in her hand,
Scriptorium), `maras_room` (the unsent letter, her cell). Notes (never
counted): `the_ledger`, `the_preacher`, `the_congregation`, `the_dream`,
`the_how`, `the_talk`, `the_bear`, the cult testimony (`cult_calling` /
`cult_bargain` / `cult_digging`).
- **`maras_receipt`** (`grant_receipt`): "A store tab off Hettie's spike,
  headed 'M. Blaine' in her hand." / "Matches, canned milk, the same short
  list run down most of a year. The staples a resident buys, week on week." /
  "She lived here."
- **`maras_record`** (`_office_interact`, `scenes/villager_houses.py`): "A
  booking slip in the Sheriff's records. Blaine, Mara." / "Held a night for a
  disturbance on the main road, shouting at the sky. Released at dawn, no
  charge filed."
- **`maras_dig`** (`build_works_scriptorium._interact`, `scenes/well.py`):
  the Sign in Mara's own hand / "No captive draws this."
- **`the_fall`** (`build_depths_antechamber._interact`, `scenes/depths.py`):
  "There is no way back above you, and you are not hurt. Cut stone, worn
  smooth by years of feet that came this way before you."
- **`threshing_floor`** (`build_depths_threshing._interact`): "The yield,
  raked into low heaps: grain, all of it, tithed down from the fields above.
  The town's whole harvest, carried down and never carried back up."
- **`the_old_stores_shelves`** (`build_the_old_stores._interact`): "Shelves
  of the dig's gear: lamps burned black, pick hafts worn down to the grain,
  every one tagged in the same steady brown hand."
- **`the_preacher`** (`preacher_body_examine`, note): "The Preacher. He
  named them from his pulpit, every Sunday. Then he went down to the river
  after them, believing a flock can be talked home." / "They opened him for
  it and left him on the bank, where the whole town could find him." / "His
  collar's still white. His cross lies in the mess. You take it."
- **`cult_digging`** (`build_the_old_stores._interact`, note): "The last
  pages stop being sentences. Just the word door, over and over, pressed hard
  enough to tear the paper."
- **`the_how`** (`_vane_how_told`, note): "[c=dim]The sheriff spent his one
  card. A blind man, no name, lit up with certainty, promised his own eyes by
  the dream once the work is finished. Sent to fetch the last holdout, and
  thanked him for refusing. / Nobody was argued north.
  Each of them was promised the one thing they were starving for, and every one came gladly.[/c]"
- **`the_congregation`** (`_mara_voice`, note): "Mara, kneeling with the congregation. Turned. There was never anyone to bring back."
- **`the_dream`** (`_log_dream_entry`, note; canon-guarded "a year", no
  recurrence): "I never reached it. One dream, a year ago, and it never came
  again. So why do I know this place."
- *(The remaining evidence-beat and note excerpts live in the code and are
  transcribed here as Wave 6 lands; see Coverage.)*

## The descent-voice track
`systems/game.py` `_DESCENT_VOICE`, keyed to descent milestones. The PI's own
diary-voice runs **first person** (chalk_surface, descent_dig, chalk_deep);
the intruding lure runs **second person** (descent_leave, descent_mask) — a
deliberate self-vs-lure split, not a POV wobble. Fires as an on-screen beat +
a case note.
- **`chalk_surface`**: "A door, chalked onto the floorboards. The size of a
  real one, and careful about it. A frame laid flat, like you could step down
  through it. ...Kids do stranger. I wrote it down anyway."
- **`descent_mask`** (the temptation): "His face, in your hands. Light as
  folded paper, cold, and it knows your grip." / "The pale mask hums in your
  hand." / "And you KNOW it, the way you know a thing in a dream. Carry this,
  and the town opens. The roads let you out." / "The names, the register, the
  girl her father wanted found. You have enough. You could be in the car by
  morning. You could just go."
- **`chalk_deep`**: "The drawn doors are behind my eyes now, every time I
  shut them. Everything in me is pulling for the surface. The way back is
  shut. So down."
- *(Full track transcribed as Wave 6 lands; the code is authoritative until
  then.)*

## The fold notes
`systems/narrative_mixin.py` `_fold_mentioned` (a local names the looping
roads) and `Game.cross_fold` (`_note_fold_portal` = a visible pane, awe;
`_note_fold_loop` = the second silent loop, the creep). The perceptible
spatial fold only (looping roads), never the door or the cosmology.
- **`the_fold_told`** note: "[c=dim]... And my own engine turned over and died at the lodge steps.[/c]"; the spoken reflection: "{name} says there's no
  driving out of here. The roads loop, the corn hands you back. Said it like
  weather." / "A town doesn't talk like that about nothing. And my car died at the steps."

## The dream & the threshold recognition
- **The journal door-dream** (on `mom_notebook` pickup): wordless cutscene,
  no text; files `the_dream` (above).
- **The threshold recognition** (`scenes/depths.py build_threshold`, if
  `flashback_seen`): "You have stood here before. In sleep." then the plain
  doorframe beat.

## The close-up examine tableaux
Diegetic close-up "look at the thing" modals (art in `ui/tableau.py`, state in
`systems/tableau_mixin.py`): press `[E]` on a tagged prop and the world pauses
on an animated close-up with a menu that mutates it live. The same frame also
hosts a **conversation** with a principal (the pilot: Sable). Player-facing
text:
- **Mr. Sable's reception desk** (`_open_sable_tableau`, opened from
  `clerk_dialogue`). The talk itself IS the tableau: `SABLE_CONVO` runs in
  `tableau=True` mode, so its spoken beats are the caption ([E] advances) and
  its question menu is the option panel. All of its words are quoted under
  **Mr. Sable** in Part A. The close-up reacts to the talk: the photograph
  appears on the register once he has been shown it (`sable_showed_photo`),
  and the sealed Invitation appears once he has handed it over
  (`rite_envelope_given`). Escape (or walking the talk out) closes it.
- **Sheriff Vane's office** (`_open_vane_tableau`, opened from
  `sheriff_dialogue`; words under **Sheriff Hollis Vane** in Part A). Cold
  window daylight, the stopped JAN 15 calendar, the cell bars at the frame's
  edge, the gun cabinet in the back. Reactive on two axes: his **pose** reads
  the despair ledger exactly as the mood prompt does (`_vane_tableau_state`
  mirrors `_vane_prompt`'s thresholds; mood, never a number), and the desk
  carries what the talk has earned: the **newspaper** stays spread flat once
  given (`convo_vane_paper_asked`), the **cabinet** stands open and emptied
  once he unlocks it (`vane_gave_cache`).
- **Hettie's shop counter** (`_open_hettie_tableau`, opened from
  `hettie_dialogue`; words under **Hettie** in Part A). The gutted shop:
  bare shelves with dust-ghosts where the stock stood and one tin left, the
  till empty since the new year, the shop door at her left, and her ONE
  kept bulb burning over the counter, swaying just barely (the stoop line
  made light). Her spectacles keep her sprite's tell: lenses filled black,
  the glint on the same wrong side of both; her "blink" is the glints going
  out. Reactive: her idle **glances at the door** every few seconds (the
  framing line made pose), **Mara's tab** stays curled on the spike by the
  till until the receipt is taken (`evidence_maras_receipt`), and the
  **traded newspaper** lies open on the counter after the barter
  (`newspaper_traded`).
- **Rev. Crane's lectern** (`_open_crane_tableau`, opened from
  `preacher_dialogue`; words under **Rev. Asa Crane** in Part A). The
  chancel in candled dusk: board walls, the plain wooden cross, the tall
  arched window with the day going out of it, the bell rope hanging dead at
  the frame's edge, his candle stand the only light. Reactive: his **hands** read the
  press fork exactly as the framing line does (`_crane_tableau_state`
  mirrors `_crane_prompt`): folded over the lectern while he waits;
  gripping its corners, head forward, once `preacher_doomed` latches.
- **Toby's little table** (`_open_toby_tableau`, opened from
  `toby_dialogue`; words under **Toby** in Part A). The one almost-normal
  room in Brimley, and that is its dread: plain daylight, his crayon
  drawings taped up crooked, the closet door with its own drawing, the toy
  radio on its shelf, crayons and a half-drawn sheet on the table, his
  small hands (one fidgeting a crayon). His sprite's tell survives: the
  cheek marks that read as old tear-streaks on the second look. Reactive:
  his idle **watches the corn line** out the window (the framing line made
  pose), the dark **procession drawing** hangs among the cheerful ones
  once he has told what he saw (`toby_told`), and his worried **brows
  level out** once the PI has made the promise
  (`convo_toby_holding_up_asked`).
- **Mara's confrontation** (`_open_mara_tableau`, opened from `_mara_voice`
  at the calling-out; words under **Mara** in Part A). The last seat, and
  the REVEAL: she stands out of the rank one more hood of the congregation,
  the carved mask (the Talk's grammar, slighter, NEW wood: the last one in,
  the cleanest cuts, no graft) with the gold embers far down in the
  sockets, the rite still running at her back (the Sign's daub-strokes on
  the apse wall, the altar candles, the kneeling rank, the rite-holder who
  never pauses). The caption LISTS her as "One of them" until the greet's
  reveal beat: her hands come up (the dig's ledger: raw knuckles, dark
  nailbeds), pull the mask down off her face (her eyes come free first, the
  embers dying as the wood leaves the flesh), and carry it out of the frame;
  the face from the photograph is under it, gone thin, and the listing turns
  to her name. Reactive: her idle glances back toward the rite behind her
  (the pull, made pose); the father card (`mara_lucid`) drops her eyes to
  her raised, bleeding palms ("My hands. Look at my hands."); the name-beat
  (`mara_named`) closes her fist on YOUR coat at the frame's corner and the
  rank behind stirs, heads lifting. Escape pages her captions (the reveal
  always lands); her menu takes it as "Say nothing."
- **THE TALK's grip** (`_open_talk_tableau`, opened from `_cult_talk` on the
  first cult grab of a run; the beats are quoted under **The cult (THE
  TALK)** in Part A). The tone inversion of the five seats: no room (near
  nothing behind him), no table (his arm crosses the frame to YOUR shoulder
  at the corner), no face (the carved wooden mask of his sprite, grafted in
  at the gore seam, void sockets with a gold ember far down, no mouth: the
  courteous words come from behind wood that does not move). The closest
  frame in the game, and it gets closer: he leans in, very slowly, the
  whole time; the only other motion is the embers and the fingers. The one
  reactive state: `reaching` rests his other hand on the PI's wrist.
  Escape pages instead of aborting, so the release always runs.
- **THE PEDESTAL** (`_open_altar_tableau`, opened from the Sign Chamber altar
  interact, `scenes/well.py`). An OBJECT close-up, not a person: the Pallid
  Mask on the hewn stone ("pale as a drowned face, the eyeholes black") and
  warm (a gold ember far down in each socket, because it knows the PI's
  hands), the daubed Yellow Sign (its own 2D brand) breathing on the apse
  wall above, the kneeling congregation at the PI's back in the cult-dark,
  two candles the only light. The two instincts (NARRATIVE §8) ride on as the
  menu. Prompt: **"The whole machine of it, here in reach."** (trimmed from
  the old modal wording now that the close-up shows the mask/Sign/kneeling).
  - **Lift the mask.** → `_take_mask`: the Mask is the keystone item, and the
    `descent_mask` temptation lands (the Spread/Seal fork opens).
  - **Tear it down. End this.** → BREAK (`_play_ending("rite_broken")`): the
    trap. The rite is the only lid on Him; broken before the source is
    sealed, His influence floods out uncontained. Wordless by design (the
    axe mask-yank, then the Carcosa blast). Escape backs out (the mask stays
    on the altar, re-interactable).
- **The bedroom desk** (`_open_desk_tableau`, opened from `bedroom_interact`).
  Menu labels: **"Take the pistol"** (drops once taken), **"Read the case
  file"**, **"Step back"**. Reading hint: "(walk away to close)".
  - **The case file** (`_tableau_read_case`, sets `read_journal`): "CLIENT:
    Walter Blaine. Wants his daughter found and brought home." / "MARA BLAINE,
    26. Cut ties, drove north, quit calling home. The trail runs cold at
    Brimley." / "The job: ask my questions, find the girl, drive home by
    morning." / "The drive in was easy. Then the engine died at the lodge
    steps and wouldn't catch again."
  - **After the Dark** (`hive_seen`, the file has rewritten itself): "Subject:
    located. Recovery: declined." / "The handwriting is yours. You don't
    remember writing it."
  - Taking the pistol also fires the notice "You take your pistol off the
    desk."

## The death cards
`systems/game.py` `_trigger_death(kind)`: `cultist` → CAPTURED (taken alive);
`sheriff` → TAKEN INTO CUSTODY (the hollow lawman); `king` → the Carcosa
mask-furnace cutscene. Card text is flow-guarded.

## Prop examines
Transcribed as the narrator sweep (`TODO.md` #13b/#15) reaches each. The
ones landed so far:
- **the Arcadia guest-hall LOCKED doors** (`build_lodge_hall._hall_interact`,
  `scenes/lodge.py`; every locked 'l' door in the guest wing): "[c=dim](Locked.
  A row of them, all the same, all shut.)[/c]" (the uncanny hotel of shut
  rooms kept ready for guests who won't come, NARRATIVE §4).
- **`the_burning`** (`build_clearing._void_boss_interact`,
  `scenes/interiors.py`): "A fire pit big enough to stand a family around,
  cold a long while. What it burned was not all wood. Buckles, bowl rims,
  boot eyelets, a watch case, slagged in the ash."
- **the procession candles** (`build_depths_procession._candles_interact`,
  first read): "[c=dim]They walked this in single file, carrying light.
  Nobody hurried. The wax says nobody ever hurried.[/c]"
- **`barrow_tools`** (`_brimley` barrow examine, note): "Digging tools left
  in the barrow, rusted over. The edges are still bright."
- **the emptied church** (`old_man_house_on_enter`, after `preacher_doomed`):
  "[c=dim]Mud on the aisle boards, dried in a line toward the door. River
  mud.[/c]" (the atmospheric "lectern stands empty / stove is cold" line was
  cut, play-notes; the river-mud pointer stays, it is the only in-church
  signal toward the riverbank body).
- **the payphone** (`_brimley`): examine **CUT** (play-notes). The dead
  phone stays as silent set-dressing; the "you hear your own voice" beat is
  gone. No pointer or evidence was on it.

The rest (lodge register / ledger, the well, news rack, cellar key,
headstone, `scarecrow`, `worn_stone`, `bell_tower`) remain indexed: the code
is authoritative for their exact words until the sweep transcribes them here,
and the contract still binds (touch one, update the other).
