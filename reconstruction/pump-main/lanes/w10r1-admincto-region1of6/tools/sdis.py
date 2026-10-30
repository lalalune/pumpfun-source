#!/usr/bin/env python3
"""dis.py <so|orig> <start> <size> : print 'off(hex rel) text' lines, offsets relative to start."""
import sys,re,subprocess
from pathlib import Path
H=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w10r1-admincto-region1of6/reconstruction/harness')
sys.path.insert(0,str(H))
from llvm_tools import objdump
from score import BASE
from original_input import resolve_original
def dis(path,start,size):
    txt=subprocess.check_output([objdump(),'-d','--no-show-raw-insn',f'--start-address={start:#x}',f'--stop-address={start+size:#x}',str(path)],text=True)
    out=[]
    for line in txt.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',line)
        if m:
            a=int(m.group(1),16)
            t=re.sub(r'\s+<[^>]*>','',m.group(2).strip())
            out.append((a-start,t))
    return out
if __name__=='__main__':
    p=sys.argv[1]
    if p=='orig': p=resolve_original(BASE/'original.so')
    for o,t in dis(p,int(sys.argv[2],0),int(sys.argv[3],0)): print(f'{o:#06x} {t}')
