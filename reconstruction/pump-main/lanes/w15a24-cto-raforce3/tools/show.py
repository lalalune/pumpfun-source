import json,sys
for f in sys.argv[1:]:
  print('==',f)
  for x in sorted((json.loads(l) for l in open(f) if l.strip()),key=lambda x:x['name']):
    print(f"{x['name']:10} {x.get('ratio')} {x.get('slots')} {x.get('bytes')} L2={x.get('L2')} {x.get('error','')[:80]}")
