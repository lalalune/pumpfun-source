from pathlib import Path
import hashlib, json, subprocess, os
HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]

def require(value, message):
    if not value:
        raise SystemExit(message)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\x00' + b).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=APP, env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'})
m = json.loads((HERE / 'MANIFEST.json').read_text())
r = json.loads((HERE / 'RECORD.json').read_text())
for name, e in m['files'].items():
    p = HERE / name
    require(p.is_file() and (not p.is_symlink()), 'missing receipt ' + name)
    b = p.read_bytes()
    require(len(b) == e['bytes'] and sha(b) == e['sha256'], 'receipt changed ' + name)
for name, e in r['qualifiedInputs'].items():
    p = APP / name
    require(p.is_file() and (not p.is_symlink()), 'missing input ' + name)
    b = p.read_bytes()
    require(len(b) == e['bytes'] and sha(b) == e['sha256'] and (blob(b) == e['gitBlob']), 'input changed ' + name)
    require(git('rev-parse', r['candidate']['head'] + ':app/' + name).decode().strip() == e['gitBlob'], 'Git input changed ' + name)
    if e['kind'] == 'browser-method':
        require(git('rev-parse', r['baseline']['head'] + ':app/' + name).decode().strip() == e['gitBlob'], 'method changed ' + name)
for name, e in r['referenceTooling']['files'].items():
    b = git('show', r['referenceTooling']['commit'] + ':app/' + name)
    require(len(b) == e['bytes'] and sha(b) == e['sha256'] and (blob(b) == e['gitBlob']), 'reference changed ' + name)
t = r['preparationTool']
b = git('show', t['commit'] + ':' + t['path'])
require(len(b) == t['bytes'] and sha(b) == t['sha256'] and (blob(b) == t['gitBlob']), 'preparation tool changed')
for width in ['390', '1280']:
    before = json.loads((HERE / 'browser/baseline' / width / 'admission.json').read_text())
    after = json.loads((HERE / 'browser/fixed' / width / 'observed.json').read_text())
    require(before['list'] == after['list'] and before['detail'] == after['detail'], 'API data changed ' + width)
    a = after['beforeTick']
    b = after['afterTick']
    require(a['labels'] == ['Days', 'Hours', 'Minutes', 'Seconds'] and b['totalSeconds'] < a['totalSeconds'] and (b['now'] > a['now']), 'real-clock observation invalid ' + width)
    require(b['clientWidth'] > 0 and b['scrollWidth'] <= b['clientWidth'] + 1 and (after['errors'] == []), 'UI negative control failed ' + width)
require(all((v == {'code': 0, 'signal': None} for v in r['ownedFinalWorkerNextExits'])), 'unclean final worker exit')
print('Verified', len(r['qualifiedInputs']), 'Git inputs, four referenced loopback tools, preparation tool and', len(m['files']), 'finite receipts; no provider/API/expiry parity claim')
