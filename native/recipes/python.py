"""Python games, run by one CPython 3.13 built from pinned source (docs/RUNTIME.md, "Python games").

libgame_python.so is a static CPython with the built-in modules the games need, followed by a zip
archive holding the compiled standard library, Tuikio's launcher module (_tuikio_run) and every
Python game's code. Python imports from that archive only (native/ports/python/tuikio_python.c):
isolated mode, no `site`, no current directory on the path. The executable lives read-only in the
APK's native library directory, so nothing in a game's home (or a save archive) can be imported.
The interpreter has no socket, subprocess, ctypes or ssl modules: Python games are offline and
can't start programs.

A game is started as `game_python <game id>`; _tuikio_run looks the id up in GAMES (generated
from PY_GAMES below) and runs its entry point with the game's home as working directory.
"""
import io
import os
import shutil
import subprocess
import threading
import zipfile

import tk
from tk import BuildError, game, replace_in, run, unpack

PORTS = os.path.join(tk.HERE, "ports", "python")
CPYTHON = "cpython-cbc944f4.tar"
VERSION = "3.13.16"
ZLIB = "zlib_1.3.dfsg.orig.tar.xz"

# Built-in extension modules (Modules/Setup.stdlib names). Everything else is n/a.
MODULES = (
    "array", "_bisect", "_contextvars", "_csv", "_heapq", "_json", "_opcode", "_pickle", "_queue",
    "_random", "_struct", "math", "cmath", "_statistics", "_datetime", "binascii", "zlib", "_md5",
    "_sha1", "_sha2", "_sha3", "_blake2", "unicodedata", "fcntl", "grp", "select", "termios",
    "_curses", "_curses_panel", "resource", "_zoneinfo",
)
DISABLED = (
    "_asyncio", "_lsprof", "_interpreters", "_interpchannels", "_interpqueues", "_decimal", "_bz2",
    "_lzma", "_dbm", "_gdbm", "readline", "pyexpat", "_elementtree", "_codecs_cn", "_codecs_hk",
    "_codecs_iso2022", "_codecs_jp", "_codecs_kr", "_codecs_tw", "_multibytecodec", "mmap",
    "_posixsubprocess", "_socket", "syslog", "_posixshmem", "_multiprocessing", "_ctypes",
    "_sqlite3", "_ssl", "_hashlib", "_uuid", "_tkinter", "_scproxy", "xxsubtype", "_xxtestfuzz",
    "_testbuffer", "_testinternalcapi", "_testcapi", "_testlimitedcapi", "_testclinic",
    "_testclinic_limited", "_testimportmultiple", "_testmultiphase", "_testsinglephase",
    "_testexternalinspection", "_ctypes_test", "xxlimited", "xxlimited_35", "_ctypes_test",
)
# Standard library packages and modules left out of the archive (unused by the games, or
# useless without the modules above).
STDLIB_SKIP = (
    "test", "idlelib", "tkinter", "turtledemo", "turtle.py", "ensurepip", "lib2to3", "pydoc_data",
    "venv", "sqlite3", "ctypes", "asyncio", "multiprocessing", "concurrent", "xml", "xmlrpc",
    "http", "urllib", "email", "wsgiref", "html", "dbm", "unittest", "tomllib", "site-packages",
    "__phello__", "_pyrepl", "pydoc.py", "doctest.py", "pdb.py", "imaplib.py", "smtplib.py", "ftplib.py",
    "poplib.py", "nntplib.py", "mailbox.py", "ssl.py", "socketserver.py", "subprocess.py",
    "_pydecimal.py", "decimal.py", "config-3.13", "lib-dynload", "zipapp.py", "mimetypes.py",
    "webbrowser.py", "telnetlib.py", "cgi.py", "cgitb.py", "smtpd.py", "asynchat.py", "asyncore.py",
)


def py_game(lock, notice, package, entry, *, subst=(), skip=(), data=None, libs=()):
    """[package]: {path in the source: name in the archive} (a directory or a .py file);
    [entry]: "module:function" or "module" (run as __main__); [skip]: paths under a package to
    leave out; [data]: {path in the source: path in the game's home} installed as assets;
    [libs]: names in LIBS (pure-Python libraries the game imports)."""
    return dict(lock=lock, notice=notice, package=package, entry=entry, subst=subst, skip=skip,
                data=data or {}, libs=libs)


