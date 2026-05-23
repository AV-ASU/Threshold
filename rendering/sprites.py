"""Character sprites: NPCs, enemies, the player."""
import math
import random
import pygame
from constants import C_BLACK

def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False):
    """`blink=True` suppresses eye dots for NPC kinds that have human
    eyes (mom/kid/bandit/policeman). Used by Game.draw to make a single
    NPC's eyes vanish for a single frame -- a subliminal wrongness.
    `gaze=True` lights the watcher's eyes (sees the player). Watchers
    only.
    while the player stands still."""
    if kind == "_invisible":
        return
    if kind == "mom":
        # red dress (desaturated, slightly dirtied), dark bun, apron with
        # a faint smudge along the hem so she doesn't read as a fairytale
        # housewife. Eyes sit in shallow hollows so she always looks a
        # little exhausted; on `blink` the dots become 2x2 voids rather
        # than disappearing -- a frame where her face is wrong.
        pygame.draw.rect(surf, (150, 56, 70), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 188), (x - 6, y + 2, 12, 14))  # apron
        pygame.draw.rect(surf, (130, 96, 90), (x - 6, y + 14, 12, 2))    # apron hem stain
        pygame.draw.circle(surf, (228, 198, 168), (x, y - 12), 7)
        pygame.draw.circle(surf, (50, 32, 24), (x - 6, y - 18), 4)  # hair
        pygame.draw.circle(surf, (50, 32, 24), (x + 6, y - 18), 4)
        # Sunken eye hollows (skin-shadow band under the brow)
        pygame.draw.line(surf, (170, 130, 110), (x - 4, y - 11), (x - 1, y - 11), 1)
        pygame.draw.line(surf, (170, 130, 110), (x + 1, y - 11), (x + 4, y - 11), 1)
        if blink:
            # Void frame: oversized black holes where the eyes were.
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
            # Tiny wet glint above each pupil
            try:
                surf.set_at((x - 3, y - 13), (240, 240, 250))
                surf.set_at((x + 1, y - 13), (240, 240, 250))
            except (IndexError, ValueError):
                pass
    elif kind == "old":
        # Brown coat, hat, beard, cane. The face slot under the hat brim
        # is darkened into a shadow band so two faint pinprick eyes glint
        # from inside the shadow rather than reading as plain face. Beard
        # is now off-white / ash-yellow so he reads as kept-too-long.
        pygame.draw.rect(surf, (78, 60, 42), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (200, 196, 180), (x - 7, y - 5, 14, 6))  # beard (yellowed)
        pygame.draw.rect(surf, (30, 20, 12), (x - 9, y - 22, 18, 4))   # hat brim
        pygame.draw.rect(surf, (30, 20, 12), (x - 6, y - 28, 12, 7))   # crown
        # Hat-brim shadow band across the eyes
        pygame.draw.rect(surf, (60, 40, 30), (x - 6, y - 14, 12, 3))
        # Pinprick eyes inside the shadow
        if not blink:
            pygame.draw.circle(surf, (210, 200, 160), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (210, 200, 160), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (90, 60, 30), (x + 10, y - 4), (x + 10, y + 14), 2)  # cane
    elif kind == "shopkeep":
        # Blue apron, bald top, glasses. Lenses are now FILLED black
        # instead of outlined -- you can't see his eyes through them, the
        # two black rectangles ARE the eye-read. Subtle and uncanny: every
        # time he turns toward you, you fail to find his gaze.
        pygame.draw.rect(surf, (54, 70, 104), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 190), (x - 6, y, 12, 16))  # apron
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.arc(surf, (40, 28, 22), (x - 8, y - 18, 16, 8), 0, math.pi, 1)  # hair ring
        # Glasses frames + filled black lenses (no eyes visible)
        pygame.draw.rect(surf, (10, 10, 14), (x - 4, y - 13, 3, 2))     # glasses L lens
        pygame.draw.rect(surf, (10, 10, 14), (x + 1, y - 13, 3, 2))     # glasses R lens
        pygame.draw.line(surf, (40, 40, 50), (x - 1, y - 12), (x + 1, y - 12), 1)  # bridge
        # A faint reflection-line on each lens so they read as glass,
        # not eyeholes -- but the reflection is on the WRONG side of
        # each lens (both reflect from the right), which is impossible
        # if the light source is overhead and singular.
        try:
            surf.set_at((x - 2, y - 13), (140, 150, 160))
            surf.set_at((x + 3, y - 13), (140, 150, 160))
        except (IndexError, ValueError):
            pass
    elif kind == "kid":
        # Desaturated yellow tunic; the original bright primary made the
        # kid read as cheerful, which fights the "trailing creep" use.
        # Hair hangs lower over the brow; the cheek dots used to be
        # freckles, now they sit slightly low and asymmetric so they
        # read as old tear-streaks when you look twice.
        pygame.draw.rect(surf, (172, 156, 70), (x - 7, y, 14, 14))
        pygame.draw.circle(surf, (228, 196, 168), (x, y - 8), 6)
        pygame.draw.rect(surf, (80, 50, 30), (x - 7, y - 13, 14, 5))
        # Long fringe -- a fringe-band lower over the eyes than the hair
        # cap, so the kid always looks like he's peering up through it.
        pygame.draw.rect(surf, (80, 50, 30), (x - 6, y - 9, 12, 2))
        # Sunken eye hollows
        pygame.draw.line(surf, (170, 130, 100), (x - 4, y - 7), (x - 1, y - 7), 1)
        pygame.draw.line(surf, (170, 130, 100), (x + 1, y - 7), (x + 4, y - 7), 1)
        if blink:
            # Void blink: oversized 3x2 black holes that overflow the
            # eye area -- bigger than the head ought to allow.
            pygame.draw.rect(surf, (2, 0, 4), (x - 4, y - 9, 3, 3))
            pygame.draw.rect(surf, (2, 0, 4), (x + 1, y - 9, 3, 3))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 8), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 8), 1)
            try:
                surf.set_at((x - 3, y - 9), (240, 240, 250))
                surf.set_at((x + 1, y - 9), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Cheek marks -- low and asymmetric so the eye reads them as
        # old tear tracks before settling on "freckles".
        pygame.draw.circle(surf, (150, 90, 80), (x - 4, y - 5), 1)
        pygame.draw.circle(surf, (140, 84, 76), (x + 5, y - 4), 1)
    elif kind == "bandit":
        # THRESHOLD: re-skinned as a hooded cultist. Coarse undyed-
        # wool robe (dirty cream) over a dark inner shirt; deep hood
        # casts a shadow across the eyes; faint ash on the hem from
        # the cauldron fire. Used by the patrol_cultist NPCs that
        # appear at higher Pursuer proximity.
        robe       = (170, 156, 130)     # undyed wool
        robe_dark  = (110, 100, 84)      # shadow seam
        inner      = (40, 36, 40)        # shirt under the robe
        skin_dim   = (180, 156, 130)     # face in hood-shadow
        ash        = (60, 54, 50)        # scorched hem
        # Body / robe
        pygame.draw.rect(surf, robe, (x - 9, y - 4, 18, 20))
        pygame.draw.rect(surf, robe_dark, (x - 9, y - 4, 18, 20), 1)
        # Vertical seam
        pygame.draw.line(surf, robe_dark, (x, y - 4), (x, y + 14), 1)
        # Inner shirt peek at the collar
        pygame.draw.rect(surf, inner, (x - 4, y - 4, 8, 3))
        # Head (in hood shadow)
        pygame.draw.circle(surf, skin_dim, (x, y - 12), 7)
        # Hood drape over the head and shoulders
        pygame.draw.rect(surf, robe, (x - 10, y - 22, 20, 10))
        pygame.draw.rect(surf, robe_dark, (x - 10, y - 22, 20, 10), 1)
        # Hood shadow across the eyes -- pure-black band, slightly
        # deeper than skin. The shadow now extends a row lower so it
        # darkens the cheekbones too, killing any "person" read.
        pygame.draw.rect(surf, (4, 2, 6), (x - 7, y - 14, 14, 5))
        if blink:
            # Void blink: yellow pinpricks vanish and a faint pale jaw
            # shape ghosts through the shadow -- the suggestion of teeth
            # / skull where a face ought to be. The mouth-row sits below
            # the shadow band, never visible at rest.
            pygame.draw.line(surf, (180, 168, 152), (x - 4, y - 9), (x + 4, y - 9), 1)
            pygame.draw.line(surf, (140, 128, 112), (x - 3, y - 8), (x + 3, y - 8), 1)
            # Two faint nose-cavity pricks in the shadow band
            pygame.draw.rect(surf, (12, 10, 14), (x - 1, y - 11, 1, 1))
            pygame.draw.rect(surf, (12, 10, 14), (x + 1, y - 11, 1, 1))
        else:
            # Eyes -- two faint pinpricks in the hood shadow
            pygame.draw.circle(surf, (200, 180, 60), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (200, 180, 60), (x + 2, y - 12), 1)
        # Scorched hem
        pygame.draw.rect(surf, ash, (x - 9, y + 14, 18, 2))
    elif kind == "policeman":
        # Navy uniform, peaked cap, gold badge. Cap-brim shadow falls
        # across the upper face so the eyes sit in a permanent dark
        # band; sunken hollows beneath. On `blink` the eyes become
        # 2x2 voids -- the cop's face goes wrong for a frame.
        pygame.draw.rect(surf, (32, 50, 100), (x - 9, y - 4, 18, 18))   # blue body
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (22, 30, 70), (x - 9, y - 22, 18, 6))    # cap brim
        pygame.draw.rect(surf, (22, 30, 70), (x - 7, y - 28, 14, 7))    # cap crown
        pygame.draw.rect(surf, (140, 50, 50), (x - 7, y - 7, 14, 4))    # collar/tie
        # Cap-brim shadow band across the upper face
        pygame.draw.rect(surf, (50, 40, 50), (x - 6, y - 15, 12, 2))
        # Sunken hollows
        pygame.draw.line(surf, (160, 130, 110), (x - 4, y - 12), (x - 1, y - 12), 1)
        pygame.draw.line(surf, (160, 130, 110), (x + 1, y - 12), (x + 4, y - 12), 1)
        if blink:
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 14, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 14, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 13), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 13), 1)
            try:
                surf.set_at((x - 3, y - 14), (240, 240, 250))
                surf.set_at((x + 1, y - 14), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Gold badge on the chest
        pygame.draw.rect(surf, (220, 200, 80), (x - 1, y, 3, 3))
        pygame.draw.rect(surf, C_BLACK, (x - 1, y, 3, 3), 1)
        # Black belt
        pygame.draw.rect(surf, (10, 10, 18), (x - 9, y + 6, 18, 2))
    elif kind == "fisherman":
        # Mustard coat, weathered hat. Hat brim shadows the eyes; an
        # extra small dark line runs across the upper face so the eye
        # area reads as deeply shadowed even in bright scenes. Beard
        # has a damp green-grey cast (algae / pond-water).
        pygame.draw.rect(surf, (140, 112, 76), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (180, 162, 64), (x - 10, y - 22, 20, 4))  # hat brim
        pygame.draw.rect(surf, (180, 162, 64), (x - 7, y - 28, 14, 7))   # crown
        pygame.draw.rect(surf, (160, 170, 150), (x - 6, y - 5, 12, 8))   # beard (damp/mossy)
        # Hat-brim shadow band
        pygame.draw.rect(surf, (50, 40, 28), (x - 6, y - 14, 12, 3))
        if not blink:
            pygame.draw.circle(surf, (200, 200, 220), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (200, 200, 220), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (80, 60, 40), (x - 10, y), (x - 14, y - 10), 2)  # rod
    elif kind == "guard":
        # Iron helmet + spear. The visor slit is now a deeper, pitch-
        # black void with two faint red glints inside -- you don't see
        # eyes, you see something looking out from inside the helm.
        pygame.draw.rect(surf, (96, 96, 116), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (130, 130, 150), (x - 9, y - 22, 18, 12))  # helmet
        # Visor slit -- pitch black with two pinprick reds
        pygame.draw.rect(surf, (4, 2, 4), (x - 4, y - 14, 8, 4))
        if not blink:
            pygame.draw.circle(surf, (180, 30, 30), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (180, 30, 30), (x + 2, y - 12), 1)
        pygame.draw.line(surf, (60, 40, 25), (x + 12, y - 18), (x + 12, y + 16), 2)
        pygame.draw.polygon(surf, (200, 200, 220),
                            [(x + 12, y - 18), (x + 9, y - 22), (x + 15, y - 22)])
    elif kind == "shadow":
        pygame.draw.rect(surf, (8, 4, 12), (x - 8, y - 4, 16, 18))
        pygame.draw.circle(surf, (8, 4, 12), (x, y - 10), 8)
        pygame.draw.circle(surf, (220, 30, 30), (x - 3, y - 11), 1)
        pygame.draw.circle(surf, (220, 30, 30), (x + 3, y - 11), 1)
    elif kind == "tall_shadow":
        # Tall, THIN smear of darkness. ~2.5x a normal NPC vertically, but
        # narrow enough that it reads as not-quite-human. Used for the
        # runaway forest enemy. In lore the figure is a Visitor (alien),
        # which is why the eyes are three blue dots stacked vertically --
        # not a face we recognise.
        # The silhouette now BREATHES on a slow sine: top of the body
        # drifts left/right by a pixel, and the seam wavers. Adds a
        # subliminal "this isn't standing still" cue without changing
        # the silhouette enough to mistake for movement.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        sway = math.sin(t * 0.9) * 1
        body_rect = pygame.Rect(x - 8 + int(sway), y - 50, 16, 64)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-4, -6))
        # Wavering vertical seam
        for sy_step in range(0, 60, 4):
            seam_x = x + int(math.sin(t * 1.3 + sy_step * 0.2) * 1)
            pygame.draw.line(surf, (2, 0, 4),
                             (seam_x, y - 48 + sy_step),
                             (seam_x, y - 48 + sy_step + 4), 1)
        # Three vertical eye dots. One of the three flickers off on a
        # staggered cycle so the row is rarely all lit at the same time
        # -- the eyes never quite "match" each other.
        flicker = int(t * 2.4) % 7
        if flicker != 0:
            pygame.draw.circle(surf, (60, 130, 220), (x, y - 42), 1)
        if flicker != 3:
            pygame.draw.circle(surf, (60, 130, 220), (x, y - 38), 1)
        if flicker != 5:
            pygame.draw.circle(surf, (60, 130, 220), (x, y - 34), 1)
    elif kind == "yellow_king":
        _draw_yellow_king(surf, x, y, facing)
    elif kind == "wolf":
        # Lean grey quadruped, low to the ground. Yellow eyes give a
        # threat read at a glance even with the small sprite size.
        body = (90, 88, 100)
        dark = (50, 48, 56)
        # Torso (low horizontal oval)
        pygame.draw.ellipse(surf, body, (x - 11, y - 4, 22, 12))
        pygame.draw.ellipse(surf, dark, (x - 11, y - 4, 22, 12), 1)
        # Tail
        pygame.draw.line(surf, dark, (x - 11, y - 4), (x - 18, y - 8), 2)
        # Legs (4 short stumps)
        for lx in (-7, -3, 3, 7):
            pygame.draw.rect(surf, dark, (x + lx - 1, y + 4, 2, 6))
        # Head (right side)
        pygame.draw.circle(surf, body, (x + 8, y - 8), 6)
        pygame.draw.circle(surf, dark, (x + 8, y - 8), 6, 1)
        # Snout
        pygame.draw.polygon(surf, body, [(x + 11, y - 6), (x + 17, y - 5), (x + 11, y - 4)])
        pygame.draw.polygon(surf, dark, [(x + 11, y - 6), (x + 17, y - 5), (x + 11, y - 4)], 1)
        # Pointed ears (two triangles)
        pygame.draw.polygon(surf, dark, [(x + 4, y - 12), (x + 6, y - 17), (x + 8, y - 12)])
        pygame.draw.polygon(surf, dark, [(x + 9, y - 12), (x + 11, y - 17), (x + 13, y - 12)])
        # Eye (yellow)
        pygame.draw.circle(surf, (220, 200, 60), (x + 9, y - 9), 1)
    elif kind == "black_figure":
        # Pure-black humanoid silhouette, NPC proportions. No eyes, no
        # facial detail -- just the hole-shaped outline of a person.
        # Spawned in the player's house on the 7th re-entry.
        outline = (0, 0, 0)
        # Slight darker-than-black aura behind the body so it reads as
        # absence rather than a flat sprite on dark floors.
        aura = pygame.Surface((30, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (0, 0, 0, 90), (0, 0, 30, 36))
        surf.blit(aura, (x - 15, y - 18))
        # Body
        pygame.draw.rect(surf, outline, (x - 9, y - 4, 18, 18))
        # Head
        pygame.draw.circle(surf, outline, (x, y - 12), 7)
        # Shoulders / cloak hint
        pygame.draw.rect(surf, outline, (x - 11, y - 4, 22, 6))
        # Legs
        pygame.draw.rect(surf, outline, (x - 6, y + 14, 5, 8))
        pygame.draw.rect(surf, outline, (x + 1, y + 14, 5, 8))
    elif kind == "cultist":
        # Hooded cultist. Coarse undyed robe, deep cowl, no face. Used
        # for the chasers in the depths. Walks with a slight forward
        # lean so the silhouette reads as "coming for you" even when
        # idling. No facial detail at all -- the cult has erased him.
        robe = (110, 95, 70)
        robe_lo = (70, 60, 45)
        cowl = (50, 42, 30)
        # Body
        pygame.draw.polygon(surf, robe,
                            [(x - 9, y + 16), (x - 7, y - 10),
                             (x + 7, y - 10), (x + 9, y + 16)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 9, y + 16), (x - 7, y - 10),
                             (x + 7, y - 10), (x + 9, y + 16)], 1)
        # Hood
        pygame.draw.ellipse(surf, cowl, (x - 7, y - 18, 14, 12))
        # Hem stain
        pygame.draw.line(surf, (40, 25, 20),
                         (x - 8, y + 16), (x + 8, y + 16), 2)
    elif kind == "alien_boss":
        # Final encounter: a Visitor with reaching tentacles. Body is
        # the tall_shadow silhouette enlarged + four wiggling tentacles
        # that point in the `facing` direction (toward the player when
        # in chase). Animated by pygame.time so the wiggle keeps moving
        # even when the enemy is mid-attack.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        body_rect = pygame.Rect(x - 11, y - 56, 22, 72)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-6, -8))
        pygame.draw.line(surf, (2, 0, 4), (x, y - 54), (x, y + 14), 1)
        for ey in (-46, -42, -38):
            pygame.draw.circle(surf, (60, 130, 220), (x, y + ey), 2)
        fx, fy = facing
        for i in range(4):
            phase = t * 6 + i * 1.4
            wiggle = math.sin(phase) * 6
            sway_x = -fy * wiggle
            sway_y = fx * wiggle
            origin = (x + (i - 1.5) * 4, y - 4)
            mid = (origin[0] + fx * 12 + sway_x * 0.5,
                   origin[1] + fy * 12 + sway_y * 0.5)
            tip = (origin[0] + fx * 26 + sway_x,
                   origin[1] + fy * 26 + sway_y)
            pygame.draw.line(surf, (8, 6, 14),
                             (int(origin[0]), int(origin[1])),
                             (int(mid[0]), int(mid[1])), 3)
            pygame.draw.line(surf, (16, 12, 24),
                             (int(mid[0]), int(mid[1])),
                             (int(tip[0]), int(tip[1])), 2)
            pygame.draw.circle(surf, (60, 130, 220),
                               (int(tip[0]), int(tip[1])), 1)
    elif kind == "static_figure":
        pygame.draw.rect(surf, (40, 40, 50), (x - 8, y - 2, 16, 18))
        pygame.draw.circle(surf, (200, 180, 160), (x, y - 10), 7)
        pygame.draw.rect(surf, (30, 25, 20), (x - 8, y - 17, 16, 8))
    elif kind == "doll":
        # Pink-dress doll with X-stitched eyes. Once every ~4 seconds
        # there's a brief frame where the X eyes invert into open
        # round pupils -- the doll is looking at you. The window is
        # ~80ms (one stale frame) so the player questions whether
        # they saw it. Tear streak under the right eye.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        anomaly = (t % 4.0) > 3.92
        pygame.draw.rect(surf, (200, 100, 130), (x - 6, y - 2, 12, 14))
        pygame.draw.circle(surf, (250, 230, 220), (x, y - 9), 6)
        if anomaly:
            # Open black eyes
            pygame.draw.circle(surf, C_BLACK, (x - 3, y - 10), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 3, y - 10), 1)
        else:
            pygame.draw.line(surf, C_BLACK, (x - 4, y - 11), (x - 2, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x - 2, y - 11), (x - 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 2, y - 11), (x + 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 4, y - 11), (x + 2, y - 9), 1)
        # Faint tear streak under the right eye (always visible)
        pygame.draw.line(surf, (180, 130, 140),
                         (x + 3, y - 7), (x + 3, y - 4), 1)
    elif kind == "watcher":
        # A floating orb with a vertical seam. The seam parts to
        # reveal a yellow iris when the orb is watching the player
        # (gaze=False -> player isn't looking AT it). When the
        # player looks at it (gaze=True), the seam closes.
        t = pygame.time.get_ticks() / 1000.0
        bob = int(math.sin(t * 1.4 + x * 0.013) * 2)
        layer = pygame.Surface((36, 36), pygame.SRCALPHA)
        cx = 18
        cy = 18 + bob
        body    = (60, 60, 72, 230)
        body_lo = (25, 25, 35, 230)
        body_hi = (105, 105, 120, 230)
        pygame.draw.circle(layer, body, (cx, cy), 13)
        pygame.draw.circle(layer, body_lo, (cx, cy), 13, 1)
        pygame.draw.circle(layer, body_hi, (cx - 4, cy - 5), 3)
        if gaze:
            pygame.draw.line(layer, (10, 10, 14, 255),
                             (cx, cy - 11), (cx, cy + 11), 2)
        else:
            split = 3 + int(math.sin(t * 2.1) * 1)
            pygame.draw.ellipse(layer, (10, 10, 14, 255),
                                (cx - split, cy - 11, split * 2, 22))
            iw = max(2, split * 2 - 2)
            pygame.draw.ellipse(layer, (210, 190, 70, 255),
                                (cx - split + 1, cy - 8, iw, 16))
            pygame.draw.ellipse(layer, (240, 220, 110, 255),
                                (cx - split + 1, cy - 4, iw, 8))
            pygame.draw.ellipse(layer, (10, 8, 0, 255),
                                (cx - 1, cy - 3, 2, 6))
            halo = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(halo, (210, 190, 70, 60),
                               (cx, cy), 16)
            layer.blit(halo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(layer, (x - 18, y - 26))
    elif kind == "glitch_npc":
        for _ in range(30):
            ox = random.randint(-9, 9); oy = random.randint(-12, 8)
            col = (random.randint(80,255), random.randint(0,60), random.randint(0,60))
            pygame.draw.rect(surf, col, (x + ox, y + oy, 2, 2))
    else:
        # generic placeholder
        pygame.draw.rect(surf, (200, 200, 200), (x - 8, y - 8, 16, 16))


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None, mud=0.0,
                        prone=False):
    """THRESHOLD: drifter in 1994 rural America. Faded denim jacket
    over a dark-grey shirt, blue jeans, brown work boots, brown
    hair. Replaces the original purple cloak/body. Armor overlays
    are vestigial (combat is gone) but still draw if equipped, so
    old saves render cleanly.

    A faint ground-shadow ellipse roots the player in the scene.
    None of the NPCs cast a shadow, which is by design -- the player
    is the only thing here that's properly *here*."""
    jacket = (78, 92, 120)        # faded denim
    shirt  = (50, 50, 56)         # dark grey shirt under
    jeans  = (50, 60, 100)        # blue jeans
    boots  = (40, 28, 20)         # brown leather
    skin   = (220, 190, 160)
    hair   = (80, 50, 30)
    if prone:
        # Lying on the cot. Compress the figure to a horizontal
        # silhouette with a thin blanket overlay. Drawn off-centre
        # so it reads as resting on the bedding rather than on the
        # floor.
        bx = x - 12
        by = y - 2
        # Blanket / quilt
        pygame.draw.rect(surf, (90, 60, 70), (bx, by, 24, 9))
        pygame.draw.rect(surf, (60, 40, 50), (bx, by, 24, 9), 1)
        # Head poking out at one end
        pygame.draw.circle(surf, skin, (bx + 22, by + 4), 4)
        pygame.draw.rect(surf, hair, (bx + 19, by, 7, 4))
        # Eyes closed: a thin dark line
        pygame.draw.line(surf, (40, 30, 24),
                         (bx + 21, by + 4), (bx + 24, by + 4), 1)
        # One boot peeking out the foot end
        pygame.draw.rect(surf, boots, (bx, by + 5, 4, 3))
        return
    # Ground shadow under the boots (drawn first so the body sits on it).
    shadow = pygame.Surface((22, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 22, 8))
    surf.blit(shadow, (x - 11, y + 16))
    # Lower body: jeans
    pygame.draw.rect(surf, jeans, (x - 7, y + 6, 14, 8))
    # Upper body: shirt under jacket (small inner stripe shows)
    pygame.draw.rect(surf, shirt, (x - 6, y - 4, 12, 12))
    # Jacket panels
    pygame.draw.rect(surf, jacket, (x - 8, y - 4, 4, 14))   # left
    pygame.draw.rect(surf, jacket, (x + 4, y - 4, 4, 14))   # right
    pygame.draw.rect(surf, jacket, (x - 8, y - 4, 16, 3))   # collar/yoke
    # Vestigial armor overlay (combat is gone; if a player has
    # equipped armor from a legacy save it still renders so the
    # save isn't broken visually).
    if armor == "cloth_tunic":
        pygame.draw.rect(surf, (200, 180, 140), (x - 7, y - 2, 14, 10))
    elif armor == "leather_armor":
        pygame.draw.rect(surf, (110, 70, 40), (x - 8, y - 3, 16, 12))
    elif armor == "iron_armor":
        pygame.draw.rect(surf, (140, 145, 160), (x - 8, y - 4, 16, 14))
    # Head
    pygame.draw.circle(surf, skin, (x, y - 12), 7)
    # Hair across the top
    pygame.draw.rect(surf, hair, (x - 7, y - 18, 14, 6))
    # Boots: walking animation
    leg_off = int(math.sin(walk_phase) * 2)
    pygame.draw.rect(surf, boots, (x - 6, y + 14, 5, 4 + max(0, -leg_off)))
    pygame.draw.rect(surf, boots, (x + 1, y + 14, 5, 4 + max(0, leg_off)))
    # THRESHOLD wake-state mud. The player's boots are caked when the
    # opening fires; the splatter recedes as they walk. Two flecks of
    # darker brown on each boot + a smear up the jeans cuff that
    # fades with `mud` (0..1).
    if mud > 0.05:
        m_a = max(40, min(220, int(180 * mud)))
        mud_col = (28, 18, 10)
        pygame.draw.rect(surf, mud_col, (x - 6, y + 14, 5, 2))
        pygame.draw.rect(surf, mud_col, (x + 1, y + 14, 5, 2))
        # cuff smear
        cuff = pygame.Surface((14, 4), pygame.SRCALPHA)
        pygame.draw.rect(cuff, (30, 22, 14, m_a), (0, 0, 14, 4))
        surf.blit(cuff, (x - 7, y + 12))
        # one fleck higher up the leg, only when very muddy
        if mud > 0.5:
            pygame.draw.rect(surf, mud_col, (x - 4, y + 9, 2, 2))
            pygame.draw.rect(surf, mud_col, (x + 3, y + 10, 2, 2))
    # Eyes (look in facing direction)
    fx, fy = facing
    eye_y = y - 12 + int(fy * 2)
    eye_dx = int(fx * 2)
    pygame.draw.circle(surf, C_BLACK, (x - 2 + eye_dx, eye_y), 1)
    pygame.draw.circle(surf, C_BLACK, (x + 2 + eye_dx, eye_y), 1)


