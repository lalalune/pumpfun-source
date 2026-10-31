import struct,sys,collections
W={0x79:8,0x7b:8,0x7a:8,0x61:4,0x63:4,0x62:4,0x69:2,0x6b:2,0x6a:2,0x71:1,0x73:1,0x72:1}
def insns(b):
    i=0
    while i<len(b):
        op=b[i]; n=16 if op==0x18 else 8; yield i,b[i:i+n]; i+=n
def accesses(b):
    acc=collections.defaultdict(list); taken=set()
    for o,t in insns(b):
        op=t[0]; dst=t[1]&15; src=t[1]>>4; off=struct.unpack('<h',t[2:4])[0]
        if op in (0x79,0x61,0x69,0x71) and src==10: acc[-off].append((o,W[op],'ld'))
        elif op in (0x7b,0x7a,0x63,0x62,0x6b,0x6a,0x73,0x72) and dst==10: acc[-off].append((o,W[op],'st'))
        elif op==0x07 and False: pass
    # address taken: mov rX,r10 ; add rX,-imm
    L=list(insns(b))
    for k,(o,t) in enumerate(L):
        if t[0]==0xbf and (t[1]>>4)==10:
            d=t[1]&15
            for o2,t2 in L[k+1:k+3]:
                if t2[0]==0x07 and (t2[1]&15)==d: taken.add(-struct.unpack('<i',t2[4:8])[0]); break
    return acc,taken
def spill_slots(b,lo=0x800):
    acc,taken=accesses(b); tk=sorted(taken)
    res=[]
    for o,L in acc.items():
        if o<lo or o%8: continue
        if not all(w==8 for _,w,_ in L): continue
        # any other access overlapping (o-8,o+8) with different base
        bad=any(o2!=o and o2<o+8 and o2+w>o for o2,L2 in acc.items() for _,w,_ in L2)
        if bad or any(t<=o<t+8 or t==o for t in tk): continue
        res.append(o)
    return sorted(res)
if __name__=='__main__':
    for f in sys.argv[1:]:
        b=open(f,'rb').read(); s=spill_slots(b); print(f,len(s),hex(min(s)),hex(max(s)))
