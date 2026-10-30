import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__)); import px
def toks(path): return px.mask(px.elf_fn(path,px.KEEP))
o=px.mask(px.orig_window())
def per(path,B=0x800):
    c=toks(path); sm=difflib.SequenceMatcher(None,o,c,autojunk=False); h={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(a,a+n): h[k*8//B]=h.get(k*8//B,0)+1
    return h
a=per(sys.argv[1]); b=per(sys.argv[2])
tot=0
for k in sorted(set(a)|set(b)):
    d=b.get(k,0)-a.get(k,0); tot+=d
    if d: print('0x%05x %+d'%(0x22a10+k*0x800,d))
print('total',tot)
