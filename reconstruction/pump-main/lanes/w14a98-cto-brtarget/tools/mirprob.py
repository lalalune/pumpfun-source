#!/usr/bin/env python3
"""mirprob.py <pre.mir> <out_prefix> blk=a:b,... : fixed-RA MBP oracle. Edit successor probabilities of MIR blocks
(IR name, e.g. bb23.i; first successor listed gets a/(a+b)) in a post-RA MIR (llc -stop-before=block-placement),
then llc -start-before=block-placement, score. Experiment only."""
import sys,os,re,subprocess,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sc
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def run(mir,outp,spec,score=True):
    t=open(mir).read()
    for kv in [x for x in spec.split(',') if x]:
        b,w=kv.split('='); a,c=map(float,w.split(':'))
        pat=re.compile(r'(\n  bb\.\d+\.'+re.escape(b)+r':[^\n]*\n    successors: )%bb\.(\d+)\(0x[0-9a-f]+\), %bb\.(\d+)\(0x[0-9a-f]+\)')
        m=pat.search(t); assert m,b
        p=int(round(0x80000000*a/(a+c))); p=max(1,min(0x7fffffff,p)); q=0x80000000-p
        t=t[:m.start()]+m.group(1)+f'%bb.{m.group(2)}(0x{p:08x}), %bb.{m.group(3)}(0x{q:08x})'+t[m.end():]
    open(outp+'.mir','w').write(t)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections','-start-before=block-placement',outp+'.mir','-o',outp+'.s'],capture_output=True,text=True)
    if r.returncode: return {'err':r.stderr[-500:]}
    s=sc.score(outp+'.s'); s.pop('ch',None); return s
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else '')))
