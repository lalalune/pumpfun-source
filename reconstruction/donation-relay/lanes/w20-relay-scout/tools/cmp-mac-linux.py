import sys,os,hashlib,collections,re
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
from relaylib import *
a,b=sys.argv[1:3]
A=Elf(a);B=Elf(b);sa=symbols(a);sb=symbols(b)
for s in ('.text','.rodata','.data.rel.ro','.dynsym','.dynstr','.rel.dyn'):
    x=A.section_bytes(s);y=B.section_bytes(s)
    print(s,len(x),len(y),'equal' if x==y else 'DIFF')
def keyset(e,sy):
    c=collections.Counter()
    for addr,(sz,n) in sy.items():
        c[(demangle(n),sz,hashlib.sha1(e.norm(addr,sz)[0]).digest())]+=1
    return c
ka,kb=keyset(A,sa),keyset(B,sb)
print('funcs',sum(ka.values()),sum(kb.values()),'only A',sum((ka-kb).values()),'only B',sum((kb-ka).values()))
for k in list((ka-kb))[:12]: print(' only mac',k[0][:90],k[1])
for k in list((kb-ka))[:12]: print(' only linux',k[0][:90],k[1])
# same names and order? names with hashes
na={n for _,n in sa.values()};nb={n for _,n in sb.values()}
print('mangled same',len(na&nb),'mac only',len(na-nb),'linux only',len(nb-na))
oa=[demangle(sa[x][1]) for x in sorted(sa)];ob=[demangle(sb[x][1]) for x in sorted(sb)]
print('same demangled order',oa==ob, sum(1 for p,q in zip(oa,ob) if p!=q))
same_addr=sum(1 for x in sa if x in sb and demangle(sa[x][1])==demangle(sb[x][1]) and sa[x][0]==sb[x][0]);print('same addr+name',same_addr)
