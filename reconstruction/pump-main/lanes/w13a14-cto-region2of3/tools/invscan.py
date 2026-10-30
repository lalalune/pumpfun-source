"""invscan.py <mod.ll> <out.jsonl> [jobs]: invert every conditional br in execute (xor cond + swap successors, swap !prof),
llc oracle, record ratio/bytes/region-2 matched tokens + sret-slot rank vector. Experiment only."""
import sys,os,json,subprocess,re,difflib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
mod=open(sys.argv[1]).read(); out=sys.argv[2]; J=int(sys.argv[3]) if len(sys.argv)>3 else 3
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); fn=mod[i:j]
lines=fn.split('\n')
BR=re.compile(r'^(\s*)br i1 (%[\w.$"]+), label (%[\w.$"]+), label (%[\w.$"]+)(.*)$')
idx=[k for k,l in enumerate(lines) if BR.match(l)]
otok,w=co.orig_tokens(); off=[];o=0
for t in otok: off.append(o); o+=len(t)
def r2(ctok):
    sm=difflib.SequenceMatcher(None,otok,ctok,autojunk=False); n=0
    for a,b,sz in sm.get_matching_blocks():
        n+=sum(1 for k in range(sz) if 0x23b0<=off[a+k]<0x4760)
    return n
PROF={}
for m in re.finditer(r'^(!\d+) = !\{!"branch_weights",(?: !"expected",)? i32 (\d+), i32 (\d+)\}$',mod,re.M): PROF[m.group(1)]=(m.group(2),m.group(3))
def job(k):
    L=lines[:]; m=BR.match(L[k]); ind,c,a,b,rest=m.groups()
    extra=''
    pm=re.search(r'!prof (!\d+)',rest)
    newmod_tail=''
    if pm and pm.group(1) in PROF:
        x,y=PROF[pm.group(1)]; nid=f'!9{k:06d}'; rest=rest.replace(pm.group(1),nid); newmod_tail=f'\n{nid} = !{{!"branch_weights", i32 {y}, i32 {x}}}\n'
    L[k]=f'{ind}%inv{k} = xor i1 {c}, true\n{ind}br i1 %inv{k}, label {b}, label {a}{rest}'
    d2=f'{out}.d/{k}'; os.makedirs(d2,exist_ok=True)
    open(f'{d2}/m.ll','w').write(mod[:i]+'\n'.join(L)+mod[j:]+newmod_tail)
    r=subprocess.run(co.LLC+[f'{d2}/m.ll','-filetype=obj','-o',f'{d2}/m.o'],capture_output=True,text=True)
    res=dict(k=k,line=lines[k].strip()[:120])
    if r.returncode: res['err']=r.stderr[-300:]
    else:
        ctok,raw,_=co.obj_tokens(f'{d2}/m.o',sym); res.update(co.metrics(otok,ctok,len(raw),w['bytes'])); res['r2']=r2(ctok)
    for f in ('m.ll','m.o'):
        try: os.unlink(f'{d2}/{f}')
        except FileNotFoundError: pass
    os.rmdir(d2); return res
with ThreadPoolExecutor(J) as ex, open(out,'w') as fo:
    for m in ex.map(job, idx):
        fo.write(json.dumps(m)+'\n'); fo.flush()
