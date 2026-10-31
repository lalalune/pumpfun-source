import sys,runpy
sys.argv=['webs.py',sys.argv[1],'--min-span','0x1000000']
g=runpy.run_path(''+__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'webs.py')+'')
S=g['S'];L=g['L']
sys.setrecursionlimit(100000)
idx=0;st=[];on=set();ix={};lo={};res=[]
def sc(v):
    global idx
    ix[v]=lo[v]=idx;idx+=1;st.append(v);on.add(v)
    for w in S[v]:
        if w not in ix: sc(w);lo[v]=min(lo[v],lo[w])
        elif w in on: lo[v]=min(lo[v],ix[w])
    if lo[v]==ix[v]:
        c=[]
        while True:
            w=st.pop();on.discard(w);c.append(w)
            if w==v:break
        if len(c)>1: res.append(c)
for v in range(len(L)):
    if v not in ix: sc(v)
for c in res: print(len(c),hex(L[min(c)][0]),hex(L[max(c)][0]))
