#!/usr/bin/env python3
"""mv.py <slot> <edits.py>...: for each edits file (EDITS=[(old,new)] on admin_cto.rs, line count kept, optional BASE=crate dir),
copy crate, apply, measure.sh into t/<name>; append one result line to res.jsonl. Deletes .so unless KEEP=1."""
import sys,os,subprocess,runpy,json,shutil,glob
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a23-cto-decisionenum')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a23-cto-decisionenum'
M='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh'
slot=sys.argv[1]
for ef in sys.argv[2:]:
    name=os.path.basename(ef)[:-3]; g=runpy.run_path(ef); src=g.get('BASE',WT+'/programs/pump')
    v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
    subprocess.run(['rsync','-a','--exclude','target',src+'/',v+'/'],check=True)
    f=v+'/src/creator/admin_cto.rs'; s=open(f).read(); n0=s.count('\n'); err=None
    for a,b in g['EDITS']:
        c=s.count(a)
        if c!=1: err=f'count {c}: {a[:100]}'; break
        s=s.replace(a,b)
    if not err and s.count('\n')!=n0: err='line count changed'
    if err:
        r={'name':name,'error':err}
    else:
        open(f,'w').write(s)
        p=subprocess.run([M,v,f'{OUT}/work{slot}',f'{OUT}/t/{name}'],capture_output=True,text=True)
        try:
            d=json.loads(p.stdout.strip().splitlines()[-1])
            c=d.get('admin_cto') or {}
            r={'name':name,'ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),
               'norm':d.get('normalized'),'raw':d.get('raw'),'losses':len(d.get('losses') or []),'raw_losses':len(d.get('raw_losses') or []),'err':(d.get('error') or '')[-600:]}
        except Exception as ex:
            r={'name':name,'error':'parse '+str(ex)+p.stdout[-500:]+p.stderr[-500:]}
        if os.environ.get('KEEP')!='1':
            for so in glob.glob(f'{OUT}/t/{name}/*.so'):
                if not so.endswith('unstripped.so'): os.remove(so)
    shutil.rmtree(v,ignore_errors=True)
    print(json.dumps(r),flush=True)
    open(f'{OUT}/res.jsonl','a').write(json.dumps(r)+'\n')
