"""Board, card and puzzle games (the "boards" batch): falling blocks, Sudoku, Minesweeper, solitaires,
strategy games and the GNU chess, Go and shogi engines. Sources are pinned in
native/sources.lock.json (Ubuntu 24.04 source packages through their signed index, git trees by
commit, release tarballs by SHA-256). Paths that pointed at /usr, /var or /tmp are redirected into
the game's home, its working directory, with exact, checked substitutions."""
import glob
import os
import re
import shutil
import tarfile
import threading

import tk
from tk import (BUILD, LEGACY, BuildError, apply_debian_patches, apply_patches, autotools, cc, compile_objects,
                game, install_asset, link, placeholder, replace_in, run, unpack)


def files(src, *patterns, exclude=()):
    out = []
    for p in patterns:
        out += [f for f in sorted(glob.glob(os.path.join(src, p))) if os.path.basename(f) not in exclude]
    if not out:
        raise BuildError(f"no sources match {patterns} in {src}")
    return out


def tree(abi, gid, archive, debian=None, skip=()):
    src = unpack(archive, os.path.join(abi.work(gid), "src"))
    if debian:
        apply_debian_patches(src, debian, skip)
    apply_patches(src, gid)
    return src


def tar_member_text(archive, rel):
    """One text file from a verified source archive (a license, for the notices)."""
    with tarfile.open(tk.fetch(archive)) as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.split("/", 1)[-1] == rel:
                return tf.extractfile(m).read().decode("utf-8", "replace")
    raise BuildError(f"{rel} not found in {archive}")


# ---------------------------------------------------------------- Boost (for Bastet)

BOOST = "boost1.83_1.83.0.orig.tar.xz"
_boost_lock = threading.Lock()


BOOST_HEADER = re.compile(r"^libs/(?:numeric/)?[^/]+/include/(boost/.*)$")


def boost_tree():
    """The parts of Boost 1.83 that Bastet needs, extracted once for every ABI: the headers and
    Boost.Program_options' sources (the one compiled library it links). Ubuntu's archive has the
    modular layout (each library's headers under libs/<name>/include/boost/), so the headers are
    gathered into one include/boost, as Boost's own build does. The archive is 77 MB and unpacks to
    ten times that, so only those members are taken, with unpack()'s path checks."""
    root = os.path.join(BUILD, "shared", "boost-1.83")
    stamp = os.path.join(root, ".done")
    with _boost_lock:
        if os.path.exists(stamp):
            return root
        archive = tk.fetch(BOOST)
        if os.path.exists(root):
            shutil.rmtree(root)
        os.makedirs(root)
        real = os.path.realpath(root)
        tk.log("boost: extracting headers and program_options")
        with tarfile.open(archive) as tf:
            members = []
            for m in tf:
                rel = m.name.split("/", 1)[-1]
                header = BOOST_HEADER.match(rel)
                if header:
                    m.name = "include/" + header.group(1)
                elif rel.startswith("libs/program_options/src/"):
                    m.name = "po/" + rel[len("libs/program_options/src/"):]
                elif rel == "LICENSE_1_0.txt":
                    m.name = rel
                else:
                    continue
                if not (m.isfile() or m.isdir()):
                    raise BuildError(f"boost: unexpected member type: {rel}")
                target = os.path.realpath(os.path.join(root, m.name))
                if target != real and not target.startswith(real + os.sep):
                    raise BuildError(f"boost: refusing path outside archive root: {rel}")
                members.append(m)
            tf.extractall(root, members=members, filter="data")
        open(stamp, "w").close()
        return root


# ---------------------------------------------------------------- Bastet

