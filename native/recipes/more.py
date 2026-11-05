"""More single games, pinned by commit (tools/ports/git_lock.py) or by archive hash, each built
from the file list its upstream makefile compiles."""
import glob
import os

import tk

from tk import EXTRA_NOTICES, HERE, LEGACY, BuildError, autotools, cc, game, install_asset, replace_in, run, unpack


def files(src, *patterns):
    out = []
    for p in patterns:
        out += sorted(glob.glob(os.path.join(src, p), recursive=True))
    if not out:
        raise BuildError(f"no sources match {patterns}")
    return out


@game("brogue-community-edition", notice=("brogue-ce-363440c4.tar", "LICENSE.txt"))
def build_brogue(abi):
    """Brogue: Community Edition with its curses front end only (no SDL). Data and high scores
    live in the working directory, the game's home."""
    src = unpack("brogue-ce-363440c4.tar", os.path.join(abi.work("brogue"), "src"))
    exe = os.path.join(abi.work("brogue"), "game_brogue")
    srcs = files(src, "src/brogue/*.c", "src/variants/*.c") + [
        os.path.join(src, "src/platform", f) for f in
        ("main.c", "platformdependent.c", "null-platform.c", "curses-platform.c", "term.c")]
    cc(abi, srcs, exe, '-std=gnu99 -Isrc/brogue -Isrc/platform -Isrc/variants -DDATADIR=. -DBROGUE_CURSES '
       '-DBROGUE_EXTRA_VERSION=\\"\\"', f"{abi.curses_libs} -lm", cwd=src)
    return {"game_brogue": exe}


@game("viper-snake", curses=False, notice=("viper-edd02980.tar", "LICENSE"))
def build_viper(abi):
    """VIper: snake with vi keys and colour schemes. It draws with escape sequences itself."""
    src = unpack("viper-edd02980.tar", os.path.join(abi.work("viper"), "src"))
    exe = os.path.join(abi.work("viper"), "game_viper")
    cc(abi, [os.path.join(src, "viper.c")], exe, "-std=gnu99", "", cwd=src)
    return {"game_viper": exe}


@game("open-adventure", curses=False, notice=("open-adventure-e6160529.tar", "COPYING"))
def build_open_adventure(abi):
    """Colossal Cave Adventure 430 (ESR's forward port). Its dungeon tables are generated from
    adventure.yaml by its own Python script; line input comes from a stand-in for libedit's
    readline (native/ports/open-adventure)."""
    work = abi.work("open-adventure")
    src = unpack("open-adventure-e6160529.tar", os.path.join(work, "src"))
    run("python3 make_dungeon.py", src)
    version = open(os.path.join(src, "NEWS.adoc")).read().split("\n")
    version = next(l.split(":")[0] for l in version if l[:1].isdigit())
    exe = os.path.join(work, "game_advent")
    cc(abi, [os.path.join(src, f) for f in ("main.c", "init.c", "actions.c", "score.c", "misc.c", "saveresume.c", "dungeon.c")],
       exe, f'-std=gnu99 -D_DEFAULT_SOURCE -DVERSION=\\"{version}\\" -I{os.path.join(HERE, "ports", "open-adventure")}', "",
       cwd=src)
    return {"game_advent": exe}


# Zig games pin the Zig release they were written for; Zig's language and build API still change
# between releases. 0.15.1 comes from PyPI (pip install ziglang==0.15.1, docs/BUILD.md), like the
# toolchain's own Zig, at $ZIG_0_15 or in /opt/tuikio-tools/zig-0.15.
ZIG_TARGET = {"arm64-v8a": "aarch64-linux-musl", "armeabi-v7a": "arm-linux-musleabihf", "x86_64": "x86_64-linux-musl"}


def zig_015():
    z = os.environ.get("ZIG_0_15") or "/opt/tuikio-tools/zig-0.15/ziglang/zig"
    if not os.path.exists(z):
        raise BuildError("Zig 0.15.1 not found: pip install --target /opt/tuikio-tools/zig-0.15 ziglang==0.15.1, "
                         "or set ZIG_0_15")
    return z


