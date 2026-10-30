"""Marginal official-raw value of fixing each unmatched window's size (our order). Usage: sizemarg.py <so> <refined>"""
import sys,itertools
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
U=sorted(M.UN); order=[a for a in M.cst]
def run(fixset):
    fx=set(M.pair[s] for s in fixset)
    sz=lambda a: M.wins[M.inv[a]]['bytes'] if a in fx else M.units[a][0]
    r=M.eval(order,sz); return len([s for s in r if g[s]])
print('none',run([]),'all',run(U))
for s in U:
    d=M.wins[s]['bytes']-M.units[M.pair[s]][0]
    print(hex(s),'delta',d,'only',run([s]),'all-but',run([x for x in U if x!=s]))
