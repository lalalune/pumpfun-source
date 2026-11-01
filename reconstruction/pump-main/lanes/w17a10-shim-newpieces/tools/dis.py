#!/usr/bin/env python3
"""dis.py <fn.bin> : disassemble a raw admin_cto function blob (offsets from 0) using a minimal sBPF decoder."""
import sys,struct
R=lambda n:f'r{n}'
ALU={0x0:'add',0x1:'sub',0x2:'mul',0x3:'div',0x4:'or',0x5:'and',0x6:'lsh',0x7:'rsh',0x8:'neg',0x9:'mod',0xa:'xor',0xb:'mov',0xc:'arsh',0xd:'end'}
JMP={0x0:'ja',0x1:'jeq',0x2:'jgt',0x3:'jge',0x4:'jset',0x5:'jne',0x6:'jsgt',0x7:'jsge',0x8:'call',0x9:'exit',0xa:'jlt',0xb:'jle',0xc:'jslt',0xd:'jsle'}
SZ={0x18:'dw',0x00:'w',0x08:'h',0x10:'b'}
def dis(b):
    i=0;out=[]
    while i<len(b):
        op,regs,off,imm=struct.unpack_from('<BBhi',b,i); dst=regs&0xf; src=regs>>4
        cls=op&7; n=8
        if op==0x18:
            imm2=struct.unpack_from('<i',b,i+12)[0]; s=f'lddw {R(dst)}, {hex((imm2<<32)|(imm&0xffffffff))}'; n=16
        elif cls in (4,7):
            a=ALU.get(op>>4,'?')+('64' if cls==7 else '32')
            s=f'{a} {R(dst)}, '+(R(src) if op&8 else hex(imm))
        elif cls==5:
            j=JMP.get(op>>4,'?')
            if j=='call': s=f'call {hex(imm)}' if src==0 else f'call {hex(imm)} (int)'
            elif j=='exit': s='exit'
            elif j=='ja': s=f'ja {off:+#x}'
            else: s=f'{j} {R(dst)}, '+(R(src) if op&8 else hex(imm))+f', {off:+#x}'
        elif cls==1: s=f'ldx{SZ[op&0x18]} {R(dst)}, [{R(src)} {"+" if off>=0 else "-"} {hex(abs(off))}]'
        elif cls==3: s=f'stx{SZ[op&0x18]} [{R(dst)} {"+" if off>=0 else "-"} {hex(abs(off))}], {R(src)}'
        elif cls==2: s=f'st{SZ[op&0x18]} [{R(dst)} {"+" if off>=0 else "-"} {hex(abs(off))}], {hex(imm)}'
        else: s=f'?? {op:#x}'
        out.append((i,s)); i+=n
    return out
if __name__=='__main__':
    for o,s in dis(open(sys.argv[1],'rb').read()): print(hex(o),s)
