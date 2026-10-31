#!/usr/bin/env python3
"""brw.py <m.ll> <lineno> <w1:w2>[,<w1:w2>..] [--watch irblock,..]: single-branch !prof weight oracle on post-opt IR.
Puts branch_weights on the conditional br at <lineno> (1-based) of the slimmed post-opt module, runs release llc to asm,
assembles + scores (rx metric) and prints, for each weight pair, the ratio/slots and the layout neighbourhood (previous
and next IR block in the asm) of each watched IR block. Placement cause test: does a weight alone reproduce a
chainscan move? Experiment only."""
import sys,os,re,json,subprocess,tempfile
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ORIG=G['orig_window']()
a=sys.argv[1:]; M=a.pop(0); LN=int(a.pop(0)); WS=a.pop(0).split(','); WATCH=[]
while a:
    x=a.pop(0)
    if x=='--watch': WATCH=a.pop(0).split(',')
L=open(M).read().split('\n')
br=L[LN-1]; assert re.match(r'\s+br i1 ',br), br
def layout(s):
    out=[]
    for l in s.split('\n'):
        m=re.match(r'^(LBB0_\d+:|# %bb\.\d+:)\s+# %(\S+)',l)
        if m: out.append(m.group(2))
    return out
def run(w):
    t=list(L)
    if w!='none':
        x,y=w.split(':'); b=re.sub(r', !prof !\d+','',br)
        t[LN-1]=b+', !prof !99991'; t.append('!99991 = !{!"branch_weights", i32 %s, i32 %s}'%(x,y))
    with tempfile.TemporaryDirectory() as d:
        open(d+'/m.ll','w').write('\n'.join(t))
        r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=asm','-o',d+'/m.s'],capture_output=True,text=True)
        if r.returncode: return {'w':w,'err':r.stderr[-400:]}
        s=open(d+'/m.s').read()
        r=subprocess.run([SDK+'/clang','-cc1as','-triple','sbf','-target-feature','+store-imm','-target-feature','+jmp-ext','-filetype','obj',d+'/m.s','-o',d+'/m.o'],capture_output=True,text=True)
        c=G['elf_fn'](d+'/m.o',G['KEEP']); rr,sd=G['metric'](c,ORIG)
        lo=layout(s); nb={}
        for wb in WATCH:
            if wb in lo: i=lo.index(wb); nb[wb]=(lo[i-1] if i else None, lo[i+1] if i+1<len(lo) else None)
        return {'w':w,'ratio':round(rr,5),'bytes':len(c),'slots':sd,'nb':nb}
print('br:',br.strip()[:160])
for w in ['none']+WS: print(json.dumps(run(w)))
