"""More single games, pinned by commit (tools/ports/git_lock.py) or by archive hash, each built
from the file list its upstream makefile compiles."""
import glob
import os

from tk import HERE, BuildError, cc, game, run, unpack


def files(src, *patterns):
    out = []
    for p in patterns:
        out += sorted(glob.glob(os.path.join(src, p)))
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
