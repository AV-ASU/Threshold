"""outside_innkeeper_house (key: 'our_house_area') -- the gravel
yard behind the Clerk's house. The WOODSHED sits in the SW (the axe,
rope and flashlight; a locked facade door 'l' -> the `woodshed`
interior, key-gated by the Lodge cellar key). The dirt path leaves
east toward the cornfields; west onto the ARRIVAL ROAD (the looping
road the PI drove in on, where the dead car / SPREAD escape now sits),
whose dirt path carries on to the country lane and town.

The basement is reached from inside the Clerk's house (the
kitchen cellar hatch). A previous build placed a redundant cellar
bulkhead in this yard too -- removed because it created a one-way
trip (basement only exits via the kitchen ladder) and a duplicate
"door to the basement" two tiles outside the same building.

THRESHOLD reskin: original 'our_house_area' had two houses, a patrol,
a rust-key cellar gate, and respawning enemies. All cut. The Sheriff
patrols this scene as part of his random outdoor route (wired in Pass F).
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def build_our_house_area():
    # 24w x 18h. The Clerk's house occupies the upper-left quadrant
    # with a back door (H) into the kitchen. The woodshed sits in the
    # lower-left -- a locked facade door 'l' you interact with (key-gated)
    # to enter the `woodshed` interior. The dirt road runs east-west across
    # the middle; west now leads onto the looping arrival road.
    floor = [
        "gggggggggggggggggggggggg",   # 0
        "gggggggggggggggggggggggg",   # 1
        "gggggggggggggggggggggggg",   # 2
        "gggggggggggggggggggggggg",   # 3
        "gggggggggggggggggggggggg",   # 4
        "ggggggdddddddddddddddddd",   # 5  short stub dirt north of footpath
        "dddddddddddddddddddddddd",   # 6  3-tile dirt footpath
        "dddddddddddddddddddddddd",   # 7
        "dddddddddddddddddddddddd",   # 8
        "ggggggdddddddddddddddddd",   # 9  short stub south
        "gggggggggggggggggggggggg",   # 10
        "gggggggggggggggggggggggg",   # 11
        "gggggggggggggggggggggggg",   # 12
        "gggggggggggggggggggggggg",   # 13
        "gggggggggggggggggggggggg",   # 14
        "gggggggggggggggggggggggg",   # 15
        "gggggggggggggggggggggggg",   # 16
        "gggggggggggggggggggggggg",   # 17
    ]
    # The yard's open ground -- the permeable forest band is stamped
    # below. Lodge structure (W roof walls, H back door) preserved in
    # the protected ring; west/east passages stay clear.
    objects = [
        "........................",   # 0
        "........................",   # 1
        "...WWWWW................",   # 2  Clerk's house north wall
        "...WrrrW................",   # 3  roof
        "...WrrrW................",   # 4  roof
        "...WWHWW................",   # 5  H = back door of the Clerk's house
        "a......................e",   # 6  west passage (river path)
        "a......................e",   # 7  east passage (cornfield_path)
        "a......................e",   # 8
        "........................",   # 9
        "........................",   # 10
        "........................",   # 11
        "........................",   # 12
        "........................",   # 13
        "........................",   # 14
        "........................",   # 15
        "........................",   # 16
        "........................",   # 17
    ]
    sc = Scene("our_house_area", floor, objects, music="village")
    # The Lodge yard wraps on the x axis. The country lane comes in
    # from the west; walking east through or past the yard wraps back
    # to its west side. The road past the Lodge to the highway doesn't
    # exist in fiction -- there is no past-the-Lodge; the fold makes
    # sure of it.
    sc.wrap_x = True
    # H = back door of the Clerk's house. Returns to 'house' scene
    # (the kitchen/living/hallway).
    sc.add_exit("H", "house", "from_our_house_area")
    # Outdoor passages: west onto the ARRIVAL ROAD (the looping road the PI
    # drove in on, with the dead car), which the dirt path carries on to the
    # country lane and town; east to the cornfield path.
    sc.add_exit("a", "arrival_road", "from_our_house_area")
    sc.add_exit("e", "forest_path", "from_our_house_area")
    # Direction-sensitive hidden fold: walking NORTH across the 'M'
    # tile (one of the yard's path tiles south of the Lodge) opens
    # onto Mara's arrival -- the night she walked up onto this porch
    # with a suitcase. From any other angle it's just yard floor.
    sc.add_exit("M", "lodge_arrival", "from_our_house_area",
                direction="north")
    # Carve the M tile into the yard at (5, 12), south of the Lodge
    # back door so the player passes it walking up to the porch.
    yard_obj = [list(r) for r in sc.objects]
    yard_obj[12][5] = "M"
    # The WOODSHED in the SW of the yard -- west of the Lodge, where it
    # belongs (it used to sit clear across town in brimley). A small solid
    # structure with a facade door 'l' on its north face; locked until you
    # find the woodshed key in the Lodge cellar. Clear of the dirt path
    # (cols 4-6) and the 'M' arrival fold (5,12).
    for cy in (12, 13, 14):
        for cx in (1, 2, 3):
            yard_obj[cy][cx] = "W"
    yard_obj[12][2] = "l"          # locked facade door, north face
    sc._shed_door_pos = (2 * TILE + 16, 12 * TILE + 16)
    # ---- Permeable forest band ----
    # Replaces the old hard corn-wall perimeter. Same helper as brimley
    # so the visual treatment of the wrap is consistent. Lodge structure
    # + door passages stay protected.
    floor_ll_yd = [list(r) for r in sc.floor]
    YARD_W = len(yard_obj[0]); YARD_H = len(yard_obj)
    def _yd_protected(tx, ty):
        # West + east passage corridors (rows 6-8 deep into the band).
        if 6 <= ty <= 8:
            return True
        # Lodge structure footprint + porch approach.
        if 2 <= tx <= 7 and 2 <= ty <= 6:
            return True
        # The road row stub (5-9 north + south stubs of road).
        if 5 <= ty <= 9 and tx >= 5:
            return True
        # The main dirt path running SOUTH from the Lodge porch (the 'M'
        # arrival-fold tile sits on it). Protected so the forest band doesn't
        # scatter trees onto it; painted dirt just below (after scatter), cut
        # clean through the band like the roads (NARRATIVE 11).
        if 4 <= tx <= 6 and 9 <= ty <= 14:
            return True
        # The woodshed footprint + its north approach (so the forest band
        # doesn't bury the door).
        if 1 <= tx <= 3 and 11 <= ty <= 15:
            return True
        return False
    _yd_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_ll_yd, yard_obj, YARD_W, YARD_H,
                        depth=3, seed=83,
                        tree_density=0.50, passable_ratio=0.65,
                        bush_density=0.18,
                        protected=_yd_protected,
                        place_bush=lambda px, py:
                            _yd_bushes.append((px, py)))
    sc.floor = floor_ll_yd
    sc.objects = yard_obj
    # Paint the main path south from the Lodge as DIRT -- it was bare grass,
    # but the 'M' arrival fold is described as one of the yard's path tiles.
    # A 3-wide corridor from the east-west road down past the M tile, so the
    # walk up to the porch reads as a maintained path, not blank lawn.
    for ty in range(9, 15):
        for tx in range(4, 7):
            if 0 <= ty < len(sc.floor) and 0 <= tx < len(sc.floor[ty]):
                sc.floor[ty][tx] = "d"
    for bx, by in _yd_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))

    sc.set_spawn("default", 12, 7)
    sc.set_spawn("from_house", 5, 6)             # one south of back door
    sc.set_spawn("from_country_lane", 1, 7)      # one east of west passage
    sc.set_spawn("from_arrival_road", 1, 7)      # walked EAST off the road
    sc.set_spawn("from_village", 1, 7)           # legacy save alias
    sc.set_spawn("from_forest", 22, 7)           # one west of east passage
    sc.set_spawn("from_river", 1, 7)             # west passage spawn alias
    sc.set_spawn("from_woodshed", 2, 11)         # one N of the shed door
    # Return spawn from the lodge_arrival fold -- lands the player
    # one tile south of the directional M tile so they don't
    # immediately re-trigger the fold.
    sc.set_spawn("from_lodge_arrival", 5, 13)

    # The pickup truck -- a decoration the player can SEE but not
    # use. The player's car (the escape vehicle) is on the Brimley
    # east bank; this truck is the Clerk's. Now drawn at
    # vehicle scale (~2 tiles wide); a 2x1 footprint of solid 'X'
    # invisible tiles under it makes the player bump correctly.
    sc.add_decoration(Decoration(20 * TILE + 16, 12 * TILE + 16,
                                 "pickup_truck"))
    objects = [list(r) for r in sc.objects]
    for tx in (19, 20, 21):
        if 0 <= tx < sc.w:
            objects[12][tx] = "X"
    sc.objects = objects

    # No hide spots: the solid pickup truck and the corn perimeter are
    # cover the player breaks line of sight behind (corn is walkable cover).
    sc.hide_spots = []

    def _outside_interact(game):
        px, py = game.player.x, game.player.y
        # The woodshed -- locked facade door. Needs the woodshed key from the
        # Lodge cellar workbench; opens to the woodshed interior (axe, rope,
        # flashlight). Now in the yard, west of the Lodge, where you'd expect
        # it -- not across town.
        sdx, sdy = sc._shed_door_pos
        if abs(px - sdx) < 44 and abs(py - sdy) < 44:
            if not game.player.inventory.has("woodshed_key"):
                game.audio.play("door_locked", 0.6)
                game.show_notice("Locked. The key's somewhere inside the "
                                 "Lodge.")
                return
            game.audio.play("door_open", 0.7)
            game.begin_transition("woodshed", "from_yard")
            return
        # Bloody handprint on the back door -- atmosphere, not a clue.
        # show_notice keeps it as a corner-line that doesn't interrupt
        # play with a full dialog pop.
        hx, hy = sc._handprint_pos
        if abs(px - hx) < 48 and abs(py - hy) < 48:
            game.show_notice(
                "Handprint on the back door. Palm-out. Someone leaving.")
            return
        # The Clerk's pickup is visible-but-useless. Examining it turns
        # the noun into worldbuilding: he doesn't drive it because there
        # is nowhere in Brimley for him to go.
        tx, ty = 20 * TILE + 16, 12 * TILE + 16
        if abs(px - tx) < 56 and abs(py - ty) < 56:
            game.show_notice(
                "The Clerk's truck. He doesn't drive it. None of them do.")
    sc.on_interact_fn = _outside_interact
    # [E] cue on the shed door.
    sc.add_interactable(sc._shed_door_pos[0], sc._shed_door_pos[1], 44)

    # Atmosphere -- chimney smoke from the house, a couple of crows,
    # scattered grass. No patrol NPC. No enemy spawn.
    sc.add_decoration(Decoration(5 * TILE + 16, 2 * TILE - 6, "smoke"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE - 4, "lantern"))
    sc.add_decoration(Decoration(2 * TILE + 8, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(20 * TILE + 8, 16 * TILE + 22, "crow"))
    # Yard dressing: a clothesline (banner deco) between two lantern
    # posts, a garden bloodstain near the woodshed (something happened
    # here), a creepy_tree at the NE corner of the yard, two dead
    # crows on the dirt road, a bloody handprint smearing the back
    # door. The Clerk's window has a faint passing-figure already
    # baked into the tile draw -- watch the south face of his house.
    sc.add_decoration(Decoration(10 * TILE + 16, 10 * TILE + 16,
                                 "banner", color=(220, 220, 200)))  # clothesline
    sc.add_decoration(Decoration(8 * TILE + 16, 10 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(12 * TILE + 16, 10 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(21 * TILE + 16, 2 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(17 * TILE + 16, 7 * TILE + 16, "dead_crow"))
    # Bloody handprint smearing the south face of the Clerk's house,
    # right by the back door (col 5, row 5). The comment above this
    # block has long promised one; the prop is finally placed, and the
    # yard's interact gives it a voice.
    handprint_x = 6 * TILE + 16
    handprint_y = 5 * TILE + 28
    sc.add_decoration(Decoration(handprint_x, handprint_y, "bloodstain",
                                 scale=0.9))
    sc._handprint_pos = (handprint_x, handprint_y)
    # Small mailbox on the road shoulder (use a gas_pump deco -- close
    # enough silhouette; future polish could carve a true mailbox).
    sc.add_decoration(Decoration(11 * TILE + 16, 9 * TILE + 16,
                                 "phantom_mark"))   # mark in the dirt
    rng = random.Random(2026)
    for _ in range(20):
        gx = rng.randint(1, 22) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, 16) * TILE + rng.randint(0, 30)
        tx_ = gx // TILE; ty_ = gy // TILE
        if 2 <= ty_ <= 5 and 3 <= tx_ <= 7: continue
        if 11 <= ty_ <= 14 and 3 <= tx_ <= 7: continue
        if 6 <= ty_ <= 8: continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    return sc


def build_arrival_road():
    """The county road the PI drove in on -- west of the Arcadia. A gravel
    road running NORTH-SOUTH that the fold has closed into a LOOP: walk it
    either way and it never ends (wrap_y), the same stretch coming around
    again, your own dead car passing on the shoulder a second time, a third.
    Nothing stops you turning back -- a DIRT PATH crosses it east-west (the
    real route: east to the Lodge yard, west on to the country lane and town).

    The dead car is the PI's own, killed at the steps on the way in. It is the
    SPREAD escape: the engine catches only with the Sign, and then the looping
    road finally lets a car through (NARRATIVE §1/§6).

    The road is deliberately TALLER than the camera view so the wrap never
    shows its own repeat in a single frame -- you don't notice the loop until
    you've walked far enough for your own car to come back around. The E-W PATH
    sits in the SOUTH third; NORTH of it is a long straight runway toward the
    idle King at the vanishing point (KING_PROMPT idle state): he hangs a fixed
    gap up the road, so running the runway never closes on him -- the road grows
    between you. The car sits just north of the path."""
    W, H = 15, 80
    PATH = (H - 14, H - 13, H - 12)     # the E-W dirt path rows (deep south)
    PMID = PATH[1]                       # the path's centre row (the mouths)
    floor_rows = []
    for y in range(H):
        row = ["g"] * W
        if y in PATH:                       # E-W DIRT path (the real route)
            for x in range(W):
                row[x] = "d"
        for x in (6, 8):                    # N-S PAVED road lanes (runs through
            row[x] = "P"                    # the dirt crossing, unbroken)
        row[7] = "Y"                        # centre lane + dashed centreline
        floor_rows.append("".join(row))
    # Pine forest walls the road (same as the intro drive). RAGGED, not a ruled
    # line: each row's inner edge wavers a tile or two and the odd lone pine
    # stands out into the shoulder, so the treeline reads as woods, not a fence.
    # The road (cols 6-8) and the car/sign lane (cols 9-10) stay clear.
    forest_rng = random.Random(90210)
    objects_l = []
    for y in range(H):
        row = ["."] * W
        if y not in PATH:
            for x in range(0, 2 + forest_rng.randint(0, 2)):       # west wall
                row[x] = "T"
            for x in range(W - 2 - forest_rng.randint(0, 2), W):   # east wall
                row[x] = "T"
            if forest_rng.random() < 0.12:                          # lone pine W
                row[forest_rng.choice((3, 4))] = "T"
            if forest_rng.random() < 0.12:                          # lone pine E
                row[forest_rng.choice((11, 12))] = "T"
        objects_l.append(row)
    for dy in (-1, 0, 1):                   # path mouths W (lane) + E (yard)
        objects_l[PMID + dy][0] = "a"
        objects_l[PMID + dy][W - 1] = "e"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("arrival_road", floor_rows, objects, music="outside")
    # The road never ends: walk north or south and the same stretch wraps
    # back. The E-W path still exits normally -- only the road loops.
    sc.wrap_y = True
    sc.add_exit("a", "country_lane", "from_arrival_road")
    sc.add_exit("e", "our_house_area", "from_arrival_road")
    sc.set_spawn("default", 7, PMID)
    sc.set_spawn("from_our_house_area", W - 2, PMID)   # walked WEST from the yard
    sc.set_spawn("from_country_lane", 1, PMID)         # walked EAST from town side

    # Same road as the intro drive: the "Entering Brimley" sign on the east
    # shoulder, and just AHEAD of it (north, the way the PI drove in) his own
    # dead car. Off the driving lanes (cols 6-8) so the looping road stays
    # walkable both ways and you pass both each time round.
    sign_tx, sign_ty = 10, PMID - 4                    # east shoulder, by the path
    _sign_deco = Decoration(sign_tx * TILE + 16, sign_ty * TILE + 16,
                            "town_sign", text="BRIMLEY")
    sc.add_decoration(_sign_deco)
    sc._sign_deco = _sign_deco                          # hidden with the car on the treadmill
    # The dead car a few tiles north of the sign -- seen from BEHIND (it died
    # facing up the road into town). Solid footprint under the sprite; the
    # interact anchor sits at its road-facing (west) edge. The Sign fires
    # SPREAD; without it the engine never catches.
    car_tx, car_ty = 10, PMID - 9                      # east shoulder, N of sign
    car_x = car_tx * TILE + 16
    car_y = car_ty * TILE + 16
    # yaw -pi/2 aims the 3D car NORTH, up the road into town (default yaw 0 left
    # it broadside across the lane -- you saw its whole flank + all four tyres).
    _car_deco = Decoration(car_x, car_y, "player_car", yaw=-math.pi / 2)
    sc.add_decoration(_car_deco)
    sc._car_deco = _car_deco                           # so the treadmill can hide it
    sc._car_pos = ((car_tx - 1) * TILE + 16, car_y)   # west edge, by the road
    objs = [list(r) for r in sc.objects]
    for cx in (car_tx - 1, car_tx):                   # footprint runs N-S now
        for cy in (car_ty - 1, car_ty, car_ty + 1):   # (the car points up-road)
            if 0 <= cx < sc.w and 0 <= cy < sc.h:
                objs[cy][cx] = "X"
    sc.objects = objs

    def _road_interact(game):
        cx, cy = sc._car_pos
        if abs(game.player.x - cx) < 44 and abs(game.player.y - cy) < 44:
            if (game.player.inventory.has("sigil_rubbing")
                    and hasattr(game, "_begin_car_escape")):
                game._begin_car_escape()          # the Sign breaks the fold
                return
            game.audio.play("door_locked", 0.6)
            game.show_notice("You turn the key. The engine catches, and "
                             "catches, and dies. The fold won't let the car "
                             "go. Not with empty hands.")
    sc.on_interact_fn = _road_interact
    sc.add_interactable(sc._car_pos[0], sc._car_pos[1], 44)

    # Atmosphere: corn tufts off the road, a reflector post or two, a dead
    # crow on the gravel, a missing-flyer the rain has taken. Hide spots in
    # the corn shoulders.
    rng = random.Random(2031)
    for _ in range(70):
        gx = rng.randint(0, W - 1) * TILE + rng.randint(0, 30)
        gy = rng.randint(0, H - 1) * TILE + rng.randint(0, 30)
        tx_, ty_ = gx // TILE, gy // TILE
        if 6 <= tx_ <= 8:                   # keep the road clear
            continue
        if ty_ in PATH:                     # keep the path clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(5 * TILE + 8, 28 * TILE + 22, "dead_crow"))
    sc.add_decoration(Decoration(4 * TILE + 16, 22 * TILE + 16, "missing_flyer"))
    sc.add_decoration(Decoration(5 * TILE + 8, 12 * TILE + 22, "dead_crow"))
    # Extra leafless trees just inside the WEST shoulder up the long runway --
    # under tilt they stand as billboards, deepening the forest wall and giving
    # the approach toward the idle King its perspective + scroll read (the
    # treadmill to the vanishing point). The east shoulder holds the sign + car.
    tree_rng = random.Random(7777)
    ry = 3
    while ry < PMID - 4:
        # irregular spacing + wandering column + jitter so they never line up;
        # east side only well north of the car/sign lane.
        col = tree_rng.choice((3, 4, 5) if ry > PMID - 16 else (3, 4, 5, 11, 12))
        sc.add_decoration(Decoration(col * TILE + tree_rng.randint(2, 30),
                                     ry * TILE + tree_rng.randint(2, 30),
                                     "creepy_tree"))
        ry += tree_rng.randint(3, 8)
    sc.hide_spots = []

    def _road_update(game, scene, dt):
        # The TELL. The road wraps N-S (wrap_y), so walking it long enough
        # brings the same stretch -- and the PI's own dead car -- back around.
        # The recurring car IS the recognition (no narration, NARRATIVE §1b
        # discipline); a soft, escalating dread pulse underscores the wrongness
        # the moment the fold folds the road back. Detected as the big single-
        # frame y jump the wrap produces.
        p = game.player
        if p is None:
            return
        wh = scene.h * TILE
        last = getattr(scene, "_last_py", None)
        if last is not None and abs(p.y - last) > wh * 0.5:
            scene._loops = getattr(scene, "_loops", 0) + 1
            game.save.set_flag("arrival_road_looped", True)
            game.audio.play("low_pulse", min(0.75, 0.34 + 0.12 * scene._loops))
        scene._last_py = p.y
    sc.on_update_fn = _road_update
    return sc


def build_woodshed():
    """The Arcadia woodshed -- in the SW of the Lodge yard, west of the
    Lodge (it used to sit clear across town; consolidated here so the tools
    are where you'd expect). Single room: splitting axe on the wall, a coil
    of rope on the workbench, the flashlight on a chopping stump in the
    centre. Locked from outside; the key is in the Lodge cellar."""
    floor = ["=" * 12 for _ in range(9)]
    objects = [
        "WWWWWWWWWWWW",   # 0
        "W.....W....W",   # 1  main shed (cols 1-5) | tool nook (cols 7-10)
        "W.....W....W",   # 2  workbench (rope) out front
        "W..........W",   # 3  doorway gap in the partition (col 6)
        "W.....W....W",   # 4
        "W.....WWWWWW",   # 5  tool nook sealed off below
        "W..........W",   # 6
        "W...h......W",   # 7  h = exit door (back to the yard)
        "WWWWWWWWWWWW",   # 8
    ]
    sc = Scene("woodshed", floor, objects, music="home")
    # `h` exit returns the player to the LODGE YARD (the shed is back in the
    # Arcadia yard, west of the Lodge).
    sc.add_exit("h", "our_house_area", "from_woodshed")
    sc.set_spawn("default",            5, 6)
    sc.set_spawn("from_yard",          4, 6)   # entered from the yard door
    sc.set_spawn("from_brimley_shed",  4, 6)   # legacy fallback
    sc.set_spawn("from_village_shed",  4, 6)   # legacy fallback

    rope_pos   = (2 * TILE + 16, 2 * TILE + 16)
    # The splitting axe hangs in the back tool nook -- behind the partition,
    # so the weapon is an indoor blind spot you have to round the wall for.
    axe_pos    = (8 * TILE + 16, 1 * TILE + 16)
    flash_pos  = (4 * TILE + 16, 5 * TILE + 16)   # on the chopping stump
    sc._rope_pos = rope_pos
    sc._axe_pos  = axe_pos
    sc._flash_pos = flash_pos
    # Sized workbench (the rope sits on it).
    sc.add_furniture("table", [(2, 2)], w=54, h=36)
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(3 * TILE + 20, 6 * TILE + 8, "bloodstain",
                                 scale=2.6))
    # It IS a woodshed: a split-wood stack against the west wall, a
    # kerosene lamp on the workbench, and cobwebs in the corners. The
    # firewood is collision furniture, set clear of the axe/rope/door.
    sc.add_furniture("firewood", [(1, 5), (1, 6)], w=24, h=58)
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = []

    def _woodshed_interact(game):
        px, py = game.player.x, game.player.y
        # Axe on the wall.
        if abs(px - axe_pos[0]) < 36 and abs(py - axe_pos[1]) < 36:
            if not game.save.flag("axe_taken"):
                game.save.set_flag("axe_taken", True)
                game.player.inventory.add("lumber_axe", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("Splitting axe.")
                return
        # Rope on the bench.
        if abs(px - rope_pos[0]) < 36 and abs(py - rope_pos[1]) < 36:
            if not game.save.flag("rope_taken"):
                game.save.set_flag("rope_taken", True)
                game.player.inventory.add("rope", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("Coil of rope. Long enough for the well.")
                return
        # Flashlight left on the chopping stump in the centre.
        if abs(px - flash_pos[0]) < 36 and abs(py - flash_pos[1]) < 36:
            if not game.save.flag("flashlight_taken"):
                game.save.set_flag("flashlight_taken", True)
                game.player.inventory.add("flashlight", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("A flashlight. Press [F] in the dark, "
                                 "but light draws the eye.")
                return
    sc.on_interact_fn = _woodshed_interact

    def _woodshed_on_enter(game, scene):
        # The axe, rope and flashlight had no world object AND no [E] cue
        # -- three critical items you'd walk right past. Glimmer-mark each
        # one still on offer and register it for the [E] prompt; drop the
        # marker once it's been taken.
        for pos, flag in ((axe_pos, "axe_taken"),
                          (rope_pos, "rope_taken"),
                          (flash_pos, "flashlight_taken")):
            if not game.save.flag(flag):
                scene.add_decoration(Decoration(pos[0], pos[1], "item_drop"))
                scene.add_interactable(pos[0], pos[1], 36)
        # A box of cartridges by the hunting gear (this is a hunting town).
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 4, 3, 6, "ammo_woodshed")
    sc.on_enter_fn = _woodshed_on_enter
    return sc
