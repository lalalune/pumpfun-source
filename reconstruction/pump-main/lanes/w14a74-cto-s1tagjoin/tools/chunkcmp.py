import sys,difflib,collections
sys.argv_=sys.argv
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/tools/rx.py').read()
g={'__name__':'x'}; exec(src[:src.index("OUT=os.environ.get")],g)
orig=g['mask'](g['orig_window']())
# orig token byte offsets
off=[];o=0
for t in orig: off.append(o); o+=len(t)
def per(fn):
    c=g['mask'](open(fn,'rb').read())
    sm=difflib.SequenceMatcher(None,orig,c,autojunk=False)
    cnt=collections.Counter()
    for a,b,n in sm.get_matching_blocks():
        for i in range(a,a+n): cnt[off[i]//0x800]+=1
    return cnt,sm.ratio()
fs=sys.argv[1:]
R=[per(f) for f in fs]
print('chunk',*[f.split('/')[-2] for f in fs])
for k in range(0,(o+0x7ff)//0x800):
    print('%05x'%(k*0x800),*[r[0][k] for r in R], R[1][0][k]-R[0][0][k] if len(R)>1 else '')
print('tot',*[sum(r[0].values()) for r in R],*[round(r[1],5) for r in R])
