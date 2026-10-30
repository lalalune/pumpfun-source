import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import ir
t=ir.getslim(ir.L+'/ir/b2297/pump_recovered.ll')
i=t.index('\nbb112:'); j=t.index('\n',i+1)+1; k=j; L=[]
while ' = phi ' in t[k:t.index('\n',k)]:
    e=t.index('\n',k)+1; L.append(t[k:e]); k=e
for p in sys.argv[1:]:
    p=tuple(int(c) for c in p)
    print(p, ir.run_text('p1',t[:j]+''.join(L[x] for x in p)+t[k:])[0])
