import sys,struct,collections
import os; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../harness'))
from score import BASE
from original_input import resolve_original
def secs(b):
    shoff=struct.unpack_from('<Q',b,0x28)[0]; es,n,si=struct.unpack_from('<HHH',b,0x3a)
    L=[struct.unpack_from('<IIQQQQ',b,shoff+i*es) for i in range(n)]
    so=L[si][4]; return {b[so+s[0]:b.index(b'\0',so+s[0])].decode():(s[3],s[4],s[5]) for s in L}
def census(path):
    b=open(path,'rb').read(); S=secs(b); ra,ro,rs=S['.rodata']; da,do,ds=S['.data.rel.ro']
    out=collections.Counter()
    for o in range(do,do+ds-23,8):
        lo,p,l,line,col=struct.unpack_from('<IIQII',b,o)
        if lo==0 and ra<=p<ra+rs and 3<l<200 and 0<line<100000 and col<1000:
            s=b[ro+p-ra:ro+p-ra+l]
            if s.endswith(b'.rs'):
                out[(s.decode(errors='replace'),line,col)]+=1
    return out
o=census(resolve_original(BASE/'original.so')); c=census(sys.argv[1])
print('orig',sum(o.values()),len(o),'cand',sum(c.values()),len(c))
on=collections.Counter(); cn=collections.Counter()
for k in o: on[k[0]]+=1
for k in c: cn[k[0]]+=1
for f in sorted(set(on)|set(cn)):
    if on[f]!=cn[f] or {k for k in o if k[0]==f}!={k for k in c if k[0]==f}: print('DIFF',f,on[f],cn[f], sorted({k[1:] for k in o if k[0]==f}^{k[1:] for k in c if k[0]==f})[:20])
print('files',len(on))
for f in sorted(on): print(' ',on[f],f) if not f.startswith('programs') else None
