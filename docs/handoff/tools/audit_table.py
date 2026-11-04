"""Per-game table for docs/AUDIT.md from the RenderShotsTest output (-Pshots=primary)."""
import glob
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SHOTS = os.path.join(ROOT, "app", "build", "shots")
NOTES = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}  # docs/handoff/tools/audit_notes.json

rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "catalog/games/*.json"))):
    g = json.load(open(f))
    gid = g["id"]
    o = g["runtime"]["orientation"]
    tags = {"landscape": ["land"], "portrait": ["port"], "any": ["port", "land"]}[o]
    cells, chips = [], []
    for t in tags:
        p = os.path.join(SHOTS, f"{gid}-{t}.json")
        if os.path.exists(p):
            m = json.load(open(p))
            cells.append(f"{m['cell'][1] / m['density']:.0f}")
            chips += [c for c in m["chips"] if c not in chips]
    term = "×".join(map(str, g["runtime"]["terminal"]["preferred"]))
    rows.append(f"| {g['title']} | {o} | {term} | {g['controls'].removesuffix('.v1')} | {' / '.join(cells) or '-'} | "
                f"{', '.join(chips) or '-'} | {NOTES.get(gid, '')} |")
print("| Game | Orientation | Terminal | Controls | Text (dp) | Chips on the audited screen | Fixed in this audit |")
print("|---|---|---|---|---|---|---|")
print("\n".join(rows))
