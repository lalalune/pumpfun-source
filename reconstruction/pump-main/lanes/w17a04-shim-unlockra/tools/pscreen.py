#!/usr/bin/env python3
"""pscreen.py <m.ll> <bp.txt> <out.jsonl> <factors,...> [jobs] [--base combo.json]: branch-probability perturbation screen.
For every conditional br in admin_cto::execute, set branch_weights so the true-edge probability is p0*f (p0 = the default
BPI probability from `opt -passes=print<branch-prob>`), llc, score. Models llvm.expect.with.probability shims. Experiment only."""
import sys,os,re,json
sys.path.insert(0,os.path.dirname(__file__))
import vscreen
from multiprocessing import Pool
def blocks(L):
    cur='start'; m={}
    for k,l in enumerate(L):
        mm=re.match(r'^([\w.$"\-]+):',l)
        if mm: cur=mm.group(1).strip('"')
        if re.match(r'\s+br i1 %',l): m[k]=cur
    return m
def p0map(bp):
    P={}
    for l in open(bp):
        mm=re.match(r'\s+edge %(\S+) -> %(\S+) probability is 0x([0-9a-f]+) / 0x80000000',l)
        if mm: P[(mm.group(1).strip('"'),mm.group(2).strip('"'))]=int(mm.group(3),16)/0x80000000
    return P
def build(t,P,edits):
    i=t.index('\ndefine '); j=t.index('\n}\n',i); pre,body,post=t[:i],t[i:j],t[j:]
    L=body.split('\n'); B=blocks(L); md=max([int(x) for x in re.findall(r'^!(\d+) = ',t,re.M)]+[0])+1; extra=''
    for k,f in edits:
        l=L[k]; assert k in B and '!prof' not in l,(k,l)
        tt=re.match(r'\s+br i1 %\S+, label %("[^"]+"|\S+), label',l).group(1).strip('"').rstrip(',')
        p0=P[(B[k],tt)]; p=min(max(p0*f,1e-7),1-1e-7)
        a=max(1,round(p*(1<<24))); b=max(1,round((1-p)*(1<<24)))
        L[k]=l+f', !prof !{md}'; extra+=f'\n!{md} = !{{!"branch_weights", i32 {a}, i32 {b}}}'; md+=1
    return pre+'\n'.join(L)+post+extra+'\n'
_T=None;_P=None
def winit(m,bp):
    global _T,_P
    vscreen.init(); _T=open(m).read(); _P=p0map(bp)
def wrun(e):
    k,f=e; return vscreen.run((f'pw:{k}:{f}',build(_T,_P,[(k,f)])))
if __name__=='__main__':
    a=sys.argv[1:]; t=open(a[0]).read(); P=p0map(a[1]); out=a[2]; F=[float(x) for x in a[3].split(',')]
    jobs=int(a[4]) if len(a)>4 and a[4].isdigit() else 4
    i=t.index('\ndefine '); j=t.index('\n}\n',i); L=t[i:j].split('\n'); B=blocks(L)
    J=[]
    for k in sorted(B):
        if '!prof' in L[k]: continue
        for f in F: J.append((k,f))
    print(len(J),'jobs',file=sys.stderr)
    with Pool(jobs,initializer=winit,initargs=(a[0],a[1])) as p, open(out,'a') as fo:
        for r in p.imap_unordered(wrun,J):
            k=int(r['name'].split(':')[1]); r['line']=L[k].strip()[:140]; fo.write(json.dumps(r)+'\n'); fo.flush()
