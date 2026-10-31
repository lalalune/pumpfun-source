#!/usr/bin/env python3
"""irgreedy.py <m.ll(renumbered)> <out.jsonl> <first> <last> [seedspec...]: experiment-only IR block-ORDER scan of the
validate region of admin_cto execute (blocks first..last in current IR order). Units: single blocks, to_string error
groups (ts+unreachable+exit), ts pairs. Positions: before every block of the region that follows a conditional-br
block, plus before <last>'s successor. Each variant = one unit moved; scored with px.py. Seeds (unit@before) are
applied first. IR block order is semantics-free; on BPF it decides ISel fallthroughs and MBP glue."""
import sys,re,json,os,subprocess,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src,outf,first,last=sys.argv[1:5]; seeds=sys.argv[5:]
def load(text):
    L=text.split('\n')
    fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
    fe=fs+[k for k,l in enumerate(L[fs:]) if l=='}'][0]
    st=[i for i in range(fs+1,fe) if re.match(r'^("[^"]+"|[\w.$-]+):',L[i])]
    bl=[]
    for k,i in enumerate(st):
        e=st[k+1] if k+1<len(st) else fe
        n=re.match(r'^("[^"]+"|[\w.$-]+):',L[i]).group(1).strip('"')
        bl.append([n,L[i:e]])
    return L[:st[0]],bl,L[fe:]
def short(n): return n.split('E.')[-1] if 'to_string' in n else n
def move(bl,unit,before):
    names=[b[0] for b in bl]
    u=[b for b in bl if short(b[0]) in unit]; assert len(u)==len(unit),(unit,)
    rest=[b for b in bl if short(b[0]) not in unit]
    k=[i for i,b in enumerate(rest) if short(b[0])==before][0]
    return rest[:k]+u+rest[k:]
def dump(h,bl,t): return '\n'.join(h+[l for b in bl for l in b[1]]+t)
H,BL,TL=load(open(src).read())
for s in seeds:
    u,b=s.split('@'); BL=move(BL,u.split('+'),b)
names=[short(b[0]) for b in BL]
a,z=names.index(first),names.index(last)
reg=BL[a:z+1]
def term(b): 
    t=[l.strip() for l in b[1] if l.strip().startswith(('br ','switch','unreachable','ret'))]; return t[-1] if t else ''
units=[]
for i,b in enumerate(reg):
    n=short(b[0]); units.append([n])
    if n.startswith('bb3.i') and i>0 and i+1<len(reg):
        p=short(reg[i-1][0]); x=short(reg[i+1][0])
        units.append([p,n,x]); units.append([p,n]); 
pos=[short(reg[i+1][0]) for i,b in enumerate(reg[:-1]) if term(b).startswith('br i1')]+[names[z+1]]
pos=sorted(set(pos),key=names.index)
jobs=[(u,p) for u in units for p in pos if p not in u]
def run(j):
    u,p=j
    try: bl=move(BL,u,p)
    except Exception as e: return {'u':u,'p':p,'err':str(e)}
    if [b[0] for b in bl]==[b[0] for b in BL]: return None
    with tempfile.TemporaryDirectory() as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL))
        r=subprocess.run([sys.executable,T+'/px.py',f],capture_output=True,text=True)
        try: return {'u':'+'.join(u),'p':p,**json.loads(r.stdout.strip().split('\n')[-1])}
        except Exception: return {'u':u,'p':p,'err':r.stdout[-200:]}
if __name__=='__main__':
    if os.environ.get('DUMP'):
        open(os.environ['DUMP'],'w').write(dump(H,BL,TL)); sys.exit()
    print(len(units),'units',len(pos),'pos',len(jobs),'jobs',flush=True)
    with Pool(int(os.environ.get('NP','6'))) as P, open(outf,'w') as f:
        for r in P.imap_unordered(run,jobs):
            if r: f.write(json.dumps(r)+'\n'); f.flush()
