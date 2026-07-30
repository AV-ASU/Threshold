"""LOOK -- one running game you can look at, EDIT, and PLAY.

This is the agent's workbench, and it is deliberately ONE tool. There were
forty-seven, each booting its own game, each with its own flags and its own
idea of what to print, so every job started by picking between sporks. Worse,
none of them could do the thing that actually matters: change something and
see the change. They rendered stills of a world you could not touch.

So this holds ONE game open and answers three kinds of question:

  LOOK   load a scene, turn it, walk the eye around, zoom into a corner,
         preview a prop on its own, in daylight or in the dark.
  EDIT   move a wall, drop a prop, cut a doorway, place a person -- and the
         answer to every edit is a fresh picture of what you just did.
  PLAY   stop editing and drive it with the real controls: walk in from the
         road, press E on the door, get seen. The game, not a screenshot.

Every editing command re-renders and prints the PNG path, because an edit you
cannot see is a guess. `save` writes the scene out as a layout file, which is
the data form scenes are moving to.

    python tools/look.py serve &        # boot once, leave it up
    python tools/look.py scene shop_yard
    python tools/look.py put woodpile 12 9
    python tools/look.py play
    python tools/look.py walk w 20

Run `python tools/look.py help` for the full verb list.
"""
import json
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
LAYOUTS = os.path.join(_ROOT, "scenes", "layouts")
SEED = 1994
HEADINGS = {"n": -math.pi / 2, "s": math.pi / 2, "e": 0.0, "w": math.pi}
KEYNAMES = ("w", "a", "s", "d", "e", "f", "i", "n", "space", "return", "escape",
            "up", "down", "left", "right")


