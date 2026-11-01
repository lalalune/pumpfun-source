#!/usr/bin/env python3
"""fillnotes.py: fill NOTES.md placeholders from an/beam.json + an/singles.json + composite captures."""
import json,os,sys,collections
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile')
N='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile/NOTES.md'
b=json.load(open(OUT+'/an/beam.json')); S=json.load(open(OUT+'/an/singles.json'))
byname={r['name']:r for r in S}
L=['Best predicted composite per number of right jumps (of 41; main 11):','','| right | TCF right | pred M | bytes | composite |','| ---: | ---: | ---: | ---: | --- |']
for g in sorted(b['levels'],key=int):
    r=b['levels'][g]; L.append(f"| {g} | {r['gt']} | {r['predM']} | {r['bytes']} | {' + '.join(r['set']) or 'main'} |")
L+=['','Top predicted composites (all at or below main):','','| pred M | right | composite |','| ---: | ---: | --- |']
for r in b['top'][:8]: L.append(f"| {r['predM']} | {r['good']} | {' + '.join(r['set']) or 'main'} |")
comp=[r for r in S if r['name'].startswith('J_') and 'M' in r]
L+=['','Composite captures (real builds, RA interactions included) against the model:','','| capture | genes | bytes | M | right (TCF/sh) |','| --- | --- | ---: | ---: | --- |']
for r in comp: L.append(f"| {r['name']} | `{r['genes']}` | {r['bytes']} | {r['M']} | {r['good']} ({r['gt']}/{r['gs']}) |")
cnt=collections.Counter((r.get('m3078'),r.get('m3370')) for r in S if 'M' in r)
M=['| accounts+232 reg / temps reg | captures | examples |','| --- | ---: | --- |']
for k,v in cnt.most_common():
    ex=[r['name'] for r in S if 'M' in r and (r.get('m3078'),r.get('m3370'))==k][:8]
    M.append(f"| {k[0]} / {k[1]} | {v} | {', '.join(ex)} |")
nsp=sum(1 for r in S if 'M' in r and r['name']!='main')
M.append(''); M.append(f"{nsp} spellings captured (lamports-first pcva forms, c2 + neighbours, and every neighbour literal order); the original's r6 / r0 appears in none.")
t=open(N).read()
t=t.replace('RESULT_TABLE_PLACEHOLDER','\n'.join(L)).replace('MARKER_TABLE_PLACEHOLDER','\n'.join(M))
open(N,'w').write(t); print('filled', nsp)
