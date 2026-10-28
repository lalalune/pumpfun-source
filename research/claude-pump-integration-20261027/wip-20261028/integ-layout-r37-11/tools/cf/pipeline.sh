#!/bin/bash
# pipeline.sh <base crate dir> <out crate dir> : rebuild the coordfiles lane source from a base crate.
set -e
L=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work/lanes/coordfiles
rm -rf "$2"; cp -R "$1" "$2"
python3 $L/structural.py "$2" > /dev/null
python3 $L/closures.py "$2" > /dev/null
python3 $L/split_buy_v2.py "$2" > /dev/null
python3 $L/closures2.py "$2" > /dev/null
python3 $L/closures3.py "$2" > /dev/null
python3 $L/closures4.py "$2" > /dev/null
python3 $L/closures5.py "$2" > /dev/null
python3 $L/closures6.py "$2" > /dev/null
python3 $L/closures7.py "$2" > /dev/null
python3 $L/closures8.py "$2" > /dev/null
python3 $L/layout.py apply --src "$2" --sitemap $L/sitemap.json --sitemap $L/extra_anchors.json --json "$2.layout.json" | grep -E "OFF|FAIL" || true
echo "pipeline done: $2"
