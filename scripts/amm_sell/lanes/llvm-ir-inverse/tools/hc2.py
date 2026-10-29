# hc2.py FN START_JSON PART NPART OUT : single-move scan, log only strict slot improvements
import sys, json; sys.path.insert(0,'tools'); import irfn
f=irfn.Fn(sys.argv[1])
def after(o,a,b):
    o=[x for x in o if x!=a]; o.insert(o.index(b)+1,a); return o
o=list(f.order0)
for a,b in json.loads(sys.argv[2]): o=after(o,a,b)
part,npart=int(sys.argv[3]),int(sys.argv[4])
out=open(sys.argv[5],'w')
base=f.run(o); print(json.dumps({'base':base}),file=out,flush=True)
n=0
for i,x in enumerate(o[1:],1):
    if i%npart!=part: continue
    for p in range(1,len(o)):
        oo=[y for y in o if y!=x]; oo.insert(p,x)
        if oo==o: continue
        r=f.run(oo); n+=1
        if 'error' in r: continue
        if r['slot_diffs']<base['slot_diffs'] or r['masked_equal']:
            print(json.dumps({'x':x,'after':oo[p-1],'r':r}),file=out,flush=True)
        if r['masked_equal']:
            print(json.dumps({'FOUND':oo}),file=out,flush=True)
print(json.dumps({'done':n}),file=out,flush=True)
