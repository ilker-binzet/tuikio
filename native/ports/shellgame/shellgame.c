/* Tuikio: one executable for the 25 Shell Games (github.com/MCookinho/shellgame).
 *
 * Upstream builds every game as its own program and starts them from menu.c with system(),
 * which Android can't do (no shell, no exec of other programs). Here each game's main() is
 * compiled as sg_<name>_main (native/recipes/arcade.py) and the catalog starts the game named by
 * the first argument, so each title is its own game in the app with its own controls. Every
 * game keeps all its state in file-local statics, so they share one binary without clashes.
 *
 * The locale is set here for every game: only some of them call setlocale(), and the others
 * (Solitaire's suits, Spire Ascent's energy symbol, Super Auto Pets' dash) drew their UTF-8 text
 * as escaped bytes without it. */
#include <locale.h>
#include <ncurses.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

/* getch() for the games (sg_input.h): an empty poll repeated within 5 ms naps 15 ms. */
int sg_getch(void)
{
    static struct timespec last;
    int ch = wgetch(stdscr);
    if (ch == ERR) {
        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        long gap = (now.tv_sec - last.tv_sec) * 1000L + (now.tv_nsec - last.tv_nsec) / 1000000L;
        if (gap < 5) {
            napms(15);
            clock_gettime(CLOCK_MONOTONIC, &now);
        }
        last = now;
    }
    return ch;
}

#define GAMES(X) X(asteroids) X(blackjack) X(breakout) X(centipede) X(checkers) X(chess) X(digdug) \
    X(donkeykong) X(duckhunt) X(enduro) X(frogger) X(galaga) X(game2048) X(hangman) X(minesweeper) \
    X(paciencia) X(pacman) X(pong) X(qbert) X(rhythm) X(snake) X(spire) X(superautopets) X(tetris) X(typer)

#define DECLARE(name) int sg_##name##_main(void);
GAMES(DECLARE)

static const struct {
    const char *name;
    int (*run)(void);
} games[] = {
#define ENTRY(name) {#name, sg_##name##_main},
    GAMES(ENTRY)
};

int main(int argc, char **argv)
{
    setlocale(LC_ALL, "");
    if (argc > 1)
        for (size_t i = 0; i < sizeof games / sizeof games[0]; i++)
            if (strcmp(argv[1], games[i].name) == 0)
                return games[i].run();
    fputs("usage: shellgame <game>\ngames:", stderr);
    for (size_t i = 0; i < sizeof games / sizeof games[0]; i++)
        fprintf(stderr, " %s", games[i].name);
    fputc('\n', stderr);
    return 2;
}
