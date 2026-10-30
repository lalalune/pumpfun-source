#!/usr/bin/env python3
"""llco.py <name> <edits.py> [--base m.ll]: apply EDITS (exact (old,new) or callables) to the post-opt slim module, llc, score.
Writes rx/<name>/{m.ll,fn.bin,dis.txt}. Experiment only."""
import sys,os,subprocess,json,runpy
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
a=sys.argv[1:]; name=a.pop(0); ed=a.pop(0); base=OUT+'/rx/base/m.ll'
if a and a[0]=='--base': a.pop(0); base=a.pop(0)
t=open(base).read()
for e in runpy.run_path(ed)['EDITS']:
    if callable(e): t=e(t); continue
    x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*a],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=g['elf_fn'](d+'/m.o',g['KEEP']); open(d+'/fn.bin','wb').write(cand)
rr,sd=g['metric'](cand,g['orig_window']())
dis=subprocess.run(['bash',T+'/dis.sh',d+'/m.o'],capture_output=True,text=True).stdout; open(d+'/dis.txt','w').write(dis)
import re
tagslot=None
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots':sd}
print(json.dumps(res))
# extra frame-insensitive metrics
import struct,difflib
def toks(raw,maskframe=False,maskreg=False):
    out=[];i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; b=bytearray(raw[i:i+n])
        if op==0x85: b[1]&=0x0f; b[4:8]=b'\0'*4
        if op==0x18: b[4:8]=b'\0'*4; b[12:16]=b'\0'*4
        regs=b[1]
        if maskframe and ((regs&0xf)==10 or (regs>>4)==10): b[2:4]=b'\0\0'
        if maskreg: b[1]=(0xa0 if (regs>>4)==10 else 0)|(0x0a if (regs&0xf)==10 else 0)
        out.append(bytes(b)); i+=n
    return out
o=g['orig_window']()
fm=difflib.SequenceMatcher(None,toks(o,True),toks(cand,True),autojunk=False).ratio()
frm=difflib.SequenceMatcher(None,toks(o,True,True),toks(cand,True,True),autojunk=False).ratio()
res.update(fm=round(fm,5),frm=round(frm,5)); print(json.dumps(res))
open(d+'/res.json','w').write(json.dumps(res))
