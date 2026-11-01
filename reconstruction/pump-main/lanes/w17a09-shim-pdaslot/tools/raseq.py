#!/usr/bin/env python3
"""raseq.py <name>: run debug llc regalloc on fx/<name>/m.ll and print the first greedy decisions"""
import sys,re,subprocess,os
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
n=sys.argv[1]; k=int(sys.argv[2]) if len(sys.argv)>2 else 40
p=f'{OUT}/ra/{n}.ra.txt'
if not os.path.exists(p):
    with open(p,'w') as f:
        subprocess.run(['nice','-n','5',D,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections','-debug-only=regalloc',f'{OUT}/fx/{n}/m.ll','-filetype=obj','-o',f'{OUT}/ra/{n}.o'],stderr=f,stdout=subprocess.DEVNULL)
out=[];cur=None
for l in open(p):
    m=re.match(r'selectOrSplit GPR:(%\d+) \[(\d+)[rBed]',l)
    if m: cur=(m.group(1),m.group(2)); continue
    m=re.match(r'assigning (%\d+) to \$(r\d+)',l)
    if m and cur: out.append(f'{m.group(1)}@{cur[1]}->{m.group(2)}'); continue
    m=re.match(r'evicting \$(r\d+) interference: Cascade (\d+)',l)
    if m: out.append(f'EV{m.group(1)}')
    if len(out)>=k: break
print(n,' '.join(out))
