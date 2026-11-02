"""Terminal games written in Rust and Go, pinned by commit (tools/ports/git_lock.py).

Rust games build like native/recipes/rust.py: cargo --locked against the tree's Cargo.lock, or
native/ports/<game>/Cargo.lock where the tree has none or a patch changes its dependencies.

Go games build with go_build(): the installed Go toolchain (GOTOOLCHAIN=local, Go 1.24.7 or newer
1.24.x), modules from the Go module proxy checked against the tree's go.sum (-mod=readonly), with
cgo and external linking through the ABI's zig cc, which makes the same static PIEs as every other
game (Go's own linker can only make PIEs that need a dynamic loader).

Patches in native/ports/<game>/patches/ are applied to both kinds; each one says why at its top.
"""
import os
import re
import shutil
import subprocess
import threading

import tk
from tk import CACHE, HERE, BuildError, cargo, game, install_asset, run, unpack
from recipes.rust import LICENSE_FILE, crate_notices

_notice_lock = threading.Lock()


# ---------------------------------------------------------------- Rust

def rust(lock, exe, binary, *, notice="LICENSE", args="", data=()):
    return dict(lock=lock, exe=exe, binary=binary, notice=notice, args=args, data=data)


RUST = {
    # The court follows the terminal (patch); upstream wanted at least 130x28.
    "terminal-pong": rust("terminal-pong-aff432ef.tar", "game_terminal_pong", "terminal-pong"),
    # Its sound needs ALSA (kira -> cpal), which Android doesn't have: built without it (patch).
    "unipac": rust("unipac-dc0f6d0b.tar", "game_unipac", "rspacman"),
}


def build_rust(abi, gid):
    e = RUST[gid]
    src = unpack(e["lock"], os.path.join(abi.work(gid), "src"))
    tk.apply_patches(src, gid)
    lock = os.path.join(HERE, "ports", gid, "Cargo.lock")
    if os.path.exists(lock):
        shutil.copyfile(lock, os.path.join(src, "Cargo.lock"))
    for rel in e["data"]:
        install_asset(f"games/{gid}/{rel}", os.path.join(src, rel))
    exe = cargo(abi, src, e["binary"], e["args"])
    with _notice_lock:
        if gid not in tk.EXTRA_NOTICES:
            tk.EXTRA_NOTICES[gid] = crate_notices(abi, src)
    return {e["exe"]: exe}


# ---------------------------------------------------------------- Go

GO_ARCH = {"arm64-v8a": ("arm64", {}), "armeabi-v7a": ("arm", {"GOARM": "7"}), "x86_64": ("amd64", {})}
GO_CACHE = os.path.join(CACHE, "go")
GO_MIN = (1, 24, 7)


def go_tool():
    go = os.environ.get("GO") or shutil.which("go") or "/usr/local/go/bin/go"
    if not os.path.exists(go) and not shutil.which(go):
        raise BuildError("go not found: install Go 1.24.7 or newer (see docs/BUILD.md), or set GO")
    out = subprocess.run([go, "env", "GOVERSION"], capture_output=True, text=True,
                         env=dict(os.environ, GOTOOLCHAIN="local")).stdout.strip()
    m = re.match(r"go(\d+)\.(\d+)(?:\.(\d+))?", out)
    if not m or tuple(int(x or 0) for x in m.groups()) < GO_MIN:
        raise BuildError(f"{go} is {out or 'unknown'}; the Go games need go{'.'.join(map(str, GO_MIN))} or newer")
    return go


def go_env(abi):
    arch, extra = GO_ARCH[abi.name]
    env = dict(os.environ)
    for k in [k for k in env if k.startswith("GO") or k.startswith("CGO_")]:
        del env[k]  # nothing from the host's Go setup leaks into the build
    env.update(extra)
    env.update({
        "GOOS": "linux", "GOARCH": arch, "GOTOOLCHAIN": "local", "GOENV": "off", "GOWORK": "off",
        "GOFLAGS": "-mod=readonly -trimpath -buildvcs=false",
        "GOPATH": os.path.join(GO_CACHE, "path"), "GOMODCACHE": os.path.join(GO_CACHE, "mod"),
        "GOCACHE": os.path.join(GO_CACHE, "build"),
        "GOPROXY": "https://proxy.golang.org", "GOSUMDB": "sum.golang.org",
        "CGO_ENABLED": "1", "CC": abi.cc, "CXX": abi.cxx,
        "CGO_CFLAGS": tk.CFLAGS, "CGO_LDFLAGS": "",
    })
    return env


