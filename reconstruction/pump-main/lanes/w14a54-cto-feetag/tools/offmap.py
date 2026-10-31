import sys,struct,difflib,collections
def toks(b):
    r=[];i=0
    while i<len(b):
        op=b[i];n=16 if op==0x18 else 8;x=bytearray(b[i:i+n]);cls=op&7;d=x[1]&15;s=x[1]>>4
        off=None
        if (cls==1 and s==10) or (cls in(2,3) and d==10): off=-struct.unpack_from('<h',x,2)[0]; x[2:4]=b'\0\0'
        if op==0x85: x[1]&=0x0f; x[4:8]=b'\0'*4
        if op==0x18: x[4:8]=b'\0'*4; x[12:16]=b'\0'*4
        r.append((bytes(x),off,i));i+=n
    return r
A=toks(open(sys.argv[1],'rb').read()); B=toks(open(sys.argv[2],'rb').read())
sm=difflib.SequenceMatcher(None,[a[0] for a in A],[b[0] for b in B],autojunk=False)
c=collections.Counter(); ex=collections.defaultdict(list)
for m in sm.get_matching_blocks():
    for k in range(m.size):
        a=A[m.a+k];b=B[m.b+k]
        if a[1] is not None and a[1]!=b[1]: c[(a[1],b[1])]+=1; ex[(a[1],b[1])].append(a[2])
for (x,y),n in sorted(c.items(),key=lambda z:-z[1])[:int(sys.argv[3]) if len(sys.argv)>3 else 40]:
    print(hex(x),'->',hex(y),n,'at',','.join(hex(e) for e in ex[(x,y)][:4]))
print('total remapped',sum(c.values()))
