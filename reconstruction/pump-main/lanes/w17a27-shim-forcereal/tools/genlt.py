#!/usr/bin/env python3
"""genlt.py <m.ll> <cells.jsonl> [--maxn K]: lifetime-marker cells on the post-opt execute body (w17a19 xstart/early ideas):
  ls  an EXTRA lifetime.start of slot X at a later position (after X's START, before X's next use): moves only the DAG chain
  le  an EXTRA lifetime.end of slot X at an earlier block start (between X's last use and its END)
  lE  an EXTRA lifetime.end of X right after each use of X that is followed by no other use in that block (early END)
Experiment only."""
import sys,re,json
a=sys.argv[1:]; m,outp=a[0],a[1]; maxn=int(a[a.index('--maxn')+1]) if '--maxn' in a else 12
L=open(m).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define ') and 'admin_cto7execute' in l][0]; e=s
while L[e]!='}': e+=1
isblk=lambda z: re.match(r'^[\w.$"-]+:',L[z]) is not None
real=lambda z: not re.search(r'llvm\.lifetime\.|getelementptr|^\s*$|^\s*;|= phi ',L[z]) and not isblk(z)
cells=[]
for q in range(s+1,e):
    mm=re.search(r'call void @llvm\.lifetime\.(start|end)\.p0\(i64 (\d+), ptr nonnull (%[\w.$]+)\)',L[q])
    if not mm: continue
    kind,n,p=mm.groups(); pat=re.compile(re.escape(p)+r'(?![\w.$])')
    if kind=='start':
        k=0; last=None
        for z in range(q+1,e):
            if pat.search(L[z]): break
            if re.match(r'^\s+(ret|unreachable)\b',L[z]): break
            if real(z) and z!=last:
                cells.append({'id':f'ls:{q}:{z}:{p}','ops':[['ins',z,L[q]]]}); last=z; k+=1
            if k>=maxn: break
    else:
        k=0
        for z in range(q-1,s,-1):
            if pat.search(L[z]) and 'lifetime' not in L[z]: break
            if isblk(z):
                pos=z+1
                while re.match(r'^\s+%\S+ = phi ',L[pos]): pos+=1
                if pos!=q: cells.append({'id':f'le:{q}:{pos}:{p}','ops':[['ins',pos,L[q]]]}); k+=1
            if k>=maxn: break
with open(outp,'w') as f:
    for c in cells: f.write(json.dumps(c)+'\n')
print(len(cells),'cells',file=sys.stderr)
