# HANDCRAFT BACKLOG — sprites/art that don't fit the 3D tilt yet

> The oblique tilt camera is the default. Under it, things should render as
> **volumetric solids** (`rendering/furniture.py`, `rendering/props.py`),
> **stood-up billboards/standees** (`props.py` `_STANDEE_KINDS`, `scenes/base.py`
> `_tilt_standee`), **wall-hung cards** (`_WALL_DECO_KINDS`), or **flat decals
> warped onto the floor/surface plane** (`_FLOOR_DECAL_KINDS` /
> `_SURFACE_DECAL_KINDS`). Anything still drawn **flat top-down** reads as a
> *stain on the floor* under tilt.
>
> **STATUS (2026-06 audit): the original backlog is almost entirely BUILT.**
> A per-kind audit against the live kind-sets found nearly every item already
> handled; the stragglers were finished in the same pass. The mechanism map
> below is kept for the next new decoration kind.

## Audit result (how each original item renders today)

- **FURNITURE box volumes** (`furniture.py`): table, chair, bed, bookshelf,
  shelf, wardrobe, stove, fireplace, counter, firewood, crate, barrel, cot,
  bone_rack, pew, **chest, small_chair, overturned_chair, terminal, computer,
  gas_pump, payphone, headstone**.
- **SOLID_PROPS / live solids** (`props.py`): well, pillar, cistern_basin,
  grain_heap, doorframe, waterfall, shaft_ladder, cellar_hatch, town_sign,
  flagpole, **player_car, pickup_truck**, stalagmite, candle, kerosene_lamp,
  lantern, brazier, wall_torch, rope, stalk_marker, smoke, wisp, mote, flock,
  **crow** (live, so its hop + looking-backwards anomaly survive).
- **Standees** (grounded elevation cards): creepy_tree, corn_doll, corn_altar,
  wheelbarrow, pedestal, **steeple**, tall_grass, grass_tuft, doll,
  husk_bundle, hanging_figure (hung).
- **Wall-hung cards** (`_WALL_DECO_KINDS`): **mirror, photo, wrong_photo,
  missing_flyer, polaroid_wall, banner, calendar, clock, apology_wall,
  buck_head, antler_rack, mounted_fish, wrong_taxidermy**, chalk_door_wall,
  chalkboard, cobweb, passing_silhouette.
- **Floor/surface decals** (intentionally flat, warped onto the plane): rug,
  bloodstain, gore, yellow_sign, bloody_handprint, bloody_pile, symbol,
  binding_sigil, swallow_hole, body, drowned_body, bush, dead_crow,
  mud_footprint, claw_marks, mist, leaves, ledger, **place_setting**.
- **Tabletop-seated** (`_TABLETOP_PROP_KINDS` + `seat_tabletop_props`): radio,
  **wrong_radio**, bowl, cup, plate, papers, book, photo, lamps...

## Closed in the 2026-06 pass

1. **Pickup ground shadows** — scene items already had a tilt shadow in
   `_draw_item`; the `item_drop` *decoration* now draws its own contact
   shadow too (`entities/decoration.py`).
2. **crow** — was the last truly flat ambient kind; now a LIVE solid prop
   (`props.py _draw_crow_solid`): grounded with a contact shadow, legs, body
   and head projected at real heights, animation (hop / head-turn / the rare
   looking-backwards beat) intact. Flat pitch-0 art unchanged.
3. **place_setting** — now a surface decal: warps flat onto the table top
   (seated to the surface z) instead of standing up as a sticker.
4. **wrong_radio** — seated like the plain radio; the shop builder also puts
   a low goods shelf under it so it sits ON something.
5. **Surface-decal depth fix** — seated props now depth-sort at their host
   tile's SOUTH edge, so a plate near a tile's north edge can't sort behind
   its own table (the table top used to paint over it).
6. **crate / barrel / counter flat fallbacks** — these FURNITURE kinds had no
   `_draw_<kind>` and rendered as the magenta `_draw_unknown` square in the
   pitch-0/F3 view (house, basement, well_bottom, well_passage, works_sorting,
   the_sump). Proper top-down art added.
7. **The river tile** — the backlog's "organic dark depth patches drifting
   mid-channel" already shipped (`scenes/base.py` `draw_floor` `'~'`), along
   with bank fringes, algae, and cold glints. Confirmed in-game; nothing left.

## Genuinely open

- **3b. Player / weapons** — `draw_axe_held` now exists (the equipped weapon
  always reads); the remaining note is an eyeball pass on the held-weapon
  offset at every camera yaw.

## Closed in the 2026-07 pass

- **`drowned_body` — CUT (design call settled 2026-07).** The keep-or-cut
  question was decided: cut. The `well_bottom` placement, the
  `_draw_drowned_body` draw fn (`entities/decoration.py`), and the
  `_FLOOR_DECAL_KINDS` entry are removed; the seep pool and claw gouges
  carry the room's dread.
- **4. Flat-feeling detail** — the last straggler is done: `counter` now has
  a `_d_counter` near-face detail (butcher-block seams, worn lip, knife
  scores, an old stain) wired into the FURNITURE spec. The
  `fireplace`/`stove` firebox, `bed` blanket, and `shelf` layout details
  already existed.

> Mechanism reminder when adding a new kind: add it to `FURNITURE`/`SOLID_PROPS`
> for a real volume, `_STANDEE_KINDS` for a flat-card-stood-up,
> `_WALL_DECO_KINDS` to hang it, `_FLOOR_DECAL_KINDS`/`_SURFACE_DECAL_KINDS` to
> lie it flat, or `_TABLETOP_PROP_KINDS` to seat it on furniture. Animated
> kinds that must stay animated need a LIVE solid fn (standee cards freeze at
> t=0). Verify with a tilt capture before/after.
