"""Entry point for Threshold. Run from the repository root:

    python main.py

Requires pygame (see requirements.txt). The game opens on the title
screen -- choose New Save to begin. Saving happens in-world by sleeping
at the cot; there is no quicksave.
"""
from systems.game import Game

if __name__ == "__main__":
    Game().run()
