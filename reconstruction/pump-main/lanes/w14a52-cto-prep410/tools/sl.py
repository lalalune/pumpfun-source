import sys,re
def load(dis,lst,base):
    names={}
    for l in open(lst):
        p=l.split(' ; ')
        if len(p)>1: names[int(p[0].split()[0],16)]=p[1].strip()
    out=[]
    for l in open(dis):
        l=l.rstrip('\n'); m=re.match(r'\s*(0x[0-9a-f]+|[0-9a-f]+)\s+(.*)',l)
        if not m: continue
        a=int(m.group(1),16)-base
        t=m.group(2)
        if a in names: t=re.sub(r'call.*','',t)+names[a]
        out.append((a,t))
    return out
o=load('orig.dis','o.lst',0x22a10); c=load('cand.dis','c.lst',0)
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
for nm,L in (('ORIG',o),('CAND',c)):
    print('=====',nm)
    for a,t in L:
        if lo<=a<hi: print('%04x %s'%(a,t))
