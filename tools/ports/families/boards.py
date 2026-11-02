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
]
