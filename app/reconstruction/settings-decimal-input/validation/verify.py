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
    require(row['expectedErrors']==['SYNTHETIC numeric commit denial'] and row['unexpectedErrors']==[] and row['overflow'] is False,'errors/overflow changed')
    require(row['initial']['state']['value']==5 and len(row['initial']['mounts'])==1,'initial props/lifetime changed')
    require(row['clampedDraft']['commits'][-1]=={'value':2.5,'accepted':True},'min clamp changed')
    require(row['parentUpdated']['state']['value']==9,'controlled parent update changed')
    require(row['maximumDraft']['commits'][-1]=={'value':123456789012,'accepted':True},'12-character commit changed')
    require(row['disabled']['state']['value']==8 and row['disabled']['state']['isDisabled'] is True,'disabled boundary changed')
    require(row['denied']['state']['value']==8 and row['denied']['commits'][-1]=={'value':6.25,'accepted':False},'denied callback/parent state changed')
    require(row['retried']['state']['value']==7.75 and row['retried']['commits'][-1]=={'value':7.75,'accepted':True},'retry changed')
    require(row['remounted']['state']['value']==18 and len(row['remounted']['mounts'])==2 and len(row['remounted']['unmounts'])==1,'remount changed')
    require(len(row['unmounted']['unmounts'])==2,'final cleanup changed')
checks=json.loads((HERE/'checks.json').read_text())
require(checks['head']==record['testedHead'] and len(checks['results'])==6 and all(c['returncode']==0 for c in checks['results']),'check statuses changed')
require(record['checks']==checks and record['browser']['returncode']==0,'result mapping changed')
import re
for name,count in [('focused-final.log',18),('browser-frozen.tap',1)]:
    log=gzip.decompress((HERE/'logs'/(name+'.gz')).read_bytes()).decode()
    for label,value in [('tests',count),('pass',count),('fail',0)]:require(re.search(r'(?m)^# '+label+' '+str(value)+r'$',log),'executed counts changed')
old=gzip.decompress((HERE/'logs/source-setup-missing-evidence.log.gz').read_bytes()).decode()
require('ENOENT' in old and "lstat" in old and '/app/evidence' in old,'initial sparse setup failure lost')
print('Verified',len(record['inputs']),'selected executed Git-bound inputs,',len(manifest['files']),'sealed receipts; finite decimal input display/callback proof only')
