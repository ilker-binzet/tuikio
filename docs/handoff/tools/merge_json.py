"""Merge the shared JSON files of the porting branches into the working tree as data, not text.

usage: merge_json.py <branch> [<branch> ...]
  native/sources.lock.json   files: union (a name pinned differently on two sides is an error)
  native/tests/play.json     games: union (same id with different scripts is an error)
  native/tests/shots.json    games: union
Run it after `git merge` stopped on conflicts in these files (or before, on a clean tree):
it rewrites them from HEAD plus every branch's version.
"""
import os
import json
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def show(ref, path):
    try:
        return json.loads(subprocess.check_output(["git", "-C", ROOT, "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL))
    except subprocess.CalledProcessError:
        return None


def merge(path, key, refs):
    base = show("HEAD", path)
    out = dict(base[key])
    for ref in refs:
        other = show(ref, path)
        if other is None:
            continue
        for k, v in other[key].items():
            if k in out and out[k] != v:
                base_v = base[key].get(k)
                if out[k] == base_v:
                    out[k] = v  # changed only on the branch
                elif v == base_v:
                    pass  # changed only on our side
                else:
                    sys.exit(f"{path}: {k} differs between HEAD and {ref}")
            else:
                out[k] = v
    base[key] = out  # keep insertion order: existing entries first, new ones appended
    with open(f"{ROOT}/{path}", "w") as fh:
        json.dump(base, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"{path}: {len(out)} {key}")


refs = sys.argv[1:]
merge("native/sources.lock.json", "files", refs)
merge("native/tests/play.json", "games", refs)
merge("native/tests/shots.json", "games", refs)
