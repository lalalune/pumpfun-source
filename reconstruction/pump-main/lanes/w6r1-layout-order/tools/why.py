import sys,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
sc=json.load(open(sys.argv[3]))['windows']
off_raw={int(k) for k,v in sc.items() if v['raw']}
r=M.eval(M.cst)
print('model raw',len(r),'official',len(off_raw),'diff',sorted(hex(x) for x in r^off_raw))
print('text size cand',hex(M.csec['.text']['size']),'orig',hex(M.osec['.text']['size']))
# unmatched size deltas
for st in sorted(M.UN):
    a=M.pair.get(st); 
    if a: print(hex(st),'orig',M.wins[st]['bytes'],'cand',M.units[a][0],'delta',M.units[a][0]-M.wins[st]['bytes'],M.names[a][:60])
# classify
nd=0;cats={}
for st,a,calls,tl,hd in M.checks:
    if st in r: continue
    k=('data' if hd else 'nodata')
    cats[k]=cats.get(k,0)+1
print(cats)