# ===========================================================================
# THE YELLOW KING
#
# Not a body. A floating clot of sick-gold light packed with the cult's fused
# faces, broken arms reaching out of the glow to grasp. No legs: it hovers (a
# faint shadow far below) and PHASES like the watcher -- some seconds you can
# almost not see it. The trapped faces surface and dissolve back into the
# light on staggered cycles, and the whole apparition drags a short ghost-
# trail as it drifts. Self-animated off pygame.time.get_ticks(); `facing`
# leans the faces and points the reaching arms toward the player. Spawns at
# apex Pursuer proximity; contact is the closure ending.
# ===========================================================================
_YK_TRAIL = []                       # recent mass-centre screen positions
_YK_T1, _YK_T2, _YK_T3, _YK_T4 = (140, 96, 22), (196, 150, 42), (236, 198, 66), (252, 226, 120)
_YK_GOLD, _YK_HOT = (236, 204, 64), (252, 226, 120)
_YK_DK, _YK_DK_HI = (28, 25, 34), (60, 55, 72)
_YK_BONE = (150, 128, 70)
_YK_FHI, _YK_FMID, _YK_FLO, _YK_PIT = (210, 202, 180), (150, 143, 120), (92, 86, 70), (10, 8, 12)
# Warm, gold-tinted mask tones so the masks read as part of the light (drawn
# translucent + luminous) rather than separate pale objects floating in it.
_YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT = (238, 222, 174), (210, 178, 108), (150, 116, 52), (78, 52, 18)


