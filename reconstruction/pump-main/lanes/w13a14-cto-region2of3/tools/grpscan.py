"""grpscan.py <mod.ll> <outjsonl> <lo> <hi> [jobs]: move every alloca with list index in [lo,hi] to every other position in [lo,hi]
(llc oracle, ratio + region-2 matched tokens). Experiment only."""
import sys,os,json,subprocess,re,difflib,collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
mod=open(sys.argv[1]).read(); out=sys.argv[2]; lo,hi=int(sys.argv[3]),int(sys.argv[4]); J=int(sys.argv[5]) if len(sys.argv)>5 else 3
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); fn=mod[i:j]
lines=fn.split('\n'); al=[k for k,l in enumerate(lines) if ' = alloca ' in l]
names=[re.match(r'\s*(%[\w.$"]+) = alloca',lines[k]).group(1) for k in al]
otok,w=co.orig_tokens(); off=[];o=0
for t in otok: off.append(o); o+=len(t)
def r2(ctok):
    sm=difflib.SequenceMatcher(None,otok,ctok,autojunk=False); n=0
    for a,b,sz in sm.get_matching_blocks():
        n+=sum(1 for k in range(sz) if 0x23b0<=off[a+k]<0x4760)
    return n
def job(a,b):
    L=lines[:]; src=al[a]; dst=al[b]; x=L.pop(src)
    # after removal, indices > src shift by -1
    d=dst if dst<src else dst
    L.insert(d,x)
    fn2='\n'.join(L); d2=f'{out}.d/{a}_{b}'; os.makedirs(d2,exist_ok=True)
    open(f'{d2}/m.ll','w').write(mod[:i]+fn2+mod[j:])
    r=subprocess.run(co.LLC+[f'{d2}/m.ll','-filetype=obj','-o',f'{d2}/m.o'],capture_output=True)
    if r.returncode: return dict(a=a,b=b,err=1)
    ctok,raw,_=co.obj_tokens(f'{d2}/m.o',sym); m=co.metrics(otok,ctok,len(raw),w['bytes'])
    m.update(a=a,b=b,mv=names[a],to=names[b],r2=r2(ctok)); 
    for f in ('m.ll','m.o'): os.unlink(f'{d2}/{f}')
    os.rmdir(d2); return m
pairs=[(a,b) for a in range(lo,hi+1) for b in range(lo,hi+1) if b not in (a,a+1)]
with ThreadPoolExecutor(J) as ex, open(out,'w') as fo:
    for m in ex.map(lambda p: job(*p), pairs):
        fo.write(json.dumps(m)+'\n'); fo.flush()
