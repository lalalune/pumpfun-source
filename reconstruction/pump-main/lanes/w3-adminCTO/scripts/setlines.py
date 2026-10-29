import sys,json
p=sys.argv[1]; d=json.load(open(sys.argv[2]))
L=open(p).read().split('\n')
for k,v in d.items(): L[int(k)-1]=v
open(p,'w').write('\n'.join(L))
