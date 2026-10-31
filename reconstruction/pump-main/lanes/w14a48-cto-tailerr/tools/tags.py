import sys,struct
raw=open(sys.argv[1],'rb').read()
ins=[];i=0
while i<len(raw):
    op=raw[i]; n=16 if op==0x18 else 8
    _,regs,off,imm=struct.unpack_from('<BBhi',raw,i); ins.append((i,op,regs&15,regs>>4,off,imm)); i+=n
for k,(o,op,d,s,off,imm) in enumerate(ins):
    if op in(0x55,0x15) and d==7 and imm==2:
        x=''
        if k+1<len(ins) and ins[k+1][1]==5: x=' ; ja ->%x'%(ins[k+1][0]+8+ins[k+1][4]*8)
        print('%x %s r7,2 -> %x%s'%(o,'jne' if op==0x55 else 'jeq',o+8+off*8,x))
