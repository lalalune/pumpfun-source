#!/usr/bin/env python3
"""annot.py <orig|unstripped.so> : admin_cto listing, rel offsets, call targets named via the candidate
symbol table (layout is identical outside the window), and mov-imm line hints. Output: 'off text ; label'."""
import sys,os,re
H=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../harness'); sys.path.insert(0,H)
from score import original_windows, BASE
from win import Cand, insns, demangle, ORIG_SECS, objdump_text, resolve_original
SYMSO=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
symc=Cand(SYMSO); names={s:demangle(nm) for s,n,nm in symc.funcs}
def short(n):
    n=re.sub(r'<[^<>]*>','',n); n=re.sub(r'<[^<>]*>','',n)
    return '::'.join(n.split('::')[-2:])
arg=sys.argv[1]
if arg=='orig':
    w={x['start']:x for x in original_windows()}[0x22a10]; st=0x22a10
    I=insns(w['raw'],st,ORIG_SECS); T=objdump_text(resolve_original(BASE/'original.so'),st,st+27400)
else:
    c=Cand(arg); s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if re.search(r'admin_cto::execute$',demangle(nm))][0]
    st=s; I=insns(c.fn(s,n),s,c.secs); T=c.disassembly(s,n)
for a,raw,_ in I:
    t=T.get(a,'')
    lab=''
    if raw[0]==0x85 and raw[1]&0xf0==0x10 or (raw[0]==0x85):
        imm=int.from_bytes(raw[4:8],'little',signed=True)
        if raw[1]==0x10 or True:
            tgt=a+8+imm*8
            if tgt in names: lab=short(names[tgt])
            elif raw[1]==0: lab='syscall'
    print(f'{a-st:05x} {t}'+(f' ; {lab}' if lab else ''))
