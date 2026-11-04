"""GNU's board games (native/recipes/gnu.py)."""

DEFAULTS = dict(
    recipe="native/recipes/gnu.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-04",
    discovery_notes="Ported to Tuikio from the Ubuntu 24.04 source package.",
)

GAMES = [
    dict(id="gnu-shogi", title="GNU Shogi", exe="game_gnushogi", controls="text.v1", input="typing", args=["-C"],
         keys=["Hint=hint\r", "Undo=undo\r", "Switch=switch\r", "New=new\r"],
         summary="Japanese chess against the computer, on a curses board.",
         description="Pick a level (1 is quickest), then type moves as from and to squares, such as 7g7f; drop a "
                     "captured piece with its letter and a square, such as P*5e. Hint suggests a move.",
         category="strategy", tags=["shogi", "japanese chess", "strategy"],
         authors=["Matthias Mutz", "Mike Vanier", "Yann Dirson", "the GNU Chess team"], license="GPL-3.0-or-later",
         source_url="https://www.gnu.org/software/gnushogi/", version="1.5~git20140725",
         archive="gnushogi_1.5~git20140725.orig.tar.gz", discovery="gnu-shogi",
         test_notes="Host test: level, board, a move and the computer's reply."),
]
