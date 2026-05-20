"""Round-10 bug sweep + integration test. Standalone -- run after smoke
to confirm none of the round-10 changes introduced regressions across
guard waypoints, basement note removal, wanted poster, C_BG match,
boss kill consumption, portal accusation, haunted_house_glitch flow,
policeman sprite kind, easter_egg / barn doll placement, world_emptied
NPC vanish, badge code surfacing, and chest delivery.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems.game import Game
from constants import TILE, C_BG
from scenes.base import is_object_solid, is_floor_solid, FLOOR_DEFS
from scenes import SCENE_BUILDERS

g = Game()
g.save.load()
g.audio.music_muted = True
g._start_play()

print("=== BUG SWEEP ===")

# B1: C_BG matches @-floor color
print("B1 C_BG=", C_BG, "vs @-floor=", FLOOR_DEFS["@"]["color"])
assert C_BG == FLOOR_DEFS["@"]["color"]

# B2: guard waypoints all on walkable tiles
for scene_key in ("village", "our_house_area"):
    g.load_scene_now(scene_key, "default")
    sc = g.scene
    guards = [n for n in sc.npcs
              if n.name == "Guard" and n.movement == "patrol"]
    if not guards:
        print(f"B2 {scene_key}: no guard found (skipping)")
        continue
    g_npc = guards[0]
    bad = []
    for (wx, wy) in g_npc.waypoints:
        tx, ty = int(wx // TILE), int(wy // TILE)
        if not (0 <= tx < sc.w and 0 <= ty < sc.h):
            bad.append(("OOB", wx, wy, tx, ty))
            continue
        obj = sc.objects[ty][tx]
        flo = sc.floor[ty][tx]
        if is_object_solid(obj):
            bad.append(("solid_obj", tx, ty, obj))
        if is_floor_solid(flo):
            bad.append(("solid_floor", tx, ty, flo))
    print(f"B2 {scene_key}: {len(g_npc.waypoints)} wps, {len(bad)} bad")
    assert not bad, f"{scene_key} bad waypoints: {bad}"

# B3: basement no longer has Note NPC (only Photo). Reset
# world_emptied so the post-alien NPC purge doesn't strip the photo.
g.save.data["flags"]["world_emptied"] = False
g.load_scene_now("basement", "default")
note_npcs = [n for n in g.scene.npcs
             if getattr(n, "tag", "") == "basement_note"]
photo_npcs = [n for n in g.scene.npcs
              if getattr(n, "tag", "") == "basement_photo"]
print(f"B3 basement: notes={len(note_npcs)} photos={len(photo_npcs)}")
assert len(note_npcs) == 0
assert len(photo_npcs) == 1

# B4: wanted poster dialog
g.load_scene_now("village", "default")
flyer_x, flyer_y = 26 * TILE + 28, 12 * TILE + 16
g.player.x, g.player.y = flyer_x, flyer_y
g.save.data["flags"]["flyer_read"] = False
shown = []
g.dialog.show = lambda lines, **k: shown.append(lines)
g.scene.on_interact_fn(g)
print("B4 flyer first line:", repr(shown[0][0]))
# Round-11: poster line trimmed to "This paper is quite worn." +
# "Faintly it reads, WANTED:". The B18 test below covers the
# new wording in detail.
assert "worn" in shown[0][0] or "wanted" in shown[0][0].lower()

# B5: every spawn walkable + not on exit
errs = []
for k in SCENE_BUILDERS:
    sc = SCENE_BUILDERS[k]()
    for spawn_name, (px, py) in sc.spawns.items():
        tx, ty = int(px // TILE), int(py // TILE)
        if not (0 <= tx < sc.w and 0 <= ty < sc.h):
            errs.append((k, spawn_name, "oob", tx, ty))
            continue
        obj = sc.objects[ty][tx]
        flo = sc.floor[ty][tx]
        if is_object_solid(obj):
            errs.append((k, spawn_name, "solid_obj", obj))
        if is_floor_solid(flo):
            errs.append((k, spawn_name, "solid_floor", flo))
        if obj in sc.exits:
            errs.append((k, spawn_name, "on_exit", obj))
print(f"B5 spawn audit: {len(errs)} bad")
for e in errs:
    print("  ", e)
assert not errs

# B6: every exit resolves to a target with the named spawn
errs = []
scenes_built = {k: SCENE_BUILDERS[k]() for k in SCENE_BUILDERS}
for k, sc in scenes_built.items():
    for ech, (target, spawn_id) in sc.exits.items():
        if target not in scenes_built:
            errs.append((k, ech, "unknown_target", target))
            continue
        if spawn_id not in scenes_built[target].spawns:
            errs.append((k, ech, "missing_spawn", target, spawn_id))
print(f"B6 exit audit: {len(errs)} bad")
assert not errs

# B7: (alien boss kill test removed -- the alien is gone in
# THRESHOLD's depths arc. Polaroid now sources from the basement
# photo dialogue, not a boss kill.)

# B8: portal-accusation with diary
notices = []
g.show_notice = lambda txt, **k: notices.append(txt)
inv.add("diary_page_1", 1)
g.save.data["flags"]["symbol_portal_used"] = False
g.load_scene_now("symbol_portal_room", "from_haunted")
sym_x = 7 * TILE + 16
sym_y = 5 * TILE + 16
g.player.x, g.player.y = sym_x, sym_y
g.transition_target = None
g.state = "playing"
g.scene.update(0.016, g)
print("B8 portal+diary notices:", notices)
assert any("Your sin burns you" in n for n in notices)

# B9: haunted_house glitch transition
g.save.data["flags"]["haunted_glitch_sealed"] = False
g.save.data["flags"]["symbol_portal_used"] = False
g.load_scene_now("haunted_house", "default")
g.player.x, g.player.y = 3 * TILE + 16, 7 * TILE + 16
g.transition_target = None
g.state = "playing"
g.scene.update(0.016, g)
print("B9 haunted->glitch:", g.transition_target)
assert g.transition_target == ("haunted_house_glitch", "from_normal")

# B10: policeman kind on bandit_cave_boss boss
g.load_scene_now("bandit_cave_boss", "default")
g.save.set_arg("user_code", None)
g.scene.enemies = []
from scenes.interiors import _spawn_boss
_spawn_boss(g.scene)
print("B10 boss kind=", g.scene.enemies[0].kind)
assert g.scene.enemies[0].kind == "policeman"

# B11: barn has 3 wolves + 0 dolls
g.save.data["arg"]["wolves_killed"] = 0
g.load_scene_now("barn", "default")
wolves = [e for e in g.scene.enemies if e.kind == "wolf"]
dolls = [e for e in g.scene.enemies if e.kind == "doll"]
print(f"B11 barn wolves={len(wolves)} dolls={len(dolls)}")
assert len(wolves) == 3
assert len(dolls) == 0
key_drop = [w for w in wolves if "slobbery_key" in w.drops]
assert len(key_drop) == 1

# B12: easter_egg_room has 2 dolls
g.save.data["flags"]["first_easter_egg"] = False
g.load_scene_now("easter_egg_room", "default")
dolls = [e for e in g.scene.enemies if e.kind == "doll"]
print(f"B12 easter_egg dolls={len(dolls)}")
assert len(dolls) == 2

# B13: world_emptied wipes NPCs
g.save.set_flag("world_emptied", True)
for k in ("village", "kid_house", "old_man_house", "shop"):
    g.load_scene_now(k, "default")
    if g.scene.npcs:
        print(f"B13 FAIL {k} has npcs:", [n.name for n in g.scene.npcs])
    assert len(g.scene.npcs) == 0
g.save.data["flags"]["world_emptied"] = False
print("B13 world_emptied OK")

# B14: badge desc surfaces code
g.save.set_arg("user_code", "d-742")
from systems.items import effective_desc
print("B14 badge:", repr(effective_desc("badge", g.save)))
assert "D-742" in effective_desc("badge", g.save)

# B15: chests across all 4 sites
chest_tests = [
    ("bandit_cave",       "chest_cave_main",      "potion_clear", None),
    ("bandit_cave_west",  "chest_cave_west",      "potion_red",   None),
    ("bandit_cave_east",  "chest_cave_east_bread","bread",        None),
    ("bandit_cave_east",  "chest_cave_east_key",  "brass_key",    None),
    ("barn",              "chest_barn",           "old_doll",     "slobbery_key"),
]
for scene_key, flag, item, key in chest_tests:
    g.save.data["flags"][flag] = False
    while inv.has(item):
        inv.remove(item, 99)
    g.load_scene_now(scene_key, "default")
    if scene_key == "bandit_cave_east":
        cx, cy = g.scene._east_chest_a if flag == "chest_cave_east_bread" else g.scene._east_chest_b
    elif scene_key == "bandit_cave":
        cx, cy = g.scene._cave_chest_pos
    elif scene_key == "bandit_cave_west":
        cx, cy = g.scene._west_chest_pos
    elif scene_key == "barn":
        cx, cy = g.scene._barn_chest_pos
    g.player.x, g.player.y = cx, cy
    if key:
        while inv.has(key):
            inv.remove(key, 99)
        inv.add(key, 1)
    g.scene.on_interact_fn(g)
    print(f"B15 {scene_key}/{flag}: has({item})={inv.has(item)}")
    assert inv.has(item), f"chest {flag} failed to deliver {item}"
print("B15 all chests OK")

# B16: house decorations actually got added
for scene_key, min_decos in (("bedroom", 8), ("house", 10),
                              ("basement", 5), ("old_man_house", 5),
                              ("fisherman_cottage", 6),
                              ("kid_house", 6)):
    g.load_scene_now(scene_key, "default")
    n = len(g.scene.decorations)
    print(f"B16 {scene_key} decorations: {n} (expect >= {min_decos})")
    assert n >= min_decos, f"{scene_key} only has {n} decorations"

# B17: lore item descs
from systems.items import ITEM_DEFS
print("B17 old_doll:", repr(ITEM_DEFS["old_doll"]["desc"]))
assert ITEM_DEFS["old_doll"]["desc"] == "Chewed."
print("B17 diary:", repr(ITEM_DEFS["diary_page_1"]["desc"][:60]))
assert "Visitors came" in ITEM_DEFS["diary_page_1"]["desc"]
print("B17 broken_crutch:", repr(ITEM_DEFS["broken_crutch"]["desc"]))
assert ITEM_DEFS["broken_crutch"]["desc"] == "Bent."

# B18 (round-11): wanted poster says "WANTED:"
g.save.data["flags"]["flyer_read"] = False
g.load_scene_now("village", "default")
flyer_x, flyer_y = 26 * TILE + 28, 12 * TILE + 16
g.player.x, g.player.y = flyer_x, flyer_y
shown = []
g.dialog.show = lambda lines, **k: shown.append(lines)
g.scene.on_interact_fn(g)
print("B18 wanted poster:", shown[0])
assert any("worn" in l for l in shown[0])
assert any("WANTED:" in l for l in shown[0])

# B19: void chest delivers easter_egg + rust_key
g.save.data["flags"]["chest_void"] = False
while inv.has("easter_egg"):
    inv.remove("easter_egg", 99)
while inv.has("rust_key"):
    inv.remove("rust_key", 99)
g.load_scene_now("void", "default")
cx, cy = g.scene._void_chest_pos
g.player.x, g.player.y = cx, cy
g.scene.on_interact_fn(g)
print("B19 void chest: egg=", inv.has("easter_egg"), "key=", inv.has("rust_key"))
assert inv.has("easter_egg") and inv.has("rust_key")

# B20: basement diary chest delivers + sets diary_taken; no respawn
g.save.data["flags"]["diary_taken"] = False
while inv.has("diary_page_1"):
    inv.remove("diary_page_1", 99)
g.load_scene_now("basement", "default")
cx, cy = g.scene._basement_chest_pos
g.player.x, g.player.y = cx, cy
g.scene.on_interact_fn(g)
print("B20 basement chest: diary=", inv.has("diary_page_1"),
      "diary_taken=", g.save.flag("diary_taken"))
assert inv.has("diary_page_1") and g.save.flag("diary_taken")

# B21: 3 black_figures in basement after diary_taken
g.load_scene_now("basement", "default")
shadows = [e for e in g.scene.enemies if e.kind == "black_figure"]
print(f"B21 basement shadows after diary_taken: {len(shadows)}")
assert len(shadows) == 3

# B22: no shadows in basement before diary_taken
g.save.data["flags"]["diary_taken"] = False
g.load_scene_now("basement", "default")
shadows = [e for e in g.scene.enemies if e.kind == "black_figure"]
print(f"B22 basement shadows before diary_taken: {len(shadows)}")
assert len(shadows) == 0

# B23: police bulletin uses Missing not Deceased
g.save.set_arg("user_code", "d-742")
g.save.data["flags"]["terminal_unlocked"] = False
g.load_scene_now("old_man_house", "default")
term = next(n for n in g.scene.npcs
            if getattr(n, "tag", None) == "computer")
shown.clear()
g.dialog.show = lambda lines, **k: shown.append(lines)
class StubModal:
    def __init__(self):
        self.active = False
    def open(self, prompt="", on_submit=None, on_cancel=None):
        on_submit("d-742")
g.text_input = StubModal()
term.dialogue_fn(g, term)
print("B23 bulletin lines:")
for line in shown[0]:
    print("   ", line)
assert any("Missing:" in l for l in shown[0])
assert not any("Deceased" in l for l in shown[0])

# B24: daughter dog popup fires on first polaroid entry
g.save.data["flags"]["daughter_dog_line_seen"] = False
g.save.set_flag("polaroid_taken", True)
shown.clear()
g.dialog.show = lambda lines, **k: shown.append(lines)
g.load_scene_now("daughter_room", "default")
print("B24 daughter popup:", shown if shown else "(none)")
assert any("scared of the dogs" in l
           for lines in shown for l in lines)
# B24b: subsequent entry doesn't re-fire
shown.clear()
g.load_scene_now("daughter_room", "default")
print("B24b second entry popup:", shown if shown else "(silent)")
assert all("scared of the dogs" not in l
           for lines in shown for l in lines)

# B25: ARG and NotesUI files actually deleted
import os
HERE_T = os.path.dirname(os.path.abspath(__file__))
ROOT_T = os.path.dirname(HERE_T)
for path in ("ui/notes_ui.py", "systems/arg.py"):
    full = os.path.join(ROOT_T, path)
    print(f"B25 {path} exists?", os.path.exists(full))
    assert not os.path.exists(full)

# B26: no remaining game.arg or .drop_evidence references in source
import glob
src = []
for pattern in ("scenes/*.py", "systems/*.py", "ui/*.py", "entities/*.py"):
    src.extend(glob.glob(os.path.join(ROOT_T, pattern)))
bad = []
for f in src:
    with open(f, "r", encoding="utf-8") as h:
        text = h.read()
    if "game.arg." in text:
        bad.append((f, "game.arg."))
    if "drop_evidence" in text:
        bad.append((f, "drop_evidence"))
print(f"B26 stale refs: {bad}")
assert not bad

print("\nBUG SWEEP COMPLETE - no issues found.")
