import json,sys
R=[json.loads(l) for l in open(sys.argv[1])]
E=[r for r in R if 'err' in r]
R=[r for r in R if 'ratio' in r]
by={}
for r in R: by.setdefault(r['bytes'],[]).append(r)
for b in sorted(by):
    rs=sorted(by[b],key=lambda r:-r['ratio'])[:int(sys.argv[2]) if len(sys.argv)>2 else 5]
    print(b,len(by[b]),[(r['lab'],r['ratio']) for r in rs])
print('errs',len(E))
