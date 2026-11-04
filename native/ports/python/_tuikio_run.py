"""Starts a Python game: `game_python <game id> [arguments]` (native/recipes/python.py).

The table below is filled in at build time: game id -> "module:function" (call it) or "module"
(run it as __main__). Games run with their home as working directory and HOME.
"""
import os
import runpy
import sys

GAMES = {}  # @GAMES@


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in GAMES:
        sys.stderr.write("usage: game_python <game> [arguments]\n")
        return 64
    gid, entry = sys.argv[1], GAMES[sys.argv[1]]
    sys.argv = [gid] + sys.argv[2:]
    home = os.environ.get("HOME")
    if home and os.path.isdir(home):
        os.chdir(home)
    module, _, func = entry.partition(":")
    if func:
        mod = __import__(module, fromlist=[func])
        result = getattr(mod, func)()
        return result if isinstance(result, int) else 0
    runpy.run_module(module, run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
