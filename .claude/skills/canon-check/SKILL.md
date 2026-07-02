---
name: canon-check
description: Pre-writing check for ANY player-facing text or story-adjacent change — dialogue, notes, item descriptions, notices, ending text, new beats, cast changes, or code that touches the ledger, the fork, the descent, or the cast. Use BEFORE writing the words, not after (e.g. "add a line for Hettie", "write the letter in Mara's cell", "new evidence note", "change what Sable says"). Catches canon drift, voice drift, and the no-dash rule while they are still cheap.
---

# Canon check

The narrative is this project's spine and it is *load-bearing*: story
facts gate mechanics (evidence count drives the King and infestation),
and the docs are explicit that when code and bible disagree, the bible
is the intent. This skill is the reasoning you do BEFORE writing a
player-visible word. Doing it after has already cost this project
reverted commits.

## 1. Establish which facts you're standing on

Read (don't recall) the relevant sections, in authority order:

1. **`NARRATIVE.md`** — the bible. Premise, cast, geography, the §
   fences. If your text implies a fact, find that fact here.
2. **`GAME_CHANGES.md`** — settled 2026-06 decisions that OVERRIDE
   older code and comments. Check it before touching: the cast, the
   Ledger (front desk, not cellar), Mr. Sable (most-attuned LOCAL),
   the Playscript (the cult's own notes), the descent (the rope is
   CUT; the rite opens the fold; the Deep Stair is CUT; the blast is
   the way down), the fork, the face.
3. **`tests/flow.py` canon guards** — greppable list of facts already
   locked (e.g. the dream note must say "a year" and contain no
   recurrence language). Your text must not fight a guard.

Write down the 2–4 canon facts your new text depends on, with the doc
section. If you can't cite one, the fact doesn't exist yet — that's a
question for the user, not an improvisation.

## 2. Check the fences (what must NOT be said)

The bible's restraint is deliberate. Before drafting, confirm you are
not about to breach:

- **§10 / the cosmology fence**: the lure chain, what the King is, and
  why the PI was chosen are NEVER stated in-game. They may only be
  *felt* — unease, sensation, an oblique image. If your beat explains,
  cut the explanation and keep the feeling.
- **§1b / the dream**: the PI dreamed the door ONCE, a year ago, never
  reached it, and it never recurred. No text may imply recurrence or
  arrival.
- **The dream note goes to `notes`, never `evidence`** — only the six
  `CANONICAL_EVIDENCE` beats live in `evidence`; it drives the
  King-gate and infestation.
- **No day/night**: nothing may reference nights passing, mornings,
  or a day count.
- **One phenomenon, two presentations**: folds and the King's portal
  are the same thing; don't write text that splits them.

## 3. Match the voice

- The PI's interior voice: terse, concrete, half-dismissive of what he
  can't file. Case notes read like case notes, not poetry.
- Locals are 1994 rural plain-spoken; the cult speaks little or not at
  all; the King is never quoted.
- Quote a couple of existing lines from the same speaker/surface
  (grep `scenes/dialogue.py`, `systems/narrative_mixin.py`) and match
  register before writing new ones.

## 4. The hard formatting rule

**No dashes in player-facing text.** No em-dash, en-dash, or `--` as
punctuation in anything the player reads: names, descriptions,
dialogue, narrator beats, notices, notes, ending text, labels.
Rewrite with a period, comma, colon, or a new sentence. Docs and code
comments are exempt. After writing, actually scan your strings for
`—`, `–`, and `--`; this rule has been missed in review before.

## 5. After writing

- Re-read the draft against the facts from step 1 — does any sentence
  quietly assert something the bible doesn't?
- If the new text locks a canon fact (a date, a name, a fence), add a
  guard to `tests/flow.py` in the same change.
- Run `python tests/run_all.py`; the existing guards are the last line
  of defense, not the first.
