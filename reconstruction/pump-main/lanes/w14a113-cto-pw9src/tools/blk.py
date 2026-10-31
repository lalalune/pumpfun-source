#!/usr/bin/env python3
"""blk.py x.s [lo hi]: list execute's asm blocks with byte offset, insn count and IR block name (from relay.parse)."""
import sys,re,importlib.util,os
T=os.path.dirname(os.path.abspath(__file__))+'/../tools93'
sys.argv_s=sys.argv; 
sp=importlib.util.spec_from_file_location('relay',T+'/relay.py'); R=importlib.util.module_from_spec(sp); sv=sys.argv; sys.argv=['x']; sp.loader.exec_module(R); sys.argv=sv
pre,bl,post=R.parse(sys.argv[1]); lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
off=0
for n,b in bl:
    ii=R.insns(b); sz=sum(16 if b[i].strip().startswith('lddw') else 8 for i in ii)
    m=re.search(r'#\s*(%\S+)',b[0]); ir=m.group(1) if m else ''
    if lo<=off<hi: print('%05x %4d %-10s %s'%(off,len(ii),n,ir))
    off+=sz
