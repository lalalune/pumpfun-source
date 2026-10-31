# probe.py <name>: colmap rx/<name>/m.ll; find event accounts piece (root %0, sites in 0x4d80-0x5200 voting r6), old_fee, force piece=r6
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event'); n=sys.argv[1]; os.chdir(O)
subprocess.run(['python3','tools/colmap.py',f'rx/{n}/m.ll',f'cm/{n}'],capture_output=True)
d=json.load(open(f'cm/{n}.json')); R=d['rows']
ev=[r for r in R if r['root']==0 and any(0x4d00<=int(s,16)<0x5200 for s in r['sites']) and r['orig_major'] in('r6','r2') and r['ours']!='r6']
res={'name':n}
jobs=[{'name':'none','full':1}]+[{'name':f"f{r['vreg']}",'force':f"{r['vreg']}=r6",'full':1} for r in ev[:3]]
jf=f's/pj_{n}.jsonl'; rf=f's/pr_{n}.jsonl'
open(jf,'w').write('\n'.join(json.dumps(j) for j in jobs)+'\n')
if os.path.exists(rf): os.remove(rf)
subprocess.run(['python3','tools/screen.py',f'rx/{n}/m.ll',jf,rf,'4'],capture_output=True)
res['ev']=[(r['vreg'],r['ours'],r['sites'][:3]) for r in ev[:3]]
res['forces']=[(x['name'],x.get('ratio'),x.get('bytes')) for x in map(json.loads,open(rf))]
print(json.dumps(res))
