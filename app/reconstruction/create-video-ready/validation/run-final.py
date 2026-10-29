import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

root=Path('/workspace/pump-app-chart')
frontend=root/'app/packages/frontend'
proof=Path('/workspace/pump-create-video-audit')
base='094a06f18df738d41e77070c1a009e135671ac1a'
candidate='4fa1124d7d20bcb5182e23c2122c9e3e0dc65252'
env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
git=lambda *args:subprocess.check_output(['git',*args],cwd=root,env=env)
assert git('rev-parse','HEAD').decode().strip()==candidate
assert not git('status','--porcelain')
with socket.socket() as check:assert check.connect_ex(('127.0.0.1',3010))!=0
sourcepath='app/packages/frontend/src/app/create-video-input.tsx'
source=(root/sourcepath).read_bytes()
(proof/'candidate-create-video-input.tsx').write_bytes(source)
(proof/'executed-final.spec.ts.txt').write_bytes((frontend/'tests/create-video-ready.spec.ts').read_bytes())
preflight=[]
for path in ['app/tsconfig.base.json','app/pnpm-lock.yaml','app/packages/frontend/tests/create-video-ready.spec.ts','app/packages/frontend/tests/create-video.spec.ts','app/packages/frontend/tests/create.spec.ts','app/packages/frontend/tests/fixtures/native-2s.webm','app/packages/frontend/tests/fixtures/empty.webm']:
 b=(root/path).read_bytes();assert b==git('show',candidate+':'+path)
 preflight.append({'path':path,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(proof/'final-preflight.json').write_text(json.dumps(preflight,indent=2)+'\n')
config=frontend/'playwright.create-video-ready.tmp.config.ts'
config.write_text('''import {defineConfig} from "@playwright/test";
import base from "./playwright.config";
export default defineConfig({...base,reporter:[["line"],["json",{outputFile:`/workspace/pump-create-video-audit/report-${process.env.VIDEO_READY_PHASE}.json`}]],outputDir:`/workspace/pump-create-video-audit/browser-${process.env.VIDEO_READY_PHASE}`,webServer:{...base.webServer,command:"corepack pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3010",url:"http://127.0.0.1:3010",reuseExistingServer:false,timeout:120000,env:{PUMPFUN_DEVELOPER_API_KEY:""}}});
''')
(proof/'executed-final.config.ts.txt').write_text(config.read_text())

def admit(phase,revision):
 records=[]
 for path in git('ls-tree','-r','--name-only',revision,'--','app/packages/frontend/src').decode().splitlines():
  b=(root/path).read_bytes();assert b==git('show',revision+':'+path),path
  records.append({'path':path,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 (proof/(phase+'-runtime-inputs.json')).write_text(json.dumps(records,indent=2)+'\n')

def run(phase,tests):
 command=['corepack','pnpm','exec','playwright','test','--config',config.name,*tests]
 start=time.time()
 with (proof/(phase+'-browser.log')).open('wb') as log:
  r=subprocess.run(command,cwd=frontend,env={**env,'VIDEO_READY_PHASE':phase},stdout=log,stderr=subprocess.STDOUT)
 record={'source':base if phase=='qualified-base' else candidate,'command':command,'cwd':str(frontend),'returncode':r.returncode,'seconds':time.time()-start}
 (proof/(phase+'-command.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
 return r.returncode

try:
 (root/sourcepath).write_bytes(git('show',base+':'+sourcepath))
 admit('qualified-base',base)
 assert run('qualified-base',['tests/create-video-ready.spec.ts'])==1
finally:
 (root/sourcepath).write_bytes(source)
admit('qualified-candidate',candidate)
try:
 code=run('qualified-candidate',['tests/create-video-ready.spec.ts','tests/create-video.spec.ts','tests/create.spec.ts'])
finally:
 config.unlink(missing_ok=True)
 p=frontend/'next-env.d.ts'
 if p.is_file():(proof/'generated-final-next-env.d.ts').write_bytes(p.read_bytes())
 p.write_bytes(git('show',candidate+':app/packages/frontend/next-env.d.ts'))
 assert (root/sourcepath).read_bytes()==source
 for row in preflight:assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
raise SystemExit(code)
