#!/usr/bin/env python3
"""fx.py <name> <m.ll> [edits.py]: post-opt IR (+optional EDITS), llc (LLC env or SDK; RAPRIO_* passed through), score.
Prints ratio, bytes, slots, M (matched tokens) and M_oo_tcf (orig 0x2600-0x3c00 unmatched). Experiment only."""
import sys,os,subprocess,runpy,json,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
OUT=os.path.dirname(T); SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; name,base=a[0],a[1]; ed=a[2] if len(a)>2 else None
d=OUT+'/fx/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if ed:
    for e in runpy.run_path(ed)['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
r=subprocess.run([os.environ.get('LLC',SDK+'/llc'),'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(json.dumps({'name':name,'error':r.stderr[-500:]})); sys.exit(1)
c=g['elf_fn'](d+'/m.o',g['KEEP']); open(d+'/fn.bin','wb').write(c)
Ob=open(T+'/orig.bin','rb').read(); rr,sd=g['metric'](c,Ob)
ot=g['mask'](Ob); ct=g['mask'](c)
off=[];i=0
for x in ot: off.append(i); i+=len(x)
h=[0]*len(ot); tot=0
for bl in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks():
    tot+=bl.size
    for k in range(bl.size): h[bl.a+k]=1
oo=sum(1-h[i] for i in range(len(ot)) if 0x2600<=off[i]<0x3c00)
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
fo,fc=fm(ot),fm(ct); hf=[0]*len(fo); ftot=0
for bl in difflib.SequenceMatcher(None,fo,fc,autojunk=False).get_matching_blocks():
    ftot+=bl.size
    for k in range(bl.size): hf[bl.a+k]=1
foo=sum(1-hf[i] for i in range(len(fo)) if 0x2600<=off[i]<0x3c00)
res={'name':name,'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd,'M':tot,'M_oo_tcf':oo,'fM':ftot,'fM_oo_tcf':foo}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
if not os.environ.get('KEEP'): os.remove(d+'/m.ll')
