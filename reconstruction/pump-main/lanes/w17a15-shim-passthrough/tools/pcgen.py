#!/usr/bin/env python3
"""pcgen.py <slim.ll> <edits.jsonl>: passthrough on CONSTANT values stored into local allocas (phi-of-constants
incoming values after SROA), e.g. `store i8 0, ptr %do_coin` -> `%pcvN = pt8(N, 0); store i8 %pcvN`. Source form:
pt1(N,false) / pt64(N,0) as the arm value."""
import sys,re,json
sys.path.insert(0,__import__('os').path.dirname(__file__)); from ptgen import ranges,decl,mang
VAL=r'(%[\w.$-]+|%"[^"]+")'
def main(src,dst):
    L=open(src).read().split('\n'); R=ranges(L); E=[]; seq=5000
    for fn,(a,b) in R.items():
        allocas=set(); gbase={}
        for i in range(a,b):
            m=re.match(r'^\s+'+VAL+r' = alloca ',L[i])
            if m: allocas.add(m.group(1))
            m=re.match(r'^\s+'+VAL+r' = getelementptr [^,]+, ptr '+VAL,L[i])
            if m: gbase[m.group(1)]=gbase.get(m.group(2),m.group(2))
        for i in range(a+1,b):
            m=re.match(r'^(\s+)store (i1|i8|i64) (-?\d+|true|false), ptr '+VAL+r'(.*)$',L[i])
            if not m: continue
            p=m.group(4)
            if gbase.get(p,p) not in allocas: continue
            t=m.group(2); c=m.group(3); seq+=1; nv='%%pcv%d'%seq
            rep={i:['  %s = call %s @llvm.bpf.passthrough.%s.%s(i32 %d, %s %s)'%(nv,t,mang(t),mang(t),seq,t,c), m.group(1)+'store %s %s, ptr %s%s'%(t,nv,p,m.group(5))]}
            E.append({'id':'pc:%s:%d'%(fn,i),'kind':'pc','cls':t,'fn':fn,'rep':rep,'extra':[decl(t)],'src':L[i].strip()[:120]})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    import collections; print(len(E),collections.Counter(e['fn'] for e in E))
if __name__=='__main__': main(*sys.argv[1:])
