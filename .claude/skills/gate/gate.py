"""The one-command pre-commit gate: compile check + the full test gate
(tests/run_all.py: smoke + flow + fold_pursuit + king_roam + render_smoke)
+ the dash rule (no dash punctuation in player-facing strings).

Exits 0 only if EVERYTHING is green. Run from anywhere:

    python .claude/skills/gate/gate.py
"""
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

STEPS = [
    ("compile", [sys.executable, "-m", "compileall", "-q",
                 "systems", "entities", "scenes", "rendering", "ui",
                 "main.py"]),
    ("dash-check", [sys.executable,
                    os.path.join(".claude", "skills", "dash-check",
                                 "check_dashes.py")]),
    ("tests", [sys.executable, os.path.join("tests", "run_all.py")]),
]


def main():
    env = dict(os.environ, PYTHONPATH=_ROOT)
    results = {}
    for name, cmd in STEPS:
        print(f"\n===== {name} =====", flush=True)
        rc = subprocess.run(cmd, cwd=_ROOT, env=env).returncode
        results[name] = (rc == 0)
        if not results[name] and name == "compile":
            break  # nothing downstream is meaningful on a syntax error

    print("\n===== GATE =====")
    for name, _ in STEPS:
        state = {True: "PASS", False: "FAIL", None: "SKIP"}[results.get(name)]
        print(f"  {state}  {name}")
    if all(results.get(name) for name, _ in STEPS):
        print("\nGate green. Safe to commit.")
        return 0
    print("\nGate RED. Do not commit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
