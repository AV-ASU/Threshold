"""Four-facing capture for ONE scene -- the VISION.md look-pass harness.

    python tools/capture_facings.py <scene_key> [--px X --py Y] [--bright] [--tag T]

Writes /tmp/facings_<tag>/<key>_{N,E,S,W}.png plus a labelled contact sheet
`<key>_sheet.png`, and PRINTS a per-pair difference report.

**Why this tool exists.** `Game._update_camera` sets the camera POSITION only,
never its yaw -- the yaw is copied from `look.cam_yaw` inside `_update_look`,
which the ad-hoc render path never runs. Skip the explicit `camera.yaw = ...`
and every "facing" renders at yaw 0, so a four-facing sheet is NORTH four
times. That has now shipped twice as "verified all four facings" (VISION.md
records the first; the lost-space islands were the second). So this tool sets
the yaw itself AND asserts the frames actually differ -- if the yaw silently
stops taking, the run FAILS instead of handing back four norths.

`--ev N` sets the evidence count, so a storm-staged outdoor scene can be
judged at the darkness the player actually meets it in (ev0 is daylight).
`--bright` drops the sight cone + film grade for clean geometry inspection;
without it you get the real player view (dark overlay, fog, grade).
`--tick N` runs the scene's on_update N times first, so content that only
exists once the scene has updated (spawned crews, relocating lights) is
actually in frame instead of silently absent.
"""
import os
import sys
import math
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import random
import pygame
from tools.capture_world import _boot_game
from systems.look_control import wrap

# heading per facing; the camera sits behind it (heading + pi/2)
FACINGS = (("N", -math.pi / 2, (0, -1)), ("E", 0.0, (1, 0)),
           ("S", math.pi / 2, (0, 1)), ("W", math.pi, (-1, 0)))
SEED = 7


def _place_creature(g, spec):
    """Drop a creature into the loaded scene so it can be LOOKED at in a real
    room, at all four facings, in the light the player actually meets.

    This gap is why "black creature on a black floor" shipped: every creature
    was judged on a preview card with a chosen backdrop, and nothing put one in
    an actual dark scene. `spec` is "kind[:seed][@TX,TY]", e.g. "amalgam:3" or
    "amalgam:3@12,9"; default position is a couple of tiles in front of the
    player so it lands inside the sight cone.

    The special kind **apex** drops the Mask-bearer rather than an
    ordinary unit: the host flags plus the `Game._apex` state its face and its
    grabbing limbs are read from, wound to full intent. Without it the bearer
    draws as a plain amalgam and the two features the apex exists for are
    invisible in the one tool meant to check them."""
    import math as _m
    from entities.npc import NPC
    from constants import TILE as _T
    kind, _, rest = spec.partition(":")
    seed, _, at = rest.partition("@")
    if at:
        atx, _, aty = at.partition(",")
        cx, cy = (int(atx) + 0.5) * _T, (int(aty) + 0.5) * _T
    else:
        fx, fy = getattr(g.player, "facing", (0, 1))
        n = _m.hypot(fx, fy) or 1.0
        cx = g.player.x + fx / n * _T * 2.6
        cy = g.player.y + fy / n * _T * 2.6
    apex = (kind == "apex")
    w = NPC(cx, cy, "", "amalgam" if apex else (kind or "amalgam"),
            voice="blip_low",
            portrait="watcher", movement="watch", speed=0.0,
            no_prompt=True, solid=False)
    w.tag = "watcher"
    w.dialogue_fn = None
    w.sprite_seed = int(seed) if seed.strip().isdigit() else 3
    w._birth = 1.0
    if apex:
        from systems.config import APEX_EXTRA_HI
        w._apex = True
        w._apex_extra = APEX_EXTRA_HI
        g._apex = {"state": "borne", "cd": 0.0, "host": w, "seed": w.sprite_seed,
                   "roared": True,
                   "face": {"intent": 1.0, "strain": 0.85, "t": 3.0}}
        g._watchers.append(w)
    g.scene.add_npc(w)
    return w


