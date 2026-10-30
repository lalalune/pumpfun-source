"""Thin receipt wrapper around the repository's scripts/window_measure.py.

Measures normalized/raw window matches between the captured original Pump ELF
and a candidate SYMBOL (unstripped) ELF, exactly per docs/TOOLING.md rules.
Usage: python3 measure_windows.py <original.so> <candidate-unstripped.so> <output.json> [label]
"""
import json
import sys
from pathlib import Path

ROOT = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
sys.path.insert(0, str(ROOT / 'scripts'))
import window_measure  # noqa: E402

original, candidate, output = sys.argv[1], sys.argv[2], sys.argv[3]
label = sys.argv[4] if len(sys.argv) > 4 else 'unlabelled'
rows = window_measure.measure(original, candidate)
matched = sum(1 for r in rows if r['match'])
raw = sum(1 for r in rows if r['raw'])
summary = {
    'label': label,
    'tool': 'scripts/window_measure.py',
    'tool_call': 'window_measure.measure(%r, %r)' % (original, candidate),
    'original': original,
    'candidate': candidate,
    'total': len(rows),
    'normalized_matched': matched,
    'raw_matched': raw,
    'unmatched_originals': [r for r in rows if not r['match']],
}
Path(output).write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ('label', 'total', 'normalized_matched', 'raw_matched')}))
