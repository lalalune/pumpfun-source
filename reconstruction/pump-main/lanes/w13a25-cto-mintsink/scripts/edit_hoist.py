# HOIST="v1@after1,v2@after2": move the definition of %v right after the definition of %after (same function); renumber
import re,os
SPEC=[x.split('@') for x in os.environ['HOIST'].split(',')]
def edit(f):
    L=f.split('\n')
    for v,after in SPEC:
        k=[i for i,l in enumerate(L) if re.match(r'  %'+re.escape(v)+r' = ',l)][0]
        line=L.pop(k)
        d=[i for i,l in enumerate(L) if re.match(r'  %'+re.escape(after)+r' = ',l)][0]
        L.insert(d+1,line)
    s='\n'.join(L)
    order=[m.group(1) for m in re.finditer(r'^  %(\d+) = ',s,re.M)]
    nums=sorted(order,key=int); mp=dict(zip(order,nums))
    s=re.sub(r'%(\d+)(?![\w.$-])',lambda m:'%__'+mp[m.group(1)] if m.group(1) in mp else m.group(0),s)
    return s.replace('%__','%')
