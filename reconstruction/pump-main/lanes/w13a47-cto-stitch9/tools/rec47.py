# rec47.py <results.jsonl>: record runner rows in the shared ledger
import json,subprocess,os,sys
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a47-cto-stitch9/reconstruction/pump-main/log_attempt.py'
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a47-cto-stitch9'
BASES={'s':('main 52c0b087c',0.62103,'52c0b08'),'c':('main 52c0b087c',0.62103,'52c0b08'),'m2':('main 6ff770f7a',0.62403,'6ff770f'),'m3':(None,None,None)}
if os.path.exists(OUT+'/bases.json'): BASES.update({k:tuple(v) for k,v in json.load(open(OUT+'/bases.json')).items()})
df=OUT+'/recorded.txt'; done=set(open(df).read().split()) if os.path.exists(df) else set()
for ln in open(sys.argv[1]):
    d=json.loads(ln); n=d['name']
    if n in done: continue
    desc,mr,sha=BASES[n.split('-')[0]]
    st=d.get('status')
    status=('partial' if d.get('bytes')==27400 and (d.get('ratio') or 0)>mr else 'rejected') if st=='built' else ('compile-failed' if st=='compile-failed' else 'rejected')
    key=f"0x22a10-w13-{sha}-stitch9-{n}-v1"
    note=f"{d.get('bytes')} B, ratio {d.get('ratio')} (main {mr})"+(f", byte-identical to {d['dup_of']}" if d.get('dup_of') else '')+(f", {d.get('error','')[:150]}" if st!='built' else '')
    data={'output':f"{OUT}/t/{n}",'target':{'ratio':d.get('ratio'),'cand_bytes':d.get('bytes')},'notes':note+' (target_metric; measure.sh only for proposed composites)'}
    r=subprocess.run(['python3',L,'record','--lane','w13a47-cto-stitch9','--approach','stitch-composite','--target','0x22a10','--dedupe-key',key,'--hypothesis',f"{desc} + genes {d.get('genes')} (lane tools/genes47.py: w13a30 genes30 + w13a34 knobs + w13a19/w13a24/w13a09 leads)",'--status',status,'--data',json.dumps(data)],capture_output=True,text=True)
    if '"recorded": true' in r.stdout or 'uplicate' in (r.stdout+r.stderr): done.add(n)
    else: print('fail',n,r.stdout[-200:],r.stderr[-200:])
open(df,'w').write('\n'.join(sorted(done))+'\n')
print(len(done))
