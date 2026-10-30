#!/usr/bin/env python3
"""catalog.py: merge this lane's knob screens into $SWARM/w11/sizeknobs-cto.json (idempotent)."""
import json,runpy,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a34-cto-newknobs'
CAT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'
BASES={'m06e6bb8':('06e6bb829',0.57669,'hc/s1_06e6bb8.jsonl'),'m8cf3c5f':('8cf3c5f8a',0.62043,'hc/s6all.jsonl')}
def cat(n):
    if n.startswith('g_'): return 're-screen (w13a10 genes13 library)'
    for p,c in [('ev_ts','Clock/Rent call site'),('wl_ts','Clock/Rent call site'),('rent','Clock/Rent call site'),('ev_','AdminCtoEvent field source'),
                ('rs_','AdminCtoEvent field source (sharing_config_reset)'),('pool_','admin_cto_pool CPI argument form'),('sh_','admin_cto_sharing_config CPI argument form'),
                ('sig_','pool-authority signer seeds form'),('pu_','post-update tail (pool_updated / msg)'),('tail_','post-update tail (pool_updated / msg)'),
                ('cu_','curve update block'),('wl_','wallet event')]:
        if n.startswith(p): return c
    return 'other'
d=json.load(open(CAT))
d['bases'].update({k:{'commit':v[0],'bytes':27400,'ratio':v[1],'source':'w13a34-cto-newknobs raw-IR oracle'} for k,v in BASES.items()})
byname={k['name']:k for k in d['knobs']}
extra=[]
for nm,(c,br,f) in BASES.items():
    p=os.path.join(O,f)
    if not os.path.exists(p): continue
    for l in open(p):
        r=json.loads(l)
        if 'ratio' not in r or r['name'].startswith('base'): continue
        n=r['name']; E=runpy.run_path(f'{O}/edits/{n}.py')['EDITS']
        k=byname.get(n)
        if not k:
            k={'name':n,'category':cat(n),'edit':[{'old':a,'new':b} for a,b in E],'results':{}}; d['knobs'].append(k); byname[n]=k
        k['results'][nm]={'bytes':r['bytes'],'delta_bytes':r['bytes']-27400,'ratio':r['ratio'],'delta_ratio':round(r['ratio']-br,5),
            'identical_to_base':bool(r.get('eq_main')) or (r['bytes']==27400 and abs(r['ratio']-br)<1e-9),'method':'raw-IR opt+llc oracle (w13a23 rx.py; equals the identity build)','source':'w13a34-cto-newknobs'}
tmp=CAT+'.tmp'; json.dump(d,open(tmp,'w'),indent=1); os.replace(tmp,CAT); print(len(d['knobs']))
