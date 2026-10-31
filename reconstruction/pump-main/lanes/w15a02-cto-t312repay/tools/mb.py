import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
o=oracle.mask(oracle.orig_window())
def offs(t):
    r=[];p=0
    for x in t: r.append(p); p+=len(x)
    return r
oo=offs(o)
for p in sys.argv[1:]:
    q=p if '.' in p else f'{os.path.dirname(T)}/rx/{p}/fn.bin'
    c=oracle.mask(xled.load(q)); co=offs(c)
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    lo=int(os.environ.get('LO','0'),16); hi=int(os.environ.get('HI','2000'),16)
    print(p)
    for m in sm.get_matching_blocks():
        if m.size and lo<=oo[m.a]<hi: print('  orig %05x  cand %05x  n=%d  shift=%+d'%(oo[m.a],co[m.b],m.size,co[m.b]-oo[m.a]))
