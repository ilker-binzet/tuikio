/* Tuikio: included before every Shell Games source (native/recipes/arcade.py).
 *
 * Several games poll the keyboard with nodelay() in loops that don't always sleep: the shop in
 * Super Auto Pets, the map in Spire Ascent and the game-over screens of Blackjack, Chess,
 * Checkers and Rhythm Spire spin at 100% CPU, which drains a phone's battery while the screen
 * just waits for a key. getch() goes through sg_getch() (shellgame.c), which naps 15 ms when it
 * is polled again within 5 ms of an empty poll. Real-time games sleep 16 ms or more between
 * polls, so their speed doesn't change. */
#ifndef TUIKIO_SG_INPUT_H
#define TUIKIO_SG_INPUT_H
#include <ncurses.h>

int sg_getch(void);
#undef getch
#define getch() sg_getch()

#endif
