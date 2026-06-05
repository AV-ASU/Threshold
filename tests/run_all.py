"""The full THRESHOLD test gate: smoke + flow + fold_pursuit + render_smoke.

One command to run every harness before a commit/push. Self-configures the
SDL dummy drivers (no display/audio needed) and sets PYTHONPATH, runs each
suite as its own subprocess so a crash in one is isolated, prints a summary,
and exits NONZERO if any suite fails. Run from the repo root:

    python tests/run_all.py

The individual suites still run standalone (e.g. `python tests/smoke.py`).
"""
import os
import subprocess
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Order: cheapest/most-fundamental first.
SUITES = ["smoke", "flow", "fold_pursuit", "render_smoke"]


def main():
    env = dict(os.environ, PYTHONPATH=_ROOT)
    results = {}
    for name in SUITES:
        path = os.path.join(_ROOT, "tests", f"{name}.py")
        print(f"\n===== {name} =====", flush=True)
        rc = subprocess.run([sys.executable, path], env=env).returncode
        results[name] = (rc == 0)

    print("\n===== SUMMARY =====")
    for name in SUITES:
        print(f"  {'PASS' if results[name] else 'FAIL'}  {name}")

    if all(results.values()):
        print("\nAll suites green.")
        return 0
    print("\nFAILURES present (see above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
