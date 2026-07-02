---
name: pre-flight
description: The verification gate to run before EVERY commit/push in this repo, plus the edit-discipline rules that prevent the errors it catches. Use when about to commit, when the user says "commit/push/ship/PR", or when wrapping up a multi-file change (e.g. "looks good, push it", "commit that"). Encodes the working agreements this project learned the hard way, including the NameError that got pushed twice.
---

# Pre-flight

A commit in this repo is a claim: "the game boots, the spine is
completable, and canon holds." This skill is how you earn the right to
make that claim. It exists because batching edits and skipping the
gate has shipped a `NameError` to main twice.

## The gate (in order, all green before `git commit`)

```bash
# 1. Everything still compiles
python -m compileall systems entities scenes rendering ui .

# 2. The full harness gate: smoke + flow + fold_pursuit + king_roam
#    + render_smoke. Self-configures SDL dummy drivers.
python tests/run_all.py
```

3. **Rendering or refactor work?** Also run the byte-identity gate:
   `tools/capture_world.py --tag before` (on the pre-change tree),
   `--tag after`, then `--diff`. Pitch 0 must be byte-identical for
   pure-refactor and tilt-only changes; a diff you didn't intend is a
   finding, not noise.

4. **Player-facing text changed?** Scan the new strings for `—`, `–`,
   and `--` (the no-dash rule), and confirm against the canon-check
   skill if you haven't already.

5. **New canon fact or fixed invariant?** Add a `tests/flow.py` guard
   in the same commit.

Never commit on "it should still pass" — re-run after the LAST edit.
An edit made after the gate invalidates the gate.

## Edit discipline (prevents what the gate catches)

- **One edit at a time on a shifting file.** Multiple `Edit`s batched
  against the same file in one turn silently mis-apply as earlier
  edits move the context. For multi-site mechanical changes, write a
  small Python patch script with `assert count == 1` per replacement,
  run it, then verify.
- **`__pycache__` / `.pyc` never get committed** (gitignored; keep it
  that way).
- Check `git status` and `git diff --stat` before staging — stray
  scratch files and unintended edits are cheaper to catch here than
  in review.

## Commit and push

- Clear, descriptive message in this repo's style (imperative,
  specific: look at `git log --oneline` and match).
- Push with `git push -u origin <branch>`; on network failure retry
  with backoff (2s, 4s, 8s, 16s).
- **"Push to main" MEANS MERGE TO MAIN** — when the maintainer says
  push/PR to main, open the PR and merge it in the same action; do not
  stop to ask for a second confirmation.

## Honest reporting

Report the gate's actual output. If a harness fails, say so with the
failure text and stop — do not commit around it, and do not describe a
partial verification as "tests pass". If you skipped a step (e.g. no
capture diff because the change was pure text), say which and why.
