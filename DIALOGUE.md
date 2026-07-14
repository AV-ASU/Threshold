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

## Mr. Sable — the Lodge clerk
- **Voice:** `blip_low`. **Code:** `scenes/dialogue.py` `SABLE_CONVO`,
  `sable_on_death`, `clerk_dialogue`. **Who:** local, the most-attuned of
  them, the lucky one (NARRATIVE §4). Genteel host, funereal undertow, never
  gives the girl up; points suspicion at the "unfriendly" old families (the
  trap). He checked the PI in the night before, so every exchange resumes an
  acquaintance. Framing carries the PI four-tier weather (`_pi_framing`).
- **Greet** (`sable_greeted`):
  - (npc) "Up early. You came in late off the north road. I put you down in the book as staying a while."
- **Exchange `mara`** — "I'm looking for someone." / "I'm looking for a woman. Mara Blaine. She'd have come through here."
  - (npc) "Blaine. No, I can't say the name lands anywhere. We get a great many faces through that door."
  - (npc) "You'll mean one of the new folk, though. We had no end of those this past year. They came like they had heard something worth the drive."
  - (npc) "And I was glad of every one. This town was drying up before they came. I had every room full. You should have seen this house with every window lit."
  - (pi) "And the rest of Brimley feels the same?"
  - (npc) "Ah. There you have it. Not everyone's been so warm. Some of the old families have gone cold as a root cellar about the newcomers."
  - (npc) "I would mind who you take your questions to, friend. Not everyone here wishes a stranger well. I do. You remember that."
  - (ask) "Show him her photograph?"
    - **Slide the photo across the desk** → (pi) "(You lay her photo on the register.)" / (npc) "(He looks at it a good while, smiling.) Pretty thing. No, I couldn't say. She'll have found her feet by now. They all do." *(sets `sable_showed_photo`)*
    - **Keep it in your coat** → (pi) "(You leave it where it is.)" / (npc) "No matter. Ask around, if you must. Start with the friendly ones. There are fewer of those than you would think."
- **Exchange `cellar`** — "About that cellar of yours." / "A lot of doors in this town stay locked. You keep a cellar under this place?"
  - (npc) "Storage, mostly. The key is about somewhere. Nothing down there worth the dust, I promise you."
  - (npc) "If it is names you want, sign-in register is right here on the desk. Guest and date, all the way back. Read it as long as you like."
- **Exchange `sealed`** — "Nothing leaves this town. Why?" / "Nothing leaves this town. No car, no truck, no mail since January. That's three months. What happened here?"
  - (npc) "Happened? Nothing happened. The snows came in around the new year and the road just... stopped mattering. It does that, up here."
  - (npc) "Three months is nothing to a town like this. Folk get comfortable. Warm bed, full larder, good company. You will too, give it time."
- **Exchange `car`** — "My car won't start." / "My car died at the lodge steps the night I drove in. Turns over and never catches."
  - (npc) "The roads are not going anywhere tonight. Neither are you. I would not fret over the car."
  - (pi) "I didn't ask about tonight. I asked what's wrong with it."
  - (npc) "Nothing a night's rest won't settle. It will keep till morning. Everything here does. Get some rest."
- **Exchange `checkouts`** (avail: read the Ledger) — "The checkouts stop a year back." / "I read your old registers. Guests used to settle up and leave. The dates stop a year back. Since then everyone signs in and nobody signs out."
  - (npc) "(The pleasant look does not shift.) Do they not? Fancy that. I never was much of a hand with the paperwork."
  - (npc) "They will not have gone far. Nobody does. It is a restful town, friend. People stay. It is the one thing I can promise a guest."
- **Exchange `her_state`** (avail: read Mara's journal) — "When did she change?" / "Her journal reads like someone already halfway out a door. When did she change?"
  - (npc) "(He sets his hands flat on the desk.) You keep telling me she is lost. I keep telling you she is not."
  - (npc) "She stopped fretting, toward the end. Folk do, here. It is a mercy, if you let it be. You will let it be too, in time."
- **Exchange `the_fold`** (avail: heard the fold named AND walked it) — "The road out brought me back." / "I walked the road out of town. Followed it two hours, due west. It set me back down past this window."
  - (npc) "I told you the roads were not going anywhere. You heard a man being hospitable. I meant it plainly."
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
  - (npc) "I can't put a day or a door to her. The new folk came in numbers and they keep to their own. She'd have been one of them."
  - (npc) "They filled the school, the barn, the lodge. Then one night those rooms were empty, all at once. Wherever your girl is, that's the direction. I can't tell you where it GOES."
  - (pi) "[c=dim]More of an answer than anyone in this town has risked. He watched those rooms.[/c]"
- **Exchange `car`** — "My car died the night I drove in." (files the fold note, no chained reflection)
  - (npc) "Won't start. Won't ever. Nothing with an engine leaves Brimley."
  - (pi) "Engines don't all quit at once. Somebody got to it."
  - (npc) "Nobody touched your car. I know how that sounds. I've watched men tear three trucks down to the block hunting the part that failed. There is no part."
  - (npc) "[c=dim]It's the town.[/c]"
  - (pi) "[c=dim]He said it flat. Like weather. So.[/c]"
- **Exchange `town`** — "What happened to this town?"
  - (npc) "I was born here. So was my dad."
  - (npc) "They started showing up in the summer. The new ones. Polite folks. After a while the road stopped going anywhere."
  - (npc) "I tell people to leave. I haven't been able to in months."
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
  - (npc) "You don't talk a hundred strangers onto one road. They weren't tricked. Every one of them was going toward something, and glad of it. What it was, who was holding it out, I never got closer than that chair. That's the piece that keeps my lights on at night."
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
  hold).
- **Greet** (`crane_greeted`):
  - (npc) "Another new face. That's all that comes to Brimley anymore, strangers off the highway, more every season. And not one of them leaves."
- **Opener intro:**
  - (npc) "I don't trust it. They arrive too easy, like something held the door. Then they go quiet, drift out to the corn, and they don't come back."
  - (npc) "A young woman came through in the fall. Bright thing, full of questions, like you. She's one of them now, whatever they are. That who you're after?"
- **Opener photo:**
  - (npc) "(He looks, and his mouth goes tight.)"
  - (npc) "I know her. She sat my pews twice, early on, right at the back. I remember thinking, there's one with her eyes still open."
  - (npc) "[c=dim]Then she stopped coming. They all stop.[/c]"
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
- **Greet** (`mara_confront_greeted`):
  - (npc) "My father sent you. Of course he did. He never could let a thing stay lost."
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
- **THE TALK** (`systems/threat_mixin.py` `_cult_talk`, the first grab of a
  run): grab caption "[c=dim]The hand lands on your shoulder before you hear
  him coming. The grip is friendly. Nothing else about it is.[/c]"; the
  cult's warning lines (white); PI reaction "[c=dim]Well shit, this town
  really doesn't have a midwestern welcome at all.[/c]" and the filed note
  `the_talk`.
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

## The death cards
`systems/game.py` `_trigger_death(kind)`: `cultist` → CAPTURED (taken alive);
`sheriff` → TAKEN INTO CUSTODY (the hollow lawman); `king` → the Carcosa
mask-furnace cutscene. Card text is flow-guarded.

## Prop examines
Transcribed as the narrator sweep (`TODO.md` #13b/#15) reaches each. The
ones landed so far:
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
