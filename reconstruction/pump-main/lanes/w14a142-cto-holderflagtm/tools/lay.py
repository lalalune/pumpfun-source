#!/usr/bin/env python3
# lay.py <mir-dump>: block order with IR name, instr count, cumulative byte offset (approx: 8B/instr, LD_imm64 16B)
import sys,re
cur=None; out=[]; 
for l in open(sys.argv[1]):
    m=re.match(r'^bb\.(\d+)(?:\.([\w.$-]+))?',l)
    if m: cur=[int(m.group(1)),m.group(2) or '',0]; out.append(cur); continue
    if cur is None: continue
    s=l.strip()
    if not s or s.startswith(('successors','liveins',';','#','frameInfo')) or s.endswith(':') or s=='}' : continue
    if re.match(r'^(\$\w+ = )?[A-Z]',s) or re.match(r'^\$',s):
        op=re.sub(r'^(\$\w+(, \$\w+)* = )','',s).split()[0]
        if op in ('CFI_INSTRUCTION','EH_LABEL','DBG_VALUE','KILL','IMPLICIT_DEF'): continue
        cur[2]+= 2 if op.startswith('LD_imm64') or op=='LD_pseudo' else 1
off=0
for b,n,c in out:
    print('%5x %4d bb.%d %s'%(off,c,b,n)); off+=c*8
