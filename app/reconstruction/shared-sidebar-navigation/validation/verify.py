"""Check selected frozen inputs and retained finite React observations."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
APP = HERE.parents[2]


def require(value, reason):
    if not value:
        raise SystemExit(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe(root, name):
    parts = Path(name).parts
    require(parts and not Path(name).is_absolute() and ".." not in parts, "unsafe path")
    result = root
    for part in parts:
        result = result / part
        require(not result.is_symlink(), "symlink input/receipt")
    require(result.is_file(), "missing file: " + name)
    return result


record = json.loads((HERE / "RECORD.json").read_text())
manifest = json.loads((HERE / "MANIFEST.json").read_text())
actual = set()
for path in HERE.rglob("*"):
    require(not path.is_symlink(), "symlink receipt")
    if path.is_file() and path != HERE / "MANIFEST.json":
        actual.add(path.relative_to(HERE).as_posix())
require(actual == set(manifest["files"]), "receipt membership changed")
for name, entry in manifest["files"].items():
    data = safe(HERE, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"], "receipt changed: " + name)
env = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}
tree = subprocess.check_output(["git", "rev-parse", record["testedHead"] + "^{tree}"],
                               cwd=APP, env=env).decode().strip()
require(tree == record["testedTree"], "tested tree changed")
for name, entry in record["inputs"].items():
    expected = subprocess.check_output(["git", "rev-parse", record["testedHead"] + ":app/" + name],
                                       cwd=APP, env=env).decode().strip()
    require(expected == entry["gitBlob"], "Git binding changed: " + name)
    data = safe(APP, name).read_bytes()
    require(len(data) == entry["bytes"] and sha(data) == entry["sha256"]
            and blob(data) == entry["gitBlob"], "executed input changed: " + name)

observations=json.loads((HERE/'browser/observations.json').read_text())
require(observations['syntheticOnly'] is True and observations['bundleSha256']==record['browserBundleSha256'],'bundle/provenance changed')
require(observations['requests']==[{'method':'GET','url':name} for name in ['/','/fixture.js']]*2,'GET ledger changed')
require([r['width'] for r in observations['results']]==[390,1280],'widths changed')
for row in observations['results']:
    require(row['expectedErrors']==['SYNTHETIC trigger callback denial'] and row['unexpectedErrors']==[] and row['overflow'] is False,'errors/overflow changed')
    require(row['initial']['context']=={'open':False,'openMobile':False,'state':'collapsed'} and row['initial']['listeners']==1,'root/default/listener changed')
    require(row['batched']['context']['open']==(row['width']>=768) and row['batched']['context']['openMobile'] is False,'captureddesktop/mobilefunctional quirk changed')
    require(round(row['groupWidth'])==(288 if row['width']<768 else 56),'diagnostic native geometry changed')
    require(row['routed']['href'].split('?',1)[0].endswith('/explore') and row['routed']['context']['openMobile']==(row['width']<768),'owned route/port state changed')
    require(any(e['kind']=='navigate-callback' and e['key']=='explore' for e in row['routed']['events']),'actual forwarded callback lost')
    require(row['keyboard']['listeners']==1 and any(e['kind']=='media' and e['query']=='(max-width: 767px)' for e in row['keyboard']['events']),'native query/key handler changed')
    require([e for e in row['prevented']['events'] if e['kind']=='trigger-callback'][-1]['prevent'] is True,'prevented callback input changed')
    require(row['denied']['context']=={'open':row['width']>=768,'openMobile':False,'state':'expanded' if row['width']>=768 else 'collapsed'},'denial source-state changed')
    require(row['unmounted']['listeners']==0,'global key cleanup changed')
    require(row['controlledDenied']['context']['open'] is False and [e for e in row['controlledDenied']['events'] if e['kind']=='controlled-callback'][-1]=={'kind':'controlled-callback','value':True,'accepted':False},'controlled callback denial changed')
    require(row['controlledAccepted']['context']['open'] is True and row['cleanup']['listeners']==0,'controlled update/final cleanup changed')
checks=json.loads((HERE/'checks.json').read_text());require(checks['head']==record['testedHead'] and len(checks['results'])==6 and all(c['returncode']==0 for c in checks['results']),'check statuses changed');require(record['checks']==checks and record['browser']['returncode']==0,'result mapping changed')
import re
for name,count in [('focused-final.log',18),('browser-frozen.tap',1)]:
    log=gzip.decompress((HERE/'logs'/(name+'.gz')).read_bytes()).decode()
    for label,value in [('tests',count),('pass',count),('fail',0)]:require(re.search(r'(?m)^# '+label+' '+str(value)+r'$',log),'executed counts changed')
contract=json.loads(safe(APP,'reconstruction/shared-sidebar-navigation/contract.json').read_text());require(len(contract['retained'])==45 and len(contract['publicSidebarExports'])==12,'source closure changed');require([n['defaultOpen'] for n in contract['capturedRoot']['layout']]==[False,False],'actual captured root admissions changed')
print('Verified',len(record['inputs']),'selected executed Git-bound inputs,',len(manifest['files']),'sealed receipts; finite completeSidebar/controller with explicit diagnostic primitive/router/style ports')
