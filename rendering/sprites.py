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
        # The Yellow King avatar. A jaundiced, pulpy mass of eyes, a
        # tearing toothed maw, and oozing tentacles that PHASES in and
        # out of being on a slow sine -- some seconds you can almost
        # not see it. Gore pass: dark veins crawl the body, the maw
        # gapes on its own cycle, and arterial ichor weeps down and
        # drips off the underside. Rendered onto a SRCALPHA layer so
        # the whole sprite alpha-pulses together.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        # Phase: 0..1, where 0 is nearly transparent, 1 is solid.
        phase = 0.55 + 0.45 * math.sin(t * 1.7)
        # Brief "blink-out" at the troughs so the figure genuinely
        # vanishes for an instant -- not just a soft alpha pulse.
        if math.sin(t * 1.7) < -0.8:
            phase *= 0.15
        layer = _pg.Surface((64, 82), _pg.SRCALPHA)
        lx, ly = 32, 60     # local origin (feet)
        body_yellow = (210, 190, 60)
        body_dark = (120, 95, 28)
        ichor = (152, 30, 24)       # dark arterial red
        ichor_lo = (92, 14, 12)
        eye_white = (240, 230, 160)
        eye_pupil = (20, 12, 0)
        # Lurching, asymmetrical blob body. Two stacked ellipses
        # so the silhouette feels "wrong-shouldered."
        _pg.draw.ellipse(layer, body_yellow, (lx - 16, ly - 38, 32, 30))
        _pg.draw.ellipse(layer, body_dark, (lx - 16, ly - 38, 32, 30), 1)
        _pg.draw.ellipse(layer, body_yellow, (lx - 14, ly - 22, 28, 26))
        _pg.draw.ellipse(layer, body_dark, (lx - 14, ly - 22, 28, 26), 1)
        # Veins -- dark-red threads crawling over the mass, twitching.
        for i in range(5):
            vx = lx - 10 + i * 5
            vy = ly - 34 + (i % 2) * 4
            _pg.draw.line(layer, ichor_lo, (vx, vy),
                          (vx + int(math.sin(t * 1.1 + i) * 2), vy + 12), 1)
        # A tearing maw low on the body: a vertical split that gapes on
        # its own cycle, lined with wet teeth.
        gape = 2 + int((math.sin(t * 1.9) * 0.5 + 0.5) * 6)
        mcx, mcy = lx, ly - 6
        _pg.draw.ellipse(layer, (15, 6, 4), (mcx - gape, mcy - 9, gape * 2, 18))
        for tj in range(-gape + 1, gape, 3):
            _pg.draw.polygon(layer, (235, 225, 200),
                             [(mcx + tj, mcy - 8), (mcx + tj + 1, mcy - 4),
                              (mcx + tj + 2, mcy - 8)])
            _pg.draw.polygon(layer, (235, 225, 200),
                             [(mcx + tj, mcy + 8), (mcx + tj + 1, mcy + 4),
                              (mcx + tj + 2, mcy + 8)])
        # Mass of eyes scattered across the body, blinking on
        # staggered cycles -- never all open at once.
        eye_pos = [
            (-10, -32), (0, -34), (10, -32),
            (-12, -24), (-2, -26), (8, -24),
            (-9, -16), (1, -18), (11, -16),
            (-6, -10), (4, -12),
        ]
        for i, (ex, ey) in enumerate(eye_pos):
            if (t * 1.3 + i * 0.7) % 4.0 < 0.25:
                continue        # this eye is shut
            cx = lx + ex
            cy = ly + ey
            _pg.draw.circle(layer, eye_white, (cx, cy), 2)
            # Pupil tracks toward the player (facing direction).
            fx, fy = facing
            _pg.draw.circle(layer, eye_pupil,
                            (cx + int(fx), cy + int(fy)), 1)
        # Tentacles. Four wavering legs trailing from the bottom of
        # the body to the ground -- they don't stride, they pulse.
        for i in range(4):
            base_x = lx + (i - 1.5) * 6
            base_y = ly - 4
            for s_step in range(0, 18, 2):
                wob = math.sin(t * 2.4 + i * 1.1 + s_step * 0.3) * 2
                seg_x = int(base_x + wob)
                seg_y = base_y + s_step
                _pg.draw.line(layer, body_dark,
                              (seg_x, seg_y), (seg_x, seg_y + 2), 2)
            _pg.draw.circle(layer, body_dark,
                            (int(base_x + math.sin(t * 2.4 + i) * 2),
                             ly + 14), 2)
        # Ichor drips: red beads welling and sliding down on a loop.
        for i in range(3):
            dphase = (t * 0.8 + i * 0.6) % 1.0
            dx = lx - 8 + i * 8
            dy = ly - 2 + int(dphase * 16)
            _pg.draw.circle(layer, ichor, (dx, dy), 2)
            _pg.draw.circle(layer, ichor_lo, (dx, dy), 2, 1)
        # Sickly halo behind the body so it reads even when low-alpha.
        halo = _pg.Surface((64, 82), _pg.SRCALPHA)
        _pg.draw.ellipse(halo, (210, 190, 60, 50),
                         (lx - 22, ly - 42, 44, 50))
        layer.blit(halo, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)
        layer.set_alpha(int(255 * phase))
        surf.blit(layer, (x - lx, y - ly))
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
        # Hooded cultist -- coarse robe, deep cowl, the cult has erased
        # his face but for two dim eyes that catch the light in the
        # cowl-shadow. Breathes and sways on a slow cycle so even an
        # idling figure reads as alive and coming for you. A crusted
        # dark stain runs down the robe.
        t = pygame.time.get_ticks() / 1000.0
        lean = int(math.sin(t * 1.6 + x * 0.02))         # upper-body sway
        breathe = int((math.sin(t * 2.2) * 0.5 + 0.5))   # hood rise/fall
        robe = (96, 84, 62)
        robe_lo = (60, 52, 38)
        cowl = (38, 32, 22)
        # Body (shoulders sway via `lean`).
        pygame.draw.polygon(surf, robe,
                            [(x - 9, y + 16), (x - 7 + lean, y - 10),
                             (x + 7 + lean, y - 10), (x + 9, y + 16)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 9, y + 16), (x - 7 + lean, y - 10),
                             (x + 7 + lean, y - 10), (x + 9, y + 16)], 1)
        # Hood
        pygame.draw.ellipse(surf, cowl,
                            (x - 7 + lean, y - 18 - breathe, 14, 12))
        # Two dim eyes in the cowl shadow, blinking together on a cycle.
        if (t + x * 0.05) % 3.4 > 0.18:
            ey = y - 13 - breathe
            pygame.draw.circle(surf, (168, 148, 70), (x - 3 + lean, ey), 1)
            pygame.draw.circle(surf, (168, 148, 70), (x + 3 + lean, ey), 1)
        # Crusted blood up the robe + dark hem.
        pygame.draw.line(surf, (74, 22, 18), (x, y + 4), (x + 1, y + 14), 2)
        pygame.draw.line(surf, (40, 25, 20),
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
        # Raised hands, mid-rite, ichor beading off the fingertips.
        for s in (-1, 1):
            hx = x + s * (10 + int(sway * s))
            hy = y - 6 + int(math.sin(t * 1.7 + s) * 1)
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
        # A vertical row of small yellow curse-eyes down the chest,
        # blinking on staggered cycles -- the curse, looking out.
        for i in range(3):
            if (t * 1.1 + i * 0.8) % 3.0 > 0.3:
                pygame.draw.circle(surf, (210, 185, 70), (x + lean, y - 6 + i * 6), 1)
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
        # A Watcher -- the curse made flesh. A bloodshot, weeping eye
        # that hangs in the air and stares: a fleshy sclera laced with
        # red veins, a yellow iris that dilates, and a blood tear that
        # wells and falls on a loop. It blinks shut on a slow cycle,
        # and clenches shut the instant the player looks straight at it
        # (gaze=True). Only the cursed see them.
        t = pygame.time.get_ticks() / 1000.0
        bob = int(math.sin(t * 1.4 + x * 0.013) * 2)
        layer = pygame.Surface((40, 40), pygame.SRCALPHA)
        cx = 20
        cy = 20 + bob
        sclera = (200, 180, 150, 235)       # sickly fleshy white
        sclera_lo = (120, 95, 80, 235)
        vein = (150, 40, 34, 235)
        pygame.draw.circle(layer, sclera, (cx, cy), 14)
        pygame.draw.circle(layer, sclera_lo, (cx, cy), 14, 1)
        # Bloodshot veins crawling in from the rim.
        for i in range(7):
            ang = t * 0.3 + i * (math.tau / 7)
            ex = cx + int(math.cos(ang) * 13)
            ey = cy + int(math.sin(ang) * 13)
            mx = cx + int(math.cos(ang) * 6)
            my = cy + int(math.sin(ang) * 6)
            pygame.draw.line(layer, vein, (ex, ey), (mx, my), 1)
        if gaze or (t + x * 0.02) % 4.2 < 0.2:
            # Lid clenched shut -- a wet seam.
            pygame.draw.line(layer, (70, 40, 36, 255),
                             (cx - 13, cy), (cx + 13, cy), 3)
        else:
            irad = 7 + int(math.sin(t * 1.3))             # iris dilates
            pygame.draw.circle(layer, (200, 175, 60, 255), (cx, cy), irad)
            pygame.draw.circle(layer, (240, 220, 110, 255), (cx, cy), irad, 1)
            prad = max(2, irad - 4 + int(math.sin(t * 0.9)))
            pygame.draw.circle(layer, (8, 6, 0, 255), (cx, cy), prad)
            pygame.draw.circle(layer, (255, 250, 220, 255), (cx - 2, cy - 2), 1)
            halo = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(halo, (200, 175, 60, 55), (cx, cy), 18)
            layer.blit(halo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        # Blood tear: a bead welling at the base and falling on a loop.
        tphase = (t * 0.7 + x * 0.05) % 1.0
        ty = cy + 8 + int(tphase * 16)
        pygame.draw.circle(layer, (150, 30, 28, 255), (cx + 3, ty), 2)
        pygame.draw.circle(layer, (90, 16, 14, 255), (cx + 3, ty), 2, 1)
        surf.blit(layer, (x - 20, y - 28))
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
