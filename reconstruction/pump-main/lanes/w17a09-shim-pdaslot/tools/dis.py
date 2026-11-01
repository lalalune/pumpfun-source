#!/usr/bin/env python3
"""dis.py <fn.bin|name> [--range a-b] [--full]: disassemble an fx fn.bin and diff it against the original admin_cto window (masked tokens)."""
import sys,os,struct,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
ALU={0:'add',1:'sub',2:'mul',3:'div',4:'or',5:'and',6:'lsh',7:'rsh',8:'neg',9:'mod',10:'xor',11:'mov',12:'arsh',13:'end'}
JMP={0:'ja',1:'jeq',2:'jgt',3:'jge',4:'jset',5:'jne',6:'jsgt',7:'jsge',8:'call',9:'callx',10:'exit',0xa:'jlt',0xb:'jle',0xc:'jslt',0xd:'jsle'}
JMP={0x0:'ja',0x1:'jeq',0x2:'jgt',0x3:'jge',0x4:'jset',0x5:'jne',0x6:'jsgt',0x7:'jsge',0x8:'call',0x9:'exit',0xa:'jlt',0xb:'jle',0xc:'jslt',0xd:'jsle'}
SZ={0:'w',8:'h',0x10:'b',0x18:'dw'}
def h(x): return ('-' if x<0 else '')+hex(abs(x))
def dec(b):
    op=b[0]; dst=b[1]&15; src=b[1]>>4; off=struct.unpack_from('<h',b,2)[0]; imm=struct.unpack_from('<i',b,4)[0]
    cls=op&7
    if op==0x18: imm64=imm&0xffffffff|(struct.unpack_from('<I',b,12)[0]<<32); return f'lddw r{dst}, {hex(imm64)}'
    if cls==1: return f'ldx{SZ[op&0x18]} r{dst}, [r{src} {"+" if off>=0 else "-"} {hex(abs(off))}]'
    if cls==2: return f'st{SZ[op&0x18]} [r{dst} {"+" if off>=0 else "-"} {hex(abs(off))}], {h(imm)}'
    if cls==3: return f'stx{SZ[op&0x18]} [r{dst} {"+" if off>=0 else "-"} {hex(abs(off))}], r{src}'
    if cls in (4,7):
        nm=ALU.get(op>>4,'?')+('64' if cls==7 else '32')
        if op>>4==8: return f'{nm} r{dst}'
        return f'{nm} r{dst}, '+(f'r{src}' if op&8 else h(imm))
    if cls==5:
        k=op>>4; nm=JMP.get(k,'?')
        if nm=='exit': return 'exit'
        if nm=='call': return f'call {h(imm)}' if src==0 else f'call +{h(imm)}'
        if nm=='ja': return f'ja {"+" if off>=0 else ""}{h(off)}'
        return f'{nm} r{dst}, '+(f'r{src}' if op&8 else h(imm))+f', {"+" if off>=0 else ""}{h(off)}'
    return f'?? {b.hex()}'
def split(raw):
    i=0;o=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; o.append((i,raw[i:i+n])); i+=n
    return o
def main():
    a=sys.argv[1:]; p=a[0]
    if not os.path.exists(p): p=f'{OUT}/fx/{p}/fn.bin'
    raw=open(p,'rb').read(); ow=oracle.orig_window()
    oi=split(ow); ci=split(raw)
    ot=oracle.mask(ow); ct=oracle.mask(raw)
    lo,hi=0,1<<30
    if '--range' in a:
        r=a[a.index('--range')+1].split('-'); lo,hi=int(r[0],16),int(r[1],16)
    full='--full' in a
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    M=sum(x.size for x in sm.get_matching_blocks()); print(f'M {M} bytes {len(raw)} ratio {2*M/(len(ot)+len(ct)):.5f}')
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if i2<=i1 and not (lo<= (oi[i1][0] if i1<len(oi) else 1<<29) <hi): 
            if not (j1<len(ci) and lo<=ci[j1][0]<hi): continue
        if i1<len(oi) and oi[i1][0]>=hi and (j1>=len(ci) or ci[j1][0]>=hi): continue
        if i2>0 and i2<=len(oi) and oi[i2-1][0]<lo and (j2==0 or ci[j2-1][0]<lo): continue
        if tag=='equal':
            if not full and i2-i1>4:
                for k in range(2): print(f'  {oi[i1+k][0]:#06x} {ci[j1+k][0]:#06x}  {dec(ci[j1+k][1])}')
                print(f'  ... {i2-i1-4} equal ...')
                for k in range(i2-i1-2,i2-i1): print(f'  {oi[i1+k][0]:#06x} {ci[j1+k][0]:#06x}  {dec(ci[j1+k][1])}')
            else:
                for k in range(i2-i1): print(f'  {oi[i1+k][0]:#06x} {ci[j1+k][0]:#06x}  {dec(ci[j1+k][1])}')
            continue
        for k in range(i1,i2): print(f'- {oi[k][0]:#06x}         {dec(oi[k][1])}')
        for k in range(j1,j2): print(f'+        {ci[k][0]:#06x}  {dec(ci[k][1])}')
if __name__=="__main__": main()
