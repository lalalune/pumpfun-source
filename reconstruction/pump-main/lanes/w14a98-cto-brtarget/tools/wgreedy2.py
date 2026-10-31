import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import irord
B=['bb6.i','bb7.i','bb14.i','bb16.i','bb22.i','bb23.i','bb28.i','bb37.i','bb38.i','bb44.i','bb45.i','bb47.i','bb95.i','bb52.i','bb54.i']
W=[None,'1:1','20:12','12:20','2:1','1:2']
import os as _o; cur=eval(_o.environ.get('WSTART','{}'))
def ev(c):
    pr=','.join(f'{k}={v}' for k,v in c.items() if v)
    r=irord.run(O+'/tmp/mn.ll',O+'/tmp/wg'+_o.environ.get('WTAG',''),'',pr or None)
    return r.get('M',0),r.get('bytes'),r.get('jM'),r.get('fM')
O=os.path.dirname(T)
best=ev(cur); print('start',cur,best,flush=True)
for rnd in range(3):
    imp=False
    for b in B:
        for w in W:
            if cur.get(b)==w: continue
            c=dict(cur); c[b]=w
            r=ev(c)
            if r[0]>best[0]: best=r; cur=c; imp=True; print('imp',b,w,best,cur,flush=True)
    if not imp: break
print('final',cur,best)
