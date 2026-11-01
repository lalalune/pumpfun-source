#!/usr/bin/env python3
"""pwscan.py <m.ll> <blocks.txt> <probs comma> <out.jsonl>: mild !prof weights on single post-opt branches; llc only"""
import sys,os,json,subprocess,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import rc, oracle
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.dirname(T)
ml,bf,probs,outf=sys.argv[1],sys.argv[2],sys.argv[3].split(','),sys.argv[4]
B=[x.strip() for x in open(bf) if x.strip()]
O=rc.orig_window(); OT,OO=rc.mask(O)
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
LLCA=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
def run(job):
    b,p=job; tag=f'pw_{abs(hash(b))%10**8}_{p}'
    d=os.path.join(OUT,'pw'); os.makedirs(d,exist_ok=True)
    ll=os.path.join(d,tag+'.ll'); o=os.path.join(d,tag+'.o')
    r=subprocess.run(['python3',T+'/pw.py',ml,ll,f'{b}=p{p}'],capture_output=True,text=True)
    if r.returncode: return {'b':b,'p':p,'err':r.stderr[-200:]}
    subprocess.run(['nice','-n','5',LLC,*LLCA,ll,'-filetype=obj','-o',o],capture_output=True)
    try: c=oracle.elf_fn(o,oracle.KEEP)
    except SystemExit: return {'b':b,'p':p,'err':'llc'}
    for f in (ll,o):
        try: os.remove(f)
        except Exception: pass
    ct,_=rc.mask(c); sm=difflib.SequenceMatcher(None,OT,ct,autojunk=False)
    M=sum(x.size for x in sm.get_matching_blocks())
    res={'b':b,'p':p,'M':M,'bytes':len(c)}
    with open(outf,'a') as f: f.write(json.dumps(res)+'\n')
    return res
jobs=[(b,p) for b in B for p in probs]
with ThreadPoolExecutor(4) as ex: list(ex.map(run,jobs))
