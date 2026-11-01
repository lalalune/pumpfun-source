#!/bin/bash
# Usage: trial.sh <name> <workslot 0|1> <edits.json>
# edits.json: [[relpath, old, new], ...] applied (exactly-once replacements) to a fresh copy of the lane crate.
set -u
NAME=$1; SLOT=$2; EDITS=$3
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a10-hint-noforcehops
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a10-hint-noforcehops
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools
BASE=/Users/shawwalters/.cache/pumpfun-reconstruction/w11/current-baseline
V=$OUT/var/$NAME; rm -rf "$V"; mkdir -p "$V"
rsync -a --exclude target "$WT/programs/pump/" "$V/"
python3 - "$V" "$EDITS" <<'PY' || exit 1
import json, sys, pathlib
root = pathlib.Path(sys.argv[1]); edits = json.load(open(sys.argv[2]))
for rel, old, new in edits:
    p = root / rel; s = p.read_text()
    n = s.count(old)
    if n != 1: sys.exit(f"edit not unique in {rel}: count={n}: {old[:80]!r}")
    s2 = s.replace(old, new)
    if s.count('\n') != s2.count('\n'): sys.exit(f"line count changed in {rel}")
    p.write_text(s2)
PY
R=$("$TOOLS/measure.sh" "$V" "$OUT/work$SLOT" "$OUT/t/$NAME")
echo "$R" > "$OUT/t/$NAME/measure.json"
CMPU=$(cmp -s "$OUT/t/$NAME/unstripped.so" "$BASE/unstripped.so" && echo same || echo diff)
CMPS=$(cmp -s "$OUT/t/$NAME/candidate.so" "$BASE/candidate.so" && echo same || echo diff)
echo "$NAME stripped=$CMPS unstripped=$CMPU $R" | cut -c1-900
