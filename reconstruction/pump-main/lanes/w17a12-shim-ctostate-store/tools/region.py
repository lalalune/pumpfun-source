import sys
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(sys.argv[1]):
    o=int(l.split()[0][1:],16)
    if lo<=o<hi: print(l.rstrip())
