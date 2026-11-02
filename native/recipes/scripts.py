"""Games written in interpreted languages, run by interpreters built from pinned source with the
same Zig toolchain as every other game (docs/RUNTIME.md, "Script games").

Bash games: one GNU Bash 5.2 (libgame_bash.so) serves every bash game. A game's scripts and data
are installed into its home (data_files); the manifest runs `game_bash <script>` with BASH_ENV
naming the prelude native/ports/bash/tuikio-bash.sh, which maps the few commands the games call
(stty, sleep, tput...) to two helpers in the native library directory: libtuikio_toybox.so
(a toybox with only those commands) and libtuikio_tput.so (ncurses' tput). Bash is patched to run
only the script files it was built for (native/ports/bash/tuikio_pinned.c): the SHA-256 of every
installed script is compiled into it, so a save archive that replaced a script can't run code.
Network redirections (/dev/tcp) are compiled out: games are offline.
"""
import os
import shutil
import tarfile
import threading

import tk
from tk import BuildError, game, install_asset, replace_in, run, unpack

PORTS = os.path.join(tk.HERE, "ports")
# Game scripts are text, the same for every ABI: they are prepared once, here.
STAGE = os.path.join(tk.BUILD, "scripts")
GPL2 = ("base-files_13ubuntu10.tar.xz", "licenses/GPL-2")


def _cached(out, key, build):
    """Reuses [out] when it was built with the same [key] (recipe inputs), else runs [build]."""
    stamp = out + ".key"
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
        return out
    built = build()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(built, out)
    os.chmod(out, 0o755)
    with open(stamp, "w") as fh:
        fh.write(key)
    return out


# ---------------------------------------------------------------- bash games

def bash_game(lock, notice, files, run_files, *, subst=(), data=()):
    """[files]: source path -> path in the game's home; [run_files]: the ones bash runs (pinned)."""
    return dict(lock=lock, notice=notice, files=files, run=run_files, subst=subst, data=data)


BASH_GAMES = {
    "piu-piu-sh": bash_game(
        "piu-piu-sh-c7da41c0.tar", "LICENSE.md", {"piu-piu": "piu-piu"}, ["piu-piu"],
        subst=[
            # Multiplayer runs nc over the network, and games are offline: no menu entry for it,
            # and no `hostname -I` lookup of the local address at start (no such command).
            ("piu-piu", "       caddr=( $(hostname -I) )\n", "       caddr=()\n"),
            ("piu-piu", "items=('' \"start $game\" 'multiplayer' 'configure' 'exit')",
             "items=('' \"start $game\" 'configure' 'exit')", 2),
            # A ~/.piuconf the player can't edit here; bash would refuse to source it anyway.
            ("piu-piu", "[[ -e ~/.piuconf ]] && . ~/.piuconf\n", ""),
        ]),
    "shellshock": bash_game(
        "shellshock-6b072c66.tar", GPL2, {"shellshock": "shellshock"}, ["shellshock"],
        subst=[
            # The high score is compared in (( )), where bash evaluates a crafted value as code:
            # read it without a `cat` command and keep it only when it is a plain number.
            ("shellshock", 'highscore=$(command cat "${HOME}/.shellshock" 2>/dev/null)',
             '{ highscore=$(<"${HOME}/.shellshock"); } 2>/dev/null; [[ $highscore =~ ^[0-9]{1,15}$ ]] || highscore=0'),
        ]),
}

# Extra notice text per game (appended to its LICENSES/<id>.txt).
BASH_NOTICES = {
    "shellshock": "ShellShock is Copyright 2012 Øyvind 'bolt' Hvidsten <bolt@dhampir.no>, released under the GNU General "
                  "Public License version 2 (stated in the header of the script; the text is above).\n",
}

PRELUDE = os.path.join(PORTS, "bash", "tuikio-bash.sh")
_stage_lock = threading.Lock()
_pinned = []


def stage_bash():
    """Installs every bash game's files into the assets once, and returns the SHA-256 of each file
    bash runs (the prelude and the games' scripts): the list compiled into bash."""
    with _stage_lock:
        if _pinned:
            return list(_pinned)
        hashes = {tk.sha256(PRELUDE)}
        for gid, e in BASH_GAMES.items():
            src = unpack(e["lock"], os.path.join(STAGE, gid, "src"))
            for rel, old, new, *count in e["subst"]:
                replace_in(os.path.join(src, rel), old, new, *count)
            for rel, dest in e["files"].items():
                path = install_asset(f"games/{gid}/{dest}", os.path.join(src, rel))
                if dest in e["run"]:
                    hashes.add(tk.sha256(path))
            install_asset(f"games/{gid}/tuikio-bash.sh", PRELUDE)
        _pinned.extend(sorted(hashes))
        return list(_pinned)


