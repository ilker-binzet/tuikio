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
    dict(id="angband", title="Angband", exe="game_angband", controls="dungeon8.v1", hide=["pickup"],
         keys=["Wield=w", "Take off=T", "Eat=E", "Quaff=q", "Read=r", "Fire=t", "Cast=m", "Look=x", "Map=M",
               "Rest=R", "Character=C", "Help=?"],
         summary="The great Tolkien roguelike: 100 levels down to Morgoth, Lord of Darkness.",
         description="Create a character, buy supplies in the town, then descend. The pad walks (diagonals too) with "
                     "the roguelike keyset; the buttons cover the common commands and ? lists them all.",
         category="roguelike", tags=["roguelike", "dungeon", "tolkien"],
         authors=["Robert Alan Koeneke", "Ben Harrison", "the Angband team"], license="GPL-2.0-only",
         **gh("angband/angband", "e473720e"), discovery="angband",
         saves=(["angband/Angband/save/PLAYER", "angband/Angband/scores.raw"], "Saved character and scores"),
         test_notes="Host test: splash, character creation, the town."),
    dict(id="rogue", title="Rogue", exe="game_rogue", controls="dungeon8.v1", hide=["more"],
         keys=["Quaff=q", "Read=r", "Eat=e", "Wield=w", "Wear=W", "Take off=T", "Ring on=P", "Ring off=R",
               "Throw=t", "Zap=z", "Save=S", "Help=?"],
         summary="The 1980 original that named a genre: find the Amulet of Yendor.",
         description="Rogue 5.4.4. The pad walks, diagonals too; the buttons cover its one-letter commands, and "
                     "Save keeps your game for later.",
         category="roguelike", tags=["roguelike", "dungeon", "classic"],
         authors=["Michael Toy", "Glenn Wichman", "Ken Arnold"], license="BSD-3-Clause",
         **gh("Davidslv/rogue", "f4653c2a"), discovery="rogue",
         saves=(["rogue.save", "rogue.scr"], "Saved game and scores"),
         test_notes="Host test: first room, walking, status line."),
    dict(id="npush", title="nPush", exe="game_npush", controls="arrows.v1", labels={"select": "Action"},
         hide=["space", "back"], keys=["Switch=<TAB>", "Undo=u", "Quit=q"],
         summary="Push rocks, collect gold, blow your way out with dynamite: 18 hand-made puzzles.",
         description="A Sokoban-like puzzle game: gather every piece of gold, then reach the exit. Rocks can be pushed "
                     "or blasted; some levels give you several characters to switch between. Undo takes a move back.",
         category="puzzle", tags=["sokoban", "puzzle", "dynamite"], authors=["the nPush developers"],
         license="GPL-2.0-or-later", source_url="https://npush.sourceforge.net/", version="0.7",
         archive="npush-0.7.tgz", discovery="npush",
         test_notes="Host test: level list, level 1, moving."),
    dict(id="asciiportal", title="ASCIIpOrtal", exe="game_asciiportal", controls="pad-fire.v1",
         labels={"fire": "Portal"}, hide=["quit"],
         keys=["Blue=z", "Yellow=x", "Clear=c", "Restart=r", "Menu=<ESCAPE>"],
         summary="Portal as an ASCII puzzle platformer: two portals, boulders, buttons and a lot of falling.",
         description="Run with the pad, climb ladders with up and down; up and down also aim. Portal fires the next "
                     "portal, Blue and Yellow fire one of each, Clear removes them. Fling yourself through the test "
                     "chambers: over 200 levels in many map packs (Change Map Set in the menu).",
         category="puzzle", tags=["portal", "platformer", "puzzle"],
         authors=["Joe Larson", "the ASCIIpOrtal contributors"], license="GPL-3.0-only AND MIT",
         **gh("cymonsgames/ASCIIpOrtal", "0d7fb094", "asciiportal"), discovery="asciiportal",
         saves=(["asciiportal"], "Progress in each map pack"),
         test_notes="Host test in a PTY at 80x24: title, menu, the first test chamber, moving. Built without SDL "
                    "or sound; fixed two functions that fell off their end (the game crashed on loading a map)."),
    dict(id="gnuski", title="GNUSki", exe="game_gnuski", controls="arrows4.v1",
         summary="A SkiFree clone: race downhill between trees and rocks, and outrun the snowman.",
         description="Left and right lean the skier, up slows down, down speeds up. Quit ends the run.",
         category="arcade", tags=["skiing", "skifree", "classic"], authors=["Rudolf Olah"], license="GPL-2.0-or-later",
         source_url="https://sourceforge.net/projects/gnuski/", version="0.3", archive="gnuski-0.3.tar.gz",
         discovery="gnuski",
         test_notes="Host test in a PTY at 80x24: start, leaning, crash and score."),
    dict(id="cnibbles", title="cNibbles", exe="game_cnibbles", controls="arrows4.v1", keys=["Pause=p"],
         terminal=((80, 25), (80, 25)),
         summary="Nibbles in the terminal: steer the worm to the food and don't bite yourself.",
         description="The pad steers. Pause pauses, Quit ends the game. High scores and replays are kept.",
         category="arcade", tags=["snake", "nibbles", "classic"], authors=["Daniel Aarno"], license="AFL-1.2",
         source_url="https://cnibbles.sourceforge.net", version="2.0.1", archive="cNibbles-2.0.1.tbz",
         discovery="cnibbles", saves=(["cNibbles"], "High scores and replays"),
         test_notes="Host test in a PTY at 80x25: intro, game, steering. Needs 25 rows."),
    dict(id="ascii-dash", title="ASCII DASH", exe="game_ascii_dash", controls="pad-fire.v1",
         labels={"fire": "Dig", "ok": "Dynamite"}, hide=["quit"], keys=["Pause=p", "End=e"],
         terminal=((92, 29), (92, 29)),
         summary="Boulder Dash I in ASCII: dig through the caves, grab the diamonds, mind the boulders.",
         description="The pad moves Rockford. Dig, then a direction, digs without moving; Dynamite, then a "
                     "direction, drops dynamite. In the start cave, walk onto a menu number to choose it. "
                     "Pause pauses, End ends the game. The 20 caves of Boulder Dash I.",
         category="arcade", tags=["boulder dash", "puzzle", "classic"], authors=["Stefan Roettger"], license="MIT",
         source_url="https://sourceforge.net/projects/ascii-dash/", version="1.3", archive="ASCII-DASH-1.3.zip",
         discovery="ascii-dash", saves=(["dash.txt"], "High score"),
         test_notes="Host test in a PTY at 92x29: the start cave, moving and digging. No sound (SDL) in this build."),
]
