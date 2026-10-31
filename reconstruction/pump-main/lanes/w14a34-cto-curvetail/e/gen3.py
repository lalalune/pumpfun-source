#!/usr/bin/env python3
"""gen3.py: factorial over pool-gate/tail toggles (w14a34)."""
import os,itertools,runpy
D=os.path.dirname(os.path.abspath(__file__))
exec(open(D+'/gen2.py').read().split('combos=')[0])
K['evhr']=[("is_holder_reward:holder,is_cashback_coin","is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin")]
K['evcb']=[("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cashback,")]
T=['own','e1','evhr','ph','hf','evcb']
done=set(open(D+'/q2.list').read().split())|set(open(D+'/q1.list').read().split())
names=[]
for r in range(1,len(T)+1):
    for c in itertools.combinations(T,r):
        n='g_'+'_'.join(c)
        if n in done: continue
        E=[]
        for k in c: E+=K[k]
        open(f'{D}/e/{n}.py','w').write('EDITS='+repr(E)+'\n'); names.append(n)
print(' '.join(names))
