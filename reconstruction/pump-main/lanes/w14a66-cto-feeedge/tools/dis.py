import struct,sys
OPS={0x07:'add',0x0f:'add',0x17:'sub',0x1f:'sub',0x27:'mul',0x2f:'mul',0x37:'div',0x47:'or',0x4f:'or',0x57:'and',0x5f:'and',0x67:'lsh',0x6f:'lsh',0x77:'rsh',0x7f:'rsh',0x87:'neg',0xa7:'xor',0xaf:'xor',0xb7:'mov',0xbf:'mov',0xc7:'arsh',
0x05:'ja',0x15:'jeq',0x1d:'jeq',0x25:'jgt',0x2d:'jgt',0x35:'jge',0x3d:'jge',0xa5:'jlt',0xad:'jlt',0xb5:'jle',0xbd:'jle',0x55:'jne',0x5d:'jne',0x45:'jset',0x65:'jsgt',0x6d:'jsgt',0x75:'jsge',0xc5:'jslt',0xd5:'jsle',
0x85:'call',0x95:'exit',0x18:'lddw',0x61:'ldxw',0x69:'ldxh',0x71:'ldxb',0x79:'ldxdw',0x62:'stw',0x6a:'sth',0x72:'stb',0x7a:'stdw',0x63:'stxw',0x6b:'stxh',0x73:'stxb',0x7b:'stxdw',0xb4:'mov32',0xbc:'mov32',0x04:'add32',0x0c:'add32',0x54:'and32',0x64:'lsh32',0x74:'rsh32',0x44:'or32'}
def dis(b):
    i=0;out=[]
    while i<len(b):
        op=b[i];d=b[i+1]&15;s=b[i+1]>>4;off=struct.unpack_from('<h',b,i+2)[0];imm=struct.unpack_from('<i',b,i+4)[0]
        n=16 if op==0x18 else 8
        m=OPS.get(op,hex(op))
        if op in (0x18,): t=f'{m} r{d}, {imm:#x}'
        elif op&7 in (4,7): t=f'{m} r{d}, '+(f'r{s}' if op&8 else f'{imm:#x}')
        elif op&7==5 and op not in (0x85,0x95): t=f'{m} r{d}, '+(f'r{s}' if op&8 else f'{imm:#x}')+f', {off:+#x}' if op!=0x05 else f'ja {off:+#x}'
        elif op==0x85: t=f'call {imm:#x}'
        elif op&7==1: t=f'{m} r{d}, [r{s}{off:+#x}]'
        elif op&7==3: t=f'{m} [r{d}{off:+#x}], r{s}'
        elif op&7==2: t=f'{m} [r{d}{off:+#x}], {imm:#x}'
        else: t=m
        out.append((i,t)); i+=n
    return out
if __name__=='__main__':
    for o,t in dis(open(sys.argv[1],'rb').read()): print(f'{o:#06x} {t}')
