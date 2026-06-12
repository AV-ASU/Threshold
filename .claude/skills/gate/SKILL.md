---
name: gate
description: Run the full THRESHOLD pre-commit gate (compile check + dash rule + all five test harnesses) as one command with one exit code. Use before every commit/push, or whenever asked "is the build green", "run the tests", "is it safe to commit".
---

# The gate

Run exactly this and relay the summary; do not read any files:

```bash
python .claude/skills/gate/gate.py
```

Exit 0 = green, safe to commit. Nonzero = report the FAIL lines and fix
before committing. That's the whole skill.
