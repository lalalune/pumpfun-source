#!/usr/bin/env python3
"""and1.py <name> <which> : post-opt IR and-1 forms (w14a78): replace `%v = icmp eq i8 %x, 0` by `trunc i8 %x to i1` + xor (no BPI zero
heuristic, ISel and 1). which: tag306 (%trunc.not.not.i), tag298 (%trunc11 / trunc8), holder (%_0.sroa.0.0.off0.i.not), he (%_31.not.i), hr (%_19.not.i); '+' joins."""
import sys,os,re,json,subprocess; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, eseq
n,which=sys.argv[1],sys.argv[2]; t=open(f'{O}/rx/{n}/mi.ll').read()
V={'tag306':r'%trunc\.not\.not\.i','tag298':r'%trunc(?:11|8)\.not\.not\.i','holder':r'%_0\.sroa\.0\.0\.off0\.i\.not','he':r'%_31\.not\.i','hr':r'%_19\.not\.i'}
k=0
for w in which.split('+'):
    pat=re.compile(r'\n  ('+V[w]+r') = icmp eq i8 (%[\w.]+), 0\n'); m=pat.search(t); assert m,w
    v,x=m.group(1),m.group(2); k+=1
    t=t[:m.start()]+f'\n  %a1_{k} = trunc i8 {x} to i1\n  {v} = xor i1 %a1_{k}, true\n'+t[m.end():]
d=f'{O}/rx/{n}_a1_{which.replace("+","_")}'; os.makedirs(d,exist_ok=True); open(d+'/mi.ll','w').write(t)
subprocess.run(['bash',T+'/llc.sh',d+'/mi.ll',d+'/m.s'],check=True)
s=sc.score(d+'/m.s'); s.pop('ch',None); s['eseq']=' '.join(map(str,eseq.seq(sc.fn(d+'/m.s'))[:10])); print(n,which,json.dumps({x:s[x] for x in ('bytes','M','jM','fM','skM','eseq')}))
