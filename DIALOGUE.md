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

**Coverage (audited 2026-07, the anti-drift pass).** Part A is complete and
verbatim for the whole speaking cast, INCLUDING the chorus's full
conversations, every framing line, every full spoken question (`q`) behind a
short menu label, the ask-prompts, and the option labels. Part B transcribes
verbatim: every case-notebook write (the five canonical evidence beats and
every note), the descent-voice track in full, the school and grove rites, the
descent gates and staging boxes, the endings' captions, and the narrator
boxes. What stays **indexed, not transcribed**, is the one-line HUD/system
notice layer: controls and key prompts ("Mash E", "Press [F]"), cover/hide
state lines, combat feedback ("Empty. You need cartridges."), threat tells
("They've seen you."), pickup confirmations, and routine one-line prop
examines (headstones, the bell-tower view). Those are UI, not narration; the
code is authoritative for their exact words, but the contract still binds:
touch one, update the other.

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
   mechanism. Vane holds exactly ONE fragment of the *how* (the
   recruiter's offer) and it stays a hard-won, half-understood piece he
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
9. **A mode of address belongs to ONE speaker.** "son" had spread across
   Vane, Old Pell and Garrick (eight uses, three speakers) and was a large
   part of why those three read as interchangeable. It is **Garrick's**: he
   sits the square, he counts who is left, he talks to the PI like a younger
   man. Nobody else uses it, including the hollow Sheriff. The same holds for
   "friend", which is Sable's. **"mister" is exempt and stays shared** on
   purpose: nobody in Brimley ever learns the PI's name, so it is the correct
   default in every mouth and says nothing about the speaker. Enforced by
   `tests/conventions.py` check 10, because the drift is invisible one line
   at a time.
10. **Markup never leaks.** `[c=...]`, `[/c]`, and every style token is
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

**The shared conversation strings** (`ui/conversation.py`, the convo dicts):
- Every principal's and chorus member's menu closes on the same leave option:
  **"That's all for now."** (Mara's confrontation alone closes on **"Say
  nothing."**). The engine's fallback framing prompt, if a conversation
  authors none, is "What do you ask?" (every shipped convo authors its own).
- **The PI's four-tier weather** (`_PI_WEATHER`, `DESIGN.md` §2): every framing
  line below composes one of these onto its base as evidence mounts (tier 0
  is empty; the NPC's words never change, the man hearing them does):
  - tier 1 (1-2 evidence): " Something in this town isn't sitting right, and
    I can't put a name to it yet."
  - tier 2 (3 evidence): " I know what's under this town now. It's work,
    keeping a plain face plain while I listen."
  - tier 3 (4+ evidence): " I've been down where the road ends. Ordinary's a
    thing I decide to believe now."

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
- **Framing** (`_pi_framing` base): "Sable folds his hands on the register
  and waits."
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
    - **"Slide the photo across the desk."** → (pi) "(You lay her photo on the register.)" / (npc) "(He looks at it a good while, then hands it back.) No. A pretty thing, but no. I could not put a name or a room to her. So many faces came through that door." *(sets `sable_showed_photo`; confirms only that he does not know her)*
    - **"Keep it in your coat."** → (pi) "(You leave it where it is.)" / (npc) "No matter. Ask around, if you must. Start with the friendly ones. There are fewer of those than you would think."
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
- **Exchange `paper`** (avail: carries newspaper; the favor economy, the NULL door and the tell: no reward, the chill files as the note) — "I brought yesterday's newspaper." / "Yesterday's newspaper, Mr. Sable. First word from outside since the winter. It's the house's if you want it."
  - (npc) "(He takes it in both hands and squares it on the desk, unopened, the fold lined up with the register's edge.)"
  - (npc) "That is a kindness, friend. The Arcadia thanks you."
  - (npc) "We will set it out in the common room. Guests do like having something to read."
  - (pi) "You're not going to open it?"
  - (npc) "Oh, I expect I will get to it. The news keeps, friend. It always has."
  - (npc) "Now. Was there anything else?"
  - (pi) "[c=dim]Half this town would give a finger for that page. He squared it to the desk like a coaster.[/c]"
- **Exchange `the_way_down`** (avail: 3 evidence, no envelope yet) — "You've been holding something for me." / "You've kept something back from me since I walked in. I'll take it now."
  - (npc) "You are past pretending to be a guest now, I think. All right."
  - (npc) "(He lays a long envelope on the desk. Wax seal, the Sign pressed into it. He handles it like a room key.)"
  - (npc) "My guests left it at the desk when they went below. It was meant for me. They wanted me to come down after them, and they meant it kindly."
  - (npc) "But I never wanted what they went to find. I wanted a full house, friend, and I had one. Take it. Somebody has to keep the desk."
- **On leave** (`sable_on_leave`, once; the host keeping the guest a beat
  longer):
  - (npc) "Hold a moment. You drove in off that road last night. So you'll know."
  - (npc) "Did it feel to you like it went anywhere? Folk say it does not, lately. I wouldn't know. I never leave the desk."
- **If Sable is killed before the handoff** (`sable_on_death`, the Invitation
  drops with the body): notice "Something stiff in the clerk's coat: a
  wax-sealed envelope."

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
- **Opener photo** (the WARM DELIVERY of the booking slip, NARRATIVE §6: he
  personally booked her, so the photograph is a recognition, not a shrug. The
  `("do", grant_record)` beat hands the slip over mid-exchange; the office
  records drawer is only the fallback for a dead or hollow Vane):
  - (npc) "(He takes it to the window light and works it corner to corner, a lawman's look. Then he stops working it.)"
  - (npc) "I know that face. I had her in my cell one night in December."
  - (pi) "You booked her."
  - (npc) "Disturbance on the main road, near midnight. She was not drunk and she was not hurt, so I held her till first light and let her go. No charge. There was nothing to charge her with."
  - (npc) "She thanked me for the blanket. Polite as Sunday. Then she walked back out into it."
  - (npc) "(He goes to the files and comes back with a slip, and holds it out without reading it.) Take it. It is the only paper in this office with her name on it."
  - (npc) "The new folk filled the school, the barn, the lodge. Then one night those rooms were empty, all at once. Wherever your girl is, that's the direction."
- **Exchange `the_night`** (avail: photo shown + the record held; once; files
  the `the_disturbance` note) — "The night you booked her." / "Tell me about
  the night you booked her. What was she doing out on that road?" — the slip
  says what he WROTE DOWN; this is what he saw, and what he did not. The lead
  it leaves (a man who sits the square all day) is stated as plain fact and
  never pointed at: connecting it to Garrick is the player's.
  - (npc) "I did not see the start of it. By the time I walked up she was standing in the middle of the road with her head back."
  - (pi) "Shouting at what?"
  - (npc) "Nothing that was there. Words, plain enough, and not one of them for me. I could not tell you a single one now."
  - (npc) "I have booked drunks and I have booked men out of their heads. She was neither. She was answering somebody."
  - (pi) "Who came and got you?"
  - (npc) "One of the old boys who sits the square all day. He stood and watched the whole of it before he ever thought to come for me."
- **Exchange `town`** — "What's happening to this town?" / "What's happening to this town, Sheriff?" (dynamic beats, `_vane_town_beats`: Vane's lived arc, then a reaction that branches on whether the PI already knows the seal). **Present tense by design** (maintainer, 2026-07): not a history lesson about something finished, the thing still happening to him. It absorbed the retired `car` exchange, so the dead engines are a symptom of the town here rather than an errand about the PI's own vehicle, and this is where the fold note is filed now.
  - (npc) "Brimley was dying before any of this. Half the town gone south for work, storefronts boarded up. Some weeks the phone never rang once."
  - (npc) "Then last summer the strangers started coming up the north road, and they didn't stop. More than we had beds for. Polite, every one. Kept to their own. Not one could tell me where they'd driven in from, or why they'd want a dead town like this."
  - (npc) "I kept waiting on the trouble strangers bring. It never came. Something quieter did. The trucks stopped running. The mail stopped. And the road out stopped taking anybody anywhere."
  - (npc) "Nothing with an engine leaves Brimley. Not yours, not mine. I have watched men tear three trucks down to the block hunting the part that failed. There is no part."
  - (npc) "[c=dim]It's the town.[/c]"
  - (pi) "[c=dim]He said it flat.[/c]"
  - (npc) "You need to get out of here. We all do. No one has been able to leave in months."
  - **first time** (has not learned the seal yet; marks the fold heard): (pi) "Wait. What are you saying, Sheriff? No one has left?" / (npc) "Not a soul, not since the winter. They try. I tried, more times than I'll admit to a stranger. Every road out of Brimley turns you around and sets you back at that well." / (npc) "You'll learn that yourself soon enough. Everybody does."
  - **already knows** (heard the roads loop / walked one / re-asking): (pi) "Then you tell me how, Sheriff. Every road out, every engine, a whole town that can't leave. It's not right. How?" / (npc) "You think I haven't stood right where you're standing and asked that, every night for a year? I don't have a how for you. Just this badge, and a list of folks I can't help."
- **Exchange `share_journal`** (avail: intro asked + journal found; hope + trust) — "I found Mara's journal." / "I found her journal. They all dreamed the same door, every one of them. She wrote that she was digging down to it. Glad about it."
  - (npc) "Say the first part again. The same door. All of them."
  - (pi) "All of them. And she didn't write like a prisoner. She wrote like a woman nearly home."
  - (npc) "A year I've been asking this town for one honest page. You walk in off a dead road and hand me her whole hand."
  - (npc) "That's the first real piece of work anybody has brought through that door since it all shut. I won't forget you did."
  - (pi) "[c=dim]Something in him let go a notch.[/c]"
- **Exchange `paper`** (avail: intro asked + carries newspaper) — "I brought yesterday's newspaper." / "I've got yesterday's paper in my coat. April fourteenth. Figured the law here should have some word from outside." (despair lever, +VANE_PAPER_DESPAIR)
  - (npc) "(He takes it in both hands, careful, like something that might go out.)"
  - (npc) "(He spreads it flat on the desk and stands over the front page a long time.)"
  - (npc) "Kurt Cobain. Huh."
  - (npc) "I drove down to the Cities to see him play, before all this. Stood at the back. Best night I had that whole year."
  - (pi) "Sheriff?"
  - (npc) "He had every road out of every town, that man. The whole world open. And he shut the door on it from the inside."
  - (npc) "So it isn't just here. That's what a front page is for, I guess. Telling you the weather's the same all over."
  - (npc) "Thank you for the paper, son. Go on home now. (He doesn't look up from the page again.)"
  - (pi) "[c=dim]I meant it as a kindness. Walking out, I couldn't remember why I thought it would land as one.[/c]"
- **Exchange `how`** (avail: THE TALK has happened, and he has not told it
  yet; re-askable) — "Where are the cultists gathered?" / "One of them put a
  hand on me today. Where are they gathered, Sheriff?" — **ask anytime, he
  refuses** (maintainer ruling, 2026-07): the row opens on the Talk alone, so
  the question can always be put; TRUST decides the ANSWER, not the
  availability. He answers the WHERE either way, because it costs him nothing
  and he does not know it (NARRATIVE §4). What he withholds is the HOW, his
  one card (`_vane_where_beats`).
  - **untrusted** (no discovery shared yet; the row stays askable):
    - (npc) "Gathered where? The school, the barn, the lodge. Then one night those rooms were empty, and I have not found the room they went to since."
    - (pi) "That isn't all you have."
    - (npc) "(He looks at you a while.) No. It isn't."
    - (npc) "You have been walking my town asking after one girl, and you have not put one thing in my hand. The ones who came before you were friendly too, son."
    - (npc) "Bring me something I can hold. Then we will see what I have got."
  - **trusted** (at least one discovery shared; files `the_how` and retires
    the row):
    - (npc) "Gathered where? The school, the barn, the lodge. Then one night those rooms were empty, and I have not found the room they went to since. So I cannot give you where."
    - (npc) "I can give you how. I have given it to nobody."
    - (npc) "I asked that question every night for a year. What I've got is one conversation. I'll spend it on you."
    - (npc) "After the rooms emptied, one of them came back up the road to this office and sat down in that chair. No name. I asked twice."
    - (npc) "Man had not slept in a week by the look of him. Hands going the whole time. He told me about his wife."
    - (npc) "She is in a county home down in Aitkin. Three years now. Doesn't know his face, doesn't know her own. He used to drive down every Sunday."
    - (pi) "Used to."
    - (npc) "He quit going. Said there was no sense in it yet. Said when the work is finished she will know him, and he wanted her to know him the first time she saw him."
    - (npc) "He cried the whole way through it. Never once got near the part of him that was certain."
    - (pi) "He wasn't there to confess anything. He was there to fetch you."
    - (npc) "He made the offer. Told me to name the thing I want most in this world, and come with him, and it would be waiting. I put him out. He thanked me for my time."
    - (npc) "You don't talk a hundred strangers onto one road. They weren't tricked. Every one of them was going toward something."
    - (npc) "What it was, who was holding it out, I never got closer than that chair. That's the piece that keeps my lights on at night."
- **Exchange `cache`** (avail: intro asked, cabinet not yet given;
  re-askable) — "Am I on my own out there?" / "If this goes the way it's been
  going, I'll be out there alone. Is there anything you can put in my hand,
  Sheriff?" — the same ask-anytime/refuse contract (`_vane_cache_beats`).
  - **untrusted** (the refusal never arms the ammo drop):
    - (npc) "I've got no deputies, no cell that holds, and a law nobody up here answers to anymore."
    - (npc) "What I have got, I am not handing to a man who drove in off that road last week and has told me nothing since."
    - (npc) "Work the case. Come back and show me you did. Then ask me again."
  - **trusted** (sets `vane_gave_cache` and drops the office ammo):
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
- **Framing** (`_pi_framing` base): "Hettie keeps one eye on the window."
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
- **Exchange `safe`** (avail: intro asked) — "Who is 'they'?" / "You said don't go where they tell me it's safe. Who is 'they'?"
  - (npc) "You haven't gone quiet. Like the others. Good. Then listen once."
  - (npc) "Don't trust the easy ones. The first to make peace, they went the soonest."
  - (npc) "That's the whole answer you're getting to that."
- **Exchange `others`** (avail: saw photo or volunteered memory) — "Others came asking before me." / "You've had people ask after faces before me. Haven't you?"
  - (npc) "I sold to the girl too. And the ones before her."
  - (npc) "None of them came back to buy again. You're the first."
- **Exchange `way_out`** (avail: heard the fold) — "Is there a way out?" / "If there were a way out of this town, would you tell me?"
  - (npc) "(She glances at the door before she speaks.)"
  - (npc) "If you find the way out. The real one. You don't owe this town a goodbye. Just go."
- **One-shot: the preacher** (avail: body found + met her):
  - "Heard about the preacher. I won't be saying his prayers in here. Don't ask me to."
- **One-shot: the Mara memory** (avail: shown the photo; hands over the tab, `grant_receipt`). **Rewritten 2026-07:** the "one thing worth the telling" preamble is gone (a character announcing she is about to say something important), and so is the "sad around the eyes, and polite with it" portrait, which contradicted her own answer to the photograph four lines earlier: *"Faces come through this shop. I stopped keeping them."* She either retains faces or she does not. What is left is a shopkeeper talking about her till.
  - "Your girl. She was a regular. Up till a few months back."
  - "Then she wasn't. Whole lot of them stopped coming in around the same time, her with them."
  - "Last of it, past the new year, she set her basket down half filled and walked out. Left it sitting there. Never came back for it."
  - *(The smiling exit and "It was the smiling I minded" were CUT, 2026-07: a
    smile the shopkeeper finds disturbing is a visible mark of claiming, and
    NARRATIVE §2 says there is none. Mara is grieving, not elated. She simply
    stopped coming in, and nobody clocked anything.)*
  - (if tab not yet lifted) "[c=dim]She goes into the bin under the till, digs a while, and comes up with a curled slip. Flattens it on the counter and turns it toward you. Her tab for the girl.[/c]" *(the BIN, not the spike, 2026-07: she is not keeping a shrine to the girl, it is refuse she has not taken out because nothing leaves this town, refuse included)*
- **One-shot: the newspaper OFFER** (avail: met her, carries newspaper;
  The favor-economy rework: she notices and offers, but the trade is the PLAYER'S
  call now -- one copy, six doors):
  - "[c=dim]Her eyes stop on the newspaper folded in your coat pocket. She goes very still.[/c]"
  - "What's the date on that. The date."
  - "[c=dim]You show her. April 14. Yesterday. You bought it before the drive north.[/c]"
  - "Yesterday's. We haven't had a paper through here since the trucks stopped."
  - "Leave it on the counter and take what's under it. The till's been empty since the new year. The shelf under it hasn't."
  - (ask) "The offer sits on the counter."
    - **Trade the paper.** -> "[c=dim]One load of cartridges across the counter. She's already reading yesterday's news like a letter from someone she'd given up on.[/c]" *(the barter: `newspaper_traded`, one load of cartridges, the copy spent)*
    - **Keep it. I've got somewhere for it.** -> "(She looks at your pocket a beat longer, then lets it go.) Suit yourself. The shelf keeps."
- **Exchange `paper`** (avail: offered before, still carrying, not traded) — "About that trade." / "That trade you offered. The paper for what's under the till."
  - (npc) "(Her hand is under the counter before you finish saying it.)"
  - (npc) "Counter. Now. Before I think better of what I keep under here."
  - (pi) "[c=dim]One load of cartridges across the counter. She's already reading the front page.[/c]"
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
- **Exchange `flock`** (avail: intro asked, not doomed) — "Tell me about the new folk." / "You watch this town from a pulpit. Tell me about the new folk. The congregation that isn't yours."
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
- **Framing** (`_pi_framing` base): "Toby watches the corn line while I
  think."
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
- **Exchange `home`** — "Anything strange at home?" / "How are things at home? Anything strange?"
  - (npc) "My mom hums a song that doesn't stop. She doesn't know she's doing it."
- **Exchange `church`** — "Do you go by the church much?"
  - (npc) "I don't walk past the church anymore."
  - (npc) "[c=dim]The door is open. They left it open.[/c]"
- **Exchange `way_out`** (avail: heard the fold) — "If I find a way out, I'll come get you." / "If I find a way out of this town, I'll come get you first."
  - (npc) "If you find a way out, don't tell me."
  - (npc) "[c=dim]I tried to lie yesterday. My mouth wouldn't.[/c]"
- **Exchange `holding_up`** (avail: `toby_told`) — "You holding up okay, kid?"
  - (npc) "Do you know what's wrong here, mister? Nobody will tell me."
  - (pi) "Not all of it. But I'm going to find out, and I'm going to make it stop."
  - (npc) "Am I gonna be okay?"
  - (pi) "You're gonna be okay. I promise. When I'm done, I'll come back for you."
  - (npc) "[c=dim]Okay. I believe you.[/c]"
- **Exchange `paper`** (avail: intro asked + carries newspaper; the favor economy, mercy) — "I brought the funny pages." / "There's a fat run of funnies in yesterday's paper. You want them?"
  - (npc) "The funnies? Whole ones?"
  - (pi) "[c=dim](You fold the front page under and away, and hand him the back of the paper.)[/c]"
  - (npc) "(He spreads it flat on the table with both hands, like a map of somewhere good.)"
  - (npc) "Calvin's still in it. He didn't stop."
  - (npc) "Can I keep it? Mom reads over my shoulder when I've got something. She doesn't hum when she's reading."
  - (pi) "[c=dim]He gets the funnies. The front page stays out of this house.[/c]"
- **One-shot: the bear** (`toby_dialogue`, avail: `toby_told` + reassured):
  - "[c=dim]He digs in his coat and holds something out with both hands. A stuffed bear, worn soft, a name stitched on the tag.[/c]"
  - "The lady gave it to me. The one in your picture. She said she couldn't keep it and she couldn't throw it out."
  - "It's the only toy in the whole town. If you find her... give it back? She should have it."
  - "[c=dim](You take a bear from a boy, and you promise. You do not let yourself read the name on the tag. Not yet.)[/c]"

## The Brimley chorus — Old Pell, Mrs. Calder, Royce, Garrick
- **Code:** `scenes/dialogue.py` `PELL_CONVO` / `CALDER_CONVO` /
  `ROYCE_CONVO` / `GARRICK_CONVO`, `chorus_dialogue`; each is AT HOME in
  their own house (`scenes/yards.py` `build_pell_house` / `build_calder_house`
  / `build_royce_house` / `build_garrick_house`) and carries their reactive
  beat there. Locals describe **failure, never pattern** about the
  roads (§4). Each carries the shared opener pair + one or two signature
  questions; the reactive stoop beats fire ahead of the menu, once each.

### Old Pell (blip_low)
- **Framing:** "Pell stays put on his step, arms folded."
- **Greet** (`pell_greeted`): (npc) "[c=dim]You're new. We don't get new. Nobody gets in. Nobody gets...[/c]" / (npc) "Hm. Well."
- **Opener intro:** (npc) "A detective. On my step." / (npc) "There's a foulness set over this whole town, son. You feel it more than smell it. Folk are tired under it, all of them, and sleep doesn't mend it." / (npc) "[c=dim]You're breathing it now too. Same as the rest of us.[/c]"
- **Opener photo:** (npc) "(He tips the photograph toward the light, slow about it.)" / (npc) "Could be she went by in the fall. Could be she didn't. The new faces all ran together after a while. Then they stopped going by at all."
- **Exchange `corn`** — "Nobody brought the corn in?" / "All that corn west of the river, dead and still standing in April. Nobody brought it in?": (npc) "That's Pell corn, son. Northernmost corn in the world, grown on this ground since 1894. My father took ribbons on it. So did I." / (npc) "Nobody cut it last fall. First harvest this town ever missed. It stood there and died standing." / (npc) "[c=dim]I don't look at the fields long anymore.[/c]"
- **Exchange `paper`** (avail: intro asked + carries newspaper; the favor economy, mercy, no item) — "I brought yesterday's newspaper." / "It's yesterday's paper, Mr. Pell. Out of the Cities. I'd like you to have it.": (npc) "(He doesn't reach for it. He reads the masthead where it sits in your hand, slow, like a man reading a headstone.)" / (npc) "April 14. Out there it got to April 14." / (npc) "I quit marking days, son. Nothing was coming that a marked day would bring any closer." / (npc) "(He takes it, folds it once, and tucks it under his arm the way you carry tools.)" / (npc) "There'll be a corn report in here somewhere. Prices. Somebody's weather. Somebody still growing, somewhere south of us." / (npc) "I believe I'll pencil today in when I get home. Just today. We'll see about the one after it." / (pi) "[c=dim]Nothing came back across for it. I wasn't waiting on anything to.[/c]"
- **Stoop beat `beat_pell_coal`** (1+ evidence, gated OFF once the paper has gone to him): "You've been digging at it. I can tell. It's on you like coal dust." / "Whatever you're finding out there, don't bring it up my step. I've got the calendar where I want it. Stopped. Some of us need it stopped."
- **Stoop beat `beat_pell_marked`** (after the paper; the favor-economy ripple, replaces the coal beat): "Wrote the date in this morning. April 15, plain as you like. First one since the winter." / "[c=dim]Can't say it did anything. Can't say it didn't. I'll write tomorrow in tomorrow.[/c]"

### Mrs. Calder (blip_mid)
- **Framing:** "Mrs. Calder watches the road past my shoulder."
- **Greet** (`calder_greeted`): (npc) "Oh. Is it you? ...Are you the one the place is set for?" / (npc) "No. No, it couldn't be you. Forgive an old woman her hoping."
- **Opener intro:** (npc) "(She takes your hand in both of hers before you finish saying it.)" / (npc) "Somebody's daughter. And somebody sent for, to bring her home. There's still such a thing. Isn't that fine."
- **Opener photo:** (npc) "(She holds it out at arm's length, the way the far-sighted do.)" / (npc) "No, dear. I don't know her. I've not seen her at my gate."
- **Exchange `plate`** — "Who's the place set for?" / "You asked if I was the one the place is set for. What place? Set for who?": (npc) "I lay an extra plate at supper. Have done a while now. Couldn't tell you who for. Someone's coming. I know it the way I know my own name." / (npc) "[c=dim]I'll know the face when it's across the table from me. Till then it would be unkind not to be ready.[/c]"
- **Stoop beat `beat_calder_unlatched`** (1+ evidence): "Closer now. Whoever the place is set for. An old woman can feel a knock coming before it lands." / "I've started leaving the door unlatched at night. It seemed... polite."

### Royce (blip_mid)
- **Framing:** "Royce looks down the road while I talk."
- **Greet** (`royce_greeted`): (npc) "(He looks you over a long moment before he says a word.)" / (npc) "You're the one who drove in. Off the north road, at night. Nothing has come up that road in months." / (npc) "I'd shake your hand, mister, but I don't know yet what you are."
- **Opener intro:** (npc) "A detective. Come up here to find somebody, and then drive her home." / (pi) "That's the shape of it." / (npc) "The finding I can't speak to. The driving home I can. Ask me about the roads sometime. Ask me what they do."
- **Opener photo:** (npc) "(He wipes his hands on his jacket before he takes it. Looks properly, corner to corner.)" / (npc) "No. A lot of new faces drove in this past year, same as anybody comes anywhere. Hers isn't one I know."
- **Exchange `roads`** (files the fold note) — "What do the roads do?" / "Everyone in this town talks around the roads. You drove them. What do they do?": (npc) "I drove it. River road, county line, every road out of Brimley. Same as everybody in this town with a set of keys. The corn handed me back every time." / (npc) "Same bend. Same bridge. Same town coming up in the windshield. And I'd swear to you on anything I never turned the wheel." / (npc) "[c=dim]I gave it up. Everybody did. There's no out to drive to.[/c]" / (pi) "[c=dim]Said flat. No fear left in it.[/c]"
- **Exchange `how_in`** (avail: roads asked) — "Something on your mind?" / "You keep looking at me like I owe you something. Say it.": (npc) "You came IN. That's what's on my mind. That road only ever hands a man BACK, and it carried you in easy as Sunday." → (ask) "He wants the answer more than he wants air.":
    - **"Tell him the truth. The road just drove."** → (pi) "I drove up at night. Radio went to static past the county line, and the road just drove. There was nothing to it." / (npc) "(Something goes out of him.) Nothing to it. Every driver in this town tried that same drive till they quit. For you it just drove." / (npc) "[c=dim]Then it wanted you in, mister. I'd chew a while on what that means for getting out.[/c]"
    - **"Give him nothing."** → (pi) "Same as anybody drives anywhere. I wasn't paying attention." / (npc) "Wasn't paying attention. (He laughs, and there's no fun in it.) No. I don't suppose you were." / (npc) "[c=dim]Sure you weren't. (He looks back down the road.) Nobody drives that road easy. Nobody but you.[/c]"
- **Exchange `paper`** (avail: intro asked + carries newspaper; the favor economy, escape-hope: pays in his hoarded batteries + his best road, testimony filed as a note) — "I brought yesterday's newspaper." / "I carried yesterday's paper up with me. April 14, off a Cities rack. It's yours.": (npc) "(He checks the date before anything else on the page. Then he checks it again.)" / (npc) "Printed yesterday. Yesterday this page was OUTSIDE. Presses running. Trucks rolling. Some kid throwing this at a porch." / (npc) "I'd about talked myself out of all that still being there." / (npc) "Hold on. You're not walking off with nothing for it." / (npc) "[c=dim]He digs under his truck seat and comes back with a paper sack, heavy for its size. Flashlight batteries, loose, a careful winter's hoard.[/c]" / (npc) "And hear this, it's the only thing I own worth telling. River road, south. That one held longest before it handed me back. Two bends past the bridge. If any road out of here ever remembers where it goes, it'll be that one." / (pi) "[c=dim]He walked off with the box scores open. Lighter on his feet than I've seen him.[/c]"
- **Stoop beat `beat_royce_throat`** (2+ evidence): "You're still here. Course you're still here." / "I keep turning it over. Every road out of Brimley hands you back. Except the one that carried you in. If a door only opens the one way, mister, it isn't a door." / "[c=dim]It's a throat.[/c]"

### Garrick (blip_mid)
- **Framing:** "Garrick leans on the well and waits."
- **Greet** (`garrick_greeted`): (npc) "Seen you already, son. Door to door, both banks. I sit this square most of the day. Everything in Brimley crosses it sooner or later."
- **Opener intro:** (npc) "Folks who ask questions in this town go quiet. Real quiet. I'm not threatening you, son. I'm counting for you." / (npc) "[c=dim]The Sheriff will tell you to head on home. He knows you can't. He can't either.[/c]"
- **Opener photo:** (npc) "(He barely looks at the photograph. He looks at you instead.)" / (npc) "Faces pass this well all year. Maybe hers did too, with the new folk. They kept to their own side of things, and then they stopped being seen at all."
- **Exchange `roads`** (files the fold note) — "Any safe way around this town?" / "Is there a safe way to move around this town? You watch it all day.": (npc) "Stay on the roads. People who go off the roads come out wrong-side of where they went in. I've watched it happen to better walkers than you." / (npc) "And don't put your faith in a road going where it went last week. Make for the county line and you'll be back at this well by supper." / (npc) "[c=dim]Go on home, son. ...Oh. Right. None of us can.[/c]"
- **Stoop beat `beat_garrick_quiet`** (after the preacher's body is found): "The reverend's gone quiet. Any other week you'd hear him clear from here, worked up over something or other." / "Nothing out of him for days now. Man spends his life raising his voice, then nothing at all." / "You go by and look in on him, son. Somebody ought to."

### Hettie's stoop (the homebody at the shop step, `scenes/yards.py` `build_shop_yard`, via `dialogue.doorstep_voice`)
- "Still open. Always open. The shelves don't empty anymore. Have you noticed." / "No deliveries. In a while now. But we manage. We always." / "I keep the lights on. So they know. Someone's keeping them on."

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
- **Framing:** "She stands out of the rank, waiting." **Leave option:** "Say
  nothing."
- **Greet** (`mara_confront_greeted`; the second beat is the reveal's stage
  caption, landed as the mask comes away):
  - (npc, listed "One of them") "My father sent you. Of course he did. He never could let a thing stay lost."
  - (npc, the listing turns "Mara") "[c=dim]She lifts the mask away. The face from the photograph, gone thin.[/c]"
  - (npc) "Tell him what I told him at the start. I'm not lost. I've never been this close."
  - (npc) "[c=dim]I was not taken. I was answered, and I went to it gladly.[/c]"
- **Exchange `leave`** — "Come with me." / "Come with me, Mara. Right now. I'll get you out.":
  - (npc) "Out."
  - (npc) "Nobody leaves, mister. Nobody has left since the winter. You have walked the roads by now. You know it better than the ones who quit trying."
  - (npc) "And why would I go. He is right there. A few feet of earth, and he is right there."
- **Exchange `way_out`** — "How do I get out?" / "Then tell me how I get out. There has to be a way out.":
  - (npc) "There isn't. We can't. None of us can."
  - (npc) "It is not a wall, mister. A wall has a far side. Every way out of this town is a way further in."
  - (npc) "Go home, while the town still lets you think you can."
- **Exchange `father`** (ends the confrontation; sets `mara_lucid`) — "Your father is waiting." / "Walter is waiting, Mara. Your father. He picks up the phone every time it rings.":
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
  - (npc) "[c=dim]She lets go of your coat, turns, and kneels back into the rank. Her hands find the dirt. The chamber settles, as though nothing rose.[/c]"
- **After the confrontation** (`_mara_voice` on a re-press): (narrator)
  "[c=dim]She has gone back to the kneeling. She won't look at you
  again.[/c]"
- **The lure-chain caption** (queued behind the tableau, only if the PI
  lived the dream, `flashback_seen`; the `NARRATIVE.md` §1 fence, felt once, never
  stated): (narrator) "[c=dim](A door in your sleep, a year back. Then a
  grief job you had no reason to take, and an itch that drove you north
  with it.)[/c]" / "[c=dim](And every road in handed you here. To her,
  kneeling. You start the arithmetic of that, and you put it down. Some
  sums you don't finish standing up.)[/c]"
- **The rite-holder's closer** (the staging's last word, once the room
  settles): (narrator) "[c=dim]The one bowed at the altar's foot never
  paused. Not when they rose. Not at her name. Its share of the rite is the
  whole of it now.[/c]"

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
    "[c=dim]Well shit, this town really doesn't have a Midwestern welcome
    at all.[/c]"
  - The **`the_talk` case note**: "One of them put hands on me today. Told
    me to go back to my room. Told me to run." / "Well shit, this town
    really doesn't have a Midwestern welcome at all."
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
- **`maras_receipt`** (`grant_receipt`): "A store tab out of the bin under
  Hettie's till, headed 'M. Blaine' in her hand." / "Matches, canned milk, bread, kerosene,
  lamp oil. The same short list, week on week, autumn through the new year."
  The list is the whole entry. **"She lived here" was CUT** (maintainer
  ruling, 2026-07): that is the player's connection to make, and a tab of
  lamp oil and canned milk week on week makes it without the book saying so.
  "Most of a year" was also flatly wrong, since Mara drove north in the fall
  of 1993 and the present is April 1994.
- **`maras_record`** (`grant_record`, `scenes/dialogue.py`; the WARM handover
  is Vane's photo opener in Part A, the office records drawer only the
  fallback once he is dead or hollow): "A booking slip in the Sheriff's
  records. Blaine, Mara." / "Held a night for a disturbance on the main road,
  shouting at the sky. Released at dawn, no charge filed." Pickup notice:
  "Her booking slip."
- **`the_first_one`** (`_dispel_watcher`, `systems/threat_mixin.py`; note,
  fired the FIRST time he sees a Watcher off and **never again**): "Something
  stood at the edge of the light and did not move while I looked at it." / "I
  did not look away. Could not tell you why that was the thing I decided to
  do." / "Whatever was lit behind the eyes went out, and the rest of it went
  after them." / "I have been awake a long time and this town does not agree
  with me."
  > **The silence after it is the design.** They keep opening for the whole
  > run and he never writes about them again. An arc where he notices he has
  > stopped being frightened would be the game announcing that he changed; a
  > notebook that simply stops recording them lets the player notice it. He is
  > confused and tired and ordinary throughout, not hardening. Seeing one and
  > staring it out is ONE event, so the entry lands on the dispel, not the
  > spawn. Guarded in `tests/flow.py`.
- **`the_disturbance`** (`_vane_night_told`, note; his account of the
  detention night, a STATEMENT so it never counts): "Vane booked her the
  eleventh of December. Middle of the main road at night, head back, shouting
  at nothing he could see. Not drunk and not hurt." / "He came late to it.
  One of the men who sits the square fetched him, and watched the whole of it
  before the law got there."
- **`maras_journal`** (`_barn_update`, `scenes/interiors.py`; a walk-over
  pickup, fires the door-dream ON PICKUP, files quietly): "A notebook,
  shoved down behind the workbench. You know the hand. It's hers." / "Her
  journal. Three leaves, in a hand that gets calmer as it goes:" / "\"They
  told me grief would pass. It did not pass. It only learned my name.\"" /
  "\"I have started to dream of a door. It is not frightening. It feels
  like being remembered.\"" / "\"They dreamed the same door, every one of
  them. We are digging down to it together now. I am not lost. I have never
  been this close.\"" Pickup notice: "Her journal."
- **`maras_dig`** (`build_works_scriptorium._interact`, `scenes/well.py`):
  "A leaf pulled from a copying desk. The Sign, inked over and over down
  the page." / "The hand is hers. The same as the journal, the same as the
  letter." / "No captive draws this." Pickup notice: "The Sign, in her
  hand."
- **`maras_room`** (`build_maras_room._interact`, `scenes/well.py`; the cot
  in her cell, grants the robe + the unsent letter): "Her cell. A cot, a
  burnt-down candle, a cult robe on a peg, worn soft. Chosen." / "Folded
  inside the robe: a letter to her father. Stamped, never mailed. It opens
  \"Dad.\"" / "\"There was going to be a baby. A boy. I never told you, and
  then I could not find a way to tell you the rest. I almost decided
  different, right at the last, and then I wanted him more than I have ever
  wanted anything. He came still.\"" / "\"I keep finding ways it was my
  fault. I know that isn't sane. I keep finding them anyway. I wanted a son
  the way you wanted a daughter, Dad. Somebody to wait up for.\"" /
  "\"Don't come after me. I'm not lost. I've never been this close.\" It
  stops there. No signature." / "A journal page, weighted flat under the
  candle: \"I was the last one in. The rest had been here since the summer,
  and still they looked up when I came down the road like they had set a
  place for me. Whatever it cost them to give in, it cost me next to
  nothing. I was driving north before I had even finished dreaming it.\"" /
  "This is a room someone moved into. Blaine hired you to bring her home.
  She was already home." / "The letter is addressed to a man you cannot
  reach. You are the only one who will ever read it."
- **`the_sign`** (`_take_mask`, `scenes/well.py`; the Mask off the altar,
  the keystone item, not a counted beat): "On the altar, beneath the daubed
  Sign: a mask. Pale as a drowned face, the eyeholes black." / "Every
  scrawl in this place is a flat copy of it. This is the thing itself." /
  "You lift it. Lighter than it should be, and warm. It knows your hands."
  / "His face. You're holding His face." Then the `descent_mask` temptation
  (the descent-voice track below).
- **`the_ledger`** (`basement_interact`, `scenes/lodge.py`; a town NOTE,
  never case-evidence): "Boxes of the Lodge's old registers, years deep,
  carried down here as each book filled. You lift the top one out and start
  back through it." / "Names signed in, in the Clerk's hand, and a date
  beside each one where they settled up and left. Then those dates just...
  stop. The last anyone signed out was a year back. Every name since signs
  in and never out." Closer if Sable gave cellar permission: "[c=dim]He let
  me down here without a blink. A year of guests, and the clean book
  upstairs starts right where these leave off. I'll keep it in mind.[/c]";
  else: "[c=dim]Probably nothing. A clerk who got lazy, dropped the habit.
  ...Still. A year of guests, and the clean book upstairs starts right
  where these leave off. I'll keep it in mind.[/c]" Re-examine: "[c=dim]A
  year of names that never signed out. You've read enough of them.[/c]"
- **`the_fall`** (`build_depths_antechamber._interact`, `scenes/depths.py`):
  "There is no way back above you, and you are not hurt. Cut stone, worn
  smooth by years of feet that came this way before you."
- **`threshing_floor`** (`build_depths_threshing._interact`): "The yield,
  raked into low heaps: grain, all of it, tithed down from the fields above."
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
  card. One of them came back up the road to his office after the rooms
  emptied and sat down. No name. Hadn't slept." / "Wife in a county home
  three years. Doesn't know him. He quit driving down to see her. Said she
  will know him when the work is finished, and he wanted her to know him the
  first time." / "Then he put the same offer to Vane. Name the thing you want
  most, come along, it will be waiting." / "Nobody was argued into this. Every
  one of them was promised the one thing they were starving for.[/c]"
- **`the_congregation`** (`_mara_voice`, note): "Mara, kneeling with the congregation. Turned. There was never anyone to bring back."
- **`the_dream`** (`_log_dream_entry`, note; canon-guarded "a year", no
  recurrence): "Her journal put me back inside the one odd dream. A year
  back, before any of this. I'd forgotten I had it." / "A door standing
  open in the dark. No wall around it, just the frame, old dry wood." /
  "Light behind it the colour of old gold, breathing in and out like
  something asleep." / "I walked up. I looked in. For a blip something
  looked back, met my eye, and then it broke." / "I never reached it. One
  dream, a year ago, and it never came again. So why do I know this place."
- **`the_rite`** (`_finish_rite`, note; the descent-dream completed): "I went
  back into the dream. On purpose, this time. The same door, the same
  light under it, a year old and not one day faded." / "I walked up to it
  the way I never did in my sleep. It knew me. It let me in." / "When I
  opened my eyes I was at the bottom of the shaft, in the dark, the mouth a
  coin of grey light far above. No rope carried me down. I do not let
  myself think about what did."
- **`the_turning`** (`_tick_king_roam`, note; 2 evidence, the telegraph):
  "Something at the end of the north road turned to face me. It has not
  moved. It does not need to yet." / "It knows my face. Like a draft off a
  door left open somewhere behind you."
- **`the_breath`** (`_tick_king_roam`, note; 3 evidence, the arm grace):
  "The road has gone still, all at once. No wind, no birds. The whole town
  holding its breath." / "I have what I came for. I should not be standing
  in the open when it lets that breath go."
- **`cult_calling`** (Scriptorium, note): "Every hand different. Every one
  of them grateful. I keep waiting for the page where somebody admits they
  were tricked. It isn't here." Pickup notice: "The Calling. Their own
  testimony."
- **`cult_bargain`** (the Sump, note): "They write about the bargain like
  a debt almost paid off. Not one of them can say what they put up for it,
  only that the last payment is close. I never took a confession this
  happy." Pickup notice: "The Bargain. Their own testimony."
  (`cult_digging`'s pickup notice: "The Digging. Their last pages.")
- **`the_bear`** (`toby_dialogue`, note; the loan): "The kid put a stuffed
  bear in my hands. Homemade, a name sewn on the tag. Said the girl in the
  photo gave it to him, that she couldn't keep it and couldn't throw it
  out." / "He asked me to give it back to her, if I find her. I said I
  would. I have carried worse lies than that one lighter."
- **`showed_the_clerk`** (`_sable_showed_photo`, note): "I put her face on
  his desk. He looked at it a long while, smiling the whole time, and told
  me nothing at all." / "I had the feeling he did not need the picture."
- **`the_invitation`** (`_sable_give_invitation`, note): "Sable kept an
  envelope under the register. Since the winter. Handed it to me like a
  room key." / "The guests who never signed out left it for him, for the
  day he was ready. He gave it away instead. Says the desk needs him." /
  "It reads like scripture and gives directions like a flyer. The school
  first, it says. Where they slept."
- **`ready_for_the_desk`** (`_ready_for_the_desk`, note; 3 canonical beats
  on the surface, Invitation not yet held, once): "[c=dim]The clerk has
  been holding something for me since I walked in.[/c]"
- **`the_procession`** (`_candles_interact`, `scenes/depths.py`, note): "A
  candle line tended half a mile under Brimley, wax on old wax. They filed
  to their rite the way other towns file to Sunday service. Unhurried.
  Certain."
- **`works_cistern_seen`** (`_vats_on_enter`, `scenes/well.py`; the dig
  breaking into the river): "[c=dim]The water runs on, downward, and does
  not echo back.[/c]"
- **The newspaper allocations** (the favor economy, `_paper_given`; ONE fires per
  run, whichever door the copy went through; all notes, never evidence):
  - `paper_royce`: "Spent the paper on Royce. He paid in hoarded flashlight
    batteries and the one road that held longest: river road south, two
    bends past the bridge." / "His account, not mine. But he would know."
  - `paper_pell`: "Gave Old Pell the paper. He said he'd pencil today into
    his calendar. He'd stopped marking days at all." / "No trade. Didn't
    want one."
  - `paper_toby`: "Gave the kid the funny pages. His mother reads over his
    shoulder, and she doesn't hum while she's reading." / "Best price I
    got for it all day."
  - `paper_sable`: "Left the paper with Sable. He squared it on the desk,
    unopened, and thanked me for the house." / "The whole town is starving
    for word from outside. He is not."
  - `paper_hettie`: "Traded the paper across Hettie's counter for a load
    of cartridges." / "She was reading it before I reached the door."
  - `paper_vane`: "Gave the sheriff the paper. Kurt Cobain on the front
    page." / "He didn't look up from it again."
- *(Every case-notebook write, evidence and note alike, is now transcribed
  above or in its speaker's Part A section; see Coverage.)*

## The Casebook: the PI's running notebook

The Case tab is ONE RUNNING DOCUMENT (`ui/journal_ui.py`; maintainer ruling,
2026-07). Everything he writes down goes in in the order he wrote it, headed
if it is a thing he FOUND and unheaded if it is a thought he had, and nothing
is ever reordered, merged or overwritten. Up and down turn the leaf.

- **`the_case`** (the intake, seeded at run start): "Client: Walter Blaine,
  Minneapolis. Wants his girl home." / "Subject: his daughter Mara, 24. Drove
  north in the fall, quit calling home by the new year, and that was the last
  of her." / "I told him what he already knew. She's grown, and nobody makes a
  grown woman come home who won't. \"See what you can do,\" he says.
  \"Please.\"" / "So I went looking. Trail ends in Brimley. Find her, put her
  father's word to her, let her decide. That's the job." / "I don't leave a
  case open. Whatever's up here, Walter gets his answer."

**What he concludes, written down ONCE each** (`_THEORY_THOUGHTS`,
`_tick_theory_notes`). Each lands the moment he reaches it and stays on its
page for the rest of the run. They render with no heading, because a
conclusion he jots is a line in the flow rather than a titled find.
> **The three CASE reads are CUT** (maintainer ruling, 2026-07): "A resident,
> not a drifter", "She lived here and came apart here", "She wasn't taken, she
> walked to it willing", and the SON read ("A boy, Sam. She gave his bear to
> the one live kid here. His name breaks her"). Each was the conclusion its own
> evidence had been built to earn, handed over instead of left; the son one was
> worse, because "his name breaks her" had the PI predicting a scene he has not
> reached. **He never solves Mara on the page.** What he writes down is the
> town. The bear still DETONATES, in the item's own text once the letter is
> read (`systems/items.py` `effective_desc`), which is where that beat always
> lived.

- **`theory_fold`** (`crossed_a_fold`): "And the town won't let go. I've felt
  the ground fold back under my own feet. Her or not, how do I get out?"
- **`theory_robes`** (has actually met them): "The robes run this. If anyone
  can shut it off it's them, and the only way out runs through all of them. I
  hate it." **This is the WRONG read, and the game never corrects it**
  (NARRATIVE invariant). Because the book never rewrites itself, it stays
  legible on its page for the whole run, including after he learns better.
- **`theory_mask`** (holds the Pallid Mask): "Got the mask. And I know it
  clean: carry it out and the town lets me go. Down doesn't come back. God
  help me, I want out."

> **The TIMELINE is CUT** (maintainer ruling, 2026-07). It was a derived page
> that re-sorted his finds into Mara's chronology, which is precisely the
> connection the player is meant to make. **He writes the dates down as he
> finds them** (the booking slip's "Dated the eleventh of December", the
> registers' "a year back", the receipt's year of staples, the gas receipt's
> July) and the arithmetic of this-then-this-then-this belongs to the player.
> The old `_current_lead` strings remain DEAD CODE, rendered nowhere.

## The descent-voice track
`systems/game.py` `_DESCENT_VOICE`, keyed to descent milestones. The PI's own
diary-voice runs **first person** (chalk_surface, descent_dig, chalk_deep);
the intruding lure runs **second person** (descent_leave, descent_mask) — a
deliberate self-vs-lure split, not a POV wobble. Fires as an on-screen beat +
a case note.
- **`chalk_surface`** beat: "[c=dim]A door, chalked onto the floorboards.
  The size of a real one, and careful about it. A frame laid flat, like you
  could step down through it. ...Kids do stranger. I wrote it down
  anyway.[/c]"
- **`descent_mask`** (the temptation) beat: "[c=dim]His face, in your
  hands. Light as folded paper, cold, and it knows your grip.[/c]" /
  "[c=dim]The pale mask hums in your hand.[/c]" / "[c=dim]And you KNOW it,
  the way you know a thing in a dream. Carry this, and the town opens. The
  roads let you out.[/c]" / "[c=dim]The names, the register, the girl her
  father wanted found. You have enough. You could be in the car by morning.
  You could just go.[/c]"
- **`chalk_deep`** beat: "[c=dim]The drawn doors are behind my eyes now,
  every time I shut them. Everything in me is pulling for the surface. The
  way back is shut. So down.[/c]"

The full track, each entry an on-screen **beat** plus a fuller case
**note**:
- **`chalk_surface`** note: "Someone chalked a door onto the barn floor.
  Full size, and they weren't careless about it. Jambs, a lintel, even a
  knob. Drawn flat, like a thing you'd step down into. Around nothing. Bare
  plank under it." / "Could be a child. Doesn't read like a child. It reads
  like practice." / "Filing it. Probably nothing. I've filed nothing before
  and been wrong."
- **`descent_dig`** (the Sorting Hall) beat: "[c=dim]Their whole lives,
  sorted and shelved down here. ...My pen won't hold still. That's
  new.[/c]" Note: "This is no cellar. It's a dig. Room after room of it,
  going down, and it cost them a year of hands." / "Everything they owned
  is catalogued in here. Coats, photographs, a child's shoe, folded. Set
  down neat, the way you leave a thing you mean never to need again." /
  "I've worked bad rooms. This is the first one to put a shake in my hands.
  I do not like how far down I am."
- **`chalk_works`** beat: "[c=dim]Down here it's nothing but the drawn
  doors. Walls, floor, over each other. None of them open onto anything.
  They knew that. They kept drawing.[/c]" Note: "The whole dig is papered
  in them. Chalk doors on chalk doors, hundreds, going down with the
  tunnel." / "Not one opens onto anything. They knew. You can see them
  pressing harder, trying to get it right, like the right one would finally
  come loose from the wall." / "I came down for a missing girl. I keep
  checking over my shoulder for the way back up. Still open. I say so to
  myself more than a steady man would."
- **`descent_leave`** (reading The Calling seeds the want-to-leave) beat:
  "[c=dim]You turn through the bound notes. Their own hands, page on page.
  ...You've got plenty here. More than plenty.[/c]" / "[c=dim]A case this
  size, you don't keep digging it. You carry it up and let the people who
  can drop a roof on this town do the rest. Time to climb out.[/c]" Note:
  "Read the bound one. Their own notes. There's enough in this town to hang
  it twice over. Past enough." / "No call to go deeper. You don't work a
  case past the point it's made. You bring it up to the ones who can finish
  it." / "Climb out. Make the call. Let the law come down on Brimley like a
  roof. That's the job. [c=dim]That's always been the job.[/c]"
- **`descent_mask`** note: "I have the mask off the altar. His face. Pale
  as a drowned man, cold, light as paper." / "And I'm sure of a thing I've
  no right to be sure of. This is the way out. Whoever carries it, the town
  lets go." / "I have enough for any court that would hear me. I could
  climb out and never look down again." / "I want to. God help me, I want
  to. I'm setting it down here so I remember that I did."
- **`chalk_deep`** note: "The stair shut the way behind me when it opened.
  No way back up. Only down now." / "Everything in me is pulling for the
  surface. The car, the road, the county line. And there is nothing left to
  climb. So I go down, because down is the only direction left." / "I shut
  my eyes and the chalk doors are still there, drawn on the inside of them.
  I could draw one from memory now. [c=dim]I don't want to know that about
  myself.[/c]"

## The fold notes
`systems/narrative_mixin.py` `_fold_mentioned` (a local names the looping
roads) and `Game.cross_fold` (`_note_fold_portal` = a visible pane, awe;
`_note_fold_loop` = the second silent loop, the creep). The perceptible
spatial fold only (looping roads), never the door or the cosmology.
- **`the_fold_told`** note (`{name}` is whoever told him): "{name} told me
  you can't drive out of Brimley. The roads loop. Make for the county line
  and the corn hands you back where you started." / "Said it flat. The way
  you'd say it always rains here. No fear left in it. A fact they've all
  stopped arguing with." / "A whole town doesn't go strange like that over
  a lie. [c=dim]And my own engine turned over and died at the lodge
  steps.[/c]" The spoken reflection (skipped for convo exchanges, which
  carry their own closing beat): "[c=dim]{name} says there's no driving out
  of here. The roads loop, the corn hands you back. Said it like
  weather.[/c]" / "[c=dim]A town doesn't talk like that about nothing. And
  my car died at the steps.[/c]"
- **`saw_the_door`** note (`_note_fold_portal`, the first VISIBLE pane
  crossed): "Saw the damnedest thing I ever have. A gold rim, shaped like a
  door, standing in the open air." / "Where the other side should be, it
  just goes somewhere else. And I stepped through it, on foot. I did." /
  "No word for it. The car dying I could tell myself a story about. Not
  this."
- **`walked_in_circles`** note (`_note_fold_loop`, the SECOND silent loop;
  the `%s` is corn/trees/road by where it caught him): "Couldn't
  get through the %s. It just kept going." / "Figured I'd forgotten how
  to walk a straight line, till the same landmarks came round a second
  time. And the way back's too short for how far I went." / "This is
  concerning. Writing it down so I quit telling myself I imagined it."

## The dream & the threshold recognition
- **The journal door-dream** (on `mom_notebook` pickup): wordless cutscene,
  no text; files `the_dream` (above).
- **The threshold recognition** (`scenes/depths.py build_threshold`, if
  `flashback_seen`): "[c=dim]You have stood here before. In sleep.[/c]"
  then the `the_doorframe` beat: "A doorframe with no wall."
- **Stepping through without the Mask** (once): notice "You step through
  the frame. You are standing in the same room. It is only a frame, and
  cold."

## The school rite (`scenes/threshold_extras.py`)
The Invitation's directions, walked: incense at the commune's cold indoor
fire, then the last chalk door on the board.
- **The chalk stub** (pickup): "A stub of chalk off the teacher's desk."
  **The incense** (pickup): "Dried incense, left beside a cot."
- **The fire, nothing to burn:** "A fire burned flat on the floorboards.
  Sweeten the air, the sheet says. You have nothing to burn." First look:
  "They burned a fire inside, on the floorboards, the way squatters do."
- **Lighting the incense:** "[c=dim](You set the bundle on the cold ash and
  light it. The smoke goes up in one straight line, sweet and cold, and
  then it stops going anywhere. It hangs.)[/c]" / "[c=dim]The room smells
  the way it must have smelled every night they slept here.[/c]"
  Re-examine: "The smoke hangs in the room and does not drift."
- **The board, before the air is sweetened:** "[c=dim](The chalkboard.
  Under a child's faded lesson, the same door is drawn over and over,
  smaller and smaller, to the corner.)[/c]" / "[c=dim]The sequence stops
  one door short. The smallest one was never drawn. The sheet in your
  pocket says the air comes first.[/c]" With no chalk: "The last door wants
  drawing. You have nothing to draw with."
- **Drawing the last door:** "[c=dim](The sequence stops one door short of
  the corner. You set the chalk where the last hand left off and draw it
  once more. Smaller. The smallest one.)[/c]" / "[c=dim]The chalk goes
  through the board like a knife through paper, and behind you the smoke
  leans toward the old fire.[/c]" / "[c=dim]Something stands up in the
  middle of the room.[/c]"
- **The board, after:** "[c=dim](The lesson, the shrinking doors, and at
  the corner your own hand, the smallest one. It is the only door on the
  board that is open.)[/c]"

## The mine mouth & the descent gates
- **The descent** (`_grove_interact`; the mine mouth in the grove -- a green
  HILL with a dark stone ADIT cut into its south face, timbered over, the shaft
  dropping away just inside).
  **REDESIGNED 2026-07: the descent is the physical mine now, not a
  rift-portal, and it is NOT re-gated at the grove** (the way here was already
  earned upstream, Sable's Invitation at 3 evidence then the school rite). E at
  the mouth is a two-press commit: "[c=dim](You stand at the mouth of the mine.
  A few feet in, the floor drops away into a shaft, and the cut haul rope hangs
  into it, frayed, a body's length, then nothing.)[/c]" / "[c=dim]You have
  stood here before. A year ago, asleep, at a door you never reached.[/c]" /
  "[c=dim](Press again to go down.)[/c]" The second press plays the
  door-dream, and the dream IS the descent (the mine carries the PI down to
  the works). After the descent seals, the mine is dead: "Cold air climbs out
  of the mine. It is done with this place." (The old evidence-gated rift beats
  over the dead fire -- the thread of gold, the light that would not take your
  weight, the fire ready for something you were never given -- were CUT with
  this rework.)
- **The circle holds** (a surface exit after the rite, once): notice "The
  way you came does not open. The circle holds. There is only down."
- **The shaft-floor pane, no Mask** (once): notice "The pane stands where
  the rope hung, and it does not open. It is waiting on a face."
- **The SPREAD counterweight** (`well_bottom` on entry, Mask in hand, not
  sealed, once): "[c=dim]The pane stands where the rope hung, and with His
  face in your hands you can feel it holding the door open for you. Up is
  real again. The roads would run.[/c]" / "[c=dim]And under your feet the
  dig runs the other way, down to the thing this whole town kneels to. You
  could end it where it starts. Nobody is coming down here after you to do
  it instead.[/c]"
- **The Deepest Face** (`scenes/well.py`): no powder: "[c=dim](The dig
  stops here. Dead earth, picked at and given up on. You put your ear to
  it, and you would swear there is a hollow behind it.)[/c]" / "A charge
  would open it. A dig like this keeps powder somewhere." Powder but no
  Mask: "[c=dim](You lay the charge out, and stop. The thing all of this
  kneels to is still down here somewhere, and you have not seen its
  face.)[/c]" / "Finish the sweep first. Then the wall." The laid fork
  (first press): "[c=dim](You set the charge against the last few feet of
  earth and run the fuse back. Your hands are steady. You note that the way
  you note evidence.)[/c]" / "You have enough. The register, the names, the
  Preacher, the girl her father sent you for, and His face in your hands.
  The way up answers it. The car answers it. You could climb out and let
  the world learn His name." / "[s=slow]Or you light it, and you cut this
  thing off at its source.[/s]" / "[c=dim](Your thumb finds the striker.
  Once it catches, there is no way back up from where this goes.)[/c]" The
  blast (second press): notice "The charge takes the wall, and the floor
  goes with it. You drop with the stone into a dark the dig never reached."
