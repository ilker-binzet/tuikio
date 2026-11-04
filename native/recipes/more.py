"""More single games, pinned by commit (tools/ports/git_lock.py) or by archive hash, each built
from the file list its upstream makefile compiles."""
import glob
import os

from tk import EXTRA_NOTICES, HERE, BuildError, autotools, cc, game, install_asset, replace_in, run, unpack


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
