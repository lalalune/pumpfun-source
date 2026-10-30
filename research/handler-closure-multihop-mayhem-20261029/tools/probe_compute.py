"""Compute-budget probe: same AMM work, different Pump ELF identity.

Runs the retained two-curve Tokenkeg case (which fits the default 200k budget on
both sides) and records every `consumed X of Y` line. The pre-Pump AMM work is
identical in each run; only the loaded Pump ELF differs (captured original,
current candidate, and the candidate's unstripped symbol build = same source).
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
FROZEN = REPO / 'repro/pump/tokenkeg-two-curve-fortyeight/harness/pump_tokenkeg_two_curve_differential.py'
spec = importlib.util.spec_from_file_location('tk', FROZEN)
tk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tk)

PUMP = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
AMM = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
CONSUMED = re.compile(r'Program (\w+) consumed (\d+) of (\d+) compute units')

binaries = {
    'original-captured': None,
    'candidate-stripped': REPO / 'research/pump-program-creator-notice-qualification-20261028/builds/primary/candidate.so',
    'candidate-unstripped': REPO / 'research/pump-program-creator-notice-qualification-20261028/builds/primary/unstripped.so',
}
out = {}
for name, path in binaries.items():
    r = tk.invoke(False, 1000000, 'captured', 1, path.resolve() if path else None)
    rows = []
    for line in r['logs']:
        m = CONSUMED.search(line)
        if m:
            rows.append({'program': m.group(1)[:8], 'consumed': int(m.group(2)), 'budget': int(m.group(3))})
    pump_rows = [x for x in rows if x['program'] == PUMP[:8]]
    amm_rows = [x for x in rows if x['program'] == AMM[:8]]
    out[name] = {
        'pump_elf_bytes': (path.stat().st_size if path else (REPO / 'evidence/original/pump/deployed.so').stat().st_size),
        'error': r['error'],
        'pump_frames': pump_rows,
        'amm_frames': amm_rows,
        'pump_entry_budget': pump_rows[0]['budget'] if pump_rows else None,
    }
print(json.dumps(out, indent=2))
Path(sys.argv[1]).write_text(json.dumps(out, indent=2) + '\n')
