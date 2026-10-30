#!/usr/bin/env python3
"""screen.py <bc> <base.o> <optsfile>: llc each option line, report #changed functions and which targets changed."""
import sys, subprocess, os, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__)); from objfuncs import load
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
bc,baseo,optf=sys.argv[1:4]; B=load(baseo)
T={'v3_buy_costs':'0x80df8','create_v29execute':'0x1e7c0','admin_cto7execute':'0x22a10','swap_hop':'0x5b3b0','sweep7execute':'0x72810','buy_handler':'0x13b9b8','buy_exact_quote_in_handler':'0x13f630','buy_exact_quote17':'0x1489f8'}
def run(opt):
    o=f'llc/scr-{abs(hash(opt))}.o'
    r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections','-data-sections','-filetype=obj',*opt.split(),bc,'-o',o],capture_output=True,text=True)
    if r.returncode: return opt,'ERR '+r.stderr.strip().splitlines()[0][:120]
    A=load(o); os.unlink(o)
    ch=[n for n in B if n in A and A[n]!=B[n]]
    tg=sorted({v for n in ch for k,v in T.items() if k in n})
    sz={v:(len(B[n][0]),len(A[n][0])) for n in ch for k,v in T.items() if k in n}
    return opt,f'changed {len(ch)} targets {tg} sizes {sz}'
opts=[l.strip() for l in open(optf) if l.strip() and not l.startswith('#')]
with cf.ThreadPoolExecutor(3) as ex:
    for opt,res in ex.map(run,opts): print(f'{opt:60s} {res}',flush=True)
