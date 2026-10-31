#!/usr/bin/env python3
"""rec.py [names...]: record results.jsonl rows (not yet recorded) to the shared ledger."""
import json,subprocess,sys,os,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a77-cto-entrykeycopy')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a77-cto-entrykeycopy/reconstruction/pump-main/log_attempt.py'
SHA=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done=set(open(O+'/recorded.txt').read().split()) if os.path.exists(O+'/recorded.txt') else set()
G=runpy.run_path(O+'/e/genes.py')['G']
MAIN=0.66507
for l in open(O+'/results.jsonl'):
    d=json.loads(l); n=d['name']
    if n in done or n=='main0': continue
    edits=sum((G[g] for g in n.split('+')),[])
    es=json.dumps([(a[:90],b[:120]) for a,b in edits])[:600]
    key=f'0x22a10-w14-{SHA}-entrykeycopy-{n}-v1'
    r=d.get('ratio'); st='compile-failed' if 'error' in d else ('rejected' if (r is None or r<=MAIN or d.get('bytes')!=27400) else 'partial')
    note=(f"raw-IR capture + rx opt/llc oracle on main {SHA} (main0 eq_main, 0.66507 @27400). ratio {r} bytes {d.get('bytes')} eq_main {d.get('eq_main')}; "
          f"entry orig 0x0-0x800 local rm {d.get('L_rm')} (main 150) exact {d.get('L_ex')} (main 78), global rm 0x0-0x800 {d.get('G_rm0800')} (main 131), rmT {d.get('G_rmT')} (main 2782). EDITS={es}")
    data={'output':O+'/rx/'+n,'target':{'ratio':r,'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},'notes':note}
    subprocess.run(['python3',L,'record','--lane','w14a77-cto-entrykeycopy','--approach','entry-key-spelling','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'entry spelling {n} (shared-first kept): which entry key comparison / PDA input spelling gives the original copy-then-memcmp entry idiom',
        '--status',st,'--data',json.dumps(data)],check=True,capture_output=True)
    done.add(n); print('recorded',key,st)
open(O+'/recorded.txt','w').write('\n'.join(sorted(done)))
