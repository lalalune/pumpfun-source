#!/usr/bin/env python3
"""canon.py <mn.ll> <out.jsonl>: IR oracle for the original's canonical per-clone windows on the literal clones:
for each literal base X, move X's key load to the top of X's lamports block and X's owner/rent/flag loads to the top of
the block after X's data clone (derived AccountInfo::clone order), singly per literal and all together. Also extra
pairs given as names on argv[3:] (unit@blk{top,bot} like cbmv)."""
import sys,os,re,json,itertools
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import px2
sys.argv=[sys.argv[0],sys.argv[1],'/dev/null','0','1']+sys.argv[3:] if False else sys.argv
mn,outp=sys.argv[1],sys.argv[2]; extra=sys.argv[3:]
g={'__file__':T+'/cbmv.py'}; sv=sys.argv; sys.argv=['cbmv',mn,'/dev/null','0','1']
exec(compile(open(T+'/cbmv.py').read().split("if __name__=='__main__':")[0],'cbmv','exec'),g); sys.argv=sv
L=g['L']; blocks=g['blocks']; units=g['units']
def blk(i): return next(k for k,(a,b) in enumerate(blocks) if a<=i<=b)
def rcblock(base,off):
    for i in range(blocks[0][0],blocks[-1][1]+1):
        if re.match(r'  %[\w.]+ = getelementptr inbounds i8, ptr '+re.escape(base)+r', i64 '+str(off)+r'$',L[i]): return blk(i)
ORD=os.environ.get('CORD','')
def apply(moves):
    M=list(L); ins={}
    if ORD: moves=sorted(moves,key=lambda m:(m[1],(1 if ORD=='rev' else -1)*-fieldoff(m[0])))
    for lines,pos in moves:
        for k in lines: ins.setdefault(pos,[]).append(M[k]); M[k]=None
    out=[]
    for i,x in enumerate(M):
        if i in ins: out+=ins[i]
        if x is not None: out.append(x)
    return '\n'.join(out)
def fieldoff(lines):
    m=re.search(r'i64 (\d+)$',L[lines[0]]) if len(lines)==2 else None
    return int(m.group(1)) if m else 0
plans={}
for base in sorted({u[1] for u in units}-{'%_439','%_473'}):
    lb=rcblock(base,8); db=rcblock(base,16)
    if lb is None or db is None: continue
    mv=[]
    for lines,b,bi,v in units:
        if b!=base: continue
        off=fieldoff(lines)
        if off==0: tgt=max(blocks[lb][0]+1,g['defline'](base)+1)
        else: tgt=blocks[db+1][0]+1
        if bi==blk(tgt) and abs(lines[0]-tgt)<3: continue
        mv.append((lines,tgt))
    plans['canon_'+base.strip('%')]=mv
plans['canon_all']=[m for k,v in list(plans.items()) for m in v]
def parse(n):
    v,rest=n.split('@'); bj=int(re.match(r'\d+',rest).group()); pos=rest[len(str(bj)):]
    u=next(u for u in units if u[3]==v); a,b=blocks[bj]
    return (u[0], a+1 if pos=='top' else b)
if extra: plans['extra_'+'+'.join(extra)]=[parse(n) for n in extra]
d=os.path.join(os.path.dirname(os.path.abspath(outp)),'cbtmp'); os.makedirs(d,exist_ok=True)
with open(outp,'a') as o:
    for k,mv in plans.items():
        fn=f'{d}/canon.ll'; open(fn,'w').write(apply(mv)); r=px2.run(fn); r['name']=k; r['n']=len(mv)
        ch=r.pop('ch',None); print(json.dumps(r)); o.write(json.dumps(r)+'\n')
