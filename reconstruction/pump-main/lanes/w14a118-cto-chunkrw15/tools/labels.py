#!/usr/bin/env python3
"""labels.py [sz]: per orig chunk, error-line immediates and called symbols (resolved via the main unstripped.so symtab)."""
import sys,os,struct,re,subprocess
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,dis as D
sz=int(sys.argv[1],16) if len(sys.argv)>1 else 0x200
so=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
b=open(so,'rb').read()
shoff=struct.unpack_from('<Q',b,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
syms={}
for s in sh:
    if s[1]==2:
        so_=sh[s[6]][4]
        for j in range(s[5]//24):
            nm,info,oth,shndx,val,size=struct.unpack_from('<IBBHQQ',b,s[4]+j*24)
            if (info&0xf)==2: syms[val]=b[so_+nm:b.index(b'\0',so_+nm)].decode()
dem=subprocess.run(['c++filt'],input='\n'.join(syms.values()),capture_output=True,text=True).stdout.split('\n')
names=dict(zip(syms.keys(),dem))
def short(n):
    n=re.sub(r'::h[0-9a-f]{16}$','',n); n=re.sub(r'<[^<>]*>','',n); n=re.sub(r'<[^<>]*>','',n)
    return '::'.join(n.split('::')[-2:])
O=oracle.orig_window(); W=0x22a10+0x120  # text vaddr base guess fixed below
# find text section vaddr: window start in vaddr = 0x22a10 + text_off? derive from symbol of admin_cto in main
base=[v for v,n in syms.items() if 'admin_cto7execute' in n][0]
per={}
ins=D.d(O)
for k,(o,t) in enumerate(ins):
    c=o//sz; e=per.setdefault(c,[[],[]])
    m=re.match(r'stw \[r10-0x2b8\], (\d+)',t)
    if m: e[0].append(m.group(1))
    if t.startswith('call '):
        imm=struct.unpack_from('<i',O,o+4)[0]
        if imm==-1: e[1].append('abort'); continue
        tgt=base+o+8+imm*8
        e[1].append(short(names.get(tgt,hex(tgt))))
for c in sorted(per):
    ln,cl=per[c]; 
    from collections import Counter
    cc=Counter(cl); cs=', '.join(f'{k}' + (f'x{v}' if v>1 else '') for k,v in cc.items())
    print(f'{c*sz:#06x} lines[{",".join(ln)}] calls[{cs}]')
