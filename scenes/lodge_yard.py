"""outside_innkeeper_house (key: 'lodge_yard') -- the gravel
yard behind the Clerk's house. The WOODSHED sits in the SW (the axe,
flashlight; a locked facade door 'l' -> the `woodshed`
interior, key-gated by the Lodge cellar key). The dirt path leaves
east toward the cornfields; west onto the ARRIVAL ROAD (the looping
road the PI drove in on, where the dead car / SPREAD escape now sits),
whose dirt path carries on to the country lane and town.

The basement is reached from inside the Clerk's house (the
kitchen cellar hatch). A previous build placed a redundant cellar
bulkhead in this yard too -- removed because it created a one-way
trip (basement only exits via the kitchen ladder) and a duplicate
"door to the basement" two tiles outside the same building.

THRESHOLD reskin: original 'lodge_yard' had two houses, a patrol,
a rust-key cellar gate, and respawning enemies. All cut. The Sheriff
patrols this scene as part of his random outdoor route (wired in Pass F).
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def build_lodge_yard():
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
        "..WWWWWWWW..............",   # 2  the Arcadia -- a two-storey hotel now
        "..WrrrrrrW..............",   # 3  roof (loft dormer stands over it)
        "..WrrrrrrW..............",   # 4  roof
        "..WiWHWWiW..............",   # 5  south face: door H (col5), lit windows
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
    sc = Scene("lodge_yard", floor, objects, music="village")
    # The Lodge yard wraps on the x axis. The country lane comes in
    # from the west; walking east through or past the yard wraps back
    # to its west side. The road past the Lodge to the highway doesn't
    # exist in fiction -- there is no past-the-Lodge; the fold makes
    # sure of it.
    sc.wrap_x = True
    # H = back door of the Clerk's house. Returns to 'lodge' scene
    # (the kitchen/living/hallway).
    sc.add_exit("H", "lodge", "from_lodge_yard")
    # Outdoor passages: west onto the ARRIVAL ROAD (the looping road the PI
    # drove in on, with the dead car), which the dirt path carries on to the
    # country lane and town; east to the cornfield path.
    sc.add_exit("a", "arrival_road", "from_lodge_yard")
    sc.add_exit("e", "cornfield_path", "from_lodge_yard")
    yard_obj = [list(r) for r in sc.objects]
    # The WOODSHED in the SW of the yard -- west of the Lodge, where it
    # belongs (it used to sit clear across town). A small solid
    # structure with a facade door 'l' on its north face; locked until you
    # find the woodshed key in the Lodge cellar. Clear of the dirt path
    # (cols 4-6).
    for cy in (12, 13, 14):
        for cx in (1, 2, 3):
            yard_obj[cy][cx] = "W"
    yard_obj[12][2] = "l"          # locked facade door, north face
    sc._shed_door_pos = (2 * TILE + 16, 12 * TILE + 16)
    # ---- Permeable forest band ----
    # Replaces the old hard corn-wall perimeter. The same helper the yards
    # so the visual treatment of the wrap is consistent. Lodge structure
    # + door passages stay protected.
    floor_ll_yd = [list(r) for r in sc.floor]
    YARD_W = len(yard_obj[0]); YARD_H = len(yard_obj)
    def _yd_protected(tx, ty):
        # West + east passage corridors (rows 6-8 deep into the band).
        if 6 <= ty <= 8:
            return True
        # Lodge structure footprint + porch approach (widened 2026-07 -- the
        # Arcadia is a two-storey hotel now, cols 2-9).
        if 2 <= tx <= 9 and 2 <= ty <= 6:
            return True
        # The pocket clearing behind the Lodge (a protected pocket; the
        # old 'M' arrival fold that stood here was cut). The band still crowds
        # the rest of the strip, so reaching the pocket means pushing
        # through the scattered trees around the building's sides.
        if 4 <= tx <= 6 and ty <= 1:
            return True
        # The road row stub (5-9 north + south stubs of road).
        if 5 <= ty <= 9 and tx >= 5:
            return True
        # The main dirt path running SOUTH from the Lodge porch toward the
        # woodshed corner. Protected so the forest band doesn't scatter
        # trees onto it; painted dirt just below (after scatter), cut
        # clean through the band like the roads (DESIGN.md §7).
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
    # Paint the main path south from the Lodge as DIRT -- it was bare grass.
    # A 3-wide corridor from the east-west road down toward the woodshed
    # corner, so the walk up to the porch reads as a maintained path, not
    # blank lawn.
    for ty in range(9, 15):
        for tx in range(4, 7):
            if 0 <= ty < len(sc.floor) and 0 <= tx < len(sc.floor[ty]):
                sc.floor[ty][tx] = "d"
    for bx, by in _yd_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))
    # A BRIMLEY board on the road's north shoulder by the WEST mouth
    # (2026-07 playtest fix): leaving the Lodge yard, town is that way.
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 24,
                                 "town_sign", text="BRIMLEY"))

    # THE MOUTH (TODO #26). North and south of the yard is the forest band,
    # and past it the map bound -- an invisible wall in daylight. Once the
    # storm has darkened the surface (rot stage 2, so you have earned two
    # pieces of Mara's trail), pushing through the treeline in the dark stops
    # being refused: the world lets go and drops you in the lost forest. The
    # x axis is the fold and stays a fold; only the treeline opens. The yard
    # light by the porch is genuine cover -- a lit spot never opens.
    sc.set_lost_edge("ns", "lost_forest")

    # ---- THE YARD VOCABULARY (DESIGN.md §14, TODO #26) ----
    # A yard's job is to tell you about a household without anybody speaking.
    # Every piece below answers who lives here and what they stopped doing;
    # nothing is here for texture. All are parts-built props checked against
    # a real reference (rendering/references.py).
    #
    # THE STOOP at the Lodge's back door: the step between the ground and
    # the threshold, so going in reads as arriving. yaw=-pi/2 climbs north,
    # into the door.
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 20, "stoop",
                                 yaw=-math.pi / 2))
    # THE GENSET against the Lodge's east wall, and it is RUNNING: Sable
    # keeps the desk of an empty hotel lit and ready (NARRATIVE §4). The
    # grid died with the seal, so a warm work-bulb burning out here is the
    # tell that somebody is still keeping the place.
    sc.add_decoration(Decoration(10 * TILE + 16, 4 * TILE + 16, "generator",
                                 running=True))
    # and the can standing beside it, which is the other half of the same
    # sentence: somebody is still walking out here to fuel this thing
    # (DESIGN.md §15). A dead yard's can lies on its side and empty.
    sc.add_decoration(Decoration(11 * TILE + 12, 4 * TILE + 16, "fuel_can"))
    # THE MAILBOX out at the road, exactly on the seam where the yard meets
    # the safe path. Deliveries stopped with the fold in January, so it is
    # still FULL: nobody has emptied it because nothing has come to replace
    # what is in it.
    sc.add_decoration(Decoration(12 * TILE + 16, 5 * TILE + 24, "mailbox",
                                 yaw=math.pi / 2, full=True))
    # THE INTERRUPTED TASK: firewood half-stacked AGAINST the woodshed's east
    # wall with the axe still standing in the block. The seal was January and
    # it is April. It has to touch the shed: a stack standing alone in open
    # dirt reads as dumped lumber, and firewood is always stacked against
    # something so it does not fall over (rendering/references.py).
    sc.add_decoration(Decoration(4 * TILE + 6, 13 * TILE + 16, "woodpile",
                                 yaw=math.pi / 2, axe=True))
    # THE BOUNDARY: a wire fence along the yard's south side, where the kept
    # ground stops and the treeline starts. It reads as an edge you push
    # through rather than a wall, which is what the mouth needs (DESIGN §13).
    #
    # The bays are laid END TO END, at the bay's own width rather than on a
    # tile multiple. Spaced every four tiles they were 42-unit bays with
    # 86-unit holes between them, which reads as four abandoned fence
    # FRAGMENTS instead of one line -- and a boundary that is mostly hole
    # cannot make a gap mean anything.
    _BAY = 33.0
    _x0 = 9 * TILE
    _n = int((21 * TILE - _x0) / _BAY) + 1
    for _i in range(_n):
        sc.add_decoration(Decoration(_x0 + _i * _BAY, 15 * TILE + 20,
                                     "yard_fence",
                                     seed=_i, gap=(_i == _n // 2)))

    sc.set_spawn("default", 12, 7)
    sc.set_spawn("from_lodge", 5, 6)             # one south of back door
    sc.set_spawn("from_country_lane", 1, 7)      # one east of west passage
    sc.set_spawn("from_arrival_road", 1, 7)      # walked EAST off the road
    sc.set_spawn("from_forest", 22, 7)           # one west of east passage
    sc.set_spawn("from_woodshed", 2, 11)         # one N of the shed door

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

    # Enclosed hide (the 2026-07 stealth pass, TODO #5): the gap under
    # the Clerk's dead pickup. The corn perimeter stays the mobile
    # concealment the player breaks line of sight in.
    sc.hide_spots = [
        (20 * TILE + 16, 13 * TILE + 16, "under"),   # under the pickup's bed
    ]

    def _outside_interact(game):
        px, py = game.player.x, game.player.y
        # The woodshed -- locked facade door. Needs the woodshed key from the
        # Lodge cellar workbench; opens to the woodshed interior (axe,
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
    sc.on_interact_fn = _outside_interact
    # [E] cue on the shed door.
    sc.add_interactable(sc._shed_door_pos[0], sc._shed_door_pos[1], 44)

    # The LOFT DORMER standing over the roof -- the tell that the Arcadia is
    # two storeys (its lit window is Sable's loft). Like the church steeple,
    # rise lifts it onto the roofline and a depth_bias sorts it above the
    # building's own opaque roof so it isn't buried.
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 6, "lodge_gable",
                                 rise=26, depth_bias=140))
    # A hanging ARCADIA board by the porch -- the hotel's name.
    sc.add_decoration(Decoration(9 * TILE + 20, 6 * TILE + 8,
                                 "town_sign", text="ARCADIA"))
    # Atmosphere -- chimney smoke from the house, a couple of crows,
    # scattered grass. No patrol NPC. No enemy spawn. The smoke sits over
    # the roof's baked chimney at the BACK-EAST corner of the ridge
    # (2026-07 audit fix: the rebuild widened the roof and the plume was
    # left stranded at the west end, rising from nothing).
    sc.add_decoration(Decoration(9 * TILE + 8, 2 * TILE - 8, "smoke"))
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
    # A phantom mark in the road-shoulder dirt (a rot decal, not a
    # real prop).
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

    def _yard_on_enter(game, scene):
        # The CELLAR KEY hangs on a nail behind the house (2026-07: the
        # Ledger moved down into the padlocked cellar; this is its
        # gate). Walk-over pickup with a glimmer marker, flag-gated so
        # it drops exactly once per save.
        if (game.save.flag("cellar_key_taken")
                or game.player.inventory.has("cellar_key")):
            return
        kx, ky = 7 * TILE + 16, 1 * TILE + 16

        def _took(g):
            g.save.set_flag("cellar_key_taken", True)
            g.scene.decorations = [
                d for d in g.scene.decorations
                if not (d.kind == "item_drop"
                        and abs(d.x - kx) < 2 and abs(d.y - ky) < 2)]
        scene.add_item(kx, ky, "cellar_key", on_pickup=_took)
        scene.add_decoration(Decoration(kx, ky, "item_drop"))
    sc.on_enter_fn = _yard_on_enter

    return sc


def build_arrival_road():
    """The county road the PI drove in on -- west of the Arcadia. A gravel
    road running NORTH-SOUTH that the fold has stretched into an ENDLESS
    forest corridor: walk NORTH and the paved road + the pine walls tile on
    forever toward the vanishing point, the same anonymous stretch with NO
    landmark ever coming back around. Nothing stops you turning back -- a DIRT
    PATH crosses it east-west in the SOUTH (the real route: east to the Lodge
    yard, west on to the country lane and town).

    The infinity is built from a landmark-FREE forest BAND in the north that
    renders endlessly (Scene._render_band tiles its grass/road/treeline toward
    the horizon) AND loops your travel (the `_treadmill`: cross the band's north
    edge walking up and you warp back to its south edge, player + camera shifted
    together, no jump). The southern ARRIVAL zone -- the dead car, the BRIMLEY
    sign, the E-W crossing and its exits -- sits BELOW the band, renders ONCE,
    and never clones into the northern view. So walking north reads as infinite;
    turn around and you pass the fixed arrival zone once and exit by the path.

    The dead car is the PI's own, killed at the steps on the way in. It is the
    SPREAD escape: the engine catches only with the Sign, and then the road
    finally lets a car through (NARRATIVE §1/§6).

    NORTH of the crossing is a long straight runway toward the idle King at the
    vanishing point (KING_PROMPT idle state): he hangs a fixed gap up the road,
    so running the runway never closes on him -- the road grows between you."""
    # 2026-07: brought onto the SAFE PATH cross-section (DESIGN.md §14) so the
    # county road reads the same here as everywhere else -- five lanes of
    # asphalt in a nine-tile corridor, not a three-tile strip. Every column
    # below is derived from these rather than written as a literal, which is
    # what made the widening possible at all.
    from scenes.safe_path import ROAD_HALF, SHOULDER, LAMP_OFF, LAMP_STEP
    W, H = 23, 80
    ROAD_C = 11                          # the centre lane's column
    CORR = ROAD_HALF + SHOULDER          # corridor half-width (4)
    CAR_COL = ROAD_C + CORR + 2          # the car/sign lane, out on the verge
    PATH = (H - 14, H - 13, H - 12)     # the E-W dirt path rows (deep south)
    PMID = PATH[1]                       # the path's centre row (the mouths)
    floor_rows = []
    for y in range(H):
        row = ["g"] * W
        if y in PATH:                       # E-W DIRT path (the real route)
            for x in range(W):
                row[x] = "d"
        for dx in range(-CORR, CORR + 1):   # the N-S road runs through the
            x = ROAD_C + dx                 # dirt crossing, unbroken
            row[x] = "d" if abs(dx) > ROAD_HALF else "P"
        row[ROAD_C] = "Y"                   # centre lane + dashed centreline
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
            for x in range(0, 3 + forest_rng.randint(0, 3)):       # west wall
                row[x] = "T"
            for x in range(W - 3 - forest_rng.randint(0, 3), W):   # east wall
                row[x] = "T"
            if forest_rng.random() < 0.12:                          # lone pine W
                row[forest_rng.choice((ROAD_C - CORR - 2,
                                       ROAD_C - CORR - 1))] = "T"
            if forest_rng.random() < 0.12:                          # lone pine E
                row[forest_rng.choice((ROAD_C + CORR + 1,
                                       ROAD_C + CORR + 2))] = "T"
        objects_l.append(row)
    # South of the crossing the road RUNS ON -- and loops (2026-07: the
    # flat tree wall across the asphalt is gone). The lanes continue a
    # short stretch with the pines crowding back in at the shoulders;
    # walking south past the loop line folds you silently back onto the
    # road NORTH of the crossing (a same-scene relocation, the maze
    # pattern -- no fade, no frame): the roads loop, on foot, exactly as
    # the town says. SIGHTLINE RULE (maintainer): the idle King is a
    # NORTH-facing sight only -- the loop lands you SOUTH of the render
    # band (the idol gate reads player.y >= band bottom), so after
    # looping he is not in view until you deliberately walk north up
    # the band again. Beyond the loop line the canopy closes over the
    # lanes in a taper, so the far south reads as the woods taking the
    # road, not a hedge pasted across it.
    LOOP_ROW = PMID + 7
    for y in range(PMID + 2, H):
        objects_l[y] = ["T"] * W
    for y in range(PMID + 2, LOOP_ROW + 1):
        for x in range(ROAD_C - CORR, ROAD_C + CORR + 1):
            objects_l[y][x] = "."          # the road strip stays open
        if forest_rng.random() < 0.4:      # ragged inner tree edge
            objects_l[y][ROAD_C - CORR] = "T"
        if forest_rng.random() < 0.4:
            objects_l[y][ROAD_C + CORR] = "T"
    for i, y in enumerate(range(LOOP_ROW + 1, min(H, LOOP_ROW + 5))):
        for x in range(ROAD_C - ROAD_HALF, ROAD_C + ROAD_HALF + 1):
            if forest_rng.random() > 0.30 + 0.22 * i:
                objects_l[y][x] = "."
    for x in range(ROAD_C - CORR, ROAD_C + CORR + 1):   # the silent loop line
        if objects_l[LOOP_ROW][x] == ".":
            objects_l[LOOP_ROW][x] = "I"
    # CORN bleeds in at the WEST shoulder around the crossing (the corn
    # lane is right through the west mouth; the hard pine/corn biome cut
    # read disconnected). Passable stalks ('A') scattered over the
    # shoulder rows so the field leaks toward its gap in the trees.
    corn_rng = random.Random(1994)
    for y in range(PMID - 5, PMID + 4):
        for x in range(1, ROAD_C - CORR):
            if 0 <= y < H and objects_l[y][x] in (".", "T") \
                    and y not in PATH and corn_rng.random() < 0.45:
                objects_l[y][x] = "A"
    for dy in (-1, 0, 1):                   # path mouths W (lane) + E (yard)
        objects_l[PMID + dy][0] = "a"
        objects_l[PMID + dy][W - 1] = "e"
    # Keep the crossing's north shoulders clear for the directional
    # boards below (a lone pine or the wall jitter could land on them).
    objects_l[PMID - 2][ROAD_C - CORR - 1] = "."
    objects_l[PMID - 2][ROAD_C + CORR + 1] = "."
    objects = ["".join(r) for r in objects_l]
    sc = Scene("arrival_road", floor_rows, objects, music="outside")
    # A landmark-FREE forest band to the NORTH does two jobs: it RENDERS
    # endlessly (sc._render_band tiles its anonymous grass/road/treeline toward
    # the vanishing point -- never an unloaded edge, never a southern landmark
    # cloned into the distance) and it loops your TRAVEL (the `_treadmill`:
    # walking north past BAND_TOP warps you back to BAND_BOTTOM, player + camera
    # shifted together, no jump). The southern arrival stretch (car, sign, the
    # E-W crossing + its exits) sits BELOW the band, renders ONCE, and is walked
    # back to normally -- it never tiles north, so nothing recognisable repeats
    # ahead of you. NOTE: wrap_y is deliberately OFF (a full-column wrap would
    # clone the car / sign / dirt path into the northern view -- the old loop
    # tell, now reversed). The idle King shows only while you are on the band.
    sc.wrap_y = False
    _BAND_TOP, _BAND_BOTTOM = 8, PMID - 23     # rows; ~14 tiles N of the car
    sc._treadmill = (_BAND_TOP * TILE, _BAND_BOTTOM * TILE)
    sc._render_band = (_BAND_TOP, _BAND_BOTTOM)   # tile rows that tile north
    sc.add_exit("a", "country_lane", "from_arrival_road")
    sc.add_exit("e", "lodge_yard", "from_arrival_road")
    # The south loop: a same-scene direction-gated fold (silent by canon;
    # _build_fold_cache skips same-scene folds, so no frame is drawn).
    # Southward walkers land back NORTH of the crossing, south of the
    # render band, still striding south toward the crossing again.
    sc.add_exit("I", "arrival_road", "reloc_south_loop", direction="south")
    sc.set_spawn("reloc_south_loop", ROAD_C, PMID - 14)
    sc.set_spawn("default", ROAD_C, PMID)
    sc.set_spawn("from_lodge_yard", W - 2, PMID)   # walked WEST from the yard
    sc.set_spawn("from_country_lane", 1, PMID)         # walked EAST from town side

    # Same road as the intro drive: the "Entering Brimley" sign on the east
    # shoulder, and just AHEAD of it (north, the way the PI drove in) his own
    # dead car. Off the driving lanes (cols 6-8) so the looping road stays
    # walkable both ways and you pass both each time round.
    sign_tx, sign_ty = CAR_COL, PMID - 4               # east verge, by the path
    _sign_deco = Decoration(sign_tx * TILE + 16, sign_ty * TILE + 16,
                            "town_sign", text="BRIMLEY")
    _sign_deco._no_wrap = True                           # never clones into the road AHEAD
    sc.add_decoration(_sign_deco)
    # Directional boards FLANKING the crossing (2026-07 playtest fix:
    # "no clear roads from the lodge"). The junction is the one
    # wayfinding moment on the lodge side; each board stands on the
    # crossing's north shoulder beside the path it names, so a player
    # at the asphalt reads town-west, lodge-east at a glance.
    for bx, btxt in ((ROAD_C - CORR - 1, "BRIMLEY"),
                     (ROAD_C + CORR + 1, "LODGE")):
        b = Decoration(bx * TILE + 16, (PMID - 2) * TILE + 24,
                       "town_sign", text=btxt)
        b._no_wrap = True
        sc.add_decoration(b)
    # The dead car a few tiles north of the sign -- seen from BEHIND (it died
    # facing up the road into town). Solid footprint under the sprite; the
    # interact anchor sits at its road-facing (west) edge. The Sign fires
    # SPREAD; without it the engine never catches.
    car_tx, car_ty = CAR_COL, PMID - 9                 # east verge, N of sign
    car_x = car_tx * TILE + 16
    car_y = car_ty * TILE + 16
    # yaw -pi/2 aims the 3D car NORTH, up the road into town (default yaw 0 left
    # it broadside across the lane -- you saw its whole flank + all four tyres).
    _car_deco = Decoration(car_x, car_y, "player_car", yaw=-math.pi / 2)
    _car_deco._no_wrap = True                          # never clones into the road AHEAD
    sc.add_decoration(_car_deco)
    sc._car_pos = ((car_tx - 1) * TILE + 16, car_y)   # west edge, by the road
    objs = [list(r) for r in sc.objects]
    for cx in (car_tx - 1, car_tx):                   # footprint runs N-S now
        for cy in (car_ty - 1, car_ty, car_ty + 1):   # (the car points up-road)
            if 0 <= cx < sc.w and 0 <= cy < sc.h:
                # see-over solid ('x', the counter precedent): a sedan is
                # waist-high, so it blocks the body but not the sight cone
                # (the tall 'X' carved a hard black wedge behind the car,
                # 2026-07 quality sprint).
                objs[cy][cx] = "x"
    sc.objects = objs

    def _road_interact(game):
        cx, cy = sc._car_pos
        if abs(game.player.x - cx) < 44 and abs(game.player.y - cy) < 44:
            if (game.player.inventory.has("pallid_mask")
                    and hasattr(game, "_begin_car_escape")):
                game._begin_car_escape()          # His face breaks the fold
                return
            game.audio.play("door_locked", 0.6)
            game.show_notice("You turn the key. The engine catches, and "
                             "catches, and dies. Brimley won't let the car "
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
        if abs(tx_ - ROAD_C) <= CORR:       # keep the whole corridor clear
            continue
        if ty_ in PATH:                     # keep the path clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration((ROAD_C - CORR - 1) * TILE + 8,
                                 28 * TILE + 22, "dead_crow"))
    sc.add_decoration(Decoration((ROAD_C - CORR - 2) * TILE + 16,
                                 22 * TILE + 16, "missing_flyer"))
    sc.add_decoration(Decoration((ROAD_C - CORR - 1) * TILE + 8,
                                 12 * TILE + 22, "dead_crow"))
    # THE LAMP PATTERN (DESIGN.md §14), applied to the straight run: facing
    # pairs on the outer shoulder every LAMP_STEP rows. The endless stretch is
    # the one place in the game where the rhythm itself is the tell -- each
    # pair you pass looks exactly like the last one, forever.
    for ly in range(PMID - 6, 2, -LAMP_STEP):
        for lx in (ROAD_C - LAMP_OFF, ROAD_C + LAMP_OFF):
            m = Decoration(lx * TILE + 16, ly * TILE + 16, "street_lamp")
            m._no_wrap = True
            sc.add_decoration(m)

    # ---- Arrival-zone detail (2026-07 pass). South of the band only:
    # the looping runway north stays landmark-free on purpose. ----
    # The car died with a window gone: glass on the gravel by the
    # driver's door (a noise trap underfoot).
    sc.add_noise_trap((car_tx - 2) * TILE + 16, car_ty * TILE + 16,
                      "glass", seed=23)
    # The town walks the dirt path; the paved road keeps no prints.
    sc.add_decoration(Decoration((ROAD_C - CORR - 2) * TILE + 16,
                                 PATH[0] * TILE + 16, "mud_footprint"))
    sc.add_decoration(Decoration((ROAD_C - CORR - 1) * TILE + 24,
                                 PMID * TILE + 8, "mud_footprint"))
    # A crow posted by the east mouth that flushes as you leave the yard.
    # On the open verge just outside the corridor -- the widening pushed the
    # old literal column into the east tree wall.
    sc.add_noise_trap((ROAD_C + CORR + 1) * TILE + 16, (PMID - 2) * TILE + 16,
                      "crow", seed=24)
    for lx, ly in ((ROAD_C - CORR, PMID - 6), (ROAD_C + CORR, PMID + 1)):
        sc.add_decoration(Decoration(lx * TILE + 16, ly * TILE + 16,
                                     "leaves"))
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
        # The TELL. Walking the northern band long enough warps you back to its
        # south edge (the `_treadmill`) -- the same anonymous forest coming round
        # with no landmark to catch the eye, the road going nowhere. No narration
        # (NARRATIVE §2 discipline); a soft, escalating dread pulse underscores
        # the wrongness each time the fold folds the band back. Detected as the
        # single-frame y jump the treadmill warp produces (a band-height hop).
        p = game.player
        if p is None:
            return
        tm = getattr(scene, "_treadmill", None)
        band = (tm[1] - tm[0]) if tm else scene.h * TILE
        last = getattr(scene, "_last_py", None)
        if last is not None and abs(p.y - last) > band * 0.5:
            scene._loops = getattr(scene, "_loops", 0) + 1
            game.audio.play("low_pulse", min(0.75, 0.34 + 0.12 * scene._loops))
        scene._last_py = p.y
    sc.on_update_fn = _road_update
    return sc


def build_woodshed():
    """The Arcadia woodshed -- in the SW of the Lodge yard, west of the
    Lodge (it used to sit clear across town; consolidated here so the tools
    are where you'd expect). Single room: splitting axe on the wall, a coil
    of old chain on the workbench. Locked from outside; the key is in the
    Lodge cellar."""
    floor = ["=" * 12 for _ in range(9)]
    objects = [
        "WWWWWWWWWWWW",   # 0
        "W.....W....W",   # 1  main shed (cols 1-5) | tool nook (cols 7-10)
        "W.....W....W",   # 2  workbench out front
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
    sc.add_exit("h", "lodge_yard", "from_woodshed")
    sc.set_spawn("default",            5, 6)
    sc.set_spawn("from_yard",          4, 6)   # entered from the yard door

    # The splitting axe hangs in the back tool nook -- behind the partition,
    # so the weapon is an indoor blind spot you have to round the wall for.
    # (The flashlight LEFT the woodshed in the 2026-07 light pass: it is
    # the PI's own kit on the bedroom desk now, beside the pistol.)
    axe_pos    = (8 * TILE + 16, 1 * TILE + 16)
    sc._axe_pos  = axe_pos
    # Sized workbench.
    sc.add_furniture("table", [(2, 2)], w=54, h=36)
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(3 * TILE + 20, 6 * TILE + 8, "bloodstain",
                                 scale=2.6))
    # It IS a woodshed: a split-wood stack against the west wall, a
    # kerosene lamp on the workbench, and cobwebs in the corners. The
    # firewood is collision furniture, set clear of the axe/door.
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
                game.scene.clear_ground_marker(*axe_pos)
                return
    sc.on_interact_fn = _woodshed_interact

    def _woodshed_on_enter(game, scene):
        # The axe had no world object AND no [E] cue -- a critical item
        # you'd walk right past. Glimmer-mark it while still on offer and
        # register it for the [E] prompt; drop the marker once taken.
        if not game.save.flag("axe_taken"):
            scene.add_decoration(Decoration(axe_pos[0], axe_pos[1],
                                            "item_drop"))
            scene.add_interactable(axe_pos[0], axe_pos[1], 36)
    sc.on_enter_fn = _woodshed_on_enter
    return sc
