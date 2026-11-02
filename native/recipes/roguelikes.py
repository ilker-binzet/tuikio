"""Roguelikes and interactive fiction: NetHack 3.6 and its variant SporkHack, Angband, Brogue CE,
Hydra Slayer, Open Adventure and Frotz with the Zork trilogy.

The NetHack family generates its data with programs built on the build machine (makedefs, the
level and dungeon compilers, the data librarian). Its level files and quest text are written
with fwrite() of C structs holding longs and pointers, so they must be generated with the same
type sizes as the game reads them with: one host build with 64-bit types serves x86_64 and
arm64-v8a, one with 32-bit types (Zig's i386 musl target, run on the build machine) serves
armeabi-v7a, whose game reads its own copy of the data library. Both copies ship in the game's
home; each binary opens only its own.

Every game's data paths are relative: the app starts each game in its private home directory.
"""
import glob
import os
import shutil
import threading

from tk import (ASSETS, BUILD, CFLAGS, HERE, LEGACY, BuildError, cc, compile_objects, game, install_asset, link,
                placeholder, replace_in, run, unpack, zig)

PORTS = os.path.join(HERE, "ports")
# makedefs stamps the build date into the game: a reproducible one (NetHack 3.6.7's release day).
SOURCE_DATE_EPOCH = "1676505600"


def host_cc(bits):
    """A compiler for programs run on the build machine, with the target's type sizes."""
    arch = "x86" if bits == 32 else "x86_64"
    return f"{zig()} cc -target {arch}-linux-musl -static -O1 -w"


def stage_tree(gid, src, rel, dest):
    """Installs a file, or every file under a directory, as assets/games/<gid>/<dest>."""
    path = os.path.join(src, rel)
    if os.path.isdir(path):
        for dirpath, _, names in os.walk(path):
            for n in sorted(names):
                full = os.path.join(dirpath, n)
                install_asset(f"games/{gid}/{dest}/{os.path.relpath(full, path)}", full)
    else:
        install_asset(f"games/{gid}/{dest}", path)


def keep_dir(gid, rel):
    """An empty directory the game writes into (aapt2 drops hidden files, so a visible one)."""
    path = os.path.join(ASSETS, "games", gid, rel, "keep")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


# ---------------------------------------------------------------- NetHack family

class NetHackTree:
    """A NetHack-derived source tree: its configuration edits and file lists."""

    def __init__(self, gid, archive, exe, game_srcs, sys_srcs, win_srcs, defs, edits, dat_dlb, dat_plain,
                 makedefs_steps, nhrc):
        self.gid, self.archive, self.exe = gid, archive, exe
        self.game_srcs, self.sys_srcs, self.win_srcs = game_srcs, sys_srcs, win_srcs
        self.defs, self.edits = defs, edits
        self.dat_dlb, self.dat_plain = dat_dlb, dat_plain
        self.makedefs_steps = makedefs_steps
        self.nhrc = nhrc
        self.lock = threading.Lock()
        self.hosts = {}

    def configure(self, src):
        for rel, old, new in self.edits:
            replace_in(os.path.join(src, rel), old, new)

    def host(self, bits):
        """Builds the data-generating programs with [bits]-bit types and runs them once; returns
        the configured tree with its generated headers, sources and data library."""
        with self.lock:
            if bits in self.hosts:
                return self.hosts[bits]
            work = os.path.join(BUILD, "host", f"{self.gid}-{bits}")
            src = unpack(self.archive, os.path.join(work, "src"))
            self.configure(src)
            util, dat = os.path.join(src, "util"), os.path.join(src, "dat")
            for f in ("lev_lex.c", "lev_yacc.c", "dgn_lex.c", "dgn_yacc.c"):
                shutil.copyfile(os.path.join(src, "sys", "share", f), os.path.join(util, f))
            for f in ("lev_comp.h", "dgn_comp.h"):
                shutil.copyfile(os.path.join(src, "sys", "share", f), os.path.join(src, "include", f))
            hcc = f"{host_cc(bits)} {LEGACY} -I../include {self.defs}"
            env = dict(os.environ, SOURCE_DATE_EPOCH=SOURCE_DATE_EPOCH)
            mon = "../src/monst.c ../src/objects.c"
            run(f"{hcc} makedefs.c {mon} -o makedefs", util)
            for step in self.makedefs_steps:
                run(f"./makedefs {step}", util, env)
            run(f"{hcc} lev_yacc.c lev_lex.c lev_main.c ../src/alloc.c panic.c ../src/drawing.c ../src/decl.c {mon} "
                "-o lev_comp", util)
            run(f"{hcc} dgn_yacc.c dgn_lex.c dgn_main.c ../src/alloc.c panic.c -o dgn_comp", util)
            run(f"{hcc} dlb_main.c ../src/dlb.c ../src/alloc.c panic.c -o dlb", util)
            for des in sorted(glob.glob(os.path.join(dat, "*.des"))):
                run(f"../util/lev_comp {os.path.basename(des)}", dat)
            run("../util/dgn_comp dungeon.pdf", dat)
            files = []
            for pattern in self.dat_dlb:
                found = sorted(os.path.basename(p) for p in glob.glob(os.path.join(dat, pattern)))
                if not found:
                    raise BuildError(f"{self.gid}: no data file matches {pattern}")
                files += found
            run(f"LC_ALL=C ../util/dlb cf nhdat {' '.join(files)}", dat)
            self.hosts[bits] = src
            return src

    def stage(self):
        """Data for the game's home: one data library per type size, and the plain files."""
        for bits, name in ((64, "nhdat"), (32, "nhdat32")):
            install_asset(f"games/{self.gid}/{name}", os.path.join(self.host(bits), "dat", "nhdat"))
        src = self.host(64)
        for f in self.dat_plain:
            install_asset(f"games/{self.gid}/{f}", os.path.join(src, "dat", f))
        install_asset(f"games/{self.gid}/nethackrc", self.nhrc)
        # They must exist: the game locks each by opening it (perm is only a lock).
        for f in ("perm", "record", "logfile", "xlogfile"):
            placeholder(f"games/{self.gid}/{f}")
        keep_dir(self.gid, "save")

    def build(self, abi):
        bits = 32 if abi.name == "armeabi-v7a" else 64
        src = self.host(bits)
        self.stage()
        dlb = ' -DDLBFILE=\\"nhdat32\\"' if bits == 32 else ""
        srcs = ([os.path.join(src, "src", f) for f in self.game_srcs] +
                [os.path.join(src, f) for f in self.sys_srcs + self.win_srcs])
        objs = compile_objects(abi, srcs, os.path.join(abi.work(self.gid), "obj"),
                               f"{LEGACY} -I{src}/include {self.defs}{dlb}", cwd=src)
        exe = os.path.join(abi.work(self.gid), self.exe)
        link(abi, objs, exe, abi.curses_libs)
        return {self.exe: exe}