@game("zigtris", curses=False, notice=("zigtris-60206d8f.tar", "LICENSE.md"))
def build_zigtris(abi):
    """Tetris in Zig. Its one dependency (mibu, terminal handling) is pinned too and given to the
    build as a local path: zig's own fetcher isn't used. Built as a static PIE."""
    work = abi.work("zigtris")
    src = unpack("zigtris-60206d8f.tar", os.path.join(work, "src"))
    mibu = unpack("mibu-be3713ff.tar", os.path.join(work, "mibu"))
    replace_in(os.path.join(src, "build.zig.zon"),
               '.url = "git+https://github.com/xyaman/mibu.git#be3713ff04e7db3584669e679253ef388e426dc6",\n'
               '            .hash = "mibu-0.0.1-dev-Ddr1riTEAAAYAe1TWBT--W8fPUL8UyBE7dy-yNNZ3z5V",',
               f'.path = "{os.path.relpath(mibu, src)}",')
    replace_in(os.path.join(src, "build.zig"), "        .root_module = zigtris_mod,\n    });\n",
               "        .root_module = zigtris_mod,\n    });\n    exe.pie = true;\n")
    run(f"{zig_015()} build -Dtarget={ZIG_TARGET[abi.name]} -Doptimize=ReleaseSmall "
        f"--cache-dir {os.path.join(work, 'cache')} --global-cache-dir {os.path.join(work, 'gcache')}", src)
    EXTRA_NOTICES["zigtris"] = "\n\n---- mibu ----\n\n" + open(os.path.join(mibu, "LICENSE")).read()
    return {"game_zigtris": os.path.join(src, "zig-out", "bin", "zigtris")}


ANGBAND_DATA = ("customize", "gamedata", "help", "screens", "user")


@game("angband", notice=("angband-e473720e.tar", "docs/copying.rst"))
def build_angband(abi):
    """Angband 4.2 with its curses front end (main-gcu.c) only: no X11, SDL, sound or tiles. Its
    text data (game data, help, screens, preferences) is installed under lib/ in the game's home;
    the player's files go in ~/angband, also in the home."""
    work = abi.work("angband")
    src = unpack("angband-e473720e.tar", os.path.join(work, "src"))
    # The roguelike keyset by default: the pad sends h/j/k/l/y/u/b/n, which the original keyset
    # doesn't use for walking (it needs a numeric keypad for diagonals).
    replace_in(os.path.join(src, "src", "list-options.h"),
               'OP(rogue_like_commands,   "Use the roguelike command keyset",\nINTERFACE, false)',
               'OP(rogue_like_commands,   "Use the roguelike command keyset",\nINTERFACE, true)')
    srcs = [f for f in files(src, "src/*.c")
            if not os.path.basename(f).startswith(("main-", "snd-")) or os.path.basename(f) == "main-gcu.c"]
    exe = os.path.join(work, "game_angband")
    cc(abi, srcs, exe, '-std=gnu99 -Isrc -DUSE_GCU -DUSE_NCURSES -DGAMEDATA_IN_LIB -DPRIVATE_USER_PATH=\\"~/angband\\" -DDEFAULT_CONFIG_PATH=\\"lib/customize/\\" '
       '-DDEFAULT_LIB_PATH=\\"lib/\\" -DDEFAULT_DATA_PATH=\\"lib/\\"', f"{abi.curses_libs} -lm", cwd=src)
    if abi.name == "x86_64":  # the data is the same for every ABI
        for d in ANGBAND_DATA:
            for path in files(os.path.join(src, "lib", d), "**/*"):
                if os.path.isfile(path) and "/." not in path[len(src):]:
                    install_asset(f"games/angband/lib/{d}/{os.path.relpath(path, os.path.join(src, 'lib', d))}", path)
    return {"game_angband": exe}


@game("rogue", notice=("rogue-f4653c2a.tar", "LICENSE.TXT"))
def build_rogue(abi):
    """Rogue 5.4.4, the 1980 original: score file and lock in the working directory (the home)."""
    src = unpack("rogue-f4653c2a.tar", os.path.join(abi.work("rogue"), "src"))
    # It sets curscr's cursor fields directly; this ncurses keeps WINDOW opaque.
    replace_in(os.path.join(src, "main.c"), "    curscr->_cury = oy;\n    curscr->_curx = ox;\n",
               "    wmove(curscr, oy, ox);\n")
    autotools(abi, src, "--enable-scorefile=rogue.scr --enable-lockfile=rogue.lck --disable-setgid --enable-wizardmode=no",
              cflags="-fcommon -D_GNU_SOURCE", make="make -j4 rogue")
    return {"game_rogue": os.path.join(src, "rogue")}


