import sys
f,a,b=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(f):
    x=int(l.split()[0],16)
    if a<=x<b: print(l.rstrip())