# Pure-Python libraries some games import: lock, {path in the source: name in the archive},
# licence file, licence line for the game's notice.
LIBS = {
    "scrap_engine": ("scrap_engine-9ba3878b.tar", {"src/scrap_engine": "scrap_engine"}, "LICENSE",
                     "scrap_engine by lxgr-linux, GPL-3.0"),
    "art": ("art-3917a898.tar", {"art": "art"}, "LICENSE", "art by Sepand Haghighi, MIT"),
}


PY_GAMES = {}

_lock = threading.Lock()
_host = {}


def build_zlib(abi, work):
    """A static zlib for the zlib module (compressed archive members, gzip)."""
    zsrc = unpack(ZLIB, os.path.join(work, "zlib"))
    names = ("adler32", "crc32", "deflate", "infback", "inffast", "inflate", "inftrees", "trees",
             "zutil", "compress", "uncompr")
    objs = tk.compile_objects(abi, [os.path.join(zsrc, n + ".c") for n in names], os.path.join(work, "zobj"), cwd=zsrc)
    lib = os.path.join(work, "zlib", "libz.a")
    run(f"{abi.ar} rcs {lib} {' '.join(objs)}", work)
    return zsrc, lib


def host_python():
    """A CPython of the same version for the build machine: cross-compiling needs one to freeze
    modules, and it compiles the standard library archive (same bytecode magic)."""
    with _lock:
        if "py" in _host:
            return _host["py"]
        work = os.path.join(tk.BUILD, "host", "cpython")
        exe = os.path.join(work, "src", "python")
        stamp = os.path.join(work, "stamp")
        if not (os.path.exists(exe) and os.path.exists(stamp) and open(stamp).read() == CPYTHON):
            src = unpack(CPYTHON, os.path.join(work, "src-unpack"))
            dst = os.path.join(work, "src")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.rename(src, dst)
            env = dict(os.environ, CC="gcc")
            run("./configure --without-ensurepip --disable-test-modules", dst, env)
            run(f"make -j{os.cpu_count() or 2}", dst, env)
            with open(stamp, "w") as fh:
                fh.write(CPYTHON)
        _host["py"] = exe
        return exe


CONFIG_SITE = "ac_cv_file__dev_ptmx=yes\nac_cv_file__dev_ptc=no\nac_cv_buggy_getaddrinfo=no\n"


def build_interpreter(abi):
    """The static interpreter for one ABI (without the archive)."""
    work = abi.work("tuikio-python")
    main_c = os.path.join(PORTS, "tuikio_python.c")
    key = CPYTHON + repr(MODULES) + repr(DISABLED) + open(main_c).read() + CONFIG_SITE + "v1"
    out = os.path.join(work, "python")
    stamp = out + ".key"
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
        return out
    hostpy = host_python()
    zsrc, zlib = build_zlib(abi, work)
    src = unpack(CPYTHON, os.path.join(work, "src"))
    shutil.copyfile(main_c, os.path.join(src, "Programs", "python.c"))
    # Reproducible: no build date in sys.version.
    replace_in(os.path.join(src, "Modules", "getbuildinfo.c"), "#define DATE __DATE__", '#define DATE "Jan  1 1970"')
    replace_in(os.path.join(src, "Modules", "getbuildinfo.c"), "#define TIME __TIME__", '#define TIME "00:00:00"')
    site = os.path.join(work, "config.site")
    with open(site, "w") as fh:
        fh.write(CONFIG_SITE)
    na = {f"py_cv_module_{m}": "n/a" for m in DISABLED}
    env = abi.env(CONFIG_SITE=site, MODULE_BUILDTYPE="static", CPPFLAGS="", LDFLAGS=abi.ldflags,
                  CFLAGS=tk.CFLAGS, OPT="-DNDEBUG",
                  LIBS="", ZLIB_CFLAGS=f"-I{zsrc}", ZLIB_LIBS=zlib,
                  CURSES_CFLAGS=f"{abi.curses_cflags} -DHAVE_NCURSESW=1", CURSES_LIBS=abi.curses_libs,
                  PANEL_CFLAGS=abi.curses_cflags, PANEL_LIBS=f"-L{abi.sysroot}/lib -lpanelw", **na)
    run(f"./configure --host={abi.triple} --build=x86_64-pc-linux-gnu --with-build-python={hostpy} "
        "--disable-shared --without-ensurepip --disable-test-modules --disable-ipv6 "
        "--without-static-libpython --with-pymalloc --without-doc-strings", src, env)
    run(f"make -j{os.cpu_count() or 2} python LINKFORSHARED= CONFIGURE_LDFLAGS= CONFIGURE_LDFLAGS_NODIST=", src, env)
    built = os.path.join(src, "python")
    # Every module asked for must really be built in (a missing header turns one off silently).
    names = subprocess.run(["strings", built], capture_output=True, text=True).stdout
    for m in MODULES:
        if f"PyInit_{m}" not in names and m not in names:
            raise BuildError(f"python: module {m} is not built in")
    shutil.copyfile(built, out)
    with open(stamp, "w") as fh:
        fh.write(key)
    return out


