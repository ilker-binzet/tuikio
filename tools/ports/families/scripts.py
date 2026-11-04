"""Games written in interpreted languages (native/recipes/scripts.py): bash games run by the shared
GNU Bash in libgame_bash.so, with BASH_ENV naming the prelude that maps the commands they call to
the helpers in the native library directory (docs/RUNTIME.md, "Script games")."""

DEFAULTS = dict(
    recipe="native/recipes/scripts.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-02",
    discovery_notes="Ported to Tuikio from the upstream repository, pinned by commit; runs on the bundled GNU Bash "
                    "(libgame_bash.so), which only runs the game's pinned scripts.",
)

BASH_ENV = {"BASH_ENV": "tuikio-bash.sh"}


def gh(repo, commit, name=None):
    """Upstream fields for a game pinned at <commit>; the archive is <name>-<commit>.tar (git_lock.py)."""
    name = name or repo.split("/")[1].lower()
    return dict(source_url=f"https://github.com/{repo}", version=f"git {commit}", archive=f"{name}-{commit}.tar")


GAMES = [
    dict(id="piu-piu-sh", title="piu-piu", exe="game_bash", args=["piu-piu"], env=BASH_ENV, controls="piu-piu.v1",
         summary="A side-scrolling space shooter written in pure bash: shoot down the alien drones, then their mothership.",
         description="Fly with the pad and shoot with Fire. Crates dropped by aliens give lives, ammo or a bigger gun. "
                     "In the menu the pad moves up and down, left and right change your ship's look, and Fire picks.",
         category="arcade", tags=["shooter", "space", "bash"], authors=["Ivan Marov (vaniacer)"], license="MIT",
         **gh("vaniacer/piu-piu-SH", "c7da41c0", "piu-piu-sh"),
         test_notes="Host test in a PTY at 80x24: intro, menu without multiplayer, play with WASD and P, lives and ammo "
                    "counting down. Multiplayer (netcat) removed: games are offline."),
    dict(id="shellshock", title="ShellShock", exe="game_bash", args=["shellshock"], env=BASH_ENV, controls="shellshock.v1",
         summary="A top-down space shooter in bash: blast the falling rocks before they hit your ship.",
         description="Fire starts the game and shoots; the pad flies the ship. Auto toggles autofire, Pause pauses, "
                     "and Quit goes back to the title screen. Your best score is kept.",
         category="arcade", tags=["shooter", "space", "bash"], authors=["Øyvind 'bolt' Hvidsten"], license="GPL-2.0-only",
         source_url="https://github.com/PacAnimal/shellshock", version="git 6b072c66",
         archive="shellshock-6b072c66.tar", saves=([".shellshock"], "Best score"),
         discovery_notes="Ported to Tuikio from the author's GitHub repository (PacAnimal/shellshock, the same script "
                         "as dhampir.no/stuff/bash/shellshock), pinned by commit; runs on the bundled GNU Bash.",
         test_notes="Host test in a PTY at 80x24: title, start, flying, firing, rocks and score; the high score file "
                    "is read as a number only."),
    dict(id="awkaster", title="awkaster", exe="game_bash", args=["awkaster.sh"], env=BASH_ENV, controls="awkaster.v1",
         keys=["#1-4"],
         summary="A first-person raycaster shooter, written in awk.",
         description="Walk the maze, shoot the monsters and find the lift: the pad walks and steps sideways, the "
                     "turn buttons turn, Lift calls the elevator (it takes a while to arrive). 1-4 change the colours.",
         category="arcade", tags=["raycaster", "fps", "awk"], authors=["Fedor Kalugin"], license="MIT",
         **gh("TheMozg/awk-raycaster", "ac7f1b03", "awkaster"), discovery="awkaster",
         test_notes="Host test in a PTY at 80x24: the 3D view, walking, turning and shooting."),
]
