#!/usr/bin/env python3
"""rec.py <res.jsonl> <manifest.json> [prefix]: compute M for each oracle row, print table, append ledger rows once."""
import sys,os,json,difflib,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.argv_saved=sys.argv[:]
import oracle
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a73-cto-autospell')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a73-cto-autospell'
SHA=os.environ.get('SHA') or open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
a=sys.argv_saved[1:]; res,man=a[0],a[1]; pre=a[2] if len(a)>2 else 'autospell'
o=oracle.mask(oracle.orig_window())
mf={v['name']:v for v in json.load(open(man))}
done=set(open(O+'/recorded-'+os.path.basename(res)+'.txt').read().split()) if os.path.exists(O+'/recorded-'+os.path.basename(res)+'.txt') else set()
rows=[json.loads(l) for l in open(res) if l.strip()]
out=[]
for r in rows:
    n=r['name']
    if 'ratio' in r:
        raw=open(f'{O}/rx/{n}/fn.bin','rb').read(); c=oracle.mask(raw)
        r['M']=sum(s for _,_,s in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
    out.append(r)
    if n in done: continue
    v=mf.get(n,{}); st='compile-failed' if 'ratio' not in r else ('rejected')
    d={'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},'M':r.get('M'),'eq_main':r.get('eq_main'),
       'notes':f"raw-IR capture + rx opt/llc oracle on main {SHA}; from={v.get('from','')[:100]!r} to={v.get('to','')[:100]!r}"}
    subprocess.run(['python3',WT+'/reconstruction/pump-main/log_attempt.py','record','--lane','w14a73-cto-autospell','--approach','autospell','--target','0x22a10',
        '--dedupe-key',f'0x22a10-w14-{SHA}-{pre}-{n}-v1','--hypothesis',f"autospell single-site spelling {v.get('rule','?')} at line {v.get('line','?')}",
        '--status',st,'--data',json.dumps(d)],capture_output=True)
    done.add(n)
open(O+'/recorded-'+os.path.basename(res)+'.txt','w').write('\n'.join(sorted(done)))
out.sort(key=lambda r:-(r.get('M') or 0))
for r in out:
    if 'ratio' in r: print(f"{r['name']:24s} {r['ratio']:.5f} {r['bytes']:6d} M {r['M']:5d} {'EQ' if r['eq_main'] else ''}")
    else: print(f"{r['name']:24s} ERR {r.get('error')}")
