#!/usr/bin/env python3
"""retune.py <m.ll> <out.jsonl> <jobs> <k=p>...: replace the !prof of already-weighted branch k with expect.with.probability weights for p (true edge). Experiment only."""
import sys,os,re,json,math
sys.path.insert(0,os.path.dirname(__file__))
import vscreen
from multiprocessing import Pool
def bw(p): return math.ceil(p*(2**31-2)+1.0), math.ceil((1-p)*(2**31-2)+1.0)
_T=None
def winit(m):
    global _T; vscreen.init(); _T=open(m).read()
def wrun(spec):
    t=_T; i=t.index('\ndefine '); j=t.index('\n}\n',i); pre,body,post=t[:i],t[i:j],t[j:]
    L=body.split('\n'); md=max([int(x) for x in re.findall(r'^!(\d+) = ',t,re.M)])+1; extra=''
    for e in spec.split(','):
        k,p=e.split('='); k=int(k); p=float(p); a,b=bw(p)
        L[k]=re.sub(r', !prof !\d+',f', !prof !{md}',L[k]); extra+=f'\n!{md} = !{{!"branch_weights", i32 {a}, i32 {b}}}'; md+=1
    return vscreen.run((spec,pre+'\n'.join(L)+post+extra+'\n'))
if __name__=='__main__':
    a=sys.argv[1:]; m,out,jobs=a[0],a[1],int(a[2])
    with Pool(jobs,initializer=winit,initargs=(m,)) as p, open(out,'a') as fo:
        for r in p.imap_unordered(wrun,a[3:]): fo.write(json.dumps(r)+'\n'); fo.flush()