_archive = {}


def _launcher_source():
    games = {gid: e["entry"] for gid, e in PY_GAMES.items()}
    return (open(os.path.join(PORTS, "_tuikio_run.py"), encoding="utf-8").read()
            .replace("GAMES = {}  # @GAMES@", f"GAMES = {games!r}"))


_archive_lock = threading.Lock()


def build_archive():
    """The zip appended to the interpreter: compiled stdlib, the launcher, every game. Built once
    per run, whichever ABI asks first (every ABI shares it; the others wait)."""
    with _archive_lock:
        if "zip" not in _archive:
            _archive["zip"] = _build_archive()
        return _archive["zip"]


def _build_archive():
    hostpy = host_python()
    work = os.path.join(tk.BUILD, "scripts", "python")
    os.makedirs(work, exist_ok=True)
    tree = os.path.join(work, "tree")
    if os.path.exists(tree):
        shutil.rmtree(tree)
    lib = os.path.join(os.path.dirname(hostpy), "Lib")
    shutil.copytree(lib, tree, ignore=lambda d, names: [
        n for n in names if (d == lib and n in STDLIB_SKIP) or n == "__pycache__" or n == "tests"])
    with open(os.path.join(tree, "_tuikio_run.py"), "w", encoding="utf-8") as fh:
        fh.write(_launcher_source())
    units = [(f"lib-{n}", lock, pkg, (), ()) for n, (lock, pkg, _, _) in LIBS.items()]
    units += [(gid, e["lock"], e["package"], e["subst"], e["skip"]) for gid, e in PY_GAMES.items()]
    for gid, lock, package, subst, skip in units:
        src = unpack(lock, os.path.join(work, "games", gid))
        for rel, old, new, *count in subst:
            replace_in(os.path.join(src, rel), old, new, *count)
        for rel, name in package.items():
            path = os.path.join(src, rel)
            dst = os.path.join(tree, name)
            if os.path.exists(dst):
                raise BuildError(f"python: {name} from {gid} clashes with another module")
            if os.path.isdir(path):
                shutil.copytree(path, dst, ignore=lambda d, names, p=path, s=skip: [
                    n for n in names if os.path.relpath(os.path.join(d, n), p) in s or n in ("__pycache__", "tests", "test")])
            else:
                shutil.copyfile(path, dst)
        for rel, dest in PY_GAMES.get(gid, {}).get("data", {}).items():
            tk.install_asset(f"games/{gid}/{dest}", os.path.join(src, rel))
    # Compile with the same interpreter version; store only the bytecode (no sources needed).
    out = os.path.join(work, "stdlib.zip")
    script = (
        "import sys, os, zipfile, py_compile, importlib.util\n"
        "tree, out = sys.argv[1:3]\n"
        "with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:\n"
        "    for d, dirs, files in sorted(os.walk(tree)):\n"
        "        dirs.sort()\n"
        "        for f in sorted(files):\n"
        "            p = os.path.join(d, f); rel = os.path.relpath(p, tree)\n"
        "            if f.endswith('.py'):\n"
        "                c = importlib.util.cache_from_source(p)\n"
        "                py_compile.compile(p, cfile=c, dfile=rel, doraise=True, optimize=2,\n"
        "                    invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)\n"
        "                zi = zipfile.ZipInfo(rel[:-3] + '.pyc', (1980, 1, 1, 0, 0, 0))\n"
        "                zi.compress_type = zipfile.ZIP_DEFLATED\n"
        "                z.writestr(zi, open(c, 'rb').read())\n"
        "            elif '__pycache__' not in rel and not f.endswith(('.pyc', '.so', '.dll', '.mp3', '.exe')):\n"
        "                zi = zipfile.ZipInfo(rel, (1980, 1, 1, 0, 0, 0))\n"
        "                zi.compress_type = zipfile.ZIP_DEFLATED\n"
        "                z.writestr(zi, open(p, 'rb').read())\n")
    subprocess.run([hostpy, "-I", "-c", script, tree, out], check=True)
    return out


_runtime = {}
_runtime_locks = {name: threading.Lock() for name in tk.ABIS}


