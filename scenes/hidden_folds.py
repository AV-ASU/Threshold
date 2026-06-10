"""Hidden fold scenes -- direction-sensitive warps off the main outdoor
world. Accessed by walking a specific tile in a specific direction;
from any other angle the tile reads as floor and the player walks
over it without consequence.

Each scene is small, atmospheric, and read-only -- the player witnesses
something they're not supposed to see, can leave the way they came, and
the scene exists to close a thread in the canon:

  effigy_grove     -- a cult work-clearing tended by no one: the dead fire,
                     the effigy ring, the nailed-up faces, no worker (the
                     rite claimed the whole town at once)
  lodge_arrival   -- Mara's arrival at the Lodge, witnessed (makes the
                     "she chose this" beat concrete)
  highway_walk    -- the road the missing locals walked out on, where it
                     stretches and never ends

All three are in SEAMLESS_WORLD_SCENES so crossing into them carries no
fade -- the player walks into the fold without realising they crossed
a boundary.
"""
import random
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene


# ----- #2: The Work-Clearing (no worker) ----------------------------

def build_effigy_grove():
    """A clearing the cult once worked, found by walking east-to-west
    through a specific cornstalk gap in cornfield_maze, or (act break)
    through the school door. A dead fire pit at centre, effigy-dolls in a
    ring, a polaroid board with faces nailed to it -- the work without the
    worker (the closing rite claimed the town at once, NARRATIVE 1b/3).

    THE WAY DOWN lives here now: a fold stands over the dead fire ('O'),
    clarifying with the evidence count (fold_charge_fn) and crossable only
    at 3 evidence (exit_gate_fn) -- the world rots and opens on the same
    dial. Crossing it lands at the bottom of the well (well_bottom). The
    Deep Stair seals it (descent_sealed). A second fold ('M') is the school
    door's return pane, open only once the chalk door is drawn."""
    W, H = 18, 13
    # Floor: charred dirt at the centre, grass at the edges. The clearing
    # is wider than the old build so the tree-wall standees ring the
    # tableau instead of crowding it (the fire and the fold need air).
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if 6 <= tx <= 12 and 4 <= ty <= 8:
                row.append("x")     # charred ground around the fire
            else:
                row.append("g")
        floor_rows.append("".join(row))
    # Objects: tree-wall perimeter, "G" return tile on the EAST face
    # (the player walked west to get in; walking east back out returns
    # to the maze).
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if ty == 0 or ty == H - 1 or tx == 0 or tx == W - 1:
                row.append("T")
            else:
                row.append(".")
        objects_l.append(row)
    # Return exit on the east wall at the centre row. (Off the fold's
    # column, so walking out east never brushes the way down.)
    objects_l[6][W - 1] = "G"
    # THE WAY DOWN: the fold tile at the dead fire ('O', a marker char:
    # invisible, walkable), walked SOUTH into --
    # a deliberate step into the pane, never crossed by the natural
    # east-west walk through the clearing.
    objects_l[5][9] = "O"
    # The school door's grove-side pane ('M'), south of the ring. Walked
    # SOUTH.
    objects_l[10][9] = "M"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("effigy_grove", floor_rows, objects, music="outside")
    # Part of the continuous outside world -- transitions in and out
    # are fade-less.
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("G", "cornfield_maze", "from_effigy_grove")
    sc.add_exit("O", "well_bottom", "from_grove", direction="south")
    sc.add_exit("M", "schoolhouse", "from_grove", direction="south")
    sc.set_spawn("default", 1, 6)
    # The player walked WEST onto the entry tile in the maze; they
    # arrive on the west bank of the grove, the fire ahead of them.
    sc.set_spawn("from_cornfield_maze", 1, 6)
    # Back up out of the well: beside the fire, carried westward so
    # arrival never re-fires the south-walked crossing.
    sc.set_spawn("from_well_bottom", 8, 5)
    # In through the school door: one tile north of its return pane.
    sc.set_spawn("from_school", 9, 9)

    # ---- The two state-driven folds ----
    def _charge(game, ch):
        ev = game._evidence_count()
        if ch == "O":
            if game.save.flag("descent_sealed"):
                return 0.0
            # A thread of gold at 0 evidence; fully formed at 3. The
            # frame IS the evidence meter, standing in the world.
            return min(1.0, 0.15 + 0.85 * (ev / 3.0))
        if ch == "M":
            if not game.save.flag("school_door_open"):
                return 0.0
            # The school door forms over a few seconds when it is first
            # drawn; on any later load it simply stands.
            t0 = getattr(game, "_school_door_t0", None)
            if t0 is None:
                return 1.0
            import pygame as _pg
            return min(1.0, (_pg.time.get_ticks() - t0) / 2500.0)
        return 1.0
    sc.fold_charge_fn = _charge

    def _gate(game, ch):
        if ch == "O":
            if game.save.flag("descent_sealed"):
                return False
            if game._evidence_count() >= 3:
                return True
            # Shut: the tile reads as floor. Once, say why in sensation.
            if not game.save.flag("grove_fold_refused"):
                game.save.set_flag("grove_fold_refused", True)
                game.audio.play("low_pulse", 0.4)
                game.show_notice("The light over the fire will not take "
                                 "your weight. Not yet.", duration=3.2)
            return False
        if ch == "M":
            return (game.save.flag("school_door_open")
                    and _charge(game, "M") >= 0.999)
        return True
    sc.exit_gate_fn = _gate

    def _grove_enter(game, scene):
        if game.save.flag("grove_seen"):
            return
        game.save.set_flag("grove_seen", True)
        if (game._evidence_count() < 3
                and not game.save.flag("descent_sealed")):
            game.dialog.show([
                "[c=dim](Something over the dead fire catches the light. "
                "A thread of gold, standing on end. You lose it when you "
                "look straight at it.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
    sc.on_enter_fn = _grove_enter

    # ---- Decorations ----
    # The dead fire pit on the fold tile itself, the Sign painted under
    # it. (The fold's gold pool relights the charred ring as the frame
    # clarifies; the way down stands IN the fire.)
    sc.add_decoration(Decoration(9 * TILE + 16, 5 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(9 * TILE + 16, 5 * TILE + 16,
                                 "yellow_sign"))
    # Effigy circle around the fire -- six small chairs/effigies on
    # the charred ring. Each represents a local the priest was working
    # against.
    effigy_ring = [
        (7, 4), (11, 4), (7, 8), (11, 8), (6, 6), (13, 6),
    ]
    for tx, ty in effigy_ring:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "small_chair"))
    # Polaroid board on the north wall -- faces nailed up.
    sc.add_decoration(Decoration(9 * TILE + 16, 1 * TILE + 22,
                                 "polaroid_wall"))
    # Two leafless trees flanking the ring -- focal dread.
    sc.add_decoration(Decoration(4 * TILE + 16, 6 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(14 * TILE + 16, 6 * TILE + 16,
                                 "creepy_tree"))
    # Hanging figures in the deep canopy at the corners.
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(15 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    # One old stain on the approach, one mark off the ring -- kept sparse
    # so the fire and the fold stay the focus.
    sc.add_decoration(Decoration(4 * TILE + 16, 6 * TILE + 16,
                                 "bloodstain"))
    sc.add_decoration(Decoration(7 * TILE + 16, 9 * TILE + 16,
                                 "phantom_mark"))
    # Watching-wounds in the surrounding tree-mass.
    sc.add_decoration(Decoration(0 * TILE + 24, 5 * TILE + 16,
                                 "watching_wound", size="small"))
    sc.add_decoration(Decoration(17 * TILE + 8, 7 * TILE + 16,
                                 "watching_wound", size="small"))
    # ---- No worker ----
    # There is no worker here. The closing rite claimed the whole town
    # at once (NARRATIVE 1b/3), so individual cursing -- and the figure
    # who'd do it -- is gone. The grove is left as the work without the
    # worker: the dead fire, the effigy ring, the nailed-up faces, all
    # tended by no one you'll ever see. It reads like its siblings
    # (husk_grove, scarecrow_ring): a maker-less dread tableau.
    sc.hide_spots = []
    return sc


# ----- #3: Mara's Arrival -------------------------------------------

def build_lodge_arrival():
    """The Lodge yard at a different moment -- Mara on the porch with
    her suitcase, the Clerk welcoming her in. Both are frozen-feeling.
    They do not see the PI. The PI can walk around them, see her face,
    and leave by the south end of the yard. Makes 'she chose this'
    concrete. Entered through the BACK of the Lodge (the fold pane
    against its rear wall in our_house_area, walked south): in the
    back, out the front, years earlier -- the building is the fold."""
    W, H = 18, 12
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if 4 <= tx <= 13 and 4 <= ty <= 8:
                row.append("d")     # the yard's worn dirt
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if ty == 0 or ty == H - 1 or tx == 0 or tx == W - 1:
                row.append("T")
            else:
                row.append(".")
        objects_l.append(row)
    # Return tile on the SOUTH wall at col 9. The player stepped out of
    # the Lodge's front; walking south down the yard (past the tableau)
    # returns them to our_house_area, back behind the building.
    objects_l[H - 1][9] = "G"
    # The Lodge's south face -- one row of wall + a door at col 9.
    for tx in range(5, 14):
        objects_l[3][tx] = "W"
    objects_l[3][9] = "d"   # leave the doorway as floor so it reads
                            # as the Lodge's open front door
    objects = ["".join(r) for r in objects_l]
    sc = Scene("lodge_arrival", floor_rows, objects, music="village")
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("G", "our_house_area", "from_lodge_arrival")
    sc.set_spawn("default", 9, H - 2)
    # The player walked SOUTH into the back of the Lodge; they emerge
    # just south of its porch in the past, stride preserved -- out the
    # front door of the building they walked into the back of. Two
    # tiles below Mara so the spawn never overlaps the figures; one
    # turn and the tableau is there.
    sc.set_spawn("from_our_house_area", 9, 6)
    # ---- Decorations ----
    # Lit windows flanking the Lodge door.
    sc.add_decoration(Decoration(7 * TILE + 16, 3 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16, 3 * TILE + 16, "candle"))
    # Mara's suitcase on the porch step.
    sc.add_decoration(Decoration(10 * TILE + 16, 4 * TILE + 16, "table"))
    # A single lantern over the door.
    sc.add_decoration(Decoration(9 * TILE + 16, 2 * TILE + 22, "lantern"))
    # Grass tufts and crows in the yard.
    rng = random.Random(411)
    for _ in range(18):
        gx = rng.randint(2, W - 3) * TILE + rng.randint(2, 28)
        gy = rng.randint(8, H - 2) * TILE + rng.randint(2, 28)
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(2 * TILE + 16, 9 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(15 * TILE + 16, 9 * TILE + 16, "crow"))
    # The "this happened" mark -- one phantom_mark on the path.
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE + 16,
                                 "phantom_mark"))
    # ---- The figures ----
    # Mara on the porch, with her back partly to the PI (facing the
    # door, which is north). She does not see the PI.
    mara = NPC(9 * TILE + 16, 4 * TILE + 22, "Mara",
               "townswoman", movement="idle", radius=20)
    mara.facing = (0, -1)
    mara.lock_facing = True
    sc.add_npc(mara)
    # The Clerk just inside the doorway, leaning out. He smiles. He
    # does not see the PI either.
    clerk = NPC(9 * TILE + 16, 3 * TILE + 8, "the Clerk",
                "clerk", movement="idle", radius=18)
    clerk.facing = (0, 1)   # facing Mara, south
    clerk.lock_facing = True
    sc.add_npc(clerk)
    return sc


# ----- #4: The Highway That Doesn't End -----------------------------

def build_highway_walk():
    """A short stretch of empty highway that wraps east-west forever.
    Two figures walk east, their backs to the PI -- the locals who
    walked out to flag down help and never came back. The PI can
    follow as far as they want; the figures stay ahead. Walking west
    returns to country_lane. The road never reaches anywhere."""
    W, H = 60, 9
    # Floor: a paved road through the middle, grass shoulders.
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if 3 <= ty <= 5:
                row.append("d")    # dirt-road tiles -- the highway
            else:
                row.append("g")
        floor_rows.append("".join(row))
    # Tree shoulders top and bottom. The road rows (3-5) stay OPEN at
    # the left and right columns so the east-west wrap actually
    # connects -- walking off the east edge of the road lands you on
    # the west edge of the road and you keep going. (If the edge
    # columns were solid here, wrap_x would be a no-op and the road
    # would just dead-end against an invisible wall.)
    objects_l = []
    for ty in range(H):
        row = []
        on_road = 3 <= ty <= 5
        for tx in range(W):
            if ty == 0 or ty == H - 1:
                row.append("T")
            elif (tx == 0 or tx == W - 1) and not on_road:
                row.append("T")     # tree shoulders pinch the grass
            else:
                row.append(".")
        objects_l.append(row)
    # Return barrier on the road, one tile IN from the west seam,
    # spanning all three road rows. It's direction-sensitive (fires
    # only when walked WEST), so heading back the way you came drops
    # you to country_lane -- but walking EAST and wrapping across the
    # seam runs straight over it (facing east, no trigger) and the
    # road keeps going forever. Inland of the seam so the wrap itself
    # never lands the player on the exit tile.
    for ry in (3, 4, 5):
        objects_l[ry][1] = "G"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("highway_walk", floor_rows, objects, music="outside")
    # The road wraps east-west. Walking east never gets anywhere.
    sc.wrap_x = True
    sc.wrap_y = False
    sc.add_exit("G", "country_lane", "from_highway_walk", direction="west")
    # Spawn a few tiles east of the G barrier, facing east (carried
    # from the eastward walk into the fold) so arrival doesn't instantly
    # bounce back out.
    sc.set_spawn("default", 4, 4)
    sc.set_spawn("from_country_lane", 4, 4)
    # ---- The two figures ----
    # Both walk east on the road, ahead of the player. Their facing
    # is east. Movement is a slow patrol on a long eastward stretch;
    # because the world wraps, they appear to walk forever. The
    # waypoint loops them along row 4 from col 30 -> 58 -> 30 (the
    # wrap eats the seam). They do not stop, do not turn.
    # They are not here to be met -- they're the locals who already walked
    # out and never arrived. Non-solid (you pass through them; they're
    # ahead of you, not blocking) and no_prompt (no [E] over them, or they
    # read as ordinary random NPCs you can talk to). The road just keeps
    # them ahead of you forever.
    walker_a = NPC(30 * TILE + 16, 4 * TILE + 16, "A figure on the road",
                   "old_townsman", movement="patrol", solid=False, no_prompt=True,
                   waypoints=[(30 * TILE + 16, 4 * TILE + 16),
                              (58 * TILE + 16, 4 * TILE + 16)])
    walker_a.facing = (1, 0)
    walker_a.lock_facing = True
    sc.add_npc(walker_a)
    walker_b = NPC(35 * TILE + 16, 4 * TILE + 16, "A figure on the road",
                   "old_townsman", movement="patrol", solid=False, no_prompt=True,
                   waypoints=[(35 * TILE + 16, 4 * TILE + 16),
                              (58 * TILE + 16, 4 * TILE + 16)])
    walker_b.facing = (1, 0)
    walker_b.lock_facing = True
    sc.add_npc(walker_b)
    # Dressing -- some grass tufts, a couple of distant crows, a
    # single dropped item on the shoulder.
    rng = random.Random(719)
    for _ in range(50):
        gx = rng.randint(2, W - 3) * TILE + rng.randint(2, 28)
        gy_choice = rng.choice([1, 2, 6, 7])
        gy = gy_choice * TILE + rng.randint(2, 28)
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(10 * TILE + 16, 2 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(48 * TILE + 16, 7 * TILE + 16, "crow"))
    # One dropped object -- a hat or a small bag -- on the shoulder
    # where someone began the walk.
    sc.add_decoration(Decoration(5 * TILE + 16, 5 * TILE + 16,
                                 "small_chair"))
    return sc


# ----- The Husk Grove -- where the corn-dolls are made --------------

def build_husk_grove():
    """A small clearing in the corn where the cult assembles the
    corn-dolls. Accessed by walking EAST off a specific tile in
    lane 5 of the cornfield maze. Workbenches with unfinished dolls,
    bundles of husks, twine wound on a stake. No NPC -- the work is
    here, the worker is somewhere else. Walking west off the west
    edge returns to the maze."""
    W, H = 12, 9
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            row.append("d" if 1 <= tx <= W - 2 and 1 <= ty <= H - 2 else "g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if ty == 0 or ty == H - 1 or tx == 0 or tx == W - 1:
                row.append("C")    # corn-wall perimeter
            else:
                row.append(".")
        objects_l.append(row)
    # Return tile on the west wall at row 4. Player walked east to
    # get in; walking west takes them back to the maze.
    objects_l[4][0] = "G"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("husk_grove", floor_rows, objects, music="outside")
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("G", "cornfield_maze", "from_husk_grove")
    sc.set_spawn("default", W - 2, 4)
    sc.set_spawn("from_cornfield_maze", W - 2, 4)
    # Two corn_altars used here as workbenches (visually they read
    # as ritual mounds) with unfinished dolls scattered around.
    sc.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 16, "corn_altar"))
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "corn_altar"))
    # Unfinished dolls in two rows near the altars.
    for dx, dy in [(3, 4), (5, 4), (6, 6), (8, 6),
                   (4, 6), (3, 2), (5, 2)]:
        sc.add_decoration(Decoration(dx * TILE + 16, dy * TILE + 16,
                                     "corn_doll"))
    # A stalk-marker stake -- the cult mark, the next to be tracked.
    sc.add_decoration(Decoration(9 * TILE + 16, 4 * TILE + 16,
                                 "stalk_marker"))
    # A single candle still lit -- someone was just here.
    sc.add_decoration(Decoration(7 * TILE + 16, 4 * TILE + 16, "candle"))
    # Phantom marks scattered.
    sc.add_decoration(Decoration(6 * TILE + 16, 3 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(8 * TILE + 16, 7 * TILE + 16,
                                 "phantom_mark"))
    sc.hide_spots = []
    return sc


# ----- The Scarecrow Ring -------------------------------------------

def build_scarecrow_ring():
    """A ring of scarecrows facing inward around a Yellow Sign
    carved into the dirt. Accessed by walking WEST off a specific
    tile in lane 1 of the cornfield maze. Six scarecrows in a tight
    ring; one of them is wearing clothes the player has seen on a
    local. The Sign at the centre is bigger here than anywhere
    above-ground. Walking east off the east edge returns to the
    maze."""
    W, H = 12, 10
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            # Charred dirt inside the ring, regular dirt outside.
            if 3 <= tx <= 8 and 3 <= ty <= 7:
                row.append("x")
            elif 1 <= tx <= W - 2 and 1 <= ty <= H - 2:
                row.append("d")
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if ty == 0 or ty == H - 1 or tx == 0 or tx == W - 1:
                row.append("C")
            else:
                row.append(".")
        objects_l.append(row)
    # Return tile on the east wall at row 5.
    objects_l[5][W - 1] = "G"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("scarecrow_ring", floor_rows, objects, music="outside")
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("G", "cornfield_maze", "from_scarecrow_ring")
    sc.set_spawn("default", 1, 5)
    sc.set_spawn("from_cornfield_maze", 1, 5)
    # The Sign at the centre -- much bigger / more obvious than the
    # versions in the curse circles. The cult is centred here.
    sc.add_decoration(Decoration(5 * TILE + 16, 5 * TILE + 16,
                                 "yellow_sign"))
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 16,
                                 "yellow_sign"))
    # Six scarecrows in a ring around the Sign, facing inward.
    # Implemented as hanging_figure decorations (the closest
    # available sprite to a scarecrow on a post).
    ring = [(3, 3), (6, 3), (8, 4), (8, 6), (5, 7), (3, 6)]
    for tx, ty in ring:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "hanging_figure"))
    # Two braziers flanking the Sign, lit.
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 16, "brazier"))
    # Bloodstains under the central Sign.
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(6 * TILE + 16, 4 * TILE + 16, "bloodstain"))
    # Watching wounds at the corners.
    sc.add_decoration(Decoration(0 * TILE + 16, 1 * TILE + 16,
                                 "watching_wound", size="small"))
    sc.add_decoration(Decoration(W * TILE - 16, H * TILE - 16,
                                 "watching_wound", size="small"))
    sc.hide_spots = []
    return sc