class Eyes:
    """One booted Game, held open: looked at, edited, and played."""

    def __init__(self):
        import pygame
        # The shared boot: fresh save, _start_play (player + first scene +
        # playing state), a FROZEN clock and position-stable ids, so two shots
        # of an unchanged scene are identical and any difference is the scene
        # changing rather than the weather.
        from tools.capture_world import _boot_game
        pygame.init()
        random.seed(SEED)
        self.pg = pygame
        self.g = _boot_game()
        self.key = None
        self.heading = math.pi / 2
        self.zoom = "fit"
        self.bright = True
        self.mode = "look"          # look | play
        self.shots = 0
        self.edits = []             # what this session changed, for save/diff
        self.undo = []
        self.g._render_scale = 1.0
        self._muted = {}
        self._fixed = {}
        self._mute_interface()
        self._learn_caches()

    # ------------------------------------------------------ presentation
    def _mute_interface(self):
        """Silence every pass that paints INTERFACE rather than world.

        `draw_world` ends by painting the HUD, the interact prompt, the two
        toasts, speech and the caption. In a look pass that is text across the
        thing being judged. PLAY mode puts them all back, because then the
        interface is part of what is being judged.
        """
        g = self.g
        for name in ("_draw_hud", "_draw_interact_prompt", "_draw_notebook_toast",
                     "_draw_save_toast", "_draw_notice"):
            if hasattr(g, name) and name not in self._muted:
                self._muted[name] = getattr(g, name)
                setattr(g, name, lambda *a, **k: None)

    def _unmute_interface(self):
        for name, fn in self._muted.items():
            setattr(self.g, name, fn)
        self._muted = {}

    def _mute_dark(self):
        """VISION.md's clean-inspection recipe: no darkness, fog, cone, grade.

        Dropping only the darkness leaves the grade's desaturate and vignette
        on, and the shot comes back murky enough to hide the defect it was
        taken to find.
        """
        import scenes.base as _sb
        import rendering.sight as _sight
        self.g._draw_dark = lambda: None
        self.g._draw_sight_fog = lambda: None
        _sb.apply_grade = lambda *a, **k: None
        _sight.visible_factor = lambda *a, **k: 1.0

    def _fit(self):
        """Zoom + centre so the WHOLE map is in frame at the current turn.

        The projected footprint changes as the world turns, so this is
        recomputed from the map's own corners every time: project all four at
        the live yaw, take the box they make, scale it to the window. A fixed
        zoom frames one angle and crops the other three.
        """
        from constants import TILE, SCREEN_W, SCREEN_H
        sc, cam = self.g.scene, self.g.camera
        if sc is None:
            return
        w, h = sc.w * TILE, sc.h * TILE
        old = (cam.scale, cam.origin)
        cam.scale, cam.origin = 1.0, (0, 0)
        pts = [cam.project(wx - self.g.cam_x, wy - self.g.cam_y, wz)
               for wx in (0, w) for wy in (0, h) for wz in (0, 30)]
        cam.scale, cam.origin = old
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        bw, bh = max(1e-6, max(xs) - min(xs)), max(1e-6, max(ys) - min(ys))
        s = (min(SCREEN_W * 0.94 / bw, SCREEN_H * 0.94 / bh)
             if self.zoom == "fit" else float(self.zoom))
        cam.scale = s
        cam.origin = (SCREEN_W / 2 - (min(xs) + max(xs)) / 2 * s,
                      SCREEN_H / 2 - (min(ys) + max(ys)) / 2 * s)

    def _aim(self):
        g = self.g
        g.look.body = g.look.aim = self.heading
        g.look.cam_yaw = self.heading + math.pi / 2
        g._update_camera(snap=True)
        g.camera.yaw = g.look.cam_yaw     # _update_camera never sets yaw

    def _render(self, name=None):
        """Draw the live game to a PNG and return its path. The whole point:
        every edit answers with a picture."""
        from constants import SCREEN_W, SCREEN_H
        if self.g.scene is None:
            return "load a scene first"
        if self.bright and self.mode == "look":
            self._mute_dark()
        random.seed(SEED)
        self.g.notice_text, self.g.notice_t = None, 0.0
        if self.mode == "look":
            self._aim()
            self._fit()
        surf = self.pg.Surface((SCREEN_W, SCREEN_H))
        self.g.screen = surf
        try:
            from scenes import base as _sb
            _sb._GREY_CACHE["frame"] = None
        except Exception:
            pass
        self.g.draw_world()
        os.makedirs(SHOTS, exist_ok=True)
        self.shots += 1
        out = os.path.join(SHOTS, name or "%s_%03d" % (self.key, self.shots))
        if not out.endswith(".png"):
            out += ".png"
        self.pg.image.save(surf, out)
        return out

    # ------------------------------------------------------------ helpers
    def _tile(self, tx, ty):
        from constants import TILE
        return (int(tx) + 0.5) * TILE, (int(ty) + 0.5) * TILE

    def _decos_at(self, tx, ty, r=1):
        from constants import TILE
        cx, cy = self._tile(tx, ty)
        return [d for d in self.g.scene.decorations
                if abs(d.x - cx) <= r * TILE and abs(d.y - cy) <= r * TILE]

    def _note(self, kind, **kw):
        self.edits.append(dict(kind=kind, scene=self.key, **kw))

    # ------------------------------------------------------------ dispatch
    def do(self, line):
        parts = line.split()
        if not parts:
            return "?"
        fn = getattr(self, "c_" + parts[0], None)
        if fn is None:
            return "unknown verb %r -- try: help" % parts[0]
        try:
            return fn(*parts[1:])
        except TypeError as e:
            return "usage error on %r: %s" % (parts[0], e)
        except Exception as e:
            return "ERROR %s: %r" % (parts[0], e)

    def c_help(self):
        return __doc__ + """
LOOK   scene <key> | scenes | face n|e|s|w | spin <deg> | zoom fit|<f>
       at <tx> <ty> | close <tx> <ty> [zoom] | shot [name] | where
       bright on|off | ev <n> | kinds <word>
EDIT   put <kind> <tx> <ty> [k=v ...]   drop a prop, then SEE it
       rm <tx> <ty> [radius]            remove props at a tile
       mv <tx> <ty> <tx2> <ty2>         move what is there
       tile <tx> <ty> <char>            set an object tile (wall, door, ...)
       floor <tx> <ty> <char>           set a floor tile
       fill <x1> <y1> <x2> <y2> <char>  rectangle of object tiles
       npc <sprite> <tx> <ty> [name]    place a person
       item <key> <tx> <ty>             place a pickup
       exit <char> <target> [spawn]     make a tile a way out
       spawn <name> <tx> <ty>           name a place to arrive
       undo                             take back the last edit
PLAY   play | look                      switch mode
       key <name> | walk <w|a|s|d> <n> | step [n] | frame
SAVE   save [path] | changes | quit
"""

    # ---------------------------------------------------------------- LOOK
    def c_scenes(self):
        from scenes import SCENE_BUILDERS
        return " ".join(sorted(SCENE_BUILDERS))

    def c_scene(self, key):
        self.g.load_scene_now(key)
        self.key = key
        self.edits, self.undo = [], []
        self._aim()
        sc = self.g.scene
        return ("scene %s  %dx%d tiles, %d props, %d people -> %s"
                % (key, sc.w, sc.h, len(sc.decorations), len(sc.npcs),
                   self._render()))

    def c_face(self, d):
        d = d[0].lower()
        if d not in HEADINGS:
            return "face takes n/e/s/w"
        self.heading = HEADINGS[d]
        return "facing %s -> %s" % (d, self._render())

    def c_spin(self, deg):
        self.heading += math.radians(float(deg))
        return "heading %.0f -> %s" % (math.degrees(self.heading) % 360,
                                       self._render())

    def c_zoom(self, z):
        self.zoom = "fit" if z == "fit" else float(z)
        return "zoom %s -> %s" % (z, self._render())

    def c_at(self, tx, ty):
        self.g.player.x, self.g.player.y = self._tile(tx, ty)
        return "eye at %s,%s -> %s" % (tx, ty, self._render())

    def c_close(self, tx, ty, zoom="3"):
        """Stand at a tile and zoom in -- the middle altitude between a prop
        on its own and the whole map, which is where placement defects live."""
        self.g.player.x, self.g.player.y = self._tile(tx, ty)
        old = self.zoom
        self.zoom = float(zoom)
        out = self._render()
        self.zoom = old
        return "close on %s,%s -> %s" % (tx, ty, out)

    def c_shot(self, name=None):
        return self._render(name)

    def c_bright(self, on="on"):
        self.bright = (on == "on")
        return "bright %s -> %s" % (on, self._render())

    def c_ev(self, n):
        self.g.save.set_arg("evidence", [{"name": "look%d" % i, "content": "x"}
                                         for i in range(int(n))])
        if self.key:
            self.g.load_scene_now(self.key)
        return "evidence %s -> %s" % (n, self._render())

    def c_kinds(self, word=""):
        """What is this kind registered as? The question that decides whether
        a prop draws as a volume or ships as a flat magenta stain."""
        from rendering.props import SOLID_PROPS, _STANDEE_KINDS
        from rendering.assemblies import ASSEMBLIES
        from rendering.furniture import FURNITURE
        from scenes.terrain import (_FLOOR_DECAL_KINDS, _SURFACE_DECAL_KINDS,
                                    _WALL_DECO_KINDS, _TABLETOP_PROP_KINDS)
        tables = [("assembly", ASSEMBLIES), ("solid", SOLID_PROPS),
                  ("standee", _STANDEE_KINDS), ("furniture", FURNITURE),
                  ("floor-decal", _FLOOR_DECAL_KINDS),
                  ("surface-decal", _SURFACE_DECAL_KINDS),
                  ("wall-deco", _WALL_DECO_KINDS),
                  ("tabletop", _TABLETOP_PROP_KINDS)]
        names = set()
        for _n, t in tables:
            names |= set(t)
        rows = []
        for k in sorted(n for n in names if word in n):
            where = [n for n, t in tables if k in t]
            rows.append("  %-22s %s" % (k, ", ".join(where) or "NOWHERE"))
        return "\n".join(rows) or "no kind matching %r" % word

    def c_where(self):
        from constants import TILE
        sc = self.g.scene
        return ("scene=%s %dx%d  eye=%.0f,%.0f (tile %d,%d)  heading=%.0f  "
                "zoom=%s bright=%s mode=%s  edits=%d"
                % (self.key, sc.w, sc.h, self.g.player.x, self.g.player.y,
                   self.g.player.x // TILE, self.g.player.y // TILE,
                   math.degrees(self.heading) % 360, self.zoom, self.bright,
                   self.mode, len(self.edits)))

    # ---------------------------------------------------------------- EDIT
    def c_put(self, kind, tx, ty, *kv):
        from entities.decoration import Decoration
        kwargs = {}
        for pair in kv:
            k, _, v = pair.partition("=")
            for cast in (int, float):
                try:
                    v = cast(v)
                    break
                except ValueError:
                    pass
            else:
                v = {"true": True, "false": False}.get(str(v).lower(), v)
            kwargs[k] = v
        x, y = self._tile(tx, ty)
        d = Decoration(x, y, kind, **kwargs)
        self.g.scene.decorations.append(d)
        self.undo.append(("rm-deco", d))
        self._note("put", what=kind, tx=int(tx), ty=int(ty), kwargs=kwargs)
        return "put %s at %s,%s -> %s" % (kind, tx, ty, self._render())

    def c_rm(self, tx, ty, radius="0"):
        gone = self._decos_at(tx, ty, int(radius))
        for d in gone:
            self.g.scene.decorations.remove(d)
        self.undo.append(("add-decos", gone))
        self._note("rm", tx=int(tx), ty=int(ty), removed=[d.kind for d in gone])
        return ("removed %s -> %s"
                % ([d.kind for d in gone] or "nothing", self._render()))

    def c_mv(self, tx, ty, tx2, ty2):
        from constants import TILE
        movers = self._decos_at(tx, ty)
        dx = (int(tx2) - int(tx)) * TILE
        dy = (int(ty2) - int(ty)) * TILE
        for d in movers:
            d.x += dx
            d.y += dy
        self.undo.append(("shift", movers, -dx, -dy))
        self._note("mv", frm=[int(tx), int(ty)], to=[int(tx2), int(ty2)],
                   what=[d.kind for d in movers])
        return ("moved %s -> %s"
                % ([d.kind for d in movers] or "nothing", self._render()))

    def _set_cell(self, grid, tx, ty, ch):
        tx, ty = int(tx), int(ty)
        was = grid[ty][tx]
        grid[ty][tx] = ch
        return was

    def c_tile(self, tx, ty, ch):
        was = self._set_cell(self.g.scene.objects, tx, ty, ch)
        self.undo.append(("obj", int(tx), int(ty), was))
        self._note("tile", tx=int(tx), ty=int(ty), ch=ch, was=was)
        self._retile()
        return "tile %s,%s %r -> %r -> %s" % (tx, ty, was, ch, self._render())

    def c_floor(self, tx, ty, ch):
        was = self._set_cell(self.g.scene.floor, tx, ty, ch)
        self.undo.append(("flr", int(tx), int(ty), was))
        self._note("floor", tx=int(tx), ty=int(ty), ch=ch, was=was)
        self._retile()
        return "floor %s,%s %r -> %r -> %s" % (tx, ty, was, ch, self._render())

    def c_fill(self, x1, y1, x2, y2, ch):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        back = []
        for ty in range(min(y1, y2), max(y1, y2) + 1):
            for tx in range(min(x1, x2), max(x1, x2) + 1):
                back.append((tx, ty, self._set_cell(self.g.scene.objects, tx, ty, ch)))
        self.undo.append(("objs", back))
        self._note("fill", rect=[x1, y1, x2, y2], ch=ch)
        self._retile()
        return "filled %d tiles with %r -> %s" % (len(back), ch, self._render())

    def _caches(self):
        """Every module-level render cache, by name."""
        import scenes.base as _sb
        import scenes.terrain as _t
        out = []
        for mod in (_t, _sb):
            for name in dir(mod):
                if name.endswith("CACHE"):
                    c = getattr(mod, name)
                    if isinstance(c, dict):
                        out.append((name, c))
        return out

    def _learn_caches(self):
        """Note which caches are FIXED-SHAPE before anything is edited.

        Most caches are plain lookup tables and can be emptied. Four are
        single-slot records (`{"key":..., "surf":...}`) whose readers index
        those keys directly, so emptying one raises KeyError on the very next
        frame and every later command dies with it. Learn the shapes up front
        and reset those instead of clearing them.
        """
        self._fixed = {name: tuple(c.keys()) for name, c in self._caches()
                       if c and all(isinstance(k, str) for k in c)}

    def _retile(self):
        """Drop the render caches so an edited tile actually redraws.

        Tiles are cached BY CHARACTER and per scene, so without this an edit
        changes the grid and the picture comes back identical, which would make
        the whole tool lie about what it just did.
        """
        for name, c in self._caches():
            if name in getattr(self, "_fixed", {}):
                for k in self._fixed[name]:
                    c[k] = None
            else:
                c.clear()
        sc = self.g.scene
        for attr in ("_surface_tops", "_door_views"):
            v = getattr(sc, attr, None)
            if isinstance(v, dict):
                v.clear()

    def c_npc(self, sprite, tx, ty, name=None):
        from entities.npc import NPC
        x, y = self._tile(tx, ty)
        n = NPC(x, y, name or sprite.title(), sprite, movement="idle")
        self.g.scene.npcs.append(n)
        self.undo.append(("rm-npc", n))
        self._note("npc", what=sprite, tx=int(tx), ty=int(ty))
        return "placed %s at %s,%s -> %s" % (sprite, tx, ty, self._render())

    def c_item(self, key, tx, ty):
        x, y = self._tile(tx, ty)
        self.g.scene.add_item(x, y, key)
        self._note("item", what=key, tx=int(tx), ty=int(ty))
        return "item %s at %s,%s -> %s" % (key, tx, ty, self._render())

    def c_exit(self, ch, target, spawn="default"):
        self.g.scene.add_exit(ch, target, spawn)
        self._note("exit", ch=ch, target=target, spawn=spawn)
        return "exit %r -> %s (%s)" % (ch, target, spawn)

    def c_spawn(self, name, tx, ty):
        self.g.scene.set_spawn(name, int(tx), int(ty))
        self._note("spawn", name=name, tx=int(tx), ty=int(ty))
        return "spawn %s at %s,%s" % (name, tx, ty)

    def c_undo(self):
        if not self.undo:
            return "nothing to undo"
        act = self.undo.pop()
        sc = self.g.scene
        if act[0] == "rm-deco":
            sc.decorations.remove(act[1])
        elif act[0] == "add-decos":
            sc.decorations.extend(act[1])
        elif act[0] == "shift":
            for d in act[1]:
                d.x += act[2]
                d.y += act[3]
        elif act[0] == "rm-npc":
            sc.npcs.remove(act[1])
        elif act[0] == "obj":
            sc.objects[act[2]][act[1]] = act[3]
            self._retile()
        elif act[0] == "flr":
            sc.floor[act[2]][act[1]] = act[3]
            self._retile()
        elif act[0] == "objs":
            for tx, ty, was in act[1]:
                sc.objects[ty][tx] = was
            self._retile()
        if self.edits:
            self.edits.pop()
        return "undone %s -> %s" % (act[0], self._render())

    def c_changes(self):
        return json.dumps(self.edits, indent=1) if self.edits else "no edits"

    # ---------------------------------------------------------------- PLAY
    def c_play(self):
        """Hand the game back its interface and its darkness and play it.

        A scene judged only in the clean inspection view is judged in a light
        no player ever sees; this is the same room under the rules.
        """
        self.mode = "play"
        self._unmute_interface()
        self.g.camera.scale = 1.0
        self.g._update_camera(snap=True)
        return "PLAY mode -- walk/key/step; `look` to go back -> %s" % self._render()

    def c_look(self):
        self.mode = "look"
        self._mute_interface()
        return "LOOK mode -> %s" % self._render()

    def _press(self, name, down=True):
        pg = self.pg
        code = getattr(pg, "K_" + name, None)
        if code is None:
            return False
        ev = pg.event.Event(pg.KEYDOWN if down else pg.KEYUP, key=code,
                            unicode="", mod=0, scancode=0)
        self.g.handle_event(ev)
        return True

    def c_key(self, name, *rest):
        if not self._press(name, True):
            return "no such key %r (try: %s)" % (name, ", ".join(KEYNAMES))
        self.g.step(1 / 60)
        self._press(name, False)
        return "pressed %s -> %s" % (name, self._render())

    def c_walk(self, d, steps="10"):
        """Hold a direction for N frames, the way a player holds a key.

        Movement is read from the held-key state each frame, so a press and an
        immediate release moves nobody: the key has to STAY down while the
        frames tick.
        """
        pg = self.pg
        code = getattr(pg, "K_" + d, None)
        if code is None:
            return "walk takes w/a/s/d"
        held = {}

        class _K(dict):
            def __getitem__(self, k):
                return k == code

            def __call__(self, *a):
                return self
        real = pg.key.get_pressed
        pg.key.get_pressed = _K()
        try:
            for _ in range(int(steps)):
                self.g.step(1 / 60)
        finally:
            pg.key.get_pressed = real
        return ("walked %s x%s -> %s  %s"
                % (d, steps, self._render(), self.c_where()))

    def c_step(self, n="1"):
        for _ in range(int(n)):
            self.g.step(1 / 60)
        return "stepped %s -> %s" % (n, self._render())

    def c_frame(self):
        return self._render()

    # ---------------------------------------------------------------- SAVE
    def c_save(self, path=None):
        """Write the live scene out as a LAYOUT -- the data form scenes are
        moving to. Uses the game's own format (`scenes/layout.py`), so what
        this tool writes is exactly what the game reads."""
        from scenes.layout import dump
        out = dump(self.g.scene, path)
        return "saved %s (%d props, %d people, %d edits this session)" % (
            out, len(self.g.scene.decorations), len(self.g.scene.npcs),
            len(self.edits))

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
        return "look is not running -- start it: python tools/look.py serve &"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(300)
    s.connect(SOCK)
    s.sendall(" ".join(argv).encode())
    out = s.recv(1 << 22).decode()
    s.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
    elif len(sys.argv) > 1:
        print(client(sys.argv[1:]))
    else:
        print(__doc__)
