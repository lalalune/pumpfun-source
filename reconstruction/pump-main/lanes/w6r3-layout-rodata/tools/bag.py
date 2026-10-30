"""bag-of-normalized-instruction overlap and 3-gram overlap between original window and candidate fn. Usage: bag.py so orig_start symregex"""
import sys,re,collections
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r3-layout-rodata/reconstruction/harness'
sys.path.insert(0,H); import win
from original_input import resolve_original
from score import BASE
st=int(sys.argv[2],16)
o=win.Cand(resolve_original(BASE/'original.so')); c=win.Cand(sys.argv[1])
_,w=win.find_window(sys.argv[2]); 
ot=o.tokens(st,w['bytes'])
for s,n,nm in c.funcs:
    if re.search(sys.argv[3],nm):
        ct=c.tokens(s,n); break
def ov(a,b):
    A=collections.Counter(a);B=collections.Counter(b); return sum((A&B).values())/max(sum(A.values()),sum(B.values()))
g=lambda t,k: [tuple(t[i:i+k]) for i in range(len(t)-k+1)]
print('insns',len(ot),len(ct),'bag',round(ov(ot,ct),4),'3gram',round(ov(g(ot,3),g(ct,3)),4),'6gram',round(ov(g(ot,6),g(ct,6)),4))
