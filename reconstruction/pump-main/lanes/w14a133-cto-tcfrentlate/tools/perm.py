import sys,itertools,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import px2
L=open('rx/main0/mn.ll').read().split('\n')
s=4360  # 0-based index of line 4361
U={'R':L[s:s+2],'E':L[s+2:s+4],'W':L[s+4:s+6],'S':L[s+6:s+8],'L':L[s+8:s+11]}
assert 'i64 32' in U['R'][0] and 'i64 42' in U['E'][0] and 'i64 40' in U['S'][0] and 'lifetime' in U['L'][0] and 'lifetime' in U['L'][2]
def run(p):
    t=L[:s]+sum((U[c] for c in p),[])+L[s+11:]
    f=f'perm/{p}.ll'; open(f,'w').write('\n'.join(t)); r=px2.run(f); os.remove(f); r['p']=p; return r
ps=[''.join(x) for x in itertools.permutations('REWSL')]
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(run,ps):
        print(json.dumps({k:r.get(k) for k in ('p','ratio','M','bytes','slots')}),flush=True)
