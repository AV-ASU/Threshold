"""Scene registry. Each scene_key -> builder function.

Registry trimmed from ~32 scenes down to the active map. Builder
functions for cut scenes are still imported (so static analysis
stays clean) but they are not registered — nothing in the world
reaches them. Reused scenes keep the same key when the geometry is
reused, so old saves that store a scene key load into the content
for that key.
"""
from .base import Scene, tile_footstep, OBJECT_DEFS, FLOOR_DEFS, TILE
from .lodge import (build_bedroom, build_lodge, build_lodge_cellar,
                    build_clerk_room)
from .lodge_yard import (build_lodge_yard, build_woodshed,
                         build_arrival_road)
from .cornfield_path import build_cornfield_path
from .well import (build_well_bottom, build_well_passage,
                   build_works_vats, build_works_sorting,
                   build_works_scriptorium, build_works_sign,
                   build_works_deepstair, build_maras_room,
                   build_the_sump, build_the_cells)
from .depths import (build_depths_antechamber, build_depths_procession,
                     build_depths_hall, build_depths_threshing,
                     build_depths_stair, build_dark, build_threshold,
                     build_the_ossuary)
from .interiors import (build_shop, build_toby_house, build_barn,
                        build_clearing)
from .villager_houses import (build_church, build_sheriff_office,
                              build_abandoned_farmhouse)
from .brimley import build_brimley
from .hidden_folds import (build_effigy_grove, build_lodge_arrival,
                            build_husk_grove, build_scarecrow_ring)
from .threshold_extras import (build_schoolhouse, build_graveyard,
                                build_country_lane,
                                build_gravel_road_north,
                                build_backwoods_cabin,
                                build_backwoods_cabin_interior,
                                build_river_crossing,
                                build_bell_tower,
                                build_cornfield_maze)


