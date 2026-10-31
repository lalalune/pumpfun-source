#!/usr/bin/env python3
"""irscan.py <base.ll> <out.jsonl> [prefix moves...]: try every single move X>Y over validate blocks (after prefix moves); 4 workers."""
import sys,os,re,subprocess,json
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
base,out=sys.argv[1],sys.argv[2]; pre=sys.argv[3:]
L=open(base).read().split('\n')
names=[]
for l in L:
    m=re.match(r'^("?[^":]+"?):',l)
    if m:
        s=m.group(1).strip('"'); s=s.split('E.')[-1] if 'to_string' in s else s; names.append(s)
a=names.index('bb6.i'); b=names.index('bb71.i'); V=names[a:b+1]
moves=[(x,y) for x in V for y in V if x!=y and x!='bb6.i']
def run(mv):
    x,y=mv; n=f'sc_{abs(hash((x,y)))%10**9}'
    r=subprocess.run(['python3',T+'/irmv.py',base,n,*pre,f'{x}>{y}'],capture_output=True,text=True)
    for f in (f'{T}/../tmp/p/{n}.ll',f'{T}/../tmp/p/{n}.s',f'{T}/../tmp/p/{n}.o'):
        try: os.remove(f)
        except: pass
    try: d=json.loads(r.stdout.split('\n')[0].split(' ',1)[1]); return {'mv':f'{x}>{y}','M':d['M'],'jM':d['jM'],'bytes':d['bytes'],'ratio':d['ratio']}
    except Exception: return {'mv':f'{x}>{y}','err':r.stderr[-200:]}
if __name__=='__main__':
    with Pool(4) as p, open(out,'w') as f:
        for r in p.imap_unordered(run,moves): f.write(json.dumps(r)+'\n'); f.flush()
