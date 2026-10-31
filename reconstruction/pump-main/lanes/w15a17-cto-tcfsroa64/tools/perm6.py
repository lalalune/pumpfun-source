# perm6.py: permute O R S W E L units of the tai-base program clone tail (IR oracle only)
import sys,itertools,json,os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import px2
L=open('rx/p_tai/mn.ll').read().split('\n')
s=4359
U={'O':L[s:s+2],'R':L[s+2:s+4],'S':L[s+4:s+6],'W':L[s+6:s+8],'E':L[s+8:s+10],'L':L[s+10:s+13]}
assert 'i64 24' in U['O'][0] and 'i64 32' in U['R'][0] and 'i64 40' in U['S'][0] and 'i64 42' in U['E'][0] and 'lifetime' in U['L'][0] and 'lifetime' in U['L'][2], U
os.makedirs('perm',exist_ok=True)
def run(p):
    t=L[:s]+sum((U[c] for c in p),[])+L[s+13:]
    f=f'perm/{p}.ll'; open(f,'w').write('\n'.join(t)); r=px2.run(f); os.remove(f); r['p']=p; return r
ps=[''.join(x) for x in itertools.permutations('ORSWEL')]
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(run,ps):
        print(json.dumps({k:r.get(k) for k in ('p','ratio','M','bytes','slots','err')}),flush=True)
