import sys,struct
b=open(sys.argv[1],'rb').read(); i=0
while i<len(b):
    op,r,off,imm=struct.unpack_from('<BBhi',b,i)
    print('%04x %02x %d %d %d %d'%(i,op,r&15,r>>4,off,imm)); i+=16 if op==0x18 else 8
