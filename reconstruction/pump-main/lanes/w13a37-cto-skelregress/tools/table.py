import json
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress'
rows=[]
for l in open(OUT+'/results.jsonl'):
    d=json.loads(l)
    if not d.get('ok'): continue
    c=d['cto']; p=(d.get('skel') or '').split()
    rows.append((d['name'],c['ratio'],c['cand_bytes'],c.get('slots_diff'),float(p[1]),p[11],p[12],json.loads(d['spec'])))
# pareto on (ratio, skel) among all, and among 27400
def pareto(R):
    return [r for r in R if not any((o[1]>=r[1] and o[4]>=r[4]) and (o[1]>r[1] or o[4]>r[4]) for o in R)]
print('| variant | ratio | bytes | slots | skeleton | chunk 0x3c34 | chunk 0x42e5 | Pareto |')
print('|---|---:|---:|---:|---:|---:|---:|---|')
P=set(r[0] for r in pareto(rows)); P4=set(r[0] for r in pareto([r for r in rows if r[2]==27400]))
for r in sorted(rows,key=lambda r:-r[1]):
    tag=('all' if r[0] in P else '')+(' 27400' if r[0] in P4 else '')
    print(f'| {r[0]} | {r[1]:.5f} | {r[2]} | {r[3] if r[3] is not None else "-"} | {r[4]:.4f} | {r[5]} | {r[6]} | {tag.strip()} |')
