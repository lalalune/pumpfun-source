import sys
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(sys.argv[1]):
    p=l.split(None,1)
    if p and lo<=int(p[0],16)<=hi: print(l.rstrip())
