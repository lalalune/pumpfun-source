import sys,re
# allclones.py <mn.ll>: every AccountInfo ptr X whose key load and lamports(+8)/data(+16) geps follow within 20 lines
L=open(sys.argv[1]).read().split('\n')
for i,l in enumerate(L):
    m=re.match(r'  (%\S+) = load ptr, ptr (%\S+), align 8',l)
    if not m: continue
    X=m.group(1); w=L[i+1:i+70]
    if any(re.match(r'  %\S+ = load ptr, ptr '+re.escape(X)+', align 8',x) for x in w) and any(re.search(r'ptr '+re.escape(X)+', i64 8$',x) for x in w):
        print(i+1,X)
