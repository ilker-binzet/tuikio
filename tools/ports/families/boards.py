"""Board, card and puzzle games of the "boards" batch (native/recipes/boards.py)."""

DEFAULTS = dict(
    recipe="native/recipes/boards.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-10-24",
    discovery_notes="Ported to Tuikio from pinned upstream sources (native/recipes/boards.py).",
)


def ubuntu(version, archive, url):
    return dict(source_url=url, version=version, archive=archive,
                discovery_notes="Ported to Tuikio from the Ubuntu 24.04 source package.")


def git(url, commit, archive):
    return dict(source_url=url, version=f"git {commit[:8]}", archive=archive,
                discovery_notes="Ported to Tuikio from the upstream repository, pinned by commit.")


GAMES = [
    # 54x24: it centres a 22-column well with a 16-column panel beside it, and needs 24 rows.
    dict(id="bastet", title="Bastet", exe="game_bastet", controls="bastet.v1", orientation="portrait",
         terminal=((54, 24), (54, 24)),
         summary="Bastard Tetris: it always picks the piece you least want.",
         description="A falling-blocks game whose block chooser studies the well and hands you the worst "
                     "possible piece. Left and right slide, Up and Turn rotate, Drop sends the piece down, Pause "
                     "stops the clock. The harder version doesn't even show the next piece.",
         category="arcade", tags=["blocks", "tetris", "evil"], authors=["Federico Poloni"],
         license="GPL-3.0-or-later", **ubuntu("0.43", "bastet_0.43.orig.tar.gz", "https://fph.altervista.org/prog/bastet.html"),
         saves=(["bastet.scores2", ".bastetrc"], "High scores and key settings"),
         test_notes="Host test: menu, a game played to the end with Drop, the high score table, back to the menu. "
                    "Boost 1.83 (headers and Program_options) is built in."),
    # It refuses to start below 80x24.
    dict(id="yetris", title="yetris", exe="game_yetris", controls="blocks.v1",
         labels={"ok": "OK"}, hide=["back"], keys=["Hold=c", "Turn left=z", "Pause=p", "Help=h"],
         summary="A full-featured Tetris clone: hold, ghost piece, statistics and colourful menus.",
         description="Pick Single Player, then Start Game. Up turns the piece, Drop hard-drops it, Hold keeps it "
                     "for later and OK pauses with a menu. Game settings set the starting level, noise and more; "
                     "your profile keeps scores and statistics.",
         category="arcade", tags=["blocks", "tetris", "hold"], authors=["Alexandre Dantas"],
         license="GPL-3.0-or-later",
         **git("https://github.com/alexdantas/yetris", "cf3fee6c2f1daf5b2c35468b9e211c2e87530a4f", "yetris-cf3fee6c.tar"),
         saves=([".local/share/yetris"], "Profile: settings, high scores and statistics"),
         test_notes="Host test: first-run profile prompt, main menu, a game with rotation, pause menu, game over "
                    "and restart at 80x24."),
    # Its screen is a fixed 65x21 layout (timer and score beside a 37-column grid).
    dict(id="nsuds", title="nsuds", exe="game_nsuds", controls="arrows.v1", terminal=((66, 22), (66, 22)),
         labels={"select": "OK"}, hide=["space", "back"],
         keys=["#1-9", "Delete=x", "Mark=m", "Pause=p", "New=n", "Scores=H", "Help=?", "Quit=q"],
         summary="Sudoku against the clock, with 30 levels and pencil marks.",
         description="Choose a difficulty, then fill the grid before the timer runs out: move with the pad and tap a "
                     "digit. Mark followed by a digit pencils it in; Help lists every command.",
         category="puzzle", tags=["sudoku", "logic", "numbers"], authors=["Vincent Launchbury"],
         license="GPL-2.0-or-later", source_url="https://sourceforge.net/projects/nsuds/", version="0.7B",
         archive="nsuds-0.7B.tar.gz", saves=(["nsuds/high_scores"], "High scores"),
         discovery_notes="Ported to Tuikio from the 0.7B release tarball on SourceForge.",
         test_notes="Host test: difficulty menu, a number entered and deleted, pause, help and the quit dialog at 66x22."),
    # An 18x24 field fills an upright 40x29 screen (it clamps any field to the terminal).
    dict(id="minesviiper", title="minesVIiper", exe="game_minesviiper", controls="space-select.v1",
         orientation="portrait", terminal=((40, 29), (40, 29)), args=["-c", "18x24"],
         labels={"space": "Open"}, hide=["enter", "back"],
         keys=["Flag=i", "Open/flag mode=s", "New=:n\\r", "Again=r", "Quit=:q\\r"],
         summary="Minesweeper with vi keys, chording and a colourful board.",
         description="Move with the pad, Open uncovers a square (or clears around a satisfied number) and Flag marks "
                     "a mine. After a win or a loss, Again deals a new board.",
         category="puzzle", tags=["minesweeper", "logic"], authors=["Tobias Girstmair"], license="GPL-3.0-only",
         **git("https://github.com/girst/minesviiper", "f39a17cdae0c4c5986f8b3f12146910300727b63", "minesviiper-f39a17cd.tar"),
         test_notes="Host test: 18x24 board at 40x29, open, flag, :n new game and :q quit."),
]

_SOL = dict(controls="space-select.v1", orientation="portrait", category="cards", authors=["Tobias Girstmair"],
            license="GPL-3.0-only", license_file="solvitaire.txt",
            **git("https://github.com/girst/solvitaire", "1883ee0c67f3e5f7807f7a886333360e31f804be", "solvitaire-1883ee0c.tar"))

