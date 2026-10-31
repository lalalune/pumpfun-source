#!/usr/bin/env python3
"""Observe actual static-pattern production and compare the generated packets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--checkout', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--expect', choices=('base', 'fixed'), required=True)
a = p.parse_args()
root = a.checkout.resolve()
if a.output.exists():
    p.error('choose a fresh output file')
sys.path.insert(0, str(root / 'scripts'))
from window_elf_reader import Elf
import deep_section_analysis as analysis

EXPECTED = {'associated_token': 86, 'donation_relay': 483, 'spl_token': 24,
            'spl_token_2022': 420, 'token_metadata': 314, 'mayhem': 441,
            'pump': 1208, 'pump_amm': 742, 'pump_fees': 578}
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

records = []
for path in sorted((root / 'evidence').glob('*/*/deployed.so')):
    observed = {}
    def observe(frame, event, result):
        if event == 'return' and frame.f_code is analysis.recover_anchor_idl.__code__:
            # Observe the real producer's completed list before its display
            # slice; neither instructions nor its return value are changed.
            observed['patterns'] = frame.f_locals['deser_patterns']
    sys.setprofile(observe)
    try:
        result = analysis.recover_anchor_idl(Elf(path))
    finally:
        sys.setprofile(None)
    full = observed['patterns']
    name = path.parent.name
    assert len(full) == EXPECTED[name]
    assert result['deserialization_patterns'] == full[:100]
    assert result['inferred_struct_sizes'] == sorted({row['likely_struct_size'] for row in full if row['likely_struct_size'] > 0})
    if a.expect == 'fixed':
        assert result['deserialization_pattern_count'] == len(full)
        assert result['displayed_deserialization_pattern_count'] == len(full[:100])
    record = {'program': name, 'capture': str(path.relative_to(root)),
              'capture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'observed_full_count': len(full), 'displayed_count': len(result['deserialization_patterns']),
              'reported_full_count': result.get('deserialization_pattern_count'),
              'full_patterns_sha256': digest(full),
              'displayed_patterns_sha256': digest(result['deserialization_patterns']),
              'inferred_struct_sizes_sha256': digest(result['inferred_struct_sizes']),
              'other_layer4_fields_sha256': digest({k: v for k, v in result.items() if k not in {'deserialization_pattern_count', 'displayed_deserialization_pattern_count'}})}
    if name in {'pump', 'pump_amm', 'pump_fees', 'mayhem', 'donation_relay'}:
        with tempfile.TemporaryDirectory(prefix='section-count-cli-') as temporary:
            output = Path(temporary) / 'packet'
            command = [sys.executable, '-B', str(root / 'scripts/deep_section_analysis.py'), '--program', name, '--output', str(output)]
            cli = subprocess.run(command, cwd=root, capture_output=True, text=True)
            assert cli.returncode == 0, cli.stderr
            layer = json.loads((output / 'layer4-anchor-idl.json').read_text())
            assert layer == result
            summary = json.loads((output / 'summary.json').read_text())['layer4_anchor_idl']
            expected_count = len(full) if a.expect == 'fixed' else len(full[:100])
            assert summary['deser_patterns'] == expected_count
            readme = (output / 'README.md').read_text()
            assert f'Deserialization patterns: {expected_count}' in readme
            if a.expect == 'fixed':
                assert summary['displayed_deser_patterns'] == len(full[:100])
                assert f'({len(full[:100])} displayed)' in readme
            verified = subprocess.run([sys.executable, '-B', str(output / 'verify.py')], cwd=root, capture_output=True, text=True)
            assert verified.returncode == 0, verified.stdout + verified.stderr
            record['cli'] = {'returncode': cli.returncode, 'summary_count': summary['deser_patterns'],
                             'summary_displayed_count': summary.get('displayed_deser_patterns'),
                             'generated_verifier_returncode': verified.returncode,
                             'other_layers_sha256': {f'layer{i}': hashlib.sha256(next(output.glob(f'layer{i}-*.json')).read_bytes()).hexdigest() for i in (1, 2, 3, 5)}}
    records.append(record)
    print(json.dumps({'program': name, 'full': len(full), 'displayed': len(full[:100]), 'cli_summary': record.get('cli', {}).get('summary_count') }), flush=True)
assert len(records) == 9
payload = {'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
           'expected_revision_behavior': a.expect, 'postconditions_passed': True,
           'method': 'Read-only observation of actual producer locals; nine unchanged captured ELF inputs; five real static CLI packets and generated verifiers. No model, compiler or VM execution.',
           'records': records}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(payload, indent=2) + '\n')
