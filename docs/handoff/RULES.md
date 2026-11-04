# Rules and standing decisions

These came from the owner, or were decided with the owner, during development. Treat them as
requirements, not suggestions.

## Working with the owner

- The owner is **Ömer SÜSİN** (GitHub `omersusin`). They usually write in **Turkish**, sometimes
  English: answer in the language they write in, plainly, with results first.
- They care about **quality as a player sees it**. The trigger for the big audits was: *"the games
  aren't fully ported: a game asks me to press a button the app doesn't have… detailed games look
  half-done, disproportionate, shapeless. If you can't fix it I'll delete the project."* Every
  game must be **fully playable with on-screen controls**, **fit the phone screen legibly**, and
  **start without errors**. Otherwise don't ship it; decline it with a reason.
- They asked to **save tokens / be efficient**: batch work, don't re-read what you know, don't
  narrate. And at one point: **"Don't use agents anymore"**. Parallel subagents burned the usage
  limit and stalled. Use subagents only if the owner asks.
- Report honestly: say what passed, what failed, and what wasn't tested. Never claim a device test
  that didn't happen.

## Hard rules (security, legal, honesty)

1. **Secrets**: keystores, passwords, tokens and private keys never go in Git, app sources, logs,
   CI or chat text. The release key travels to the owner as files, deliberately, never pasted. No
   OAuth client secret or GitHub App private key in the APK; no universal GitHub write token.
   `tools/release/check_apk.py` scans for leaks.
2. **No publishing, spending money, creating paid accounts or uploading keys without the owner's
   explicit approval.** That covers the Play Store, F-Droid, GitHub Releases pages, server
   deployment and app signing services.
3. **Visual-direction approval stays BLOCKED on the owner.** Never invent or assume their
   approval of the design.
4. **No dark patterns** (no fake urgency, no hidden opt-outs, no nagging).
5. **Never execute arbitrary downloaded binaries.** Build everything from pinned source. Official
   toolchains (Zig from PyPI, rustup, Go) are fine. Running the games you built is fine.
6. **Games are offline.** No network at runtime (`"network": "none"`). Online games need an opt-in,
   clearly labelled network mode that the owner hasn't decided on.
7. **Prevent SSRF, path traversal and zip bombs** wherever data is fetched or unpacked
   (`tk.unpack` checks archives; the community server has SSRF tests; save import has traversal and
   zip-bomb tests).
8. **Network policy**: `dl.google.com` and Google Maven were blocked where this was built. Don't
   route around a policy block, and don't retry proxy 403s. (That's why there is no AGP/R8:
   `build-logic` + ProGuard instead.) ftp.gnu.org returned 403 too, so Ubuntu's signed source
   packages are used instead (`tools/ports/ubuntu_sources.py`).
9. **Licences**: only redistributable free licences (OSI/FSF, or public domain/CC0/Unlicense). No
   licence file means all rights reserved: decline. Every bundled binary ships its licence text and
   exact source reference (`LICENSES/`, generated). Data files (WADs, levels, story files) must be
   free too. Credit the owner and contributors in the app's About screen and the README
   (`gen_credits.py`).
10. **Honest catalog**: statuses are `CANDIDATE` → `PORTABLE` (host-tested) → `ANDROID_TESTED` (real
    device, with evidence) → `STORE_READY`. The validator rejects `ANDROID_TESTED`/`STORE_READY`
    without evidence. The app labels everything "Preview port" until device-tested.
11. **Games get no shell**: `SHELL` and `PATH` are `/nonexistent`. Android 8 and 9 have no
    `/bin/sh`, and games must not run arbitrary commands. Pagers run directly (`tuikio_pager`). The
    bundled bash runs only the pinned scripts it was built for (their SHA-256 values are compiled
    in), with only the helper commands they need.
12. **W^X**: executables live only in the APK's native library directory (`lib<exe>.so`), static PIE,
    no program interpreter. Data goes in the game's home (its working directory, `HOME`).

## Git and process

- Develop on branch `claude/new-session-h45p5a` (or whatever branch the owner names). Push with
  `git push -u origin <branch>`. **Don't open a PR unless asked.**
- Commit messages: plain, descriptive. When an AI authors them, end with that tool's attribution
  trailer; earlier commits use `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and a
  `Claude-Session:` line. **No model identifiers in code, docs or comments.**
- Before every push: catalog validation, credits check, the relevant tests. CI runs everything;
  a red CI is your job to fix (find the root cause, never skip or disable tests).
- `signing.properties` goes into the repo root only for the release build, then is deleted.

## Product decisions already made

- **Original design**, no Material/AndroidX. Mascot Kio. Brand packs (6 + an accessibility pack
  "Phosphor"), launcher identity switching via activity-aliases.
- **Adaptive controls**: each game has a control profile (pads, buttons), per-game `keys`
  (labelled buttons for keys its profile lacks), `control_labels`/`control_hide` (buttons named
  for what they do in that game, unused ones hidden), answer chips for questions (`PromptChips`)
  and key chips for keys the screen names (`KeyHints`). Typing games start with the keyboard up
  (`"input": "typing"`). Chips sit in a strip under the game; they never cover it.
- **Fit**: per-game terminal size and orientation; text sizes measured in `docs/AUDIT.md`. Upright
  games use about 40–48 columns, sideways 80×24, bigger only when the game needs it.
- **Card pictures** come from each game's real screen (`capture_art.py`); Lantern Tide keeps its
  drawn one.
- **Sounds**: the terminal bell becomes a short synthesized blip (`GameBell`), silent when the
  phone is silenced, with a switch under You › Game sounds.
- **Per-ABI APKs** in addition to the universal one; the app checks the checksums of the ABI that
  was actually installed.