- **The powder** (the Sump): notice "Blasting powder, kept dry on the
  ledge. Enough to open a few feet of dead earth."
- **The car** (`scenes/lodge_yard.py`, without the Mask): notice "You turn
  the key. The engine catches, and catches, and dies. Brimley won't let the
  car go. Not with empty hands."

## The endings (captions; flow-guarded)
- **SPREAD (`escape_alone`,** the drive-out cutscene): "You turn the key
  and the engine roars to life." / "You drive down the highway further than
  you could before, and near the edge of Brimley." / "The mask shifts in
  the seat, as if to look at you." / "You gaze into the mask's deep sunken
  eyes." / "And for the first time in twenty years, you feel. All of it,
  all at once. You have to stop the car because you are laughing, or
  weeping. You can't tell. You don't care. It's back." / "When you drive
  on, your hands are steady and the road south is wide open. For the first
  time in your life, you know exactly where you are going." / "Everyone
  will know."
- **SEAL (`seal_threshold`,** after the live warp): "You stood at the
  Threshold and held the Mask out before you. You took the step." / "The
  moment it crossed, you were pulled through with it. And Brimley came
  after, every acre." / "The sky holds black stars. The twin suns peek at
  the horizon." / "You look up as the door slams shut." / "Rage
  approaches." then the wordless tableau.
