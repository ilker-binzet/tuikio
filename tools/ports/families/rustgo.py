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
