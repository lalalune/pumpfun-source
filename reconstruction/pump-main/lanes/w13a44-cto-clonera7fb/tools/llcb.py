#!/usr/bin/env python3
"""llcb.py <m.ll> [--dbg] [llc args...]: llc a slimmed execute module (as rx.py), print ratio, slots, clonefeat, segstat 0x3e00-0x4a00."""
import sys,os,subprocess,json,tempfile,runpy
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
rx=None
a=sys.argv[1:]; m=a.pop(0); dbg=False
if a and a[0]=='--dbg': dbg=True; a.pop(0)
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc' if dbg else '~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
o=tempfile.mktemp(suffix='.o',dir=os.path.dirname(m))
r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o',o,*a],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
src=open(T+'/rx.py').read(); g={}
exec(src.split("OUT=os.environ")[0],g)
cand=g['elf_fn'](o,g['KEEP']); os.remove(o)
fb=os.path.join(os.path.dirname(m),'fn_%d.bin'%os.getpid()); open(fb,'wb').write(cand)
rr,sd=g['metric'](cand,g['orig_window']())
import ctoracle as co, tokio, clonefeat, segstat_lib as sl
otok,_=co.orig_tokens(); ct=tokio.toks(fb); s,rg=clonefeat.feats(ct)
seg=sl.segs(otok,ct,0x200); both={k:v[3] for k,v in seg.items() if 0x3e00<=k<0x4a00}
os.remove(fb)
print(json.dumps({'args':' '.join(a),'ratio':round(rr,5),'bytes':len(cand),'slots':sd,'cf':f'{s}/{rg}','b42':both.get(0x4200),'b44':both.get(0x4400),'bsum':sum(both.values())}))