@game("npush", notice=("npush-0.7.tgz", "COPYING"))
def build_npush(abi):
    """nPush: a Sokoban-like puzzle with dynamite and monsters. It reads levels/ from the working
    directory, the game's home. (The archive's prebuilt binary is not used.)"""
    work = abi.work("npush")
    src = unpack("npush-0.7.tgz", os.path.join(work, "src"))
    # Its level files have spaces in their names, which app data paths don't allow: they are
    # installed with underscores, shown with spaces in the menu and opened with underscores.
    game_cpp = os.path.join(src, "npush.cpp")
    replace_in(game_cpp, '    std::string fileName = "levels/" + name;\n',
               '    std::string fileName = "levels/" + name;\n'
               '    std::replace (fileName.begin (), fileName.end (), \' \', \'_\');\n')
    replace_in(game_cpp, '        std::string filename (de->d_name);\n',
               '        std::string filename (de->d_name);\n'
               '        std::replace (filename.begin (), filename.end (), \'_\', \' \');\n')
    exe = os.path.join(work, "game_npush")
    cc(abi, [game_cpp], exe, "-std=c++11 -include algorithm", f"{abi.curses_libs}", cxx=True, cwd=src)
    if abi.name == "x86_64":
        for path in files(src, "levels/*"):
            install_asset(f"games/npush/levels/{os.path.basename(path).replace(' ', '_')}", path)
    return {"game_npush": exe}


YAML_CPP = "yaml-cpp_0.8.0+dfsg.orig.tar.xz"


@game("asciiportal", notice=("asciiportal-0d7fb094.tar", "LICENSE"))
def build_asciiportal(abi):
    """ASCIIpOrtal: Portal as an ASCII puzzle platformer, in its plain-text build (no SDL, no sound),
    with yaml-cpp (Ubuntu's source) compiled in for its map-pack descriptions and saves. The map
    packs are data in the game's home; saves go to ~/asciiportal (not the hidden ~/.asciiportal)."""
    work = abi.work("asciiportal")
    src = unpack("asciiportal-0d7fb094.tar", os.path.join(work, "src"))
    ysrc = unpack(YAML_CPP, os.path.join(work, "yaml"))
    replace_in(os.path.join(src, "src", "ap_filemgr.cpp"), 'userpath += s + ".asciiportal";', 'userpath += s + "asciiportal";')
    # Included unconditionally "to compile on OS X"; the plain-text build uses no SDL.
    replace_in(os.path.join(src, "src", "main.cpp"), "#include <SDL/SDL.h>\n", "")
    # It moves into its executable's directory to find maps/; on a phone that is the read-only
    # native library directory. The game's home (its working directory) holds the maps.
    replace_in(os.path.join(src, "src", "main.cpp"), "  chdir(dirname(argv[0]));\n", "")
    # Two functions fall off their end without a return value: undefined behaviour, which the
    # compiler turns into a trap (the game crashed loading its first map pack).
    replace_in(os.path.join(src, "src", "ap_maps.cpp"), "  load_map();\n}\n", "  load_map();\n  return 0;\n}\n")
    replace_in(os.path.join(src, "src", "ap_play.cpp"), "  if (game.has_won()) return 3;\n}\n",
               "  if (game.has_won()) return 3;\n  return 2;\n}\n")
    # Reproducible build: no build date on the title screen.
    replace_in(os.path.join(src, "src", "menu.cpp"), '"v%s (%s)", AP_VERSION, __DATE__', '"v%s", AP_VERSION')
    # The notice that it created the directory would be printed over the menu.
    replace_in(os.path.join(src, "src", "ap_filemgr.cpp"),
               '      cout << "Home directory " << userpath << " not existing, creating it." << endl;\n', "")
    srcs = [os.path.join(src, "src", n + ".cpp") for n in
            ("ap_pager", "ap_object", "ap_maps", "ap_filemgr", "ap_input", "ap_draw", "ap_play", "main", "menu")]
    srcs += files(ysrc, "src/*.cpp", "src/contrib/*.cpp")
    exe = os.path.join(work, "game_asciiportal")
    cc(abi, srcs, exe, f'-std=gnu++17 {abi.curses_cflags} -I{ysrc}/include -I{ysrc}/src -DYAML_CPP_STATIC_DEFINE -D__NOSDL__ -D__NOSOUND__ '
       '-DAP_VERSION=\\"1.3-beta8\\"', abi.curses_libs, cxx=True, cwd=src)
    for path in files(src, "maps/**/*"):
        if os.path.isfile(path):
            install_asset("games/asciiportal/" + os.path.relpath(path, src), path)
    EXTRA_NOTICES["asciiportal"] = ("\n\n" + "=" * 72 + "\nIt includes yaml-cpp 0.8.0 (MIT): Copyright (c) 2008-2015 Jesse Beder.\n")
    return {"game_asciiportal": exe}


