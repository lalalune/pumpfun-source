"""Exercise documented compressed outputs with complete real Fees CLI corpora.

Both comparison sides use captured images as controls. No source build, mock VM,
synthetic positive receipt, live RPC or successful source equivalence is claimed.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/scoped-proof'
CAPTURE = ROOT / 'evidence/original/pump_fees/deployed.so'
ORIGINAL_SHA = '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')


def main():
    assert sha(CAPTURE) == ORIGINAL_SHA
    transition = json.loads((HERE / 'proposed-asset-transition.json').read_text())
    actual = {name: sha(ROOT / name) for name in transition['before']}
    stage = next((key for key in ('before','after') if actual == transition[key]), None)
    if stage is None:
        raise RuntimeError('producer source drift outside reviewed transition')
    OUT.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env.pop('PYTHONOPTIMIZE', None)
    results, errors = {}, []
    for script in actual:
        directory = OUT / Path(script).stem
        directory.mkdir()
        records = {}
        for label, filename in (('plain','report.json'), ('gzip','report.json.gz')):
            output = directory / filename
            command = [sys.executable, '-B', str(ROOT/script), '--candidate', str(CAPTURE), '--output', str(output)]
            print(command, flush=True)
            child = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                                   encoding='utf-8', errors='replace', timeout=1000)
            row = {'command': command, 'returncode': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr}
            records[label] = row
            save(directory/(label+'-command.json'), row)
            if child.returncode or not output.is_file():
                raise RuntimeError(f'genuine producer failed for {script}: {row}')
            wire = output.read_bytes()
            compressed = wire.startswith(b'\x1f\x8b')
            raw = gzip.decompress(wire) if compressed else wire
            report = json.loads(raw)
            assert report['cases'] and not report['mismatches']
            assert report['candidate_sha256'] == ORIGINAL_SHA
            if 'original_sha256' in report:
                assert report['original_sha256'] == ORIGINAL_SHA
            row.update({'wire_sha256': sha(output), 'decoded_sha256': hashlib.sha256(raw).hexdigest(),
                        'compressed': compressed, 'case_count': len(report['cases'])})
            if compressed != (stage == 'after' and label == 'gzip'):
                errors.append(script+': unexpected compression for '+label)
            if compressed and wire[4:8] != bytes(4):
                errors.append(script+': nonzero gzip mtime')
            if label == 'gzip':
                # This is the standard-library consumer, not a substitute
                # verdict or an execution result manufactured by this proof.
                decode_command = [sys.executable, '-B', '-c',
                    'import gzip,json,sys; r=json.load(gzip.open(sys.argv[1],"rt",encoding="utf-8")); print(len(r["cases"]))', str(output)]
                decoded = subprocess.run(decode_command, cwd=ROOT, capture_output=True, text=True, timeout=60)
                row['gzip_reader'] = {'command': decode_command, 'returncode': decoded.returncode,
                                      'stdout': decoded.stdout, 'stderr': decoded.stderr}
                expected = 0 if stage == 'after' else 1
                if decoded.returncode != expected or (expected and 'BadGzipFile' not in decoded.stderr):
                    errors.append(script+': unexpected standard gzip-reader outcome')
            save(directory/(label+'-command.json'), row)
        if records['plain']['decoded_sha256'] != records['gzip']['decoded_sha256']:
            errors.append(script+': decoded report content differs between output names')
        results[script] = records
    summary = {'revision': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'stage': stage, 'producer_sha256': actual, 'capture_sha256': ORIGINAL_SHA,
        'producers': results, 'errors': errors,
        'total_cases_per_output_format': sum(r['plain']['case_count'] for r in results.values()),
        'scope': 'Complete real CLI corpora for the selected nine producers, captured-image controls, receipt framing only',
        'limits': 'No reconstructed-source, full-protocol or security conclusion; signature claims remain those of the unchanged ordinary-signature fixture implementations'}
    save(OUT/'summary.json', summary)
    print(json.dumps({'stage': stage, 'case_counts': {k:v['plain']['case_count'] for k,v in results.items()},
        'gzip_reader_statuses': {k:v['gzip']['gzip_reader']['returncode'] for k,v in results.items()}, 'errors': errors}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
