# Lessons learned (read before changing subtle things)

## Testing traps

- **Gradle reuses stale test results** when a test reads files Gradle doesn't know are inputs. That
  hid a CI failure: `ControlLayoutTest` reads `catalog/profiles`. Now declared as inputs: the
  controls tests, and the runtime tests (`native/tests` and `catalog/games`). If a test "passes"
  suspiciously, rerun it with `--rerun-tasks`.
- **Play scripts must tolerate timing.**
  - Animated title screens (Brogue) drop keys sent too early.
  - Real-time games (Shell Games' Snake) can end before the first check.
  - Wait before keys, and expect text that appears on every outcome.
- **Test the app's arrow keys, not raw `ESC [ A`.** curses games in keypad mode receive
  `ESC O A`. A bare `ESC [` reads as Escape, which quits many games. The early play-tester sent the
  wrong form and made Pipes, Muncher and others "quit". The app was right all along.
- `RenderShotsTest` waits ~1.6 s before running a script; games that die in that time can't be
  steered for the screenshot.

## Android and runtime traps

- **APK packaging drops hidden files** (names starting with a dot) from assets. Doom's
  `.default.cfg` would never have reached a phone, and its keys would have been wrong. The
  validator now rejects hidden asset paths. Hidden save paths are rejected too; patch the game
  (Angband's `~/.angband` became `~/angband`).
- **Spaces in data file names** are rejected by the validator. Rename them and patch the code
  (nPush).
- **There is no `/bin/sh` on Android 8/9**, and games get `SHELL=/nonexistent`. Pagers,
  `system()` and `popen()` must be patched.
- **On the host, `getpwuid` finds `/root`**; on a phone the compat shim returns the game's home.
  Host tests may write to `/root/...`; clean up.
- **A per-ABI APK installs one ABI even when the phone supports several.** Choose checksums by the
  installed files, not by `Build.SUPPORTED_ABIS[0]`.
- ncurses here is built with an **opaque `WINDOW`**: code poking `win->_cury` needs `wmove` (Rogue).
- C++ from the 2000s: `register` is an error in C++17 (`-Wno-register`). Old K&R C needs `LEGACY`
  flags and `-fcommon`.
- Some autotools builds race under `make -j` (GNU Chess `src`): build them sequentially.
- **Games sharing one executable** (the bash interpreter) used to install it concurrently through
  the same temp name. Installs now use unique temp names.

## Process traps

- **Parallel subagents** on a 4-core, 15 GB machine contend for CPU and RAM and burn the usage
  limit fast. They stalled twice and the owner banned them. Work sequentially, in batches.
- **Merging parallel branches**: `native/sources.lock.json`, `native/tests/play.json`,
  `native/tests/shots.json` and `catalog/discovery.json` conflict textually. Merge them as data
  (`docs/handoff/tools/merge_json.py`), then regenerate discovery with
  `tools/ports/manifests.py`.
- **Commit only after the checks you'd run before pushing.** A commit once went in with stale
  README credits because a `;` let it through. Chain checks with `&&`.
- **Generated files**: `catalog/games/*.json` (from families), `LICENSES/*` (from the native
  build), README credits (`gen_credits.py`), card `art` (`capture_art.py`). Edit the source, then
  regenerate.
- Proxy-restricted environments: ftp.gnu.org gave 403; zig's package fetcher fails. Use Ubuntu
  source packages and local pinned paths. Never retry a 403 or route around a policy block.

## Design and quality judgments

- Card crops: tall regions get tiny on a card (about 3 columns per row is the right shape). Prose
  games honestly show prose.
- Truecolour screens (Brogue) can exceed the 62-colour card palette; extra colours fall back to the
  default ink.
- Text adventures are better upright at 48 columns with word wrap. Boards that need 80 columns go
  landscape. Brogue needs 100×34, Balatro 112×40.
- When a game needs a key it never names on screen, add it as a labelled `keys` button; don't rely
  on the keyboard.
