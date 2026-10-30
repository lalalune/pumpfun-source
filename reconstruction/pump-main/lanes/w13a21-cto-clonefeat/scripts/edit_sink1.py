import re,os
NAMES=os.environ.get('SINK','_5.i229').split(',')
def edit(f):
    L=f.split('\n')
    for n in NAMES:
        k=[i for i,l in enumerate(L) if re.match(r'  %'+re.escape(n)+r' = ',l)][0]
        pat=re.compile(r'%'+re.escape(n)+r'(?![\w.$-])')
        u=[i for i,l in enumerate(L) if i!=k and pat.search(l)][0]
        b=u
        while not re.match(r'^\S.*:',L[b]): b-=1
        d=b+1
        while re.match(r'  %\S+ = phi ',L[d]): d+=1
        line=L.pop(k)
        if k<d: d-=1
        L.insert(d,line)
    s='\n'.join(L)
    order=[m.group(1) for m in re.finditer(r'^  %(\d+) = ',s,re.M)]
    nums=sorted(order,key=int); mp=dict(zip(order,nums))
    s=re.sub(r'%(\d+)(?![\w.$-])',lambda m:'%__'+mp[m.group(1)] if m.group(1) in mp else m.group(0),s)
    return s.replace('%__','%')
