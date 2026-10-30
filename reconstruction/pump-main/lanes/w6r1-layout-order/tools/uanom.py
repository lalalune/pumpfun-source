import sys,re; sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
base=lambda n: re.sub(r'17h[0-9a-f]{16}E$','',n)
for reg in sys.argv[3]:
    U=[a for a in M.cst if M.region(a)==reg and a in M.inv]
    oU=sorted(U,key=lambda a:M.inv[a])
    for i,a in enumerate(oU):
        # anomaly: original order of base names not sorted at this point
        if 0<i<len(oU)-1:
            p,n=base(M.names[oU[i-1]]),base(M.names[oU[i+1]]); me=base(M.names[a])
            if not (p<=me<=n) and not (p==n):
                print(reg,i,hex(M.inv[a]),M.units[a][0],me[:100],' | prev',p[:50],' next',n[:50])
