import sys,os,struct,re,bisect,collections
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
from relaylib import *
p=sys.argv[1]
e=Elf(p);d=e.sec['.data.rel.ro'];ro=e.sec['.rodata']
refs=collections.defaultdict(list)
fs=e.functions();st=[a for a,_ in fs]
for a,op,regs,o,imm,n in e.insns():
    if op==0x18 and a in e.rel:
        v=e.lddw(a)
        if d['addr']<=v<d['addr']+d['size']:
            refs[v].append(st[bisect.bisect_right(st,a)-1])
rows=[]
for off in sorted(e.rel):
    if d['addr']<=off<d['addr']+d['size']:
        v=e.ptr(off)
        if ro['addr']<=v<ro['addr']+ro['size'] and off+24<=d['addr']+d['size']:
            n=struct.unpack_from('<Q',e.b,d['off']+off-d['addr']+8)[0]
            if 3<n<200:
                s=e.b[ro['off']+v-ro['addr']:ro['off']+v-ro['addr']+n]
                if s.rstrip(b'\0').endswith(b'.rs'):
                    ln,col=struct.unpack_from('<II',e.b,d['off']+off-d['addr']+16)
                    rows.append((off,s.rstrip(b'\0').decode(),ln,col,sorted(set(refs.get(off,[])))))
for r in rows:
    print(hex(r[0]),r[1],r[2],r[3],' '.join(hex(x) for x in r[4]))
