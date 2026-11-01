#!/usr/bin/env python3
"""mv.py <name> <moves> [--base m.ll] [--w spec]: post-opt IR block moves in execute: moves = 'A>B;C>D' moves block A (with its
following blocks up to the next listed? no: single block) to just after block B. Then px weights (--w) and llc."""
import sys,os,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
def blocks(t):
    L=t.split('\n')
    st=[i for i,l in enumerate(L) if l.startswith('define ') and re.search(oracle.KEEP,l)][0]
    en=st+[i for i,l in enumerate(L[st:]) if l=='}'][0]
    starts=[i for i in range(st+1,en) if re.match(r'^("[^"]+"|[\w.$-]+):',L[i])]
    return L,st,en,starts
def name_of(l): return re.match(r'^("[^"]+"|[\w.$-]+):',l).group(1).strip('"')
def denum(t):
    L,st,en,S=blocks(t)
    for i in range(st,en+1):
        L[i]=re.sub(r'%(\d+)\b',r'%n\1',L[i])
    return '\n'.join(L)
def move(t,moves):
    t=denum(t)
    for mv in [m for m in moves.split(';') if m]:
        a,b=mv.split('>')
        L,st,en,S=blocks(t)
        B=[(s,(S[k+1] if k+1<len(S) else en)) for k,s in enumerate(S)]
        names=[name_of(L[s]) for s,_ in B]
        ia=names.index(a); ib=names.index(b)
        sa,ea=B[ia]; blk=L[sa:ea]
        rest=L[:sa]+L[ea:]
        # recompute insertion point
        sb,eb=B[ib]
        if sb>sa: sb-=len(blk); eb-=len(blk)
        L2=rest[:eb]+blk+rest[eb:]
        t='\n'.join(L2)
    return t
if __name__=='__main__':
    a=sys.argv[1:]; name=a[0]; moves=a[1]; base=OUT+'/fx/m0/m.ll'; w=''
    if '--base' in a: base=a[a.index('--base')+1]
    if '--w' in a: w=a[a.index('--w')+1]
    t=move(open(base).read(),moves)
    d=OUT+'/px'; os.makedirs(d,exist_ok=True); p=d+'/mv_'+name+'.ll'; open(p,'w').write(t)
    r=px.run(name,w,p); os.remove(p); r['moves']=moves; print(json.dumps(r))
