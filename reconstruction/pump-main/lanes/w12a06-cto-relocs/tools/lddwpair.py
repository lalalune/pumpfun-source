#!/usr/bin/env python3
"""lddw census for one window: classify every lddw target in two ELFs and print the multiset diff.
usage: lddwpair.py <orig.so> <cand.so> [start=0x22a10] [size=27400] [--list]"""
import re,sys,struct,subprocess,collections
import os; B=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def secs(path):
    out=subprocess.check_output([B+'/llvm-readelf','-S',path],text=True)
    d={}
    for l in out.splitlines():
        m=re.search(r'\]\s+(\S+)\s+\S+\s+([0-9a-f]{16})\s+([0-9a-f]+)\s+([0-9a-f]+)',l)
        if m: d[m.group(1)]=(int(m.group(2),16),int(m.group(3),16),int(m.group(4),16))
    return d
def dis(path,start,size):
    out=subprocess.check_output([B+'/llvm-objdump','-d','--no-show-raw-insn',f'--start-address={start}',f'--stop-address={start+size}',path],text=True)
    res=[]
    for l in out.splitlines():
        m=re.match(r'\s*(\d+):\s+(.*)',l)
        if m: res.append(((int(m.group(1))*8)-start,re.sub(r'\s*<.*>$','',m.group(2))))
    return res
def classify(path,start,size):
    data=open(path,'rb').read(); S=secs(path); rb,ro,rs=S['.rodata']
    res=[]
    for off,ins in dis(path,start,size):
        m=re.match(r'lddw (r\d+), (\S+)',ins)
        if not m: continue
        r,v=m.groups(); v=int(v,16) if not v.startswith('-') else -int(v[1:],16)
        desc=f'const {v:#x}'
        for n in ('.rodata','.data.rel.ro'):
            if n not in S: continue
            base,foff,sz=S[n]
            if base<=v<base+sz:
                o=foff+(v-base); b=data[o:o+48]
                if n=='.data.rel.ro':
                    p,l2=struct.unpack('<QQ',b[:16])
                    s=data[ro+(p-rb):ro+(p-rb)+min(l2,60)] if rb<=p<rb+rs else b''
                    line,col=struct.unpack('<II',b[16:24])
                    if s: desc=f'{n}+{v-base:#x} Loc {s!r} l{line}:c{col}'
                    else: desc=f'{n}+{v-base:#x} ptr={p:#x} {b[:24].hex()}'
                else:
                    desc=f'{n}+{v-base:#x} {b[:32]!r}'
        res.append((off,r,desc))
    return res
a=sys.argv[1:]; lst='--list' in a; a=[x for x in a if x!='--list']
start=int(a[2],16) if len(a)>2 else 0x22a10; size=int(a[3]) if len(a)>3 else 27400
o=classify(a[0],start,size); c=classify(a[1],start,size)
co=collections.Counter(d for _,_,d in o); cc=collections.Counter(d for _,_,d in c)
print(f'lddw total orig {len(o)} cand {len(c)}; relocated orig {sum(1 for x in o if not x[2].startswith("const"))} cand {sum(1 for x in c if not x[2].startswith("const"))}')
for k in sorted(set(co)|set(cc)):
    flag='' if co[k]==cc[k] else '  <<<'
    if flag or lst: print(f'{co[k]:3} {cc[k]:3} {k}{flag}')
if lst:
    for k in sorted(set(co)|set(cc)):
        if co[k]!=cc[k]:
            print('ORIG offs',[hex(x) for x,_,d in o if d==k]); print('CAND offs',[hex(x) for x,_,d in c if d==k])
