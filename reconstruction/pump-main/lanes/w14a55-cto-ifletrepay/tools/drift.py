import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window())
def offs(t):
    r=[];a=0
    for x in t: r.append(a); a+=len(x)
    return r
oo=offs(o)
for p in sys.argv[1:]:
    c=mask(open(p,'rb').read()); co=offs(c)
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    print('##',p)
    last=None
    for b in sm.get_matching_blocks():
        if b.size<3: continue
        d=co[b.b]-oo[b.a]
        if oo[b.a]>=0x3a00 and oo[b.a]<=0x5200 and d!=last: print(hex(oo[b.a]),hex(co[b.b]),d,b.size); last=d
