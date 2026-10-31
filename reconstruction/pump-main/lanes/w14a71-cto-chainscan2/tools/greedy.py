#!/usr/bin/env python3
"""greedy.py <m.s> <out.json> --chains L1,L2,.. [--steps 3] [-j 4] [--exclude L,..] [--seed LAB:BEFORE,..]: greedy multi-move placement-only pass.
Uses blkscan.py's chain split (fallthrough chains ending in ja/exit). At each step, every listed chain is tried at every
legal insertion point on the CURRENT order; the best strictly-improving move is applied. Registers/frame are fixed, so the
result bounds what moving only those chains (jointly) is worth. Also writes the final asm next to out.json."""
import sys,os,re,json,subprocess,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIG=G['orig_window']()
a=sys.argv[1:]; S=a.pop(0); OUTF=a.pop(0); J=4; CH=[]; STEPS=3; EXC=[]; SEED=[]
while a:
    x=a.pop(0)
    if x=='-j': J=int(a.pop(0))
    elif x=='--chains': CH=a.pop(0).split(',')
    elif x=='--steps': STEPS=int(a.pop(0))
    elif x=='--exclude': EXC=a.pop(0).split(',')
    elif x=='--seed': SEED=a.pop(0).split(',')
L=open(S).read().split('\n')
fs=[k for k,l in enumerate(L) if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l)][0]
fe=[k for k,l in enumerate(L) if l.startswith('.Lfunc_end0')][0]
def isstart(l): return re.match(r'^(LBB0_\d+:|# %bb\.\d+:)',l) is not None
starts=[k for k in range(fs+1,fe) if isstart(L[k])]
blocks=list(zip(starts,starts[1:]+[fe]))
def last(b):
    xs=[l.strip() for l in L[b[0]+1:b[1]] if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('.')]
    return xs[-1] if xs else ''
def name(b): return L[b[0]].split(':')[0].replace('# ','')
term=[last(b).startswith('ja ') or last(b)=='exit' for b in blocks]
nb=[]; cur=None
for i,b in enumerate(blocks):
    cur=b if cur is None else (cur[0],b[1])
    if term[i]: nb.append(cur); cur=None
if cur: nb.append(cur)
blocks=nb; term=[last(b).startswith('ja ') or last(b)=='exit' for b in blocks]
names=[name(b) for b in blocks]
pre=L[:blocks[0][0]]; post=L[fe:]
def assemble(order):
    body=[]
    for i in order: body+=L[blocks[i][0]:blocks[i][1]]
    return '\n'.join(pre+body+post)
def score(text):
    with tempfile.TemporaryDirectory() as d:
        s=d+'/a.s'; o=d+'/a.o'; open(s,'w').write(text)
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',s,'-o',o],capture_output=True,text=True)
        if r.returncode: return None
        c=G['elf_fn'](o,G['KEEP']); rr,sd=G['metric'](c,ORIG); return (round(rr,5),len(c),sd)
def cands(order,i):
    rest=[k for k in order if k!=i]; pos=order.index(i); out=[]
    for p in range(1,len(rest)+1):
        if p<len(rest) and not names[rest[p]].startswith('LBB'): continue
        if not term[rest[p-1]]: continue
        o2=rest[:p]+[i]+rest[p:]
        if o2==order: continue
        out.append((o2,names[rest[p]] if p<len(rest) else 'END'))
    return out
def job(arg):
    order,i=arg; best=None
    for o2,bef in cands(order,i):
        r=score(assemble(o2))
        if r and (best is None or r[0]>best[0][0] or (r[0]==best[0][0] and r[2]<best[0][2])): best=(r,bef,o2)
    return (names[i],best)
if __name__=='__main__':
    order=list(range(len(blocks))); base=score(assemble(order)); hist=[{'step':0,'score':base}]
    for mv in SEED:
        lab,bef=mv.split(':'); i=names.index(lab); o=[k for k in order if k!=i]
        p=len(o) if bef=='END' else o.index(names.index(bef)); order=o[:p]+[i]+o[p:]
        hist.append({'seed':mv,'score':score(assemble(order))})
    print(json.dumps({'seeded':hist}),flush=True)
    idx=[names.index(c) for c in CH if c in names and c not in EXC]
    print(json.dumps({'base':base,'chains':[names[i] for i in idx]}),flush=True)
    cur=hist[-1]['score']
    with Pool(J) as P:
        for st in range(1,STEPS+1):
            res=P.map(job,[(order,i) for i in idx])
            res=[r for r in res if r[1]]
            res.sort(key=lambda r:(-r[1][0][0],r[1][0][2]))
            top=[(n,b[0],b[1]) for n,b in res[:5]]
            print(json.dumps({'step':st,'top':top}),flush=True)
            if not res or res[0][1][0][0]<=cur[0]: break
            n,(r,bef,o2)=res[0]; order=o2; cur=r
            hist.append({'step':st,'move':n,'before':bef,'score':r,'top':top})
    json.dump({'base':base,'hist':hist,'order':[names[i] for i in order]},open(OUTF,'w'),indent=1)
    open(OUTF[:-5]+'.s','w').write(assemble(order))