def _yk_slots():
    """Deterministic swirl params for the faces + eyes (own RNG so the global
    stream the game relies on is never touched). Each face orbits the core at
    its own radius/speed and surfaces/dissolves on its own fade cycle."""
    r = random.Random(20240611)
    faces, eyes = [], []
    # mask designs: plain, screaming, hollow/gaunt, cracked, and a melted
    # double (two faces fused) that only POPS UP now and then.
    kinds = ["plain", "scream", "hollow", "plain", "crack", "double",
             "plain", "scream", "hollow", "double"]
    for k in kinds:
        faces.append((
            r.uniform(0.22, 0.82),     # orbit radius (fraction of R)
            r.uniform(0, math.tau),    # base angle
            r.uniform(0.30, 0.85),     # angular speed (swirl, one direction)
            r.randint(4, 8),           # mask radius (bigger -> clearer)
            r.uniform(0.5, 1.3),       # fade speed
            r.uniform(0, 6.28),        # fade / phase offset
            k,                         # mask design
        ))
    for _ in range(4):
        eyes.append((r.uniform(0.2, 0.7), r.uniform(0, math.tau),
                     r.uniform(0.3, 0.8), r.uniform(0, 6.28)))
    return faces, eyes


_YK_FACES, _YK_EYES = _yk_slots()


