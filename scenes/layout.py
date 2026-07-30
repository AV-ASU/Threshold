"""LAYOUTS -- a scene as saved data, and the loader that reads it back.

Scenes used to exist only as hand-written builder functions, so the only way to
change a room was to edit code and re-run it, and the only way to know what a
room held was to read the function that made it. A layout is that same room
written down: the tiles, the props, the people, the ways in and out.

TWO RULES DECIDE WHAT GOES IN.

**Placement is data; behaviour is not.** Every tile, every prop and its kwargs,
every spawn travels as data. A scene's `on_enter` / `on_update` / `on_exit` /
`on_interact`, and the words a person says, are FUNCTIONS: they travel as
`module:name` and are imported back at load. So a layout can move a woodpile
but can never invent what happens when you knock on the door, which is the
right split -- placement is a thing you look at, behaviour is a thing you write.

**Anything else the builder stashed travels too, generically.** Builders hang
their own attributes on a scene (where the bell door is, which tiles are
bridge, where the chalk doors are) and those matter. Rather than maintain a
list of fields that is always one short, everything plain is written out and
read back, with tuples and sets preserved -- JSON has neither, and a face
direction that comes back as a list instead of a pair is a person facing
nowhere.

    from scenes.layout import dump, build_from_layout, has_layout
    dump(scene)                       # -> scenes/layouts/<key>.json
    sc = build_from_layout("shop_yard")

Guarded by `tests/layouts.py`, which builds every scene, dumps it, reads it
back, and compares the two field by field.
"""
import importlib
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
LAYOUT_DIR = os.path.join(_HERE, "layouts")

# Handled explicitly below; everything else on the scene rides in `attrs`.
_STRUCTURAL = {"key", "floor", "objects", "decorations", "npcs",
               "on_enter_fn", "on_update_fn", "on_exit_fn", "on_interact_fn"}

# Per-frame scratch. Writing it down would record one session's noise as if it
# were part of the room.
_SCRATCH = {"_door_anim", "_door_views", "_noise_events", "_noise_mask",
            "_noise_now", "_last_step_event", "_surface_tops", "_render_band",
            "_ground_hf", "projectiles", "enemies"}

_OVERRIDES = {}          # name -> callable, for behaviour that cannot be imported


def register(name, fn):
    """Force a name to resolve to this function (rarely needed: a hook is
    normally found by importing the module it was defined in)."""
    _OVERRIDES[name] = fn


# ----------------------------------------------------------------- encoding
def _enc(v):
    """JSON has no tuples and no sets, and both carry meaning here."""
    if isinstance(v, tuple):
        return {"()": [_enc(x) for x in v]}
    if isinstance(v, set):
        return {"{}": sorted((_enc(x) for x in v), key=repr)}
    if isinstance(v, list):
        return [_enc(x) for x in v]
    if isinstance(v, dict):
        return {k: _enc(x) for k, x in v.items()}
    return v


