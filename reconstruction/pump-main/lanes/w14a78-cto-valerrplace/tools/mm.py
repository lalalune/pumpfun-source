#!/usr/bin/env python3
"""mm.py <obj|.s>...: matched-token count M and jump-masked M (jM) vs original, plus bytes. .s files are assembled."""
import sys,os,difflib,subprocess,tempfile
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=G['orig_window']()
def toks(raw,jm):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]
        if jm and op&7==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
        out.append(bytes(t))
    return out
OT=[toks(O,0),toks(O,1)]
for p in sys.argv[1:]:
    if p.endswith('.s'):
        o=p[:-2]+'.o'; subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',p,'-o',o],check=True)
        p=o
    c=open(p,'rb').read() if p.endswith('.bin') else G['elf_fn'](p,G['KEEP'])
    r=[]
    for jm in (0,1):
        sm=difflib.SequenceMatcher(None,OT[jm],toks(c,jm),autojunk=False)
        r.append(sum(b.size for b in sm.get_matching_blocks()))
    n=len(toks(c,0)); print('%-28s bytes %d ntok %d M %d jM %d ratio %.5f'%(p.split('/')[-1],len(c),n,r[0],r[1],2*r[0]/(len(OT[0])+n)))
