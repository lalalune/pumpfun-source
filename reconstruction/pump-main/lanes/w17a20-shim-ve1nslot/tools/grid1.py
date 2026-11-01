#!/usr/bin/env python3
"""grid1.py: ce3 grid on main 8330455eb: early curve-flag subsets x global early x store order (main|orig) x volatile stores. Experiment only."""
import sys,os,json,itertools
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import ce3,pscore
ORIGBLK=['mf','he','fc','s_cb','s_hr','s_my','cr','s_ql','s_fc','s_he','s_mf']
def cells():
    for n in range(4):
        for early in itertools.combinations(('cb','hr','my'),n):
            for G in (False,True):
                for order in ('main','orig'):
                    for vs in (False,True):
                        yield early,G,order,vs
def job(c):
    early,G,order,vs=c
    if order=='main':
        blk=[k for k in ce3.MAIN if k not in early and not (G and k=='g')]
    else:
        rest=[k for k in ('cb','hr','my') if k not in early]
        blk=([] if G else ['g'])+rest+ORIGBLK
    name='g1_%s_%s_%s_%s'%(''.join(early) or 'none','G' if G else 'g',order,'v' if vs else 'n')
    try:
        t=ce3.build(early=early,G=G,block=blk,volst=vs)
        r=pscore.score_text(t,name)
    except Exception as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    C=list(cells())
    with Pool(4) as p:
        for r in p.imap_unordered(job,C): print(json.dumps(r),flush=True)
