# identity check of .data.rel.ro text pointers: does each original target window pair with the candidate target?
import sys,json,bisect
sys.argv=[sys.argv[0]]+sys.argv[1:]
exec(open(__file__.rsplit('/',1)[0]+'/drr.py').read().split("diff=")[0])
R=json.load(open(sys.argv[2])); P={int(k,16):int(v,16) for k,v in R['pair'].items()}
ost=sorted(P); 
ok=bad=0; badl=[]
for i,(x,y) in enumerate(zip(o,c)):
    if x[0]=='P' and x[1]=='.text':
        oa=OS['.text']['addr']+x[2]; ca=CS['.text']['addr']+y[2] if y[0]=='P' else None
        j=bisect.bisect_right(ost,oa)-1; ws=ost[j]
        exp=P[ws]+(oa-ws)
        if ca==exp: ok+=1
        else: bad+=1; badl.append((hex(i*8),hex(oa),hex(ws),hex(exp),hex(ca) if ca else y))
print('text ptr slots ok',ok,'bad',bad)
for b in badl[:20]: print(b)
