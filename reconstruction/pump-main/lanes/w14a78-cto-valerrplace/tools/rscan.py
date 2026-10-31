#!/usr/bin/env python3
"""rscan.py <m.s> <out.jsonl> <first_block> <last_block> [-j N]: branch-aware single-block move scan (experiment only).
Like blkscan, but any block in [first,last] (glued fallthroughs included) may move to any position in that span:
relay.py semantics add 'ja' for broken fallthroughs and drop 'ja' to a new layout successor. Prints top moves by M and jM."""
import sys,os,json,difflib,subprocess,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/relay.py').read().split("if __name__")[0].replace("T=os.path.dirname(os.path.abspath(__file__))","T=%r"%T)
exec(src)
O=G['orig_window']()
def toks(raw,jm):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]
        if jm and op&7==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
        out.append(bytes(t))
    return out
OT=[toks(O,0),toks(O,1)]
a=sys.argv[1:]; S,OUTF,F,L=a[:4]; J=int(a[a.index('-j')+1]) if '-j' in a else 6
pre,blocks,post=parse(S); eb=explicit(blocks); names=[x[0] for x in eb]
lo,hi=names.index(F),names.index(L)
def M(order):
    t=emit(pre,[eb[i] for i in order],post)
    with tempfile.TemporaryDirectory() as d:
        open(d+'/a.s','w').write(t)
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',d+'/a.s','-o',d+'/a.o'],capture_output=True)
        if r.returncode: return None
        c=G['elf_fn'](d+'/a.o',G['KEEP'])
    res=[len(c)]
    for jm in (0,1):
        sm=difflib.SequenceMatcher(None,OT[jm],toks(c,jm),autojunk=False); res.append(sum(b.size for b in sm.get_matching_blocks()))
    return res
base=list(range(len(eb)))
def job(arg):
    i,p=arg; o=[k for k in base if k!=i]; o.insert(p,i)
    if o==base: return None
    return (names[i],names[o[p+1]] if p+1<len(o) else 'END',M(o))
if __name__=='__main__':
    b0=M(base); print('base',b0,flush=True)
    jobs=[(i,p) for i in range(lo,hi+1) for p in range(lo,hi+1)]
    with Pool(J) as pool: res=[r for r in pool.map(job,jobs,chunksize=8) if r and r[2]]
    with open(OUTF,'w') as f:
        for r in res: f.write(json.dumps({'blk':r[0],'before':r[1],'bytes':r[2][0],'M':r[2][1],'jM':r[2][2]})+'\n')
    res.sort(key=lambda r:-(r[2][1]))
    for r in res[:12]: print('M  ',r[0],'before',r[1],r[2],'dM %+d djM %+d'%(r[2][1]-b0[1],r[2][2]-b0[2]))
    res.sort(key=lambda r:-(r[2][2]))
    for r in res[:8]: print('jM ',r[0],'before',r[1],r[2],'dM %+d djM %+d'%(r[2][1]-b0[1],r[2][2]-b0[2]))
