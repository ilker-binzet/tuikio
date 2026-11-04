# Playbook: how to do the recurring jobs

`PORTING-BRIEF.md` has the full rules for porting one game. This file is the quick, ordered
version of every job.

## Port a game

1. **Assess**:
   - licence (free and redistributable, else decline);
   - language and build system;
   - size (aim for under ~5 MB binary per ABI and under ~10 MB data);
   - runtime needs: network (decline), X11/SDL-only (decline), exec of other programs or a shell
     (patch it out), data files.
2. **Pin** the source:
   - git: `python3 tools/ports/git_lock.py <name>-<commit8>.tar <url> <full commit>`;
   - Ubuntu package: `python3 tools/ports/ubuntu_sources.py --lock <package>`;
   - tarball: add `{"url", "sha256"}` to `native/sources.lock.json` and put the file in
     `native/.cache/dl/`.
3. **Recipe**:
   - Add `@game("<id>", notice=(<lock name>, <licence path in archive>))` in a module under
     `native/recipes/`. `more.py` is a good template: `cc(...)` file lists, `autotools(...)`,
     `unpack`, `replace_in` for exact checked patches, `install_asset` for data.
   - Redirect `/usr/share`, `/var` and `/tmp` paths into the home.
   - Never leave `system()` or `popen()` in place.
   - Hidden file names (leading dot) and spaces can't be asset or save paths: rename them, and
     patch the code to match.
4. **Build**: `python3 native/build.py --abi x86_64 --game <id>`, then without `--abi` for all
   three ABIs.
5. **Play-test** in a PTY:
   - Run `TUIKIO_OUT=$PWD/native/build/out python3 docs/handoff/tools/explore.py <id> <exe> <cols>x<rows> w1500 s ...`.
     It needs pyte: `pip install pyte`.
   - Steps: `w<ms>`, `t<text>` (`\n` = Enter), `k<UP|DOWN|LEFT|RIGHT|ENTER|ESC|SPACE|TAB|BS>`,
     `s` (print the screen).
   - It sends application-mode arrows like the app. It does **not** pass the manifest `env` (for
     bash games, test through `PlayScriptsTest`).
   - Check: starts clean; every key used in play works; help, quit and game over work; it fits;
     try it larger to see what gets cut.
6. **Controls**:
   - Choose a profile in `catalog/profiles/` or add one (copy `doom.v1.json` or
     `awkaster.v1.json`).
   - In the family entry set `keys=[...]` (compact notation: `"Bomb=b"`, `"#1-9"`, `"Next=<TAB>"`,
     `"a1=a1\r"`), `labels={...}`, `hide=[...]`, and `input="typing"` for typing games.
   - Run `./gradlew :core:controls:test`: the layout test fails if buttons don't fit small phones.
7. **Catalog**:
   - Add a `dict(...)` to a family in `tools/ports/families/*.py`.
   - Fields: id, title, exe, controls, terminal, orientation, summary, description, category
     (`arcade|puzzle|strategy|cards|words|roguelike|adventure|simulation`), tags, authors,
     license, source, `discovery=`, saves, test_notes.
   - Then run `python3 tools/ports/manifests.py <family>`.
8. **Scripts**:
   - `native/tests/play.json`: `expect:`, `type:`, `key:`, `wait:`. It must get into play, and be
     tolerant of timing. Animated title screens drop early keys, so wait first.
   - `native/tests/shots.json`: deeper scripts for screenshots and card art.
9. **Check**:
   - `./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"`;
   - `python3 tools/catalog/gen_credits.py` (then `--check`);
   - `./gradlew :core:runtime:test -PrequireNative --tests '*PlayScriptsTest*'`.
10. **Card art**:
    - `./gradlew :app:test --tests '*RenderShotsTest.portrait' --tests '*RenderShotsTest.landscape' -Pshots=<ids>`;
    - `python3 tools/catalog/capture_art.py`;
    - review: `./gradlew :app:test --tests '*RenderShotsTest.cards' -Pshots=all`, then open
      `app/build/shots/cards-*.png`;
    - fix bad crops with `PIN`/`SQUASH` in `capture_art.py`. Cards fit about three columns per
      row.
11. **Audit doc**:
    - `python3 docs/handoff/tools/audit_table.py docs/handoff/tools/audit_notes.json` prints the
      per-game table for `docs/AUDIT.md`; add a note per new game to `audit_notes.json`;
    - add a round section with what was fixed.
12. **Commit and push**, then watch CI.

## Decline a candidate

Add it to `tools/ports/triage/<name>.json`:

```json
{"<discovery id>": {"license": "<SPDX or UNKNOWN>", "notes": "<specific reason>"}}
```

Then run `python3 docs/handoff/tools/apply_triage.py <date>`. That updates
`catalog/discovery.json` and keeps the status `CANDIDATE`, with `last_checked` set and the notes
explaining why.

## Interpreters (bash, awk; Python if ever)

See `native/recipes/scripts.py` and `docs/RUNTIME.md`:
- GNU Bash built from source runs only the game scripts whose SHA-256 is compiled in;
- `BASH_ENV` points at a prelude (`native/ports/bash/tuikio-bash.sh`) that maps the few commands
  scripts call (stty, sleep, tput) to helper binaries (`libtuikio_toybox.so`,
  `libtuikio_tput.so`);
- `/dev/tcp` is compiled out;
- awkaster uses GNU Awk as an extra runtime output.

A Python runtime would follow the same pattern: static CPython, curses linked against our
ncurses, stdlib zipped as data, scripts pinned.

## Other toolchains

- **Go games**: `go_build()` in `native/recipes/rustgo.py` (cgo on, external link with the ABI's
  zig cc, static PIE).
- **Rust games**: `tk.cargo` with a `--locked` `Cargo.lock`, and crate licence notices via
  `crate_notices`.
- **Zig games**: pin the Zig release they target. Give dependencies as local pinned paths, since
  zig's own fetcher fails through proxies. Set `exe.pie = true`.
- **Builds that run their own generated tools** (GNU Go's pattern compiler, for example): run them
  through qemu-user when cross-compiling. See the removed gnu-go recipe in git history (commit
  "Six more games…").

## Release

1. Bump `versionCode` and `versionName` in `app/build.gradle.kts`.
2. Run the full tests:
   - `./gradlew :core:terminal:test :core:controls:test :core:catalog:test :core:community:test :backend:test`;
   - `./gradlew :core:runtime:test -PrequireNative`;
   - `./gradlew :app:test`;
   - validate the catalog;
   - check the credits.
3. Commit and push; wait for green CI.
4. Copy `signing.properties` (from the owner's key folder) into the repo root, run
   `./gradlew :app:assembleReleaseApk :app:assembleReleaseSplitApks`, then **delete
   `signing.properties`**.
5. Run `python3 tools/release/check_apk.py <each apk>`. All checks must pass, and the signer
   certificate SHA-256 must be `d8ea95d3…0874`.
6. Name the outputs `tuikio-<version>[-<abi>].apk` and write `SHA256SUMS.txt`.
7. Tag `v<version>` and push the tag. Publishing a GitHub Release, the Play Store or F-Droid
   needs the owner's approval.

## CI

`.github/workflows/ci.yml`. The native job installs Zig 0.17.0 (pip), Rust 1.97.0 with the musl
targets, Zig 0.15.1, Go 1.24.7 and qemu. It caches `native/.cache` keyed on `sources.lock.json`.
Read failing jobs' logs and fix the root cause. Common traps are in `LESSONS.md`.