NH36_GAME = """allmain alloc apply artifact attrib ball bones botl cmd dbridge decl detect dig display dlb do do_name
do_wear dog dogmove dokick dothrow drawing dungeon eat end engrave exper explode extralev files fountain hack
hacklib invent isaac64 light lock mail makemon mapglyph mcastu mhitm mhitu minion mklev mkmap mkmaze mkobj mkroom
mon mondata monmove monst mplayer mthrowu muse music o_init objects objnam options pager pickup pline polyself
potion pray priest quest questpgr read rect region restore rip rnd role rumors save shk shknam sit sounds sp_lev
spell steal steed sys teleport timeout topten track trap u_init uhitm vault version vision vis_tab weapon were
wield windows wizard worm worn write zap""".split()

# Configuration for a phone: the game's home is its data directory; no mail spool, shell escape,
# job control (^Z would stop the game under the app) or external compressor.
NH_DEFS = '-DNOTPARMDECL -DDLB -DHACKDIR=\\".\\" -DNOSHELL -DREPRODUCIBLE_BUILD'
NH36_EDITS = [
    ("include/unixconf.h", "#define MAIL /* Deliver mail during the game */",
     "/* Tuikio: no mail spool on a phone */"),
    ("include/unixconf.h", "#define SUSPEND /* let ^Z suspend the game */", "/* Tuikio: no job control */"),
    # No system-wide configuration file: its defaults are compiled in.
    ("include/config.h", '#define SYSCF                /* use a global configuration */\n'
                         '#define SYSCF_FILE "sysconf" /* global configuration is in a file */\n', ""),
    # The app runs every game as user "player": ask for the hero's name instead (sysconf's
    # GENERICUSERS setting).
    ("src/sys.c", "\n    sysopt.genericusers = (char *) 0;", '\n    sysopt.genericusers = dupstr("player");'),
    # The options file is "nethackrc" in the home: APK packaging drops hidden files, so a
    # ".nethackrc" could not ship there.
    ("src/files.c", '    ".nethackrc";', '    "nethackrc";'),
    ("src/files.c", 'Strcpy(tmp_config, ".nethackrc");', 'Strcpy(tmp_config, "nethackrc");'),
    ("src/files.c", 'envp, ".nethackrc");', 'envp, "nethackrc");'),
    # Saves are written uncompressed: there is no compress or gzip program to run.
    ("include/config.h", '#define COMPRESS "/usr/bin/compress" /* Lempel-Ziv compression */\n'
                         '#define COMPRESS_EXTENSION ".Z"      /* compress\'s extension */\n', ""),
]

NETHACK = NetHackTree(
    "nethack", "nethack_3.6.7.orig.tar.gz", "game_nethack",
    [f"{f}.c" for f in NH36_GAME],
    ["sys/share/ioctl.c", "sys/share/unixtty.c", "sys/unix/unixmain.c", "sys/unix/unixunix.c", "sys/unix/unixres.c",
     "sys/share/posixregex.c"],
    ["win/tty/getline.c", "win/tty/termcap.c", "win/tty/topl.c", "win/tty/wintty.c"],
    NH_DEFS, NH36_EDITS,
    ["help", "hh", "cmdhelp", "keyhelp", "history", "opthelp", "wizhelp", "dungeon", "tribute", "*.lev",
     "bogusmon", "data", "engrave", "epitaph", "oracles", "options", "quest.dat", "rumors"],
    ["license", "symbols"],
    ["-o", "-p", "-z", "-v", "-d", "-r", "-q", "-h", "-s", "-e"],
    os.path.join(PORTS, "nethack", "nethackrc"),
)

game("nethack", notice=("nethack_3.6.7.orig.tar.gz", "dat/license"))(NETHACK.build)
