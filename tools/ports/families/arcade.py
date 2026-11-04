"""Action and arcade games from the "arcade" porting batch (native/recipes/arcade.py)."""

DEFAULTS = dict(
    recipe="native/recipes/arcade.py",
    terminal=((80, 24), (80, 24)),
    orientation="landscape",
    host_tested="2026-10-24",
    discovery_notes="Ported to Tuikio from the upstream source, pinned by commit or hash.",
)


def gh(repo, commit, name=None):
    """Upstream fields for a game pinned at <commit>; the archive is <name>-<commit>.tar (git_lock.py)."""
    name = name or repo.split("/")[1].lower()
    return dict(source_url=f"https://github.com/{repo}", version=f"git {commit}", archive=f"{name}-{commit}.tar")


def size(cols, rows):
    return dict(terminal=((cols, rows), (cols, rows)))


# Shell Games: 25 small ncurses games in one executable, started with the game's name.
SG = dict(exe="game_shellgame", license_file="shell-games.txt", authors=["Peu Borges"], license="MIT", **gh("MCookinho/shellgame", "dd1aa485"),
          discovery_notes="Ported to Tuikio as one game per title, all built into one executable (the collection's "
                          "menu starts the others with system(), which Android lacks). Licence: MIT, as declared by "
                          "the author's PKGBUILD; the repository has no licence file.")
AGAIN = "Again=<ENTER>"


def sg(gid, game, **kw):
    d = dict(SG, id=f"shellgame-{gid}", args=[game])
    d.update(kw)
    return d


