"""Online games: games played on someone else's server over SSH or telnet (docs/RUNTIME.md,
"Online games"). Nothing of the game runs on the phone; Tuikio bundles two clients:

- libgame_ssh.so: Dropbear's dbclient, with port forwarding, agent forwarding, proxy commands,
  netcat mode and X11 compiled out, so a session can only be a terminal on the one server;
- libgame_telnet.so: a small telnet client (native/ports/online/tuikio_telnet.c).

The app starts them only for manifests with network "required" and an "online" endpoint, only
after the player has turned online games on, with arguments built from that endpoint alone. A
static musl program can't use Android's DNS resolver, so the app resolves the host itself (and
refuses private addresses) and passes the address in TUIKIO_ADDR; the clients connect there and
keep using the host name (Dropbear checks the server's key against it).
"""
import os
import threading

import tk
from tk import BuildError, game, replace_in, run, unpack

DROPBEAR = "dropbear-b1b4e349.tar"
PORTS = os.path.join(tk.HERE, "ports", "online")

# Client features a game session doesn't need: none of them may be reachable.
DROPBEAR_OPTIONS = """\
#define DROPBEAR_CLI_LOCALTCPFWD 0
#define DROPBEAR_CLI_REMOTETCPFWD 0
#define DROPBEAR_CLI_AGENTFWD 0
#define DROPBEAR_CLI_PROXYCMD 0
#define DROPBEAR_CLI_NETCAT 0
#define DROPBEAR_X11FWD 0
#define DROPBEAR_SVR_LOCALTCPFWD 0
#define DROPBEAR_SVR_REMOTETCPFWD 0
#define DROPBEAR_SVR_LOCALSTREAMFWD 0
#define DROPBEAR_SVR_REMOTESTREAMFWD 0
#define DROPBEAR_SVR_AGENTFWD 0
#define DROPBEAR_USER_ALGO_LIST 0
#define DO_MOTD 0
"""

_locks = {name: threading.Lock() for name in tk.ABIS}
_built = {}


def build_ssh(abi):
    work = abi.work("tuikio-ssh")
    out = os.path.join(work, "dbclient")
    key = DROPBEAR + DROPBEAR_OPTIONS + "v2"
    stamp = out + ".key"
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
        return out
    src = unpack(DROPBEAR, os.path.join(work, "src"))
    with open(os.path.join(src, "localoptions.h"), "w") as fh:
        fh.write(DROPBEAR_OPTIONS)
    # Connect to the address the app resolved (TUIKIO_ADDR), keeping the host name for the
    # known-hosts check and the prompts.
    replace_in(os.path.join(src, "src", "cli-main.c"),
               "\t\tprogress = connect_remote(cli_opts.remotehost, cli_opts.remoteport,",
               "\t\tconst char *tuikio_addr = getenv(\"TUIKIO_ADDR\");\n"
               "\t\tprogress = connect_remote(tuikio_addr && *tuikio_addr ? tuikio_addr : cli_opts.remotehost, cli_opts.remoteport,")
    # Messages start with "ssh:", not with the executable's long path in the app's library directory.
    replace_in(os.path.join(src, "src", "cli-runopts.c"), "\tcli_opts.progname = argv[0];", '\tcli_opts.progname = "ssh";')
    env = abi.env(CPPFLAGS="", LIBS="")
    run(f"./configure --host={abi.triple} --build=x86_64-pc-linux-gnu --disable-zlib --disable-syslog "
        "--disable-lastlog --disable-utmp --disable-utmpx --disable-wtmp --disable-wtmpx --disable-pututline "
        "--disable-pututxline --disable-pam --enable-static --disable-harden", src, env)
    run("make -j4 PROGRAMS=dbclient", src, env)
    built = os.path.join(src, "dbclient")
    if not os.path.exists(built):
        raise BuildError("dropbear: dbclient was not built")
    os.replace(built, out)
    with open(stamp, "w") as fh:
        fh.write(key)
    return out


def build_telnet(abi):
    out = os.path.join(abi.work("tuikio-telnet"), "game_telnet")
    tk.cc(abi, [os.path.join(PORTS, "tuikio_telnet.c")], out, "-Wall -Wextra -Werror")
    return out


def client(abi, protocol):
    with _locks[abi.name]:
        k = (abi.name, protocol)
        if k not in _built:
            _built[k] = build_ssh(abi) if protocol == "ssh" else build_telnet(abi)
        return _built[k]


# Game id -> protocol. The endpoints themselves are in tools/ports/families/online.py.
ONLINE_GAMES = {
    "sshtron": "ssh",
    "ssh-hattrick": "ssh",
    "late-sh": "ssh",
    "nethack-alt-org": "ssh",
    "telehack-z-code-games": "telnet",
}

for _g, _p in ONLINE_GAMES.items():
    if _p == "ssh":
        game(_g, curses=False, notice=(DROPBEAR, "LICENSE"), license_name="dropbear")(
            lambda abi: {"game_ssh": client(abi, "ssh")})
    else:
        game(_g, curses=False)(lambda abi: {"game_telnet": client(abi, "telnet")})
