import struct,re
def get(path,pat=r'admin_cto7execute'):
    b=open(path,'rb').read()
    shoff=struct.unpack_from('<Q',b,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
    sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
    for i,s in enumerate(sh):
        if s[1]==2:
            strtab=sh[s[6]]; so=strtab[4]
            for j in range(s[5]//24):
                nm,info,oth,shndx,val,size=struct.unpack_from('<IBBHQQ',b,s[4]+j*24)
                name=b[so+nm:b.index(b'\0',so+nm)].decode()
                if re.search(pat,name) and (info&0xf)==2:
                    sec=sh[shndx]; off=sec[4]+val-(sec[3] if path.endswith('.so') else 0)
                    return b[off:off+size]
