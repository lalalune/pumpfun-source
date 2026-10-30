import sys
L=open(sys.argv[1]).read().split('\n')
vs=next(i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto8validate' in l)
for i in range(vs,len(L)):
    if 'lifetime.start.p0(i64 32, ptr %t)' in L[i]:
        for j in range(i,i+8):
            if L[j].lstrip().startswith('switch'): print(j); sys.exit()