TOYBOX_COMMANDS = ("stty", "sleep", "date", "uname", "cat", "rm", "mktemp")


def build_toybox(abi):
    """A toybox with only the commands the prelude maps (fractional sleep needs TOYBOX_FLOAT)."""
    work = abi.work("tuikio-toybox")
    config = "".join(f"CONFIG_{c.upper()}=y\n" for c in ("toybox", "toybox_float") + TOYBOX_COMMANDS)

    def build():
        src = unpack("toybox_0.8.9+dfsg.orig.tar.xz", os.path.join(work, "src"))
        with open(os.path.join(work, "mini.config"), "w") as fh:
            fh.write(config)
        env = abi.env(CFLAGS=tk.CFLAGS, LDFLAGS=abi.ldflags, HOSTCC="gcc", NOSTRIP="1")
        run(f"make allnoconfig KCONFIG_ALLCONFIG={work}/mini.config HOSTCC=gcc", src, env)
        for c in TOYBOX_COMMANDS:  # the configuration must hold exactly what was asked for
            if f"CONFIG_{c.upper()}=y" not in open(os.path.join(src, ".config")).read():
                raise BuildError(f"toybox: {c} missing from the configuration")
        run(f"make toybox CC={abi.cc} HOSTCC=gcc", src, env)
        return os.path.join(src, "generated", "unstripped", "toybox")

    return _cached(os.path.join(work, "toybox"), config, build)


def build_tput(abi):
    """ncurses' own tput, linked like the games: terminal descriptions compiled in, no database."""
    work = abi.work("tuikio-tput")

    def build():
        src = unpack("ncurses_6.4+20240113.orig.tar.gz", os.path.join(work, "src"))
        obj = os.path.join(work, "obj")
        if os.path.exists(obj):
            shutil.rmtree(obj)
        os.makedirs(obj)
        env = abi.env(CPPFLAGS="")
        run(f"{src}/configure --host={abi.triple} --build=x86_64-pc-linux-gnu --prefix=/ "
            "--without-shared --with-normal --without-debug --without-ada --without-cxx "
            "--without-cxx-binding --without-manpages --without-tests "
            "--enable-widec --disable-database --without-pkg-config --disable-home-terminfo "
            "--with-fallbacks=xterm-256color,xterm,vt100,linux,dumb --with-build-cc=gcc "
            "--disable-stripping --without-gpm --enable-ext-colors --enable-ext-mouse "
            "--with-default-terminfo-dir=/nonexistent", obj, env)
        run("make -j2 libs", obj, env)
        run("make -C progs tput", obj, env)
        return os.path.join(obj, "progs", "tput")

    return _cached(os.path.join(work, "tput"), "ncurses 6.4+20240113 tput v1", build)


BASH_CONFIG = (
    "--without-bash-malloc --disable-nls --disable-readline --disable-history --disable-bang-history "
    "--disable-progcomp --disable-net-redirections --disable-help-builtin --without-curses --disable-mem-scramble"
)
# Answers to the configure checks that can't run while cross-compiling (musl on Linux).
BASH_CACHE = dict(
    bash_cv_getcwd_malloc="yes", bash_cv_job_control_missing="present", bash_cv_sys_named_pipes="present",
    bash_cv_dev_fd="standard", bash_cv_func_sigsetjmp="present", bash_cv_printf_a_format="yes",
    bash_cv_unusable_rtsigs="no", bash_cv_wcontinued_broken="no", bash_cv_func_ctype_nonascii="no",
    bash_cv_func_snprintf="yes", bash_cv_func_vsnprintf="yes", bash_cv_func_strcoll_broken="no",
    bash_cv_must_reinstall_sighandlers="no", bash_cv_opendir_not_robust="no", bash_cv_pgrp_pipe="no",
    bash_cv_ulimit_maxfds="yes", bash_cv_wexitstatus_offset="8", bash_cv_fnmatch_equiv_fallback="no",
)


