#!/usr/bin/env python3
"""wr.py <m.ll|fn.bin> [...]: llc (if .ll) and report ratio, bytes, slots, M (matched orig tokens, whole difflib),
Mw (matched in orig wallet [0x5c40,0x6b08)), Mpos (positional equal slots in wallet), do_coin register guess."""
import sys,os,subprocess,difflib,tempfile,re,json
T=os.path.dirname(os.path.abspath(__file__))
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
ORIG=g['orig_window']()
def fn(p):
    if p.endswith('.bin'): return open(p,'rb').read()
    if p.endswith('.so') or p.endswith('.o'): return g['elf_fn'](p,g['KEEP'])
    o=tempfile.mktemp(suffix='.o',dir=os.path.dirname(os.path.abspath(p)))
    r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',o],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
    b=g['elf_fn'](o,g['KEEP']); os.remove(o); return b
def rep(p):
    c=fn(p); o=g['mask'](ORIG); k=g['mask'](c)
    sm=difflib.SequenceMatcher(None,o,k,autojunk=False)
    M=0; Mw=0; lo,hi=0x5c40//8,0x6b08//8
    for a,b,n in sm.get_matching_blocks():
        M+=n; Mw+=max(0,min(a+n,hi)-max(a,lo))
    pos=sum(1 for i in range(lo,min(hi,len(k),len(o))) if o[i]==k[i])
    # do_coin reg: in orig the wallet has 'mov64 r8, 0x0' right before 'mov64 r6, 0x0; jne r0,0,+1'
    reg=None
    for i in range(lo-8,min(hi,len(k)-2)):
        ins=c[i*8:i*8+8]
        if ins[0]==0xb7 and ins[1]&0xf==6 and int.from_bytes(ins[4:8],'little')==0:
            prev=c[(i-1)*8:(i-1)*8+8]
            reg='r%d'%(prev[1]&0xf) if prev[0]==0xb7 else ('spill' if prev[0]==0x7b else '?'); break
    _,sd=g['metric'](c,ORIG)
    return {'f':p,'ratio':round(sm.ratio(),5),'bytes':len(c),'slots':sd,'M':M,'Mw':Mw,'Mpos':pos,'docoin':reg}
for p in sys.argv[1:]: print(json.dumps(rep(p)))
