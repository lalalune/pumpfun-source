import sys,struct
def seq(b):
    r=[];i=0
    while i<len(b):
        op=b[i]
        if op in (0x62,0x7a,0xb7):
            imm=struct.unpack_from('<i',b,i+4)[0]
            if op==0x62 and 280<=imm<=780: r.append(imm)
        i+=16 if op==0x18 else 8
    return r
if __name__=='__main__':
 for f in sys.argv[1:]:
    s=seq(open(f,'rb').read()); print(f.split('/')[-2], ' '.join(map(str,s[:16])))
