#!/usr/bin/env python3
"""occ2.py <dir>: run radbg if needed; find clone-5 rent_epoch load (LDD x,32 in the block with LDB x,42 following key4) of the
sweep transfer run; print final physreg occupancy (originals) at that slot index."""
import sys,re,os,subprocess
d=sys.argv[1]; T=os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(d+'/ra.log'): subprocess.run(['bash',T+'/radbg.sh',d])
t=open(d+'/ra.log').read(); L=t.split('\n')
a=[i for i,l in enumerate(L) if l.startswith('********** MACHINEINSTRS')]; g=[i for i,l in enumerate(L) if l.startswith('********** GREEDY')][0]
mi=[l for l in L[a[1]:g]]
# slot of the n-th 'LDB_V1 %x, 42' after first index
pat=sys.argv[2] if len(sys.argv)>2 else '_216.i'
slot=None
for l in mi:
    m=re.match(r'(\d+)B\s+%(\d+):gpr = LDD_V1 %(\d+):gpr, 0 :: \(load \(s64\) from %ir\.'+re.escape(pat)+r'\)',l)
    if m: slot=int(m.group(1)); keyv=m.group(2); break
print('key vreg',keyv,'slot',slot)
# find the rent load (LDD x,32) just before
prev=[l for l in mi if re.match(r'\d+B',l)]
cur={}; parent={}; last=None
for l in L[g:]:
    m=re.match(r'selectOrSplit GPR:(%\d+)',l)
    if m: last=m.group(1)
    m=re.match(r'queuing new interval: (%\d+)',l)
    if m and last and int(m.group(1)[1:])>int(last[1:]) and m.group(1) not in parent: parent[m.group(1)]=last
    m=re.match(r'assigning (%\d+) to (\$r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=(m.group(2),m.group(3))
    m=re.match(r'unassigning (%\d+) from',l)
    if m: cur.pop(m.group(1),None)
def root(v):
    while v in parent: v=parent[v]
    return v
defs={}
for l in mi:
    m=re.match(r'(\d+)B\s+(%\d+):gpr = (.*)',l)
    if m and m.group(2) not in defs: defs[m.group(2)]=m.group(3)[:80]
def covers(rs,s):
    for x,y in re.findall(r'\[(\d+)\w,(\d+)\w:',rs):
        if int(x)<=s<int(y): return True
    return False
S=int(sys.argv[3]) if len(sys.argv)>3 else slot-16
for v,(r,rs) in sorted(cur.items(),key=lambda x:int(x[1][0][2:])):
    if covers(rs,S): print(r,v,'<-',root(v),defs.get(root(v),''))
