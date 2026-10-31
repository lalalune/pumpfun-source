#!/usr/bin/env python3
"""Compare real analysis CLI totals with raw captured relocation table entries."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from elftools.elf.elffile import ELFFile

p = argparse.ArgumentParser()
p.add_argument('--checkout', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--expect', choices=('base', 'fixed'), required=True)
a = p.parse_args()
root = a.checkout.resolve()
if a.output.exists():
    p.error('choose a fresh output file')
records = []
sha = lambda raw: hashlib.sha256(raw).hexdigest()
for name in ['pump', 'pump_amm', 'pump_fees', 'mayhem']:
    capture = root / f'evidence/original/{name}/deployed.so'
    image = capture.read_bytes()
    parsed = ELFFile(io.BytesIO(image))
    text = parsed.get_section_by_name('.text')
    raw_relocations = list(parsed.get_section_by_name('.rel.dyn').iter_relocations())
    raw_text = sum(text['sh_addr'] <= row['r_offset'] < text['sh_addr'] + text['sh_size'] for row in raw_relocations)
    with tempfile.TemporaryDirectory(prefix='relocation-total-cli-') as temporary:
        output = Path(temporary) / 'packet'
        command = [sys.executable, '-B', str(root / 'scripts/analyze_program.py'), '--program', name, '--output', str(output)]
        cli = subprocess.run(command, cwd=root, capture_output=True, text=True)
        assert cli.returncode == 0, cli.stderr
        summary = json.loads((output / 'summary.json').read_text())
        windows = json.loads((output / 'window-inventory.json').read_text())
        window_total = sum(row['relocations'] for row in windows)
        assert window_total == raw_text
        readme = (output / 'README.md').read_text()
        if a.expect == 'fixed':
            assert summary['total_relocations'] == len(raw_relocations)
            assert summary['text_window_relocations'] == window_total
            assert f'| Total ELF relocations | {len(raw_relocations)} |' in readme
            assert f'| Text-window relocations | {raw_text} |' in readme
        else:
            assert summary['total_relocations'] == raw_text < len(raw_relocations)
            assert 'text_window_relocations' not in summary
            assert f'| Total relocations | {raw_text} |' in readme
        verifier = subprocess.run([sys.executable, '-B', str(output / 'verify.py')], capture_output=True, text=True)
        assert verifier.returncode == 0, verifier.stdout + verifier.stderr
        unrelated = {key: value for key, value in summary.items() if key not in ('total_relocations', 'text_window_relocations')}
        record = {'program': name, 'capture_sha256': sha(image),
                  'raw_relocation_rows': len(raw_relocations), 'raw_text_relocation_rows': raw_text,
                  'raw_data_relocation_rows': len(raw_relocations) - raw_text,
                  'reported_total_relocations': summary['total_relocations'],
                  'reported_text_window_relocations': summary.get('text_window_relocations'),
                  'window_relocation_sum': window_total,
                  'other_summary_fields_sha256': sha(json.dumps(unrelated, sort_keys=True).encode()),
                  'payload_sha256': {filename: sha((output / filename).read_bytes()) for filename in ['window-inventory.json', 'call-graph.json', 'function-index.json', 'section-layout.json', 'verify.py']},
                  'cli_returncode': cli.returncode, 'generated_verifier_returncode': verifier.returncode}
    assert capture.read_bytes() == image
    records.append(record)
    print(json.dumps(record), flush=True)
a.output.write_text(json.dumps({'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
                               'expectation': a.expect, 'postconditions_passed': True,
                               'records': records, 'scope': 'Four actual uninstrumented static CLI packets; raw .rel.dyn rows independently parsed with pyelftools0.32. No program, model, VM, compiler or binary synthesis.'}, indent=2) + '\n')
