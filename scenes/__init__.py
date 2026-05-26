"""Scene registry. Each scene_key -> builder function.

Registry trimmed from ~32 scenes down to the active map. Builder
functions for cut scenes are still imported (so static analysis
stays clean) but they are not registered — nothing in the world
reaches them. Reused scenes keep the same key when the geometry is
reused, so old saves that store a scene key load into the content
for that key.
"""
from .base import Scene, tile_footstep, OBJECT_DEFS, FLOOR_DEFS, TILE
from .house import (build_bedroom, build_house, build_basement,
                    build_abducted_hallway, build_son_room)
from .our_house_area import build_our_house_area, build_woodshed
from .village import build_village
from .forest_path import build_forest_path
from .well import (build_well_bottom, build_well_passage,
                   build_works_vats, build_works_sorting,
                   build_works_scriptorium, build_works_sign,
                   build_works_deepstair, build_maras_room)
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
#   bedroom            -> the player's room at the Arcadia (the cot)
#   house              -> the Arcadia ground floor (Clerk's desk + floor)
#   son_room           -> the Clerk's room (locked; flavor: his cult robe)
#   basement           -> the Arcadia cellar (the Ledger #3; the workbench)
#   our_house_area     -> the Arcadia yard (the dead car, the woodshed)
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
    # The Arcadia Lodge (your room, the ground floor, the Clerk's room)
    "bedroom":            build_bedroom,            # the player's room
    "house":              build_house,              # the ground floor
    "son_room":           build_son_room,           # the Clerk's room
    "basement":           build_basement,           # -> innkeeper_basement
    "our_house_area":     build_our_house_area,     # -> yard
    "woodshed":           build_woodshed,           # -> Clerk's shed interior
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
    # The Works -- the Basement Level. Seven rooms, well is the sole
    # entrance (rope down); the playscript gates the way deeper to the Depths.
    "well_bottom":        build_well_bottom,        # the Shaft Floor
    "well_passage":       build_well_passage,       # the Drying Racks
    "works_vats":         build_works_vats,
    "works_sorting":      build_works_sorting,
    "maras_room":         build_maras_room,         # cell off the Sorting Hall
    "works_scriptorium":  build_works_scriptorium,
    "works_sign":         build_works_sign,         # the Sign (evidence #5)
    "works_deepstair":    build_works_deepstair,    # playscript-gate -> Depths
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
