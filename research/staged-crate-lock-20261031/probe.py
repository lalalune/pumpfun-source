"""Exercise the actual stage helper with real rsync, without a compiler."""
from pathlib import Path
import argparse,hashlib,json,os,sys
p=argparse.ArgumentParser();p.add_argument('--harness',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.harness.resolve()))
import fastbuild
from source_inputs import snapshot
root=a.work.resolve();root.mkdir(parents=True,exist_ok=False)
source=root/'source';(source/'src').mkdir(parents=True)
(source/'Cargo.toml').write_text('[package]\nname="staging_probe"\nversion="0.1.0"\nedition="2021"\n[profile.release]\npanic="abort"\n[workspace]\n',encoding='utf-8')
(source/'Cargo.lock').write_text('version = 3\n',encoding='utf-8')
(source/'src/lib.rs').write_text('pub const VALUE: u8 = 1;\n',encoding='utf-8')
admitted=snapshot(source)
fresh=fastbuild.stage(source,root/'fresh-workspace',expected_inputs=admitted)
reused=fastbuild.stage(source,root/'reused-workspace',expected_inputs=admitted)
assert not (fresh/'Cargo.lock').exists() and not (reused/'Cargo.lock').exists()
stale=b'version = 3\n# stale crate-local input from another staging process\n'
(reused/'Cargo.lock').write_bytes(stale)
returned=fastbuild.stage(source,root/'reused-workspace',expected_inputs=admitted)
assert returned==reused and snapshot(source)==admitted
fresh_inputs,reused_inputs=snapshot(fresh),snapshot(reused)
report={'sourceSHA256':admitted['sha256'],'sourceUnchanged':True,'actualStageReturned':True,'sameAdmittedSource':True,'freshCrateLockExists':(fresh/'Cargo.lock').exists(),'reusedCrateLockExists':(reused/'Cargo.lock').exists(),'reusedCrateLockRetainedUnchanged':(reused/'Cargo.lock').read_bytes()==stale if (reused/'Cargo.lock').exists()else False,'freshStagedSHA256':fresh_inputs['sha256'],'reusedStagedSHA256':reused_inputs['sha256'],'sameStagedReceipt':fresh_inputs==reused_inputs,'unexpectedStagedFiles':sorted({r['path']for r in reused_inputs['files']}-{r['path']for r in fresh_inputs['files']}),'limits':'Actual source snapshot and fastbuild.stage with real rsync only; no compiler, SDK, scoring, VM or program ELF execution.'}
(root/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