# THRESHOLD scene registry. Keys name the CURRENT fiction. A 2026-07 pass
# retired the old reused-geometry key names; the mapping (OLD -> new) was:
#   house -> lodge, son_room -> clerk_room, basement -> lodge_cellar,
#   our_house_area -> lodge_yard, kid_house -> toby_house,
#   old_man_house -> church, fisherman_cottage -> sheriff_office,
#   forest_path -> cornfield_path, void_boss -> clearing,
#   haunted_house -> abandoned_farmhouse.
#   bedroom            -> the player's room at the Arcadia (the cot)
#   lodge              -> the Arcadia ground floor (Clerk's desk + floor)
#   clerk_room         -> the Clerk's room (locked; flavor: his cult robe)
#   lodge_cellar       -> the Arcadia cellar (the Ledger #3; the workbench)
#   lodge_yard         -> the Arcadia yard (the woodshed; the dead car is on arrival_road)
#   toby_house         -> Toby's house (drawings on walls)
#   brimley            -> the unified town map (was mistlands + village)
#   shop               -> general_store
#   church             -> church (with belfry; Preacher)
#   sheriff_office     -> the Sheriff's office (his wooden box; reused fisherman_cottage geometry)
#   cornfield_path     -> the dirt road east of the yard (cornstalk hides)
#   clearing           -> the burn site
#   barn               -> barn (hide spots, tunnel)
#   well_bottom        -> well_bottom (sigil etched at the binding)
#   well_passage       -> well_passage (cult tunnels)
#   abandoned_farmhouse-> the abandoned farmhouse (cult site)
#   schoolhouse        -> NEW: empty since the town's children vanished
#   graveyard          -> NEW: behind the church
SCENE_BUILDERS = {
    # The Arcadia Lodge (your room, the ground floor, the Clerk's room)
    "bedroom":            build_bedroom,            # the player's room
    "lodge":              build_lodge,              # the ground floor
    "clerk_room":         build_clerk_room,         # the Clerk's room
    "lodge_cellar":       build_lodge_cellar,       # the Arcadia cellar
    "lodge_yard":         build_lodge_yard,         # the yard (dead car removed -> arrival_road)
    "arrival_road":       build_arrival_road,       # -> the looping road W of the lodge (the SPREAD car)
    "woodshed":           build_woodshed,           # -> Clerk's shed interior
    # Next door
    "toby_house":         build_toby_house,         # Toby's house
    "shop":               build_shop,               # -> general_store
    "church":             build_church,             # -> church (Preacher)
    "sheriff_office":     build_sheriff_office,     # -> the Sheriff's office
    # Outlying / paths
    "cornfield_path":     build_cornfield_path,     # the dirt road east of the yard
    "clearing":           build_clearing,           # the burn site
    "barn":               build_barn,
    # The Works -- the Basement Level. Seven rooms, well is the sole
    # entrance (the grove's descent fold); the Mask gates the way to the Depths.
    "well_bottom":        build_well_bottom,        # the Shaft Floor
    "well_passage":       build_well_passage,       # the Drying Racks
    "works_vats":         build_works_vats,
    "works_sorting":      build_works_sorting,
    "maras_room":         build_maras_room,         # cell off the Sorting Hall
    "the_sump":           build_the_sump,           # branch off the Cistern
    "the_cells":          build_the_cells,          # branch off the Sorting Hall
    "works_scriptorium":  build_works_scriptorium,
    "works_sign":         build_works_sign,         # the Sign (evidence #5)
    "works_deepstair":    build_works_deepstair,    # keystone gate -> Depths
    # The depths -- five rooms, one-way fall from well_bottom
    "depths_antechamber": build_depths_antechamber,
    "depths_procession":  build_depths_procession,
    "the_ossuary":        build_the_ossuary,        # branch off the procession
    "depths_hall":        build_depths_hall,
    "depths_threshing":   build_depths_threshing,
    "depths_stair":       build_depths_stair,
    "dark":               build_dark,
    "threshold":          build_threshold,
    # Cult sites
    "abandoned_farmhouse": build_abandoned_farmhouse,  # the abandoned farmhouse
    # The town
    "brimley":            build_brimley,            # the unified town map
    # New scenes
    "schoolhouse":        build_schoolhouse,
    "graveyard":          build_graveyard,
    "country_lane":       build_country_lane,
    "gravel_road_north":  build_gravel_road_north,
    "backwoods_cabin":    build_backwoods_cabin,
    "backwoods_cabin_interior": build_backwoods_cabin_interior,
    "river_crossing":     build_river_crossing,
    "bell_tower":         build_bell_tower,
    "cornfield_maze":     build_cornfield_maze,
    # Hidden fold scenes (direction-sensitive warps off the main world).
    "effigy_grove":        build_effigy_grove,
    "lodge_arrival":      build_lodge_arrival,
    "husk_grove":         build_husk_grove,
    "scarecrow_ring":     build_scarecrow_ring,
}

# DELETED (the prior combat/loot game -- removed wholesale, not just
# unregistered): void, the cave arenas (_west/_east/_boss), easter_egg_room,
# daughter_room, abducted_hallway, haunted_house_glitch, locked_house,
# mist_house, alter_room, void_room_1/2. Also cut (2026-07 dead-scene pass):
# highway_walk (the never-hit walked-out-road fold off country_lane) and the
# legacy "town" orphan stub (no live inbound exit). Any stale save or exit
# pointing at one of these keys falls back to "bedroom" via load_scene below.


def load_scene(key):
    if key not in SCENE_BUILDERS:
        # Any save or exit pointing at a deleted scene falls back to the
        # player's room rather than crashing.
        key = "bedroom"
    sc = SCENE_BUILDERS[key]()
    # Seat candles/lamps/bowls/etc. ON the furniture they're placed on, so they
    # don't float at the furniture's base under the tilt.
    sc.seat_tabletop_props()
    return sc


__all__ = [
    "Scene", "OBJECT_DEFS", "FLOOR_DEFS", "TILE",
    "SCENE_BUILDERS", "load_scene", "tile_footstep",
]