def go_build(abi, src, pkg, out):
    """Cross-builds the Go package <pkg> (relative to the module root <src>) as a static PIE for the
    ABI, at <out>. cgo is on so that the external linker, the ABI's zig cc, links it: musl's
    self-relocating start files, the Android compatibility shim, and no program interpreter."""
    go = go_tool()
    env = go_env(abi)
    ldflags = f"-s -w -linkmode=external -extld={abi.cc} '-extldflags={abi.ldflags}'"
    run(f'{go} build -buildmode=pie -ldflags="{ldflags}" -o {out} {pkg}', src, env)
    tk.check_static_pie(out, abi)
    return out


def go_notices(abi, src, pkg):
    """The license texts of every module linked into the program (MIT and BSD ask for them to
    travel with binaries); the Go standard library's is LICENSES/go-std.txt."""
    go = go_tool()
    listing = subprocess.run(
        [go, "list", "-deps", "-f", "{{with .Module}}{{if not .Main}}{{.Path}}\t{{.Version}}\t{{.Dir}}{{end}}{{end}}", pkg],
        cwd=src, env=go_env(abi), check=True, capture_output=True, text=True).stdout
    mods = sorted({tuple(line.split("\t")) for line in listing.splitlines() if line.strip()})
    seen = {}
    out = ["", "", "=" * 72, "Go modules linked into this game", "=" * 72]
    for path, version, mdir in mods:
        out += ["", f"{path} {version}"]
        found = False
        for f in sorted(os.listdir(mdir)):
            if not LICENSE_FILE.match(f) or not os.path.isfile(os.path.join(mdir, f)):
                continue
            found = True
            text = open(os.path.join(mdir, f), encoding="utf-8", errors="replace").read().strip()
            key = text
            if key in seen:
                out.append(f"  {f}: same text as {seen[key]}")
            else:
                seen[key] = f"{path} {f}"
                out += [f"--- {f}", text]
        if not found:
            raise BuildError(f"{path} {version}: no license file in the module")
    write_go_std_notice(go)
    out += ["", "The Go standard library and runtime linked into it are listed in go-std.txt."]
    return "\n".join(out) + "\n"


def write_go_std_notice(go):
    goroot = subprocess.run([go, "env", "GOROOT"], capture_output=True, text=True, check=True,
                            env=dict(os.environ, GOTOOLCHAIN="local")).stdout.strip()
    version = subprocess.run([go, "env", "GOVERSION"], capture_output=True, text=True, check=True,
                             env=dict(os.environ, GOTOOLCHAIN="local")).stdout.strip()
    body = f"Go standard library and runtime ({version})\n\n" + open(os.path.join(goroot, "LICENSE"), encoding="utf-8").read()
    patents = os.path.join(goroot, "PATENTS")
    if os.path.exists(patents):
        body += "\n\n--- PATENTS\n" + open(patents, encoding="utf-8").read()
    path = os.path.join(tk.LICENSES, "go-std.txt")
    os.makedirs(tk.LICENSES, exist_ok=True)
    if not os.path.exists(path) or open(path, encoding="utf-8").read() != body:
        with open(path + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(path + ".tmp", path)


def golang(lock, exe, *, pkg=".", notice="LICENSE", data=()):
    return dict(lock=lock, exe=exe, pkg=pkg, notice=notice, data=data)


GO = {
    "wordle-cli": golang("wordle-cli-90f3c622.tar", "game_wordle_cli"),
}


def build_go(abi, gid):
    e = GO[gid]
    src = unpack(e["lock"], os.path.join(abi.work(gid), "src"))
    tk.apply_patches(src, gid)
    extra = os.path.join(HERE, "ports", gid, "files")
    if os.path.isdir(extra):  # whole new files a patch refers to (data the game embeds)
        shutil.copytree(extra, src, dirs_exist_ok=True)
    for rel in e["data"]:
        install_asset(f"games/{gid}/{rel}", os.path.join(src, rel))
    out = go_build(abi, src, e["pkg"], os.path.join(abi.work(gid), e["exe"]))
    with _notice_lock:
        if gid not in tk.EXTRA_NOTICES:
            tk.EXTRA_NOTICES[gid] = go_notices(abi, src, e["pkg"])
    return {e["exe"]: out}


for _g, _e in RUST.items():
    game(_g, curses=False, notice=(_e["lock"], _e["notice"]))(lambda abi, _g=_g: build_rust(abi, _g))
for _g, _e in GO.items():
    game(_g, curses=False, notice=(_e["lock"], _e["notice"]))(lambda abi, _g=_g: build_go(abi, _g))
