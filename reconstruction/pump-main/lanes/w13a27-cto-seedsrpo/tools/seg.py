import sys,os,difflib,struct
sys.path.insert(0,os.path.dirname(__file__)); import oracle
def toks(raw,mr=False,mf=False):
    out=[]
    for t in oracle.mask(raw):
        b=bytearray(t); op=b[0]; cls=op&7
        if mr and op!=0x85: b[1]=0
        if mf:
            if op&7 in (1,2,3) : b[2:4]=b'\0\0'
            if op in (0x07,) : b[4:8]=b'\0'*4
            if cls==5 and op not in (0x85,0x95): b[2:4]=b'\0\0'
        out.append(bytes(b))
    return out
o=oracle.orig_window(); c=open(sys.argv[1],'rb').read(); W=int(sys.argv[2],16) if len(sys.argv)>2 else 0x800
res={}
for name,(mr,mf) in {'plain':(0,0),'regs':(1,0),'frame':(0,1),'both':(1,1)}.items():
    a=toks(o,mr,mf); b=toks(c,mr,mf)
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    # per-orig-offset bins
    off=[];p=0
    for t in a: off.append(p); p+=len(t)
    bins={}
    for blk in sm.get_matching_blocks():
        for k in range(blk.a,blk.a+blk.size): bins[off[k]//W]=bins.get(off[k]//W,0)+1
    res[name]=bins
tot={}
p=0
for t in toks(o): tot[p//W]=tot.get(p//W,0)+1; p+=len(t)
print('bin   tot plain regs frame both')
for k in sorted(tot): print(f'{k*W:#6x} {tot[k]:4} '+' '.join(f'{res[n].get(k,0):5}' for n in res))
print('sum', sum(tot.values()), ' '.join(str(sum(res[n].values())) for n in res))
