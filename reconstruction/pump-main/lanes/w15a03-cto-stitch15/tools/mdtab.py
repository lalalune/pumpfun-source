#!/usr/bin/env python3
"""mdtab.py <res.jsonl> [--main 2248] [--filter prefix,..] [--all]: markdown table of oracle rows (name, genes, dB, M, dM),
sorted by dM then |dB|. Without --all, byte-identical-to-main rows are collapsed into one count line."""
import sys,json
a=sys.argv[1:]; MM=2248; pre=None; allr='--all' in a
if '--all' in a: a.remove('--all')
if '--main' in a: i=a.index('--main'); MM=int(a[i+1]); del a[i:i+2]
if '--filter' in a: i=a.index('--filter'); pre=a[i+1].split(','); del a[i:i+2]
rows={};eq=[];err=[]
for l in open(a[0]):
    r=json.loads(l)
    if pre and not any(r['name'].startswith(p) for p in pre): continue
    if 'error' in r: err.append(r['name']); continue
    if r.get('eq_main') and not allr: eq.append(r['name']); continue
    rows[r['name']]=r
print('| variant | genes | dB | M | dM |\n| --- | --- | ---: | ---: | ---: |')
for r in sorted(rows.values(),key=lambda r:(-(r['M']-MM),abs(r['bytes']-27400))):
    print(f"| {r['name']} | {r['genes']} | {r['bytes']-27400:+d} | {r['M']:,} | {r['M']-MM:+d} |")
print(f'\n{len(eq)} rows byte-identical to main (masked tokens equal); {len(err)} compile/apply errors: {" ".join(err)}')
