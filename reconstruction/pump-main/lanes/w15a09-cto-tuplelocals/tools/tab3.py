import re,json
M='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a09-cto-tuplelocals'
d=json.load(open(M+'/desc.json')); lcs={}
for l in open(M+'/lcs.txt'):
    p=l.split()
    if len(p)>2 and p[-1].startswith('rfj:'): lcs[p[0]]=int(p[-1][4:])
rows=['| gene | form | ratio | bytes | M | fM | rfjM | true-LCS rfj | eq main |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
for l in open(M+'/res.txt'):
    n,g=l.split()[:2]
    if 'COMPILE FAIL' in l:
        rows.append(f'| `{n}` | {d.get(n,g)} | overlap / compile fail | | | | | | |'); continue
    m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); j=json.loads(l.split(' | ')[2])
    lc=lcs.get(n); dl=f'{lc} ({lc-3007:+d})' if lc else ''
    rows.append(f"| `{n}` | {d.get(n,'main 90300f9') if n!='none' else 'main 90300f9'} | {j['ratio']} | {m[1]} | {m[2]} | {m[3]} | {m[6]} | {dl} | {'yes' if j.get('eq_main') else 'no'} |")
open(M+'/table.md','w').write('\n'.join(rows)+'\n'); print(len(rows))
