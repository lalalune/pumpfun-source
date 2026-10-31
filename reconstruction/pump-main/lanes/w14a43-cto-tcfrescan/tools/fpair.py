#!/usr/bin/env python3
"""fpair.py <named m.ll> <fsdir> <out.jsonl> [topk] [threads]: pairs of single-clone placements (top-k per clone from fsdir/*.jsonl,
excluding each clone's current placement) applied together, llc oracle."""
import sys,os,re,subprocess,json,itertools,tempfile,glob
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
ORIG=g['orig_window']()
mll,fsd,out=sys.argv[1:4]; K=int(sys.argv[4]) if len(sys.argv)>4 else 3; NT=int(sys.argv[5]) if len(sys.argv)>5 else 4
TXT=open(mll).read()
order=['key','owner','rent','f40','f41','f42']
def apply(t,X,lab):
    L=t.split('\n'); xi=next(i for i,l in enumerate(L) if l.startswith('  '+X+' = '))
    def find(pat,start):
        for i in range(start,start+160):
            if re.match(pat,L[i]): return i
    gl={o:find(r'  (%\S+) = getelementptr inbounds i8, ptr '+re.escape(X)+r', i64 '+str(o)+'$',xi) for o in (8,16,24,32,40,41,42)}
    if gl[16] is None:
        gl[16]=next(i for i in range(gl[8],gl[8]+40) if re.match(r'  %\S+ = getelementptr inbounds i8, ptr %\S+, i64 16$',L[i]))
    keyi=find(r'  %\S+ = load ptr, ptr '+re.escape(X)+r', align 8',xi)
    fields={'key':[keyi]}
    for nm,o in (('owner',24),('rent',32),('f40',40),('f41',41),('f42',42)): fields[nm]=[gl[o],gl[o]+1]
    br=next(i for i in range(gl[16],gl[16]+40) if L[i].startswith('  br i1'))
    tgt=re.findall(r'label (%\S+)',L[br])[1].lstrip('%')
    b2=next(i for i in range(br,br+40) if L[i].split(':')[0].strip('"')==tgt.strip('"'))
    anch={'0':gl[8],'1':gl[16],'2':b2+1}
    rm=set(i for v in fields.values() for i in v); ins={}
    for nm,p in zip(order,lab): ins.setdefault(anch[p],[]).extend(L[i] for i in fields[nm])
    res=[]
    for i,l in enumerate(L):
        if i in ins: res.extend(ins[i])
        if i in rm: continue
        res.append(l)
    return '\n'.join(res)
base=None; cands=[]
for f in sorted(glob.glob(fsd+'/*.jsonl')):
    R=[json.loads(l) for l in open(f)]; R=[r for r in R if 'ratio' in r and r['bytes']==27400]
    if not R: continue
    top=max(r['ratio'] for r in R); base=top if base is None else max(base,top)
    X='%'+os.path.basename(f)[:-6]
    cands.append((f,R))
# recover XVAL names from fs list file order
names=[l.strip() for l in open(sys.argv[6])] if len(sys.argv)>6 else None
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def key(x): return x.replace('%','').replace('.','')
nm2x={key(x):x for x in names}
C=[]
for f,R in cands:
    X=nm2x[os.path.basename(f)[:-6]]
    rs=sorted(R,key=lambda r:-r['ratio'])
    # current placement = the one whose ratio equals main and is first? keep top K excluding any that equal base (current-equivalent)
    sel=[r['lab'] for r in rs if r['ratio']<base][:K]
    C+= [(X,l) for l in sel]
pairs=[(a,b) for a,b in itertools.combinations(C,2) if a[0]!=b[0]]
print('cands',len(C),'pairs',len(pairs),'base',base,file=sys.stderr)
def run(p):
    (xa,la),(xb,lb)=p
    try: t=apply(apply(TXT,xa,la),xb,lb)
    except Exception as e: return {'pair':[xa,la,xb,lb],'err':str(e)[:100]}
    d=tempfile.mkdtemp(dir=os.path.dirname(out)); open(d+'/m.ll','w').write(t)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'pair':[xa,la,xb,lb],'err':r.stderr[-150:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG); subprocess.run(['rm','-rf',d])
    return {'pair':[xa,la,xb,lb],'ratio':round(rr,5),'bytes':len(c)}
with ThreadPoolExecutor(NT) as ex, open(out,'w') as f:
    for r in ex.map(run,pairs): f.write(json.dumps(r)+'\n'); f.flush()
