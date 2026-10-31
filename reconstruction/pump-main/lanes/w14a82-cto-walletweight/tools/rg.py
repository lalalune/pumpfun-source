import sys
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(f):
    q=l.split(None,1)
    if len(q)==2 and lo<=int(q[0],16)<hi: print(l.rstrip())
