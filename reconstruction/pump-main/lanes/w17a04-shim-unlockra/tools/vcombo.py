#!/usr/bin/env python3
"""vcombo.py <m.ll> <out.jsonl> <combos.json> [jobs]: apply several vscreen-style single edits at once
(combos.json = [["vl:1821","vs:244"], ...]; edit kinds vl/vs/bl/bu as in vscreen.py) and score each combo. Experiment only."""
import sys,os,re,json
sys.path.insert(0,os.path.dirname(__file__))
import vscreen
from multiprocessing import Pool
def build(t,combo):
    i=t.index('\ndefine '); j=t.index('\n}\n',i)
    pre,body,post=t[:i],t[i:j],t[j:]
    L=body.split('\n'); md=max([int(x) for x in re.findall(r'^!(\d+) = ',t,re.M)]+[0])+1; extra=''
    for nm in combo:
        kd,k=nm.split(':'); k=int(k); l=L[k]
        if kd=='vl': assert re.search(r'= load (?!volatile)',l),nm; L[k]=l.replace('= load ','= load volatile ',1)
        elif kd=='vs': assert re.match(r'\s+store (?!volatile)',l),nm; L[k]=l.replace('store ','store volatile ',1)
        elif kd in ('bl','bu'):
            assert re.match(r'\s+br i1 %',l) and '!prof' not in l,nm
            w='2000, i32 1' if kd=='bl' else '1, i32 2000'
            L[k]=l+f', !prof !{md}'; extra+=f'\n!{md} = !{{!"branch_weights", i32 {w}}}'; md+=1
        else: raise SystemExit('bad '+nm)
    return pre+'\n'.join(L)+post+extra+'\n'
if __name__=='__main__':
    a=sys.argv[1:]; t=open(a[0]).read(); out=a[1]; combos=json.load(open(a[2])); jobs=int(a[3]) if len(a)>3 else 4
    J=[('+'.join(c),build(t,c)) for c in combos]
    with Pool(jobs,initializer=vscreen.init) as p, open(out,'a') as f:
        for r in p.imap_unordered(vscreen.run,J):
            r['combo']=r['name'].split('+'); f.write(json.dumps(r)+'\n'); f.flush()
