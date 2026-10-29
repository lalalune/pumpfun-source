from pathlib import Path
import hashlib,json,subprocess,os
HERE=Path(__file__).resolve().parent;APP=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(value,message):
 if not value:raise SystemExit(message)
def git(*args):return subprocess.check_output(['git',*args],cwd=APP,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
m=json.loads((HERE/'MANIFEST.json').read_text())
for name,e in m['files'].items():
 p=HERE/name;require(p.is_file() and not p.is_symlink(),'missing/nonregular receipt '+name);b=p.read_bytes();require(len(b)==e['bytes'] and sha(b)==e['sha256'],'receipt changed '+name)
r=json.loads((HERE/'RECORD.json').read_text())
for name,e in r['qualifiedInputs'].items():
 p=APP/name;require(p.is_file() and not p.is_symlink(),'missing/nonregular input '+name);b=p.read_bytes();require(len(b)==e['bytes'] and sha(b)==e['sha256'] and blob(b)==e['gitBlob'],'input changed '+name)
 require(git('rev-parse',r['evidenceToolHead']+':app/'+name).decode().strip()==e['gitBlob'],'evidence Git input changed '+name)
 if e['kind'] in ['runtime','browser-method']:require(git('rev-parse',r['candidate']['browserRuntimeHead']+':app/'+name).decode().strip()==e['gitBlob'],'runtime/method changed after measured source '+name)
 if e['kind']=='browser-method':require(git('rev-parse',r['baseline']['head']+':app/'+name).decode().strip()==e['gitBlob'],'before/after method changed '+name)
for name,e in r['referenceTooling']['files'].items():
 b=git('show',r['referenceTooling']['commit']+':app/'+name);require(len(b)==e['bytes'] and sha(b)==e['sha256'] and blob(b)==e['gitBlob'],'reference tool changed '+name)
for width in ['390','1280']:
 before=json.loads((HERE/'browser/baseline'/width/'observed.json').read_text());after=json.loads((HERE/'browser/fixed'/width/'observed.json').read_text());require(before['admitted']['data']==after['admitted']['data'],'API data changed')
 require([(v['label'],v['value'])for v in before['measured']['rows']]==[(v['label'],v['value'])for v in after['measured']['rows']],'date text changed')
 require(before['prizeData']==after['prizeData'],'prize text/row heights changed');require(all(len(v['labelRects'])==1 for v in after['measured']['rows']),'after labels split');require(after['measured']['scrollWidth']<=after['measured']['clientWidth']+1,'after horizontal overflow')
require(all(v=={'code':0,'signal':None}for v in r['ownedNextExits']),'unclean Next exit')
print('Verified',len(r['qualifiedInputs']),'qualified Git inputs, four external public reference tools and',len(m['files']),'finite receipt files; no production/provider/pixel parity claim')
