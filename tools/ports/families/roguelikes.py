"""Roguelikes and interactive fiction (native/recipes/roguelikes.py)."""

DEFAULTS = dict(
    recipe="native/recipes/roguelikes.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-11-02",
    discovery_notes="Ported to Tuikio; see the game manifest.",
)

GAMES = [
    dict(id="nethack", title="NetHack", exe="game_nethack", controls="dungeon8.v1",
         keys=["Wield=w", "Wear=W", "Take off=T", "Put on=P", "Remove=R", "Eat=e", "Quaff=q", "Read=r", "Zap=z",
               "Cast=Z", "Apply=a", "Fire=f", "Drop=d", "Kick=#kick\\r", "Pray=#pray\\r", "Help=?"],
         summary="The classic dungeon crawl: retrieve the Amulet of Yendor from the depths of Gehennom.",
         description="NetHack 3.6.7 with its original tty interface. Choose a role and race, then descend through "
                     "the Dungeons of Doom, the Gnomish Mines, Sokoban and beyond. The pad walks with the vi keys; "
                     "the strip holds the everyday commands, # starts any extended command from the keyboard, and "
                     "? lists everything. Leaving the game saves it.",
         category="roguelike", tags=["roguelike", "dungeon", "classic", "fantasy"],
         authors=["The NetHack DevTeam", "Stichting Mathematisch Centrum", "M. Stephenson"],
         license="NGPL", source_url="https://www.nethack.org/", version="3.6.7",
         archive="nethack_3.6.7.orig.tar.gz", discovery="nethack",
         discovery_url="https://github.com/NetHack/NetHack",
         saves=(["save", "record", "nethackrc"], "Saved game, top scores and your options file"),
         test_notes="Host test: name, role choice, first moves, kick, pray, save and restore, quit with tombstone "
                    "and score list; armeabi-v7a binary checked under qemu with its 32-bit data library."),
    dict(id="sporkhack", title="SporkHack", exe="game_sporkhack", controls="dungeon8.v1",
         keys=["Wield=w", "Wear=W", "Take off=T", "Put on=P", "Remove=R", "Eat=e", "Quaff=q", "Read=r", "Zap=z",
               "Cast=Z", "Apply=a", "Fire=f", "Drop=d", "Kick=#kick\\r", "Pray=#pray\\r", "Help=?"],
         summary="A tougher NetHack 3.4.3 variant: rebalanced monsters, new items and a meaner dungeon.",
         description="SporkHack, as played on the hardfought.org servers, with NetHack's tty interface. Pick a "
                     "class, race, gender and alignment on one screen, then '.' to play. The pad walks with the vi "
                     "keys; the strip holds the everyday commands. Leaving the game saves it.",
         category="roguelike", tags=["roguelike", "nethack", "variant", "fantasy"],
         authors=["Derek S. Ray", "The NetHack DevTeam"], license="NGPL",
         source_url="https://github.com/NHTangles/sporkhack", version="git 8d6bc8e9", archive="sporkhack-8d6bc8e9.tar",
         discovery="sporkhack",
         saves=(["save", "record", "sporkrc"], "Saved game, top scores and your options file"),
         host_tested="2026-11-05",
         test_notes="Host test in a PTY at 80x24: character screen, a Valkyrie's first room, walking."),
]
