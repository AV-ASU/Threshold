"""The Clerk's house (above the inn): spare_room (player's cot),
main floor (kitchen + living + front door), the Clerk's bedroom
(locked, holds the robe), the basement (photograph,
notebook, flashlight, bulkhead exit).

The bedroom KEY means the spare room above the inn. The house KEY
means the Clerk's downstairs. Geometries, pickups, decorations,
NPCs, and triggers are preserved.
"""
import math
import time
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene, chest_interact
from .dialogue import (clerk_dialogue, _evidence,
                       sable_on_death)


# ---- spare_room (key: 'bedroom') ----

def build_bedroom():
    """The player's spare room above the inn. THRESHOLD redesign:
    larger and more lived-in -- a wardrobe in the corner, a
    bookshelf next to the writing table, a rag rug on the floor,
    layered candles, and more wall props so the room reads as a
    place a person has been *staying*, not just sleeping. The cot
    is still the save point.

    Hide spot: into the wardrobe (real cover this time). The cot
    is the save trigger, not a hide spot; the writing desk holds
    the case notes + the PI's sidearm."""
    floor = ["=" * 16 for _ in range(12)]
    # Furniture is drawn as sized decorations (multi-tile / sub-tile)
    # with invisible solid 'X' tiles under their footprints for
    # collision: a 2x2 cot in the NW corner, a long shallow bookshelf on
    # the north wall, a writing desk, and a tall wardrobe on the west
    # wall. 'i' = window, 'D' = south door.
    objects = [
        "WWWWWWiWWWWiWWWW",   # 0  north wall, two windows
        "W.XX.......XXX.W",   # 1  cot head (2-3) + long bookshelf (11-13)
        "W.XX...........W",   # 2  cot footprint (cols 2-3, rows 1-3)
        "W.XX...........W",   # 3
        "W..............W",   # 4
        "W.........XX...W",   # 5  writing desk footprint (cols 10-11)
        "W..............W",   # 6
        "W.X............W",   # 7  wardrobe footprint (col 2, rows 7-8)
        "W.X............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWDWWWWWWWW",   # 11 south wall, door D at col 7
    ]
    sc = Scene("bedroom", floor, objects, music="home")
    sc.add_exit("D", "lodge", "from_bedroom")
    sc.set_spawn("default", 7, 6)
    sc.set_spawn("from_lodge", 7, 10)
    # The cot fills the NW corner (cols 2-3, rows 2-3). The player
    # stands one tile east at col 4 row 3 to sleep/save (the game's one
    # save point; bedroom_interact -> Game._sleep_at_cot).
    sc._cot_pos = (4 * TILE + 16, 3 * TILE + 16)
    sc.add_interactable(sc._cot_pos[0], sc._cot_pos[1], 44)
    # Hide spot: INTO the wardrobe (col 3 row 8). It used to be UNDER the
    # writing desk, but that 36px hide radius sat right on the desk's
    # notes-reading spot and stole the [E] press (you hid instead of
    # reading), so the hide moved to the wardrobe the docstring always
    # promised, leaving the desk's [E] free for the case notes.
    sc.hide_spots = [
        (3 * TILE + 16, 8 * TILE + 16, "in"),        # step into the wardrobe
    ]

    # Worn rug over the open centre -- a multi-tile covering, set
    # off-grid so it breaks the plank tiling. Added first so the props
    # below draw on top of it.
    sc.add_decoration(Decoration(7 * TILE + 24, 7 * TILE + 8, "rug",
                                 w=120, h=76, color=(86, 42, 46), seed=17))
    # Sized darkwood furniture (decorations over the 'X' collision
    # footprints in the object map). A 2x2 cot in the corner, a long
    # shallow bookshelf on the north wall, a writing desk + chair, a
    # tall wardrobe on the west wall.
    sc.add_decoration(Decoration(3 * TILE, 2 * TILE + 16, "bed", w=60, h=92))
    # Bookshelf shoved up against the north wall so it covers the lower
    # part of the east window -- a tall room, a long low case crowding
    # the glass.
    sc.add_decoration(Decoration(12 * TILE + 16, 1 * TILE - 6, "bookshelf",
                                 w=86, h=22, seed=5))
    # The writing desk: a real furniture box (cols 10-11, row 5). The open
    # case FILE and the PI's REVOLVER are drawn FLAT on its top face by the
    # furniture itself (_d_desk_top), so they foreshorten with the tilt and
    # read as lying ON the desk. `gun_present` toggles the revolver off once
    # it is taken (bedroom_interact / bedroom_on_enter).
    desk = sc.add_furniture("writing_desk", [(10, 5), (11, 5)], w=58, h=42)
    desk.tag = "writing_desk"
    desk.gun_present = True
    sc.add_decoration(Decoration(12 * TILE + 18, 6 * TILE + 4, "chair",
                                 w=22, h=28))
    sc.add_decoration(Decoration(2 * TILE + 16, 8 * TILE, "wardrobe",
                                 w=26, h=54))
    # Duffel bag beside the cot.
    sc.add_decoration(Decoration(2 * TILE + 28, 5 * TILE + 16, "bowl",
                                 filled=True))
    # Two candles on the bedside (north wall edge) and one on the
    # writing table.
    sc.add_decoration(Decoration(2 * TILE + 8,  0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(13 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16, 5 * TILE + 4, "candle"))
    # Northern-MN lodge dressing on the north wall: a mounted buck
    # (replaces the old generic photo) between the windows, a trophy
    # walleye to the west, and cobwebs fanning from the high corners.
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 24, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # A phantom_mark scratched into the wood near the door -- subtle,
    # easy to miss the first session.
    sc.add_decoration(Decoration(4 * TILE + 12, 9 * TILE + 16,
                                 "phantom_mark"))
    # Guest-room toilette: a washstand against the west wall (the basin
    # water a shade too dark), and somebody's old framed needlework on
    # the north wall, its bottom rows come undone. (North wall, not east:
    # E/W wall faces are edge-on to the tilt camera at rest, so a picture
    # there only shows during a head-turn.)
    sc.add_decoration(Decoration(1 * TILE + 18, 6 * TILE + 8, "washstand"))
    sc.add_decoration(Decoration(14 * TILE + 10, 0 * TILE + 22, "sampler",
                                 seed=9))
    # Drifting motes through the room -- dust in old light.
    for i in range(7):
        sc.add_decoration(Decoration(3 * TILE + i * 64,
                                     3 * TILE + (i % 3) * 40, "mote"))
    # A small bloodstain near the south door -- subtle, the kind
    # of thing you don't notice on day one.
    sc.add_decoration(Decoration(8 * TILE + 8, 10 * TILE + 16,
                                 "bloodstain"))

    # The case notebook is read at the writing desk -- flag it for the
    # [E] prompt so the player knows the desk is interactable.
    sc.add_interactable(11 * TILE, 5 * TILE + 16, 44)

    sc.on_enter_fn = bedroom_on_enter
    sc.on_interact_fn = bedroom_interact
    sc.on_update_fn = bedroom_on_update
    return sc


def bedroom_on_enter(game, scene):
    """Opening sequence + idempotent. The first session in this
    scene is the game's first minute: the wake notice, the
    candle-dip + creak when the doorway watcher manifests, and the
    suppressed sprint. (The arrival drive -- the car into Brimley,
    the dying engine -- plays before this, in the Game's "opening"
    state.) These pieces fire from `bedroom_on_update` so they can
    be paced over real seconds rather than crammed into entry. We
    seed them here.

    Subsequent visits (after sleeping in the cot, or returning
    later in the run) skip the opening entirely -- only the
    cot-as-save-point remains."""
    # Once the sidearm has been taken off the desk, clear it from the desk's
    # top on every load (the scene rebuilds each time, so it would otherwise
    # reappear).
    if game.save.flag("desk_pistol_taken"):
        for d in scene.decorations:
            if getattr(d, "tag", None) == "writing_desk":
                d.gun_present = False
    if game.save.flag("wake_up"):
        return
    game.save.set_flag("wake_up", True)
    # Wake-state audio: muffled music + slow heartbeat. The
    # Game side reads `_wake_muffle_t` to drive these so audio
    # cleanup happens in one place.
    game._wake_muffle_t = 8.0
    game._wake_heartbeat_t = 0.6
    # Pacing slots tracked on the scene itself so each event
    # fires once per session. `_opening_t` ticks up in
    # bedroom_on_update; the slots check thresholds.
    scene._opening_t = 0.0
    scene._opening_slots = {
        "wake_notice_armed":   True,    # fires on first step
    }
    scene._spawn_pos = scene.spawns.get("default", (0, 0))
    # First-session onboarding: the only place the game teaches its
    # controls. A gentle one-liner shown before the player moves; the
    # wake notice replaces it the moment they do. The full reference is
    # one Esc away (pause -> Controls).
    game.show_notice(
        "Move: WASD / arrows    Interact: E    Esc: controls & options",
        duration=7.0,
    )


def bedroom_on_update(game, scene, dt):
    """First-minute pacing for the spare room. Counts elapsed
    seconds since the player woke and fires the opening beats
    on real time rather than entry. All slots are guarded so
    nothing fires twice."""
    slots = getattr(scene, "_opening_slots", None)
    if slots is None:
        return
    scene._opening_t = getattr(scene, "_opening_t", 0.0) + dt
    p = game.player
    if p is None:
        return
    # First-movement gate. The wake notice + the watcher manifest
    # only after the player has actually input movement, so the
    # opening line lands as the character noticing what the
    # player just noticed (not a frame-one overlay).
    sx, sy = scene._spawn_pos
    moved = (abs(p.x - sx) + abs(p.y - sy)) > 6
    if slots["wake_notice_armed"] and moved:
        slots["wake_notice_armed"] = False
        game.show_notice(
            "You wake up.",
            duration=5.0,
        )
    # Door-stuck recoil: when begin_transition rejects the first
    # attempt to leave, it sets `_door_stuck_recoil` on the
    # scene. We dip the candle once in response so the player
    # has something subliminal to mark the moment, then clear
    # the flag.
    if getattr(scene, "_door_stuck_recoil", False):
        scene._door_stuck_recoil = False
        for d in scene.decorations:
            if d.kind == "candle":
                d.kwargs["dip_t0"] = time.time()


def bedroom_interact(game):
    """E near the cot: SLEEP, the game's one save point (the typewriter
    rule; Game._sleep_at_cot snapshots the run and writes the disk slot
    Continue reads).
    E near the writing table: read the PI's own case notebook -- the
    persistent, re-readable statement of the premise (who hired you, who
    you're after, the job), complementing the skippable opening drive.
    Diegetic (no inventory pickup); re-reading is allowed. First read sets
    `read_journal` so other systems can react."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    # Writing desk -- the sized "table" decoration over the cols 10-11,
    # row 5 footprint (see build_bedroom). Anchor on the desk itself so
    # the case-notebook prompt sits ON the table, not out on the open rug.
    # Range 44 lets the player read it from the south/sides.
    tx = 11 * TILE
    ty = 5 * TILE + 16
    if abs(px - tx) <= 44 and abs(py - ty) <= 44:
        # Take the sidearm off the desk first, if it is still lying there:
        # remove its sprite, put the pistol in the inventory (equipped), and
        # flag it so it can't be re-grabbed. The notes read on the next press.
        if not game.save.flag("desk_pistol_taken"):
            game.save.set_flag("desk_pistol_taken", True)
            for d in sc.decorations:
                if getattr(d, "tag", None) == "writing_desk":
                    d.gun_present = False
                    game._invalidate_prop_card(d)   # rebuild without the gun
            game.player.inventory.add("pistol", 1)
            game.player.inventory.equipped["weapon"] = "pistol"
            game.audio.play("pickup", 0.7)
            game.show_notice("You take your pistol off the desk.")
            return
        # After the Dark, the case has rewritten itself. The notebook
        # the player opens the game on is the same one that closes it.
        # First read is the gut-punch; subsequent reads collapse so
        # repetition doesn't dilute it.
        if game.save.flag("hive_seen"):
            if game.save.flag("case_closed_read"):
                return
            game.save.set_flag("case_closed_read", True)
            game.dialog.show([
                "[c=dim]Subject: located. Recovery: declined.[/c]",
                "[c=dim]The handwriting is yours. You don't remember "
                "writing it.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        game.dialog.show([
            "[c=dim](Your case notebook, open on the table where you left "
            "it.)[/c]",
            "CLIENT: Walter Blaine. Wants his daughter found and brought "
            "home.",
            "MARA BLAINE, 26. Cut ties, drove north, quit calling home. "
            "The trail runs cold at Brimley.",
            "The job: ask my questions, find the girl, drive home by "
            "morning.",
            "[c=dim]The drive in was easy. Then the engine died at the lodge "
            "steps and wouldn't catch again. First wrong note.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if not game.save.flag("read_journal"):
            game.save.set_flag("read_journal", True)
        return
    # The cot (stand beside it, sc._cot_pos): sleep and save.
    cx_, cy_ = getattr(sc, "_cot_pos", (4 * TILE + 16, 3 * TILE + 16))
    if abs(px - cx_) <= 44 and abs(py - cy_) <= 52:
        game._sleep_at_cot()
        return


# ---- innkeeper_house (key: 'lodge') ----

def build_lodge():
    """The Clerk's downstairs: kitchen on the left half, living
    room on the right half. Wall divider with a door between them.
    Front door on the south wall (B exit -- the player may be
    blocked here by the Clerk). Cellar hatch in the kitchen,
    PADLOCKED until the cellar key (behind the house) is carried.
    Door to spare_room hallway on the north (col 13). Door
    to the Clerk's bedroom on the north (col 4)."""
    floor = [
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
    ]
    # Kitchen (left of the col-7 counter bar): a dining table + chairs,
    # the stove, and a run of base cabinets ('5' = counter). The bar
    # ('5' down col 7) reads as a kitchen peninsula dividing the kitchen
    # from the living room, replacing the old blank wall divider.
    objects = [
        "WWWW1WWWWWWWWBWWWW",
        "W................W",
        "W................W",
        "W.tt...5.........W",
        "W.cc...5....f....W",
        "W.k....5.........W",
        "W.55...5.........W",
        "W................W",
        "W................W",
        "W..L.............W",
        "W................W",
        "WWWWWWWDWWWWWWWWWW",
    ]
    sc = Scene("lodge", floor, objects, music="home")
    # B = front door (south wall, col 13). The Clerk blocks this.
    sc.add_exit("B", "bedroom", "from_lodge")
    # 1 = Clerk's bedroom door (col 4). Not gated (TODO C6: intended locked?).
    sc.add_exit("1", "clerk_room", "from_lodge")
    # D = back door, leads to the gravel yard.
    sc.add_exit("D", "lodge_yard", "from_lodge")
    # L = cellar hatch in the kitchen.
    sc.add_exit("L", "lodge_cellar", "from_lodge")
    # SEE-THROUGH DOORS: the two interior room doors show the actual room
    # beyond through the tilt camera instead of a flat dark recess
    # (rendering.portal.draw_through_aperture, wired via Game._build_door_views).
    sc.seethrough_doors = {"B", "1"}
    sc.set_spawn("default", 9, 9)
    # The B door (spare-room) is at col 13 of the north wall.
    # The 1 door (Clerk's bedroom) is at col 4. They were both
    # set to (4, 1) which trapped the spare-room arrival south of
    # the kitchen table at (4, 3). Each spawn is now under its own
    # door.
    sc.set_spawn("from_bedroom", 13, 1)        # south of B (spare-room)
    sc.set_spawn("from_clerk_room", 4, 1)        # south of 1 (Clerk's bedroom)
    sc.set_spawn("from_lodge_yard", 7, 10)
    # The L cellar hatch is at (3, 9). Spawning even one tile north
    # of it (3, 8) shares the same column -- a south key press would
    # walk the player straight back onto L and re-enter the basement.
    # Offset the spawn one column east so the player has to actively
    # navigate back to the hatch to descend again.
    sc.set_spawn("from_lodge_cellar", 4, 8)
    # The hatch is PADLOCKED (2026-07: the Ledger moved down there;
    # the cellar key hangs on a nail behind the house). A gated-shut
    # exit reads as floor, so house_interact carries the locked
    # feedback at the hatch; the gate itself turns the key on the
    # first crossing.
    sc._hatch_pos = (3 * TILE + 16, 9 * TILE + 16)
    sc.add_interactable(sc._hatch_pos[0], sc._hatch_pos[1], 40)

    def _house_gate(game, ch):
        if ch != "L":
            return True
        if game.save.flag("cellar_unlocked"):
            return True
        if game.player.inventory.has("cellar_key"):
            game.save.set_flag("cellar_unlocked", True)
            game.audio.play("door_open", 0.55)
            game.show_notice("The iron key turns. The hatch swings up.",
                             duration=2.4)
            return True
        return False
    sc.exit_gate_fn = _house_gate

    # A large worn rug before the hearth in the living room -- off-grid
    # and multi-tile so it breaks the plank tiling. Added first so the
    # props below sit on top of it.
    sc.add_decoration(Decoration(11 * TILE + 24, 7 * TILE + 12, "rug",
                                 w=140, h=92, color=(70, 58, 40), seed=23))
    # Sized darkwood kitchen furniture (decorations over invisible
    # collision tiles): a 2-tile dining table + two chairs, the range.
    # The counter bar/cabinets stay as object tiles.
    sc.add_furniture("table", [(2, 3), (3, 3)], w=58, h=40)
    sc.add_furniture("chair", [(2, 4)], w=22, h=28)
    sc.add_furniture("chair", [(3, 4)], w=22, h=28)
    # Against the west wall -- the oven door faces east, into the kitchen.
    sc.add_furniture("stove", [(2, 5)], w=30, h=40, wall="W")
    # Decorations: kitchen clutter on the left, fireplace on the
    # right, wall items on the NORTH wall (row 0).
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 18, "clock"))
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 22, "meat"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 14, "candle"))  # on table
    sc.add_decoration(Decoration(0 * TILE + 24, 5 * TILE + 16, "banner",
                                 color=(140, 60, 70)))
    sc.add_decoration(Decoration(12 * TILE + 16, 4 * TILE + 14, "candle"))  # on fireplace
    for i in range(6):
        sc.add_decoration(Decoration(40 + i * 90,
                                     80 + (i % 3) * 60, "mote"))
    # THRESHOLD liminal dressing: the lodge common room reads
    # wrong-empty. A wall of the vanished by the north wall of the
    # living room (the same guests the cellar Ledger records), a meal
    # abandoned mid-setting on the kitchen table, and a single chair
    # knocked over in all that empty floor -- the one wrong detail in
    # the void.
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "missing_flyer"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 24, "polaroid_wall"))
    sc.add_decoration(Decoration(14 * TILE + 16, 0 * TILE + 22, "missing_flyer"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 8, "place_setting"))
    sc.add_decoration(Decoration(13 * TILE + 16, 6 * TILE + 16, "overturned_chair"))
    sc.add_decoration(Decoration(10 * TILE + 16, 8 * TILE + 16, "small_chair"))
    sc.add_decoration(Decoration(15 * TILE + 16, 7 * TILE + 16, "small_chair"))
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 16, "phantom_mark"))

    # The Lodge front desk -- the reception counter where Sable has every
    # guest sign in. The guest register (the Ledger, a case note) sits open
    # on it; you sign on arrival, and re-reading it later is the evidence
    # (house_interact). A reception nook below the wall of the vanished, so
    # the names you sign under are the names that never checked out.
    sc._frontdesk_pos = (8 * TILE + 16, 2 * TILE + 16)
    # The desk is a real low COUNTER volume (two abutting boxes, ~2 tiles
    # wide) so under the tilt it stands as a 3D reception desk the player
    # sees OVER -- Sable, behind it, shows head + torso above the top.
    sc.add_furniture("counter", [(8, 2)], see_over=True)
    sc.add_furniture("counter", [(9, 2)], see_over=True)
    sc.add_decoration(Decoration(9 * TILE, 2 * TILE + 4, "candle"))  # on the desktop
    # The open guest register itself, lying flat ON the desktop (z = counter
    # height) at the interact anchor, so the [E] prompt lands on the visible
    # book and it reads as resting on the desk, not floating or facing you.
    sc.add_decoration(Decoration(sc._frontdesk_pos[0], sc._frontdesk_pos[1],
                                 "ledger", z=14))
    sc.add_interactable(sc._frontdesk_pos[0], sc._frontdesk_pos[1], 44)

    # Northern-MN lodge decor. Wall mounts (no collision) along the
    # east + west walls; an oil lamp on the kitchen counter; cobwebs in
    # the high corners; firewood and an antler coat-rack on the floor
    # (collision, tucked against walls so they never block a path).
    # Trophy mounts flush on the NORTH wall (row 0), facing down into the
    # room -- the buck replaces the old generic photo; a walleye on the
    # kitchen-side wall. (The "wrong" taxidermy lives underground now.)
    sc.add_decoration(Decoration(15 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 24, "mounted_fish"))
    sc.add_decoration(Decoration(2 * TILE + 14, 6 * TILE + 2, "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb", ang=0.0))
    sc.add_decoration(Decoration(16 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("firewood", [(15, 8), (16, 8)], w=58, h=24)
    sc.add_furniture("antler_rack", [(16, 2)], w=22, h=46)
    # A varnish-dark oil portrait hung among the missing flyers -- some
    # founding Arcadia proprietor whose face has sunk into the murk.
    # Nobody can say who it is anymore.
    sc.add_decoration(Decoration(12 * TILE + 24, 0 * TILE + 22,
                                 "oil_portrait", seed=2))
    # An empty birdcage by the east wall, door hanging open. The lodge
    # used to keep a canary for the guests.
    sc.add_decoration(Decoration(15 * TILE + 10, 4 * TILE + 16,
                                 "birdcage"))

    # Hide spots: under the kitchen table. The spot sits on the table's
    # walkable NORTH lip -- the old coords were inside the solid
    # footprint, which roots the player in the furniture (flow §25 now
    # guards every scene's spots against this).
    sc.hide_spots = [
        (3 * TILE + 16, 2 * TILE + 24, "under"),    # under the kitchen table
    ]

    sc.on_enter_fn = house_on_enter
    sc.on_interact_fn = house_interact
    return sc


def house_on_enter(game, scene):
    """Place the Clerk NPC himself (visible going about his business
    until the confrontation fires), and the blocking variant after
    confrontation. Two states for the Clerk:

      pre-confrontation:  the deskman at his post -- stationed behind the
                          front-desk register, watching whoever comes down,
                          talkable (uses clerk_dialogue). `watch` movement,
                          so he turns to face the player. Solid.
      post-confrontation: planted in the front doorway, no_prompt
                          (no dialogue offered), solid. The 'sit
                          back down' line is one-shot from the
                          confrontation handler."""
    # Strip any stale host instance so re-entries don't stack.
    scene.npcs = [n for n in scene.npcs
                  if getattr(n, "tag", None) not in
                  ("host_innkeeper",)]
    scene._key_hook_pos = None
    # The trap-keeper at his post: standing BEHIND the front-desk
    # register (north of it, against the wall), facing south into the
    # room. The desk volume sits between him and the player, so he reads
    # head-and-torso over the counter. `watch` turns him to follow the
    # player -- the smiling man whose eyes never quite leave you -- so
    # the arrival reads as a man who was waiting for you to come down.
    nx = 9 * TILE              # centred behind the 2-tile desk (cols 8-9)
    ny = 1 * TILE + 16         # row 1, between the desk (row 2) and wall
    host = NPC(nx, ny, "Clerk", "clerk",
               solid=True, no_prompt=False,
               voice="blip_low", portrait="clerk",
               dialogue_fn=clerk_dialogue,
               movement="watch", speed=0.6, radius=320)
    host.facing = (0, 1)
    host.tag = "host_innkeeper"
    # He carries the way down. Kill him before he hands over the
    # Invitation and it drops with the body (dialogue.sable_on_death);
    # if he already gave it, there is nothing to loot.
    host.on_kill = lambda game, _n=host: sable_on_death(game, _n)
    scene.add_npc(host)


def house_interact(game):
    """Living-room interact handler. The Lodge FRONT DESK (E): the
    sign-in register. First press SIGNS it (the light arrival beat);
    re-reading it is a LEAD now, not the evidence -- the book is nearly
    new, and the full ones went somewhere when they filled. The Ledger
    itself (the Ledger, a case note) is the boxed old registers in the PADLOCKED
    cellar (2026-07 rework; the key hangs behind the house).

    The cellar hatch (E, kitchen): the locked feedback + the soft
    pointer toward the key. The gate itself lives on the scene
    (exit_gate_fn in build_lodge)."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    hx, hy = getattr(sc, "_hatch_pos", (None, None))
    if hx is not None and abs(px - hx) <= 40 and abs(py - hy) <= 40:
        if game.save.flag("cellar_unlocked"):
            return                    # the open hatch is the exit now
        game.audio.play("door_locked", 0.5)
        game.dialog.show([
            "[c=dim](A padlock through the cellar hatch, older than the "
            "hinges and freshly oiled. Locked.)[/c]",
            "[c=dim]A lodge this size keeps a spare key close. Out of "
            "the rain, near a door. I'd start behind the house.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        return
    dx, dy = getattr(sc, "_frontdesk_pos", (None, None))
    if dx is None or abs(px - dx) > 48 or abs(py - dy) > 48:
        return
    if not game.save.flag("register_signed"):
        game.save.set_flag("register_signed", True)
        game.dialog.show([
            "[c=dim](The guest register, open on the front desk. Sable lays "
            "a pen across the page without being asked.)[/c]",
            "You sign your name under tonight's date. He turns the book back "
            "and never reads it.",
            "[c=dim]\"There. Now you're on the books.\"[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        return
    if game.save.flag("evidence_the_ledger"):
        return
    game.dialog.show([
        "You flip back through the register out of habit. A clean book, "
        "barely started. The earliest name on the page is only weeks old.",
        "[c=dim]A lodge this old has years of these. They go somewhere "
        "when they fill. Down, if this place is like every hotel I've "
        "worked. And the kitchen hatch wears a padlock.[/c]",
    ], speaker="", voice="blip_soft", portrait="narrator")


# ---- the Clerk's Room (key: 'clerk_room') ----
# The Lodge Clerk's private room, off the main floor. No evidence lives
# here -- Mara's room (robe + letter, #1) and the journal (#2) moved to the
# Sorting-Hall cell and the barn, and the testimony leaves to the Scriptorium
# (scenes/well.py, scenes/interiors.py). The one tell is a pressed cult
# robe in his closet: the smiling trap-keeper is one of them.

def build_clerk_room():
    """The Lodge Clerk's private room. A bed, a closet (his pressed cult
    robe -- the tell that he's complicit), a bare dresser, a window."""
    floor = ["=" * 14 for _ in range(10)]
    # A main room plus a partitioned CLOSET alcove (cols 9-12) reached
    # through an interior doorway. The Clerk's pressed cult robe hangs in
    # that alcove -- the dividing wall makes it an indoor blind spot, so the
    # tell that the smiling man is one of them isn't visible from the room
    # until the player steps into the closet and looks.
    objects = [
        "WWWiWWWWWWWWWW",   # 0  north wall, window col 3
        "W.......W....W",   # 1  the room (cols 1-7) | closet alcove (cols 9-12)
        "W.......W....W",   # 2
        "W............W",   # 3  doorway gap in the partition (col 8)
        "W.......W....W",   # 4
        "WWWWWWWWW....W",   # 5  closet sealed off below
        "W............W",   # 6
        "W............W",   # 7
        "W............W",   # 8
        "WWW1WWWWWWWWWW",   # 9  south wall, door 1 at col 3
    ]
    sc = Scene("clerk_room", floor, objects, music="home")
    sc.add_exit("1", "lodge", "from_clerk_room")
    # Door is at (3, 9); spawn at (4, 8) is open floor and one tile
    # off-axis so the player doesn't auto-retrigger.
    sc.set_spawn("default", 8, 7)
    sc.set_spawn("from_lodge", 4, 8)

    # The dresser (table sprite) is bare. Out in the main room,
    # off the door column so a solid prop never traps the player inside.
    sc._dresser_pos = (5 * TILE + 16, 7 * TILE + 16)
    # The closet (wardrobe sprite) holds the Clerk's pressed cult robe -- a
    # flavor clue (he's complicit), not counted evidence. In the blind alcove.
    sc._closet_pos = (10 * TILE + 16, 2 * TILE + 16)
    # Hide spot under the bed. The wardrobe is NOT a hide spot: it's the
    # Clerk's-robe tell (clerk_room_interact), and a hide here took E
    # priority and made the only "the Clerk is one of them" clue
    # unreachable. (clerk_room is a SAFE scene -- the hide was cosmetic.)
    sc.hide_spots = [
        (1 * TILE + 24, 6 * TILE + 24, "under"),   # the bed's walkable lip
    ]
    # [E] cue for the robe closet (the tell). The dresser is bare and has
    # no handler in clerk_room_interact, so it gets no [E] prompt (C14a).
    sc.add_interactable(sc._closet_pos[0], sc._closet_pos[1], 40)

    # Sized darkwood furniture: a 2x2 bed, a tall closet (the Clerk's robe
    # -> _closet_pos), a low dresser (bare -> _dresser_pos).
    sc.add_furniture("bed", [(2, 6), (3, 6), (2, 7), (3, 7)], w=56, h=56)
    sc.add_furniture("wardrobe", [(10, 2), (10, 3)], w=26, h=54)
    sc.add_furniture("table", [(5, 7), (6, 7)], w=54, h=32)

    # Wall items mounted on the NORTH wall (row 0). Lodge dressing: a
    # mounted buck (replaces the old generic photo) and a trophy
    # walleye flank the window; a cobweb hangs in the closet corner and a
    # kerosene lamp burns on the dresser.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish", flip=True))
    sc.add_decoration(Decoration(12 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(6 * TILE + 16, 7 * TILE + 2,
                                 "kerosene_lamp"))
    # The Clerk's washstand against the west wall -- he keeps himself
    # presentable for the desk.
    sc.add_decoration(Decoration(1 * TILE + 18, 2 * TILE + 16, "washstand"))
    for i in range(4):
        sc.add_decoration(Decoration(40 + i * 60,
                                     200 + (i % 2) * 40, "mote"))

    sc.on_interact_fn = clerk_room_interact
    return sc


def clerk_room_interact(game):
    """The Clerk's room. CLOSET (E): the cult robe -- the PI reads it as
    membership; the truth (NARRATIVE §4, the lucky host) is that it came
    with the Invitation, the congregation's offer to bring him below, and
    he never once put it on. The never-worn detail is the quiet fact a
    player can re-read later. A one-shot flavor clue, NOT counted evidence
    ('clerk_robe' is not in CANONICAL_EVIDENCE, so it narrates but never
    moves the King-gate)."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    cx, cy = sc._closet_pos
    if abs(px - cx) <= 40 and abs(py - cy) <= 40:
        _evidence(game, "clerk_robe",
                  "A cult robe hangs in the Clerk's closet, pressed and "
                  "folded. By the creases it has never once been worn.")
        return


# ---- innkeeper_basement (key: 'basement') ----

def build_lodge_cellar():
    """The Arcadia Lodge's cellar -- the Clerk's domain, behind the
    PADLOCKED kitchen hatch (the cellar key hangs behind the house).
    Stone walls, packed dirt floor, a single hanging bulb. The
    workbench chest holds the woodshed key; the boxed OLD
    REGISTERS on the east crates are the Ledger, a case note (2026-07:
    moved back down here from the front desk, behind the lock); and the
    guttering candles pay off the cult-devotion beat once you've seen
    the dark below.

    Single entry/exit via the kitchen cellar hatch. A previous build
    had a south-wall bulkhead leading to the back yard; removed
    because it created the impression of a duplicate basement door
    on the same building footprint. The cellar is now strictly a
    one-way-down room with the ladder back as the only return."""
    floor = ["x" * 14 for _ in range(12)]
    objects_l = []
    for y in range(12):
        if y == 0 or y == 11:
            objects_l.append(list("#" * 14))
        else:
            row = ["#"] + ["."] * 12 + ["#"]
            objects_l.append(row)
    # L-shaped cellar: the SE corner is solid stone (the dig was never
    # squared off), so the room bends instead of reading as a plain box.
    for yy in range(7, 11):
        for xx in range(9, 13):
            objects_l[yy][xx] = "#"
    objects_l[1][10] = "U"          # ladder up to the kitchen
    objects = ["".join(r) for r in objects_l]
    sc = Scene("lodge_cellar", floor, objects, music="basement")
    sc.add_exit("U", "lodge", "from_lodge_cellar")
    sc.set_spawn("default", 9, 1)
    sc.set_spawn("from_lodge", 9, 1)

    # (The framed staff photograph is CUT, 2026-07: an unaged Clerk across
    # "decades" was a second impossible thing -- NARRATIVE §2 keeps the
    # impossible count at one, and Sable is a mortal local.)

    # Workbench in the SW corner (holds the woodshed key). The chest gets
    # its own chest prompt via basement_interact.
    sc._workbench_pos = (2 * TILE + 16, 7 * TILE + 16)
    sc._chest_pos = (sc._workbench_pos[0], sc._workbench_pos[1] - 8)
    # No hide spots: the firewood stacks are solid cover the player breaks
    # line of sight behind; the workbench chest stays its own E-interaction.
    sc.hide_spots = []
    sc.add_decoration(Decoration(sc._chest_pos[0], sc._chest_pos[1],
                                 "chest", open=False))

    # A second split-wood stack by the south wall -- cover, and what the
    # second hide spot crouches behind (replacing the bloodstain it used
    # to sit on; you can't hide inside a bloodstain).
    sc.add_decoration(Decoration(5 * TILE + 16, 8 * TILE + 6, "firewood",
                                 w=44, h=24))
    sc.add_decoration(Decoration(5 * TILE + 20, 6 * TILE + 20,
                                 "bloodstain", scale=3.2))
    sc.add_decoration(Decoration(1 * TILE + 24, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(10 * TILE + 8, 4 * TILE + 16, "candle"))
    # A "wrong" mount on the cellar wall -- too many eyes in the dark.
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 20,
                                 "wrong_taxidermy", wall="N", seed=11))
    # One claw gouge etched into the cellar wall.
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 8, "claw_marks",
                                 scale=2.2))
    # Cellar grime + a split-wood stack against the SE wall. Cobwebs
    # fan from the high corners; the firewood is collision furniture
    # tucked clear of the workbench and ladder paths.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("firewood", [(3, 10), (4, 10)], w=58, h=24)
    # Crates of stored goods filling out the cellar's east end. The top
    # of the west crate carries the Lodge's boxed OLD REGISTERS -- the
    # Ledger, a case note (read via basement_interact).
    sc.add_furniture("crate", [(10, 4)])
    sc.add_furniture("crate", [(11, 4)])
    sc.add_furniture("barrel", [(11, 2)])
    sc._ledger_pos = (10 * TILE + 16, 4 * TILE + 16)
    sc.add_decoration(Decoration(10 * TILE + 16, 4 * TILE + 4, "ledger",
                                 z=14))
    sc.add_interactable(sc._ledger_pos[0], sc._ledger_pos[1], 44)
    # Larder shelves of preserves on the north wall. The contents have
    # all gone the same murky shade, and one jar holds something the
    # light doesn't explain. A butter churn stands dry by the firewood.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=13))
    sc.add_decoration(Decoration(8 * TILE + 24, 0 * TILE + 22,
                                 "preserve_shelf", seed=29))
    sc.add_decoration(Decoration(1 * TILE + 18, 10 * TILE + 4,
                                 "butter_churn"))
    for mx, my in [(2, 5), (6, 6), (4, 3), (8, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))

    sc.on_enter_fn = basement_on_enter
    sc.on_interact_fn = basement_interact
    return sc


def basement_on_enter(game, scene):
    """Drop the woodshed key on the workbench (idempotent via save flag).
    (The Ledger, a case note, is the boxed old registers on the east
    crates -- basement_interact reads it; the padlocked hatch upstairs
    is the gate.)"""
    game._provoke_cult(0.10)
    # The woodshed key lives in the workbench chest -- taken by opening it
    # (E) in basement_interact, not auto-grabbed off the floor. Sync the
    # chest's open/closed visual to whether it's been emptied.
    for deco in scene.decorations:
        if deco.kind == "chest":
            deco.kwargs["open"] = game.save.flag("woodshed_key_taken")
    # A few cartridges stashed in the cellar (one-time, flag-gated).
    from .base import drop_ammo_cache
    drop_ammo_cache(game, scene, 6, 3, 4, "ammo_cellar")
    # Lodge-candle callback: once the player has seen the Cistern at the
    # Works (the dig that broke into the river), the candles in the Lodge
    # mean something they didn't before -- the Lodge has been part of the
    # cult's devotion the whole time. One-shot, fires the next descent to
    # the cellar after the Cistern beat (non-canonical evidence -- doesn't
    # move the King-gate, and the claiming cult renders no bodies at all).
    if (game.save.flag("evidence_works_cistern_seen")
            and not game.save.flag("evidence_lodge_candle_callback")):
        _evidence(game, "lodge_candle_callback", [
            "[c=dim]The same guttering candles as the dark below, kept "
            "burning up here too.[/c]",
        ])


def basement_interact(game):
    """E at the old registers (east crates): the Ledger, a case note.
    E at the workbench chest: the woodshed key (gate to the axe in the
    shed)."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    lx, ly = getattr(sc, "_ledger_pos", (None, None))
    if lx is not None and abs(px - lx) <= 44 and abs(py - ly) <= 44:
        if game.save.flag("evidence_the_ledger"):
            game.dialog.show([
                "[c=dim]A year of names that never signed out. You've "
                "read enough of them.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        game.audio.play("pickup_rare", 0.7)
        game.audio.play("low_pulse", 0.45)
        # Real, and wrong, but not Mara -- she was never at the lodge -- so
        # it files as a town NOTE, never case-evidence (NARRATIVE §6,
        # DESIGN.md §9). note=True keeps it in the notebook off the gate.
        _evidence(game, "the_ledger", [
            "Boxes of the Lodge's old registers, years deep, carried down "
            "here as each book filled. You lift the top one out and start "
            "back through it.",
            "Names signed in, in the Clerk's hand, and a date beside each "
            "one where they settled up and left. Then those dates just... "
            "stop. The last anyone signed out was a year back. Every name "
            "since signs in and never out.",
            "[c=dim]Probably nothing. A clerk who got lazy, dropped the "
            "habit. ...Still. A year of guests, and the clean book "
            "upstairs starts right where these leave off. I'll keep it "
            "in mind.[/c]",
        ], note=True)
        return
    # The workbench chest -- holds the woodshed key (gate to the axe
    # in the shed). chest_interact does its own range check and flips the
    # chest's open visual; the `woodshed_key_taken` flag keeps it emptied
    # across re-entries.
    cx, cy = sc._chest_pos
    chest_interact(game, sc, cx, cy, "woodshed_key_taken", ["woodshed_key"])
