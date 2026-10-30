#!/usr/bin/env python3
"""objsplit.py <tag> <objid>[,..] : on top of the real build, remap only the accesses of these objects to the original's per-access offsets (text-level)"""
import sys,re,difflib,subprocess,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import slotpin as S
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tag=sys.argv[1]; ids=[int(x) for x in sys.argv[2].split(',')]; d=f'{O}/q/{tag}'
ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
a,ta=S._rd(d+'/direct.txt'); r,_=S._rd(d+'/real.txt'); b,tb=S._rd(O+'/orig_fn.txt'); oa=S._offs(a); out=list(r); n=0
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1):
        x=oa[i1+k]
        if x is None: continue
        if any(ob[i]['off']<=x<ob[i]['off']+ob[i]['size'] for i in ids): out[i1+k]=b[j1+k]; n+=1
L=[l.split(None,1)[0] for l in open(d+'/real.txt')]
open(d+'/_os.txt','w').write(''.join(f'{x}  {y}\n' for x,y in zip(L,out)))
s=subprocess.run(['python3',O+'/tools/oratio.py',O+'/orig_fn.txt',d+'/_os.txt'],capture_output=True,text=True).stdout.split()
print(tag,ids,'remapped',n,'ratio',s[1],'M',round(float(s[1])*(3339+int(s[4]))/2))
