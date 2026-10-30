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
require(observations['bundleSha256']==record['browserBundleSha256'],'bundle changed')
require(observations['syntheticOnly'] is True,'fixture provenance changed')
require(observations['requests']==[{'method':'GET','url':name} for name in ['/?keep=one&keep=two','/fixture.js']]*2,'GET ledger changed')
require([r['width'] for r in observations['results']]==[390,1280],'widths changed')
for row in observations['results']:
    require(row['errors']==[] and row['overflow'] is False,'error/overflow changed')
    require(row['initial']['listeners']==row['initial']['loadCount']==0,'initial gate changed')
    require(row['initial']['schema']=={'settings':True,'setting':True} and row['initial']['options']=={'history':'replace','clearOnDefault':True},'atomic query capability changed')
    disabled=row['disabledOpen'];events=disabled['events'];before=next(e for e in events if e['kind']=='replace-before');after=next(e for e in events if e['kind']=='replace-after');dispatch=next(e for e in events if e['kind']=='dispatch')
    require(events.index(before)<events.index(after)<events.index(dispatch) and after['href']==dispatch['href']!=before['href'],'URL/event order changed')
    require(disabled['state']=={'synthetic':'history-state'} and disabled['listeners']==disabled['loadCount']==0,'disabled helper effects changed')
    require(row['opened']['listeners']==row['opened']['loadCount']==1 and row['opened']['props']=={'section':'feed','focusSettingId':'feed.synthetic'},'open mount/props changed')
    require(row['changed']['changes'][-1]=={'settings':'privacy','setting':'privacy.synthetic'},'section callback changed')
    require(row['emptyCallback']['changes'][-1]=={'settings':'feed','setting':''} and row['emptyHelper']['changes'][-1]=={'settings':'privacy','setting':''},'nullish callback changed')
    require(any(e['kind']=='dispatch' and e['detail'].get('settingId')=='' and 'setting=' not in e['href'] for e in row['emptyHelper']['events']),'helper truthy deletion changed')
    require(row['closed']['changes'][-1]=={'settings':None,'setting':None} and len(row['closed']['unmounts'])==1,'close/unmount changed')
    require(len(row['reopened']['mounts'])==2 and len(row['gated']['unmounts'])==2 and row['gated']['listeners']==0,'gate cleanup changed')
    require(len(row['noListener']['changes'])==len(row['gated']['changes']),'unregistered host received event')
    require(len(row['flagRestored']['mounts'])==3,'flag restore mount changed')
    require(len(row['unmounted']['unmounts'])==3 and row['unmounted']['listeners']==row['unmounted']['subscribers']==row['unmounted']['flagSubscribers']==0,'unmount cleanup changed')
    require(len(row['remounted']['mounts'])==4 and row['remounted']['loadCount']==row['remounted']['listeners']==1,'remount capability behavior changed')
checks=json.loads((HERE/'checks.json').read_text())
require(checks['head']==record['testedHead'] and len(checks['results'])==6 and all(c['returncode']==0 for c in checks['results']),'check status changed')
require(record['checks']==checks and record['browser']['returncode']==0,'result mapping changed')
import re
for name,count in [('focused-final.log',18),('browser-frozen.tap',1)]:
    log=gzip.decompress((HERE/'logs'/(name+'.gz')).read_bytes()).decode()
    for label,value in [('tests',count),('pass',count),('fail',0)]:
        require(re.search(r'(?m)^# '+label+' '+str(value)+r'$',log),'final counts changed')
old=gzip.decompress((HERE/'logs/focused-development.tap.gz').read_bytes()).decode()
require(re.search(r'(?m)^# pass 15$',old) and re.search(r'(?m)^# fail 3$',old) and "reading 'children'" in old,'development harness failure lost')
print('Verified',len(record['inputs']),'selected executed Git-bound inputs,',len(manifest['files']),'sealed receipts; finite Settings URL/event/conditional-mount proof only')
