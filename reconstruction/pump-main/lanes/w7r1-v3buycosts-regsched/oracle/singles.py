import sys,os,json
sys.path.insert(0,os.path.dirname(__file__))
import mut
from concurrent.futures import ThreadPoolExecutor
f=mut.F0
if os.environ.get('EDIT'):
    import runpy
    for e in os.environ['EDIT'].split(':'): f=runpy.run_path(e)['edit'](f)
jobs=mut.allmuts(f,sys.argv[1].split(','))
with ThreadPoolExecutor(6) as ex: res=list(ex.map(mut.run,jobs))
res.sort()
json.dump(res,open(mut.OUT+'/singles-%s.json'%os.environ.get('NAME','x'),'w'))
from collections import Counter
print(len(res),Counter(r[2] for r in res))
for r in res:
    if r[2] not in ('e0/3','ERR'): print(r)
