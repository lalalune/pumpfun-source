# fmr.py fn.bin...: plain ratio, frame-masked (L1) and frame+reg masked (L2) ratio, plus per-0x800 L1 matched tokens
import sys,difflib,collections
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools')
import types
C=types.ModuleType('C'); _s=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools/cls.py').read(); C.__dict__['__file__']='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a85-cto-s1reload/reconstruction/pump-main/lanes/w14a85-cto-s1reload/tools/rx.py').read()
g={'__name__':'x'}; exec(src[:src.index("OUT=os.environ.get")],g)
O=g['orig_window']()
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
oo=[o for o,_ in C.insns(O)]
for f in sys.argv[1:]:
    c=open(f,'rb').read(); r=[]
    for l in (0,1,2):
        sm=difflib.SequenceMatcher(None,toks(O,l),toks(c,l),autojunk=False); r.append(round(sm.ratio(),5))
        if l==1:
            cnt=collections.Counter()
            for a,b,n in sm.get_matching_blocks():
                for i in range(a,a+n): cnt[oo[i]//0x800]+=1
    print(f.split('/')[-2],len(c),r,' '.join(str(cnt[k]) for k in range(14)))