def build_bash(abi, pinned):
    work = abi.work("tuikio-bash")
    header = ("/* Generated by native/recipes/scripts.py: SHA-256 of every script bash may run. */\n"
              "static const char *const tuikio_pinned[] = {\n"
              + "".join(f'    "{h}",\n' for h in pinned) + "    0\n};\n")
    pin_c = os.path.join(PORTS, "bash", "tuikio_pinned.c")

    def build():
        src = unpack("bash_5.2.21.orig.tar.xz", os.path.join(work, "src"))
        shutil.copyfile(pin_c, os.path.join(src, "tuikio_pinned.c"))
        with open(os.path.join(src, "tuikio_pinned.h"), "w") as fh:
            fh.write(header)
        replace_in(os.path.join(src, "Makefile.in"), "pcomplete.o pcomplib.o syntax.o xmalloc.o $(SIGNAMES_O)\n",
                   "pcomplete.o pcomplib.o syntax.o xmalloc.o $(SIGNAMES_O) tuikio_pinned.o\n")
        # The script named on the command line ...
        replace_in(os.path.join(src, "shell.c"),
                   "  free (dollar_vars[0]);\n  dollar_vars[0] = exec_argv0 ? savestring (exec_argv0) : savestring (script_name);\n",
                   "  { extern void tuikio_require_pinned_fd (const char *, int); tuikio_require_pinned_fd (filename, fd); }\n"
                   "  free (dollar_vars[0]);\n  dollar_vars[0] = exec_argv0 ? savestring (exec_argv0) : savestring (script_name);\n")
        # ... and every file sourced ($BASH_ENV, `source`, `.`).
        replace_in(os.path.join(src, "builtins", "evalfile.c"),
                   "  if (nr == 0)\n    {\n      free (string);\n      return ((flags & FEVAL_BUILTIN) ? EXECUTION_SUCCESS : 1);\n    }\n",
                   "  if (nr == 0)\n    {\n      free (string);\n      return ((flags & FEVAL_BUILTIN) ? EXECUTION_SUCCESS : 1);\n    }\n"
                   "  { extern void tuikio_require_pinned (const char *, const char *, size_t); "
                   "tuikio_require_pinned (filename, string, nr); }\n")
        env = abi.env(CC_FOR_BUILD="gcc", CPPFLAGS="", **BASH_CACHE)
        run(f"./configure --host={abi.triple} --build=x86_64-pc-linux-gnu --prefix=/ {BASH_CONFIG}", src, env)
        # No -rdynamic: there is nothing to load dynamically (enable -f can't work in a static
        # binary), and exported symbols only make the file bigger.
        run("make -j2 LOCAL_LDFLAGS=", src, env)
        return os.path.join(src, "bash")

    key = header + open(pin_c).read() + BASH_CONFIG + repr(sorted(BASH_CACHE.items()))
    return _cached(os.path.join(work, "bash"), key, build)


_runtime = {}
_runtime_locks = {name: threading.Lock() for name in tk.ABIS}


def bash_runtime(abi):
    """Bash and its helpers for one ABI, built once per run whichever bash game asks first."""
    with _runtime_locks[abi.name]:
        if abi.name not in _runtime:
            pinned = stage_bash()
            _runtime[abi.name] = {
                "game_bash": build_bash(abi, pinned),
                "tuikio_toybox": build_toybox(abi),
                "tuikio_tput": build_tput(abi),
            }
        return dict(_runtime[abi.name])


_notice_lock = threading.Lock()


def archive_text(lock, rel):
    """<top>/<rel> from a verified source archive, read without unpacking it."""
    with tarfile.open(tk.fetch(lock)) as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.removeprefix("./").split("/", 1)[-1] == rel:
                return tf.extractfile(m).read().decode("utf-8", "replace")
    raise BuildError(f"{rel} not found in {lock}")


def write_runtime_notices():
    """LICENSES/bash.txt and LICENSES/toybox.txt: the interpreter and helper every bash game ships
    with (ncurses, which tput is part of, is always listed)."""
    with _notice_lock:
        for name, lock, rel, head in (
            ("bash", "bash_5.2.21.orig.tar.xz", "COPYING",
             "GNU Bash 5.2.21, the interpreter of the bash games (libgame_bash.so).\n"
             "Copyright (C) 1987-2022 Free Software Foundation, Inc. License: GPL-3.0-or-later.\n\n"),
            ("toybox", "toybox_0.8.9+dfsg.orig.tar.xz", "LICENSE",
             "toybox 0.8.9 (libtuikio_toybox.so: stty, sleep, date, uname, cat, rm, mktemp) for the bash games.\n"
             "License: 0BSD.\n\n"),
        ):
            path = os.path.join(tk.LICENSES, f"{name}.txt")
            body = head + archive_text(lock, rel)
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != body:
                os.makedirs(tk.LICENSES, exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(body)


def build_bash_game(abi, gid):
    out = bash_runtime(abi)
    write_runtime_notices()
    with _notice_lock:
        tk.EXTRA_NOTICES[gid] = ("\n\n" + "=" * 72 + "\n" + BASH_NOTICES.get(gid, "") +
                                 "This game runs on GNU Bash (GPL-3.0-or-later, see bash.txt), with toybox (0BSD, "
                                 "toybox.txt) and ncurses' tput (ncurses.txt).\n")
    return out


for _g, _e in BASH_GAMES.items():
    game(_g, notice=(_e["lock"], _e["notice"]) if isinstance(_e["notice"], str) else _e["notice"])(
        lambda abi, _g=_g: build_bash_game(abi, _g))
