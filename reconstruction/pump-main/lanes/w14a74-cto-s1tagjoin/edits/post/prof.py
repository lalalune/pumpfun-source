import re,sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a74-cto-s1tagjoin/reconstruction/pump-main/lanes/w14a74-cto-s1tagjoin/edits/post')
from common import *
def gate_w(t,a,b):
    d=info(t)
    old='  br i1 %s, label %%%s, label %%%s\n'%(d['tst'],d['yes'],d['no'])
    assert t.count(old)==1
    t=t.replace(old,'  br i1 %s, label %%%s, label %%%s, !prof !99990\n'%(d['tst'],d['yes'],d['no']))
    return t+'\n!99990 = !{!"branch_weights", i32 %d, i32 %d}\n'%(a,b)