def capture(g, key, heading, facing_vec, px=None, py=None, bright=False,
            ticks=0, ev=0, spawn=None):
    random.seed(SEED)
    try:
        import numpy as np
        np.random.seed(SEED)
    except Exception:
        pass
    # The surface world darkens with UNDERSTANDING, not a clock (the storm,
    # DESIGN.md §2): an outdoor scene at ev0 is full daylight and the same
    # scene at ev3 is night. Capturing only the default ev0 means a
    # STORM_STAGE_SCENES look pass never sees the state most of the game is
    # played in, so the ev the shot is judged at has to be selectable.
    if ev:
        g.save.set_arg("evidence", [{"name": f"cap_ev{i}", "content": "x"}
                                    for i in range(ev)])
    g.load_scene_now(key)
    # A look pass judges the ROOM, and a scene's on_enter tutorial notice
    # paints a black band across the middle of every one of the four frames.
    # The clock does not advance here, so it never times out on its own.
    g.notice_text = None
    g.notice_t = 0.0
    g.look.body = wrap(heading)
    g.look.aim = wrap(heading)
    g.look.cam_yaw = wrap(heading + math.pi / 2)
    # THE LINE THIS TOOL EXISTS FOR: _update_camera never touches yaw.
    g.camera.yaw = g.look.cam_yaw
    try:
        g.player.facing = facing_vec
    except Exception:
        pass
    if px is not None:
        g.player.x = px
    if py is not None:
        g.player.y = py
    # Some content only exists after the scene's own update has run (spawned
    # crews, relocating lights, anything driven by on_update). Tick it at the
    # player's final position BEFORE drawing, or the capture shows an empty
    # world and quietly lies about what the player would meet.
    for _ in range(ticks):
        fn = getattr(g.scene, "on_update_fn", None)
        if fn:
            fn(g, g.scene, 0.1)
    if spawn:
        _place_creature(g, spawn)
    g._update_camera(snap=True)
    g.camera.yaw = g.look.cam_yaw          # re-assert (snap may re-run lerps)
    if bright:
        # VISION.md's clean-inspection recipe, in full: drop the darkness, the
        # blind-spot fog, the sight CONE, and the film GRADE. Dropping only the
        # first two leaves the grade's desaturate+vignette on, so "bright" came
        # back murky and near-indistinguishable from the player view -- which
        # is exactly how a geometry defect hides in an inspection shot.
        g._draw_dark = lambda: None
        g._draw_sight_fog = lambda: None
        import scenes.base as _sb
        import rendering.sight as _sight
        _sb.apply_grade = lambda *a, **k: None
        _sight.visible_factor = lambda *a, **k: 1.0
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    try:
        from scenes import base as _sb
        _sb._GREY_CACHE["frame"] = None
    except Exception:
        pass
    g.draw_world()
    return surf.copy()


def _frac_diff(a, b):
    """Fraction of pixels differing between two same-size Surfaces."""
    from PIL import Image, ImageChops
    ia = Image.frombytes("RGB", a.get_size(), pygame.image.tostring(a, "RGB"))
    ib = Image.frombytes("RGB", b.get_size(), pygame.image.tostring(b, "RGB"))
    diff = ImageChops.difference(ia, ib)
    changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
    return changed / float(ia.width * ia.height)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--px", type=float, default=None)
    ap.add_argument("--py", type=float, default=None)
    ap.add_argument("--bright", action="store_true")
    ap.add_argument("--tick", type=int, default=0,
                    help="run the scene's on_update N times before drawing "
                         "(for spawned/driven content)")
    ap.add_argument("--ev", type=int, default=0,
                    help="evidence count -> rot stage -> storm darkness "
                         "(a STORM_STAGE_SCENES look pass at ev0 is daylight)")
    ap.add_argument("--spawn", metavar="KIND[:SEED][@TX,TY]", default=None,
                    help="drop a creature in the room first, so it is judged "
                         "in a real scene rather than on a preview card. "
                         "KIND 'apex' drops the Mask-bearer with its face and "
                         "its reach live.")
    ap.add_argument("--tag", default="look")
    args = ap.parse_args()

    out = f"/tmp/facings_{args.tag}"
    os.makedirs(out, exist_ok=True)
    g = _boot_game()
    shots = {}
    for name, heading, fv in FACINGS:
        shots[name] = capture(g, args.scene, heading, fv,
                              args.px, args.py, args.bright, args.tick,
                              args.ev, args.spawn)
        pygame.image.save(shots[name], f"{out}/{args.scene}_{name}.png")
        print(f"  wrote {out}/{args.scene}_{name}.png")

    # SELF-CHECK: consecutive facings must differ, or the yaw never took.
    print("\n  facing-difference report (N-E, E-S, S-W, W-N):")
    ok = True
    order = ["N", "E", "S", "W", "N"]
    for i in range(4):
        a, b = order[i], order[i + 1]
        f = _frac_diff(shots[a], shots[b])
        flag = "OK" if f > 0.02 else "IDENTICAL -- YAW NEVER TOOK"
        if f <= 0.02:
            ok = False
        print(f"    {a}->{b}: {f*100:6.2f}% of pixels differ   {flag}")

    from PIL import Image, ImageDraw
    ims = [(n, Image.frombytes("RGB", shots[n].get_size(),
                               pygame.image.tostring(shots[n], "RGB")))
           for n, _h, _v in FACINGS]
    w, h, lab, pad = ims[0][1].width, ims[0][1].height, 22, 8
    sheet = Image.new("RGB", (w * 2 + pad * 3, (h + lab) * 2 + pad * 3), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        r, c = divmod(i, 2)
        x, y = pad + c * (w + pad), pad + r * (h + lab)
        d.text((x + 2, y + 4), f"{args.scene}  facing {n}", fill=(232, 232, 180))
        sheet.paste(im, (x, y + lab))
    sheet.save(f"{out}/{args.scene}_sheet.png")
    print(f"\n  wrote {out}/{args.scene}_sheet.png")

    if not ok:
        print("\nFAIL: at least one facing pair is identical -- the camera yaw "
              "did not take. Do NOT treat this as a verified look pass.")
        sys.exit(1)
    print("\nPASS: all four facings are genuinely distinct.")


if __name__ == "__main__":
    main()