- **BREAK (`rite_broken`):** wordless by design. No text.

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
  Menu labels: **"Take the pistol"** (drops once taken), **"Take the
  flashlight"** (drops once taken; the PI's own light moved here from the
  woodshed in the 2026-07 light pass), **"Read the case file"**, **"Step
  back"**. Reading hint: "(walk away to close)". Taking the flashlight
  fires the notice "Your flashlight. Press [F] in the dark, but light
  draws the eye."
  - **The case file** (`_tableau_read_case`, sets `read_journal`): "CLIENT:
    Walter Blaine. Wants his daughter found and brought home." / "MARA BLAINE,
    24. Cut ties, drove north, quit calling home. The trail runs cold at
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

## Notices with story in them (one-line, `show_notice`)
The one-line system notices that carry fiction rather than controls (the
pure control/feedback layer stays indexed; see Coverage):
- *(Entering cover is WORDLESS -- 2026-07 playtest ruling. The old corn
  and shadow one-shot teach notices were CUT; the `hide_enter`/`hide_exit`
  cues and the visible cover itself are the only tells.)*
- **The gun at 3+ evidence:** "The shot barely staggers it now. You know
  too much. They won't die for you anymore." **The axe's first hit (the
  stun teach, once):** "You knock it back. It won't stay down. Run."
