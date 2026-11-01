#!/bin/sh
set -eu

root=${1:-"$(git rev-parse --show-toplevel)"}
out=${2:?usage: build_candidate.sh [repo-root] OUTPUT-DIRECTORY}
work=${3:-"$out/work"}

python3 "$root/reconstruction/toolchain/bootstrap.py" --sdk-check full
python3 "$root/reconstruction/harness/fastbuild.py" \
  --src "$root/programs/pump" --work "$work" --out "$out" \
  --recipe identity --timeout 1200
test -s "$out/candidate.so"
shasum -a 256 "$out/candidate.so"
