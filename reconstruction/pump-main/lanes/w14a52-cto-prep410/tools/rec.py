import sys,json,subprocess,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a52-cto-prep410')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a52-cto-prep410/reconstruction/pump-main/log_attempt.py'
SHA=os.environ.get('SHA','0fbf8da');BASE=os.environ.get('BASE','0.65578')
done=set(open(OUT+'/recorded.txt').read().split()) if os.path.exists(OUT+'/recorded.txt') else set()
for f in sys.argv[1:]:
  for l in open(f):
    if not l.startswith('{'): continue
    r=json.loads(l); n=r['name']
    if SHA+n in done or (SHA=='0fbf8da' and n in done): continue
    key=f'0x22a10-w14-{SHA}-prep410-{n}-v1'
    try: ed=open(f'{OUT}/e/{n}.py').read()[:900]
    except: ed=''
    note=f"raw-IR capture + rx opt/llc oracle on main {SHA} ({BASE} @27400): "+('compile error' if 'error' in r else f"ratio {r['ratio']} bytes {r['bytes']} eq_main {r['eq_main']}")+' edits: '+ed
    st='compile-failed' if 'error' in r else 'analyzed'
    d={"output":OUT+'/rx/'+n,"target":{"ratio":r.get('ratio'),"slots_diff":r.get('slots_diff'),"cand_bytes":r.get('bytes')},"notes":note}
    subprocess.run(['python3',L,'record','--lane','w14a52-cto-prep410','--approach','prep410','--target','0x22a10','--dedupe-key',key,'--hypothesis',f'prep410 bridge-region spelling {n} (tuple/Ok carry/prepare/410 forms, orig 0x1940-0x1c38)','--status',st,'--data',json.dumps(d)],capture_output=True)
    done.add(SHA+n)
open(OUT+'/recorded.txt','w').write('\n'.join(sorted(done)))
print(len(done))
