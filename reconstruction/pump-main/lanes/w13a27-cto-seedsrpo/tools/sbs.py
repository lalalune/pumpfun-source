import sys,itertools
def load(p): return [l.rstrip().split(None,1) for l in open(p)]
o=load('orig.dis'); c=load(sys.argv[1]); lo,hi,d=[int(x,16) for x in sys.argv[2:5]]
B=0x22a10
oo=[x for x in o if lo<=int(x[0],16)-B<hi]; cc=[x for x in c if lo-d<=int(x[0],16)-B<hi-d]
for a,b in itertools.zip_longest(oo,cc,fillvalue=['','']):
    ra=f'{int(a[0],16)-B:#x}' if a[0] else ''; rb=f'{int(b[0],16)-B:#x}' if b[0] else ''
    print(f'{ra:7} {a[1]:38} | {rb:7} {b[1]}')
