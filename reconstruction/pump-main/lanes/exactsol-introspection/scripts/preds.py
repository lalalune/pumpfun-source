import re,sys
# parse "addr  insn" listing; find predecessors of join target (orig addr or cand)
def parse(path):
    L=[]
    for line in open(path):
        m=re.match(r'\s*(0x[0-9a-f]+)\s+(.*)',line)
        if m: L.append((int(m.group(1),16),m.group(2).strip()))
    return L
L=parse(sys.argv[1]); join=int(sys.argv[2],16); base=L[0][0]
idx={a:i for i,(a,_) in enumerate(L)}
for i,(a,ins) in enumerate(L):
    m=re.match(r'(ja|j\w+) .*?([+-]?0x[0-9a-f]+|[+-]?\d+)$',ins)
    tgt=None
    if m and not ins.startswith('call'):
        off=int(m.group(2),16) if '0x' in m.group(2) else int(m.group(2))
        nxt=L[i+1][0] if i+1<len(L) else a+8
        tgt=nxt+off*8
    fall = (i+1<len(L) and L[i+1][0]==join and not ins.startswith('ja') and not ins=='exit')
    if tgt==join or fall:
        ctx=[x[1] for x in L[max(0,i-4):i+1]]
        print(hex(a-base), 'FALL' if fall and tgt!=join else 'JMP', ' | '.join(ctx))
