import sys, json; sys.path.insert(0,'tools'); import irfn
f=irfn.Fn(sys.argv[1])
def after(o,a,b):
    o=[x for x in o if x!=a]; o.insert(o.index(b)+1,a); return o
o=f.order0
print('base', f.run(o), flush=True)
res=[]
for y in o[1:]:
    if y in ('bb59','bb68'): continue
    r=f.run(after(o,y,'bb59'))
    if 'error' in r: continue
    res.append((r['slot_diffs'],r['distance'],r['size'],r['calls_equal'],r['masked_equal'],y[:70]))
    if r['masked_equal']: print('FOUND', y, flush=True)
res.sort()
for t in res[:15]: print(t)
