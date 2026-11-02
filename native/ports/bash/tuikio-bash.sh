# Tuikio prelude for bash games. Bash reads it before the game's script ($BASH_ENV in the game's
# manifest); see docs/RUNTIME.md, "Script games".
#
# A game gets no PATH and no shell, and Android lets the app execute files only from its native
# library directory. Bash lives there ($BASH is its absolute path), and so do two helpers built
# for script games: libtuikio_toybox.so (toybox's stty, sleep, date, uname, cat, rm and mktemp)
# and libtuikio_tput.so (ncurses' tput, with the app's terminal descriptions compiled in). The
# commands below are shell functions that run those helpers by absolute path. Nothing else can be
# started, and nothing is put on PATH.

readonly TUIKIO_LIB="${BASH%/*}"

_tuikio_box() { (exec -a "$1" "$TUIKIO_LIB/libtuikio_toybox.so" "${@:2}"); }

stty() { _tuikio_box stty "$@"; }
sleep() { _tuikio_box sleep "$@"; }
date() { _tuikio_box date "$@"; }
uname() { _tuikio_box uname "$@"; }
cat() { _tuikio_box cat "$@"; }
rm() { _tuikio_box rm "$@"; }
mktemp() { _tuikio_box mktemp "$@"; }
tput() { "$TUIKIO_LIB/libtuikio_tput.so" "$@"; }
clear() { "$TUIKIO_LIB/libtuikio_tput.so" clear; }
