#!/usr/bin/env python3
"""Fold a completed regression run (full.json.gz from regress.sh) into an integration package and reseal it."""
import gzip, hashlib, json, re, subprocess, sys
from pathlib import Path
W = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
pkg = sys.argv[1]
P = W / 'int/research/claude-pump-integration-20261027' / pkg
run = W / 'full/work/claude-reg' / pkg
rb = (run / 'full.json.gz').read_bytes(); rep = json.loads(gzip.decompress(rb))
res = json.loads((P / 'RESULT.json').read_text())
assert rep['candidate_sha256'] == res['candidate_sha256'], 'regression ran on a different candidate'
assert not rep['mismatches'] and len(rep['suites']) == 44
(P / 'full.json.gz').write_bytes(rb)
m = re.search(r'seconds=(\d+)', (run / 'run.log').read_text())
res['regression'] = {'runner': 'scripts/pump_validate_parallel.py --captured-loader', 'suites': len(rep['suites']), 'cases': rep['case_count'],
                     'paired_log_cases': rep['diagnostics']['log_bearing_cases'], 'mismatches': 0, 'seconds': int(m.group(1)) if m else None}
(P / 'RESULT.json').write_text(json.dumps(res, indent=2) + '\n')
rd = (P / 'README.md').read_text().replace('The captured-loader regression corpus has not been run for this exact package yet.',
     f"The 44-suite captured-loader corpus passes against this exact candidate: {rep['case_count']:,} cases, {rep['diagnostics']['log_bearing_cases']:,} paired diagnostic logs, 0 mismatches (`full.json.gz`).")
(P / 'README.md').write_text(rd)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = sorted(str(p.relative_to(P)) for p in P.rglob('*') if p.is_file() and p.name != 'MANIFEST.json' and '__pycache__' not in p.parts)
(P / 'MANIFEST.json').write_text(json.dumps({f: sha(P / f) for f in files}, indent=1) + '\n')
r = subprocess.run(['/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source/work/test-env/bin/python', '-B', str(P / 'verify.py')], cwd=W / 'int', capture_output=True, text=True)
print(r.stdout[-1200:], r.stderr[-1500:]); sys.exit(r.returncode)
