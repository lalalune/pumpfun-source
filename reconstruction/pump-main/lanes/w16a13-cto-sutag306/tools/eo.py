#!/usr/bin/env python3
"""eo.py name...: error-site offsets (line imm stores) of rx/<name>/fn.bin vs orig and main; plus lddw/call counts and M."""
import struct,sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle
def lines(b):
    r=[];i=0;n=0
    while i<len(b):
        op=b[i]
        if op==0x62:
            imm=struct.unpack_from('<i',b,i+4)[0]
            if 280<=imm<=780: r.append((imm,i))
        if op==0x18: n+=1
        i+=16 if op==0x18 else 8
    return r,n
def show(n,b): r,l=lines(b); print(n.ljust(10),f'lddw={l}',' '.join(f'{a}@{o:x}' for a,o in r))
show('orig',oracle.orig_window()); show('main',oracle.elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),oracle.KEEP))
for n in sys.argv[1:]:
    p=n if os.path.exists(n) else T+'/../rx/'+n+'/fn.bin'
    show(os.path.basename(n),open(p,'rb').read())
