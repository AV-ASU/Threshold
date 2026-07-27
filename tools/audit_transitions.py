"""Step 1 of the geometry overhaul: enumerate every world transition the game
has today and classify it by the proposed (style, topology, gating) taxonomy.

Five mechanisms currently coexist:
  1. Mundane exits          -- Scene.exits[ch] with no direction.
  2. Direction-gated exits  -- Scene.exits[ch] + Scene.exit_directions[ch],
                               drawn as the gold-rim 4D peek.
  3. Torus wrap             -- Scene.wrap_x / Scene.wrap_y, same map looped.
  4. on_update teleport     -- handcrafted scene hook that calls
                               Game.begin_transition / Game.load_scene_now.
  5. Runtime portals        -- the King's tear (Game._portal), not in scenes.

Proposed taxonomy (3 x 2 x 3 grid, most cells empty):
  style    : mundane | eldritch | silent
  topology : cross_map | wrap
  gating   : none | direction | inventory

This audit is read-only: it boots no Game, only constructs each Scene via its
SCENE_BUILDERS entry and reads its declared exits / wraps / on_update_fn.
on_update teleports are detected statically by source-scan -- we can't run
them. Prints a markdown table + a summary of the cells in use.

Run from repo root:
    python tools/audit_transitions.py
"""
import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import SCENE_BUILDERS, load_scene


# --- static source scan for on_update teleports ------------------------------

_TELEPORT_CALL_RE = re.compile(
    r"\b(?:begin_transition|load_scene_now)\s*\(\s*['\"]([^'\"]+)['\"]\s*,?"
)


def _scene_module_sources():
    """Slurp every scenes/*.py file once so we can scan for handcrafted
    teleport calls inside on_update_fn bodies (we can't execute them safely
    here, since they need a live Game)."""
    src_dir = os.path.join(_ROOT, "scenes")
    out = {}
    for fname in os.listdir(src_dir):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(src_dir, fname), "r") as f:
            out[fname] = f.read()
    return out


_SOURCES = _scene_module_sources()


def _all_hook_teleports():
    """One pass across scenes/*.py: every begin_transition / load_scene_now
    call, with the enclosing build_*() scene key and the local hook function
    it sits in. We can't match hook function names to scene keys 1:1 (some are
    `_school_interact`, others `_square_interact`), so we walk top-down from
    `def build_<key>(` blocks and report any teleport call inside.

    Returns [(scene_key, target_key, hook_name, source_file)]."""
    build_re = re.compile(r"^def\s+build_([a-z_0-9]+)\s*\(", re.MULTILINE)
    inner_def_re = re.compile(
        r"^\s+def\s+(_[a-z_0-9]+)\s*\(", re.MULTILINE
    )
    out = []
    for fname, src in _SOURCES.items():
        builds = list(build_re.finditer(src))
        for i, m in enumerate(builds):
            scene_key = m.group(1)
            start = m.end()
            end = builds[i + 1].start() if i + 1 < len(builds) else len(src)
            block = src[start:end]
            # Find each inner def's span so we can label calls by their hook.
            defs = list(inner_def_re.finditer(block))
            def hook_at(pos):
                last = None
                for d in defs:
                    if d.start() <= pos:
                        last = d.group(1)
                    else:
                        break
                return last or "<top-level of build_*>"
            for tm in _TELEPORT_CALL_RE.finditer(block):
                out.append((scene_key, tm.group(1),
                            hook_at(tm.start()), fname))
    return out


# --- classifier --------------------------------------------------------------

def classify_exit(scene, ch):
    """Map one Scene.exits entry to (style, gating)."""
    direction = scene.exit_directions.get(ch)
    if direction:
        return "eldritch", f"direction={direction}"
    return "mundane", "none"


def audit():
    rows = []
    wraps = []
    failures = []

    for key in sorted(SCENE_BUILDERS):
        try:
            scene = load_scene(key)
        except Exception as e:
            failures.append((key, repr(e)))
            continue

        # Mundane + eldritch exits live in scene.exits.
        for ch, (target, spawn) in scene.exits.items():
            style, gating = classify_exit(scene, ch)
            rows.append({
                "scene": key,
                "char": ch,
                "target": target,
                "spawn": spawn,
                "style": style,
                "topology": "cross_map",
                "gating": gating,
            })

        if scene.wrap_x or scene.wrap_y:
            axes = []
            if scene.wrap_x: axes.append("x")
            if scene.wrap_y: axes.append("y")
            wraps.append({
                "scene": key,
                "axes": "+".join(axes),
                "style": "silent",
                "topology": "wrap",
                "gating": "none",
            })

    hook_teleports = []
    for scene_key, target, hook_name, src_file in _all_hook_teleports():
        # Skip ones whose target equals an already-declared exit -- those are
        # "the door fires this hook to swap the spawn" style, not extra geometry.
        scene_row_targets = {r["target"] for r in rows if r["scene"] == scene_key}
        already_declared = target in scene_row_targets
        hook_teleports.append({
            "scene": scene_key,
            "target": target,
            "hook": hook_name,
            "via": src_file,
            "style": "mundane",
            "topology": "cross_map",
            "gating": "custom",
            "duplicates_exit": already_declared,
        })

    return rows, wraps, hook_teleports, failures


def _print_md_table(title, rows, cols):
    print(f"\n## {title}  ({len(rows)})\n")
    if not rows:
        print("_(none)_")
        return
    header = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    print(header)
    print(sep)
    for r in rows:
        print("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")


def _summarize(rows, wraps, hook_teleports):
    from collections import Counter
    print("\n## Cell usage in the proposed taxonomy\n")
    cells = Counter()
    for r in rows:
        cells[(r["style"], r["topology"], r["gating"])] += 1
    for w in wraps:
        cells[(w["style"], w["topology"], w["gating"])] += 1
    for h in hook_teleports:
        cells[(h["style"], h["topology"], h["gating"])] += 1
    print("| style | topology | gating | count |")
    print("|---|---|---|---|")
    for (s, t, g), n in sorted(cells.items(), key=lambda kv: -kv[1]):
        print(f"| {s} | {t} | {g} | {n} |")


def main():
    rows, wraps, hook_teleports, failures = audit()
    print("# THRESHOLD transition audit\n")
    print(f"Scenes registered: {len(SCENE_BUILDERS)}")
    print(f"Scenes built OK:   {len(SCENE_BUILDERS) - len(failures)}")
    if failures:
        print("\nBuild failures (audit skipped these):")
        for key, err in failures:
            print(f"  {key}: {err}")

    _print_md_table("Declared exits (mundane + direction-gated)",
                    rows, ["scene", "char", "target", "spawn",
                           "style", "topology", "gating"])
    _print_md_table("Torus wraps", wraps,
                    ["scene", "axes", "style", "topology", "gating"])
    _print_md_table("Handcrafted hook teleports (begin_transition / load_scene_now)",
                    hook_teleports,
                    ["scene", "target", "hook", "via",
                     "style", "topology", "gating", "duplicates_exit"])
    _summarize(rows, wraps, hook_teleports)


if __name__ == "__main__":
    main()
