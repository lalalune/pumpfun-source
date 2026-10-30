import os,re
def edit(t):
    L=t.split('\n'); X=os.environ['X'].split(',')
    s=next(i for i,l in enumerate(L) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
    e=next(i for i in range(s,len(L)) if L[i]=='}')
    pat=re.compile(r'call void @llvm\.lifetime\.(start|end)\.p0\(i64 \d+, ptr %('+'|'.join(map(re.escape,X))+r')\)')
    body=[l for l in L[s:e] if not pat.search(l)]
    return '\n'.join(L[:s]+body+L[e:])
