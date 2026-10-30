import sys,json,re
rows=[]
for l in open(sys.argv[1] if len(sys.argv)>1 else '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/results2.jsonl'):
    try: d=json.loads(l)
    except: continue
    c=d.get('coal') or ''
    m=re.search(r'pay_reg=(\S+) split=\$(\S+) in (\d+)',c); cf=re.search(r'cf=(\S+)',c)
    rows.append((d.get('ratio') or 0,d.get('name'),d.get('bytes'),d.get('rm'),d.get('rmV'),d.get('rmT'),m.groups() if m else d.get('error'),cf.group(1) if cf else ''))
key=sys.argv[2] if len(sys.argv)>2 else 'ratio'
rows.sort(key=lambda r:-(r[0] if key=='ratio' else (r[4] or 0)))
for r in rows[:int(sys.argv[3]) if len(sys.argv)>3 else 40]: print(*r)
print(len(rows),'rows')
