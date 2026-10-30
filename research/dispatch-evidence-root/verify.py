#!/usr/bin/env python3
"""Verify the proposed dispatch-helper transition without changing any assets."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
record = json.loads(Path(__file__).with_name('transition.json').read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


base = record['baseRevision']
require(re.fullmatch('[0-9a-f]{40}', base), 'base must be an exact commit')
asset = record['asset']
require(asset['path'] == 'scripts/recover_dispatch.py', 'unexpected transition asset')
require(sha(git('show', f"{base}:{asset['path']}")) == asset['beforeSha256'], 'base script drift')
require(sha((ROOT / asset['path']).read_bytes()) == asset['afterSha256'], 'current script drift')
base_paths = sorted(p for p in git('ls-tree', '-r', '--name-only', base, '--', 'scripts')
                    .decode('utf-8').splitlines() if p.count('/') == 1 and p.endswith('.py'))
current_paths = sorted(p.relative_to(ROOT).as_posix()
                       for p in (ROOT / 'scripts').glob('*.py') if p.is_file())
require(current_paths == base_paths, 'direct Python script-name set changed')
names = record['directPythonScriptSet']
require(len(base_paths) == names['count'], 'script-name count drift')
require(sha(('\n'.join(base_paths) + '\n').encode('utf-8')) == names['sha256'], 'script-name digest drift')
for path, expected in record['unchangedCaptures'].items():
    require(sha(git('show', f'{base}:{path}')) == expected, f'base capture drift: {path}')
    require(sha((ROOT / path).read_bytes()) == expected, f'current capture drift: {path}')
print('Proposed dispatch asset transition verified; no acceptance or equivalence claim.')
