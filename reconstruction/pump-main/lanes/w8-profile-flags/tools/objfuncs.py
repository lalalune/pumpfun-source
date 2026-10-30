#!/usr/bin/env python3
"""objfuncs.py: minimal ELF64 .o reader -> {symbol: (bytes, relocs)} for FUNC symbols; diff two objects."""
import struct, sys, hashlib
def load(p):
    b=open(p,'rb').read()
    shoff,=struct.unpack_from('<Q',b,0x28); shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
    S=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
    def sb(i): s=S[i]; return b[s[4]:s[4]+s[5]]
    shstr=sb(shstrndx); name=lambda off,t: t[off:t.index(b'\0',off)].decode()
    symtab=[i for i,s in enumerate(S) if s[1]==2][0]; strtab=sb(S[symtab][6]); st=sb(symtab)
    syms=[struct.unpack_from('<IBBHQQ',st,o) for o in range(0,len(st),24)]
    rel={}
    for i,s in enumerate(S):
        if s[1] in (4,9):  # RELA/REL
            ent=24 if s[1]==4 else 16; d=sb(i); L=[]
            for o in range(0,len(d),ent):
                off,info=struct.unpack_from('<QQ',d,o); sy=syms[info>>32]
                L.append((off,info&0xffffffff,name(sy[0],strtab) or ('sec%d'%sy[3]) ))
            rel.setdefault(s[7],[]).extend(L)
    out={}
    for n,info,oth,shn,val,size in syms:
        if info&0xf!=2 or shn==0 or shn>=0xff00: continue
        nm=name(n,strtab); sec=sb(shn)[val:val+size]
        r=tuple((o-val,t,x) for o,t,x in rel.get(shn,[]) if val<=o<val+size)
        out[nm]=(sec,r)
    return out
if __name__=='__main__':
    A=load(sys.argv[1]); B=load(sys.argv[2])
    ch=[n for n in A if n in B and A[n]!=B[n]]; only=[n for n in A if n not in B]+[n for n in B if n not in A]
    print('funcs',len(A),len(B),'changed',len(ch),'unpaired',len(only))
    for n in ch[:int(sys.argv[3]) if len(sys.argv)>3 else 30]: print('  ',len(A[n][0]),len(B[n][0]),n[:150])
