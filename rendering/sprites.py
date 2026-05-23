"""Character sprites: NPCs, enemies, the player."""
import math
import random
import pygame
from constants import C_BLACK

def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None):
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
        # narrow enough that it reads as not-quite-human. In lore the
        # figure is a pilgrim of the Yellow King -- which is why the eyes
        # are three jaundiced dots stacked vertically, not a face we
        # recognise.
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
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 42), 1)
        if flicker != 3:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 38), 1)
        if flicker != 5:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 34), 1)
    elif kind == "yellow_king":
        # The King in Yellow -- a black-tar wendigo that ERUPTS from a
        # cult member (the corpse's bones become its hooves), golden
        # eyes and tentacles uncoiling from the tar. The full drawing,
        # birth, and run/walk gait live in _draw_king. `birth` (0..1)
        # and `gait` come from the live NPC; when absent (a preview)
        # they loop off the clock so the emergence + run still show.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        if birth is None:
            cyc = t % 7.0
            b = min(1.0, cyc / 1.6)            # erupt over ~1.6s
            g = max(0.0, cyc - 1.6) * 7.0      # then run the rest
        else:
            b = birth
            g = gait if gait is not None else t * 7.0
        _draw_king(surf, x, y, facing, t, b, g)
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
        # Hooded cultist -- a grim, near-black robe and a deep cowl that
        # is simply a void; the cult has taken his face. He trudges: the
        # whole body rocks and rises on each step so he reads as
        # advancing on you, not idling. Two cold, recessed pinpricks of
        # sick light sit far back in the cowl -- menace, not glow.
        t = pygame.time.get_ticks() / 1000.0
        gait = math.sin(t * 3.0 + x * 0.02)
        lean = int(gait * 2)                      # rock the body
        bob = int(abs(math.sin(t * 3.0)) * 2)     # rise on each step
        robe = (50, 45, 42)                       # grim charcoal
        robe_lo = (28, 25, 24)
        cowl = (12, 11, 13)                       # black void
        top = y - 10 - bob
        pygame.draw.polygon(surf, robe,
                            [(x - 9, y + 16), (x - 7 + lean, top),
                             (x + 7 + lean, top), (x + 9, y + 16)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 9, y + 16), (x - 7 + lean, top),
                             (x + 7 + lean, top), (x + 9, y + 16)], 1)
        # Deep cowl -- a black hood, the face a hole.
        head_cy = top - 1
        pygame.draw.ellipse(surf, cowl, (x - 7 + lean, head_cy - 7, 14, 14))
        # Two cold recessed eyes (dim sick amber), blinking on a cycle.
        if (t + x * 0.05) % 4.0 > 0.2:
            pygame.draw.circle(surf, (116, 100, 50), (x - 3 + lean, head_cy), 1)
            pygame.draw.circle(surf, (116, 100, 50), (x + 3 + lean, head_cy), 1)
        # Dried blood down the robe + a black hem.
        pygame.draw.line(surf, (64, 16, 14), (x, y + 2), (x + 1, y + 15), 2)
        pygame.draw.line(surf, (16, 12, 12),
                         (x - 8, y + 16), (x + 8, y + 16), 2)
    elif kind == "curse_priest":
        # The cult's curse-priest -- the special cultist that binds the
        # Watchers to you. Taller and gaunter than the rank-and-file:
        # a blood-dark robe, a low hood over a pale ruined face with a
        # stitched-shut mouth and hollow sockets, hands raised mid-rite
        # with ichor dripping from the fingertips. A vertical row of
        # small yellow curse-eyes opens down its chest -- the curse,
        # looking out. Sways, twitches, and drips.
        t = pygame.time.get_ticks() / 1000.0
        sway = math.sin(t * 1.2 + x * 0.02)
        lean = int(sway)
        robe = (54, 40, 44)
        robe_lo = (32, 22, 26)
        blood = (122, 24, 22)
        face = (190, 180, 165)
        face_lo = (120, 110, 100)
        # Tall robe body.
        pygame.draw.polygon(surf, robe,
                            [(x - 10, y + 18), (x - 7 + lean, y - 18),
                             (x + 7 + lean, y - 18), (x + 10, y + 18)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 10, y + 18), (x - 7 + lean, y - 18),
                             (x + 7 + lean, y - 18), (x + 10, y + 18)], 1)
        # Blood down the robe front.
        pygame.draw.line(surf, blood, (x + lean, y - 14), (x, y + 16), 2)
        pygame.draw.line(surf, (70, 14, 12), (x - 3, y + 2), (x - 2, y + 16), 1)
        # A slow rite: the arms rise and fall together, ichor beading
        # off the fingertips. They lift highest as the curse-eyes flare
        # (below) -- that upswing is the moment it binds you.
        rite = math.sin(t * 1.3) * 0.5 + 0.5          # 0..1, arms down..up
        hy = y - 4 - int(rite * 9)
        for s in (-1, 1):
            hx = x + s * (9 + int(rite * 3))
            pygame.draw.line(surf, robe, (x + s * 5, y - 8), (hx, hy), 3)
            pygame.draw.circle(surf, face, (hx, hy), 2)
            drip = (t * 0.9 + (s + 1) * 0.4) % 1.0
            pygame.draw.circle(surf, blood, (hx, hy + 2 + int(drip * 10)), 1)
        # Hood + ruined pale face.
        pygame.draw.ellipse(surf, robe_lo, (x - 7 + lean, y - 26, 14, 16))
        pygame.draw.ellipse(surf, face, (x - 4 + lean, y - 23, 8, 11))
        pygame.draw.ellipse(surf, face_lo, (x - 4 + lean, y - 23, 8, 11), 1)
        # Hollow sockets -- no light there.
        pygame.draw.circle(surf, (12, 8, 10), (x - 2 + lean, y - 19), 1)
        pygame.draw.circle(surf, (12, 8, 10), (x + 2 + lean, y - 19), 1)
        # Stitched-shut mouth.
        my = y - 14
        pygame.draw.line(surf, (60, 20, 22),
                         (x - 3 + lean, my), (x + 3 + lean, my), 1)
        for sx in range(-3, 4, 2):
            pygame.draw.line(surf, (40, 12, 14),
                             (x + lean + sx, my - 1), (x + lean + sx, my + 1), 1)
        # A vertical row of small curse-eyes down the chest, flaring
        # sick-bright on the rite's upswing -- the curse, looking out.
        ecol = (150 + int(rite * 55), 120 + int(rite * 50), 56)
        for i in range(3):
            if (t * 1.1 + i * 0.8) % 3.0 > 0.3:
                pygame.draw.circle(surf, ecol, (x + lean, y - 6 + i * 6), 1)
        # Dark hem.
        pygame.draw.line(surf, (24, 14, 16),
                         (x - 9, y + 18), (x + 9, y + 18), 2)
    elif kind == "vessel_avatar":
        # A towering Yellow-King vessel with reaching tentacles. Body is
        # the tall_shadow silhouette enlarged + four wiggling tentacles
        # that point in the `facing` direction (toward the player when
        # in chase). Animated by pygame.time so the wiggle keeps moving
        # even when the figure is mid-lunge.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        body_rect = pygame.Rect(x - 11, y - 56, 22, 72)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-6, -8))
        pygame.draw.line(surf, (2, 0, 4), (x, y - 54), (x, y + 14), 1)
        for ey in (-46, -42, -38):
            pygame.draw.circle(surf, (210, 188, 70), (x, y + ey), 2)
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
            pygame.draw.circle(surf, (210, 188, 70),
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
        # A Watcher -- the curse made visible. NOT an eye: a tall,
        # ragged, faceless figure that stands at the edge of sight and
        # watches. Only the cursed see them. It is half-there -- it
        # phases on a slow sine, an apparition you can never quite fix
        # on -- and it looms a little nearer over its cycle. Two faint
        # sick pinpricks deep in the cowl are the only colour: the gaze.
        # Look straight at it (gaze=True) and the pinpricks go dark.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        phase = 0.35 + 0.5 * (math.sin(t * 1.1 + x * 0.01) * 0.5 + 0.5)
        loom = math.sin(t * 0.5 + x * 0.02) * 0.5 + 0.5      # 0..1, creeps in
        sway = int(math.sin(t * 0.8 + x * 0.03))
        layer = _pg.Surface((40, 64), _pg.SRCALPHA)
        bx = 20 + sway
        base_y = 60
        h = 38 + int(loom * 8)            # looms taller as it nears
        top = base_y - h
        shroud = (24, 22, 28, 255)
        shroud_lo = (11, 10, 14, 255)
        # Tapered shroud -- narrow shoulders to a wide, torn hem.
        body = [(bx - 4, top + 7), (bx + 4, top + 7),
                (bx + 10, base_y), (bx - 10, base_y)]
        _pg.draw.polygon(layer, shroud, body)
        _pg.draw.polygon(layer, shroud_lo, body, 1)
        # Ragged hem -- torn strips trailing into the dark.
        for hx in range(-9, 10, 3):
            _pg.draw.line(layer, shroud, (bx + hx, base_y - 3),
                          (bx + hx + 1, base_y + 3 + (hx % 3)), 2)
        # Drawn-up hood / faceless head.
        _pg.draw.circle(layer, shroud, (bx, top + 6), 6)
        _pg.draw.circle(layer, shroud_lo, (bx, top + 7), 5)
        # Thin reaching arms hinted down the body.
        _pg.draw.line(layer, shroud_lo, (bx - 4, top + 12), (bx - 8, top + 24), 2)
        _pg.draw.line(layer, shroud_lo, (bx + 4, top + 12), (bx + 8, top + 24), 2)
        # The gaze: two faint sick pinpricks (yellow used ONLY here, a
        # dim light in the dark), unless the player looks straight at it.
        if not gaze:
            g = 110 + int(math.sin(t * 2.0 + x) * 25)
            eye = (g, int(g * 0.85), 38, 255)
            _pg.draw.circle(layer, eye, (bx - 2, top + 6), 1)
            _pg.draw.circle(layer, eye, (bx + 2, top + 6), 1)
            halo = _pg.Surface((40, 64), _pg.SRCALPHA)
            _pg.draw.circle(halo, (60, 52, 22), (bx, top + 6), 7)
            layer.blit(halo, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)
        layer.set_alpha(int(255 * phase))
        surf.blit(layer, (x - 20, y - base_y))
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


def _draw_king(surf, x, y, facing, t, birth, gait):
    """The King in Yellow -- a black-tar wendigo.

    `birth` (0..1) drives the eruption: a cult member convulses, bursts
    in a spray of tar/gore/gold, and the corpse's bones splay out into
    hooves while the tar mass rises, antlers branch, tentacles uncoil,
    and golden eyes ignite. At birth >= 1.0 it runs: `gait` drives a
    galloping leg cycle, a forward lunge, and trailing tentacles. The
    only colour is the gold of the eyes against near-black tar.
    """
    import pygame as _pg
    LW, LH = 104, 120
    layer = _pg.Surface((LW, LH), _pg.SRCALPHA)
    ox, oy = 52, 104                       # feet origin in the layer
    fx, fy = facing
    fsign = 1 if fx >= 0 else -1

    tar    = (15, 14, 18)
    tar_hi = (44, 42, 52)
    tar_lo = (6, 6, 9)
    gold   = (230, 184, 46)
    goldg  = (255, 216, 90)
    bone   = (196, 184, 162)
    bone_lo = (120, 112, 96)
    gore   = (126, 22, 18)

    b = max(0.0, min(1.0, birth))

    def ss(a):
        a = max(0.0, min(1.0, a))
        return a * a * (3 - 2 * a)

    rise = ss(b)
    splay = ss((b - 0.30) / 0.50)
    teng = ss((b - 0.55) / 0.45)
    eyeon = ss((b - 0.70) / 0.30)
    antl = ss((b - 0.60) / 0.40)
    born = b >= 1.0
    lunge = int(math.sin(gait) * 3) if born else 0
    bob = int(abs(math.sin(gait)) * 3) if born else 0

    # Tar pool / shadow on the ground (widens as it rises).
    pw = int(13 + 18 * rise)
    _pg.draw.ellipse(layer, (8, 7, 10), (ox - pw, oy - 5, pw * 2, 12))

    # ---- legs + hooves (the corpse's bones), galloping ----
    hip_y = oy - int(26 * rise) - bob
    for i in range(2):
        ph = gait + i * math.pi
        sw = math.sin(ph)
        foot_x = ox + (i * 2 - 1) * 4 + int(sw * 9 * splay) + lunge
        lift = max(0, int(math.cos(ph) * 5)) if born else 0
        foot_y = oy - lift
        hip_x = ox + (i * 2 - 1) * 5
        knee_x = (hip_x + foot_x) // 2 + (i * 2 - 1) * 5
        knee_y = (hip_y + foot_y) // 2 - 3
        _pg.draw.line(layer, tar, (hip_x, hip_y), (knee_x, knee_y), 5)
        _pg.draw.line(layer, tar, (knee_x, knee_y), (foot_x, foot_y - 6), 4)
        _pg.draw.line(layer, tar_hi, (hip_x, hip_y), (knee_x, knee_y), 1)
        # hoof: torn bone (gore at the break, bone shaft, splayed hoof)
        _pg.draw.line(layer, gore, (foot_x - 2, foot_y - 7), (foot_x + 2, foot_y - 7), 3)
        _pg.draw.line(layer, bone, (foot_x, foot_y - 6), (foot_x, foot_y - 1), 4)
        _pg.draw.polygon(layer, bone, [(foot_x - 3, foot_y - 1), (foot_x + 3, foot_y - 1),
                                       (foot_x + 2, foot_y + 2), (foot_x - 2, foot_y + 2)])
        _pg.draw.line(layer, bone_lo, (foot_x, foot_y - 1), (foot_x, foot_y + 2), 1)

    # ---- body: a large, lumpy TUMOUR mass (no clean deer line) ----
    # Overlapping tar blobs of varied size give a ragged, writhing
    # silhouette; each lump pulses a little so the mass reads cancerous
    # and alive rather than as a clean animal. Built up from the hips
    # and scaled in by `rise`.
    cx = ox + lunge
    lumps = [   # (dx, dy, radius) relative to (cx, hip_y); dy<0 is up
        (0, -2, 12), (-8, -5, 8), (9, -7, 8),
        (-4, -13, 10), (7, -15, 8), (-10, -17, 6),
        (3, -22, 9), (-6, -26, 7), (8, -27, 6),
        (-2, -32, 7), (5, -35, 5), (-7, -34, 4),
    ]
    drawn = []
    for i, (dx, dy, br) in enumerate(lumps):
        lx_ = cx + int(dx * rise)
        ly_ = hip_y + int(dy * rise)
        r = max(1, int((br + math.sin(t * 2.2 + i * 0.9)) * rise))
        drawn.append((lx_, ly_, r))
        _pg.draw.circle(layer, tar, (lx_, ly_), r)
    for i, (lx_, ly_, r) in enumerate(drawn):   # seams + wet highlights
        if r >= 4:
            _pg.draw.circle(layer, tar_lo, (lx_, ly_), r, 1)
        if i % 3 == 0 and r >= 4:
            _pg.draw.circle(layer, tar_hi, (lx_ - r // 3, ly_ - r // 3),
                            max(1, r // 4))
    top_y = hip_y + int(-35 * rise)
    mid_y = hip_y + int(-16 * rise)

    # ---- antlers: asymmetric and broken, jutting from the top lumps;
    # a short forked stub on the left, a longer crooked rack on the
    # right, so the silhouette never settles into a clean stag. ----
    al = int(15 * antl)
    if al > 0:
        lx0, ly0 = cx - 5, top_y + 2
        _pg.draw.line(layer, bone, (lx0, ly0), (lx0 - int(5 * antl), ly0 - al), 2)
        _pg.draw.line(layer, bone, (lx0 - int(2 * antl), ly0 - al // 2),
                      (lx0 - int(9 * antl), ly0 - al // 2 - int(3 * antl)), 1)
        rx0, ry0 = cx + 4, top_y
        rtx, rty = rx0 + int(9 * antl), ry0 - int(al * 1.4)
        _pg.draw.line(layer, bone, (rx0, ry0), (rx0 + int(3 * antl), ry0 - al), 2)
        _pg.draw.line(layer, bone, (rx0 + int(3 * antl), ry0 - al), (rtx, rty), 2)
        _pg.draw.line(layer, bone, (rx0 + int(3 * antl), ry0 - al),
                      (rx0 + int(12 * antl), ry0 - al - int(2 * antl)), 1)
        _pg.draw.line(layer, bone, (rtx, rty), (rtx + int(4 * antl), rty - int(5 * antl)), 1)
        _pg.draw.line(layer, bone, (rtx, rty), (rtx - int(3 * antl), rty - int(4 * antl)), 1)

    # ---- tentacles uncoiling from the shoulders, writhing upward ----
    anchor = (cx - fsign * 3, mid_y)
    for i in range(4):
        base_ang = -math.pi / 2 + (i - 1.5) * 0.5
        length = (13 + (i % 2) * 6) * teng
        px, py = anchor
        pts = [(px, py)]
        segs = 5
        for s in range(1, segs + 1):
            f = s / segs
            ang = base_ang + math.sin(t * 3.0 + i * 1.3 + f * 4) * 0.5 * f
            px += math.cos(ang) * (length / segs)
            py += math.sin(ang) * (length / segs)
            pts.append((px, py))
        if length > 2:
            ipts = [(int(a), int(c)) for a, c in pts]
            _pg.draw.lines(layer, tar, False, ipts, 3)
            _pg.draw.lines(layer, tar_hi, False, ipts, 1)

    # ---- a mass of golden eyes wreathing the tar (the original King's
    # signature, merged in): the head pair anchors it, the rest scatter
    # over the body, each blinking on its own cycle so they are never
    # all open at once. Gold is the only colour. Pupils track the player.
    if eyeon > 0:
        glow = _pg.Surface((LW, LH), _pg.SRCALPHA)
        # A pair near the top of the mass anchors the "face"; the rest
        # open inside the larger tumours, scattered and out of sync.
        eye_specs = [(cx - 3, top_y + 6, 2), (cx + 4, top_y + 5, 2)]
        for i, (lx_, ly_, r) in enumerate(drawn):
            if r >= 5 and i % 2 == 1:
                eye_specs.append((lx_, ly_, 1))
        for j, (gx, gy, r) in enumerate(eye_specs):
            if (t * 1.3 + j * 0.7) % 4.0 < 0.3:
                continue                            # this eye is shut
            _pg.draw.circle(glow, (gold[0], gold[1], gold[2], int(70 * eyeon)),
                            (gx, gy), r + 2)
            _pg.draw.circle(layer, goldg, (gx, gy), max(1, int(r * eyeon)))
            if r >= 2:                              # pupils on the head pair
                _pg.draw.circle(layer, (10, 8, 0),
                                (gx + int(fx), gy + int(fy)), 1)
        layer.blit(glow, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)

    # ---- birth: the cult member it erupts from (fades out early) ----
    if b < 0.42:
        a = 1.0 - ss(b / 0.42)
        jit = int(math.sin(t * 40) * 2 * (b * 2.4))
        cf = _pg.Surface((LW, LH), _pg.SRCALPHA)
        ry0 = oy - int(26 * (1.0 + b * 0.5))
        _pg.draw.polygon(cf, (40, 36, 34, int(230 * a)),
                         [(ox - 8 + jit, oy), (ox - 6 + jit, ry0),
                          (ox + 6 + jit, ry0), (ox + 8 + jit, oy)])
        _pg.draw.ellipse(cf, (12, 11, 13, int(230 * a)),
                         (ox - 6 + jit, ry0 - 8, 12, 12))
        layer.blit(cf, (0, 0))

    # ---- rupture spray of tar, gore, and golden light ----
    if 0.22 < b < 0.70:
        sp = ss((b - 0.22) / 0.48)
        cxr, cyr = ox, oy - 18
        rad = int(6 + sp * 30)
        for i in range(14):
            ang = i * (math.tau / 14) + t
            rr = rad * (0.55 + 0.45 * ((i * 7) % 5) / 5)
            px = int(cxr + math.cos(ang) * rr)
            py = int(cyr + math.sin(ang) * rr * 0.8)
            _pg.draw.circle(layer, (tar, gore, gold)[i % 3], (px, py), 2)
        gl = _pg.Surface((LW, LH), _pg.SRCALPHA)
        _pg.draw.circle(gl, (gold[0], gold[1], gold[2], int(120 * (1 - sp))),
                        (cxr, cyr), int(8 + sp * 10))
        layer.blit(gl, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)

    # ---- phase in and out of being (the original King's apparition
    # quality, merged in) -- only once born; the eruption stays solid.
    # Softened from the original so a hunting King never fully vanishes.
    if born:
        ph = 0.6 + 0.4 * math.sin(t * 1.7)
        if math.sin(t * 1.7) < -0.8:
            ph *= 0.4
        layer.set_alpha(max(45, int(255 * ph)))
    surf.blit(layer, (x - ox, y - oy))
