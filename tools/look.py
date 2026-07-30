"""LOOK -- a headless game that stays RUNNING, so a scene can be turned.

This is the agent's eyes. It exists because the capture tools are stills: each
angle re-boots the whole game, the frame is cropped to the player's camera
window, and the HUD, the interact prompt and the scene name are painted over
the top of it. Judging a scene through that is judging a postcard of a corner
of it with a caption across the middle.

So: ONE game process, kept alive. Talk to it and it turns, walks, changes
scene, and hands back a clean frame -- no interface, the WHOLE map in shot --
without ever re-booting. Turning is then as cheap as asking.

    python tools/look.py serve &          # boot it once, leave it up
    python tools/look.py scene shop_yard
    python tools/look.py face n           # ... e, s, w, or `spin 30`
    python tools/look.py shot             # -> writes a PNG, prints the path
    python tools/look.py quit

Commands:
    scene <key>      load a scene              face n|e|s|w   set the heading
    spin <deg>       turn by degrees           zoom fit|<f>   frame the map
    at <tx> <ty>     stand the eye on a tile   ev <n>         evidence state
    bright on|off    kill darkness + grade     hud on|off     paint interface
    shot [name]      render, save, print path  scenes         list scene keys
    where            report the current state  quit           stop the server
"""
import math
import os
import random
import socket
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

SOCK = "/tmp/threshold_look.sock"
SHOTS = "/tmp/look"
SEED = 1994
HEADINGS = {"n": -math.pi / 2, "s": math.pi / 2, "e": 0.0, "w": math.pi}


