import json,glob,sys
from collections import Counter
pat=sys.argv[1] if len(sys.argv)>1 else 'ps/*_place.jsonl'; B=int(sys.argv[2]) if len(sys.argv)>2 else 27400
for f in sorted(glob.glob(pat)):
    R=[json.loads(l) for l in open(f)]; R=[r for r in R if 'ratio' in r]
    c=Counter(r['bytes'] for r in R)
    R4=sorted([r for r in R if r['bytes']==B],key=lambda r:-r['ratio'])[:5]
    print(f, len(R), dict(sorted(c.items())), [(r['lab'].split(':')[0],r['ratio']) for r in R4])
