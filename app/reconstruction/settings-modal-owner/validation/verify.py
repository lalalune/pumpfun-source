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
    require(row['expectedErrors']==['SYNTHETIC reset callback denial'] and row['unexpectedErrors']==[] and row['overflow'] is False,'errors/overflow changed')
    require(row['pending']['state']['ready'] is False and row['pending']['mounts']==row['pending']['queries']==[],'pending display changed')
    require(row['first']['state']['ready'] is True and len(row['first']['mounts'])==1,'ready display changed')
    require(row['selected']['events'][-1]=={'kind':'select','section':'privacy'},'tab callback changed')
    require(row['searching']['queries'][-1]=={'query':'first','visibleSections':['feed','privacy']},'trim/query/visibleprops changed')
    require(row['sameSearchMode']['queries'][-1]=={'query':'second','visibleSections':['feed','privacy']},'same-mode query changed')
    require(row['deniedSection']['state']['section']=='account' and row['deniedSection']['state']['sections']==row['first']['state']['sections'],'inert denied-selection setup changed')
    require(row['resetDenied']['events'][-1]=={'kind':'reset','section':'feed','accepted':False},'reset denial boundary changed')
    require(row['resetAccepted']['events'][-1]=={'kind':'reset','section':'feed','accepted':True},'reset retry boundary changed')
    require(not any(e['kind']=='close' for e in row['stillOpen']['events']),'truthy Dialog change closed owner')
    require(sum(e['kind']=='close' for e in row['done']['events'])==1 and sum(e['kind']=='close' for e in row['closed']['events'])==2,'close mapping changed')
    require(row['remounted']['state']['focusSettingId'] is None and row['remounted']['state']['section']=='privacy','remount setup changed')
    require(len(row['unmounted']['mounts'])==len(row['unmounted']['unmounts']),'readonly child cleanup changed')
checks=json.loads((HERE/'checks.json').read_text())
require(checks['head']==record['testedHead'] and len(checks['results'])==6 and all(c['returncode']==0 for c in checks['results']),'check statuses changed')
require(record['checks']==checks and record['browser']['returncode']==0,'result mapping changed')
import re
for name,count in [('focused-final.log',18),('browser-frozen.tap',1)]:
    log=gzip.decompress((HERE/'logs'/(name+'.gz')).read_bytes()).decode()
    for label,value in [('tests',count),('pass',count),('fail',0)]:require(re.search(r'(?m)^# '+label+' '+str(value)+r'$',log),'executed counts changed')
contract=json.loads(safe(APP,'reconstruction/settings-modal-owner/contract.json').read_text())
require(contract['owner']['memoSlots']==100 and [t['binding'] for t in contract['owner']['transformations']]==['Y','J'] and len(contract['retained'])==2,'owner transformation ledger changed')
print('Verified',len(record['inputs']),'selected executed Git-bound inputs,',len(manifest['files']),'sealed receipts; complete safe Settings display/controller boundary with2hook ports only')
