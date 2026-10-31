#!/usr/bin/env python3
"""tbl.py <name>...: rx/<name>/m.ll -> m.s, B.s, Br.s; M/bytes/jM, fbound fR/rfR/rfjR and errseq for each (oracle only)."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, sub, eseq, fbound
spec=open(O+'/tmp/Bspec963.txt').read().strip().split(',')
def one(n):
    d=f'{O}/rx/{n}'
    if not os.path.exists(d+'/m.s'): subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
    out={'name':n}
    names,new,miss=sub.border2(O+'/rx/m/m.s',d+'/m.s',spec)
    for tag,rev in (('-',None),('B',0),('Br',1)):
        p=d+'/m.s' if tag=='-' else d+f'/{tag}.s'
        if tag!='-':
            t,fl=sub.emit(d+'/m.s',new,rev); open(p,'w').write(t)
        s=sc.score(p); f=fbound.bound(p)
        out[tag]={'r':s['ratio'],'M':s['M'],'b':s['bytes'],'jM':s['jM'],'fR':f['fR'],'rfR':f['rfR'],'rfjR':f['rfjR'],'err':' '.join(map(str,eseq.seq(sc.fn(p))[7:11]))}
    out['miss']=miss
    return out
for n in sys.argv[1:]:
    r=one(n); print(json.dumps(r))
