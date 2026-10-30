import sys,struct,re
for path in sys.argv[1:]:
    b=open(path,'rb').read()
    shoff=struct.unpack_from('<Q',b,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
    sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
    out=[]
    for i,s in enumerate(sh):
        if s[1]==2:
            so=sh[s[6]][4]
            for j in range(s[5]//24):
                nm,info,oth,shndx,val,size=struct.unpack_from('<IBBHQQ',b,s[4]+j*24)
                name=b[so+nm:b.index(b'\0',so+nm)].decode()
                if (info&0xf)==2 and 'admin_cto' in name: out.append((size,name[-60:]))
    print(path,out)
