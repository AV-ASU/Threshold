#!/usr/bin/env python3
"""Record THE STORM as it actually ships -- a real Game, the real update loop,
the real `draw_world` -- to an MP4 you can watch.

This drives the LIVE system, not `systems/storm.py` (the dormant standalone
sim, which was superseded by the flood-as-a-mode implementation and models a
timer-driven Mask migration the game no longer uses). Everything you see here
is the thing the player gets: `_tick_watchers` opening amalgams, `_storm_tick`
walking them at you and refusing any step into a light pool, `_tick_apex`
floating the Mask onto a host that then ignores light entirely, and the fog
smear (`actor_smear_range`) that makes a 22-unit flood legible at range.

Why a video and not a contact sheet: the storm's whole content is MOTION. A
still frame cannot show units ringing a pool rather than entering it, cannot
show the apex crossing the ring the others will not, and cannot show the
cadence of a wave building. Every judgement about this system is a judgement
about how it closes in.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. \
        python tools/capture_storm.py --scene store_row --seconds 14

Writes an MP4 (default /tmp/storm.mp4). `--stills N` also drops N evenly
spaced PNGs beside it, for when a frame needs pointing at.
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                                    # noqa: E402
import numpy as np                                               # noqa: E402
import imageio                                                   # noqa: E402

from constants import TILE                                       # noqa: E402
from systems.game import Game                                    # noqa: E402
from systems.config import STORM_GATE_EVIDENCE, APEX_VIS_GATE    # noqa: E402


def lit_stand(scene):
    """A walkable tile INSIDE a light pool, else the most open dark one.

    The pool is the point: the flood's one readable rule is that a unit will
    not step into light, so the player has to be standing in some for the ring
    to form. Falling back to open ground keeps the tool working in a scene
    with no fixtures at all (you just get a straight convergence instead).
    """
    lit, dark = [], []
    if getattr(scene, "procedural", False):
        cx, cy = scene.w // 2, scene.h // 2
        ys, xs = range(cy - 40, cy + 40), range(cx - 40, cx + 40)
    else:
        ys, xs = range(2, scene.h - 2), range(2, scene.w - 2)
    for ty in ys:
        for tx in xs:
            x, y = tx * TILE + 16, ty * TILE + 16
            if scene.is_solid_at(x, y):
                continue
            (lit if scene.lit_at(x, y) else dark).append((x, y))
    if lit:
        return lit[len(lit) // 2], True
    return (dark[len(dark) // 2] if dark else (scene.w * TILE // 2,
                                               scene.h * TILE // 2)), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="store_row",
                    help="a scene the dark actually takes (default store_row: "
                         "a street at full evidence is night, and its lamps "
                         "are the islands)")
    ap.add_argument("--seconds", type=float, default=14.0)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--out", default="/tmp/storm.mp4")
    ap.add_argument("--stills", type=int, default=0)
    ap.add_argument("--warmup", type=float, default=75.0,
                    help="seconds of sim run BEFORE recording starts. The "
                         "wave builds on an evidence-scaled interval and the "
                         "Mask has to float to a host, so a cold clip is a "
                         "trickle and an empty seeking state -- the storm is "
                         "a condition you walk into, not an event")
    ap.add_argument("--vis", type=float, default=0.78,
                    help="visibility to HOLD (default 0.78). Above "
                         "APEX_VIS_GATE so the Mask comes, and below 0.95 on "
                         "purpose: at max the overlay paints His red wash and "
                         "a hard edge-crush tunnel vignette that reduces the "
                         "frame to a porthole. That overlay is real and worth "
                         "looking at, but it is a different study than how the "
                         "flood moves -- pass --vis 1.0 for it.")
    ap.add_argument("--no-apex", action="store_true",
                    help="hold visibility under APEX_VIS_GATE so the Mask "
                         "never arrives -- the plain flood on its own")
    args = ap.parse_args()

    pygame.init()
    pygame.display.set_mode((1, 1))

    g = Game()
    g.save.new()
    g._start_play()
    g.load_scene_now(args.scene, "default")

    # The gate: the storm is the Watcher wave's second MODE, live past
    # STORM_GATE_EVIDENCE in a room the dark has taken. Outdoors that same
    # count is what puts the lights out (the storm's STAGE), so setting
    # evidence is the whole setup -- there is no storm switch to flip.
    g.save.set_arg("evidence", [{"name": f"e{i}"}
                                for i in range(STORM_GATE_EVIDENCE)])
    (px, py), in_light = lit_stand(g.scene)
    g.player.x, g.player.y = px, py

    for _ in range(6):
        g.state = "playing"
        g.step(1 / 30.0)

    # Warm the flood up off-camera so the recording opens on a storm that is
    # already up, already at depth, already wearing a host.
    for _ in range(int(args.warmup * 30)):
        g.player.hidden = None
        g.visibility = 0.2 if args.no_apex else args.vis
        g.state = "playing"
        g.step(1 / 30.0)
    print(f"  warmed {args.warmup:.0f}s -> {len(g._watchers)} units up")

    print(f"  scene {args.scene}  gloom {g.scene_gloom()}  "
          f"storm {g._storm_active()}  player {'in a pool' if in_light else 'in the open'}")
    if not g._storm_active():
        print("  ! no storm here -- pick a scene the dark takes "
              "(DARK_SCENES or STORM_STAGE_SCENES)")

    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    dt = 1.0 / args.fps
    frames = int(args.seconds * args.fps)
    # x264 with an explicit crf rather than imageio's default quality ladder:
    # the default put 16 seconds of a near-black scene at 31 MiB, which is
    # over the limit for handing the clip to anyone. crf 18 is visually
    # lossless here and lands ~10 MiB. Dark gradients band easily, so do not
    # push crf much past 20 for this material.
    writer = imageio.get_writer(args.out, fps=args.fps, macro_block_size=1,
                                codec="libx264", pixelformat="yuv420p",
                                output_params=["-crf", "18", "-preset", "slow"])
    stills, peak = [], 0
    for i in range(frames):
        # The player stands still and stays EXPOSED: this is a study of how
        # the flood closes, not of evasion. Visibility is pinned above the
        # apex gate (or under it) rather than played up to, so the clip
        # starts where the interesting behavior already is.
        g.player.hidden = None
        g.visibility = 0.2 if args.no_apex else args.vis
        g.state = "playing"
        g.step(dt)
        surf.fill((0, 0, 0))
        g.draw_world()
        peak = max(peak, len(g._watchers))
        writer.append_data(np.transpose(pygame.surfarray.array3d(surf),
                                        (1, 0, 2)))
        if args.stills and i % max(1, frames // args.stills) == 0:
            path = args.out.rsplit(".", 1)[0] + f"_{len(stills):02d}.png"
            pygame.image.save(surf, path)
            stills.append(path)
    writer.close()

    apex = getattr(g, "_apex", None)
    print(f"  units peaked at {peak}  |  apex "
          f"{'borne on a host' if apex and apex.get('host') else ('seeking' if apex else 'none')}")
    print(f"  wrote {args.out}" + (f" + {len(stills)} stills" if stills else ""))


if __name__ == "__main__":
    main()