@game("bastet", notice=("bastet_0.43.orig.tar.gz", "LICENSE"))
def bastet(abi):
    src = tree(abi, "bastet", "bastet_0.43.orig.tar.gz", "bastet_0.43-7build1.debian.tar.xz")
    boost = boost_tree()
    # High scores: the global table lives in the game's home (the app creates it empty once).
    replace_in(os.path.join(src, "Config.cpp"), '"/var/games/bastet.scores2"', '"bastet.scores2"')
    # Its default drop key is KEY_ENTER, which only a keypad's Enter sends; Return arrives as 13 (it
    # turns nonl() on), as its own menus expect. Return drops, as the manual says.
    replace_in(os.path.join(src, "Config.cpp"), 'po::value<int>()->default_value(KEY_ENTER)', 'po::value<int>()->default_value(13)')
    flags = f"-std=c++14 -I{boost}/include -DNDEBUG -Wno-deprecated-declarations"
    po = compile_objects(abi, files(boost, "po/*.cpp", exclude=("winmain.cpp",)), os.path.join(src, "po"),
                         flags, cxx=True, cwd=boost)
    # Ui.cpp uses select() and struct timeval without their headers, which glibc pulls in anyway, and
    # narrows size_t in brace initialisers, which GCC only warns about.
    objs = compile_objects(abi, files(src, "*.cpp", exclude=("Test.cpp",)), os.path.join(src, "obj"),
                           f"{flags} -Wno-c++11-narrowing -include sys/select.h -include sys/time.h", cxx=True, cwd=src)
    exe = os.path.join(src, "bastet")
    link(abi, objs + po, exe, abi.curses_libs, cxx=True, cwd=src)
    placeholder("games/bastet/bastet.scores2")
    with _boost_lock:
        tk.EXTRA_NOTICES["bastet"] = ("\n\n--- Boost 1.83 (headers and Boost.Program_options, linked in) ---\n\n"
                                      + open(os.path.join(boost, "LICENSE_1_0.txt")).read())
    return {"game_bastet": exe}


# ---------------------------------------------------------------- yetris

@game("yetris", notice=("yetris-cf3fee6c.tar", "COPYING"))
def yetris(abi):
    src = tree(abi, "yetris", "yetris-cf3fee6c.tar")  # patch: no shell for rm -rf
    # The first-run profile name defaulted to the home directory's name ("home" in the app); the
    # player's name is $USER.
    replace_in(os.path.join(src, "deps", "Engine", "Helpers", "File.cpp"),
               "std::string Utils::File::getUser()\n{\n",
               "std::string Utils::File::getUser()\n{\n\tif (getenv(\"USER\") && *getenv(\"USER\")) /* Tuikio */\n"
               "\t\treturn getenv(\"USER\");\n")
    # Up did nothing in play (rotation was only x and z); on a phone's pad Up turns the piece, as in
    # the other falling-block games. Menus keep Up for moving up.
    replace_in(os.path.join(src, "src", "Game", "Entities", "Profile.cpp"),
               "settings.input.rotate_clockwise        = 'x';", "settings.input.rotate_clockwise        = KEY_UP;")
    # What its Makefile passes; DATE is the pinned commit's month instead of the build's.
    defs = '-DVERSION=\\"2.3.0\\" -DPACKAGE=\\"yetris\\" -DDATE=\\"Jan2015\\"'
    cpp = [f for f in glob.glob(os.path.join(src, "**", "*.cpp"), recursive=True)
           if os.path.relpath(f, src).startswith(("src/", "deps/Engine/"))]
    # Its rotation tables are negative offsets in plain chars: signed on x86, unsigned on ARM.
    objs = compile_objects(abi, sorted(cpp), os.path.join(src, "obj"),
                           f"-std=c++11 -fsigned-char -I{src}/src -I{src}/deps {defs}", cxx=True, cwd=src)
    objs += compile_objects(abi, [os.path.join(src, "deps", "commander", "commander.c")], os.path.join(src, "obj"),
                            "-std=gnu99", cwd=src)
    exe = os.path.join(src, "yetris")
    link(abi, objs, exe, abi.curses_libs, cxx=True, cwd=src)
    return {"game_yetris": exe}


# ---------------------------------------------------------------- nsuds

