---
name: pixel-gate
description: Byte-identity render gate for rendering refactors. Captures deterministic draw_world() snapshots before a change and diffs after, proving pixels did not move. Use for any pure refactor of rendering/, camera, sprites, or draw paths ("should be byte-identical", "no visual change").
---

# Pixel gate

Two commands; relay the verdict, do not read files:

```bash
# 1. BEFORE touching the code (on the pre-change tree):
python .claude/skills/pixel-gate/pixel_gate.py before

# 2. After the change:
python .claude/skills/pixel-gate/pixel_gate.py check
```

`check` exits 0 when every scene is byte-equal, or when the only deltas are
within capture_world's documented 0.3% ambient-spawn RNG noise floor (that
fallback needs Pillow; on INCONCLUSIVE run `pip install Pillow` and rerun).
On FAIL, per-scene deltas print and amplified diff images land in
`/tmp/world_diff/`. A diff is not automatically wrong for an intentional
visual change; it IS wrong for a refactor that promised identity.
