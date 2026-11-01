#!/usr/bin/env python3
"""pscore.py <post-opt m.ll> <name> : llc (fastbuild flags) + extract execute + M/ratio vs original (experiment only)."""
import sys,os,subprocess,json,hashlib,time,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, fx
OUT=os.environ.get('LANE_OUT')
OBJDUMP=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
def dis(o,out):
    r=subprocess.run([OBJDUMP,'-d','--no-show-raw-insn','--section=.text._ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E',o],capture_output=True,text=True)
    lines=[]
    for l in r.stdout.splitlines():
        m=re.match(r'\s*([0-9]+):\s+(.*)$',l)
        if m: lines.append('+%04x  %s'%(int(m.group(1))*8,m.group(2).strip()))
    open(out,'w').write('\n'.join(lines)+'\n')
def score_text(text,name,keepobj=False):
    d=os.path.join(OUT,'ps',name); os.makedirs(d,exist_ok=True); t0=time.time()
    open(d+'/m.ll','w').write(text)
    r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':'llc:'+r.stderr[-800:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b)
    if keepobj: dis(d+'/m.o',d+'/fn.lst')
    os.remove(d+'/m.o')
    if not keepobj: os.remove(d+'/m.ll')
    M,ratio=fx.Mof(b)
    return {'name':name,'M':M,'ratio':round(ratio,5),'bytes':len(b),'secs':round(time.time()-t0,1),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]}
if __name__=='__main__':
    print(json.dumps(score_text(open(sys.argv[1]).read(),sys.argv[2])))
