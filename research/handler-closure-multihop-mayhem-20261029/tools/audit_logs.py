"""Post-process saved receipts with the repository's own log audits.

1) `scripts/pump_diagnostic_audit.py`'s audit(): the bounded diagnostic oracle
   used by pump_validate_all (panics, AnchorError codes, compared values).
2) A strict ordered-log comparison that drops ONLY complete runtime
   compute-meter lines (same rule as the strict-ordered-log policy), retaining
   every other ordered line including Source coordinates.

Usage: python3 audit_logs.py <output.json> <receipt.json.gz> [<label>=<path> ...]
"""
import gzip
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
spec = importlib.util.spec_from_file_location('pump_diagnostic_audit', REPO / 'scripts/pump_diagnostic_audit.py')
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)

COMPUTE_METER = re.compile(r'^Program \w+ consumed \d+ of \d+ compute units$')


def strict_logs(lines):
    return [line for line in lines if not COMPUTE_METER.match(line)]


def main():
    output = Path(sys.argv[1])
    suites = {}
    labels = {}
    for arg in sys.argv[2:]:
    # argument forms: <path> or <label>=<path>
        if '=' in arg and not Path(arg).exists():
            label, path = arg.split('=', 1)
        else:
            path = arg
            label = Path(arg).stem
        raw = Path(path).read_bytes()
        data = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        suites[label] = data
        labels[label] = path
    diagnostic = audit_mod.audit(suites)
    strict = {}
    for label, data in suites.items():
        rows = []
        for case in data.get('cases', []):
            o = case.get('original') or {}
            c = case.get('candidate') or {}
            if not c:
                continue
            a, b = strict_logs(o.get('logs', o.get('logs', []))), strict_logs(c.get('logs', []))
            if a != b:
                first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                rows.append({'case': case.get('case'),
                             'first_difference_index': first,
                             'original_line': a[first] if first < len(a) else None,
                             'candidate_line': b[first] if first < len(b) else None,
                             'original_length': len(a), 'candidate_length': len(b)})
        strict[label] = {'cases_compared': sum(1 for case in data.get('cases', []) if case.get('candidate')),
                         'ordered_log_mismatches_excluding_compute_meter': rows}
    result = {'scope': __doc__,
              'inputs': labels,
              'diagnostic_audit': {k: diagnostic[k] for k in ('coverage', 'log_bearing_cases', 'mismatches')},
              'strict_ordered_logs': strict}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'diagnostic_mismatches': len(diagnostic['mismatches']),
                      'strict': {k: len(v['ordered_log_mismatches_excluding_compute_meter']) for k, v in strict.items()}}, indent=2))


if __name__ == '__main__':
    main()
