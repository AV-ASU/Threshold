"""Scene registry. Each scene_key -> builder function.

THRESHOLD: registry trimmed from ~32 scenes down to the 23-scene
1994-Yellow-King-cult fiction map. Builder functions for cut scenes
are still imported (so static analysis stays clean) but they are
not registered — nothing in the new world reaches them. Reskinned
scenes keep the same key when the geometry is reused, so old saves
that store a scene key load into the new content for that key.
"""
from .base import Scene, tile_footstep, OBJECT_DEFS, FLOOR_DEFS, TILE
from .house import (build_bedroom, build_house, build_basement,
                    build_abducted_hallway, build_son_room)
from .our_house_area import build_our_house_area, build_woodshed
from .village import build_village
from .forest_path import build_forest_path
from .well import build_well_bottom, build_well_passage
from .depths import (build_depths_antechamber, build_depths_procession,
                     build_depths_hall, build_depths_threshing,
                     build_depths_stair, build_dark, build_threshold)
from .interiors import (
    build_void, build_bandit_cave, build_shop,
    build_easter_egg_room, build_kid_house, build_barn,
    build_bandit_cave_west, build_bandit_cave_east, build_bandit_cave_boss,
    build_void_boss,
)
from .villager_houses import (
    build_old_man_house, build_fisherman_cottage,
    build_haunted_house, build_haunted_house_glitch,
    build_symbol_portal_room, build_locked_house,
    build_daughter_room,
)
from .mistlands import (build_mistlands, build_mist_house,
                        build_alter_room,
                        build_void_room_1, build_void_room_2)
from .threshold_extras import (build_schoolhouse, build_graveyard,
                                build_diner_gas_station,
                                build_country_lane,
                                build_gravel_road_north,
                                build_backwoods_cabin,
                                build_backwoods_cabin_interior,
                                build_river_crossing,
                                build_bell_tower,
                                build_cornfield_maze,
                                build_town)


# THRESHOLD scene registry. Keys map to the new fiction:
#   bedroom            -> spare_room (player's cot in Innkeeper's house)
#   house              -> innkeeper_house (kitchen + living + hallway)
#   son_room           -> innkeeper_bedroom (locked; keys, orb, robe)
#   basement           -> innkeeper_basement (Mom's photo, notebook,
#                                             charcoal, flashlight,
#                                             bulkhead exit)
#   our_house_area     -> outside_innkeeper_house (yard, pickup, shed)
#   kid_house          -> kid_house (drawings on walls)
#   village            -> town_crossroads (well + payphone)
#   shop               -> general_store
#   old_man_house      -> church (with belfry; Preacher)
#   fisherman_cottage  -> sheriffs_office (Sheriff's wooden box)
#   forest_path        -> cornfield_path (cornstalk hides)
#   void_boss          -> clearing (the cauldron site)
#   barn               -> barn (hide spots, tunnel)
#   well_bottom        -> well_bottom (sigil etched at the binding)
#   well_passage       -> well_passage (cult tunnels)
#   haunted_house      -> abandoned_farmhouse
#   symbol_portal_room -> cult_chamber (altar room)
#   mistlands          -> river_path (creek north of town)
#   schoolhouse        -> NEW: empty since the kid's family vanished
#   graveyard          -> NEW: behind the church
#   diner_gas_station  -> NEW: edge of town; player's car parked here
SCENE_BUILDERS = {
    # Player's quarters (the Innkeeper's house, above the inn)
    "bedroom":            build_bedroom,            # -> spare_room
    "house":              build_house,              # -> innkeeper_house
    "son_room":           build_son_room,           # -> innkeeper_bedroom
    "basement":           build_basement,           # -> innkeeper_basement
    "our_house_area":     build_our_house_area,     # -> yard
    "woodshed":           build_woodshed,           # -> Innkeeper's shed interior
    # Next door
    "kid_house":          build_kid_house,
    # Town crossroads
    "village":            build_village,            # -> town_crossroads
    "shop":               build_shop,               # -> general_store
    "old_man_house":      build_old_man_house,      # -> church
    "fisherman_cottage":  build_fisherman_cottage,  # -> sheriffs_office
    # Outlying / paths
    "forest_path":        build_forest_path,        # -> cornfield_path
    "void_boss":          build_void_boss,          # -> clearing
    "barn":               build_barn,
    # The well & lower chambers
    "well_bottom":        build_well_bottom,
    "well_passage":       build_well_passage,
    # The depths -- five rooms, one-way fall from well_bottom
    "depths_antechamber": build_depths_antechamber,
    "depths_procession":  build_depths_procession,
    "depths_hall":        build_depths_hall,
    "depths_threshing":   build_depths_threshing,
    "depths_stair":       build_depths_stair,
    "dark":               build_dark,
    "threshold":          build_threshold,
    # Cult sites
    "haunted_house":       build_haunted_house,     # -> abandoned_farmhouse
    "symbol_portal_room":  build_symbol_portal_room, # -> cult_chamber
    # River escape
    "mistlands":          build_mistlands,          # -> river_path
    # New scenes
    "schoolhouse":        build_schoolhouse,
    "graveyard":          build_graveyard,
    "diner_gas_station":  build_diner_gas_station,
    "country_lane":       build_country_lane,
    "gravel_road_north":  build_gravel_road_north,
    "backwoods_cabin":    build_backwoods_cabin,
    "backwoods_cabin_interior": build_backwoods_cabin_interior,
    "river_crossing":     build_river_crossing,
    "bell_tower":         build_bell_tower,
    "cornfield_maze":     build_cornfield_maze,
    # The populated town hub -- store, sheriff, school open onto it.
    "town":               build_town,
}

# CUT from registry (builders preserved for import safety only):
#   void, bandit_cave, bandit_cave_west, bandit_cave_east,
#   bandit_cave_boss, easter_egg_room, daughter_room,
#   abducted_hallway, haunted_house_glitch, locked_house,
#   mist_house, alter_room, void_room_1, void_room_2,
#   underwater_room


def load_scene(key):
    if key not in SCENE_BUILDERS:
        # Fallback: any save state pointing to a cut scene routes to
        # the spare_room. The player wakes there if the world has
        # forgotten where they were. (Cut keys: void, bandit_cave*,
        # easter_egg_room, daughter_room, abducted_hallway,
        # haunted_house_glitch, locked_house, mist_house, alter_room,
        # void_room_1, void_room_2.)
        key = "bedroom"
    return SCENE_BUILDERS[key]()


__all__ = [
    "Scene", "OBJECT_DEFS", "FLOOR_DEFS", "TILE",
    "SCENE_BUILDERS", "load_scene", "tile_footstep",
]
