"""GNU Shogi, from Ubuntu's signed source package (tools/ports/ubuntu_sources.py): a curses board,
moves typed like "7g7f". GNU Go and GNU Chess were tried and declined (catalog/discovery.json)."""
import os

from tk import autotools, game, unpack


@game("gnu-shogi", notice=("gnushogi_1.5~git20140725.orig.tar.gz", "COPYING"))
def build_gnushogi(abi):
    src = unpack("gnushogi_1.5~git20140725.orig.tar.gz", os.path.join(abi.work("gnu-shogi"), "src"))
    autotools(abi, src, "--with-curses --without-x", make="make -j4 -C gnushogi")
    return {"game_gnushogi": os.path.join(src, "gnushogi", "gnushogi")}
