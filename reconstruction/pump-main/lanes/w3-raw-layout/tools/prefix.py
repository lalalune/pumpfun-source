import sys,re; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3])
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:90]
U=[a for a in M.cst if M.region(a)=='U']; D=[a for a in M.cst if M.region(a)=='D']
L=[a for a in M.cst if M.region(a)=='L']
oL=sorted(L,key=lambda a:M.inv[a])
last=None
for k in range(0,len(oL)+1,int(sys.argv[4])):
    pre=oL[:k]; ps=set(pre)
    o=U+pre+[a for a in L if a not in ps]+D
    v=p13(M,o)
    if v!=last: print(k, hex(M.inv[oL[k]]) if k<len(oL) else '-', v, nm(oL[k]) if k<len(oL) else ''); last=v
