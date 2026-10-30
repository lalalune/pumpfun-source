import sys,struct,os
sys.path.insert(0,os.path.dirname(__file__)); import oracle
raw=open(sys.argv[1],'rb').read(); lo,hi,d=int(sys.argv[2],16),int(sys.argv[3],16),int(sys.argv[4])
b=bytearray(raw); i=0
def f(neg): return lo<=neg<=hi
while i<len(b):
    op=b[i]; dst=b[i+1]&15; src=b[i+1]>>4; cls=op&7
    if cls==1 and src==10:
        o=-struct.unpack_from('<h',b,i+2)[0]
        if f(o): struct.pack_into('<h',b,i+2,-(o+d))
    elif cls in (2,3) and dst==10:
        o=-struct.unpack_from('<h',b,i+2)[0]
        if f(o): struct.pack_into('<h',b,i+2,-(o+d))
    elif op==0x07:
        imm=struct.unpack_from('<i',b,i+4)[0]
        if imm<0 and f(-imm): struct.pack_into('<i',b,i+4,imm-d)
    i+=16 if op==0x18 else 8
o=oracle.orig_window()
print(oracle.metric(raw,o)[0], oracle.metric(bytes(b),o)[0])
