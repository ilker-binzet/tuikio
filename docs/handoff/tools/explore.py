"""Scratch explorer: run a built game in a pty (like the app does) and print its screen.

usage: explore.py <gid> <exe> <cols>x<rows> [step ...]
steps: w<ms> (wait), t<text> (type; \\n = Enter), k<UP|DOWN|LEFT|RIGHT|ENTER|ESC|SPACE>, s (print screen)
"""
import os, pty, select, shutil, signal, sys, tempfile, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pylib"))  # or: pip install pyte
import pyte

ROOT = os.environ.get("TUIKIO_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "native", "build", "out"))
KEYS = {"UP": "\x1b[A", "DOWN": "\x1b[B", "RIGHT": "\x1b[C", "LEFT": "\x1b[D", "ENTER": "\r", "ESC": "\x1b", "SPACE": " ",
        "BS": "\x7f", "TAB": "\t", "F12": "\x1b[24~", "F1": "\x1bOP"}

gid, exe, size = sys.argv[1:4]
cols, rows = map(int, size.split("x"))
steps = sys.argv[4:]
home = tempfile.mkdtemp(prefix=f"x-{gid}-")
assets = os.path.join(ROOT, "assets", "games", gid)
if os.path.isdir(assets):
    shutil.copytree(assets, home, dirs_exist_ok=True)
os.makedirs(os.path.join(home, ".tmp"), exist_ok=True)
env = {"HOME": home, "PWD": home, "TMPDIR": home + "/.tmp", "TERM": "xterm-256color", "USER": "kio", "LOGNAME": "kio",
       "LANG": "C.UTF-8", "PATH": "/nonexistent", "COLUMNS": str(cols), "LINES": str(rows), "SHELL": "/nonexistent",
       "PAGER": os.path.join(ROOT, "x86_64", "libtuikio_pager.so")}
if os.environ.get("TUIKIO_ADDR"):  # online games: the address the app would resolve
    env["TUIKIO_ADDR"] = os.environ["TUIKIO_ADDR"]
args = os.environ.get("ARGS", "").split()
pid, fd = pty.fork()
if pid == 0:
    import fcntl, struct, termios
    fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    os.chdir(home)
    path = os.environ.get("EXE_PATH") or os.path.join(ROOT, "x86_64", f"lib{exe}.so")
    os.execve(path, [path] + args, env)
import fcntl, struct, termios
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
class RepScreen(pyte.Screen):
    """pyte lacks REP (CSI n b), which ncurses uses with xterm-256color."""
    last = " "

    def draw(self, data):
        if data:
            self.last = data[-1]
        super().draw(data)

    def repeat(self, n=1, *a, **k):
        super().draw(self.last * max(1, n))


pyte.ByteStream.csi = dict(pyte.ByteStream.csi, b="repeat")
screen = RepScreen(cols, rows)
stream = pyte.ByteStream(screen)


def pump(ms):
    end = time.time() + ms / 1000
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], max(0, end - time.time()))
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return False
            if not data:
                return False
            stream.feed(data)
    return True


def show(tag=""):
    print(f"----- {tag} cursor=({screen.cursor.y},{screen.cursor.x})")
    lines = [l.rstrip() for l in screen.display]
    while lines and not lines[-1]:
        lines.pop()
    for l in lines:
        print("|" + l)


alive = pump(900)
for s in steps:
    if s == "s":
        show()
    elif s[0] == "w":
        alive = pump(int(s[1:]))
    elif s[0] == "t":
        os.write(fd, s[1:].replace("\\n", "\r").encode())
        alive = pump(150)
    elif s[0] == "k":
        key = KEYS[s[1:]]
        # Like the app's terminal: arrows in application cursor mode (DECCKM, which ncurses sets
        # with keypad()) are ESC O x; sending ESC [ x then reads as a bare Escape in many games.
        if s[1:] in ("UP", "DOWN", "LEFT", "RIGHT") and (1 << 5) in screen.mode:
            key = "\x1bO" + key[-1]
        os.write(fd, key.encode())
        alive = pump(150)
    if not alive:
        break
pump(300)
show("end")
try:
    wpid, status = os.waitpid(pid, os.WNOHANG)
    if wpid:
        print("EXITED", status)
    else:
        os.kill(pid, signal.SIGKILL)
except ChildProcessError:
    print("EXITED")
