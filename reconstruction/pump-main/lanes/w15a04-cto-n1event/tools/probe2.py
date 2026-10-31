# probe2.py <name>: event piece (root %0, sites 0x4d00-0x5200, orig r6/r2) and pool ptr (orig r7 at 0x4bc0/0x4bc8) forces, singles + pair
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event'); n=sys.argv[1]; os.chdir(O)
if not os.path.exists(f'cm/{n}.json'): subprocess.run(['python3','tools/colmap.py',f'rx/{n}/m.ll',f'cm/{n}'],capture_output=True)
R=json.load(open(f'cm/{n}.json'))['rows']
ev=[r for r in R if r['root']==0 and any(0x4d00<=int(s,16)<0x5200 for s in r['sites']) and r['orig_major'] in('r6','r2') and r['ours']!='r6'][:1]
pp=[r for r in R if any(s in ('4bc0','4bc8') for s in r['sites']) and r['orig_major']=='r7' and r['ours']!='r7'][:1]
F=[f"{r['vreg']}=r6" for r in ev]+[f"{r['vreg']}=r7" for r in pp]
jobs=[{'name':'none'}]+[{'name':f,'force':f} for f in F]+([{'name':'pair','force':','.join(F)}] if len(F)==2 else [])
jf=f's/p2j_{n}.jsonl'; rf=f's/p2r_{n}.jsonl'
open(jf,'w').write('\n'.join(json.dumps(j) for j in jobs)+'\n')
if os.path.exists(rf): os.remove(rf)
subprocess.run(['python3','tools/screen.py',f'rx/{n}/m.ll',jf,rf,'4'],capture_output=True)
print(json.dumps({'name':n,'forces':[(x['name'],x.get('force'),x.get('ratio'),x.get('bytes')) for x in map(json.loads,open(rf))]}))