GAMES = [
    sg("2048", "game2048", title="2048 (Shell Games)", controls="snake.v1", labels={"ok": "Again"},
       hide=["back", "pause"], orientation="portrait", **size(34, 20),
       summary="Slide and merge the tiles to reach 2048.",
       description="Slide every tile with the pad; two equal tiles merge into their sum. Reach 2048 before the board "
                   "fills up.",
       category="puzzle", tags=["2048", "numbers", "sliding", "shell games"],
       test_notes="Host test: board, slides in all four directions."),
    sg("asteroids", "asteroids", title="Asteroids (Shell Games)", controls="pad-fire.v1",
       labels={"up": "Thrust", "left": "Turn left", "right": "Turn right"}, hide=["ok"],
       summary="Turn, thrust and blast the asteroids before they hit your ship.",
       description="Left and right turn the ship, up thrusts and Fire shoots. Big asteroids split into smaller, faster "
                   "ones. Fast and unforgiving: the rocks wrap around the screen. Fire starts again after a crash.",
       category="arcade", tags=["shooter", "asteroids", "space", "shell games"],
       test_notes="Host test: field, turning, thrust and shots at 80x24 (it uses the whole terminal)."),
    sg("blackjack", "blackjack", title="Blackjack (Shell Games)", controls="blackjack.v1", orientation="portrait",
       **size(48, 20), summary="Beat the dealer at 21: hit, stand or double down.",
       description="Get closer to 21 than the dealer without going over. Hit takes a card, Stand lets the dealer play, "
                   "Double takes one last card. Deal starts the next round; wins, losses and pushes are counted.",
       category="cards", tags=["cards", "blackjack", "casino", "shell games"],
       test_notes="Host test: a hand dealt, hit and stand, next round."),
    sg("breakout", "breakout", title="Breakout (Shell Games)", controls="shooter.v1", labels={"fire": "Launch"},
       orientation="portrait", **size(42, 30), summary="Bounce the ball off your paddle and break every brick.",
       description="Slide the paddle with left and right to keep the ball in play. Launch serves the ball, and starts "
                   "a new game when it's over. Three lives, levels of bricks.",
       category="arcade", tags=["breakout", "paddle", "bricks", "shell games"],
       test_notes="Host test: bricks, paddle moves, ball in play."),
    sg("centipede", "centipede", title="Centipede (Shell Games)", controls="shooter.v1", keys=[AGAIN],
       orientation="portrait", **size(46, 24), summary="Shoot the centipede as it winds down through the mushrooms.",
       description="Slide your gun along the bottom and fire up at the centipede. Every segment you hit counts; "
                   "mushrooms take four shots. Clear three levels.",
       category="arcade", tags=["shooter", "centipede", "classic", "shell games"],
       test_notes="Host test: field, centipede, gun moves and fires."),
    sg("checkers", "checkers", title="Checkers (Shell Games)", controls="arrows.v1",
       labels={"select": "Select"}, hide=["space", "back"], players="2", **size(56, 18),
       summary="Draughts for two players on one phone, with forced captures.",
       description="Move the cursor with the pad and Select a piece, then Select where it goes. Captures are "
                   "compulsory and shown in red; reach the far side to crown a king. Players take turns.",
       category="strategy", tags=["checkers", "draughts", "board", "two players", "shell games"],
       test_notes="Host test: board and a first move. Fixed: the side panel ran off the screen."),
    sg("chess", "chess", title="Chess (Shell Games)", controls="arrows.v1", labels={"select": "Select"},
       hide=["space", "back"], keys=["Pieces=u"], players="2", **size(56, 23),
       summary="Chess for two players on one phone, with legal-move hints.",
       description="Move the cursor with the pad, Select a piece and its valid squares light up, then Select the "
                   "target. Check, checkmate and stalemate are detected. Pieces switches between symbols and letters.",
       category="strategy", tags=["chess", "board", "two players", "shell games"],
       test_notes="Host test: board, e2-e4. Fixed: the info panel ran off the screen."),
    sg("dig-dug", "digdug", title="Dig Dug (Shell Games)", controls="pad-fire.v1",
       labels={"fire": "Pump", "ok": "Again"}, orientation="portrait", **size(38, 23),
       summary="Dig tunnels and pump up the monsters until they pop.",
       description="Tunnel through the dirt with the pad and pump the monsters chasing you. Don't let them touch you.",
       category="arcade", tags=["dig dug", "maze", "classic", "shell games"],
       test_notes="Host test: field, digging, pump."),
    sg("donkey-kong", "donkeykong", title="Donkey Kong (Shell Games)", controls="pad-fire.v1",
       labels={"fire": "Jump", "ok": "Again"}, orientation="portrait", **size(41, 28),
       summary="Climb the ladders and jump the barrels to reach the top.",
       description="Run left and right, climb ladders with up and down, and jump over the barrels rolling down the "
                   "platforms. Reach the top to win.",
       category="arcade", tags=["platform", "donkey kong", "classic", "shell games"],
       test_notes="Host test: platforms, ladders, barrels, a jump."),
    sg("duck-hunt", "duckhunt", title="Duck Hunt (Shell Games)", controls="pad-fire.v1",
       labels={"fire": "Shoot", "ok": "Again"}, **size(52, 26),
       summary="Aim the crosshair and shoot the ducks: three shots a round.",
       description="Move the crosshair with the pad (hold to keep moving) and Shoot when a duck is under it. Every "
                   "round has more ducks and less time; miss one and the dog laughs.",
       category="arcade", tags=["shooting", "duck hunt", "classic", "shell games"],
       test_notes="Host test: round start, aiming and a shot. Played with the keyboard; no light gun or mouse."),
    sg("enduro", "enduro", title="Enduro (Shell Games)", controls="shooter.v1", hide=["fire"], keys=[AGAIN],
       orientation="portrait", **size(28, 27), summary="Weave through traffic for four days on the open road.",
       description="Steer left and right to pass the cars ahead without touching them. Survive four days to win.",
       category="arcade", tags=["racing", "enduro", "classic", "shell games"],
       test_notes="Host test: road, traffic, steering."),
    sg("frogger", "frogger", title="Frogger (Shell Games)", controls="snake.v1", labels={"ok": "Again"},
       hide=["back", "pause"], orientation="portrait", **size(35, 24),
       summary="Hop across the highway and the river to reach home.",
       description="Hop with the pad between the cars, then ride the logs across the water to the five homes at the "
                   "top.",
       category="arcade", tags=["frogger", "classic", "shell games"],
       test_notes="Host test: road, river, hops."),
    sg("galaga", "galaga", title="Galaga (Shell Games)", controls="shooter.v1", orientation="portrait",
       **size(52, 31), summary="Shoot down the alien formation before it dives at you.",
       description="Slide your ship left and right and fire at the formation. Aliens break off and dive; chain hits for "
                   "a combo. Ten stages. Fire starts a new game when it's over.",
       category="arcade", tags=["shooter", "galaga", "space", "shell games"],
       test_notes="Host test: formation, ship moves and fires."),
    sg("hangman", "hangman", title="Hangman (Shell Games)", controls="text.v1", input="typing",
       labels={"enter": "New word"}, hide=["erase"],
       summary="Guess the word one letter at a time before the man is hanged.",
       description="Type a letter to guess it. Six wrong guesses and the game is lost. Enter starts a new word.",
       category="words", tags=["hangman", "words", "letters", "shell games"],
       test_notes="Host test: gallows and word; letters guessed. Fixed: q quit at once, so words with a q (queen) "
                  "couldn't be finished; Esc quits now."),
    sg("minesweeper", "minesweeper", title="Minesweeper (Shell Games)", controls="mines.v1", hide=["new", "help"],
       keys=[AGAIN], **size(58, 26), summary="Clear a 9x9 minefield without stepping on a mine.",
       description="Move with the pad, Reveal a square or Flag it. Numbers count the mines around a square.",
       category="puzzle", tags=["minesweeper", "logic", "shell games"],
       test_notes="Host test: board, reveal, flag."),
    sg("pac-man", "pacman", title="Pac-Man (Shell Games)", controls="snake.v1", labels={"ok": "Again"},
       hide=["back", "pause"], **size(56, 28), summary="Eat all the dots and dodge the four ghosts.",
       description="Steer through the maze with the pad. Power pellets turn the ghosts blue for a while, and then you "
                   "can eat them.",
       category="arcade", tags=["maze", "pac-man", "classic", "shell games"],
       test_notes="Host test: maze, ghosts, Pac-Man moves and eats."),
    sg("pong", "pong", title="Pong (Shell Games)", controls="pong2.v1", players="1-2", **size(60, 28),
       summary="Table tennis against the computer or a friend: first to five wins.",
       description="Pick a mode with the arrows and OK. Player 1 is the left paddle (left buttons), player 2 or the "
                   "computer the right one (right buttons). Restart goes back to the mode menu.",
       category="arcade", tags=["pong", "two players", "classic", "shell games"],
       test_notes="Host test: mode menu, a game against the computer."),
    sg("q-bert", "qbert", title="Q*Bert (Shell Games)", controls="qbert.v1", **size(70, 17),
       summary="Hop down the pyramid and change every cube's colour.",
       description="The pad hops diagonally, the way the cubes are stacked. Land on every cube to change its colour, "
                   "and don't hop off the edge.",
       category="arcade", tags=["q*bert", "pyramid", "classic", "shell games"],
       test_notes="Host test: pyramid and hops."),
    sg("rhythm-spire", "rhythm", title="Rhythm Spire (Shell Games)", controls="rhythm4.v1", orientation="portrait",
       **size(44, 24), summary="Hit the notes in four lanes as they reach the line.",
       description="Notes fall down four lanes. Tap the lane's button (D, F, J or K) when a note crosses the target "
                   "line: perfect, good or miss. Pause stops the song.",
       category="arcade", tags=["rhythm", "music", "timing", "shell games"],
       test_notes="Host test: lanes, falling notes, hits. Fixed: the title was drawn over the score."),
    sg("snake", "snake", title="Snake (Shell Games)", controls="snake.v1", labels={"ok": "Again"},
       hide=["back", "pause"], orientation="portrait", **size(44, 27),
       summary="Eat and grow, and don't hit the walls or yourself.",
       description="Steer the snake with the pad. Every bite makes it longer and faster.",
       category="arcade", tags=["snake", "classic", "shell games"],
       test_notes="Host test: field, snake turns, food."),
    sg("solitaire", "paciencia", title="Solitaire (Shell Games)", controls="arrows.v1",
       labels={"select": "Pick/place", "space": "Draw", "back": "Cancel"}, **size(60, 22),
       summary="Klondike solitaire: build the four suits from ace to king.",
       description="Move the cursor with the pad. Pick/place takes a card or a run and puts it on the pile under the "
                   "cursor; Draw turns over the stock; Cancel drops the selection.",
       category="cards", tags=["solitaire", "klondike", "cards", "shell games"],
       test_notes="Host test: deal, draw, a move. Fixed: suits were drawn as escaped bytes, and the title over "
                  "the pile labels."),
    sg("spire-ascent", "spire", title="Spire Ascent (Shell Games)", controls="lr-select.v1",
       labels={"select": "Enter", "space": "End turn"}, keys=["#1-9"], **size(60, 30),
       summary="A deck-building climb: fight, rest, shop and beat the boss.",
       description="Choose your path up the map with left, right and Enter. In a fight, play cards with the number "
                   "buttons (each costs energy) and End turn when done. Win cards and relics on the way up.",
       category="roguelike", tags=["deck building", "cards", "roguelike", "shell games"],
       test_notes="Host test: map, first fight, cards played. Fixed: the map's key line was below the screen."),
    sg("super-auto-pets", "superautopets", title="Super Auto Pets (Shell Games)", controls="text.v1",
       labels={"enter": "Battle"}, hide=["space", "erase"], keys=["#a-f", "Sell=s", "#1-5"], **size(63, 23),
       summary="Buy pets, build a team and watch it battle.",
       description="Buy pets and food from the shop with a to f, sell a pet with Sell and its number, and Battle when "
                   "your team is ready. Ten lives; each win brings more gold.",
       category="strategy", tags=["auto battler", "pets", "shop", "shell games"],
       test_notes="Host test: shop, buying, a battle."),
    sg("tetris", "tetris", title="Tetris (Shell Games)", controls="blocks.v1", labels={"ok": "Again"},
       hide=["back", "pause"], orientation="portrait", **size(39, 26),
       summary="Stack the falling blocks and clear lines.",
       description="Slide with left and right, rotate with up, soft drop with down and hard drop with Drop.",
       category="arcade", tags=["blocks", "tetris", "shell games"],
       test_notes="Host test: well, pieces fall, moves and drops."),
    sg("the-typer", "typer", title="The Typer (Shell Games)", controls="text.v1", input="typing", hide=["erase"],
       labels={"enter": "Again"}, orientation="portrait", **size(44, 28),
       summary="Type the words on the zombies before they reach you.",
       description="Each zombie carries a word; type it to stop it. Ten waves, three lives.",
       category="words", tags=["typing", "zombies", "words", "shell games"],
       test_notes="Host test: zombies with words, typing kills them."),
    dict(id="doom-ascii", title="Doom (ASCII)", exe="game_doom_ascii", controls="doom.v1",
         keys=["#1-7", "Run=]", "Map=<TAB>"], **size(80, 30),
         summary="Doom, drawn in coloured text, with the free Freedoom levels.",
         description="The full Doom engine (doomgeneric) renders every frame as coloured characters. It plays "
                     "Freedoom: Phase 1, a free, complete replacement for the original episodes. Fire shoots, Use opens "
                     "doors, 1-7 pick weapons, Map toggles the automap.",
         category="arcade", tags=["fps", "doom", "shooter", "freedoom"],
         authors=["Wojciech Graj", "ozkl (doomgeneric)", "id Software", "the Freedoom project"],
         license="GPL-2.0-only AND BSD-3-Clause", **gh("wojciech-graj/doom-ascii", "940528f1"),
         saves=([f"savegame/doomsav{i}.dsg" for i in range(6)], "Saved games (six slots)"),
         test_notes="Host test: title, new game, first level rendered, moves and fires."),
]
