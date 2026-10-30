#!/usr/bin/env python3
"""pe.py <name> <edits.py> [--base rx/base/m.ll] [--dbg]: post-opt IR edit -> llc -> ratio/slots/bytes + fm/rm + per-0x800 fm/raw chunk deltas vs base."""
import sys,os,subprocess,json,runpy,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); R=os.path.dirname(T)
a=sys.argv[1:]; name=a.pop(0); ed=a.pop(0) if a and not a[0].startswith('--') else None; base=R+'/rx/base/m.ll'; dbg=False
while a:
    x=a.pop(0)
    if x=='--base': base=a.pop(0)
    elif x=='--dbg': dbg=True
d=R+'/pe/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if ed:
    for e in runpy.run_path(ed)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
cand=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](cand,g['orig_window']())
dis=subprocess.run(['bash',T+'/dis.sh',d+'/m.o'],capture_output=True,text=True).stdout; open(d+'/m.dis','w').write(dis)
import absratio as A
O=[x for x in A.O]
def hits(lines,regs):
    on=[A.norm(x,regs) for x in O]; cn=[A.norm(l.split(None,1)[1],regs) for l in lines if len(l.split(None,1))>1]
    sm=difflib.SequenceMatcher(None,on,cn,autojunk=False); h=[0]*len(on)
    for b in sm.get_matching_blocks():
        for k in range(b.size): h[b.a+k]=1
    return h
OA=[int(l.split()[0],16) for l in open(R+'/orig.rel') if len(l.split(None,1))>1]
def raw_hits(lines):
    on=[A.norm(x,False).replace('r10-X','') for x in O]
    import re
    def rn(s): s=re.sub(r'\s+<[^>]*>','',s.strip()); s=re.sub(r'[+-]0x[0-9a-f]+$','J',s) if s.startswith('j') else s; return 'call' if s.startswith('call') else re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    on=[rn(x) for x in O]; cn=[rn(l.split(None,1)[1]) for l in lines if len(l.split(None,1))>1]
    sm=difflib.SequenceMatcher(None,on,cn,autojunk=False); h=[0]*len(on)
    for b in sm.get_matching_blocks():
        for k in range(b.size): h[b.a+k]=1
    return h
L=dis.strip().split('\n'); hf=hits(L,False); hr=hits(L,True); hw=raw_hits(L)
def bins(h):
    b={}
    for i,v in enumerate(h): b[OA[i]//0x800*0x800]=b.get(OA[i]//0x800*0x800,0)+v
    return b
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots':sd,'fm':sum(hf),'rm':sum(hr),'raw':sum(hw)}
bf,br,bw=bins(hf),bins(hr),bins(hw)
res['chunks']={hex(k):[bw[k],bf[k],br[k]] for k in sorted(bf) if 0x2000<=k<0x3800}
json.dump({'fm':bf,'rm':br,'raw':bw},open(d+'/bins.json','w'))
print(json.dumps(res))
