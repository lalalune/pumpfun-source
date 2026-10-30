#!/usr/bin/env python3
"""netreg.py name [step]: sk alignment orig vs cand; per orig region, bytes orig-only minus cand-only (positive = orig has more code there)."""
import difflib,sys,os,subprocess,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion')
n=sys.argv[1]; step=int(sys.argv[2],16) if len(sys.argv)>2 else 0x800
c=[l.split(None,1)[1].strip() for l in subprocess.run(['bash',O+'/tools/dis.sh',f'{O}/rx/{n}/m.o'],capture_output=True,text=True).stdout.split('\n') if len(l.split(None,1))>1]
o=[l.strip() for l in A.O]; oa=[];x=0
for t in o: oa.append(x); x+=16 if t.startswith('lddw') else 8
sz=lambda t:16 if t.startswith('lddw') else 8
sm=difflib.SequenceMatcher(None,[A.norm(t,True) for t in o],[A.norm(t,True) for t in c],autojunk=False)
D=collections.Counter()
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    r=oa[min(i1,len(o)-1)]//step*step
    D[r]+=sum(sz(t) for t in o[i1:i2])-sum(sz(t) for t in c[j1:j2])
print(n,' '.join(f'{k:#x}:{v:+d}' for k,v in sorted(D.items())),'total',sum(D.values()))
