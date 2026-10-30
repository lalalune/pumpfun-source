import hashlib
import json
from pathlib import Path

REPO = Path('/mnt/c/Users/arzfeqsdeidm/Desktop/yop/AA/pumpfun-source-maintained')
base = REPO / 'research/pump-program-creator-notice-qualification-20261028/builds/primary'
report = json.loads((base / 'build-comparison.json').read_text())
attempt = json.loads((base / 'build-attempt.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
print('attempt returncode:', attempt.get('returncode'))
print('attempt source_unchanged:', attempt.get('source_unchanged'))
print('attempt source_sha256 == attempt source_after_sha256:', attempt.get('source_sha256') == attempt.get('source_after_sha256'))
print('attempt source_sha256 == report source_sha256:', attempt.get('source_sha256') == report.get('source_sha256'))
print('report comparison candidate_sha256:', report['comparison']['candidate_sha256'])
print('actual candidate sha256:', sha(base / 'candidate.so'))
print('match:', report['comparison']['candidate_sha256'] == sha(base / 'candidate.so'))
print('report workspace_directory:', report.get('workspace_directory'))
print('report source_directory:', report.get('source_directory'))
