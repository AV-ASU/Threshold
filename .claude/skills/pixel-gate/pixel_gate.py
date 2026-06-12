"""The byte-identity render gate as two commands instead of a three-step
recipe. Wraps tools/capture_world.py (deterministic draw_world captures).

    python .claude/skills/pixel-gate/pixel_gate.py before   # snapshot now
    python .claude/skills/pixel-gate/pixel_gate.py check    # snapshot + diff

`before` captures the current render to /tmp/world_before. After making the
rendering/refactor change, `check` captures /tmp/world_after and compares:
first a plain byte-compare of the PNGs (the captures are deterministic, so
identical bytes = identical pixels, no Pillow needed); only if bytes differ
does it fall back to capture_world's tolerance diff (needs Pillow), which
allows the documented 0.3% ambient-spawn RNG noise floor and writes
amplified diff images to /tmp/world_diff. Exit 0 = gate passed.
"""
import filecmp
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
_CAPTURE = os.path.join(_ROOT, "tools", "capture_world.py")


def _run(args, capture=False):
    return subprocess.run([sys.executable, _CAPTURE] + args, cwd=_ROOT,
                          capture_output=capture, text=capture)


def _byte_compare():
    """(identical_keys, differing_keys, unpaired_keys) by PNG file bytes."""
    same, diff, unpaired = [], [], []
    names = sorted(set(os.listdir("/tmp/world_before"))
                   | set(os.listdir("/tmp/world_after")))
    for name in names:
        if not name.endswith(".png"):
            continue
        pa, pb = f"/tmp/world_before/{name}", f"/tmp/world_after/{name}"
        if not (os.path.exists(pa) and os.path.exists(pb)):
            unpaired.append(name)
        elif filecmp.cmp(pa, pb, shallow=False):
            same.append(name)
        else:
            diff.append(name)
    return same, diff, unpaired


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "before":
        rc = _run(["--tag", "before"]).returncode
        if rc == 0:
            print("\nBaseline captured (/tmp/world_before). "
                  "Make the change, then run: pixel_gate.py check")
        return rc

    if mode == "check":
        if not os.path.isdir("/tmp/world_before"):
            print("No baseline found. Run `pixel_gate.py before` first "
                  "(on the PRE-change tree).")
            return 2
        rc = _run(["--tag", "after"]).returncode
        if rc != 0:
            return rc

        same, diff, unpaired = _byte_compare()
        for name in unpaired:
            print(f"  ? {name}: missing on one side")
        if not diff and not unpaired:
            print(f"\nPIXEL GATE: IDENTICAL "
                  f"(all {len(same)} scenes byte-equal). Safe.")
            return 0

        # Bytes differ somewhere: defer to capture_world's tolerance diff,
        # which allows the ambient-spawn RNG noise floor. It always exits 0,
        # so the verdict comes from its printed PASS/FAIL line.
        print(f"Byte deltas in: {', '.join(diff) or '(unpaired only)'} "
              f"-- running tolerance diff...")
        proc = _run(["--diff", "before", "after"], capture=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            if "No module named 'PIL'" in proc.stderr:
                print("\nPIXEL GATE: INCONCLUSIVE. Bytes differ and the "
                      "tolerance diff needs Pillow (`pip install Pillow`), "
                      "then rerun check.")
            return 2
        if "PASS (identical within tolerance)" in proc.stdout:
            print("\nPIXEL GATE: PASS (only ambient-spawn noise). Safe.")
            return 0
        print("\nPIXEL GATE: FAIL. Real pixel differences. Inspect "
              "/tmp/world_diff/*.png before deciding.")
        return 1

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