- *(The cult-dark beam-off notice, "The beam dies the moment it leaves the
  lens...", was CUT with the 2026-07 light pass: light works everywhere
  now; the deep's dread is what light costs and attracts.)*
- **The church bell:** "You haul the rope. The bell swings out over the
  town." / "The bell is already swinging." / "The bell stops mid swing."
- **The King's portal:** "The air begins to tear. Get out of sight." / "The
  air tears open. He is coming through."
- **The Kneeling Hall's crossing** (`scenes/depths.py`): "The kneeling rise
  together. Not startled. Called."
- **Listening at a door:** "You press your ear to the door. Quiet."
  **A barricade giving way:** "The pile splinters apart." / "The boards
  splinter away."
- **F5 pressed** (there is no save-by-hand; evidence is the checkpoint):
  "The case keeps itself. Every find writes it down."

## Prop examines
Transcribed as the narrator sweep reaches each. The
ones landed so far:
- **the Arcadia guest-hall LOCKED doors** (`build_lodge_hall._hall_interact`,
  `scenes/lodge.py`; every locked 'l' door in the guest wing): "[c=dim](Locked.
  A row of them, all the same, all shut.)[/c]" (the uncanny hotel of shut
  rooms kept ready for guests who won't come, NARRATIVE §4).
- **the procession candles** (`build_depths_procession._candles_interact`,
  first read): "[c=dim]A line of candles down the dark, burned to coins.
  Each one stands in older wax, and older wax under that.[/c]" /
  "[c=dim]They walked this in single file, carrying light. Nobody hurried.
  The wax says nobody ever hurried.[/c]" Re-read: "[c=dim]The wax holds its little
  lights steady. Nobody hurried here. The wax says nobody ever
  hurried.[/c]" (files `the_procession`, above)
