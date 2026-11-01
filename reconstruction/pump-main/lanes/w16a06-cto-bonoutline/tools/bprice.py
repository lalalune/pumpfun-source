#!/usr/bin/env python3
"""bprice.py <name> [ref=main]: fixed-RA B and Br (content-mapped from ref's spec names) on rx/<name>/m.s.
Prints M/jM/fM/skM/bytes for plain, B, Br; errseq; missing spec blocks."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, sub, eseq
n=sys.argv[1]; ref=sys.argv[2] if len(sys.argv)>2 else 'main'; d=f'{O}/rx/{n}'
if not os.path.exists(d+'/m.s'): subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
spec=open(O+'/tmp/'+os.environ.get('SPEC','Bspec_cur.txt')).read().strip().split(',')
def sc_(p):
    s=sc.score(p); s.pop('ch',None); return s
out={'name':n}
s=sc_(d+'/m.s'); out['plain']={k:s[k] for k in ('bytes','M','jM','fM','skM')}
out['eseq']=' '.join(map(str,eseq.seq(sc.fn(d+'/m.s'))[:10]))
names,new,miss=sub.border2(O+f'/rx/{ref}/m.s',d+'/m.s',spec); out['miss']=miss
for tag,rev in (('B',0),('Br',1)):
    t,fl=sub.emit(d+'/m.s',new,rev); b=sub.score(t,d+f'/{tag}.s')
    out[tag]={k:b[k] for k in ('bytes','M','jM','fM','skM')}; out[tag]['flips']=fl
    out[tag+'_eseq']=' '.join(map(str,eseq.seq(sc.fn(d+f'/{tag}.s'))[:10]))
print(json.dumps(out))
