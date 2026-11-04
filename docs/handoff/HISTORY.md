# History: the conversation, condensed

The project was built in one long Claude Code session (cloud container) with the owner, Ömer SÜSİN,
from 2026-10-22 to 2026-11-04. These are the owner's requests in order, with what was done. Exact
commit messages (`git log`) hold more detail.

## 1. The original brief (2026-10-22)

Build, optimize, test and sign **Tuikio**: an Android app for terminal/TUI games. Requirements:
- a W^X-compliant native runtime (games as static executables in the native library dir, run in a PTY);
- adaptive on-screen controls;
- an **original design language** with a mascot, **Kio**, and brand packs with a Brand Studio;
- community features (suggest games, credit contributors, publish) with a backend;
- an **honest catalog** (no false "tested" claims);
- release shrinking (R8, replaced by ProGuard because Google Maven was blocked) and signing;
- a final status report;
- licences for every ported game in the repo, credits in the README, and the owner and
  contributors credited in the app's About screen.

The design canvas and a clickable prototype were published for owner review. Visual-direction
approval was never given and stays blocked.

## 2. 0.1.0 – 0.1.1: first device run

The owner installed 0.1.0 on a POCO F5 (Android 17). The app launched, browsing and installing
worked, and opening a game crashed (`GameActivity` used the insets controller before
`setContentView`). Fixed in 0.1.1, along with quit/rotation crashes and an audit of Android-only
paths.

## 3. Rendering and controls

The owner asked to optimize how games look and to make the buttons adaptive ("the pause button's
text is supposed to turn to Play").

Done:
- centering;
- render artifacts fixed;
- controls no longer overlap the game;
- per-game terminal sizes;
- zoom that follows the content;
- a readable ink for low-contrast colours;
- adaptive buttons;
- typing mode with extra keys;
- word wrap for prose games.

## 4. Porting at scale

Games came from:
- bsd-games and the New BSD Games;
- Ubuntu packages (pinned via the signed index);
- GitHub C/C++ projects;
- the original **Kio: Lantern Tide**.

A candidate inventory went into `catalog/discovery.json`, imported from awesome-ttygames and
similar lists.

## 5. Audit round 1 (0.1.4)

The owner (in Turkish): *"The app is good, but the games aren't fully ported… a game asks me to
press a button the app doesn't have… detailed games look half-done, disproportionate, shapeless. If
you can't fix it I'll delete the project. Examine all the games, fix all the problems, and do an
audit."* They also asked: *"add the remaining games later and check them too."*

Every game was started on the real game screen in its orientation and checked for keys with no
button and for broken or tiny layouts.

Added:
- key chips (`KeyHints`) and answer chips;
- typing mode;
- the chip strip;
- zoom fixes.

Several games were fixed. See `docs/AUDIT.md`, round 1.

## 6. Audit round 2 (0.1.5)

This round played into each game (scripts in `native/tests/shots.json`), read each game's key
handling in its source, ran each game at a larger size to see what was cut off, and scanned the
binaries for phone-hostile paths.

Added:
- per-game `keys`, `control_labels`/`control_hide` and `"input": "typing"`;
- the Bombardier profile;
- pagers that run without a shell;
- Moria on roguelike keys;
- netToe colour fixes;
- `check_apk` rejecting stray binaries.

## 7. Card pictures, sounds, Rust games (0.1.6)

The owner showed a screenshot: one card (Lantern Tide) had a picture and the rest showed `>_`.
They asked: *"Will you apply the games' sounds if they have them, and their pictures like this?"*

Done:
- **Card art** from each game's real screen: a cell dump in RenderShotsTest, then
  `capture_art.py`, stored as manifest `art`, drawn by `MiniScreen`.
- Deeper screenshot scripts so the pictures show play.
- Hand-pinned crops for awkward screens.
- **GameBell**: the terminal bell (BEL) becomes a short tone, with a "Game sounds" switch.
- Nine Rust games built with cargo through Zig.

## 8. "Add the remaining games" (0.2.0)

The owner asked to add the games not ported yet, *"use subagents for being efficient"*.

Five subagents were started, one per batch: roguelikes, arcade, boards, Rust/Go and scripts.
They worked in git worktrees from a shared brief (`PORTING-BRIEF.md`). They repeatedly hit the
usage limit and stalled.

Meanwhile:
- **per-ABI APKs** were added;
- the app was fixed to check checksums for the ABI actually installed.

The owner then said ***"Don't use agents anymore"***. The agents were stopped and their committed
work merged: 25 Shell Games, puzzle and solitaire games, NetHack, a bash runtime with two bash
games, Wordle CLI, UniPac and Terminal Pong.

Then Doom (ASCII) with Freedoom was finished, and version 0.2.0 shipped with 148 games. A CI
failure (Blackjack buttons too wide in landscape, hidden locally by a stale Gradle cache) was found
and fixed.

## 9. "Do the 35, be efficient" (round 5)

The owner asked to port the roughly 35 remaining compiled-language candidates without burning
tokens.

**Ported:**
- nchess and clidle (finished from agent work);
- GNU Shogi;
- Brogue CE;
- VIper;
- Open Adventure;
- Zigtris (Zig 0.15.1);
- awkaster (GNU Awk);
- Angband;
- Rogue;
- nPush.

**Declined, with recorded reasons:**
- no licence: connect4, Rummy, cemetery-escape, bashmaze;
- non-free ROM: brickgame-4bit;
- X11 input: ASCII Patrol;
- played in your own shell: bash-dungeon;
- heavy dependencies: katamascii, dopewars, shell-tanks, zoridor;
- built but broken: GNU Go and GNU Chess.

## 10. "Make release 1.0.0. I'm out." (2026-11-04)

The owner asked for release 1.0.0 and a handoff folder with everything (chat, how it's built,
rules, perspectives), so another Claude Code session or another AI can continue.

That is this folder. Version 1.0.0 (code 9), 159 games, signed APKs (universal and per-ABI), and
a `v1.0.0` tag. The signing key was handed to the owner separately.

## 11. "Do it: Python, and the online games need an internet mode." (2026-11-04)

The owner approved both open decisions from the handoff. Done in 1.1.0:
- **Python runtime**: static CPython 3.13.16 (from the GitHub tag; python.org was blocked) with
  the stdlib and games zipped onto the executable, isolated, no sockets/subprocess/ctypes.
  Pokete (0.9.2: the dev branch needs protobuf codegen), Lightcycle, PyThrees, Penney's Game,
  Dango. Five candidates declined.
- **Online games**: manifest `online` endpoint + `network: required`; bundled Dropbear and a
  small telnet client; an **Online games** switch (off by default) and a consent sheet; DNS done
  by the app with private addresses refused. SSHTron, SSH Hattrick, Late.sh, NetHack (alt.org),
  Telehack. Not tested against the real servers (no egress from the build machine).

## Recurring themes from the owner

- Wants **everything fully working**, not partial. Gets frustrated by half-done ports.
- Prefers results over explanations; short status updates in Turkish.
- Is budget-conscious about tokens and usage limits.
- Has accidentally pasted unrelated content (WhatsApp diagnostics) once. When they say "ignore
  that", ignore it.
