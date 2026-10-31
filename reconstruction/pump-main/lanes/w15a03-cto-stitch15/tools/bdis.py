#!/usr/bin/env python3
"""bdis.py: minimal SBF decoder for fn.bin blobs (experiment only). dis(raw)->[(off,text)]; diff A B [--lo --hi] prints a
difflib hunk listing of B-vs-A over B offsets [lo,hi)."""
import struct,sys,difflib
ALU={0:'add',1:'sub',2:'mul',3:'div',4:'or',5:'and',6:'lsh',7:'rsh',8:'neg',9:'mod',10:'xor',11:'mov',12:'arsh',13:'end'}
JMP={0:'ja',1:'jeq',2:'jgt',3:'jge',4:'jset',5:'jne',6:'jsgt',7:'jsge',8:'call',9:'exit',10:'jlt',11:'jle',12:'jslt',13:'jsle'}
SZ={0:'w',1:'h',2:'b',3:'dw'}
def dis(raw):
    i=0;out=[]
    while i<len(raw):
        op,r,off,imm=struct.unpack_from('<BBhi',raw,i); dst=r&15; src=r>>4; cl=op&7; n=8
        if op==0x18:
            imm2=struct.unpack_from('<i',raw,i+12)[0]; t=f'lddw r{dst}, {(imm&0xffffffff)|(imm2<<32):#x}'; n=16
        elif cl in (4,7):
            o=ALU.get(op>>4,'?')+('64' if cl==7 else '32'); t=f'{o} r{dst}, '+(f'r{src}' if op&8 else f'{imm:#x}')
        elif cl in (5,6):
            o=JMP.get(op>>4,'?')
            if o=='call': t=f'call {imm:#x}'
            elif o=='exit': t='exit'
            elif o=='ja': t=f'ja {off:+#x}'
            else: t=f'{o} r{dst}, '+(f'r{src}' if op&8 else f'{imm:#x}')+f', {off:+#x}'
        elif cl==1: t=f'ldx{SZ[(op>>3)&3]} r{dst}, [r{src}{off:+#x}]'
        elif cl==3: t=f'stx{SZ[(op>>3)&3]} [r{dst}{off:+#x}], r{src}'
        elif cl==2: t=f'st{SZ[(op>>3)&3]} [r{dst}{off:+#x}], {imm:#x}'
        else: t=f'?{op:#x}'
        out.append((i,t)); i+=n
    return out
def norm(t):
    import re
    t=re.sub(r'call 0x[0-9a-f]+','call X',t); t=re.sub(r', [+-]0x[0-9a-f]+$',', J',t); t=re.sub(r'^ja .*','ja J',t)
    return t
if __name__=='__main__':
    a=sys.argv[1:]; lo,hi=0,1<<30
    if '--lo' in a: i=a.index('--lo'); lo=int(a[i+1],16); del a[i:i+2]
    if '--hi' in a: i=a.index('--hi'); hi=int(a[i+1],16); del a[i:i+2]
    A=dis(open(a[0],'rb').read()); B=dis(open(a[1],'rb').read())
    sm=difflib.SequenceMatcher(None,[norm(x[1]) for x in A],[norm(x[1]) for x in B],autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal': continue
        if j1<len(B) and not (lo<=B[min(j1,len(B)-1)][0]<hi): continue
        print(f'@@ A {A[i1][0] if i1<len(A) else -1:#x} B {B[j1][0] if j1<len(B) else -1:#x} {tag}')
        for k in range(i1,i2): print(f'-{A[k][0]:#7x} {A[k][1]}')
        for k in range(j1,j2): print(f'+{B[k][0]:#7x} {B[k][1]}')
