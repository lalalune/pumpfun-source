"""Offline synthetic token-total boundary; no reachable-state claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--host', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('liquidity_fixture', args.repo / 'tests/test_pump_amm_liquidity_captured.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for path, expected in ((m.AMM_ELF, m.AMM_SHA256), (m.TOKEN_ELF, m.TOKEN_SHA256), (m.TOKEN22_ELF, m.TOKEN22_SHA256)):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
cases = []
for ix in ('deposit', 'withdraw'):
    for leg in ('base', 'quote'):
        short = 'b' if leg == 'base' else 'q'
        dest = ('v' if ix == 'deposit' else 'u') + short
        source = ('u' if ix == 'deposit' else 'v') + short
        threshold = m.U64_MAX * 1_000_000 // 1_000_001 if ix == 'deposit' else m.U64_MAX - (400 if leg == 'base' else 200)
        for program in (m.TOKEN, m.TOKEN22):
            for offset in (-1, 0, 1):
                c = {'ix': ix, 'amount': 1, leg + '_owner': program, dest + '_amt': threshold + offset}
                if ix == 'deposit':
                    c[source + '_amt'] = m.U64_MAX
                cases.append((f'{ix}_{leg}_{"spl" if program == m.TOKEN else "2022"}_edge_{offset}', c, dest))
for program in (m.TOKEN, m.TOKEN22):
    cases.append((f'maintainer_max_{"spl" if program == m.TOKEN else "2022"}', {'base_owner': program, 'vb_amt': m.U64_MAX, 'ub_amt': m.U64_MAX, 'amount': 1}, 'vb'))
cases += [
    ('wrapped_base_then_insufficient_quote', {'vb_amt': m.U64_MAX, 'ub_amt': m.U64_MAX, 'uq_amt': 0, 'amount': 1}, 'vb'),
    ('wrapped_base_then_2022_quote_overflow', {'vb_amt': m.U64_MAX, 'ub_amt': m.U64_MAX, 'vq_amt': m.U64_MAX, 'uq_amt': m.U64_MAX, 'quote_owner': m.TOKEN22, 'amount': 1}, 'vb'),
    ('wrapped_base_then_lp_overflow', {'vb_amt': m.U64_MAX, 'ub_amt': m.U64_MAX, 'ul_amt': m.U64_MAX, 'amount': 1}, 'vb'),
]
answers = subprocess.run([str(args.host)], input=''.join(m.host_line(c) + '\n' for _, c, _ in cases), capture_output=True, text=True, check=True).stdout.splitlines()
assert len(answers) == len(cases)
checker = m.PumpAmmLiquidityCapturedTests()
rows = []
for (name, c, dest), answer in zip(cases, answers):
    captured = m.run_captured(c)
    try:
        checker.assert_matches(answer, captured)
        mismatch = None
    except AssertionError as exc:
        mismatch = str(exc)
    key = getattr(m, dest.upper())
    rows.append({'name': name, 'host_outcome': answer.split(',')[0], 'captured_error': captured['error'],
                 'destination_before': struct.unpack_from('<Q', captured['before'][key].data, 64)[0],
                 'destination_after': struct.unpack_from('<Q', captured['after'][key].data, 64)[0],
                 'account_rollback': captured['same'], 'events': len(captured['events']), 'mismatch': mismatch})
result = {'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.repo, text=True).strip(),
          'images': {str(p.relative_to(args.repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (m.AMM_ELF, m.TOKEN_ELF, m.TOKEN22_ELF)},
          'host_sha256': hashlib.sha256(args.host.read_bytes()).hexdigest(), 'count': len(rows),
          'mismatches': sum(r['mismatch'] is not None for r in rows), 'rows': rows,
          'limit': 'Synthetic inconsistent token totals; finite local host-model parity only. No reachable on-chain state or complete equivalence claim.'}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'count': result['count'], 'mismatches': result['mismatches']}))
