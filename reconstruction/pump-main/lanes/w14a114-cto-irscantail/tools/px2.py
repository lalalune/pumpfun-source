#!/usr/bin/env python3
"""px2.py m.ll: px.py + matched-token total M and per-0x400 orig-chunk M (oracle only)."""
import sys,os,subprocess,json,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
sys.path.insert(0,T); import eseq
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
_O=None
def orig():
    global _O
    if _O is None:
        p=T+'/orig.bin'
        if os.path.exists(p): _O=open(p,'rb').read()
        else: _O=G['orig_window'](); open(p,'wb').write(_O)
    return _O
def score_bin(c):
    O=orig(); o=G['mask'](O); cc=G['mask'](c)
    sm=difflib.SequenceMatcher(None,o,cc,autojunk=False)
    mb=sm.get_matching_blocks(); M=sum(m.size for m in mb)
    r=2*M/(len(o)+len(cc))
    ob=b''.join(o); cb=b''.join(cc)
    sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
    off=[];x=0
    for t in o: off.append(x); x+=len(t)
    ch={}
    for m in mb:
        for k in range(m.a,m.a+m.size):
            ch[off[k]//0x400]=ch.get(off[k]//0x400,0)+1
    return {'ratio':round(r,5),'M':M,'bytes':len(c),'slots':sd,'ch':ch}
def run(f,*a):
    b=f[:-3]
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f,'-filetype=obj','-o',b+'.o',*a],capture_output=True,text=True)
    if r.returncode: return {'err':r.stderr[-500:]}
    c=G['elf_fn'](b+'.o',G['KEEP']); os.remove(b+'.o')
    d=score_bin(c); d['es']=' '.join(map(str,eseq.seq(c)[7:11])); return d
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],*sys.argv[2:])))
