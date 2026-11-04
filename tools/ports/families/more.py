"""More single games (native/recipes/more.py)."""

DEFAULTS = dict(
    recipe="native/recipes/more.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-04",
    discovery_notes="Ported to Tuikio from the upstream source, pinned by commit or hash.",
)


def gh(repo, commit, name=None):
    name = name or repo.split("/")[1].lower()
    return dict(source_url=f"https://github.com/{repo}", version=f"git {commit}", archive=f"{name}-{commit}.tar")


GAMES = [
    dict(id="brogue-community-edition", title="Brogue: Community Edition", exe="game_brogue", controls="dungeon8.v1",
         hide=["pickup"], terminal=((100, 34), (100, 34)),
         keys=["Explore=x", "Rest=z", "Equip=e", "Remove=r", "Apply=a", "Throw=t", "Drop=d", "Help=?"],
         summary="A tight, beautiful roguelike: 26 floors down for the Amulet of Yendor.",
         description="Brogue's dungeons are full of light, gas, fire and allies. The pad walks (diagonals too); "
                     "Explore walks to unexplored ground on its own; Down (>) travels to the stairs. The bar at the bottom "
                     "of the screen can be tapped.",
         category="roguelike", tags=["roguelike", "dungeon", "brogue"],
         authors=["Brian Walker", "the Brogue CE team"], license="AGPL-3.0-or-later",
         **gh("tmewett/BrogueCE", "363440c4", "brogue-ce"), discovery="brogue-community-edition",
         saves=(["BrogueHighScores.txt", "LastGame.broguesave"], "High scores and the saved game"),
         test_notes="Host test: new game, first floor, a step and explore."),
    dict(id="viper-snake", title="VIper", exe="game_viper", controls="arrows4.v1", orientation="portrait",
         terminal=((40, 24), (40, 24)), keys=["Restart=r", "Pause=p"],
         summary="Snake in Unicode, with fruit, bonuses and a speed that keeps rising.",
         description="Steer with the pad and eat the fruit; some foods slow you down or shorten the snake. "
                     "Restart after a crash.",
         category="arcade", tags=["snake", "classic"], authors=["Tobias Girstmair"], license="GPL-3.0-only",
         **gh("girst/viper", "edd02980"), discovery="viper-snake",
         test_notes="Host test: field, food, steering, game over and restart."),
    dict(id="open-adventure", title="Open Adventure", exe="game_advent", controls="text.v1", input="typing",
         wrap="words", orientation="portrait", terminal=((48, 32), (48, 32)),
         summary="Colossal Cave Adventure, the 430-point version, kept alive by its original authors' blessing.",
         description="The 1977 adventure that started it all, in the version Crowther and Woods last released, "
                     "maintained by Eric S. Raymond. Type commands of one or two words: north, take lamp, xyzzy. "
                     "Save and resume cost a few points, as in the original.",
         category="adventure", tags=["text adventure", "interactive fiction", "classic"],
         authors=["Will Crowther", "Don Woods", "Eric S. Raymond"], license="BSD-2-Clause",
         source_url="https://gitlab.com/esr/open-adventure", version="git e6160529",
         archive="open-adventure-e6160529.tar", discovery="open-adventure",
         test_notes="Host test: instructions, building, inventory, save prompt."),
    dict(id="zigtris", title="Zigtris", exe="game_zigtris", controls="blocks.v1", orientation="portrait", hide=["ok", "back", "pause"],
         terminal=((40, 24), (40, 24)),
         summary="A compact Tetris written in Zig.",
         description="Left and right slide, up rotates, down drops faster and Drop sends the piece down.",
         category="arcade", tags=["blocks", "tetris", "zig"], authors=["Ringtail Software"], license="MIT",
         **gh("ringtailsoftware/zigtris", "60206d8f"), discovery="zigtris",
         test_notes="Host test: well, pieces fall, moves and drops."),
]
