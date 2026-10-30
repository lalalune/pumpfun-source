"""Use all 18 actual Fees suites to expose destruction of a caller's ELF."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'work/scoped-proof'
OUT.mkdir(parents=True, exist_ok=True)
SCRIPT = ROOT / 'scripts/fees_validate_all.py'
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
original_sha = sha(ORIGINAL)
candidate = ROOT / 'work/fees-publication-candidate.so'
shutil.copyfile(ORIGINAL, candidate)


def run(name, selected, output):
    with (OUT / (name + '.log')).open('w', encoding='utf-8') as log:
        return subprocess.run([sys.executable, '-B', str(SCRIPT),
                               '--candidate', str(selected), '--output', str(output)],
                              cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                              timeout=1200).returncode


control = OUT / 'control.json'
normal_code = run('control', candidate, control)
result = {'control_cli_returncode': normal_code, 'original_sha256': original_sha,
          'candidate_sha256_before': sha(candidate)}
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
assert normal_code == 0, 'complete original/original control must run first'
document = json.loads(control.read_bytes())
assert len(document['suites']) == 18 and not document['mismatches']
assert document['candidate_sha256'] == document['original_sha256'] == original_sha
result['suite_count'] = len(document['suites'])
result['case_count'] = document['case_count']
(OUT / 'control.json.gz').write_bytes(gzip.compress(control.read_bytes(), mtime=0))
control.unlink()

# This is a disposable copied ELF, never the canonical capture.
alias_code = run('candidate-alias', candidate, candidate)
result.update(alias_cli_returncode=alias_code,
              candidate_sha256_after=sha(candidate),
              candidate_preserved=sha(candidate) == original_sha,
              original_preserved=sha(ORIGINAL) == original_sha)
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
assert result['original_preserved']
assert alias_code != 0 and result['candidate_preserved'], 'aggregate overwrote its caller ELF'

# Existing ordinary report replacement remains supported and atomic.
prior = OUT / 'replacement.json'
prior.write_text('previous report\n')
replacement_code = run('replacement', candidate, prior)
replaced = json.loads(prior.read_bytes())
assert replacement_code == 0 and not replaced['mismatches']
assert replaced['case_count'] == result['case_count'] and len(replaced['suites']) == 18
(OUT / 'replacement.json.gz').write_bytes(gzip.compress(prior.read_bytes(), mtime=0))
prior.unlink()
result['normal_replacement_cli_returncode'] = replacement_code
result['replacement_suite_count'] = len(replaced['suites'])
# Exercise the actual Fees source-directory spelling with an owned unused file.
# The original program sources are never used as destructive output targets.
with tempfile.NamedTemporaryFile(dir=ROOT / 'programs/pump-fees',
                                 prefix='.fees-publication-proof-', suffix='.rs',
                                 delete=False) as stream:
    source_output = Path(stream.name)
    stream.write(b'// owned output-admission control; not compiled\n')
try:
    saved = source_output.read_bytes()
    source_code = run('source-output-alias', candidate, source_output)
    assert source_code != 0 and source_output.read_bytes() == saved
    result['source_directory_output_rejected'] = True
finally:
    source_output.unlink()
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
