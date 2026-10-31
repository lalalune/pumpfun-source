#!/usr/bin/env python3
"""px.py m.ll [llc args]: post-opt module -> llc (as rx.py) -> ratio/slots/bytes/fm/sk/errseq. Oracle only."""
import sys,os,subprocess,json,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
sys.path.insert(0,T); import eseq
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
f=sys.argv[1]; b=f[:-3]
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f,'-filetype=obj','-o',b+'.o',*sys.argv[2:]],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
c=G['elf_fn'](b+'.o',G['KEEP']); open(b+'.bin','wb').write(c); os.remove(b+'.o')
O=G['orig_window'](); rr,sd=G['metric'](c,O)
def toks(raw,fr=False,rg=False):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]; cls=op&7; dst=t[1]&15; s=t[1]>>4
        if fr and cls in (1,2,3) and (dst==10 or s==10): t[2:4]=b'\0\0'
        if rg: t[1]=0
        out.append(bytes(t))
    return out
fm=difflib.SequenceMatcher(None,toks(O,1),toks(c,1),autojunk=False).ratio()
sk=difflib.SequenceMatcher(None,toks(O,1,1),toks(c,1,1),autojunk=False).ratio()
print(json.dumps({'f':os.path.basename(b),'ratio':round(rr,5),'bytes':len(c),'slots':sd,'fm':round(fm,5),'sk':round(sk,5),'err':' '.join(map(str,eseq.seq(c)[7:11]))}))
