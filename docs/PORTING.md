# Porting a game to Tuikio

This guide is for developers who want to add a terminal game to Tuikio. It walks through one real
port from start to finish, then covers the variations: other languages, data files, saves, typing
games, online games, and how to decline a game you can't port.

Read it once top to bottom. After that, the [checklist](#the-checklist) at the end is enough.

**Contents**

1. [How a game runs in Tuikio](#1-how-a-game-runs-in-tuikio)
2. [Set up your machine](#2-set-up-your-machine)
3. [Is this game portable?](#3-is-this-game-portable)
4. [Worked example: VIper](#4-worked-example-viper), step by step
5. [Variations](#5-variations): autotools, C++, Rust, Go, Zig, bash, Python, data files, saves,
   typing games, online games
6. [Controls in depth](#6-controls-in-depth)
7. [Declining a game](#7-declining-a-game)
8. [Common problems](#8-common-problems)
9. [Opening the pull request](#9-opening-the-pull-request)
10. [The checklist](#the-checklist)

---

## 1. How a game runs in Tuikio

Tuikio runs the **real program** — the game's own C, C++, Rust, Go, Zig, bash or Python code — on
the phone. Nothing is emulated or rewritten. To make that possible on Android:

- **Every game is a static executable.** We cross-compile it with Zig's `cc` against musl libc, for
  three phone types (ABIs): `arm64-v8a`, `armeabi-v7a` and `x86_64`. Static means it needs nothing
  from the phone except the Linux kernel.
- **It ships inside the APK as `lib<name>.so`.** Android only lets an app run programs from its
  read-only native library directory (the "W^X" rule since Android 10). Naming the executable
  `libgame_viper.so` puts it there. It is a program, not a shared library; only the name says `.so`.
- **It runs in a pseudo-terminal.** A small helper (`native/pty`) starts the game on a PTY, and the
  app's own xterm-compatible terminal emulator (`core/terminal`) draws what it prints.
- **Touch controls send the game's keys.** A control profile (`catalog/profiles/*.json`) lays out a
  D-pad and buttons; each sends exactly the bytes the game expects. The game never knows it is on a
  phone.
- **A manifest describes the game** (`catalog/games/<id>.json`): title, executable, terminal size,
  orientation, controls, saves, licence. You don't write it by hand: it is generated from a short
  Python entry (step 7 below).

What you produce for one game:

| Piece | Where | What |
|---|---|---|
| Source pin | `native/sources.lock.json` | The exact upstream source, by commit and SHA-256 |
| Build recipe | `native/recipes/*.py` | How to compile it for each ABI |
| Patches (if needed) | in the recipe, or `native/ports/<game>/` | Small, checked fixes for Android |
| Catalog entry | `tools/ports/families/*.py` | Title, controls, sizes, description, licence |
| Play script | `native/tests/play.json` | The first moves, played automatically in tests |
| Generated files | `catalog/games/<id>.json`, `LICENSES/`, README credits, card art | Made by tools, committed |

---

## 2. Set up your machine

Linux (or WSL) on x86_64. You need:

| Tool | Version | Install |
|---|---|---|
| JDK | 17 or newer | your package manager |
| Python | 3.10 or newer, with PyYAML | `pip install pyyaml pyte` (pyte is for the play-tester) |
| Zig | 0.17.0 | `pip install ziglang==0.17.0`, or set `ZIG=/path/to/zig` |
| gcc, make, flex, bison, ncurses and zlib headers | any | e.g. `apt install build-essential flex bison libncurses-dev zlib1g-dev` |
| Rust (only for Rust games) | 1.97.0 + musl targets | `rustup target add aarch64-unknown-linux-musl armv7-unknown-linux-musleabihf x86_64-unknown-linux-musl` |
| Go (only for Go games) | 1.24.7 | go.dev |
| Android SDK (only for the APK) | platform 36, build-tools 36 | `docs/BUILD.md` |
| qemu-user-static (optional) | any | runs the ARM builds on your PC |

Check everything works by building one existing game:

```sh
python3 native/build.py --abi x86_64 --game viper-snake
ls native/build/out/x86_64/          # libgame_viper.so is there
```

`docs/BUILD.md` has the full details.

---

## 3. Is this game portable?

Answer these before writing any code. If one answer is "no", the game is
[declined](#7-declining-a-game) with the reason recorded; that is a normal, useful outcome.

1. **Licence.** Is there a free licence that allows redistribution (MIT, BSD, GPL, Apache, zlib,
   public domain…)? No licence file and no licence statement means *all rights reserved*: decline.
   Non-free data (ROMs, commercial game files) also means decline.
2. **Does it run in a terminal?** It must draw with text: curses, escape sequences, or plain
   `printf`. Games that need X11, SDL, a GPU or a mouse-only GUI can't be ported.
3. **Input.** It must read keys from standard input (or a tty). Games that read `/dev/input` or need
   root (for example the Python `keyboard` library) can't work.
4. **No network** (unless it is an online game, see [5.10](#510-online-games)). Multiplayer over
   sockets is removed or the game is declined.
5. **No shell or other programs.** Games may not start other programs (`system()`, `popen()`,
   `exec`, `subprocess`). There is no `/bin/sh` on many phones, and Tuikio gives games none. Small
   uses (clearing the screen, a pager) can be patched out; a game that needs an external engine
   (for example chess against Stockfish) is declined.
6. **Size.** Aim for under ~5 MB of program per ABI and under ~10 MB of data.
7. **Can it be played with a pad and a few buttons**, or by typing? Almost every terminal game can.

---

## 4. Worked example: VIper

[VIper](https://github.com/girst/viper) is a snake game in a single C file, licensed GPL-3.0. It
draws with escape sequences itself (no curses), reads keys from the terminal, and keeps no files.
This is the smallest real port in Tuikio; every port follows the same eight steps.

### Step 1: Pin the source

Tuikio never builds from a moving branch. Every source is pinned to an exact commit, and the archive
made from it is pinned by SHA-256, so a build today and a build in five years use identical code.

Find the commit you want to port (usually the latest on the default branch):

```sh
git ls-remote https://github.com/girst/viper HEAD
# edd02980f70019b1d01508467c671282561ed778  HEAD
```

Pin it. The archive name is `<name>-<first 8 characters of the commit>.tar`:

```sh
python3 tools/ports/git_lock.py viper-edd02980.tar https://github.com/girst/viper edd02980f70019b1d01508467c671282561ed778
```

This downloads exactly that commit, archives it, and adds an entry to `native/sources.lock.json`:

```json
"viper-edd02980.tar": {
  "git": "https://github.com/girst/viper",
  "commit": "edd02980f70019b1d01508467c671282561ed778",
  "sha256": "a6511619cab49f28abb0961b6cf1ba4afe1ca53e930fdaf78ae25f006725b619"
}
```

Other kinds of source:

- **Ubuntu package** (many classic games are packaged there):
  `python3 tools/ports/ubuntu_sources.py --lock <source package>`. It checks the archive against
  Ubuntu's signed index.
- **A release tarball**: add `{"url": "...", "sha256": "..."}` to `native/sources.lock.json` yourself.

### Step 2: Read the code

Before compiling, read how the game:

- **reads keys** (`getch`, `read`, `getchar`…), and which keys it uses: you need all of them for
  the controls;
- **draws** (curses, or escape sequences), and what terminal size it needs;
- **uses files**: paths under `/usr/share`, `/var/games`, `/tmp`, `~/.something`;
- **calls the system**: search for `system(`, `popen(`, `exec`, `fork`, `socket`.

```sh
mkdir -p /tmp/viper && tar -xf native/.cache/dl/viper-edd02980.tar -C /tmp/viper
grep -nE "system\(|popen\(|exec|socket|/usr/|/var/|/tmp" /tmp/viper/src/*.c
```

VIper uses none of these, so it needs no patches. Its keys are the arrows (and `hjkl`), `p` to pause
and `r` to restart.

### Step 3: Write the recipe

Recipes are Python functions registered with `@game(...)`, grouped in modules under
`native/recipes/`. `more.py` is a good home for a single game. VIper's recipe:

```python
@game("viper-snake", curses=False, notice=("viper-edd02980.tar", "LICENSE"))
def build_viper(abi):
    """VIper: snake with vi keys and colour schemes. It draws with escape sequences itself."""
    src = unpack("viper-edd02980.tar", os.path.join(abi.work("viper"), "src"))
    exe = os.path.join(abi.work("viper"), "game_viper")
    cc(abi, [os.path.join(src, "viper.c")], exe, "-std=gnu99", "", cwd=src)
    return {"game_viper": exe}
```

Line by line:

- `@game("viper-snake", ...)`: the game's **id**. It is used everywhere: manifest name, play script,
  card art. Lowercase, digits and hyphens.
- `curses=False`: VIper doesn't link ncurses. Leave the default (`True`) for curses games, and
  ncurses is built and linked for you.
- `notice=(archive, path)`: where the licence text is inside the source. It is copied to
  `LICENSES/viper-snake.txt` and shipped in the app.
- `unpack(...)`: a fresh, verified copy of the pinned source for this ABI.
- `cc(abi, files, output, cflags, libs, cwd=...)`: compiles and links a static PIE for this ABI,
  with the Android compatibility shim. For a curses game pass `abi.curses_libs` as libs.
- `return {"game_viper": exe}`: the executable's name (`game_` + something) maps to the file. It
  becomes `libgame_viper.so`. One recipe may return several programs.

Useful helpers in `native/tk.py`:

| Helper | Use |
|---|---|
| `unpack(lock, dest)` | fresh, checksum-verified copy of a pinned source |
| `cc(abi, srcs, out, cflags, libs, cwd=, cxx=)` | compile and link in one go |
| `compile_objects` / `link` | the same in two steps, for big projects |
| `autotools(abi, src, configure_args, make=...)` | `./configure && make` cross-compiled |
| `replace_in(path, old, new)` | an exact patch; the build fails if `old` isn't found exactly once |
| `install_asset("games/<id>/<path>", file)` | a data file shipped with the game (see 5.8) |
| `run(cmd, cwd, env)` | any other build command, logged |
| `tk.cargo(...)` / `go_build(...)` | Rust and Go builds |

### Step 4: Build it

```sh
python3 native/build.py --abi x86_64 --game viper-snake     # quick, one ABI
python3 native/build.py --game viper-snake                  # all three ABIs
```

Failures print the command and its output. `native/build/<abi>/work/<game>/` keeps the build tree
for you to inspect.

### Step 5: Play it on your PC

Before touching the app, play the binary in a pseudo-terminal exactly like the phone would. The
play-tester sends keys the way the app does and prints the screen:

```sh
TUIKIO_OUT=$PWD/native/build/out \
  python3 docs/handoff/tools/explore.py viper-snake game_viper 40x24 w1500 s kUP w400 kLEFT w400 s
```

Steps: `w<ms>` wait, `t<text>` type text (`\n` is Enter), `k<KEY>` press a key
(`UP DOWN LEFT RIGHT ENTER ESC SPACE TAB BS`), `s` print the screen.

Check, honestly:

- it starts without errors;
- every key the game uses works;
- pause, help, quit, game over and restart all work;
- it fits the size you chose: try it bigger too, and see if something was cut off.

You can also run it directly: `native/build/out/x86_64/libgame_viper.so` in your terminal.

### Step 6: Choose the controls

Look in `catalog/profiles/` for a profile that fits. Common ones:

| Profile | For |
|---|---|
| `arrows4.v1` | D-pad (arrow keys) + Quit |
| `arrows.v1` | D-pad + Select (Enter) + Space + Back |
| `wasd4.v1` | D-pad that sends W A S D |
| `vikeys8.v1`, `roguelike.v1`, `dungeon8.v1` | 8-way roguelikes |
| `blocks.v1` and friends | falling-block games |
| `text.v1` | typing games: Enter, Space, Erase + the phone keyboard |

VIper uses `arrows4.v1`. It also has Pause (`p`) and Restart (`r`), which the profile doesn't
have, so we add them as the game's own **keys** (buttons in a strip under the game). Details and
more options are in [section 6](#6-controls-in-depth).

### Step 7: Add the catalog entry

Catalog entries live in `tools/ports/families/<family>.py`, next to the recipe module of the same
name. VIper's, in `families/more.py`:

```python
dict(id="viper-snake", title="VIper", exe="game_viper", controls="arrows4.v1", orientation="portrait",
     terminal=((40, 24), (40, 24)), keys=["Restart=r", "Pause=p"],
     summary="Snake in Unicode, with fruit, bonuses and a speed that keeps rising.",
     description="Steer with the pad and eat the fruit; some foods slow you down or shorten the snake. "
                 "Restart after a crash.",
     category="arcade", tags=["snake", "classic"], authors=["Tobias Girstmair"], license="GPL-3.0-only",
     **gh("girst/viper", "edd02980"), discovery="viper-snake",
     test_notes="Host test: field, food, steering, game over and restart."),
```

| Field | Meaning |
|---|---|
| `id`, `exe` | as in the recipe |
| `title`, `summary` (≤140 chars), `description` | what players read. Say what the buttons do, in plain words |
| `category` | one of `arcade puzzle strategy cards words roguelike adventure simulation` |
| `controls` | the profile id |
| `keys`, `labels`, `hide` | extra buttons, renamed buttons, hidden buttons (section 6) |
| `terminal` | `((min cols, min rows), (preferred cols, rows))`. Use the smallest size the game really needs: bigger means smaller text |
| `orientation` | `portrait` (≤ ~50 columns) or `landscape` (80 columns and wider) |
| `authors`, `license` | upstream authors and the SPDX licence id |
| `**gh(repo, commit8)` | fills `source_url`, `version` and `archive` |
| `discovery` | the id of its entry in `catalog/discovery.json`, if the game was listed there |
| `saves` | `(["file", "dir/file"], "what they are")`, relative to the game's home (5.9) |
| `args`, `env` | command-line arguments and environment variables |
| `wrap="words"`, `input="typing"` | for text games (5.10) |
| `test_notes` | what you actually tested. Never claim more than you did |

Generate the manifest, then validate the whole catalog:

```sh
python3 tools/ports/manifests.py more
./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"
```

`manifests.py` writes `catalog/games/viper-snake.json` and marks the discovery entry as ported. Don't
edit the JSON by hand; edit the family entry and run it again.

### Step 8: Add the play script, credits and card picture

**Play script.** `native/tests/play.json` holds the first moves of every game. The tests start the
real binary like the app does and fail if the script stops matching:

```json
"viper-snake": ["expect:0000", "key:UP", "wait:400", "key:LEFT", "wait:300"]
```

Steps: `expect:<text on screen>`, `type:<text>` (`\n` is Enter), `key:<KEY>`, `wait:<ms>`. Make it
tolerant of timing: wait before keys on animated title screens, and expect text that appears in
every outcome.

```sh
./gradlew :core:runtime:test -PrequireNative --tests '*PlayScriptsTest*'
```

**Credits and licences.** The build already wrote `LICENSES/viper-snake.txt`. Update the README's
credits table:

```sh
python3 tools/catalog/gen_credits.py && python3 tools/catalog/gen_credits.py --check
```

**Card picture.** Each game's card in the app shows its real screen. Render it, capture it, and look
at the result:

```sh
./gradlew :app:test --tests '*RenderShotsTest.portrait' --tests '*RenderShotsTest.landscape' -Pshots=viper-snake
python3 tools/catalog/capture_art.py
./gradlew :app:test --tests '*RenderShotsTest.cards' -Pshots=all     # then open app/build/shots/cards-*.png
```

If the crop shows a title screen or something dull, add a deeper script for it to
`native/tests/shots.json` (same steps as `play.json`, plus `shot:<name>`) and capture again.

**That's the whole port.** Run the [checklist](#the-checklist) and open a pull request.

---

## 5. Variations

### 5.1 Curses games

Most terminal games use curses. Leave `curses=True` (the default) and link `abi.curses_libs`:

```python
cc(abi, files(src, "src/*.c"), exe, "-std=gnu99 -DDATADIR=.", abi.curses_libs, cwd=src)
```

Tuikio's ncurses is wide-character (`ncursesw`), has the terminal descriptions built in, and is also
reachable as `-lncurses`, `-lcurses` and `<curses.h>`. It is built with an **opaque `WINDOW`**: code
that pokes `win->_cury` must use `wmove()` instead.

### 5.2 Autotools (`./configure && make`)

```python
@game("mygame", notice=("mygame_1.2.orig.tar.gz", "COPYING"))
def build_mygame(abi):
    src = unpack("mygame_1.2.orig.tar.gz", os.path.join(abi.work("mygame"), "src"))
    autotools(abi, src, "--disable-nls --prefix=/", make="make -j4")
    return {"game_mygame": os.path.join(src, "mygame")}
```

If `make -j` races, use `make -j1`. If the build runs a program it just compiled (a table
generator), that program was built for the phone: build it with `gcc` for the host first, or run it
under qemu (see GNU Go in git history).

### 5.3 C++ and old C

- C++: `cc(..., cxx=True)`. Code from the 2000s may need `-Wno-register` (C++17 removed `register`).
- Old K&R C: add `tk.LEGACY` to the flags (`autotools()` does it for you; with `cc()` pass it in
  `cflags`). Implicit function declarations stay an error on purpose: on 64-bit they silently
  truncate pointers.

### 5.4 Rust

`native/recipes/rust.py`. Pin the repository, make sure it has a `Cargo.lock`, and build with
`tk.cargo(abi, src, "binary-name")`; it builds `--locked` for the musl target and links with Zig.
Most Rust games only need an entry in the recipe's table, which also collects each crate's licence
(`crate_notices`). Rust games are large (2–5 MB); that's normal.

### 5.5 Go

`native/recipes/rustgo.py`, `go_build(abi, src, pkg, out)`: cgo on, external link with the ABI's Zig `cc`, static
PIE.

### 5.6 Zig

Pin the Zig release the game was written for (Zigtris uses 0.15.1 via `ZIG_0_15`). Zig's package
fetcher doesn't work through proxies: give dependencies as local paths to pinned sources. Set
`exe.pie = true` in `build.zig`.

### 5.7 Bash, awk and Python games

Interpreted games run on interpreters Tuikio builds from pinned source. They can only run their own
pinned code: a save file or a downloaded script can never be run.

- **Bash** (`native/recipes/scripts.py`, `BASH_GAMES`): one GNU Bash serves every bash game. Add a
  `bash_game(lock, licence, files, run_files, subst=[...])` entry. Bash runs only scripts whose
  SHA-256 is compiled into it. A prelude maps `stty`, `sleep` and `tput` to built-in helpers;
  `/dev/tcp` is compiled out.
- **Python** (`native/recipes/python.py`, `PY_GAMES`): one CPython 3.13 serves every Python game. The
  standard library and all game code are a zip archive appended to the interpreter, and Python
  imports only from there. Add a `py_game(lock, licence, {source path: module name}, "module:function")`
  entry, with `libs=` for pure-Python dependencies (`LIBS`) and `subst=` patches.
  The interpreter has **no `socket`, `subprocess`, `ctypes` or `multiprocessing`**: patch out the
  code that imports them (Pokete's recipe shows how: music, LAN trading and `os.system` removed).
  Never let a game `exec()` or `pickle.load()` a file from its home.

### 5.8 Data files

Games that read data (levels, word lists, WADs) get it installed into their home directory, which is
their working directory:

```python
for name in os.listdir(os.path.join(src, "levels")):
    install_asset(f"games/npush/levels/{name}", os.path.join(src, "levels", name))
```

Then patch the game to look in `.` (or `./levels`) instead of `/usr/share/<game>`, for example:

```python
replace_in(os.path.join(src, "src", "game.c"), '"/usr/share/mygame/levels"', '"levels"')
```

(nPush's recipe in `native/recipes/more.py` is a real example: it also renames level files that
had spaces in their names.)

`manifests.py` records each data file's SHA-256 in the manifest; the app checks them on install.
**File names may not start with a dot or contain spaces** (Android drops hidden files from APKs):
rename them and patch the code.

### 5.9 Saves and high scores

The game's home directory is private to it. List the files to keep in the catalog entry, so players
can export and import them:

```python
saves=(["angband/save", "angband/scores.raw"], "Your characters and high scores"),
```

Paths are relative to the home. Hidden paths (`~/.game`) are rejected: patch the game to use
`~/game` instead (Angband and Pokete do this).

### 5.10 Typing games, word games, text adventures

```python
dict(..., controls="text.v1", input="typing", wrap="words", orientation="portrait", terminal=((48, 32), (48, 32)))
```

`input="typing"` opens the phone keyboard when the game starts. `wrap="words"` wraps long lines at
word boundaries instead of mid-word. A 48-column portrait screen reads far better than 80 columns
squeezed sideways.

### 5.11 Online games

Online games are played on someone else's server over SSH or telnet; nothing of the game runs on the
phone. Players must turn **Online games** on first (it's off by default), and see the server's name
before connecting. Add one entry to `tools/ports/families/online.py`:

```python
dict(id="my-server", title="My Server", online={"protocol": "ssh", "host": "games.example.org"},
     controls="arrows.v1", **SSH, summary="...", description="...", category="arcade",
     tags=[...], authors=[...], license="MIT", source_url="https://..."),
```

and its id to `ONLINE_GAMES` in `native/recipes/online.py`. Rules: only public servers you have
confirmed are up and free to play; say in the description what the player shares (a name, chat);
no saves on the phone; no `args` (they're built from `online` only).

---

## 6. Controls in depth

The goal: **every key the game needs is reachable without the keyboard**, and nothing on screen is
a button that does nothing.

### Extra keys (`keys`)

A compact list of buttons shown under the game:

| Notation | Meaning |
|---|---|
| `"Pause=p"` | a button labelled Pause that types `p` |
| `"Menu=<ESCAPE>"` | sends a named key: `ESCAPE TAB ENTER BACKSPACE UP DOWN LEFT RIGHT HOME END PAGE_UP PAGE_DOWN F1`…`F12` |
| `"#1-9"` | one button per digit 1 to 9 |
| `"a1=a1\r"` | types `a1` and Enter |

### Renaming and hiding profile buttons

```python
labels={"select": "Place", "quit": "Back"},   # the profile's Select button now reads "Place"
hide=["back"],                                # the game has no use for Back: no button
```

### A new profile

When nothing fits, copy a similar file in `catalog/profiles/` (`doom.v1.json` is a full example).
Profiles declare actions (what each button sends, repeat timing, "are you sure?" for Quit/Restart,
states such as Pause turning into Resume when the screen says "Paused") and a layout for portrait and
landscape. Then:

```sh
./gradlew :core:controls:test     # fails if the buttons don't fit on small phones
```

### What the app adds by itself

You don't configure these; they work for every game:

- **Answer chips:** when the game asks a question (`(y/n)`, `[abcq]`, `Press any key`), the answers
  appear as buttons.
- **Key hints:** when the screen names a key no button sends ("press `?` for help"), it appears as a
  chip.
- **Pause and Quit:** the app's Pause freezes the game; while paused, a Quit button appears beside it.

---

## 7. Declining a game

Not every game can or should be ported. A decline is recorded, with the reason, so nobody spends
time on it again. Add it to a file in `tools/ports/triage/`:

```json
{
  "terminal-frogger": {"license": "UNKNOWN", "notes": "Declined 2026-11-04: the repository has no licence, so it can't be redistributed."}
}
```

```sh
python3 docs/handoff/tools/apply_triage.py 2026-11-04
```

Good reasons are specific: no licence; needs X11 or SDL; needs root input devices; spawns an external
engine; needs a server that no longer exists; built but crashes in a way we couldn't fix (say where).

---

## 8. Common problems

| Symptom | Cause and fix |
|---|---|
| Game can't find its data | It looks in `/usr/share/...`. Install the data with `install_asset` and patch the path to `.` |
| `sh: not found`, pager doesn't open | `system()`/`popen()`. Patch it out; for pagers use `$PAGER` directly (the BSD games recipes show how) |
| Arrow keys quit the game | It doesn't call `keypad()` and reads `ESC` as Escape. Use the arrow form the game expects, or a WASD/vi-keys profile |
| Garbled box-drawing characters | The game never calls `setlocale(LC_ALL, "")`. Add it, or patch the program to use ASCII |
| Saves rejected by the validator | Hidden path (`~/.game`) or a space in a name. Rename and patch |
| Works on PC, not in tests | The play script is too fast: animated title screens drop early keys. Add `wait` steps |
| `win->_cury` doesn't compile | Opaque `WINDOW`: use `wmove()` / `getyx()` |
| C++ `register` error | add `-Wno-register` |
| Build passes, card shows a menu | Add a deeper script to `native/tests/shots.json` and rerun `capture_art.py` |
| Test "passes" suspiciously | Gradle reused an old result: rerun with `--rerun-tasks` |

More lessons from earlier ports: `docs/handoff/LESSONS.md`.

---

## 9. Opening the pull request

1. Run the checks below; all must pass.
2. Commit the recipe, family entry, `native/sources.lock.json`, `native/tests/play.json`, and the
   generated files (`catalog/games/<id>.json`, `catalog/discovery.json`, `LICENSES/`, `README.md`).
3. In the description, write what you tested on the PC (and on a phone, if you did), any patches and
   why, and anything you couldn't make work.
4. CI builds every game for all three ABIs, plays every script and starts every game in the app.
   Fix it until it's green.

Never claim a game was tested on a phone unless you played it on one: statuses in the catalog are
honest (`PORTABLE` means it builds and plays in the PC tests; `ANDROID_TESTED` needs real evidence).

---

## The checklist

```text
[ ] Licence allows redistribution; licence file path known
[ ] Source pinned (git_lock.py / ubuntu_sources.py / url+sha256)
[ ] Recipe builds on all three ABIs:          python3 native/build.py --game <id>
[ ] No system()/popen()/exec/sockets left; data and save paths point into the home
[ ] Played in a PTY: start, every key, pause/help/quit/game over, size fits
[ ] Controls: every key reachable without the keyboard; nothing useless on screen
[ ] Catalog entry written; manifest generated:  python3 tools/ports/manifests.py <family>
[ ] Catalog valid:      ./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"
[ ] Controls fit:       ./gradlew :core:controls:test
[ ] Play script passes: ./gradlew :core:runtime:test -PrequireNative --tests '*PlayScriptsTest*'
[ ] Credits:            python3 tools/catalog/gen_credits.py && python3 tools/catalog/gen_credits.py --check
[ ] Card picture captured and looked at
[ ] App tests:          ./gradlew :app:test
[ ] test_notes say exactly what was tested
```

Questions, or a game you're unsure about? Open an issue with the game's link and what you found in
[step 3](#3-is-this-game-portable).
