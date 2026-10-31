#!/usr/bin/env python3
"""fscan.py <m.ll> <out.jsonl> [maxblocks] : IR fallthrough-flip scan (experiment only). For each conditional
`br i1` block X (first maxblocks blocks of execute), move the successor that is NOT the next IR block to right
after X (single block, named blocks only) and score with px.py. Bounds what flipping one conditional-branch
fallthrough via IR block order is worth (BPF keeps ISel fallthrough)."""
import sys,re,subprocess,json,os,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src,outf=sys.argv[1:3]; MAXB=int(sys.argv[3]) if len(sys.argv)>3 else 120
L=open(src).read().split('\n')
def lab(l):
    m=re.match(r'^("[^"]+"|[\w.$-]+):',l); return m.group(1).strip('"') if m else None
fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
fe=fs+[k for k,l in enumerate(L[fs:]) if l=='}'][0]
st=[i for i in range(fs+1,fe) if lab(L[i])]
names=[lab(L[i]) for i in st]
jobs=[]
for bi,i in enumerate(st[:MAXB]):
    e=st[bi+1] if bi+1<len(st) else fe
    br=[l for l in L[i:e] if l.strip().startswith('br i1')]
    if not br: continue
    m=re.findall(r'label %("[^"]+"|[\w.$-]+)',br[0]); m=[x.strip('"') for x in m]
    nxt=names[bi+1] if bi+1<len(names) else None
    for s in m:
        if s!=nxt and not re.match(r'^\d+$',s) and s in names: jobs.append((names[bi],s))
def run(j):
    x,s=j
    with tempfile.TemporaryDirectory() as d:
        t=d+'/t.ll'
        nxt=names[names.index(x)+1]
        r=subprocess.run([sys.executable,T+'/irorder.py',src,t,s,nxt],capture_output=True,text=True)
        if r.returncode: return {'x':x,'s':s,'err':r.stderr[-200:]}
        r=subprocess.run([sys.executable,T+'/px.py',t],capture_output=True,text=True)
        try: return {'x':x,'s':s,**json.loads(r.stdout.strip().split('\n')[-1])}
        except Exception: return {'x':x,'s':s,'err':r.stdout[-200:]}
if __name__=='__main__':
    print(len(jobs),'jobs',flush=True)
    with Pool(int(os.environ.get('NP','4'))) as P, open(outf,'w') as f:
        for r in P.imap_unordered(run,jobs): f.write(json.dumps(r)+'\n'); f.flush()
