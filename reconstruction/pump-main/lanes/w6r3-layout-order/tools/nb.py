import sys,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])
o=sorted(M.inv.items(),key=lambda kv:kv[1])
idx={a:i for i,a in enumerate(M.cst)}
t=int(sys.argv[3],16); k=[i for i,(a,w) in enumerate(o) if w==t][0]
for a,w in o[k-12:k+14]: print(hex(w),M.wins[w]['bytes'],idx[a],hex(a),nm(a)[:100])
