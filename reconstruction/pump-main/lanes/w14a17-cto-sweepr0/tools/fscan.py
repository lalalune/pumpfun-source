#!/usr/bin/env python3
"""fscan.py <m.ll> <clone> <out.jsonl> [threads]: llc oracle over placements of the scalar field reads (key, owner, rent, signer,
writable, executable) of one hand-written AccountInfo clone into P0 (before lamports Rc), P1 (between Rc clones), P2 (after both).
clone: 'first' (TCF CpiContext pump_amm, from %364) . Order inside a position is canonical (key,owner,rent,40,41,42)."""
import sys,os,re,subprocess,json,itertools,tempfile
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
ORIG=g['orig_window']()
mll,clone,out=sys.argv[1:4]; NT=int(sys.argv[4]) if len(sys.argv)>4 else 4
L=open(mll).read().split('\n')
# locate the clone: x = load ptr from GEP base 'XGEP'
XGEP=os.environ.get('XGEP','%364')
xi=[i for i,l in enumerate(L) if re.match(r'  %(\S+) = load ptr, ptr '+re.escape(XGEP)+r', ',l)]
xi=(xi[0] if clone=='first' else xi[-1]) if xi else 0
X=re.match(r'  (%\S+) = ',L[xi]).group(1)
if os.environ.get('XVAL'):
    X=os.environ['XVAL']; xi=next(i for i,l in enumerate(L) if l.startswith('  '+X+' = '))
def find(pat,start):
    for i in range(start,start+120):
        if re.match(pat,L[i]): return i
gl={o:find(r'  (%\S+) = getelementptr inbounds i8, ptr '+re.escape(X)+r', i64 '+str(o)+'$',xi) for o in (8,16,24,32,40,41,42)}
keyi=find(r'  %\S+ = load ptr, ptr '+re.escape(X)+r', align 8',xi)
fields={'key':[keyi]}
for nm,o in (('owner',24),('rent',32),('f40',40),('f41',41),('f42',42)):
    fields[nm]=[gl[o],gl[o]+1]
# B2 label: first label after data gep
br=next(i for i in range(gl[16],gl[16]+40) if L[i].startswith('  br i1'))
tgt=re.findall(r'label (%\S+)',L[br])[1].lstrip('%')
b2=next(i for i in range(br,br+40) if L[i].startswith(tgt+':') or L[i].startswith('"'+tgt.strip('"')+'":') or L[i].split(':')[0].strip('"')==tgt.strip('"'))
anch={'P0':gl[8],'P1':gl[16],'P2':b2+1}
cur={nm:min(['P0','P1','P2'],key=lambda p:abs(anch[p]-v[0]) if anch[p]<=v[0] else 1e9) for nm,v in fields.items()}
order=['key','owner','rent','f40','f41','f42']
def build(assign):
    rm=set(i for v in fields.values() for i in v); ins={}
    for nm in order: ins.setdefault(anch[assign[nm]],[]).extend(L[i] for i in fields[nm])
    res=[]
    for i,l in enumerate(L):
        if i in ins: res.extend(ins[i])
        if i in rm: continue
        res.append(l)
    return '\n'.join(res)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def run(assign):
    lab=''.join(assign[n][1] for n in order)
    d=tempfile.mkdtemp(dir=os.path.dirname(out)); p=d+'/m.ll'; open(p,'w').write(build(assign))
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'lab':lab,'err':r.stderr[-200:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG); subprocess.run(['rm','-rf',d])
    return {'lab':lab,'ratio':round(rr,5),'bytes':len(c),'slots':sd}
print('current',''.join(cur[n][1] for n in order),file=sys.stderr)
alls=[dict(zip(order,c)) for c in itertools.product(['P0','P1','P2'],repeat=6)]
with ThreadPoolExecutor(NT) as ex, open(out,'w') as f:
    for r in ex.map(run,alls): f.write(json.dumps(r)+'\n'); f.flush()
