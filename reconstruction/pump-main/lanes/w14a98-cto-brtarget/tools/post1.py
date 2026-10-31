#!/usr/bin/env python3
"""post1.py <name>: rx/<name>/m.ll -> m.s; M, bytes, Br (corrected 963 spec, flips) M/bytes, errseq."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, sub, eseq
n=sys.argv[1]; d=f'{O}/rx/{n}'
subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
s=sc.score(d+'/m.s'); s.pop('ch',None)
spec=open(O+'/tmp/Bspec963.txt').read().strip().split(',')
res=json.load(open(d+'/res.json')); out={'name':n,'ratio':res['ratio'],'bytes':s['bytes'],'M':s['M'],'jM':s['jM'],'eq_main':res.get('eq_main')}
try:
    names,new,miss=sub.border2(O+'/rx/m/m.s',d+'/m.s',spec); t,fl=sub.emit(d+'/m.s',new,1); b=sub.score(t,d+'/Br.s')
    out.update(Br_M=b['M'],Br_b=b['bytes'],Br_jM=b['jM'],flips=fl,miss=miss)
except Exception as e: out['Br_err']=repr(e)[:200]
out['eseq']=' '.join(map(str,eseq.seq(sc.fn(d+'/m.s'))[:12]))
print(json.dumps(out))
