from pathlib import Path
import hashlib,json,subprocess,os
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(value,message):
 if not value:raise SystemExit(message)
manifest=json.loads((HERE/'MANIFEST.json').read_text())
for name,entry in manifest['files'].items():
 p=HERE/name;require(p.is_file() and not p.is_symlink(),'missing/nonregular receipt '+name)
 b=p.read_bytes();require(len(b)==entry['bytes'] and sha(b)==entry['sha256'],'receipt changed '+name)
r=json.loads((HERE/'RECORD.json').read_text())
for name,entry in r['applicationInputs'].items():
 p=ROOT/name;require(p.is_file() and not p.is_symlink(),'missing/nonregular input '+name)
 b=p.read_bytes();require(len(b)==entry['bytes'] and sha(b)==entry['sha256'],'source changed '+name)
 blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();require(blob==entry['gitBlob'],'input Git hash mismatch '+name)
 actual=subprocess.check_output(['git','rev-parse',r['candidate']['testedHead']+':app/'+name],cwd=ROOT,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}).decode().strip();require(actual==blob,'qualified Git mismatch '+name)
require(r['baseline']['causalFailures']==2 and r['candidate']['browserPasses']==2,'unexpected finite outcomes')
require(all(v=={'code':0,'signal':None} for v in r['ownedNextExits']),'unclean owned Next exit')
print('Verified',len(r['applicationInputs']),'Git-bound inputs and',len(manifest['files']),'finite receipt files; no full Drawer/provider or visual parity claim')
