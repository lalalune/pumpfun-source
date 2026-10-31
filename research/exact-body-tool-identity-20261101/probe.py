#!/usr/bin/env python3
"""Run the genuine exact-body CLI with official tools; no program execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

p = argparse.ArgumentParser()
p.add_argument('--checkout', type=Path, required=True)
p.add_argument('--sdk', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--expect', choices=('base', 'fixed'), required=True)
a = p.parse_args()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
objdump = a.sdk / 'llvm/bin/llvm-objdump'
replacement = a.sdk / 'llvm/bin/llvm-readelf'
records = []
with tempfile.TemporaryDirectory(prefix='exact-body-real-tools-', dir=a.output.parent) as temporary:
    root = Path(temporary)
    (root / 'bin').mkdir()
    (root / 'lib').symlink_to(a.sdk / 'llvm/lib', target_is_directory=True)
    tool = root / 'bin/llvm-objdump'
    for mode in ['control', 'replace-after-symbols', 'replace-after-symbols', 'delete-after-symbols']:
        index = len(records)
        shutil.copy2(objdump, tool)
        pending = root / 'bin/replacement'
        shutil.copy2(replacement, pending)
        temps = root / f'tmp-{index}'
        temps.mkdir()
        report = root / f'report-{index}.json'
        env = os.environ.copy()
        env['TMPDIR'] = str(temps)
        command = [sys.executable, '-B', str(a.checkout / 'scripts/pump_exact_body_inventory.py'),
                   '--candidate', str(a.candidate), '--objdump', str(tool), '--output', str(report)]
        process = subprocess.Popen(command, cwd=a.checkout, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        observed = False
        changed = False
        started = time.monotonic()
        while process.poll() is None:
            snapshots = list(temps.glob('pump-symbols-*'))
            if snapshots:
                observed = True
            if observed and not snapshots and mode != 'control' and not changed:
                if mode == 'delete-after-symbols':
                    tool.unlink()
                else:
                    pending.replace(tool)
                changed = True
            if time.monotonic() - started > 30:
                process.kill()
                raise RuntimeError('CLI timed out')
            time.sleep(0.0002)
        stdout, stderr = process.communicate()
        result = json.loads(report.read_text()) if report.exists() else None
        record = {'mode': mode, 'argv': command, 'returncode': process.returncode,
                  'observed_private_symbol_snapshot': observed, 'replacement_after_snapshot_closed': changed,
                  'executed_objdump_sha256': sha(objdump), 'replacement_readelf_sha256': sha(replacement),
                  'current_tool_sha256': sha(tool) if tool.exists() else None, 'reported_tool_sha256': result.get('objdump_sha256') if result else None,
                  'raw_equal_windows': result.get('raw_equal_windows') if result else None,
                  'windows_sha256': hashlib.sha256(json.dumps(result['windows'], sort_keys=True).encode()).hexdigest() if result else None,
                  'candidate_sha256': sha(a.candidate), 'stdout': stdout, 'stderr': stderr}
        records.append(record)
        print(json.dumps({k: v for k, v in record.items() if k not in ('argv', 'stdout', 'stderr')}, indent=2), flush=True)
for record in records:
    assert record['observed_private_symbol_snapshot']
    if record['mode'] != 'control':
        assert record['replacement_after_snapshot_closed']
    if record['mode'] == 'delete-after-symbols' and a.expect == 'base':
        assert record['returncode'] != 0 and record['reported_tool_sha256'] is None
        continue
    assert record['returncode'] == 0
    assert record['raw_equal_windows'] == 188
    assert record['windows_sha256'] == '90492db28b9fb81525eb3b6a48c94731f0d982a3fdd456366fac6c2164d33748'
    expected = (record['replacement_readelf_sha256'] if a.expect == 'base' and record['mode'] != 'control'
                else record['executed_objdump_sha256'])
    assert record['reported_tool_sha256'] == expected
a.output.write_text(json.dumps({'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.checkout, text=True).strip(), 'expectation': a.expect, 'postconditions_passed': True, 'records': records}, indent=2) + '\n')
