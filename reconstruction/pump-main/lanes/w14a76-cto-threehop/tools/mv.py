import sys,difflib
exec(open('amap.py').read().split('o=toks(O)')[0])
o=toks(O); c=toks(open(sys.argv[1],'rb').read()); b=toks(open('rx/base/fn.bin','rb').read())
L=len(o); N=32
a0,a1=int(sys.argv[2])*L//N,int(sys.argv[3])*L//N
for name,x in (('base',b),('cand',c)):
    sm=difflib.SequenceMatcher(None,o[a0:a1],x,autojunk=False)
    bl=[m for m in sm.get_matching_blocks() if m.size>=6]
    print(name,'orig slots',a0,a1,'matched',sum(m.size for m in bl),'cand ranges',[(m.b,m.b+m.size) for m in bl][:6],'...',[(m.b,m.b+m.size) for m in bl][-3:])
print('cand len',len(c),'orig len',L)
