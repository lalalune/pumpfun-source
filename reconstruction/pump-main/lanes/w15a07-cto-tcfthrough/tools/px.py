#!/usr/bin/env python3
"""px.py <name> <m.ll> <edits.py>: post-opt IR edits (EDITS: (old,new) exact once, or callables), SDK llc as fastbuild, score.
Prints ratio/bytes/slots, M, and the 0x2600-0x3c00 orig-only tokens (M_oo, rM_oo). Experiment only."""
import sys,os,subprocess,runpy,json,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
OUT=os.path.dirname(T); SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
name,base,ed=sys.argv[1:4]; d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
for e in runpy.run_path(ed)['EDITS']:
    if callable(e): t=e(t); continue
    a,b=e; c=t.count(a); assert c==1,(c,a[:200]); t=t.replace(a,b)
open(d+'/m.ll','w').write(t)
r=subprocess.run([os.environ.get('LLC',SDK+'/llc'),'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c)
O=oracle.orig_window(); rr,sd=oracle.metric(c,O)
ot,oo=xled.toks(O); ct,_=xled.toks(c)
def rm(z): return [bytes([x[0],0])+x[2:] for x in z]
reg={}
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
for nm,f in (('M',lambda z:z),('rM',rm),('fM',fm),('sk',xled.fmask)):
    a=f(ot); b=f(ct); h=[0]*len(a); tot=0
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        tot+=bl.size
        for k in range(bl.size): h[bl.a+k]=1
    reg[nm+'_oo_tcf']=sum(1-h[i] for i in range(len(a)) if 0x2600<=oo[i]<0x3c00); reg[nm]=tot
res={'name':name,'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd,**reg}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