- **the emptied church** (`old_man_house_on_enter`, after `preacher_doomed`):
  "[c=dim]Mud on the aisle boards, dried in a line toward the door. River
  mud.[/c]" (the atmospheric "lectern stands empty / stove is cold" line was
  cut, play-notes; the river-mud pointer stays, it is the only in-church
  signal toward the riverbank body).
- **the payphone** (on the square): examine **CUT** (play-notes). The dead
  phone stays as silent set-dressing; the "you hear your own voice" beat is
  gone. No pointer or evidence was on it.

- *(CUT 2026-07, maintainer ruling: three narrator boxes that recorded
  nothing and said nothing. The `scarecrow` examine and its [E] cue in the
  cornfield maze are GONE outright, a scarecrow standing in a corn row being
  scenery rather than an event; the graveyard's worn headstone keeps its
  two-line look but no longer files a "A weathered headstone." discovery;
  and the backwoods stash keeps its pickup without the "A small stash."
  box.)*
- **the barrow** (on the square): examine **CUT** (maintainer ruling, with
  the three above). It is a prop, not a find; its "the edges are still
  bright" contradiction went with it.
- **the dead well** (`safe_path._town_square`, first read): "[c=dim](You lean
  over the lip. The shaft drops past where any water should be. No glint,
  no bottom, just cold air climbing up out of it.)[/c]" Re-read: notice
  "Cold air climbs out of the dark. No way down for you here."
