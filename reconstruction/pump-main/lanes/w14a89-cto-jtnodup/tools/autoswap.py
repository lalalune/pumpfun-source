#!/usr/bin/env python3
"""autoswap.py in.s out.s: find the MBP swap (sweep join %bb56.i chain placed right after an error block, before the wallet
token_frozen block %bb9.i*) and move that chain back after the ProgramError From block that jumps to bb56.i. Experiment only."""
import sys,re,subprocess
src,dst=sys.argv[1:3]; L=open(src).read().split('\n')
lab=lambda l: re.match(r'^(LBB0_\d+):\s*#\s*(\S+)',l)
s=[(k,lab(l).group(1)) for k,l in enumerate(L) if lab(l) and re.match(r'%bb56\.i\d*$',lab(l).group(2))][0]
# end: first block after s whose comment is %bb9.i<digits> (wallet token_frozen)
e=[(k,lab(l).group(1)) for k,l in enumerate(L) if k>s[0] and lab(l) and re.match(r'%bb9\.i\d+$',lab(l).group(2))][0]
# ja S after a ProgramError From call
cand=[k for k,l in enumerate(L) if l.strip()=='ja '+s[1] and any('ProgramError' in L[j] for j in range(k-4,k))]
print('chain',s,e,'ja lines',[c+1 for c in cand])
r=subprocess.run(['python3',__file__.replace('autoswap','mvchain'),src,dst,s[1],e[1],str(cand[0]+1)],capture_output=True,text=True); print(r.stdout,r.stderr)
