import sys,re
P='/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs'
pat=re.compile(r'(error!|err!|require[a-z_]*!)')
def sites(path):
    out=[]
    for i,l in enumerate(open(path).read().split('\n'),1):
        for m in pat.finditer(l): out.append((i,m.group()))
    return out
a=sites(P); b=sites(sys.argv[1])
pl=open(P).read().split('\n'); vl=open(sys.argv[1]).read().split('\n')
ok=True
if len(a)!=len(b): print('COUNT',len(a),len(b)); ok=False
for x,y in zip(a,b):
    if x[0]!=y[0]: print('MOVED',x,y); ok=False
for n in (439,440):
    if pl[n-1]!=vl[n-1]: print('PANICLINE',n,repr(vl[n-1])); ok=False
print('OK' if ok else 'BAD', len(vl))
