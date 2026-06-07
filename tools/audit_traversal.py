"""Traversal-jank audit -- a headless sweep for the *signatured* feel-bugs that
otherwise only surface by playing (the kind THRESHOLD's dev kept finding one
playtest at a time): seams you can walk but not see into, transitions that
teleport you to a non-matching edge, and scenes that are too dense/slow.

It is a REPORT, not a pass/fail gate (run it, read it, fix the flagged ones).
Pure *feel* (is it scary, does the pacing drag) still needs a human; this covers
everything with a code/data signature.

    python tools/audit_traversal.py            # structural sweeps (fast)
    python tools/audit_traversal.py --perf     # + per-scene draw timing (boots a Game)

Checks:
  SEAM   -- for every exit between two SEAMLESS_WORLD_SCENES, is the crossing
            edge backed by a wrap axis (so the world looks continuous) or hard
            (a void/treeline you walk into blind)? Flags the inconsistency the
            dev hit: "I can see into B but not C and D."
  SPAWN  -- does an exit land you on the COMPLEMENTARY edge of the destination
            (north exit -> south arrival), or somewhere that reads as a
            teleport?
  DENSE  -- solid-tile fraction per outdoor scene (a proxy for "the trees catch
            me everywhere").
  PERF   -- (--perf) median draw_world ms per scene; flags frame-budget blowups.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import SCENE_BUILDERS, load_scene, TILE
from scenes.base import is_object_solid, is_floor_solid
from systems.config import SEAMLESS_WORLD_SCENES

_OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}
# Which wrap axis a given edge needs to read as visually continuous.
_EDGE_WRAP = {"N": "wrap_y", "S": "wrap_y", "E": "wrap_x", "W": "wrap_x"}


def _edges_of_tile(tx, ty, w, h, margin=1):
    """Which border(s) a tile sits on (a corner returns two)."""
    e = []
    if tx <= margin:           e.append("W")
    if tx >= w - 1 - margin:   e.append("E")
    if ty <= margin:           e.append("N")
    if ty >= h - 1 - margin:   e.append("S")
    return e


def _exit_tiles(scene, ch):
    """Every (tx, ty) where exit char `ch` sits in the objects grid."""
    out = []
    for ty, row in enumerate(scene.objects):
        for tx, c in enumerate(row):
            if c == ch:
                out.append((tx, ty))
    return out


def _dominant_edge(tiles, w, h):
    """The border most of an exit's tiles touch (None if it's interior)."""
    tally = {}
    for tx, ty in tiles:
        for e in _edges_of_tile(tx, ty, w, h):
            tally[e] = tally.get(e, 0) + 1
    if not tally:
        return None
    return max(tally, key=tally.get)


def _load_all():
    scenes = {}
    for key in SCENE_BUILDERS:
        try:
            scenes[key] = load_scene(key)
        except Exception as e:
            print(f"  !! {key}: failed to build ({e})")
    return scenes


def audit_seams_and_spawns(scenes):
    seam_flags, spawn_flags, ok = [], [], 0
    for key, sc in scenes.items():
        for ch, (target, spawn_id) in sc.exits.items():
            tiles = _exit_tiles(sc, ch)
            edge = _dominant_edge(tiles, sc.w, sc.h)
            directional = ch in getattr(sc, "exit_directions", {})
            tgt = scenes.get(target)
            seamless_pair = (key in SEAMLESS_WORLD_SCENES
                             and target in SEAMLESS_WORLD_SCENES)

            # SEAM: a seamless neighbour on a non-wrapped edge = walk-but-blind.
            if seamless_pair and edge and not directional:
                needs = _EDGE_WRAP[edge]
                if not getattr(sc, needs, False):
                    seam_flags.append(
                        f"  {key:<18} {edge}-> {target:<18} "
                        f"VOID seam (no {needs}; you walk it but can't see in)")
                else:
                    ok += 1

            # SPAWN: does it land on the complementary edge?
            if tgt is not None and edge and not directional:
                sp = tgt.spawns.get(spawn_id) or tgt.spawns.get("default")
                if sp:
                    stx, sty = int(sp[0] // TILE), int(sp[1] // TILE)
                    sp_edges = _edges_of_tile(stx, sty, tgt.w, tgt.h, margin=2)
                    want = _OPP[edge]
                    if seamless_pair and want not in sp_edges:
                        where = "/".join(sp_edges) or "interior"
                        spawn_flags.append(
                            f"  {key:<18} {edge}-> {target:<14} spawn '{spawn_id}'"
                            f" lands {where} (want {want}) -- reads as a teleport")
    return seam_flags, spawn_flags, ok


def audit_density(scenes):
    rows = []
    for key, sc in scenes.items():
        if key not in SEAMLESS_WORLD_SCENES:
            continue
        solid = total = 0
        for ty in range(sc.h):
            for tx in range(sc.w):
                total += 1
                ox = tx * TILE + TILE // 2
                oy = ty * TILE + TILE // 2
                if (is_object_solid(sc.char_object_at(ox, oy))
                        or is_floor_solid(sc.char_floor_at(ox, oy))):
                    solid += 1
        frac = solid / total if total else 0.0
        rows.append((frac, key, solid, total))
    rows.sort(reverse=True)
    return rows


def audit_perf(scenes):
    """Median draw_world ms per scene (boots one real Game)."""
    import time
    from systems.game import Game
    g = Game(); g.save.new(); g._start_play()
    out = []
    for key in scenes:
        try:
            g.load_scene_now(key)
        except Exception as e:
            out.append((key, None, str(e))); continue
        samples = []
        for _ in range(8):
            t0 = time.perf_counter()
            g.draw_world()
            samples.append((time.perf_counter() - t0) * 1000.0)
        samples.sort()
        out.append((key, samples[len(samples) // 2], None))
    out.sort(key=lambda r: (r[1] is None, -(r[1] or 0)))
    return out


def main():
    perf = "--perf" in sys.argv
    print("Building every scene...")
    scenes = _load_all()
    print(f"  {len(scenes)} scenes built.\n")

    seam_flags, spawn_flags, ok = audit_seams_and_spawns(scenes)

    print("=== SEAM continuity (see-into consistency) ===")
    print("  (wrap-backed edges look continuous via the scene's OWN wrap; a true")
    print("   neighbour render does not exist yet -- VOID = you can't even see the")
    print("   wrap illusion, just a hard edge.)")
    print("\n".join(seam_flags) if seam_flags else "  none flagged")
    print(f"  ({ok} seamless edges ARE wrap-backed)\n")

    print("=== SPAWN edge-match (teleport feel) ===")
    print("\n".join(spawn_flags) if spawn_flags else "  none flagged")
    print()

    print("=== DENSE outdoor scenes (collision-grab proxy) ===")
    for frac, key, solid, total in audit_density(scenes)[:8]:
        bar = "#" * int(frac * 40)
        print(f"  {key:<18} {frac*100:5.1f}% solid  {bar}")
    print()

    if perf:
        print("=== PERF: median draw_world ms per scene ===")
        for key, ms, err in audit_perf(scenes):
            if err:
                print(f"  {key:<18} ERROR {err}")
            else:
                flag = "  <-- over 16ms budget" if ms > 16 else ""
                print(f"  {key:<18} {ms:6.2f} ms{flag}")
    else:
        print("(run with --perf for per-scene draw timing)")


if __name__ == "__main__":
    main()
