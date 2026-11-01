"""Run the real VM regression with a hash-pinned existing fixture from PR #2164.

This retrieves only inert public JSON from the same repository, never source to
execute. It does not restore that separately owned fixture as part of this PR.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json'
EXPECTED = '17b886a6b4aa7fdc89f2fca9a1b67b318d33998794da59fe4df1fe89ca70bd27'
created = not FIXTURE.exists()
if created:
    url = ('https://api.github.com/repos/pump.fun/pumpfun-source/contents/'
           'research/imported-lab/analysis/pump_fun/config-snapshot.json'
           '?ref=5dcef2992bccfc27c601a139ed9c898e7f943793')
    with urllib.request.urlopen(url, timeout=60) as response:
        data = base64.b64decode(json.load(response)['content'])
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise SystemExit('fixture hash differs from the reviewed PR #2164 input')
    json.loads(data)
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_bytes(data)
try:
    if hashlib.sha256(FIXTURE.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('existing fixture differs from the reviewed input')
    destination = ROOT / 'work/scoped-proof'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'fixture-provenance.json').write_text(json.dumps({
        'source_pr': 2164, 'source_revision': '5dcef2992bccfc27c601a139ed9c898e7f943793',
        'path': str(FIXTURE.relative_to(ROOT)), 'sha256': EXPECTED}, indent=2) + '\n')
    result = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/test_quote_control_external_inputs.py')],
                            env={**os.environ, 'PUMP_EXTERNAL_PROOF_OUT': str(destination)})
finally:
    if created:
        FIXTURE.unlink()
raise SystemExit(result.returncode)
