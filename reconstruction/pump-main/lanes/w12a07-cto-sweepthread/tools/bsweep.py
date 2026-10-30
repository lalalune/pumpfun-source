#!/usr/bin/env python3
"""bsweep.py base.ll out.jsonl : for each conditional br in execute, weight 2000:1 each way; llc; ratio."""
import sys,re,subprocess,json,os,difflib
from concurrent.futures import ThreadPoolExecutor
L=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a07-cto-sweepthread')
src=open(sys.argv[1]).read(); outp=sys.argv[2]; MD=os.environ.get('MD','999990')
s=src.index('define '); s=[m.start() for m in re.finditer(r'^define .*admin_cto7execute17h',src,re.M)][0]; e=src.index('\n}\n',s)
lines=[(m.start(),m.group(0)) for m in re.finditer(r'^  br i1 [^\n]*$',src[s:e],re.M)]
oraw=open(O+'/orig_raw.bin','rb').read()
def toks(raw):
    i=0;out=[]
    while i<len(raw):
        k=16 if raw[i]==0x18 else 8; x=bytearray(raw[i:i+k])
        if x[0]==0x18: x[4:8]=bytes(4); x[12:16]=bytes(4)
        elif x[0]==0x85: x[4:8]=bytes(4)
        out.append(bytes(x)); i+=k
    return out
o=toks(oraw)
def run(arg):
    idx,(off,ln),w=arg
    if '!prof' in ln: return None
    t=src[:s+off]+ln+', !prof !'+MD+''+src[s+off+len(ln):]+'\n!'+MD+' = !{!"branch_weights", i32 %d, i32 %d}\n'%w
    d=O+'/bs/%d_%d'%(idx,w[0]); os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(t)
    r=subprocess.run([L+'/llc','-O3','-mtriple=sbf','-mattr=+store-imm,+jmp-ext','-relocation-model=pic','-function-sections','-data-sections','-filetype=obj',d+'/m.ll','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'i':idx,'w':w,'err':r.stderr[-200:]}
    secs=subprocess.run([L+'/llvm-objdump','-h',d+'/m.o'],capture_output=True,text=True).stdout
    sec=next(l.split()[1] for l in secs.splitlines() if 'admin_cto7execute17h' in l and '.rel' not in l)
    subprocess.run([L+'/llvm-objcopy','-O','binary','--only-section='+sec,d+'/m.o',d+'/m.bin'],check=True)
    raw=open(d+'/m.bin','rb').read()
    c=toks(raw)
    ratio=difflib.SequenceMatcher(None,o,c,autojunk=False).ratio()
    for f in ('m.ll','m.o'): os.remove(d+'/'+f)
    return {'i':idx,'w':w,'bytes':len(raw),'ratio':round(ratio,5),'br':ln.strip()[:160]}
jobs=[(i,x,w) for i,x in enumerate(lines) for w in ((2000,1),(1,2000))]
with ThreadPoolExecutor(int(os.environ.get('J','4'))) as ex, open(outp,'w') as f:
    for r in ex.map(run,jobs):
        if r: f.write(json.dumps(r)+'\n'); f.flush()
