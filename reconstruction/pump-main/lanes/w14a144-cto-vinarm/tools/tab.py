import re,json,os
M='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a144-cto-vinarm'
rows=[]
for f in ('res.txt','res2.txt'):
    for l in open(f'{M}/{f}'):
        m=re.match(r'(\S+) (\S+) \| (.*?) \| (.*)',l.strip())
        if not m: continue
        n,g,t,j=m.groups()
        v=re.findall(r'(\S+)\s+B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',t)
        try: r=json.loads(j)['ratio']
        except: r=None
        d={x[0]:x[1:] for x in v}
        def c(k): x=d.get(k); return f'{x[0]} / {x[1]} / {x[5]}' if x else '-'
        rows.append(f'| `{n}` | {"e88f9d5" if f=="res2.txt" else "ebe5387"} | {r} | {c(n)} | {c(n+"_O")} | {c(n+"_O312")} |')
open(M+'/table.md','w').write('\n'.join(rows)+'\n'); print(len(rows))
