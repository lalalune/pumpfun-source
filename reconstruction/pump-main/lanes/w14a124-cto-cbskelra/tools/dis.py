#!/usr/bin/env python3
"""dis.py <fn.bin|orig> [start_hex] [count]: minimal sBPF disassembly of a function blob."""
import sys,struct,os
def orig():
    sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
    from score import original_windows
    for w in original_windows():
        if w['start']==0x22a10: return w['raw']
ALU={0:'add',1:'sub',2:'mul',3:'div',4:'or',5:'and',6:'lsh',7:'rsh',8:'neg',9:'mod',10:'xor',11:'mov',12:'arsh'}
JMP={0:'ja',1:'jeq',2:'jgt',3:'jge',4:'jset',5:'jne',6:'jsgt',7:'jsge',10:'jlt',11:'jle',12:'jslt',13:'jsle'}
SZ={0x18:'w',0x10:'h',0x08:'b',0x00:'w',0x18:'dw'}
def d(b):
    out=[];i=0
    while i<len(b):
        op=b[i]; rg=b[i+1]; dst=rg&15; src=rg>>4; off=struct.unpack_from('<h',b,i+2)[0]; imm=struct.unpack_from('<i',b,i+4)[0]
        cls=op&7; n=8
        if op==0x18: imm2=struct.unpack_from('<I',b,i+12)[0]; s=f'lddw r{dst}, {hex((imm2<<32)|(imm&0xffffffff))}'; n=16
        elif op==0x85: s=f'call {hex(imm&0xffffffff)}'
        elif op==0x95: s='exit'
        elif cls in (4,7):
            nm=ALU.get(op>>4,'?')+('64' if cls==7 else '32')
            s=f'{nm} r{dst}, '+(f'r{src}' if op&8 else f'{imm}')
        elif cls==5:
            nm=JMP.get(op>>4,'?'); tgt=i+8+off*8
            s=f'{nm} r{dst}, '+((f'r{src}' if op&8 else f'{imm}')+', ' if nm!='ja' else '')+f'{tgt:x}'
        elif cls==1: s=f'ldx{["w","h","b","dw"][(op>>3)&3]} r{dst}, [r{src}{off:+#x}]'
        elif cls==3: s=f'stx{["w","h","b","dw"][(op>>3)&3]} [r{dst}{off:+#x}], r{src}'
        elif cls==2: s=f'st{["w","h","b","dw"][(op>>3)&3]} [r{dst}{off:+#x}], {imm}'
        else: s=f'?{op:02x}'
        out.append((i,s)); i+=n
    return out
if __name__=='__main__':
    p=sys.argv[1]; b=orig() if p=='orig' else open(p,'rb').read()
    st=int(sys.argv[2],16) if len(sys.argv)>2 else 0; c=int(sys.argv[3]) if len(sys.argv)>3 else 60
    k=0
    for o,s in d(b):
        if o>=st and k<c: print(f'{o:05x} {s}'); k+=1
