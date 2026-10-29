from pathlib import Path
import json, hashlib, subprocess, os
HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]

def require(value, reason):
    if not value:
        raise SystemExit(reason)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\x00' + b).hexdigest()

def safe(root, name):
    parts = Path(name).parts
    require(not Path(name).is_absolute() and parts and ('..' not in parts), 'unsafe validation path')
    p = root
    for part in parts:
        p = p / part
        require(not p.is_symlink(), 'symlink validation path')
    return p
m = json.loads((HERE / 'MANIFEST.json').read_text())
r = json.loads((HERE / 'RECORD.json').read_text())
for name, e in m['files'].items():
    b = safe(HERE, name).read_bytes()
    require(len(b) == e['bytes'] and sha(b) == e['sha256'], 'receipt changed ' + name)
for name, e in r['inputs'].items():
    expected = subprocess.check_output(['git', 'rev-parse', r['testedHead'] + ':app/' + name], cwd=APP, env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'}).decode().strip()
    require(expected == e['gitBlob'], 'Git binding changed ' + name)
    b = safe(APP, name).read_bytes()
    require(len(b) == e['bytes'] and sha(b) == e['sha256'] and (blob(b) == e['gitBlob']), 'executed input changed ' + name)
o = json.loads((HERE / 'browser/observations.json').read_text())
require(o['bundleSha256'] == r['browserBundleSha256'], 'bundle binding changed')
require([e['width'] for e in o['results']] == [390, 1280], 'widths changed')
for e in o['results']:
    require(e['errors'] == [] and e['overflow'] <= 1 and (not e['functional']['setterChanged']), 'browser control failed')
    require([v[2] for v in e['functional']['calls'] if v[0] == 'write'] == ['true', 'false'], 'fresh functional writes changed')
    require(e['fallback']['values']['home.show-animations'] == 'false' and e['fallback']['freshRead'] is False, 'fallback evidence changed')
    require(not [v for v in e['afterUnmount']['calls'] if v[0] == 'read'], 'unmount observation changed')
require(all((q['method'] == 'GET' and q['url'] in ['/', '/fixture.js'] for q in o['requests'])), 'unexpected request')
print('Verified', len(r['inputs']), 'Git-bound executed inputs and', len(m['files']), 'receipts; finite synthetic-port React proof only')
