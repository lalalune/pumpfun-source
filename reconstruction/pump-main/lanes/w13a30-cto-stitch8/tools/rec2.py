# rec2.py <results.jsonl> : record runner rows; base map in BASES (prefix -> desc, main ratio, sha7)
import json,subprocess,os,sys
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a30-cto-stitch8/reconstruction/pump-main/log_attempt.py'
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a30-cto-stitch8'
BASES=json.load(open(OUT+'/tools/bases.json'))
df=OUT+'/recorded.txt'; done=set(open(df).read().split()) if os.path.exists(df) else set()
for ln in open(sys.argv[1]):
    d=json.loads(ln); n=d['name']
    if n in done: continue
    desc,mr,sha=BASES[n.split('-')[0]]
    st=d.get('status')
    status=('partial' if d.get('bytes')==27400 and (d.get('ratio') or 0)>mr else 'rejected') if st=='built' else ('compile-failed' if st=='compile-failed' else 'rejected')
    key=f"0x22a10-w13-{sha}-stitch8-{n.replace('.','-').replace('+','-')}-v1"
    note=f"{d.get('bytes')} B, ratio {d.get('ratio')}, slots {d.get('slots_diff')}"+(f", byte-identical to {d['dup_of']}" if d.get('dup_of') else '')+(f", {d.get('error','')[:150]}" if st!='built' else '')
    data={'output':f"{OUT}/t/{n}",'target':{'ratio':d.get('ratio'),'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},'notes':note+' (target_metric; full score only for landed composites)'}
    r=subprocess.run(['python3',L,'record','--lane','w13a30-cto-stitch8','--approach','stitch-composite','--target','0x22a10','--dedupe-key',key,'--hypothesis',f"{desc} + genes {d.get('genes')} (lane tools/genes30.py)",'--status',status,'--data',json.dumps(data)],capture_output=True,text=True)
    if '"recorded": true' in r.stdout or 'duplicate' in r.stdout: done.add(n)
    else: print('fail',n,r.stdout[-200:],r.stderr[-200:])
open(df,'w').write('\n'.join(sorted(done))+'\n')
print(len(done))
