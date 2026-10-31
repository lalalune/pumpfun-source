import sys,struct
b=open(sys.argv[1],'rb').read(); lo=int(sys.argv[2],0); hi=int(sys.argv[3],0); i=0
while i<len(b):
    op=b[i]; d=b[i+1]&15; s=b[i+1]>>4; off,imm=struct.unpack_from('<hi',b,i+2); n=16 if op==0x18 else 8
    if lo<=i<hi: print('%04x %02x %d %d %d %d'%(i,op,d,s,off,imm))
    i+=n
