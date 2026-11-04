"""Online games (native/recipes/online.py): played on someone else's server through the bundled SSH
client (Dropbear, libgame_ssh.so) or telnet client (libgame_telnet.so). Nothing of the game runs
on the phone and nothing is saved there. The app connects only after the player turns online
games on (docs/RUNTIME.md, "Online games")."""

DEFAULTS = dict(
    recipe="native/recipes/online.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-04",
    network="required",
    discovery_notes="Offered as an online game: Tuikio connects to the public server with its bundled client, "
                    "only once the player turns online games on.",
    test_notes="Not played from the build machine (it can't reach the server). The client was tested against a "
               "local server: connecting by the app-resolved address, terminal type and size, input and output.",
)

SSH = dict(exe="game_ssh", archive="dropbear-b1b4e349.tar", license_file="dropbear.txt")
TELNET = dict(exe="game_telnet", license_file="tuikio-GPL-3.0.txt")

GAMES = [
    dict(id="sshtron", title="SSHTron", online={"protocol": "ssh", "host": "sshtron.zachlatta.com"},
         controls="arrows4.v1", hide=["quit"], **SSH,
         summary="Multiplayer light cycles over SSH: steer your trail and make the others crash into it.",
         description="Everyone connected plays on the same arena. The pad steers. Leave from the pause menu.",
         category="arcade", tags=["tron", "multiplayer", "online"], authors=["Zach Latta", "Max Wofford"], license="MIT",
         source_url="https://github.com/zachlatta/sshtron", players="2+"),
    dict(id="ssh-hattrick", title="SSH Hattrick", online={"protocol": "ssh", "host": "frittura.org"},
         controls="arrows.v1", terminal=((160, 50), (160, 50)), **SSH,
         summary="Two-player arcade football over SSH, from the frittura.org game server.",
         description="Pick sshattrick in the server's menu (Select). The pad runs, Space shoots. The game needs a "
                     "160x50 screen, so the text is small: turn the phone sideways.",
         category="arcade", tags=["football", "multiplayer", "online"], authors=["ricott1"], license="GPL-3.0-only",
         source_url="https://github.com/ricott1/sshattrick", players="2"),
    dict(id="late-sh", title="Late.sh", online={"protocol": "ssh", "host": "late.sh"},
         controls="arrows.v1", input="typing", **SSH,
         summary="A cozy terminal clubhouse over SSH: chat, news and an arcade of small games.",
         description="Move between screens with the pad and Select; the keyboard is up for chatting. It includes "
                     "public chat with strangers: what you write there, everyone sees.",
         category="arcade", tags=["social", "chat", "arcade", "online"], authors=["Mateusz Piórowski"],
         license="FSL-1.1-MIT", source_url="https://github.com/mpiorowski/late-sh", players="many"),
    dict(id="nethack-alt-org", title="NetHack (alt.org server)", online={"protocol": "ssh", "host": "alt.org", "user": "nethack"},
         controls="roguelike.v1", input="typing", **SSH,
         summary="Play NetHack on nethack.alt.org, the public server: shared high scores and watching other games.",
         description="Register or log in in the server's menu, then play. Your game is saved on the server. "
                     "The same keys as Tuikio's own NetHack.",
         category="roguelike", tags=["nethack", "roguelike", "online"], authors=["NetHack DevTeam", "alt.org"],
         license="NGPL", source_url="https://alt.org/nethack/", discovery_url="https://alt.org/nethack/"),
    dict(id="telehack-z-code-games", title="Telehack", online={"protocol": "telnet", "host": "telehack.com"},
         controls="text.v1", input="typing", wrap="words", orientation="portrait", terminal=((48, 24), (80, 24)), **TELNET,
         summary="A recreation of the 1980s ARPANET and Usenet, with dozens of text games (Zork, adventure, and more).",
         description="Type commands and press Enter: `help` lists them, `zork` or `advent` starts a game, `games` "
                     "lists the rest. Other people are online too.",
         category="adventure", tags=["text adventure", "zork", "retro", "online"], authors=["Telehack"],
         license="LicenseRef-online-service", source_url="https://telehack.com/telehack.html",
         discovery_url="http://telehack.com/telehack.html"),
]
