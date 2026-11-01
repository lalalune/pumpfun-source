#!/usr/bin/env python3
"""pabs.py <m.ll> <out.jsonl> <jobs> <spec>...: spec = k1=p1[,k2=p2...] sets branch k's TRUE-edge probability to p (absolute). Experiment only."""
import sys,os,re,json
sys.path.insert(0,os.path.dirname(__file__))
import vscreen
from multiprocessing import Pool
def build(t,edits):
    i=t.index('\ndefine '); j=t.index('\n}\n',i); pre,body,post=t[:i],t[i:j],t[j:]
    L=body.split('\n'); md=max([int(x) for x in re.findall(r'^!(\d+) = ',t,re.M)]+[0])+1; extra=''
    for k,p in edits:
        l=L[k]; assert re.match(r'\s+br i1 %',l) and '!prof' not in l,(k,l)
        a=max(1,round(p*(1<<30))); b=max(1,round((1-p)*(1<<30)))
        L[k]=l+f', !prof !{md}'; extra+=f'\n!{md} = !{{!"branch_weights", i32 {a}, i32 {b}}}'; md+=1
    return pre+'\n'.join(L)+post+extra+'\n'
_T=None
def winit(m):
    global _T; vscreen.init(); _T=open(m).read()
def wrun(spec):
    ed=[(int(x.split('=')[0]),float(x.split('=')[1])) for x in spec.split(',')]
    return vscreen.run((spec,build(_T,ed)))
if __name__=='__main__':
    a=sys.argv[1:]; m,out,jobs=a[0],a[1],int(a[2]); specs=a[3:]
    with Pool(jobs,initializer=winit,initargs=(m,)) as p, open(out,'a') as fo:
        for r in p.imap_unordered(wrun,specs): fo.write(json.dumps(r)+'\n'); fo.flush(); print(json.dumps(r),flush=True)
