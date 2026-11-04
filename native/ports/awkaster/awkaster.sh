# Tuikio launcher for awkaster, the awk raycaster (native/recipes/scripts.py writes the game's own
# awk program, with the changes listed there, between the AWKASTER lines below).
#
# Upstream, awkaster reads every key by running "stty raw; dd bs=1 count=1" through /bin/sh, and
# games get no shell. Instead this launcher puts the terminal in character mode once and passes
# each key to gawk as a line on its standard input. The program travels inside this script, which
# bash only runs when it matches its pinned SHA-256, so nothing gawk runs comes from the game's
# writable home.

stty -echo -icanon min 1 time 0
trap 'stty sane; printf "\e[0m"' EXIT
"$TUIKIO_LIB/libtuikio_gawk.so" -f /dev/fd/3 3<<'AWKASTER' < <(while IFS= read -rsn1 key; do printf '%s\n' "$key"; done)
@AWKASTER_AWK@
AWKASTER
