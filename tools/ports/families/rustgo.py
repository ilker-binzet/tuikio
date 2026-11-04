"""Terminal games written in Rust and Go, pinned by commit (native/recipes/rustgo.py)."""

DEFAULTS = dict(
    recipe="native/recipes/rustgo.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-10-24",
    discovery_notes="Ported to Tuikio from the upstream repository, pinned by commit; built for Android's musl "
                    "targets.",
)


def gh(repo, commit, name=None):
    """Upstream fields for a game pinned at <commit>; the archive is <name>-<commit>.tar (git_lock.py)."""
    name = name or repo.split("/")[1].lower()
    return dict(source_url=f"https://github.com/{repo}", version=f"git {commit}", archive=f"{name}-{commit}.tar")


GO_NOTES = ("Ported to Tuikio from the upstream repository, pinned by commit; built with Go (modules pinned by go.sum) "
            "for Android's musl targets.")

GAMES = [
    # Local play only (no SSH server) and its score history in a JSON file instead of SQLite (patch):
    # 4 MB instead of 8 MB per binary. Its layout is already upright: 58x30.
    dict(id="clidle", title="Clidle", exe="game_clidle", controls="clidle.v1", input="typing",
         orientation="portrait", terminal=((58, 30), (58, 30)),
         saves=([".local/share/clidle"], "Every game and guess, for the running total score."),
         summary="Wordle with a running score: guess the five-letter word in six tries.",
         description="Type a word and press Enter. Green letters are in the right place, yellow ones are in the "
                     "word but elsewhere, grey ones aren't in it; the keyboard below keeps track. A win scores "
                     "100 for one guess down to 50 for six, added to your total. New word starts another game.",
         category="words", tags=["wordle", "words", "puzzle"], authors=["Ajeet D'Souza"], license="MIT",
         **gh("ajeetdsouza/clidle", "fb05b782"), discovery_notes=GO_NOTES,
         test_notes="Host test: six guesses to the end of a game at 58x30, its saved history, and a new game."),
    # Upstream wanted a 130x28 terminal; the court now follows the terminal (patch): 80x24 sideways.
    dict(id="terminal-pong", title="Terminal Pong", exe="game_terminal_pong", controls="pong.v1",
         keys=["P2 up=w", "P2 down=s", "P2 power= ", "Theme=d"],
         summary="Pong against the computer or a friend, with power shots, themes and a screensaver mode.",
         description="Hold up or down to move your paddle on the left and keep the ball in play; Power smashes "
                     "it back when it is close (ten per game). Play with Friend gives the right paddle to a second "
                     "player (P2 buttons). Pause sets the difficulty and the colour theme.",
         category="arcade", tags=["pong", "paddle", "two-player"], authors=["IshmamR"], license="MIT",
         players="1-2", **gh("IshmamR/terminal.pong", "aff432ef", "terminal-pong"),
         test_notes="Host test: menu, name prompt, a rally against the computer and the pause options at 80x24."),
    # Its info panel starts at column 32 and the Ms. Pac-Man mazes are 31 rows (plus lives and the
    # marquee): 64x33, upright, with the pad under it. Built without sound (Android has no ALSA).
    dict(id="unipac", title="UniPac", exe="game_unipac", controls="unipac.v1", orientation="portrait",
         terminal=((64, 33), (64, 33)),
         summary="Pac-Man in the terminal, with emoji ghosts, fruit and the Ms. Pac-Man mazes.",
         description="Steer Pac-Man through the maze, eat every dot and grab a power pill to turn the tables on the "
                     "ghosts. Each level brings a new maze. Pause stops the game; after a game, Again starts another.",
         category="arcade", tags=["pacman", "maze", "action"], authors=["Jesper Olsen"], license="MIT",
         **gh("jesper-olsen/UniPac", "dc0f6d0b"),
         test_notes="Host test: first maze at 64x33, steering, pause, quit to GAME OVER and the Y/N prompt."),
    # Random mode: a new word whenever you like (the daily modes allow one game a day). Upright, with the
    # board above its letter keyboard (patch); side by side it needed 84 columns.
    dict(id="wordle-cli", title="Wordle CLI", exe="game_wordle_cli", controls="wordle.v1", input="typing",
         orientation="portrait", terminal=((52, 37), (52, 37)), args=["random"],
         summary="Wordle: guess the five-letter word in six tries, with coloured hints after each guess.",
         description="Type a word and press Enter. Green letters are in the right place, yellow ones are in the "
                     "word but elsewhere, grey ones aren't in it; the keyboard under the board keeps track. New "
                     "word starts another game once one is over.",
         category="words", tags=["wordle", "words", "puzzle"], authors=["Nimble Bun Works"], license="MIT",
         **gh("nimblebun/wordle-cli", "90f3c622"), discovery_notes=GO_NOTES,
         test_notes="Host test: six guesses to the end of a game at 52x37, and a new word after it."),
]