# --------------------------------------------------------------- the server
class Eyes:
    """One booted Game, held open, with the interface stubbed out."""

    def __init__(self):
        import pygame
        # The shared boot: fresh save, _start_play (player + first scene +
        # playing state), a FROZEN clock and position-stable ids, so two shots
        # of an unchanged scene are byte-identical and a difference means the
        # scene changed rather than the weather did.
        from tools.capture_world import _boot_game
        pygame.init()
        random.seed(SEED)
        self.pygame = pygame
        self.g = _boot_game()
        self.key = None
        self.heading = math.pi / 2          # facing south, the authored read
        self.zoom = "fit"
        self.bright = True
        self.hud = False
        self.shots = 0
        # The world layer draws to a smaller buffer and rescales the camera to
        # match, which fights an explicitly-set zoom. Off, so what is set is
        # what is drawn.
        self.g._render_scale = 1.0
        self._mute_interface()

    def _mute_interface(self):
        """Stub every pass that paints INTERFACE rather than world.

        `draw_world` ends by painting the HUD, the interact prompt, the two
        toasts, floating speech and the caption. All of that is the player's
        furniture; in a look pass it is text across the thing being judged.
        """
        g = self.g
        for name in ("_draw_hud", "_draw_interact_prompt", "_draw_notebook_toast",
                     "_draw_save_toast", "_draw_notice"):
            if hasattr(g, name):
                setattr(g, name, lambda *a, **k: None)
        for holder in ("float_speech", "narration", "dialog"):
            obj = getattr(g, holder, None)
            if obj is not None and hasattr(obj, "draw"):
                obj.draw = lambda *a, **k: None

    def _mute_dark(self):
        """VISION.md's clean-inspection recipe: no darkness, fog, cone, grade.

        Dropping only the darkness leaves the film grade's desaturate and
        vignette on, and an inspection shot comes back murky enough to hide
        the very defect it was taken to find.
        """
        import scenes.base as _sb
        import rendering.sight as _sight
        self.g._draw_dark = lambda: None
        self.g._draw_sight_fog = lambda: None
        _sb.apply_grade = lambda *a, **k: None
        _sight.visible_factor = lambda *a, **k: 1.0

    # ---------------------------------------------------------- framing
    def _fit(self):
        """Zoom + centre so the WHOLE map is in frame at the current turn.

        The projected footprint changes as the world turns, so the fit is
        recomputed from the map's own corners every time rather than guessed
        once: project all four at the live yaw, take the box they make, and
        scale that to the window. Without this the frame is the player's
        camera window and most of the scene is off-shot.
        """
        from constants import TILE, SCREEN_W, SCREEN_H
        sc, cam = self.g.scene, self.g.camera
        if sc is None:
            return
        w, h = sc.w * TILE, sc.h * TILE
        old_scale, old_origin = cam.scale, cam.origin
        cam.scale, cam.origin = 1.0, (0, 0)
        pts = []
        for wx in (0, w):
            for wy in (0, h):
                for wz in (0, 30):          # ground and roughly wall-top
                    pts.append(cam.project(wx - self.g.cam_x, wy - self.g.cam_y, wz))
        cam.scale, cam.origin = old_scale, old_origin
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        bw, bh = max(1e-6, max(xs) - min(xs)), max(1e-6, max(ys) - min(ys))
        if self.zoom == "fit":
            s = min(SCREEN_W * 0.94 / bw, SCREEN_H * 0.94 / bh)
        else:
            s = float(self.zoom)
        cam.scale = s
        cx, cy = (min(xs) + max(xs)) / 2 * s, (min(ys) + max(ys)) / 2 * s
        cam.origin = (SCREEN_W / 2 - cx, SCREEN_H / 2 - cy)

    def _aim(self):
        g = self.g
        g.look.body = self.heading
        g.look.aim = self.heading
        g.look.cam_yaw = self.heading + math.pi / 2
        g._update_camera(snap=True)
        g.camera.yaw = g.look.cam_yaw       # _update_camera never sets yaw

    # ---------------------------------------------------------- commands
    def do(self, line):
        parts = line.split()
        if not parts:
            return "?"
        cmd, args = parts[0], parts[1:]
        fn = getattr(self, "c_" + cmd, None)
        if fn is None:
            return "unknown command %r" % cmd
        try:
            return fn(*args)
        except Exception as e:
            return "ERROR %s: %r" % (cmd, e)

    def c_scenes(self):
        from scenes import SCENE_BUILDERS
        return " ".join(sorted(SCENE_BUILDERS))

    def c_scene(self, key):
        self.g.load_scene_now(key)
        self.key = key
        self._aim()
        return "scene %s (%dx%d tiles)" % (key, self.g.scene.w, self.g.scene.h)

    def c_face(self, d):
        d = d[0].lower()
        if d not in HEADINGS:
            return "face takes n/e/s/w"
        self.heading = HEADINGS[d]
        self._aim()
        return "facing %s" % d

    def c_spin(self, deg):
        self.heading += math.radians(float(deg))
        self._aim()
        return "heading %.0f deg" % math.degrees(self.heading)

    def c_zoom(self, z):
        self.zoom = "fit" if z == "fit" else float(z)
        return "zoom %s" % z

    def c_at(self, tx, ty):
        from constants import TILE
        self.g.player.x = (float(tx) + 0.5) * TILE
        self.g.player.y = (float(ty) + 0.5) * TILE
        self._aim()
        return "eye at tile %s,%s" % (tx, ty)

    def c_ev(self, n):
        self.g.save.set_arg("evidence", [{"name": "look%d" % i, "content": "x"}
                                         for i in range(int(n))])
        if self.key:
            self.c_scene(self.key)
        return "evidence %s" % n

    def c_bright(self, on="on"):
        self.bright = (on == "on")
        return "bright %s" % on

    def c_hud(self, on="off"):
        self.hud = (on == "on")
        return "hud %s (needs a restart to paint again)" % on

    def c_where(self):
        return ("scene=%s heading=%.0fdeg zoom=%s bright=%s"
                % (self.key, math.degrees(self.heading) % 360, self.zoom,
                   self.bright))

    def c_shot(self, name=None):
        from constants import SCREEN_W, SCREEN_H
        if self.g.scene is None:
            return "load a scene first"
        if self.bright:
            self._mute_dark()
        random.seed(SEED)
        self.g.notice_text, self.g.notice_t = None, 0.0
        self._aim()
        self._fit()
        surf = self.pygame.Surface((SCREEN_W, SCREEN_H))
        self.g.screen = surf
        try:
            from scenes import base as _sb
            _sb._GREY_CACHE["frame"] = None
        except Exception:
            pass
        self.g.draw_world()
        os.makedirs(SHOTS, exist_ok=True)
        self.shots += 1
        out = os.path.join(SHOTS, name or ("%s_%03d.png" % (self.key, self.shots)))
        if not out.endswith(".png"):
            out += ".png"
        self.pygame.image.save(surf, out)
        return out

    def c_quit(self):
        return "__quit__"


def serve():
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    eyes = Eyes()
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK)
    srv.listen(4)
    print("look: up", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            line = conn.recv(65536).decode().strip()
            reply = eyes.do(line)
            if reply == "__quit__":
                conn.sendall(b"bye")
                break
            conn.sendall((reply or "ok").encode())
    srv.close()
    os.unlink(SOCK)


def client(argv):
    if not os.path.exists(SOCK):
        return "look is not running -- start it with: python tools/look.py serve &"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(180)
    s.connect(SOCK)
    s.sendall(" ".join(argv).encode())
    out = s.recv(1 << 20).decode()
    s.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
    elif len(sys.argv) > 1:
        print(client(sys.argv[1:]))
    else:
        print(__doc__)
