import sys,struct,collections
def offs(b):
    c=collections.Counter(); i=0
    while i<len(b):
        op=b[i]; cls=op&7; reg=b[i+1]; d=reg&15; s=reg>>4; off=struct.unpack_from('<h',b,i+2)[0]
        if cls in (1,) and s==10: c[off]+=1
        if cls in (2,3) and d==10: c[off]+=1
        i+=16 if op==0x18 else 8
    return c
if __name__=='__main__':
    a=offs(open(sys.argv[1],'rb').read()); b=offs(open(sys.argv[2],'rb').read())
    ks=sorted(set(a)|set(b))
    print('min',min(a),min(b),'nslots',len(a),len(b))
    for k in ks:
        if a.get(k,0)!=b.get(k,0): print(hex(k&0xffff) if k>=0 else '-'+hex(-k), a.get(k,0), b.get(k,0))
