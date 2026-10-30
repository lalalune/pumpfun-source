import os,re
# MODE=startfirst: move quote_fee's lifetime.start to body entry; MODE=noend: delete its lifetime.ends; MODE=nostart: delete start only
def edit(t):
    L=t.split('\n'); X=os.environ['X']; M=os.environ['MODE']
    s=next(i for i,l in enumerate(L) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
    e=next(i for i in range(s,len(L)) if L[i]=='}')
    ps=re.compile(r'call void @llvm\.lifetime\.start\.p0\(i64 \d+, ptr %'+re.escape(X)+r'\)')
    pe=re.compile(r'call void @llvm\.lifetime\.end\.p0\(i64 \d+, ptr %'+re.escape(X)+r'\)')
    body=L[s+1:e]
    if M=='noend': body=[l for l in body if not pe.search(l)]
    elif M=='nostart': body=[l for l in body if not ps.search(l)]
    elif M=='startfirst':
        st=[l for l in body if ps.search(l)]; body=[l for l in body if not ps.search(l)]
        k=next(i for i,l in enumerate(body) if 'alloca' not in l and l.strip())
        body=body[:k]+st[:1]+body[k:]
    return '\n'.join(L[:s+1]+body+L[e:])