- **the news rack** (`safe_path._town_square`): "A coin rack of newspapers,
  bleached behind the scratched plastic. The county weekly." /
  "[c=dim]Dated January 15. Every copy in the stack. Nobody ever fed it
  another.[/c]"
- **the truck radio** (the placed noisemaker on the dead pickup behind the
  barn, `scenes/yards.py` `build_barn_yard`): on "The truck radio catches. A
  dead station rolls out over the yard."; off "You kill the radio."; silenced
  by the cult "The music stops dead." (The
  Cistern's pump-arm lure, `scenes/well.py`: "You knock the pump arm loose.
  The hose line begins to clank and hiss." / "You wedge the pump arm
  still." / "A hand wedges the pump arm still. The hiss dies in the line.")
- **the guest register** (`scenes/lodge.py`, first press): "[c=dim](The
  guest register, open on the front desk. Sable lays a pen across the page
  without being asked.)[/c]" / "You sign your name under tonight's date. He
  turns the book back and never reads it." / "\"There. Now you're on the
  books.\"" Later, out of habit: "You flip back through the register out of
  habit. A clean book, barely started. The earliest name on the page is
  only weeks old." / "[c=dim]A lodge this old has years of these. They go
  somewhere when they fill. Down, if this place is like every hotel I've
  worked. And the kitchen hatch wears a padlock.[/c]"