def _dec(v):
    if isinstance(v, dict):
        if set(v) == {"()"}:
            return tuple(_dec(x) for x in v["()"])
        if set(v) == {"{}"}:
            return set(_dec(x) for x in v["{}"])
        return {k: _dec(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_dec(x) for x in v]
    return v


def _enc_refs(v, npc_index):
    """Encode a value that may POINT AT people in this same scene.

    `works_sign` keeps a handle on Mara and on the kneeling rank so the
    calling-out can find them. Those are the scene's own people, so they travel
    as their position in the cast rather than as unwritable objects.
    """
    if id(v) in npc_index:
        return {"npc": npc_index[id(v)]}
    if isinstance(v, list):
        return [_enc_refs(x, npc_index) for x in v]
    if isinstance(v, tuple):
        return {"()": [_enc_refs(x, npc_index) for x in v]}
    return None if not _plain(v) else _enc(v)


def _dec_refs(v, npcs):
    if isinstance(v, dict):
        if set(v) == {"npc"}:
            return npcs[v["npc"]]
        if set(v) == {"()"}:
            return tuple(_dec_refs(x, npcs) for x in v["()"])
    if isinstance(v, list):
        return [_dec_refs(x, npcs) for x in v]
    return _dec(v)


def _refs_ok(v, npc_index):
    """True if this value is people, or plain, or a mix of the two."""
    if id(v) in npc_index or _plain(v):
        return True
    if isinstance(v, (list, tuple)):
        return bool(v) and all(_refs_ok(x, npc_index) for x in v)
    return False


def _plain(v):
    """Can this value be written down and read back unchanged?"""
    if v is None or isinstance(v, (bool, int, float, str)):
        return True
    if isinstance(v, (list, tuple, set)):
        return all(_plain(x) for x in v)
    if isinstance(v, dict):
        return all(isinstance(k, str) and _plain(x) for k, x in v.items())
    return False


# ----------------------------------------------------------------- behaviour
def _fn_name(fn):
    """`module:qualname`, so the loader can import the behaviour back.

    A closure (dialogue is usually built per person) has no importable name; it
    is recorded with a `?` so the failure at load names what went missing
    instead of quietly handing back a mute character.
    """
    if fn is None:
        return None
    for name, known in _OVERRIDES.items():
        if known is fn:
            return name
    mod = getattr(fn, "__module__", None)
    qual = getattr(fn, "__qualname__", "")
    if mod and qual and "<locals>" not in qual:
        return "%s:%s" % (mod, qual)
    return "?" + (qual or repr(fn))


def _fn(name, who=""):
    if not name:
        return None
    if name in _OVERRIDES:
        return _OVERRIDES[name]
    if name.startswith("?"):
        raise KeyError(
            "%s names %r, which is a closure with no importable name. "
            "Behaviour stays in code: call scenes.layout.register(name, fn) "
            "where it is built." % (who or "this layout", name[1:]))
    mod, _, qual = name.partition(":")
    obj = importlib.import_module(mod)
    for part in qual.split("."):
        obj = getattr(obj, part)
    return obj


def layout_path(key):
    return os.path.join(LAYOUT_DIR, "%s.json" % key)


def has_layout(key):
    return os.path.exists(layout_path(key))


# ---------------------------------------------------------------- dump/load
def _npc_index(sc):
    return {id(n): i for i, n in enumerate(sc.npcs)}


def dump(sc, path=None):
    """Write a built Scene out as a layout."""
    lay = {
        "key": sc.key,
        "floor": ["".join(r) for r in sc.floor],
        "objects": ["".join(r) for r in sc.objects],
        # NOT rounded: `t` is an animation phase and x/y are sub-tile
        # positions, and rounding either shifts a prop off the spot it was
        # authored on.
        "decorations": [dict(kind=d.kind, x=d.x, y=d.y, scale=d.scale,
                             seed=d.seed, t=d.t, kwargs=_enc(d.kwargs))
                        for d in sc.decorations],
        "npcs": [dict(name=n.name, sprite=n.sprite_kind, x=n.x, y=n.y,
                      movement=n.movement, solid=n.solid, voice=n.voice,
                      tag=n.tag, no_prompt=n.no_prompt, radius=n.radius,
                      speed=n.speed, hp=n.hp, max_hp=n.max_hp,
                      color=_enc(n.color), portrait=n.portrait,
                      move_timer=n.move_timer, facing=_enc(n.facing),
                      home=_enc(n.home), dialogue=_fn_name(n.dialogue_fn))
                 for n in sc.npcs],
        "hooks": {k: _fn_name(getattr(sc, k + "_fn", None))
                  for k in ("on_enter", "on_update", "on_exit", "on_interact")},
        # Everything else the builder put on the scene, whatever it was.
        "attrs": {k: _enc_refs(v, _npc_index(sc))
                  for k, v in vars(sc).items()
                  if k not in _STRUCTURAL and k not in _SCRATCH
                  and not callable(v) and _refs_ok(v, _npc_index(sc))},
        # A callable hung on the scene (a fold's charge test, a gate) is
        # behaviour, so it travels by name exactly like a hook.
        "fn_attrs": {k: _fn_name(v) for k, v in vars(sc).items()
                     if k not in _STRUCTURAL and callable(v)},
    }
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    out = path or layout_path(sc.key)
    with open(out, "w") as f:
        json.dump(lay, f, indent=1)
    return out


def build_from_layout(key, path=None):
    """Rebuild a Scene from its layout file."""
    from entities.decoration import Decoration
    from entities.npc import NPC
    from scenes.base import Scene
    with open(path or layout_path(key)) as f:
        lay = json.load(f)

    # Scene takes ROWS and derives its own size from them.
    sc = Scene(lay["key"], list(lay["floor"]), list(lay["objects"]))
    for d in lay["decorations"]:
        deco = Decoration(d["x"], d["y"], d["kind"], scale=d.get("scale", 1.0),
                          seed=d.get("seed"), **_dec(d.get("kwargs", {})))
        if "t" in d:
            deco.t = d["t"]                    # the animation phase
        sc.add_decoration(deco)
    for n in lay["npcs"]:
        npc = NPC(n["x"], n["y"], n["name"], n["sprite"],
                  voice=n.get("voice", "blip_mid"),
                  movement=n.get("movement", "idle"),
                  solid=n.get("solid", True), tag=n.get("tag"),
                  no_prompt=n.get("no_prompt", False),
                  radius=n.get("radius", 64), speed=n.get("speed", 1.0),
                  hp=n.get("hp", 30),
                  home=_dec(n["home"]) if n.get("home") else None)
        for attr in ("color", "facing"):
            if n.get(attr) is not None:
                setattr(npc, attr, _dec(n[attr]))
        npc.portrait = n.get("portrait")
        npc.max_hp = n.get("max_hp", npc.max_hp)
        if "move_timer" in n:
            npc.move_timer = n["move_timer"]   # the phase of their wander
        npc.dialogue_fn = _fn(n.get("dialogue"), n["name"])
        sc.add_npc(npc)
    # Attributes go on AFTER the pieces, so the builder's own bookkeeping wins
    # over whatever add_decoration / add_npc set up along the way.
    for k, v in (lay.get("attrs") or {}).items():
        setattr(sc, k, _dec_refs(v, sc.npcs))
    for k, name in (lay.get("fn_attrs") or {}).items():
        if name:
            setattr(sc, k, _fn(name, "%s.%s" % (key, k)))
    for k, name in (lay.get("hooks") or {}).items():
        if name:
            setattr(sc, k + "_fn", _fn(name, "%s.%s" % (key, k)))
    return sc
