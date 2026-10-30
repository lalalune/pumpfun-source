"""sretbound.py <orig.txt> <cand.txt> <cand.so|fn.bin> : pair the 33 sret-demotion slots by call layout position
(r1 = r10-X just before a call, X in the sret block), print the rank permutation, then rewrite the candidate's
r10 offsets in [X, X+16) to the original's slot and report the ratio bound (whole and region 2)."""
import sys,re,struct,difflib,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, tokio
def sites(p):
    L=[l.rstrip() for l in open(p) if l.strip()]; out=[]
    for k,l in enumerate(L):
        if ' call ' in l:
            for b in range(k-1,max(k-8,0),-1):
                m=re.search(r'add64 r1, -(0x[0-9a-f]+)$',L[b])
                if m and 'mov64 r1, r10' in L[b-1]:
                    x=int(m.group(1),16)
                    if 0x6a0<=x<=0x8e0: out.append(x)
                    break
    return out
o=sites(sys.argv[1]); c=sites(sys.argv[2]); assert len(o)==len(c)==33,(len(o),len(c))
ro={x:i for i,x in enumerate(sorted(o))}; rc={x:i for i,x in enumerate(sorted(c))}
print('pos orig_rank cand_rank'); print(' '.join(f'{ro[a]}/{rc[b]}' for a,b in zip(o,c)))
mp={b:a for a,b in zip(o,c)}
otok,w=co.orig_tokens(); ctok=tokio.toks(sys.argv[3])
def remap(t):
    b=bytearray(t); op=b[0]; dst=b[1]&15; src=b[1]>>4; cls=op&7
    def fix(neg):
        for X,Y in mp.items():
            if X-16<neg<=X: return Y-(X-neg)
        return None
    if cls==1 and src==10:
        off=-struct.unpack_from('<h',b,2)[0]; n=fix(off)
        if n is not None: struct.pack_into('<h',b,2,-n)
    elif cls in (2,3) and dst==10:
        off=-struct.unpack_from('<h',b,2)[0]; n=fix(off)
        if n is not None: struct.pack_into('<h',b,2,-n)
    elif op==0x07:
        imm=struct.unpack_from('<i',b,4)[0]
        if imm<0:
            n=fix(-imm)
            if n is not None: struct.pack_into('<i',b,4,-n)
    return bytes(b)
off=[];x=0
for t in otok: off.append(x); x+=len(t)
def score(ct):
    sm=difflib.SequenceMatcher(None,otok,ct,autojunk=False); r2=0
    for a,b,sz in sm.get_matching_blocks(): r2+=sum(1 for k in range(sz) if 0x23b0<=off[a+k]<0x4760)
    return round(sm.ratio(),5),r2
print('base',score(ctok)); print('sret-remapped bound',score([remap(t) for t in ctok]))
