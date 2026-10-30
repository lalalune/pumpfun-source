#!/bin/bash
# Regenerate programs/pump/link/ordered.ld from the current source (see ../NOTES.md).
# regen.sh <scratch dir>   (needs the identity toolchain; one build, ~25 s)
set -euo pipefail
R=$(cd "$(dirname "$0")/../../../.." && pwd)   # reconstruction/
S=$1; mkdir -p "$S"
rsync -a --delete --exclude /target/ "$R/../programs/pump/" "$S/src/"
cp "$R/harness/sbf_default.ld" "$S/src/link/ordered.ld"   # rustc order, hook active (link map)
python3 "$R/harness/fastbuild.py" --src "$S/src" --work "$S/work" --out "$S/default" > "$S/default.json"
T=$(dirname "$0")
python3 "$T/census.py" "$S/default/unstripped.so" "$S/census.json" > /dev/null
python3 "$T/refine.py" "$S/default/unstripped.so" "$S/ref.json" > /dev/null
python3 "$T/genld.py" "$S/default/unstripped.so" "$S/ref.json" "$S/default/link.map" "$R/harness/sbf_default.ld" "$S/ordered.ld"
cmp "$S/ordered.ld" "$R/../programs/pump/link/ordered.ld" && echo "ordered.ld reproduced" || echo "ordered.ld differs: $S/ordered.ld"
