"""Apply tools/ports/triage/*.json (declined candidates) to catalog/discovery.json: upstream_license,
notes and last_checked for each listed discovery id. Ids that a game manifest now links are skipped."""
import os
import glob
import json
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
path = f"{ROOT}/catalog/discovery.json"
entries = json.load(open(path))
by_id = {e["id"]: e for e in entries}
done, missing = 0, []
for f in sorted(glob.glob(f"{ROOT}/tools/ports/triage/*.json")):
    for did, t in json.load(open(f)).items():
        e = by_id.get(did)
        if e is None:
            missing.append(did)
            continue
        if e.get("game_id"):
            continue
        e["upstream_license"] = t.get("license", e["upstream_license"])
        e["notes"] = t["notes"]
        e["last_checked"] = sys.argv[1] if len(sys.argv) > 1 else "2026-10-24"
        done += 1
with open(path, "w") as fh:
    json.dump(entries, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print(f"triage applied to {done} entries" + (f"; unknown ids: {missing}" if missing else ""))