def _yk_radial(surf, x, y, R, color, a0, add=True):
    """Soft glowing/fading disc built from concentric circles."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    c = (R + 1, R + 1); st = max(6, R // 2)
    for i in range(st, 0, -1):
        a = int(a0 * (1 - i / st) ** 1.7)
        if a > 0:
            pygame.draw.circle(g, (color[0], color[1], color[2], a), c, int(R * i / st))
    surf.blit(g, (int(x) - R - 1, int(y) - R - 1),
              special_flags=pygame.BLEND_RGBA_ADD if add else 0)


def _yk_glow(layer, cx, cy, R, t):
    """The hovering clot of golden light -- soft bloom over a lumpy amber mass
    brightening to a hot core, breathing on a slow sine."""
    R = int(R * (1 + 0.06 * math.sin(t * 2.0)))
    _yk_radial(layer, cx, cy, int(R * 1.8), _YK_GOLD, 66)
    _yk_radial(layer, cx, cy, int(R * 1.18), _YK_GOLD, 60)
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    sw = t * 0.6                       # the light churns -- rotate the lumps
    ca, sa = math.cos(sw), math.sin(sw)
    for col, scl, grow in [(_YK_T1, 1.0, 3), (_YK_T2, 0.74, 1), (_YK_T3, 0.5, 0), (_YK_T4, 0.28, 0)]:
        for ox, oy in subs:
            rx, ry = ox * ca - oy * sa, ox * sa + oy * ca
            pygame.draw.circle(layer, col,
                               (int(cx + rx * R * 0.6), int(cy + ry * R * 0.9)),
                               int(R * 0.5 * scl) + grow)
    for k in range(4):                 # orbiting bright gold wisps -> churn
        a = sw * 1.6 + k * 1.57
        _yk_radial(layer, cx + math.cos(a) * R * 0.42, cy + math.sin(a) * R * 0.42,
                   int(R * 0.42), _YK_T4, 76)
    _yk_radial(layer, cx, cy - 2, int(R * 0.55), _YK_T4, 78)


def _yk_mask(surf, cx, cy, r, vis, kind):
    """A MASK made of the same light: warm gold-tinted, drawn TRANSLUCENT (so
    the glow reads through it) and given a luminous halo, surfacing (vis->1)
    and dissolving back into the glow (vis->0). `kind` varies the design;
    'double' is two masks melted into one."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    # luminous: brighten the patch so the mask belongs to the light
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(3, r // 2)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = r + pad
    hi, mid, lo, pit = _YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT
    ew = max(1, r // 4)
    if kind == "double":
        off = max(2, r // 2)
        for ddx in (-off, off):
            pygame.draw.circle(m, lo, (mx + ddx + 1, my + 1), r)
            pygame.draw.circle(m, mid, (mx + ddx, my), r)
            pygame.draw.circle(m, hi, (mx + ddx - 1, my - 1), max(1, r - 2))
        pygame.draw.line(m, lo, (mx, my - r), (mx, my + r), 1)       # fusion seam
        if vis > 0.4:
            for ddx in (-off, off):
                pygame.draw.circle(m, pit, (mx + ddx - r // 2, my - r // 4), ew)
                pygame.draw.circle(m, pit, (mx + ddx + r // 2, my - r // 4), ew)
            pygame.draw.ellipse(m, pit, (mx - off - r // 4, my + r // 3,
                                         2 * off + r // 2, max(2, r // 2)))   # merged maw
    else:
        pygame.draw.circle(m, lo, (mx + 1, my + 1), r)
        pygame.draw.circle(m, mid, (mx, my), r)
        pygame.draw.circle(m, hi, (mx - 1, my - 1), max(1, r - 1))
        if vis > 0.5:
            pygame.draw.circle(m, lo, (mx, my), r, 1)               # contour -> clarity
        if vis > 0.35 and r >= 3:
            if kind == "hollow":                                   # gaunt: deep sockets, slit
                pygame.draw.ellipse(m, pit, (mx - r // 2 - 1, my - r // 3, ew + 2, ew + 3))
                pygame.draw.ellipse(m, pit, (mx + r // 2 - 1, my - r // 3, ew + 2, ew + 3))
                pygame.draw.line(m, pit, (mx - r // 4, my + r // 3), (mx + r // 4, my + r // 3), 1)
            elif kind == "scream":                                 # mouth wrenched open
                pygame.draw.circle(m, pit, (mx - r // 2, my - r // 4), ew)
                pygame.draw.circle(m, pit, (mx + r // 2, my - r // 4), ew)
                pygame.draw.ellipse(m, pit, (mx - r // 3, my, max(2, 2 * r // 3), max(3, r)))
            else:                                                  # plain / cracked
                pygame.draw.circle(m, pit, (mx - r // 2, my - r // 4), ew)
                pygame.draw.circle(m, pit, (mx + r // 2, my - r // 4), ew)
                pygame.draw.line(m, lo, (mx, my - r // 5), (mx, my + r // 5), 1)   # nose ridge
                pygame.draw.ellipse(m, pit, (mx - r // 3, my + r // 3,
                                             max(2, 2 * r // 3), max(2, r // 3)))
                if kind == "crack":
                    pygame.draw.line(m, pit, (mx - 1, my - r), (mx + 2, my + r), 1)
    m.set_alpha(int(64 + 156 * vis))            # translucent -> the glow reads through
    surf.blit(m, (cx - mx, cy - my))


def _yk_arm(layer, cx, cy, ang, length, R, t, idx):
    """A broken arm that spawns from the body and reaches out of the light:
    it extends outward then draws back on its own cycle, reflex elbow,
    clawing hand."""
    wob = math.sin(t * 1.9 + idx * 1.3) * 0.14
    ext = 0.55 + 0.45 * max(0.0, math.sin(t * 1.5 + idx * 0.9))   # spawn + reach
    reach = length * ext
    root = (cx + math.cos(ang) * R * 0.5, cy + math.sin(ang) * R * 0.5)
    hand = (cx + math.cos(ang + wob) * reach, cy + math.sin(ang + wob) * reach)
    mx, my = (root[0] + hand[0]) / 2, (root[1] + hand[1]) / 2
    perp = (-math.sin(ang), math.cos(ang)); k = (R * 0.5) * (1 if idx % 2 else -1)
    elbow = (mx + perp[0] * k, my + perp[1] * k)
    pts = [(int(a), int(b)) for a, b in (root, elbow, hand)]
    w = max(3, int(R * 0.34))
    pygame.draw.lines(layer, _YK_DK_HI, False, pts, w + 2)
    pygame.draw.lines(layer, _YK_DK, False, pts, w)
    ha = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])
    pygame.draw.circle(layer, _YK_DK, (int(hand[0]), int(hand[1])), max(2, w // 2))
    for fa in (-42, -14, 16, 44):
        a2 = ha + math.radians(fa)
        tip = (hand[0] + math.cos(a2) * R * 0.5, hand[1] + math.sin(a2) * R * 0.5)
        pygame.draw.line(layer, _YK_DK, (int(hand[0]), int(hand[1])),
                         (int(tip[0]), int(tip[1])), 2)
        try:
            layer.set_at((int(tip[0]), int(tip[1])), _YK_BONE)
        except (IndexError, ValueError):
            pass


def _draw_yellow_king(surf, x, y, facing):
    global _YK_TRAIL
    t = pygame.time.get_ticks() / 1000.0
    R = 22
    hover = 42
    mcx, mcy = x, int(y - hover + math.sin(t * 1.1) * 3)
    # Phase: slow transparency pulse with a brief blink-out at the troughs.
    s = math.sin(t * 1.5)
    phase = 0.6 + 0.4 * s
    if s < -0.7:
        phase *= 0.35
    # Short ghost-trail of the glow. Reset on a teleport/respawn jump.
    WIN = 0.34
    if _YK_TRAIL:
        px, py, pt = _YK_TRAIL[-1]
        if (mcx - px) ** 2 + (mcy - py) ** 2 > 70 ** 2 or (t - pt) > 0.45:
            _YK_TRAIL = []
    _YK_TRAIL.append((mcx, mcy, t))
    _YK_TRAIL = [e for e in _YK_TRAIL if t - e[2] < WIN][-12:]
    # A glowing, mask-filled wake: it tears a seam of light and faces through
    # space that seals (fades) behind it.
    ghosts = _YK_TRAIL[:-1]
    for i, (gx, gy, gt) in enumerate(ghosts):
        age = (t - gt) / WIN
        a = int(74 * (1 - age) * phase)
        if a > 0:
            _yk_radial(surf, gx, gy, int(R * 1.15 * (1 - 0.32 * age)), _YK_GOLD, a)
        if i % 2 == 0:                          # faces caught in the rip
            mv = 0.55 * (1 - age) * phase
            if mv > 0.05:
                kk = _YK_FACES[i % len(_YK_FACES)][6]
                if kk == "double":
                    kk = "plain"
                _yk_mask(surf, gx + ((i % 3) - 1) * 3, gy + ((i % 2) * 5 - 2),
                         4 + i % 2, mv, kk)
    # Faint floating shadow on the ground, far below the mass.
    sh = pygame.Surface((40, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, int(80 * phase)), (0, 0, 40, 12))
    surf.blit(sh, (x - 20, y - 4))
    # Main apparition on its own layer so the whole thing alpha-phases together.
    L = 170
    layer = pygame.Surface((L, L), pygame.SRCALPHA)
    cx = cy = L // 2
    # Direction of travel, read off the trail -> the arms reach the way it's
    # heading (like it hauls itself along); fall back to facing when at rest.
    tdx = tdy = 0.0
    if len(_YK_TRAIL) >= 2:
        ox, oy, _ot = _YK_TRAIL[0]
        tdx, tdy = mcx - ox, mcy - oy
    if tdx * tdx + tdy * tdy > 9:
        aa = math.atan2(tdy, tdx)
    else:
        fxx, fyy = facing if facing != (0, 0) else (0, 1)
        aa = math.atan2(fyy, fxx)
    fb = (math.cos(aa) * R * 0.22, math.sin(aa) * R * 0.22)   # mass leans the way it moves
    _yk_glow(layer, cx, cy, R, t)
    # Masks swirl around the core, surfacing and dissolving in the light. The
    # melted 'double' masks stay submerged most of the time and POP UP briefly.
    for rn, ba, asp, fr, vsp, vph, kind in _YK_FACES:
        ang = ba + t * asp
        rr = rn * (0.9 + 0.1 * math.sin(t * 0.8 + vph))
        fxp = cx + math.cos(ang) * R * 0.82 * rr + fb[0]
        fyp = cy + math.sin(ang) * R * 0.95 * rr + fb[1]
        if kind == "double":
            vis = max(0.0, min(1.0, (math.sin(t * vsp + vph) - 0.55) / 0.4))
        else:
            vis = max(0.0, min(1.0, 0.5 + 0.72 * math.sin(t * vsp + vph)))
        _yk_mask(layer, fxp, fyp, fr, vis, kind)
    # Hot eye-glints swirl with the faces.
    for rn, ba, asp, ph in _YK_EYES:
        if math.sin(t * 2.1 + ph) > 0.1:
            ang = ba + t * asp
            ex = cx + math.cos(ang) * R * 0.7 * rn + fb[0]
            ey = cy + math.sin(ang) * R * 0.7 * rn + fb[1]
            _yk_radial(layer, ex, ey, 5, _YK_HOT, 110)
            pygame.draw.circle(layer, _YK_PIT, (int(ex), int(ey)), 1)
    # Arms spawn from the body and reach toward where it's heading (aa) -- a
    # fan led by the longest arm in the travel direction.
    for idx, (da, ln) in enumerate([(0.0, R * 2.05), (0.45, R * 1.7), (-0.45, R * 1.7),
                                    (0.95, R * 1.45), (-0.95, R * 1.45)]):
        _yk_arm(layer, cx, cy, aa + da, ln, R, t, idx)
    layer.set_alpha(int(255 * max(0.05, phase)))
    surf.blit(layer, (mcx - cx, mcy - cy))
