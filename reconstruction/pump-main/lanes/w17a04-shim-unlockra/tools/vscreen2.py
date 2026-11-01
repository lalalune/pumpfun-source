#!/usr/bin/env python3
"""vscreen2.py <m.ll> <out.jsonl> <kinds> [jobs]: lazy version of vscreen.py (edits built in the workers). Experiment only."""
import sys,os,re,json
sys.path.insert(0,os.path.dirname(__file__))
import vscreen,vcombo
from multiprocessing import Pool
_T=None
def winit(m):
    global _T; vscreen.init(); _T=open(m).read()
def wrun(nm): return vscreen.run((nm,vcombo.build(_T,[nm])))
if __name__=='__main__':
    a=sys.argv[1:]; m,out,kinds=a[0],a[1],a[2].split(','); jobs=int(a[3]) if len(a)>3 else 4
    t=open(m).read(); i=t.index('\ndefine '); j=t.index('\n}\n',i); L=t[i:j].split('\n')
    J=[]
    for k,l in enumerate(L):
        if 'vl' in kinds and re.search(r'= load (?!volatile)',l): J.append(f'vl:{k}')
        if 'vs' in kinds and re.match(r'\s+store (?!volatile)',l): J.append(f'vs:{k}')
        if re.match(r'\s+br i1 %',l) and '!prof' not in l:
            for kd in ('bl','bu'):
                if kd in kinds: J.append(f'{kd}:{k}')
    print(len(J),'jobs',file=sys.stderr,flush=True)
    with Pool(jobs,initializer=winit,initargs=(m,)) as p, open(out,'a') as f:
        for r in p.imap_unordered(wrun,J):
            k=int(r['name'].split(':')[1]); r['line']=L[k].strip()[:120]; f.write(json.dumps(r)+'\n'); f.flush()
