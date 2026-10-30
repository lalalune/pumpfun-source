#!/usr/bin/env python3
# llcsh.py IN.ll [--cmp unstripped.so] : llc swap_hop IR, report bytes + exactish/opregs vs original; optional equality vs a built candidate
import sys,os,subprocess,difflib,tempfile
B=os.environ.get('LLCDIR',os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin'))
OB=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src=sys.argv[1]; d=tempfile.mkdtemp(dir=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-inline/tmp'))
r=subprocess.run([B+'/llc','-O3','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',src,'-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
secs=subprocess.run([OB+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
sec=next(l.split()[1] for l in secs.splitlines() if '.text.' in l and '8swap_hop17h' in l and '.rel' not in l)
subprocess.run([OB+'/llvm-objcopy','-O','binary','--only-section='+sec,d+'/m.o',d+'/m.bin'],check=True)
raw=open(d+'/m.bin','rb').read()
P=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-inline/orig_raw.bin')
oraw=open(P,'rb').read()
def toks(raw):
    i=0;out=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; t=raw[i:i+k]
        if t[0]==0x85: t=t[:2]
        elif t[0]==0x18: t=t[:2]
        elif t[0]&7==5 and t[0]!=0x85 and t[0]!=0x95: t=t[:2]+t[4:8]
        out.append(t); i+=k
    return out
o=toks(oraw); c=toks(raw)
def R(f): return difflib.SequenceMatcher(None,[f(x) for x in o],[f(x) for x in c],autojunk=False).ratio()
print(f'{os.path.basename(os.path.dirname(src))}: bytes {len(raw)} exactish {R(lambda x:x):.4f} opregs {R(lambda x:x[:2]):.4f}')
if '--cmp' in sys.argv:
    import subprocess as sp
    so=sys.argv[sys.argv.index('--cmp')+1]
    sym=sp.run([OB+'/llvm-readelf','-sW',so],capture_output=True,text=True).stdout
    for l in sym.splitlines():
        if '8swap_hop17h' in l and 'FUNC' in l:
            f=l.split(); addr=int(f[1],16); size=int(f[2]); break
    sh=sp.run([OB+'/llvm-readelf','-SW',so],capture_output=True,text=True).stdout
    for l in sh.splitlines():
        if ' .text ' in l:
            f=l.split(); i=f.index('.text'); va=int(f[i+2],16); off=int(f[i+3],16)
    blob=open(so,'rb').read()[off+addr-va:off+addr-va+size]
    print('candidate tok-equal:', toks(blob)==c, len(blob), len(raw))
