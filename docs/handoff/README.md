# Tuikio handoff

Read this first. It is written for the next developer, human or AI, who continues Tuikio without
access to the conversations that built it. Everything you need is in this folder and the docs it
points to.

| File | What it holds |
|---|---|
| `README.md` (this) | What Tuikio is, where everything is, how to build, test and release, current state, next steps |
| `RULES.md` | The owner's rules and the project's standing decisions. **Follow them.** |
| `HISTORY.md` | The conversation, condensed: what the owner asked for, in order, and what was done and decided |
| `PLAYBOOK.md` | Step-by-step recipes for the recurring jobs: port a game, audit, card art, release, CI |
| `../PORTING.md` | The developer guide to porting a game, with a worked example (start here for ports) |
| `LESSONS.md` | Mistakes made and what they taught: read before changing anything subtle |
| `PORTING-BRIEF.md` | The brief given to porting helpers: the rules and workflow for one game, in detail |
| `tools/` | Scratch tools used during development (PTY play-tester, JSON merge, triage applier, audit table) |

## What Tuikio is

An Android app (package `dev.tuikio.app`, GPL-3.0-or-later, owner **Ömer SÜSİN**, GitHub
`omersusin/tuikio`, which GitHub now redirects to `ilker-binzet/tuikio`) that runs **real
terminal/TUI games on phones**. The games are native ports: each is a static-PIE musl ELF built from
pinned source and packaged in the APK as `lib<exe>.so`, then run in a PTY behind an
xterm-compatible terminal emulator written in Kotlin. The touch controls adapt to each game. It has
an original design language with a mascot, **Kio**, plus brand packs, a catalog with honest
statuses, community suggestion/publishing features (server code exists, not deployed), saves
export/import, and credits for every game.

