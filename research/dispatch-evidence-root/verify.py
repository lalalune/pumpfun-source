#!/usr/bin/env python3
"""Verify the landed dispatch-helper transition against Git history only."""
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


def direct_scripts(revision):
    return sorted(p for p in git('ls-tree', '-r', '--name-only', revision, '--', 'scripts')
                  .decode('utf-8').splitlines() if p.count('/') == 1 and p.endswith('.py'))


base = record['baseRevision']
landed = record['landedRevision']
require(re.fullmatch('[0-9a-f]{40}', base), 'base must be an exact commit')
require(re.fullmatch('[0-9a-f]{40}', landed), 'landed revision must be an exact commit')
require(subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', base, landed]).returncode == 0,
        'base is not an ancestor of the landed revision')
parent = git('rev-parse', f'{landed}^').decode('utf-8').strip()
asset = record['asset']
require(asset['path'] == 'scripts/recover_dispatch.py', 'unexpected transition asset')
require(sha(git('show', f"{base}:{asset['path']}")) == asset['beforeSha256'], 'base script drift')
require(sha(git('show', f"{parent}:{asset['path']}")) == asset['beforeSha256'], 'landed parent script drift')
require(sha(git('show', f"{landed}:{asset['path']}")) == asset['afterSha256'], 'landed script drift')
base_paths = direct_scripts(base)
names = record['directPythonScriptSet']
require(len(base_paths) == names['count'], 'script-name count drift')
require(sha(('\n'.join(base_paths) + '\n').encode('utf-8')) == names['sha256'], 'script-name digest drift')
require(direct_scripts(landed) == direct_scripts(parent), 'landed transition changed the direct Python script-name set')
changed = [p for p in git('diff', '--name-only', parent, landed, '--', 'scripts').decode('utf-8').splitlines()
           if p.count('/') == 1 and p.endswith('.py')]
require(changed == [asset['path']], f'landed transition changed other direct scripts: {changed}')
for path, expected in record['unchangedCaptures'].items():
    require(sha(git('show', f'{base}:{path}')) == expected, f'base capture drift: {path}')
    require(sha(git('show', f'{parent}:{path}')) == expected, f'landed parent capture drift: {path}')
    require(sha(git('show', f'{landed}:{path}')) == expected, f'landed capture drift: {path}')
print('Landed dispatch asset transition verified; no acceptance or equivalence claim.')
