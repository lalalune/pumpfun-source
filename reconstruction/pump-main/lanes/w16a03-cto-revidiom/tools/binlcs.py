"""binlcs.py <rxname|so>...: LCS of a candidate fn.bin vs the original under masks (exact, j, r+j, f+j, rfj)."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import shape,runs,lcsm
from lcsm import tok,lcs
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'w15a11'))
import struct
def dis_bin(b):
    # decode via llvm-objdump-like minimal decoder from w15a11 dis.py
    sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom/tools/w15a11')
    import importlib; D=importlib.import_module('dis') if False else None
    out=[]
    ALU={0:'add',1:'sub',2:'mul',3:'div',4:'or',5:'and',6:'lsh',7:'rsh',8:'neg',9:'mod',10:'xor',11:'mov',12:'arsh'}
    JMP={0:'ja',1:'jeq',2:'jgt',3:'jge',4:'jset',5:'jne',6:'jsgt',7:'jsge',10:'jlt',11:'jle',12:'jslt',13:'jsle'}
    i=0
    while i<len(b):
        op=b[i]; rg=b[i+1]; dst=rg&15; src=rg>>4; off=struct.unpack_from('<h',b,i+2)[0]; imm=struct.unpack_from('<i',b,i+4)[0]; cls=op&7; n=8
        if op==0x18: s=f'lddw r{dst}, 0x0'; n=16
        elif op==0x85: s=f'call 0x0'
        elif op==0x95: s='exit'
        elif cls in (4,7):
            nm=ALU.get(op>>4,'?')+('64' if cls==7 else '32'); s=f'{nm} r{dst}, '+(f'r{src}' if op&8 else (f'-{-imm:#x}' if imm<0 else f'{imm:#x}'))
        elif cls==5:
            nm=JMP.get(op>>4,'?'); s=(f'{nm} r{dst}, '+((f'r{src}' if op&8 else f'{imm:#x}')+', ') if nm!='ja' else 'ja ')+(f'+{off:#x}' if off>=0 else f'-{-off:#x}')
        elif cls==1: s=f'ldx{["w","h","b","dw"][(op>>3)&3]} r{dst}, [r{src} '+(f'+ {off:#x}]' if off>=0 else f'- {-off:#x}]')
        elif cls==3: s=f'stx{["w","h","b","dw"][(op>>3)&3]} [r{dst} '+(f'+ {off:#x}]' if off>=0 else f'- {-off:#x}]')+f', r{src}'
        elif cls==2: s=f'st{["w","h","b","dw"][(op>>3)&3]} [r{dst} '+(f'+ {off:#x}]' if off>=0 else f'- {-off:#x}]')+f', {imm:#x}'
        else: s=f'?{op:02x}'
        out.append((i,s,shape.parse(s))); i+=n
    return out
O=runs.cto_insns('orig')
OP=[(a,t,shape.parse(re.sub(r'call .*','call 0x0',re.sub(r'lddw (r\d+), .*',r'lddw \1, 0x0',t)))) for a,t,p in O] if False else None
import re
def norm_orig():
    out=[]
    for a,t,p in O:
        t2=re.sub(r'^lddw (r\d+), .*$',r'lddw \1, 0x0',t); t2=re.sub(r'^call .*$','call 0x0',t2)
        out.append((a,t2,shape.parse(t2)))
    return out
ON=norm_orig()
for name in sys.argv[1:]:
    p=name if name.endswith('.bin') else f'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom/rx/{name}/fn.bin'
    C=dis_bin(open(p,'rb').read())
    row=[]
    for r,f,j,nm in [(1,1,1,'exact'),(1,1,0,'j'),(0,1,0,'rj'),(1,0,0,'fj'),(0,0,0,'rfj')]:
        A=[tok(x[2],r,f,j) for x in ON]; B=[tok(x[2],r,f,j) for x in C]
        row.append(f'{nm}:{lcs(A,B)}')
    print(name,len(C),' '.join(row))
