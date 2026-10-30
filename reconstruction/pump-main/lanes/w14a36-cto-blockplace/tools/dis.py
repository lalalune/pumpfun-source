import struct,sys
def text_bytes(path):
    d=open(path,'rb').read()
    shoff=struct.unpack_from('<Q',d,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',d,0x3a)
    secs=[struct.unpack_from('<IIQQQQIIQQ',d,shoff+i*shentsize) for i in range(shnum)]
    strtab=secs[shstrndx]
    def nm(o): s=d[strtab[4]+o:]; return s[:s.index(b'\0')].decode()
    for s in secs:
        if nm(s[0])=='.text': return d,s[3],s[4],s[5]
def calls(path,start=0x22a10,size=27400):
    d,addr,off,sz=text_bytes(path)
    r=[]
    for pc in range(start,start+size,8):
        b=d[off+pc-addr:off+pc-addr+8]
        if b[0]==0x85:
            imm=struct.unpack_from('<i',b,4)[0]; src=b[1]>>4
            r.append((pc-start,pc+8+imm*8 if src==1 or True else imm,imm,src))
    return r
if __name__=='__main__':
    for x in calls(sys.argv[1]): print(hex(x[0]),hex(x[1]),hex(x[2]),x[3])
