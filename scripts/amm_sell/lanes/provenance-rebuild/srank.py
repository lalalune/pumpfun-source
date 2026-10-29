import json,sys,os
sys.path.insert(0,os.path.dirname(__file__))
import sdist
cache_f=os.path.join(os.path.dirname(__file__),'sdist-cache.json')
try: cache=json.load(open(cache_f))
except Exception: cache={}
rows=[]
for f in sys.argv[1:]:
  for l in open(f):
    x=json.loads(l)
    if x.get('out') and x.get('dist') is not None:
      k=x['key']
      if k not in cache:
        try: cache[k]=sdist.sdist(x['out'])[0]
        except Exception as e: cache[k]=None
      x['sd']=cache[k]; rows.append(x)
json.dump(cache,open(cache_f,'w'))
rows=[r for r in rows if r['sd'] is not None]
rows.sort(key=lambda r:r['sd'])
seen=set()
for r in rows:
  if r['key'] in seen: continue
  seen.add(r['key'])
  print(r['sd'],r['dist'],r['size'],r['jeq'],r['key'],os.path.basename(r['file']))
  if len(seen)>=int(os.environ.get('N','15')): break
