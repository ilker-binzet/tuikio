# Porting brief for Tuikio subagents

You are porting terminal games into **Tuikio**, an Android app that runs real terminal games
(ncurses and similar). The orchestrator, the main session, merges your work and does the
final full build, the Robolectric UI and screenshot audit, the card pictures, the licences,
README and docs. Your job is **correct, fully playable ports with honest records**, committed
on your own branch.

The owner's complaint that started all this: "the games are not fully ported: a game asks me
to press a key the app has no button for; detailed games look half-done, disproportionate,
shapeless." Every game you add must be **completely playable with the on-screen controls**,
**fit its screen**, and **start without errors**. A game that can't meet that is not
ported. Record why instead (see "Declining").

## The machine and the rules

- Repo: your git worktree (a checkout of branch `claude/new-session-h45p5a` at 069b247).
  Main checkout (read-only for you): `<main>` below (the orchestrator gives the path).
- Start by creating your branch: `git checkout -b port/<your-batch-name>`. Commit there only.
  **Never push**, never touch other branches, never open PRs.
- Commit messages end with these two lines:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_018DMD1fD5rYSjqxKQX3Nzd8
  ```
  Never put a model name or identifier anywhere in the repo.
- Shared machine: 4 cores and 15 GB RAM for 5 agents. Use `--jobs 1`. **Do not run**
  `./gradlew :app:test` or any Robolectric/screenshot test (the orchestrator does that once for
  everyone). Run Gradle only for the catalog validator and the runtime tests, with `--no-daemon`.
- Share the download cache: `rm -rf native/.cache && ln -s <main>/native/.cache native/.cache`.
  Copy the existing outputs so the runtime tests have every other game:
  `mkdir -p native/build && cp -r <main>/native/build/out native/build/out`.
  Seed the per-ABI curses sysroot to skip rebuilding ncurses:
  `for a in x86_64 arm64-v8a armeabi-v7a; do mkdir -p native/build/$a && cp -r <main>/native/build/$a/{bin,compat,sysroot} native/build/$a/; done`
  (if anything in there misbehaves, delete it and let `native/build.py` rebuild it).
- Network goes through a proxy. GitHub, crates.io, proxy.golang.org, pypi and the like work.
  `dl.google.com` and Google Maven are blocked by policy: don't route around it. Don't retry a
  proxy 403.
- **Security**:
  - Never run binaries you downloaded. Build everything from source; running the games you
    built is fine.
  - Never fetch anything at the game's run time: games are offline. A game that needs a
    server or the internet is declined, with the reason recorded.
  - Prevent path traversal and zip bombs in anything you add that unpacks data (`tk.unpack`
    already checks).
  - No secrets, keys or tokens anywhere.
- **Licences**: only redistributable free licences (OSI or FSF approved, or public domain /
  CC0 / Unlicense). No licence file means all rights reserved: decline, unless the README,
  source headers or a packaging file states a licence clearly; then cite where. Record the
  SPDX id and keep the upstream licence text (the recipe names it as the notice file).
- Data files must be free too (Freedoom yes, a commercial WAD no; free IF story files only if
  their licence says redistribution is allowed).

## How the runtime works (read docs/RUNTIME.md and docs/BUILD.md for detail)

- Each game is a **static-PIE musl ELF** cross-built with Zig for arm64-v8a, armeabi-v7a and
  x86_64, packaged as `lib<exe>.so` in the APK (W^X: Android only executes from the app's
  native library dir). `tk.check_static_pie` rejects anything else.
- The app runs it in a PTY with `TERM=xterm-256color`, `HOME` = the game's own writable
  directory (also the working directory), `TMPDIR=$HOME/.tmp`, `SHELL` and `PATH` set to
  `/nonexistent`, and `PAGER` set to the app's pager. **There is no shell**: `system()`,
  `popen()`, `/bin/sh` and `exec` of other programs fail on Android 8 and 9. Patch such calls
  out, or see how `native/recipes/bsdgames.py` and `native/ports/bsdgames/tuikio-pager.h`
  handle pagers.
- Data the game reads lives in its home. Recipes install data with `install_asset`, and the
  manifest's `data_files` copies it there on first launch. Paths like `/usr/share/...`,
  `/var/games/...` and `/tmp/...` must be redirected into the home with exact, checked
  substitutions (`replace_in` / the `subst=` lists in `native/recipes/github.py`) or patches in
  `native/ports/<game>/patches/`.
- Arrow keys arrive as `ESC O A..D` once a curses game enables keypad mode (the app honours
  DECCKM), otherwise `ESC [ A..D`. Enter is `\r`.

## Code map

- `native/tk.py`: the toolkit: sources, the `@game(...)` registry, Zig wrappers per ABI, `cc`,
  `autotools`, `cargo` (Rust), `unpack`, `install_asset`, `replace_in`, `check_static_pie`.
- `native/recipes/*.py`: one module per source family. `github.py` has C/C++ examples (plain
  file lists, autotools, custom builds); `rust.py` is the cargo example, including crate licence
  notices; `bsdgames.py` and `ubuntu.py` are bigger examples.
- `native/sources.lock.json`: every source pinned. For git: `python3 tools/ports/git_lock.py
  <name>-<commit8>.tar <url> <full 40-char commit>`. Tarballs: `url` plus `sha256`.
- `tools/ports/families/*.py`: catalog metadata per game (title, authors, licence, summary,
  description, category, tags, `controls` profile, `labels`, `hide`, `keys`, `input`,
  `terminal`, `orientation`, `args`, `env`, `saves`, `test_notes`...). Look at `github.py` and
  `rust.py`, and at how `tools/ports/manifests.py` turns them into `catalog/games/<id>.json`
  and links the discovery entry (`discovery=` names the existing `catalog/discovery.json`
  id when it differs from the game id).
- `catalog/profiles/*.v1.json`: on-screen control profiles (pads, buttons, what each sends).
  Reuse one where it fits exactly. Otherwise add `<name>.v1.json`. Schema:
  `catalog/schema/control-profile.schema.json`.
- `docs/CATALOG.md` documents every manifest field: `keys` (labelled buttons for keys the
  game uses that the profile lacks), `control_labels`/`control_hide`, `"input": "typing"`
  (keyboard up from the start, for games played by typing), `wrap`, terminal sizes.
- `native/tests/play.json`: a script per game (`expect:<text>`, `type:<text>` with `\n` for
  Enter, `key:<TermKey>`, `wait:<ms>`) that `core/runtime` PlayScriptsTest runs against the
  real x86_64 binary. Every game needs one that gets into actual play.
- `native/tests/shots.json`: optional deeper script (`text:`, `key:ENTER|ESCAPE|UP|DOWN|LEFT|RIGHT|SPACE`,
  `wait:`, `expect:`) the orchestrator's screenshot run uses for the audit and the card
  picture. Add one when the first screens are menus or prompts, so the shot shows play.
- `docs/AUDIT.md` is the quality bar: read the "What was wrong" tables and avoid every one of
  those problems.

## Workflow per game

1. **Assess**: language and build system, licence, size (keep a game under about 5 MB of
   binary per ABI and about 10 MB of data unless it is exceptional, and say so), runtime
   needs (network, X11/SDL, other programs, a shell), data files.
2. **Pin and port**: lock the source, write the recipe in **your own new modules**,
   `native/recipes/<batch>.py` and `tools/ports/families/<batch>.py`. Avoid editing shared
   recipe and family modules. Keep patches minimal and explain each in a comment.
3. **Build**: `python3 native/build.py --abi x86_64 --game <id> --jobs 1`, then all three
   ABIs (`--game <id>` without `--abi`). All three must build.
4. **Play-test in a PTY** with the orchestrator's tool, which behaves like the app's terminal:
   ```
   python3 docs/handoff/tools/explore.py \
       <game-id> <exe-name-without-lib-and-.so> <cols>x<rows> w1500 s tq w300 kUP w300 s ...
   ```
   Steps: `w<ms>` wait, `t<text>` type (`\n` = Enter), `k<UP|DOWN|LEFT|RIGHT|ENTER|ESC|SPACE|BS|TAB|F1|F12>`,
   `s` print the screen. Set `TUIKIO_OUT=$PWD/native/build/out` so it runs your build and
   copies your game's data (`assets/games/<id>`) into a temporary home, as the app does. Pass
   game arguments with `ARGS="..."`. Check that:
   - it starts with no error text and no file-not-found;
   - every key it uses in play works;
   - help, quit and game over all work;
   - it fits the terminal size you choose. Run it larger too, to see what the smaller size
     cuts off.
5. **Controls**: the pad, buttons and `keys` must cover every action the game takes in play.
   Name buttons for what they do in this game (`labels`) and hide the ones it ignores
   (`hide`). Typing games get `input="typing"`. Choose the orientation and terminal size that
   fill a phone screen legibly: about 40 to 48 columns upright, 80×24 sideways; bigger only
   if the game needs it.
6. **Catalog**: `python3 tools/ports/manifests.py <your-family>` writes the manifests and
   links the discovery entries. Then
   `./gradlew --no-daemon -q :tools:catalog-cli:run --args="validate $PWD/catalog"` must print ok.
7. **Scripts**: add your games to `native/tests/play.json`, and to `shots.json` where useful.
8. **Runtime tests**:
   `./gradlew --no-daemon :core:runtime:test -PrequireNative --tests '*PlayScriptsTest*'`
   must pass. It runs every game, so the copied outputs matter.
9. **Commit** the recipe module, family module, `native/ports/<game>/...` patches, profiles,
   `catalog/games/*.json`, `catalog/discovery.json`, `native/sources.lock.json` and the test
   scripts. Don't commit `LICENSES/`, `README.md` or `docs/AUDIT.md` (the orchestrator
   regenerates them), and don't commit `native/build` or caches.

## Declining

Some candidates won't be portable: closed source, no licence, an online service, Java/Ruby/
Racket with no reasonable runtime, needs X11/SDL with no terminal mode, far too big, or can't
be made playable on a phone. For each one, write an entry in
`tools/ports/triage/<batch>.json`:

```json
{ "<discovery id>": { "license": "<SPDX or UNKNOWN or Proprietary>",
                      "notes": "<one or two plain sentences: what it is and exactly why it isn't ported, or what would unblock it>" } }
```

Commit that file too; the orchestrator applies it to `catalog/discovery.json`. Be honest and
specific ("No licence anywhere in the repository or its packaging: all rights reserved"),
never vague. Don't decline a game just because it's hard. Do decline it when a port would
be broken or half-playable.

## Your report (your final message)

1. Your branch name and final commit SHA.
2. A table of games ported: id, title, licence, language, terminal size and orientation,
   controls (profile + keys), and anything notable you fixed or patched.
3. Games declined, with reasons. This mirrors your triage JSON.
4. Anything the orchestrator must know: new runtime needs, shared files you had to touch and
   why, known limitations, and the exact test commands you ran with their results.
