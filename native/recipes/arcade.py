"""Action and arcade games (the "arcade" porting batch): single games pinned by commit or by
tarball hash, plus Shell Games, 25 small ncurses games built into one executable.

Paths that pointed at /var, /tmp or /usr are redirected into the game's home (its working
directory) with exact, checked substitutions, as in native/recipes/github.py."""
import os

from tk import HERE, LEGACY, compile_objects, copy_license, game, link, replace_in, unpack

PORTS = os.path.join(HERE, "ports")


# ---------------------------------------------------------------- Shell Games

SHELLGAME = "shellgame-dd1aa485.tar"
SHELLGAME_GAMES = ("asteroids", "blackjack", "breakout", "centipede", "checkers", "chess", "digdug", "donkeykong",
                   "duckhunt", "enduro", "frogger", "galaga", "game2048", "hangman", "minesweeper", "paciencia",
                   "pacman", "pong", "qbert", "rhythm", "snake", "spire", "superautopets", "tetris", "typer")
SHELLGAME_FIXES = [
    # Hangman: q quit at once, so "queen" could never be finished. While a word is open q is a
    # guess like any letter; Esc quits (and q still does after the game).
    ("hangman.c", "        if (ch == 'q') break;\n", "        if (ch == 27 || (ch == 'q' && game_over)) break;\n"),
    ("hangman.c", '_("Q: quit", "Q: sair")', '_("Esc: quit", "Esc: sair")'),
    # Hangman: the win/loss tally was drawn over the title ("HAW: 0  L: 0"); one row lower.
    ("hangman.c", "    mvaddstr(oy, wx, buf);\n", "    mvaddstr(oy + 1, wx, buf);\n"),
    # Rhythm Spire: the title shared a row with the score ("Combo: x0PIRE"); one row higher.
    ("rhythm.c", 'mvaddstr(oy - 1, ox + cw / 2 - 7, _("RHYTHM SPIRE"', 'mvaddstr(oy - 2, ox + cw / 2 - 7, _("RHYTHM SPIRE"'),
    # Solitaire: the title sat under the pile labels ("SSLITAIWE"); moved right of the
    # foundations, on the same row.
    ("paciencia.c", 'mvaddstr(0, 2, _("SOLITAIRE", "PACIENCIA"));', 'mvaddstr(0, 44, _("SOLITAIRE", "PACIENCIA"));'),
    # Solitaire: a card's suit was one byte cut out of the UTF-8 string "♠♣♥♦", so every card
    # showed a broken character instead of its suit (on any terminal); copy the whole symbol.
    ("paciencia.c", "    char s = SUIT_CH[c.suit];\n"
                    "    if (c.rank == 10) { buf[0] = '1'; buf[1] = '0'; buf[2] = s; buf[3] = 0; }\n"
                    "    else { buf[0] = RANK_CH[c.rank]; buf[1] = s; buf[2] = ' '; buf[3] = 0; }\n",
     '    static const char *suit[] = {"\\xe2\\x99\\xa0", "\\xe2\\x99\\xa3", "\\xe2\\x99\\xa5", "\\xe2\\x99\\xa6"};\n'
     '    (void)SUIT_CH;\n'
     '    if (c.rank == 10) snprintf(buf, 16, "10%s", suit[c.suit]);\n'
     '    else snprintf(buf, 16, "%c%s ", RANK_CH[c.rank], suit[c.suit]);\n'),
    # The Typer drew its lives as '<' + 3, which is '?' ("Lives: ???"); a star per life instead.
    ("typer.c", "mvaddch(oy + 1, ox + strlen(buf) + i, '<' + 3);", "mvaddch(oy + 1, ox + strlen(buf) + i, '*');"),
    # Chess and Checkers centred only the board, so the info panel beside and below it ran off
    # the screen; centre the whole layout (board and panel: 54 columns, chess 22 rows).
    ("chess.c", "int oy = (LINES - 12) / 2;", "int oy = (LINES - 22) / 2;"),
    ("chess.c", "int ox = (COLS - 40) / 2;", "int ox = (COLS - 54) / 2;"),
    ("checkers.c", "draw((COLS - 44) / 2 < 1 ? 1 : (COLS - 44) / 2,", "draw((COLS - 54) / 2 < 1 ? 1 : (COLS - 54) / 2,"),
    # Tetris centred the well alone, and its side panel (next piece, score, keys) wrapped at the
    # right edge of a phone-width terminal; centre well and panel together (37 columns).
    ("tetris.c", "int ox = (COLS - W * 2 - 2) / 2;", "int ox = (COLS - 37) / 2;"),
    # Spire Ascent: the map's key line sat ten rows below the relics list, past the bottom of
    # any phone-sized terminal; it follows the list now.
    ("spire.c", "int by2 = rel_y + 10;", "int by2 = rel_y + 2 + (relic_sz > 0 ? relic_sz : 1);"),
]


@game("shell-games")
def build_shellgame(abi):
    """Upstream builds 25 programs and a menu that starts them with system(). Each game's main()
    becomes sg_<name>_main and native/ports/shellgame/shellgame.c starts the one named by its
    first argument: one small binary, and one catalog game per title. Every game keeps its state
    in file-local statics (main() is each file's only global symbol), so they link together
    cleanly. menu.c is left out: the catalog lists the games, and it can't start them here."""
    work = abi.work("shell-games")
    src = unpack(SHELLGAME, os.path.join(work, "src"))
    for rel, old, new in SHELLGAME_FIXES:
        replace_in(os.path.join(src, rel), old, new)
    port = os.path.join(PORTS, "shellgame")
    objs = []
    for g in SHELLGAME_GAMES:
        objs += compile_objects(abi, [os.path.join(src, f"{g}.c")], os.path.join(work, "obj"),
                                f"-I{src} -include {port}/sg_input.h -Dmain=sg_{g}_main", cwd=src)
    objs += compile_objects(abi, [os.path.join(PORTS, "shellgame", "shellgame.c")], os.path.join(work, "obj"))
    exe = os.path.join(work, "game_shellgame")
    link(abi, objs, exe, f"{abi.curses_libs} -lm")
    # The repository has no licence text; its PKGBUILD names MIT (see the notice for details).
    copy_license("shell-games", os.path.join(PORTS, "shellgame", "LICENSE"))
    return {"game_shellgame": exe}
