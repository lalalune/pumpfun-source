import sys
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(f):
    p=l.split(None,1)
    if len(p)<2: continue
    try: a=int(p[0],16)-0x22a10
    except: continue
    if lo<=a<hi: print('%04x %s'%(a,p[1].rstrip()))
