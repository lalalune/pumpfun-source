import sys,json
for l in open(sys.argv[1] if len(sys.argv)>1 else 'res.jsonl'):
    d=json.loads(l); r=d['res'] or {}; print('%-28s %s %s %s %s'%(d['trial'], r.get('ratio'), r.get('bytes'), r.get('slots_diff'), r.get('error','')))
