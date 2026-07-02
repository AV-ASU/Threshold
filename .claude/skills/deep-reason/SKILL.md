---
name: deep-reason
description: A structured reasoning protocol for hard or ambiguous decisions in this project — design calls, architecture choices, "should we X or Y", anything where the first plausible answer is likely wrong or where a mistake is expensive to undo. Use when the user asks for a recommendation, a design, a judgment call, or a plan for something non-trivial (e.g. "how should the stealth rework handle corn?", "is this the right way to do the descent?", "plan the onboarding fix"). Not for mechanical edits with an obvious shape.
---

# Deep reason

A discipline for thinking, not a template to fill. The output is a
decision the user can trust; every step exists because skipping it has
produced a confidently wrong answer in a project like this one.

## The protocol

Work these in order. Write the intermediate steps down (scratchpad or
the reply itself) — reasoning that only happens in your head doesn't get
checked.

### 1. Restate the actual question

One or two sentences: what is being decided, and what does "good" mean
here? If the request is ambiguous, name the interpretations and pick the
one you're answering (or ask, if they genuinely diverge). Most bad
answers in this repo came from answering a *neighboring* question.

### 2. Ground truth before opinion

Do NOT reason from memory of the codebase — it drifts. Before forming a
view, read the primary sources for this decision:

- **Story/canon decisions** → `NARRATIVE.md` (the bible; source of
  truth), then `GAME_CHANGES.md` (settled deltas), then `TODO.md`
  (what's already been critiqued and decided).
- **Mechanics/tuning** → the actual constants in `systems/config.py`
  and the code path in `systems/threat_mixin.py` / `entities/`, not the
  summary in CLAUDE.md.
- **Rendering/camera** → `CAMERA.md`, `PORTALS.md`, and the relevant
  `rendering/` module.
- **"Has this been decided before?"** → grep the design docs. This
  project settles decisions in writing; re-litigating a settled call
  (e.g. the rope is CUT, corpses don't persist, one teleport primitive)
  wastes a session and produces canon drift.

List the 3–6 load-bearing facts you found, with file refs. If a fact
you need is missing, go get it — don't bridge with plausibility.

### 3. Enumerate real options

At least two, usually three: the obvious one, the opposite of the
obvious one, and the "do less" option (cut/defer). For each, one
honest paragraph: what it costs, what it risks, what it makes easier
later. If you can only see one option, you haven't understood the
problem yet — the design docs here are full of rejected-but-reasonable
alternatives (the submerged drowned-body rework, the persistent-corpse
ledger) that looked like the only way at the time.

### 4. Judge against THIS project's values

Generic engineering values mislead here. The tie-breakers that actually
govern this codebase, in rough priority:

1. **Dread over mechanics.** A change that adds player power or clarity
   but drains tension loses. ("The crossing is deliberately nothing;
   the FRAME is the spectacle.")
2. **One primitive per phenomenon.** No bespoke second paths — new
   traversal goes through `cross_fold`, new sprites through the
   procedural pipeline, new rifts through `draw_rift_door`.
3. **Canon is load-bearing.** If the option needs the story to bend,
   the option is wrong (or the bible needs a deliberate, named change —
   never a silent split).
4. **Testability.** Prefer the option a flow-guard can pin down.
5. **The player never reads the docs.** Anything whose payoff lives
   only in `NARRATIVE.md` doesn't exist. (TODO.md items 5–9 are all
   this failure.)

### 5. Adversarial pass — argue against your pick

Before writing the recommendation, spend one honest paragraph as the
critic: what's the strongest case that your chosen option is wrong?
What would a playtester hate about it? What breaks in six months?
If the critique lands, go back to step 3. If it doesn't, keep the
paragraph — it becomes the "risks" section of the answer.

### 6. Decide, and say what would change your mind

End with: the recommendation in one sentence, the two or three reasons
it wins, the known risks (from step 5), and the concrete observation
that would falsify it ("if playtests show X, revisit"). A decision
without a falsifier is a mood.

## Anti-patterns this skill exists to prevent

- **Plausible-from-memory**: describing code you didn't just read.
- **Option laundering**: presenting one idea three ways.
- **Generic-values judging**: picking the "cleaner" option when the
  dread-first value system says otherwise.
- **Silent canon drift**: a design answer that quietly contradicts
  `NARRATIVE.md` or a settled `GAME_CHANGES.md` decision.
- **Unfalsifiable confidence**: a recommendation with no stated risk
  and no condition that would revisit it.
