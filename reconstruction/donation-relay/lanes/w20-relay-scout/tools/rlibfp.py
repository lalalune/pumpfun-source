#!/usr/bin/env python3
"""rlibfp.py: identify the sysroot of a stripped sBPF ELF by matching its function bodies against rlib object functions."""
import sys,os,struct,hashlib,glob,collections
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/rea'))
from relayfn import Elf
def ar_members(p):
    b=open(p,'rb').read()
    assert b[:8]==b'!<arch>\n'
    i=8;names=b''
    while i<len(b):
        h=b[i:i+60]
        n=h[:16].decode().strip();sz=int(h[48:58].decode().strip())
        d=b[i+60:i+60+sz]
        if n=='//': names=d
        elif n.startswith('/') and n[1:].strip('/').isdigit():
            o=int(n[1:].strip('/'));e=names.index(b'\n',o);yield names[o:e].decode().rstrip('/'),d
        elif n=='/' or n.startswith('__.'): pass
        else: yield n.rstrip('/'),d
        i+=60+sz+(sz&1)
def obj_funcs(b):
    if b[:4]!=b'\x7fELF': return
    shoff=struct.unpack_from('<Q',b,0x28)[0];shnum=struct.unpack_from('<H',b,0x3c)[0];shstr=struct.unpack_from('<H',b,0x3e)[0]
    S=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*64) for i in range(shnum)]
    names=b[S[shstr][4]:S[shstr][4]+S[shstr][5]]
    def nm(o): return names[o:names.index(b'\0',o)].decode()
    for i,s in enumerate(S):
        n=nm(s[0])
        if n.startswith('.text') and s[1]==1 and s[5]>0:
            yield n,b[s[4]:s[4]+s[5]]
def norm(raw):
    m=bytearray(raw);i=0
    while i<len(raw):
        op=raw[i]
        if op==0x18:
            m[i+4:i+8]=bytes(4);m[i+12:i+16]=bytes(4);i+=16
        else:
            if op==0x85:
                m[i+1]=0;m[i+4:i+8]=bytes(4)
            i+=8
    return bytes(m)
def sysroot_table(libdir,only=('core','alloc','compiler_builtins','std')):
    t={}
    for p in sorted(glob.glob(libdir+'/*.rlib')):
        base=os.path.basename(p)
        crate=base[3:].split('-')[0]
        if crate not in only: continue
        for mn,d in ar_members(p):
            if not mn.endswith('.o'): continue
            for n,raw in obj_funcs(d):
                t.setdefault(hashlib.sha1(norm(raw)).digest(),(crate,n,len(raw)))
    return t
def elf_table(e):
    fs=dict(e.functions())
    r={}
    for a,sz in fs.items():
        raw=e.text[a-e.ta:a-e.ta+sz]
        r[a]=(hashlib.sha1(norm(raw)).digest(),sz)
    return r
if __name__=='__main__':
    roots=sys.argv[1:]
    O=os.path.expanduser('~/.cache/pumpfun-reconstruction/relay')
    new=elf_table(Elf(O+'/live/deployed.elf')); old=elf_table(Elf(O+'/rea/old.so'))
    for r in roots:
        for trip in ('sbpf-solana-solana','sbf-solana-solana'):
            d=os.path.expanduser(f'~/.cache/solana/{r}/platform-tools/rust/lib/rustlib/{trip}/lib')
            if not os.path.isdir(d): continue
            t=sysroot_table(d)
            def sc(tab):
                hits=[v for v in tab.values() if v[0] in t]
                return len(hits),sum(v[1] for v in hits)
            print(r,trip,'sysroot funcs',len(t),'new hits',sc(new),'old hits',sc(old),flush=True)