- **the padlocked cellar hatch** (`scenes/lodge.py`): "[c=dim](A padlock
  through the cellar hatch, older than the hinges and freshly oiled.
  Locked.)[/c]" / "[c=dim]A lodge this size keeps a spare key close. Out of
  the rain, near a door. I'd start behind the house.[/c]" Unlocking: notice
  "The iron key turns. The hatch swings up."
- **the never-worn robe** (`clerk_room_interact`, Sable's closet; a case
  NOTE, never evidence). Read in TWO STAGES, because the PI cannot know what
  he is looking at the first time. The old single line called it "a cult
  robe" before the player had ever seen a cult (playtest error class 5).
  - **first look:** "[c=dim](A robe hangs alone in the Clerk's closet. Dark,
    plain, hand-sewn, pressed and folded over the rail.)[/c]" / "[c=dim]By
    the creases it has never once been worn.[/c]" Note: "A robe hanging
    alone in the Clerk's closet. Dark, plain, hand-sewn, pressed and folded
    over the rail." / "By the creases it has never once been worn. A man
    keeps a thing like that for a reason he has not got around to yet."
  - **after THE TALK** (`cult_talk_given`; the note is REWRITTEN in place,
    never filed twice): "[c=dim](The robe in the Clerk's closet. Dark,
    plain, hand-sewn.)[/c]" / "[c=dim]I have seen one of these up close now,
    with a man inside it and his hand on my shoulder.[/c]" Note: as above,
    with "I have seen one of these up close since. A man inside it, his hand
    on my shoulder, telling me to run." / "By the creases, Sable's has never
    once been worn."
  - **re-examine after both:** notice "The robe hangs where it hung. Never
    worn."
