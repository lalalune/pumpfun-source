#!/usr/bin/env python3
"""cdiff2.py <name> <ids comma|-> [--base ir/m0.s.ll]: apply edits to the slim module, run fx (keep), and print the
positional disassembly diff against main's fn.bin (fx/main/fn.bin). Experiment only."""
import sys,os,json,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import fx,screen,sbpfdis
OUT=os.path.dirname(T)
a=sys.argv[1:]; name=a[0]; ids=[] if a[1]=='-' else a[1].split(',')
base=a[a.index('--base')+1] if '--base' in a else OUT+'/ir/m0.s.ll'
L=open(base).read().split('\n')
E={}
for l in open(OUT+'/gen/U.jsonl'):
    e=json.loads(l); E[e['id']]=e
t=screen.apply(L,[E[i] for i in ids]) if ids else '\n'.join(L)
r=fx.run(t,name,keep=False); print(json.dumps(r))
mb=open(OUT+'/fx/main/fn.bin','rb').read() if os.path.exists(OUT+'/fx/main/fn.bin') else None
if mb is None or name=='main': sys.exit(0)
cb=open(OUT+f'/fx/{name}/fn.bin','rb').read()
DM=sbpfdis.d(mb); DC=sbpfdis.d(cb); dm=[x[1] for x in DM]; dc=[x[1] for x in DC]
sm=difflib.SequenceMatcher(None,dm,dc,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'--- {tag} main[{i1}:{i2}] cand[{j1}:{j2}]')
    for x in DM[i1:i2][:12]: print('   - %05x %s'%x)
    for x in DC[j1:j2][:12]: print('   + %05x %s'%x)
