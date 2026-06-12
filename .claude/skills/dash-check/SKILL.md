---
name: dash-check
description: Enforce the CLAUDE.md HARD RULE (no em-dash, en-dash, or double-hyphen punctuation in player-facing strings) by scanning every string literal in the game packages. Use after writing/editing any player-facing text (dialogue, item text, notes, endings, labels) or when asked to audit text for dashes.
---

# Dash check

Run exactly this and relay the output; do not grep or read files yourself:

```bash
python .claude/skills/dash-check/check_dashes.py
```

It AST-parses `scenes/ ui/ systems/ entities/ rendering/ main.py` and flags
dash punctuation in string literals (docstrings excluded, 3+ hyphen dividers
allowed). On FAIL, rewrite each flagged string with a period, comma, colon,
or a new sentence, then rerun until OK.