- **Toby's desk** (`_school_interact`, the schoolhouse's shoved pile;
  records NOTHING by design, the name does the work): "[c=dim](A child's
  desk, near the bottom of the pile. The lid lifts an inch before the desk
  above it stops.)[/c]" / "[c=dim]Inked inside, in a careful hand that ran
  out of room: TOBY. A spelling sheet folded under it, three words
  done.[/c]" Re-examine: notice "His desk, near the bottom of the pile."
- **the schoolhouse chalkboard's other half** (`_BOARD_LESSON`, shown ahead
  of the cult's drawn doors in every pre-rite look): "[c=dim](The
  chalkboard. One corner of the lesson survives under the chalk dust: a
  column of addition, worked down in a child's hand, the answer circled by
  the teacher.)[/c]" then "[c=dim]Over it, the same door drawn again and
  again, smaller and smaller, into the corner.[/c]"
- **`gas_receipt`** (a walk-over pickup under a schoolhouse cot). It writes
  NOTHING to the case: the receipt IS the record, and its item text in
  Papers carries the whole of it, so a note would only read the thing back
  to the player who just picked it up. Pickup notice: "A gas receipt, under
  a cot." The paper itself (`ITEM_DEFS`, quoted here because the player
  reads it): "CLARK OIL / SEYMOUR, WIS." / "JULY 2 1993" / "14.2 GAL   REG
  $16.75" / "CASH", closing "Four hundred miles south of here, and paid for
  in cash. Whoever slept on that cot drove up the same roads I did."
- **the lodge-candle callback** (`lodge_candle_callback`, after the
  Cistern): "[c=dim]The same guttering candles as the dark below, kept
  burning up here too.[/c]"
- **the barn hatch** (`scenes/interiors.py`): notice "Nailed fast from the
  underside. It does not give." **The farmhouse hatch**
  (`scenes/villager_houses.py`): notice "The hatch is sealed shut. It does
  not budge."
- **the hive kneelers** (`build_dark`, any press): "[c=dim]The kneeler
  doesn't stir. Its lips move, no sound.[/c]"
- **the Preacher's remains, re-examined** (`preacher_body_examine`, after
  the cross is taken): "What's left of him. The flies have found it."
- **a killed local, examined** (`_corpse_examine`, `systems/rot_mixin.py`;
  `{name}` is theirs): first read "[c=dim]{name}. Face-down where the round
  put them. You did this.[/c]"; after "[c=dim]Still here. The cold won't
  let it keep, and won't let it go.[/c]"
- **the cot** (`Game._sleep_at_cot`; a rest, not a save): "You lie down.
  The Arcadia keeps its hours around you, and for a while nothing asks
  anything of you." then notice "You wake rested. A little steadier."
- **the receipt's pickup notice** (`grant_receipt`): "Her tab from the
  shop."

The remaining one-line routine examines (headstones, the bell-tower view
"From the bell tower the town is small.")
and the HUD/system notice layer (see Coverage) stay indexed: the code is
authoritative for their exact words, and the contract still binds (touch
one, update the other).

## Lettering the player reads in the world

Text that is ART rather than narration: words built into a prop and read off
the object itself. They carry no voice and fire no beat, but the player reads
them, so the contract binds them like any other line.

- **CASSILDA'S** and **GAS FOR LESS** (`STATION_NAME` + the tagline banner in
  `rendering/props.py`; the lost road's filling station). The store name burns
  in neon across the shop fascia and again on the roadside pylon's red banner,
  the tagline on the pylon's blue banner below it. Both are spelled in the
  procedural neon-tube alphabet (`_GLYPH`), never a font. The name is the one
  deliberate Chambers echo in the world's own signage (approved by the
  maintainer): it reads as an ordinary family store to anyone who does not
  know the play, so it never states the cosmology. The three barred names
  (*Carcosa*, *the King in Yellow*, *the Yellow King*) stay off the page as
  ever (NARRATIVE §5, guarded `tests/flow.py` §33).

## The lost spaces carry NO narration (maintainer ruling)

The lost fields (`lost_corn` / `lost_forest` / `lost_road`) ship **no narrator
boxes, no notices, and no case-notebook writes at all**. The dark, the hunted
exit light, and the world changing around you are the whole text. The one
notice that existed (on reaching the exit light) was CUT: a caption there
explains away the only beat the space has. If a lost-space beat ever seems to
want words, that is the signal it needs better staging, not a line.

The SAFE PATH is the deliberate opposite and its names say so: "the Country
Lane", "River Road", "the River Bend" (`DISPLAY_NAMES`, `scenes/terrain.py`)
are plain road names, the kind a county puts on a sign. A road that names
itself in ordinary language is a road telling the truth, which is the whole
contract of that layer (`DESIGN.md` §14).

**The lost fields carry no PLACE NAME either.** Every other scene labels itself in the
HUD's lower-left corner ("the Yard", "General Store"); the lost fields set
`display_name = ""` so that corner stays blank. The default would have
titlecased the scene key into "Lost Forest" and told the player exactly what
had happened to them, which is the same explaining-away as a caption. A lost
space is somewhere with no name you know. Both halves of this ruling, the
words and the name, are enforced by `tests/conventions.py` check 6.
