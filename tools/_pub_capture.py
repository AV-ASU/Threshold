"""Publisher-review capture: shoots the game as a player actually sees it.

Boots a real Game headless in the DEFAULT tilted camera, captures the title
screen and a spread of scenes via draw_world(), plus a King-threat moment.
"""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["PYTHONHASHSEED"] = "0"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import random, pygame
pygame.init()

OUT = "/tmp/pub"
os.makedirs(OUT, exist_ok=True)

from systems.game import Game

def newsurf(g):
    s = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = s
    return s

def main():
    g = Game()
    g.save.new()

    # --- Title screen ---
    s = newsurf(g)
    try:
        g.draw_title()
        pygame.image.save(s, f"{OUT}/00_title.png")
        print("title ok")
    except Exception as e:
        print("title FAIL", e)

    g._start_play()  # tilted by default

    scenes = [
        ("bedroom", "10_bedroom"),
        ("brimley", "11_brimley_town"),
        ("arrival_road", "12_arrival_road"),
        ("cornfield_maze", "13_cornfield"),
        ("well_bottom", "14_well_bottom"),
        ("works_vats", "15_works_vats"),
        ("works_sign", "16_works_sign"),
        ("depths_hall", "17_depths_hall"),
        ("threshold", "18_threshold"),
        ("effigy_grove", "19_effigy_grove"),
    ]
    for key, name in scenes:
        random.seed(7)
        try:
            g.load_scene_now(key)
            g._update_camera(snap=True)
            random.seed(7)
            s = newsurf(g)
            g.draw_world()
            pygame.image.save(s, f"{OUT}/{name}.png")
            print(name, "ok")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(name, "FAIL", e)

    # --- King threat moment in brimley ---
    try:
        random.seed(7)
        g.load_scene_now("brimley")
        g._update_camera(snap=True)
        g.save.data["visibility"] = 1.0
        g.visibility = 1.0
        # force-materialize the roaming King near the player so he's framed
        g._roam_king["armed"] = True
        g._materialize_roam_king()
        if getattr(g, "_king", None):
            # plant him a few tiles in front of the player, fully manifested
            from scenes.base import TILE
            g._king.x = g.player.x + TILE * 3
            g._king.y = g.player.y + TILE * 2
            g._king._birth = 1.0
        s = newsurf(g)
        g.draw_world()
        pygame.image.save(s, f"{OUT}/20_king_threat.png")
        print("king ok", "spawned=", getattr(g, "_king", None) is not None)
    except Exception as e:
        import traceback; traceback.print_exc()
        print("king FAIL", e)

if __name__ == "__main__":
    main()