@game("gnuski", notice=("gnuski-0.3.tar.gz", "GPL.txt"))
def build_gnuski(abi):
    """GNUSki 0.3: a SkiFree clone in curses."""
    src = unpack("gnuski-0.3.tar.gz", os.path.join(abi.work("gnuski"), "src"))
    # setupColors() is defined in objects.c but declared nowhere.
    replace_in(os.path.join(src, "objects.h"), "struct Object makeObject (", "void setupColors (void);\nstruct Object makeObject (")
    exe = os.path.join(abi.work("gnuski"), "game_gnuski")
    cc(abi, [os.path.join(src, f) for f in ("main.c", "objects.c")], exe, LEGACY, abi.curses_libs, cwd=src)
    return {"game_gnuski": exe}


@game("cnibbles", notice=("cNibbles-2.0.1.tbz", "LICENSE"))
def build_cnibbles(abi):
    """cNibbles 2.0.1: Nibbles in curses. High scores and replays go to ~/cNibbles (not the
    hidden ~/.cNibbles)."""
    src = unpack("cNibbles-2.0.1.tbz", os.path.join(abi.work("cnibbles"), "src"))
    replace_in(os.path.join(src, "highscore.c"), 'const char highscoreDirName[] = "/.cNibbles";',
               'const char highscoreDirName[] = "/cNibbles";')
    # Reproducible build: no build date in the about text.
    replace_in(os.path.join(src, "options.c"), '     fprintf (stderr, "Built on %s @ %s\\n", __DATE__, __TIME__);\n', "")
    exe = os.path.join(abi.work("cnibbles"), "game_cnibbles")
    cc(abi, [os.path.join(src, f + ".c") for f in ("main", "misc", "screen", "options", "highscore", "replay", "intro")],
       exe, LEGACY, abi.curses_libs, cwd=src)
    return {"game_cnibbles": exe}


def unpack_zip(name, dest):
    """unpack() for a zip archive: verified, fresh, no path may leave the destination."""
    import shutil
    import zipfile
    archive = tk.fetch(name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    real = os.path.realpath(dest)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            target = os.path.realpath(os.path.join(dest, info.filename))
            if target != real and not target.startswith(real + os.sep):
                raise BuildError(f"refusing path outside archive root: {info.filename}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise BuildError(f"refusing symlink in archive: {info.filename}")
        z.extractall(dest)
    tops = os.listdir(dest)
    return os.path.join(dest, tops[0]) if len(tops) == 1 else dest


@game("ascii-dash", notice=("ASCII-DASH-1.3.zip", "COPYING"))
def build_ascii_dash(abi):
    """ASCII DASH 1.3: Boulder Dash I in ncurses, without sound (SDL) or joystick. The 20 caves of
    Boulder Dash I are data in the game's home (data/BD-I-*.ad); the high score is ./dash.txt."""
    work = abi.work("ascii-dash")
    src = unpack_zip("ASCII-DASH-1.3.zip", os.path.join(work, "src"))
    gfx = os.path.join(src, "ascii-gfx", "gfx")
    srcs = [os.path.join(src, "main.cpp")] + files(src, "dash/*.cpp") + files(gfx, "*.cpp")
    exe = os.path.join(work, "game_ascii_dash")
    cc(abi, srcs, exe, f"-std=gnu++98 {abi.curses_cflags} -I{src} -I{src}/dash -I{gfx}", abi.curses_libs, cxx=True, cwd=src)
    for path in files(src, "data/BD-I-*.ad"):
        install_asset("games/ascii-dash/data/" + os.path.basename(path), path)
    return {"game_ascii_dash": exe}
