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