def python_runtime(abi):
    with _runtime_locks[abi.name]:
        if abi.name not in _runtime:
            interp = build_interpreter(abi)
            archive = build_archive()
            out = os.path.join(abi.work("tuikio-python"), "game_python")
            tk.check_static_pie(interp, abi)
            with open(out, "wb") as fh:
                fh.write(open(interp, "rb").read())
                fh.write(open(archive, "rb").read())
            os.chmod(out, 0o755)
            _runtime[abi.name] = out
        return _runtime[abi.name]


_notice_lock = threading.Lock()


def write_runtime_notice():
    from recipes.scripts import archive_text
    with _notice_lock:
        path = os.path.join(tk.LICENSES, "python.txt")
        body = (f"CPython {VERSION} (libgame_python.so), the interpreter of the Python games, with zlib.\n"
                "Python Software Foundation License Version 2 (PSF-2.0).\n\n" + archive_text(CPYTHON, "LICENSE"))
        if not os.path.exists(path) or open(path, encoding="utf-8").read() != body:
            os.makedirs(tk.LICENSES, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)


def build_py_game(abi, gid):
    exe = python_runtime(abi)
    write_runtime_notice()
    from recipes.scripts import archive_text
    libs = "".join(f"\n\n{'=' * 72}\nIt uses {LIBS[n][3]}:\n\n" + archive_text(LIBS[n][0], LIBS[n][2])
                   for n in PY_GAMES[gid]["libs"])
    with _notice_lock:
        tk.EXTRA_NOTICES[gid] = ("\n\n" + "=" * 72 + "\nThis game runs on CPython " + VERSION +
                                 " (PSF-2.0, see python.txt), with ncurses (ncurses.txt)." + libs + "\n")
    return {"game_python": exe}


def register():
    for g, e in PY_GAMES.items():
        game(g, notice=(e["lock"], e["notice"]))(lambda abi, _g=g: build_py_game(abi, _g))


PY_GAMES.update({
    "lightcycle": py_game("lightcycle-48897113.tar", "LICENSE.md", {"lightcycle.py": "lightcycle.py"}, "lightcycle"),
    "pythrees": py_game("pythrees-3610a53a.tar", "LICENSE",
                        {"ThreesGame.py": "ThreesGame.py", "ThreesBoard.py": "ThreesBoard.py",
                         "TileDeck.py": "TileDeck.py"}, "ThreesGame"),
    "penneys-game": py_game("penney-9e3fd77c.tar", "LICENSE", {"penney": "penney"}, "penney", libs=("art",)),
    "pokete": py_game(
        "pokete-fc28e8a9.tar", "LICENSE",
        {"pokete.py": "pokete.py", "release.py": "release.py", "pokete_classes": "pokete_classes",
         "pokete_data": "pokete_data", "pokete_general_use_fns.py": "pokete_general_use_fns.py", "mods": "mods"},
        "pokete", libs=("scrap_engine",),
        subst=[
            # Saves in ~/pokete: hidden paths (~/.local/share) can't be exported or imported.
            ("release.py", 'SAVEPATH = Path(\n    os.environ.get(\n        "XDG_DATA_HOME",\n        str(Path.home()) + "/.local/share"\n    )\n) / "pokete"',
             'SAVEPATH = Path.home() / "pokete"'),
            # Never run code from the home: the oldest save format was a Python file it exec()s.
            ("pokete.py", '    elif os.path.exists(HOME / ".cache" / "pokete" / "pokete.py"):\n',
             "    elif False:  # Tuikio: saves are data, never code\n"),
            # No music: the player is a desktop library loaded with ctypes, and the MP3s are 81 MB.
            ("pokete_classes/audio.py", "import multiprocessing\n", ""),
            ("pokete_classes/audio.py", "            song: The song played\"\"\"\n        self.curr = multiprocessing.Process(",
             "            song: The song played\"\"\"\n        return  # Tuikio: no music player in this build\n        self.curr = multiprocessing.Process("),
            ("pokete_classes/audio.py", "        self.curr.terminate()\n",
             "        if self.curr is not None:\n            self.curr.terminate()\n"),
            # Games are offline: trading connects to another player over the network.
            ("pokete.py", "import socket\n", ""),
            ("pokete.py", '    """Trading with other players in the local network"""\n',
             '    """Trading with other players in the local network"""\n'
             '    ask_ok(mvp.movemap, "Trading needs a network connection,\\nand Tuikio games are offline.", mvp.movemap)\n'
             "    return\n"),
            # Runs `sh -c ""` (a Windows console trick); there is no shell.
            ("pokete.py", '    os.system("")\n', ""),
        ]),
    "dango": py_game("dango-18d2f72b.tar", "LICENSE.md", {"dango.py": "dango.py"}, "dango"),
})
register()
