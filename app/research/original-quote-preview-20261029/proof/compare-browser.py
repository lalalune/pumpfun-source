"""Same immutable seed + browser story; restore all four host files on failure."""
import hashlib,json,os,pathlib,subprocess
root=pathlib.Path('/workspace/pump-app-social');work=root/'work/original-quote-preview'
base='7f1f6627b8e3aae1d7e4a9c99c2652202549a0cd'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(), 'clean committed code required'
support=root/'app/packages/frontend/next-env.d.ts';support_bytes=support.read_bytes()
paths=['app/packages/frontend/src/components/feed/FeedList.tsx','app/packages/frontend/src/components/feed/feed-data.ts','app/packages/frontend/src/components/feed/feed-snapshot.ts','app/packages/frontend/src/app/page.tsx']
originals={p:(root/p).read_bytes()for p in paths}
sh=lambda b:hashlib.sha256(b).hexdigest()
before={p:subprocess.check_output(['git','show',base+':'+p],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})for p in paths}
command=['corepack','pnpm','exec','playwright','test','--config','playwright.quote-preview.config.ts']
env={**os.environ,'DEBUG':'pw:webserver'}
record={'schemaVersion':1,'candidateCodeCommit':head,'baseCommit':base,'productFiles':[{'path':p,'baseSha256':sh(before[p]),'candidateSha256':sh(originals[p])}for p in paths],'runs':[],'limits':['Same actual hash-bound immutable legacy seed in both runs; no test input replacement','Before restores exactly four host files from actual1374public parent; unconsumed new modules and identical authored harness remain','Passing baseline asserts expected absence, not an observed assertion failure','NEW authored local join is not original API/coordinator recovery; original owning consumers use modern envelopes','Unavailable state is source/model/join-tested, not browser-observed in the checked-in dataset']}
try:
 for p,data in before.items():(root/p).write_bytes(data)
 baseline=command+['--grep','hash-bound local Home','--output','../../artifacts/playwright-quote-preview-baseline']
 with(work/'browser-baseline.log').open('w')as log:result=subprocess.run(baseline,cwd=root/'app/packages/frontend',env={**env,'QUOTE_PREVIEW_EXPECT_BASELINE':'1'},stdout=log,stderr=subprocess.STDOUT)
 record['runs'].append({'name':'baseline','command':baseline,'mode':'expected absence','exitCode':result.returncode})
 if result.returncode:raise RuntimeError('baseline failed; all four candidate files restored in finally')
finally:
 for p,data in originals.items():(root/p).write_bytes(data)
 support.write_bytes(support_bytes)
 (work/'BROWSER-COMPARISON.json').write_text(json.dumps(record,indent=2)+'\n')
for p,data in originals.items():assert(root/p).read_bytes()==data
try:
 with(work/'browser-candidate.log').open('w')as log:result=subprocess.run(command,cwd=root/'app/packages/frontend',env={k:v for k,v in env.items()if k!='QUOTE_PREVIEW_EXPECT_BASELINE'},stdout=log,stderr=subprocess.STDOUT)
 record['runs'].append({'name':'candidate','command':command,'mode':'actual mounted previews and affected Home regressions','exitCode':result.returncode})
finally:
 support.write_bytes(support_bytes)
 (work/'BROWSER-COMPARISON.json').write_text(json.dumps(record,indent=2)+'\n')
if result.returncode:raise RuntimeError('candidate browser failed')
print(json.dumps(record,indent=2))
