"""Score a retained genuine unstripped ELF, then exercise real report publication."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'work/scoped-proof'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, default=ROOT / 'research/pump-multihop-token-quote-20261029/build/candidate/symbols.so.gz')
args = parser.parse_args()
blob = args.candidate.read_bytes()
if blob.startswith(b'\x1f\x8b'):
    blob = gzip.decompress(blob)
candidate = OUT / 'candidate.so'
candidate.write_bytes(blob)
harness = ROOT / 'reconstruction/harness'
control = OUT / 'control.json'
published = OUT / 'published.json'
observation = OUT / 'observation.json'
env = dict(os.environ, TMP=str(OUT), TEMP=str(OUT))


def run(name, command):
    completed = subprocess.run([sys.executable, '-B', *command], env=env,
                               cwd=ROOT, capture_output=True, text=True, timeout=240)
    (OUT / (name + '.stdout')).write_text(completed.stdout, encoding='utf-8')
    (OUT / (name + '.stderr')).write_text(completed.stderr, encoding='utf-8')
    return completed.returncode


assert run('control', [str(harness / 'score.py'), str(candidate), '--no-baseline',
                       '--quiet', '--json', str(control)]) == 0
wrapper = '''import hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import score
prior=Path(sys.argv[3]).parent/('.score-'+str(os.getpid()))
saved=Path(sys.argv[2]).read_bytes()
prior.write_bytes(saved)
sys.argv=[str(Path(sys.argv[1])/'score.py'),sys.argv[4],'--no-baseline','--quiet','--json',sys.argv[3]]
try:
    score.main()
finally:
    Path(OBSERVATION).write_text(json.dumps({'prior_survives':prior.exists(),'prior_unchanged':prior.exists() and prior.read_bytes()==saved,'prior_sha256':hashlib.sha256(saved).hexdigest()}),encoding='utf-8')
'''.replace('OBSERVATION', repr(str(observation)))
code = run('collision', ['-c', wrapper, str(harness), str(control), str(published), str(candidate)])
result = json.loads(observation.read_bytes())
document = json.loads(control.read_bytes())
result.update(cli_returncode=code, candidate_sha256=hashlib.sha256(blob).hexdigest(),
              selected_candidate=str(args.candidate), summary=document['summary'],
              control_report_sha256=hashlib.sha256(control.read_bytes()).hexdigest(),
              output_exists=published.exists(),
              output_equals_control=published.exists() and published.read_bytes() == control.read_bytes())
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
for report in (control, published):
    if report.is_file():
        report.with_suffix('.json.gz').write_bytes(gzip.compress(report.read_bytes(), mtime=0))
assert code == 0 and result['prior_unchanged'] and result['output_equals_control'], 'real scorer lost or blocked a prior receipt'
print(json.dumps(result))