At 1.1.0 there are **169 games**: 163 offline ports, the original **Kio: Lantern Tide**, and 5
online games. They cover BSD games, the New BSD Games, Ubuntu packages, GitHub
C/C++/Rust/Go/Zig games, NetHack, Angband, Brogue, Rogue, Doom (ASCII with Freedoom), 25 Shell
Games, two bash games, an awk raycaster, five Python games (Pokete, Lightcycle, PyThrees,
Penney's Game, Dango) on a bundled CPython, and online games over SSH/telnet behind an opt-in
switch (docs/RUNTIME.md, "Python games" and "Online games"). Every game is labelled **"Preview port"** because none has been confirmed on a real
phone yet (see RULES.md: no false `ANDROID_TESTED` claims).

## Where things are

| Path | What |
|---|---|
| `app/` | The Android app (Kotlin, **no AndroidX/Material**: own UI toolkit in `app/src/main/kotlin/dev/tuikio/app/ui`). Game screen: `game/GameActivity.kt`, `game/TerminalView.kt`, `game/ControlsView.kt`, `game/GameBell.kt`. Screens: `screens/`. Data: `data/` |
| `core/terminal` | The terminal emulator (VT/xterm, UTF-8, wide chars, 256/truecolour, mouse, alt screen) and key encoder |
| `core/controls` | Control profiles, layout engine, dispatcher, `PromptChips` (answer chips for questions), `KeyHints` (chips for keys the screen names) |
| `core/catalog` | Manifest/profile/discovery models and parsers (`GameManifest.kt`), JSON reader |
| `core/runtime` | Launching games (PTY helper protocol), saves, and the runtime tests that play every game (`PlayScriptsTest`, `RealGamesTest`, `SuspendResumeTest`) |
| `core/community`, `backend/` | Community suggestion/publish client and server (tested, **not deployed**) |
| `build-logic/` | Custom Gradle plugin (`AndroidAppPlugin.kt`): there is **no Android Gradle Plugin** (Google Maven is blocked where this was built). It runs aapt2, ProGuard, d8, zipalign and apksigner itself, and builds universal and per-ABI APKs |
| `native/` | Native build: `build.py` (entry point), `tk.py` (toolkit), `recipes/*.py` (one module per source family), `ports/<game>/` (patches, stand-in headers, launchers), `compat/` (Android shims linked into every game), `pty/` (PTY helper, pager), `original/lantern-tide`, `tests/play.json` and `tests/shots.json` (play and screenshot scripts), `sources.lock.json` (every source pinned by SHA-256 / commit) |
| `catalog/` | `games/*.json` (one manifest per game, **generated**), `profiles/*.v1.json` (control profiles), `discovery.json` (every known game, ported or not, with notes), `schema/` |
| `tools/ports/` | `families/*.py` (catalog metadata per game, **the source of the manifests**), `manifests.py` (writes `catalog/games` and links discovery), `git_lock.py` (pin a git source), `ubuntu_sources.py` (pin an Ubuntu source package via the signed index), `triage/*.json` (declined candidates with reasons) |
| `tools/catalog/` | `capture_art.py` (card pictures from screenshots), `gen_credits.py` (README credits), `import_spec_links.py` |
| `tools/catalog-cli` | Catalog validator (`./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"`) |
| `tools/release/` | `check_apk.py` (release checks), `make-keystore.sh` |
| `LICENSES/` | Licence texts and `SOURCES.txt`, **generated by `native/build.py`**, bundled into the APK |
| `docs/` | `BUILD.md`, `RUNTIME.md`, `CATALOG.md`, `ARCHITECTURE.md`, `AUDIT.md` (per-game audit, rounds 1–5), `STATUS.md`, `RELEASE.md`, `COMMUNITY.md`, `PRIVACY.md`, `PERFORMANCE.md` |

## Build, test, release (short version; details in PLAYBOOK.md and docs/BUILD.md)

Toolchains: JDK 17+ (CI uses 21); Python 3.10+; **Zig 0.17.0** (`pip install ziglang==0.17.0`, or
`ZIG=`); **Zig 0.15.1** for Zigtris (`pip install --target /opt/tuikio-tools/zig-0.15 ziglang==0.15.1`,
or `ZIG_0_15=`); **Rust 1.97.0** with the targets `aarch64-unknown-linux-musl`,
`armv7-unknown-linux-musleabihf` and `x86_64-unknown-linux-musl`; **Go 1.24.7**; Android SDK
platform 36 and build-tools 36; gcc, make, flex, bison and ncurses headers; `qemu-user-static` (ARM
smoke tests); PyYAML (Open Adventure's build).

```sh
python3 native/build.py                     # all games, 3 ABIs (~30+ min); --game X --abi x86_64 for one
./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"
python3 tools/catalog/gen_credits.py --check
./gradlew :core:terminal:test :core:controls:test :core:catalog:test :core:community:test :backend:test
./gradlew :core:runtime:test -PrequireNative     # plays every game's script against the real binaries
./gradlew :app:test                              # Robolectric UI tests, start every game on the game screen
cp <key dir>/signing.properties . && ./gradlew :app:assembleReleaseApk :app:assembleReleaseSplitApks; rm signing.properties
python3 tools/release/check_apk.py app/build/outputs/apk/release/tuikio-release*.apk
```

CI (`.github/workflows/ci.yml`) runs all of that except release signing on every push to `main`
and `claude/**`. It has three jobs: JVM tests + catalog; native build + PTY smoke + runtime tests;
UI tests + debug APK.

### The release signing key: important

The release key (`tuikio-release.p12`, RSA 4096, alias in `signing.properties`, password in
`keystore-password.txt`; certificate SHA-256
`d8ea95d3e2e4e6c65983e8a42f613695fd4a668bb42f5b62d06fca2405be0874`) is **deliberately not in Git**.
It was handed to the owner with this handoff. **Every future APK must be signed with it**, or it
won't install over existing installs (users would have to uninstall and lose saves). Keep it
somewhere safe (a password manager or encrypted storage). Never commit it, paste it into chat or
CI logs, or put it in the APK. `docs/RELEASE.md` explains the signing setup; `signing.properties`
points at the key file and password file. Copy it into the repo root only for the release build,
and delete it right after (`.gitignore` excludes it anyway).

## Current state (1.1.0, 2026-11-04)

- 1.1.0 (versionCode 10) adds the Python runtime (5 games) and online games (5, opt-in). 169
  games; 57 control profiles; 241 discovery entries. The online games were **never connected to
  their real servers** (the build machine had no DNS or SSH/telnet egress): test them on a phone
  first and drop any whose server is gone.
- 1.0.0 history: version 1.0.0 (versionCode 9). Signed APKs: universal (~95 MB) and per-ABI (~40 MB each:
  arm64-v8a is the one for almost every phone). The release commit is `d0c7606` on the branch. The
  `v1.0.0` tag could not be pushed from that environment (only the branch could): create it with
  `git tag -a v1.0.0 d0c7606 -m "Tuikio 1.0.0" && git push origin v1.0.0`. **No GitHub Release page
  was created**: make one from the tag and attach the APKs if you want public downloads. That needs
  the owner's approval: publishing is their decision.
- All tests pass locally. CI was green at the last runs checked; check the latest run on the branch.
- Work happened on branch `claude/new-session-h45p5a` (no PR was opened; `main` is behind). Merging to
  `main` is the owner's call.
- Never tested on a real phone since 0.1.1 (POCO F5, Android 17: an early crash was fixed). The
  biggest unknown is real-device behaviour; see "Next steps".

## Next steps (in priority order)

1. **Test on a real phone** (arm64): install `tuikio-1.0.0-arm64-v8a.apk`, run Settings ›
   Diagnostics, then play a sample from each control profile family. Fix what breaks. Record
   `android_tested` evidence in manifests only after real play (see RULES.md).
2. **Merge to `main`** and make a GitHub Release with the APKs, if the owner approves.
3. **Remaining candidates** (`catalog/discovery.json`, status `CANDIDATE` without `last_checked`):
   - Plausible C/C++ ports, each needing a source found and pinned: MyMan, ASCII Dash, alienwave,
     astwar, gnuski, oldrunner, nibbles/cnibbles, nsudoku, minecurses, starlanes, conquest
     (beejjorgensen), hydra-slayer (check for a terminal mode), omega (check the licence),
     asciiportal (check for a curses build), 0verkill (client/server: local play?), ft-retro,
     SporkHack (a half-done recipe was in an agent worktree; redo it from NetHack's recipe).
   - Large: Dungeon Crawl Stone Soup (console build, Lua and sqlite bundled; check size),
     Cataclysm (very large; likely decline).
   - Rust/Go: chess-tui (needs an in-process engine; no exec), gittype (must work offline),
     rebels-in-the-sky (needs an offline mode), solar-system-explorer, terminal-space-program.
   - Python: **done in 1.1.0** (`native/recipes/python.py`). Ported: Pokete, Lightcycle,
     PyThrees, Penney's Game, Dango. Declined with reasons (round6 triage): no licence
     (terminal-frogger, oregon-trail, hammurabi-python), root input devices (just-asteroids),
     spawns Stockfish (chs). Left: anonymine (source on oskog97.com; check licence and fetch).
     To add one: pin it, add a `py_game(...)` to `PY_GAMES`, check its imports against
     `MODULES`/`STDLIB_SKIP`, patch out sockets/subprocess/exec of files, add a family entry.
   - Ruby/Racket/Java (floodit, wolfentext3d, dukedomrb, terminal-phase, letrain): decline unless a
     small interpreter runs them unchanged.
   - Closed or non-free (adom, alienrl, frozen-depths, stugan, dmagnetic data, gearhead/doomrl in
     Pascal): decline with reasons via `tools/ports/triage/*.json`.
   - Online: **done in 1.1.0** (`native/recipes/online.py`, `tools/ports/families/online.py`):
     SSHTron, SSH Hattrick, Late.sh, NetHack on alt.org (ssh) and Telehack (telnet). Declined:
     onx (no public server), ssh-games (its .gq domain is gone). roguelike-gallery: confirm its
     endpoint, then add it. More public servers (crawl.akrasiac.org, etc.) are one family entry
     each; never add one you haven't confirmed is up and free to play.
   - Built but broken: GNU Go (internal "stepped on a bug" crash on the first move) and GNU Chess
     (the engine never answers). Their sources are pinned (Ubuntu packages); debugging them is
     optional.
4. **Known weak spots**: Shell Games' Snake card shows its game-over screen (it dies before the
   screenshot tool can steer); Doom's data is 28 MB; Brogue needs 100×34 (small text); text sizes
   per game are in `docs/AUDIT.md`.
5. **Blocked on the owner**: visual-direction approval of the design (never assume it); deploying
   the community server, GitHub App and OAuth client (accounts, cost); publishing on Play, F-Droid
   or GitHub Releases; a catalog signing key and hosting for remote catalog sync.
