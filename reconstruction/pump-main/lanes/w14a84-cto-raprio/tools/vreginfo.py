#!/usr/bin/env python3
"""vreginfo.py <pregreedy.mir> <vreg>... : defs and uses (block + instruction) of post-coalescing vregs, to name the IR value
behind a greedy decision. Make the MIR with llc -stop-before=greedy. Experiment only."""
import sys,re
mir=open(sys.argv[1]).read(); body=mir[mir.index('\nbody:'):]
blk=None; rows=[]
for l in body.split('\n'):
    m=re.match(r'\s{2}(bb\.\d+[^:]*):',l)
    if m: blk=m.group(1); continue
    s=l.strip()
    if s and blk and not s.startswith(('successors','liveins',';')): rows.append((blk,s))
for v in sys.argv[2:]:
    pat=re.compile(r'%'+v+r'(?![\d])')
    d=[(b,s) for b,s in rows if pat.search(s.split('=')[0]) and '=' in s]
    u=[(b,s) for b,s in rows if pat.search(s.split('=',1)[1] if '=' in s else s)]
    bl=sorted(set(b for b,_ in d+u),key=lambda x:int(x.split('.')[1]))
    print(f'%{v}: {len(d)} defs, {len(u)} uses, {len(bl)} blocks: {" ".join(b.split(".",2)[1]+("."+b.split(".",2)[2] if b.count(".")>1 else "") for b in bl[:12])}{" ..." if len(bl)>12 else ""}')
    for b,s in d[:4]: print('   def',b,'|',s[:150])
    for b,s in u[:4]: print('   use',b,'|',s[:150])
