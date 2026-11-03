"""Action and arcade games (the "arcade" porting batch): single games pinned by commit or by
tarball hash, plus Shell Games, 25 small ncurses games built into one executable.

Paths that pointed at /var, /tmp or /usr are redirected into the game's home (its working
directory) with exact, checked substitutions, as in native/recipes/github.py."""
import os
import zipfile

from tk import (EXTRA_NOTICES, HERE, LEGACY, BuildError, compile_objects, copy_license, fetch, game, install_asset, link,
                replace_in, unpack)

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


@game("doom-ascii", curses=False, notice=("doom-ascii-940528f1.tar", "LICENSE"))
def build_doom_ascii(abi):
    """Doom (doomgeneric) drawn as coloured text, with the Freedoom: Phase 1 IWAD. It writes the
    frame itself (no curses) and reads keys from the terminal; savegames and its config go in
    the working directory (the game's home)."""
    work = abi.work("doom-ascii")
    src = unpack("doom-ascii-940528f1.tar", os.path.join(work, "src"))
    s = os.path.join(src, "src")
    # A fatal error spun forever at 100% CPU after printing its message; exit instead.
    replace_in(os.path.join(s, "i_system.c"), "    while (true)\n    {\n    }\n", "    exit(-1);\n")
    # Arrow keys come as ESC O A..D when the terminal is in application cursor mode; only the
    # ESC [ form was understood, so map the SS3 arrows too.
    replace_in(os.path.join(s, "doomgeneric_ascii.c"),
               "\tswitch (**buf) {\n\tcase 'P':\n\t\treturn KEY_F1;",
               "\tswitch (**buf) {\n\tcase 'A':\n\t\treturn KEY_UPARROW;\n\tcase 'B':\n\t\treturn KEY_DOWNARROW;\n"
               "\tcase 'C':\n\t\treturn KEY_RIGHTARROW;\n\tcase 'D':\n\t\treturn KEY_LEFTARROW;\n\tcase 'P':\n\t\treturn KEY_F1;")
    # Its config dir is "." joined without a separator: ".default.cfg", a hidden file that APK
    # packaging drops. "./" makes it "./default.cfg".
    replace_in(os.path.join(s, "m_config.c"), "    result[0] = '.';\n    result[1] = '\\0';",
               "    result[0] = '.';\n    result[1] = '/';\n    result = realloc(result, 3);\n    result[2] = '\\0';")
    # Saves in a visible savegame/ folder, like its config: the catalog lists save paths, and
    # hidden ones aren't allowed.
    replace_in(os.path.join(s, "m_config.c"), 'DIR_SEPARATOR_S, ".savegame/"', 'DIR_SEPARATOR_S, "savegame/"')
    srcs = DOOM_SRC.split()
    objs = compile_objects(abi, [os.path.join(s, f) for f in srcs], os.path.join(work, "obj"),
                           '-std=gnu99 -DNORMALUNIX -DLINUX -D_DEFAULT_SOURCE -DVERSION=0.3.2', cwd=s)
    exe = os.path.join(work, "game_doom_ascii")
    link(abi, objs, exe, "-lm")
    install_asset("games/doom-ascii/default.cfg", os.path.join(s, ".default.cfg"))
    install_asset("games/doom-ascii/freedoom1.wad", zip_member("freedoom-0.13.0.zip", "freedoom-0.13.0/freedoom1.wad",
                                                               os.path.join(work, "freedoom1.wad"), 40 << 20))
    EXTRA_NOTICES["doom-ascii"] = "\n\n---- Freedoom (freedoom1.wad) ----\n\n" + zip_text(
        "freedoom-0.13.0.zip", "freedoom-0.13.0/COPYING.txt")
    return {"game_doom_ascii": exe}


DOOM_SRC = """i_main.c dummy.c am_map.c doomdef.c doomstat.c dstrings.c d_event.c d_items.c d_iwad.c
    d_loop.c d_main.c d_mode.c d_net.c f_finale.c f_wipe.c g_game.c hu_lib.c hu_stuff.c info.c
    i_cdmus.c i_endoom.c i_joystick.c i_scale.c i_sound.c i_system.c i_timer.c memio.c m_argv.c
    m_bbox.c m_cheat.c m_config.c m_controls.c m_fixed.c m_menu.c m_misc.c m_random.c
    p_ceilng.c p_doors.c p_enemy.c p_floor.c p_inter.c p_lights.c p_map.c p_maputl.c p_mobj.c
    p_plats.c p_pspr.c p_saveg.c p_setup.c p_sight.c p_spec.c p_switch.c p_telept.c p_tick.c
    p_user.c r_bsp.c r_data.c r_draw.c r_main.c r_plane.c r_segs.c r_sky.c r_things.c sha1.c
    sounds.c statdump.c st_lib.c st_stuff.c s_sound.c tables.c v_video.c wi_stuff.c
    w_checksum.c w_file.c w_main.c w_wad.c z_zone.c w_file_stdc.c i_input.c i_video.c
    doomgeneric.c doomgeneric_ascii.c"""


def zip_member(name, member, dest, limit):
    """Extracts one file from a pinned zip, refusing anything bigger than limit (zip bombs)."""
    with zipfile.ZipFile(fetch(name)) as z:
        info = z.getinfo(member)
        if info.file_size > limit:
            raise BuildError(f"{name}: {member} is {info.file_size} bytes, over the {limit} limit")
        with z.open(info) as fh, open(dest, "wb") as out:
            data = fh.read(limit + 1)
            if len(data) > limit:
                raise BuildError(f"{name}: {member} is over the {limit} limit")
            out.write(data)
    return dest


def zip_text(name, member):
    with zipfile.ZipFile(fetch(name)) as z:
        return z.read(member).decode("utf-8", "replace")


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
