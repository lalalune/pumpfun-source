#!/usr/bin/env python3
"""pfirst.py: IR-level PDA-first (w17a09 k8 shape) on the named post-opt module: move the hkx/PDA block of bb5 before the
sk copy in the entry block. Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import ce3,pscore
PS='  call void @llvm.lifetime.start.p0(i64 72, ptr nonnull %hkx)\n'
PE='  call void @llvm.lifetime.end.p0(i64 33, ptr nonnull %_17)\n'
SK='  call void @llvm.lifetime.start.p0(i64 32, ptr nonnull %sk)\n'
def pfirst(t):
    a=t.index(PS); b=t.index(PE,a)+len(PE); blk=t[a:b]; t=t[:a]+t[b:]
    s=t.index(SK); return t[:s]+blk+t[s:]
if __name__=='__main__':
    for nm,base in (('m0P',ce3.BASE),('ve1nP',ce3.ve1n())):
        t=pfirst(base); open(os.environ['LANE_OUT']+f'/ir/{nm}.ll','w').write(t)
        print(json.dumps(pscore.score_text(t,nm,keepobj=True)))
