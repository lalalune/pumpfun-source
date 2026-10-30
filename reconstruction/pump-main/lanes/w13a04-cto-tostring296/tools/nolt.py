import sys,re
# nolt.py in.ll out.ll S E name... : drop lifetime markers of the named allocas inside lines S..E
src,dst,S,E=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); names=sys.argv[5:]
L=open(src).read().split('\n'); n=0
for i in range(S-1,E):
    for nm in names:
        if 'llvm.lifetime' in L[i] and re.search(r'ptr nonnull %'+re.escape(nm)+r'\)',L[i]): L[i]=''; n+=1
open(dst,'w').write('\n'.join(L)); print('dropped',n,file=sys.stderr)
