import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T); import mirprob
B=['bb6.i','bb7.i','bb14.i','bb16.i','bb22.i','bb23.i','bb28.i','bb37.i','bb38.i','bb44.i','bb45.i','bb47.i','bb95.i','bb52.i','bb54.i','bb10.i','bb17.i','bb27.i','bb79.i','bb48.i','bb39.i','bb32.i']
W=[None,'1:1','20:12','12:20','1:8','8:1']
cur=eval(os.environ.get('WSTART','{}')); tag=os.environ.get('WTAG','g'); cap=int(os.environ.get('BCAP','99999'))
def ev(c):
    r=mirprob.run(O+'/tmp/pre.mir',O+'/tmp/mg'+tag,','.join(f'{k}={v}' for k,v in c.items() if v))
    return r.get('M',0),r.get('bytes'),r.get('jM')
best=ev(cur); print('start',cur,best,flush=True)
for rnd in range(4):
    imp=False
    for b in B:
        for w in W:
            if cur.get(b)==w: continue
            c=dict(cur); c[b]=w; r=ev(c)
            if r[1] and r[1]<=cap and (r[0]>best[0] or (r[0]==best[0] and r[1]<best[1])): best=r; cur=c; imp=True; print('imp',b,w,best,flush=True)
    if not imp: break
print('final',{k:v for k,v in cur.items() if v},best,flush=True)
