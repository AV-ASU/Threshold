#!/usr/bin/env python3
"""Canon-key drift tripwire.

Cheap, headless consistency check (no pygame, no display/audio): confirms
the load-bearing item/scene keys named in NARRATIVE.md's "Canon
invariants" section still appear as quoted string literals somewhere in
the game source, and separately spot-checks that every scene registered
in scenes/__init__.py's SCENE_BUILDERS is referenced the same way. Not a
general doc linter -- just a tripwire for a key renamed in one place and
not the other.

Usage: python tools/check_canon_keys.py
Exit 0 = every key found at least once. Exit 1 = one or more missing.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NARRATIVE = ROOT / "NARRATIVE.md"
SCENES_INIT = ROOT / "scenes" / "__init__.py"
SOURCE_DIRS = ["systems", "entities", "scenes", "rendering", "ui"]


def load_bearing_keys():
    """Pull the backtick-quoted key list out of NARRATIVE.md's "Item and
    scene keys are load-bearing" canon-invariant bullet (parsed at
    check-time, not hand-copied, so a future edit to the list stays live)."""
    text = NARRATIVE.read_text(encoding="utf-8")
    m = re.search(r"Item and scene keys are load-bearing.*?:(.*?`\.)", text, re.DOTALL)
    if not m:
        print("FAIL: could not find the 'load-bearing' key bullet in NARRATIVE.md")
        sys.exit(1)
    return re.findall(r"`([^`]+)`", m.group(1))


def scene_builder_keys():
    """Pull the dict keys straight out of scenes/__init__.py's SCENE_BUILDERS
    literal -- the authoritative live scene registry, read directly rather
    than regexed out of a doc."""
    text = SCENES_INIT.read_text(encoding="utf-8")
    m = re.search(r"SCENE_BUILDERS\s*=\s*\{(.*?)\n\}", text, re.DOTALL)
    if not m:
        print("FAIL: could not find SCENE_BUILDERS in scenes/__init__.py")
        sys.exit(1)
    return re.findall(r'"([A-Za-z0-9_]+)"\s*:', m.group(1))


def source_text():
    """Concatenated text of every .py file under the tracked source dirs."""
    chunks = []
    for d in SOURCE_DIRS:
        for path in (ROOT / d).rglob("*.py"):
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def check(keys, text, label):
    print(f"\n{label}: {len(keys)} key(s)")
    missing = []
    for key in keys:
        ok = f'"{key}"' in text or f"'{key}'" in text
        print(f"  [{'PASS' if ok else 'FAIL'}] {key}")
        if not ok:
            missing.append(key)
    return missing


def main():
    keys = load_bearing_keys()
    scene_keys = scene_builder_keys()
    text = source_text()

    missing = check(keys, text, "NARRATIVE.md load-bearing keys")
    missing_scenes = check(scene_keys, text, "scenes/__init__.py SCENE_BUILDERS keys")

    total = len(keys) + len(scene_keys)
    total_missing = len(missing) + len(missing_scenes)
    print(f"\n{total - total_missing}/{total} canon keys verified against "
          f"{', '.join(SOURCE_DIRS)}.")

    if missing or missing_scenes:
        print("\nFAIL -- missing keys (no quoted reference found in source):")
        for key in missing:
            print(f"  - {key}  (NARRATIVE.md load-bearing list)")
        for key in missing_scenes:
            print(f"  - {key}  (SCENE_BUILDERS)")
        return 1

    print("PASS -- all canon keys present in source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