@game("nsuds", notice=("nsuds-0.7B.tar.gz", "COPYING"))
def nsuds(abi):
    src = tree(abi, "nsuds", "nsuds-0.7B.tar.gz")
    # What configure finds on Linux (config.h), without running it.
    with open(os.path.join(src, "src", "config.h"), "w") as fh:
        fh.write("#define HAVE_NCURSES_H 1\n#define HAVE_STDLIB_H 1\n#define HAVE_STRING_H 1\n#define HAVE_UNISTD_H 1\n"
                 "#define HAVE_SYS_STAT_H 1\n#define HAVE_SYS_TYPES_H 1\n#define STDC_HEADERS 1\n"
                 '#define PACKAGE "nsuds"\n#define VERSION "0.7B"\n#define PACKAGE_STRING "nsuds 0.7B"\n#define PACKAGE_BUGREPORT "vincent@doublecreations.com"\n')
    # Help text and high scores live in nsuds/ in the game's home (not /usr/share/doc and /var/games).
    exe = os.path.join(src, "nsuds")
    # musl has no <sys/queue.h>; native/ports/nsuds/include has the tail-queue macros it uses. menu.c
    # calls display_scores() without including its header; its headers define globals (-fcommon).
    queue = os.path.join(tk.HERE, "ports", "nsuds", "include")
    cc(abi, files(src, "src/*.c"), exe, f"-std=gnu99 -I{src}/src -idirafter {queue} -include highscores.h -fcommon -DHELPDIR='\"nsuds/\"' -DSCOREDIR='\"nsuds/\"'",
       f"{abi.curses_libs} -lm", cwd=src)
    install_asset("games/nsuds/nsuds/main", os.path.join(src, "helpfiles", "main"))
    install_asset("games/nsuds/nsuds/high_scores", os.path.join(src, "src", "high_scores"))
    return {"game_nsuds": exe}


# ---------------------------------------------------------------- Tobias Girstmair's games (no curses)

def girst_tree(abi, gid, archive, source):
    src = tree(abi, gid, archive)
    # Switching between raw and cooked input flushed what was already typed (TCSAFLUSH), so a button
    # that sends a whole command (":n" and Enter) lost everything after the colon. Keep the input.
    replace_in(os.path.join(src, source), "TCSAFLUSH", "TCSADRAIN", count=2)
    return src


@game("minesviiper", curses=False, notice=("minesviiper-f39a17cd.tar", "LICENSE"))
def minesviiper(abi):
    src = girst_tree(abi, "minesviiper", "minesviiper-f39a17cd.tar", "mines.c")
    exe = os.path.join(src, "mines")
    cc(abi, [os.path.join(src, "mines.c")], exe, "-std=gnu99", cwd=src)
    return {"game_minesviiper": exe}


@game("solvitaire", curses=False, notice=("solvitaire-1883ee0c.tar", "LICENSE"))
def solvitaire(abi):
    src = girst_tree(abi, "solvitaire", "solvitaire-1883ee0c.tar", "sol.c")
    out = {}
    for variant, exe in (("KLONDIKE", "game_solvitaire"), ("SPIDER", "game_solvitaire_spider"),
                         ("FREECELL", "game_solvitaire_freecell")):
        path = os.path.join(src, exe)
        cc(abi, [os.path.join(src, "sol.c")], path, f"-std=gnu99 -D{variant}", cwd=src)
        out[exe] = path
    return out


# ---------------------------------------------------------------- Blue Moon

@game("blue-moon-solitaire", notice=("bluemoon-91ff5db7.tar", "COPYING"))
def bluemoon(abi):
    src = tree(abi, "blue-moon-solitaire", "bluemoon-91ff5db7.tar")
    exe = os.path.join(src, "bluemoon")
    cc(abi, [os.path.join(src, "bluemoon.c")], exe, "-std=gnu99 -DRELEASE=\\\"2.15\\\"", abi.curses_libs, cwd=src)
    return {"game_bluemoon": exe}


# ---------------------------------------------------------------- CPat

@game("cpat-solitaire", notice=("cpat-1.4.2.tar.gz", "COPYING"))
def cpat(abi):
    src = tree(abi, "cpat-solitaire", "cpat-1.4.2.tar.gz")
    # High scores go to $HOME/.cpat_scores (src/cpat.c).
    autotools(abi, src, "", make="make -j4")
    exe = os.path.join(src, "src", "cpat")
    return {"game_cpat": exe}
