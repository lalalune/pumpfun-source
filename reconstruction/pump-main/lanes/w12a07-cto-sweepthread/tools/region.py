#!/usr/bin/env python3
"""region.py <orc-name|so:path> : exact-token match fraction per 0x400 bucket of the original (where the ratio is lost)."""
import sys,os,difflib,subprocess,re
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread')
L=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def toks(raw):
    i=0;out=[];offs=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; x=bytearray(raw[i:i+k])
        if x[0]==0x18: x[4:8]=bytes(4); x[12:16]=bytes(4)
        elif x[0]==0x85: x[4:8]=bytes(4)
        out.append(bytes(x)); offs.append(i); i+=k
    return out,offs
arg=sys.argv[1]
if arg.startswith('so:'):
    sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a07-cto-sweepthread/reconstruction/harness')
    from win import Cand
    cd=Cand(arg[3:]); s,n,nm=next(f for f in cd.funcs if re.search(r'admin_cto7execute17h',f[2])); raw=cd.fn(s,n)
else:
    raw=open(O+'/orc/'+arg+'/m.bin','rb').read()
o,oo=toks(open(O+'/orig_raw.bin','rb').read()); c,co=toks(raw)
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
B=int(sys.argv[2],16) if len(sys.argv)>2 else 0x400
tot={};mat={}
for i,x in enumerate(oo): tot[x//B]=tot.get(x//B,0)+1
for a,b,n in sm.get_matching_blocks():
    for k in range(n): mat[oo[a+k]//B]=mat.get(oo[a+k]//B,0)+1
print('ratio %.5f'%sm.ratio())
for k in sorted(tot): print('%05x-%05x  %4d/%4d  %.2f'%(k*B,(k+1)*B,mat.get(k,0),tot[k],mat.get(k,0)/tot[k]))
