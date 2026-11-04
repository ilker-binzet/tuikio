"""Python games (native/recipes/python.py): run by the bundled CPython 3.13 in libgame_python.so,
which imports only from the archive appended to it (the standard library and the games' pinned
code) and has no socket, subprocess or ctypes modules (docs/RUNTIME.md, "Python games")."""

DEFAULTS = dict(
    recipe="native/recipes/python.py",
    exe="game_python",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-04",
    discovery_notes="Ported to Tuikio from the upstream repository, pinned by commit; runs on the bundled CPython "
                    "3.13 (libgame_python.so), which only imports the code built into it.",
)


def gh(repo, commit, name):
    return dict(source_url=f"https://github.com/{repo}", version=f"git {commit}", archive=f"{name}-{commit}.tar")


GAMES = [
    dict(id="pokete", title="Pokete", args=["pokete"], controls="wasd4.v1", labels={"quit": "Back"},
         keys=["OK=<ENTER>", "Menu=e", "#1-6", "Help=?"], orientation="landscape", terminal=((70, 20), (80, 24)),
         summary="A Pokémon-like adventure in the terminal: catch Poketes, train them and battle other trainers.",
         description="Walk with the pad, OK talks and confirms, Back cancels. In battle 1-4 pick an attack; on the "
                     "map 1 opens your deck, 3 the map, 4 the inventory, 5 the Pokedex. Menu has settings and saving. "
                     "Version 0.9.2 without music (the player is a desktop library) and without trading over the "
                     "network (Tuikio games are offline).",
         category="adventure", tags=["rpg", "monsters", "python"], authors=["lxgr-linux"], license="GPL-3.0-only",
         **gh("lxgr-linux/pokete", "fc28e8a9", "pokete"),
         saves=(["pokete/pokete.json"], "Your trainer, Poketes and progress"),
         test_notes="Host test in a PTY at 80x24: loading screen, the house, naming the trainer. Music and LAN "
                    "trading removed; the old save format that ran Python code is never loaded."),
    dict(id="lightcycle", title="Lightcycle", args=["lightcycle"], controls="arrows.v1", labels={"select": "Go"},
         hide=["back"], keys=["Quit=q"],
         summary="Light cycles on the grid: box in the computer's trail before it boxes in yours.",
         description="The pad steers; you can't turn back on yourself. Go starts from the menu, where you can also "
                     "pick colours, speed and the computer's skill.",
         category="arcade", tags=["tron", "snake", "python"], authors=["gsobell"], license="GPL-3.0-only",
         **gh("gsobell/lightcycle", "48897113", "lightcycle"),
         test_notes="Host test in a PTY at 80x24: menu, start, steering, crash."),
    dict(id="pythrees", title="PyThrees", args=["pythrees"], controls="arrows4.v1", orientation="portrait",
         terminal=((33, 24), (40, 26)),
         summary="Threes in Python: slide the board, add 1 and 2 to make 3, then match the threes.",
         description="Every move slides the whole board one step and a new tile comes in (shown on top). 1 and 2 "
                     "make 3; from then on only equal numbers merge.",
         category="puzzle", tags=["threes", "numbers", "sliding", "python"], authors=["Yuan Cao"], license="MIT",
         **gh("yth/pythrees", "3610a53a", "pythrees"),
         test_notes="Host test in a PTY at 80x24: board, next tile, moves."),
    dict(id="penneys-game", title="Penney's Game", args=["penneys-game"], controls="text.v1", input="typing",
         wrap="words", orientation="portrait", terminal=((48, 24), (48, 30)),
         summary="Penney's coin game: pick a heads-and-tails sequence and see whose shows up first.",
         description="You and the computer (or friends) each choose a sequence like HTH; a coin is tossed until one "
                     "appears. Type your answers and press Enter.",
         category="puzzle", tags=["coins", "probability", "python"], authors=["Sepand Haghighi"], license="MIT",
         **gh("sepandhaghighi/penney", "9e3fd77c", "penney"), discovery="penneys-game",
         test_notes="Host test in a PTY: description, the ASCII-art menu, a game against the computer."),
    dict(id="dango", title="Dango (Go board)", args=["dango"], controls="arrows.v1", labels={"select": "Place"},
         hide=["back"], keys=["Pass=p", "Undo=u", "Quit=q"],
         summary="A Go board for two players on one phone, with captures, ko and scoring.",
         description="Move the cursor with the pad and Place puts a stone; players take turns. Pass twice to end "
                     "the game. Choose the board size (9, 13, 19) and komi in the menu.",
         category="strategy", tags=["go", "baduk", "two-player", "python"], authors=["gsobell"], license="GPL-3.0-only",
         players="2", **gh("gsobell/dango", "18d2f72b", "dango"),
         test_notes="Host test in a PTY at 80x24: menu, the 19x19 board, placing stones."),
]
