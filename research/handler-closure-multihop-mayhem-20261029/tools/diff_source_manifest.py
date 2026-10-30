"""Diff the current programs/pump source manifest against the build report's record."""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
sys.path.insert(0, str(REPO / 'scripts'))
import build_source_manifest

ROOT = REPO
SOURCE_DIRECTORY = ROOT / 'programs/pump'
report = json.loads((ROOT / 'research/pump-program-creator-notice-qualification-20261028/builds/primary/build-comparison.json').read_text())
recorded = report['source_sha256']
current = build_source_manifest.source_manifest(SOURCE_DIRECTORY, ROOT, ROOT, cwd=ROOT)
print('recorded keys:', len(recorded), 'current keys:', len(current))
print('key sets equal:', set(recorded) == set(current))
for key in sorted(set(recorded) | set(current)):
    a, b = recorded.get(key), current.get(key)
    if a != b:
        print('DIFF', key, 'recorded=', (a or '')[:16], 'current=', (b or '')[:16])
