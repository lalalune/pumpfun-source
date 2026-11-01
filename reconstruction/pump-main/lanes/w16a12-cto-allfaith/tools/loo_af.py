#!/usr/bin/env python3
"""loo_af.py: leave-one-out marginal values inside the full HxT basin (h3T = h2+ft+T) against each form's single value on
main (experiment only). marginal_in_basin(X) = metric(h3T) - metric(h3T - X); single_on_main(X) = metric(main + X) - metric(main).
Class: 'needs partner' if it loses alone but helps in the basin; 'wrong' if it loses in both; 'helps' / 'basin-only loss'."""
import json,os,glob
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R={}
for f in glob.glob(O+'/res-*.jsonl'):
    for l in open(f):
        r=json.loads(l)
        if 'M' in r: R[r['name']]=r
R.setdefault('m0',{'name':'m0','M':2251,'Mperm':2295,'Mhc':2302,'Lrfj':3006})
def stk(n):
    if n=='m0': return 2302
    try: return json.load(open(f'{O}/stk/{n}_p0/stk.json'))['stacked']
    except Exception: return None
def met(n,k):
    if n not in R: return None
    return stk(n) if k=='stacked' else R[n].get(k)
# component -> (LOO cell name, single-on-main cell name)
import sys
BASE=sys.argv[1] if len(sys.argv)>1 else 'h3T'
P={'h3T':'x_','h3cT':'c_','ftcT':'f_'}[BASE]; FT={'h3T':('fee-tag phi (ft)','h2T','ft'),'h3cT':('fee-tag phi (ftc, out-param oracle)','h2T','ftc'),'ftcT':('fee-tag phi (ftc, out-param oracle)','T','ftc')}[BASE]
C=[('holder (h1: curve store from the block bool; h1b folds into it)','x_hf','h1'),
   ('per-arm cashback (h2p)','x_cb','h2p'),
   FT,
   ('s1 (sharing CPI to_account_info)','x_s1','t_s1'),
   ('s_tai2 (TCF program to_account_info)','x_tai','t_tai'),
   ('c2 (TCF pcva clone order)','x_c2','t_c2'),
   ('n1 (event reads curve fee)','x_n1','t_n1'),
   ('po (owner-first pool gate)','x_po','t_po'),
   ('rev_ff (raw amount first)','x_ff','t_ff')]
C=[(a,(b.replace('x_',P) if b.startswith('x_') else b),c) for a,b,c in C]
if BASE=='ftcT': C=[c for c in C if not c[1].startswith('f_hf') and not c[1].startswith('f_cb')]
full=BASE
print(f'Full cell {full}: '+', '.join(f"{k} {met(full,k)}" for k in ('M','Mhc','Lrfj','stacked')))
print(f'\n| form | metric | in basin ({BASE} - ({BASE}-X)) | alone on main (main+X - main) | class |')
print('| --- | --- | ---: | ---: | --- |')
for name,loo,single in C:
    for k in ('M','Mhc','Lrfj','stacked'):
        a,b=met(full,k),met(loo,k); c,z=met(single,k),met('m0',k)
        ib=(a-b) if None not in (a,b) else None; om=(c-z) if None not in (c,z) else None
        cl=''
        if ib is not None and om is not None:
            cl='needs partner' if (om<0 and ib>0) else 'wrong (loses in both)' if (om<0 and ib<=0) else 'helps on main' if om>0 else 'neutral on main'
        f=lambda x:'' if x is None else f'{x:+d}'
        print(f'| {name} | {k} | {f(ib)} | {f(om)} | {cl} |')
