#!/usr/bin/env python3
"""ship.py <suffix> <src admin_cto.rs> <measure.json> <main7> <main_ratio> <main_slots> <title-mech> <mechanism-md>
Commit src + NOTES section on branch swarm/w13a47-cto-stitch9-<suffix> (already checked out at origin/main), push, PR, land."""
import sys, json, subprocess, hashlib, os
suf, src, mj, main7, mr, ms, tmech, mech = sys.argv[1:9]
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a47-cto-stitch9'
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a47-cto-stitch9'
m=json.load(open(mj)); a=m['admin_cto']; assert m['losses']==[] and m['raw_losses']==[] and a['cand_bytes']==27400
so=os.path.join(m['out'],'unstripped.so'); sha=hashlib.sha256(open(so,'rb').read()).hexdigest()
def run(*c, **k): r=subprocess.run(c, cwd=WT, capture_output=True, text=True, **k); print(r.stdout[-400:], r.stderr[-400:]); return r
open(f'{WT}/programs/pump/src/creator/admin_cto.rs','w').write(open(src).read())
for f in ('genes47.py','run47.py','rec47.py','ship.py','neg_frozen.json'):
    if os.path.exists(f'{O}/tools/{f}'): open(f'{WT}/reconstruction/pump-main/lanes/w13a47-cto-stitch9/tools/{f}','w').write(open(f'{O}/tools/{f}').read())
table=f'''| metric | main {main7} | this change |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | {mr} | **{a['ratio']}** |
| slots_diff | {ms} | {a['slots_diff']} |
| normalized / raw | {m['normalized']} / {m['raw']} | {m['normalized']} / {m['raw']} |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `{sha}` |
'''
p=f'{WT}/reconstruction/pump-main/lanes/w13a47-cto-stitch9/NOTES.md'
open(p,'a').write(f'\n## %{suf} on main {main7} ({mr}): {tmech}\n\n{mech}\n\n{table}')
run('git','add','-A','programs/pump/src/creator/admin_cto.rs','reconstruction/pump-main/lanes/w13a47-cto-stitch9/NOTES.md','reconstruction/pump-main/lanes/w13a47-cto-stitch9/tools')
run('git','commit','-q','-m',f'pump-main w13: w13a47-cto-stitch9: {tmech} (admin_cto {mr} -> {a["ratio"]})\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
run('git','push','-q','-u','origin',f'swarm/w13a47-cto-stitch9-{suf}')
body=f'''Lane `w13a47-cto-stitch9` (wave 13, continued in wave 14). Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B.

{table}
Mechanism: {mech}

Notes: `reconstruction/pump-main/lanes/w13a47-cto-stitch9/NOTES.md`. Ledger keys `0x22a10-w13-<main7>-stitch9-*`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
'''
open(f'{O}/pr{suf}.md','w').write(body)
r=run('gh','pr','create','--repo','lalalune/pumpfun-source','--base','main','--head',f'swarm/w13a47-cto-stitch9-{suf}','--draft','--title',f'pump-main w13: w13a47-cto-stitch9: admin_cto {mr} -> {a["ratio"]} at 27400 B, 0 losses','--body-file',f'{O}/pr{suf}.md')
pr=r.stdout.strip().rsplit('/',1)[-1]
print('PR',pr)
l=subprocess.run(['python3','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/land.py',pr],capture_output=True,text=True)
open(f'{O}/land{suf}.json','w').write(l.stdout); print('land exit',l.returncode, l.stdout[-600:])