GAMES += [
    dict(_SOL, id="solvitaire", title="solVItaire Klondike", exe="game_solvitaire", terminal=((36, 40), (36, 40)),
         labels={"space": "Select", "enter": "Draw"}, hide=["back"],
         keys=["Join here=J", "Undo=u", "New=:n\\r", "Restart=:r\\r", "Quit=:q\\r"],
         summary="Klondike solitaire with big Unicode cards.",
         description="Move the cursor with the pad and Select a pile, then Select where it goes (twice sends a card "
                     "home). Draw turns the stock; Join here pulls the matching run to the cursor.",
         tags=["solitaire", "klondike", "cards"],
         test_notes="Host test: deal, draw from the stock, select and move the cursor at 36x40."),
    dict(_SOL, id="solvitaire-spider", title="solVItaire Spider", exe="game_solvitaire_spider",
         terminal=((51, 40), (51, 40)), discovery_url="https://github.com/girst/solvitaire",
         labels={"space": "Select", "enter": "Deal"}, hide=["back"],
         keys=["Join here=J", "Undo=u", "New=:n\\r", "Restart=:r\\r", "Quit=:q\\r"],
         summary="Spider solitaire (two suits) with big Unicode cards.",
         description="Build runs from King down to Ace in the same suit to clear them. Select a card, then the pile "
                     "it goes to; Deal puts a new card on every pile.",
         tags=["solitaire", "spider", "cards"],
         test_notes="Host test: deal at 51x40 (ten piles)."),
    dict(_SOL, id="solvitaire-freecell", title="solVItaire FreeCell", exe="game_solvitaire_freecell",
         terminal=((41, 40), (41, 40)), discovery_url="https://github.com/girst/solvitaire",
         labels={"space": "Select"}, hide=["enter", "back"],
         keys=["Join here=J", "Undo=u", "New=:n\\r", "Restart=:r\\r", "Quit=:q\\r"],
         summary="FreeCell with big Unicode cards.",
         description="Every card is dealt face up: use the four free cells to move them home in order. Select a card, "
                     "then where it goes.",
         tags=["solitaire", "freecell", "cards"],
         test_notes="Host test: deal at 41x40."),
    # Its four 14-card rows are 70 columns wide, with the rules printed under them.
    dict(id="blue-moon-solitaire", title="Blue Moon", exe="game_bluemoon", controls="text.v1",
         hide=["enter", "space", "erase"], keys=["#a-d", "Redraw=r", "Quit=q"],
         summary="Eric Raymond's Blue Moon: line up all four suits in order across 13 deals.",
         description="The cards that can move into a gap are marked a to d under them: tap the letter. When nothing "
                     "can move, the cards out of sequence are dealt again. Fewer deals is better.",
         category="cards", tags=["solitaire", "patience", "cards"], authors=["Tim Lister", "Eric S. Raymond"],
         license="BSD-2-Clause",
         **git("https://gitlab.com/esr/bluemoon", "91ff5db75d1eccf9731d2373c7617d6dc1ee6656", "bluemoon-91ff5db7.tar"),
         discovery="blue-moon-solitaire", test_notes="Host test: deal 1 and a move at 80x24."),
    # Every source file and its own licence screen say GPL version 2 only; the 1.4.2 tarball's
    # COPYING holds the GPL 3 text (shipped as its notice, as it comes).
    dict(id="cpat-solitaire", title="CPat", exe="game_cpat", controls="text.v1",
         hide=["enter", "space", "erase"], keys=["#a-j", "p=p", "o=o", "Undo=u", "Help=?"],
         summary="Eleven solitaires in one: FreeCell, Klondike, Spider, Yukon, Canfield and more.",
         description="Pick a game from the menu. Moves are typed as source and destination letters, the columns a to "
                     "j (k to m for Baker's Dozen on the keyboard), p for the piles and o for the other spaces (an optional count first): 'ab' moves column a "
                     "onto b, 'oo' deals. Help and Rules explain each game.",
         category="cards", tags=["solitaire", "freecell", "klondike", "spider", "cards"],
         authors=["Trevor Carey-Smith"], license="GPL-2.0-only", source_url="https://cpat.sourceforge.net/",
         version="1.4.2", archive="cpat-1.4.2.tar.gz", saves=([".cpat_scores"], "High scores and statistics"),
         discovery_notes="Ported to Tuikio from the 1.4.2 release tarball on SourceForge.",
         test_notes="Host test: menu, Klondike dealt, a deal from the stock and the quit menu at 80x24."),
    # The 26-column board is centred and its move list hangs 18 columns off its right side: 62 wide.
    dict(id="nchess", title="NChess", exe="game_nchess", controls="arrows.v1", terminal=((62, 20), (62, 20)),
         labels={"select": "OK", "space": "Pick", "back": "Menu"}, players="2",
         summary="Two-player chess on one screen, with the moves listed beside the board.",
         description="For two players taking turns: move the cursor with the pad, Pick a piece and Pick the square "
                     "it goes to. Only legal moves are allowed. Menu pauses with Resume, Restart and Exit.",
         category="strategy", tags=["chess", "board", "two players"], authors=["Billy Vinning"],
         license="GPL-3.0-only",
         **git("https://github.com/billyvinning/nchess", "7489711575df0e6bb816724319854767a923039d", "nchess-74897115.tar"),
         test_notes="Host test: menu, a2a4 played and listed, the pause menu at 62x20."),
]
