import json,sys
flt=sys.argv[1] if len(sys.argv)>1 else ''
for l in open('results.jsonl'):
    r=json.loads(l)
    if flt in r['ckey']:
        b=r.get('borrow') or []
        bb=[x for x in b if 'j' in x.split()[1][:1]][:1] if b else []
        print(f"{r['status'][:8]:8} d={r.get('dist')} sl={r.get('slots')} sz={r.get('size')} lost={r.get('lost')} {bb[0][6:30] if bb else ''} :: {r['ckey']}")
