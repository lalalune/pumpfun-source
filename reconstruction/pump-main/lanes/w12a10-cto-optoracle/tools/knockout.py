#!/usr/bin/env python3
"""knockout.py <postinline_slim.ll> <prefix> [-j N] : per-pass-instance knockout of execute's own post-inline
function pipeline (F1 = CGSCC simplification, F2 = late optimization). Each variant removes one top-level pass
instance, replays the rest (opt), llc's execute and reports ratio vs the original."""
import sys,os,re,subprocess,json,concurrent.futures as cf
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a10-cto-optoracle')
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin')
src,prefix=sys.argv[1],sys.argv[2]; j=int(sys.argv[sys.argv.index('-j')+1]) if '-j' in sys.argv else 3
F1=open(L+'/ir-main/F1.txt').read().strip(); F2=open(L+'/ir-main/F2.txt').read().strip()
def split_top(s):
    head=s[:s.index('(')+1]; body=s[len(head):-1]
    out=[]; d=0; cur=''
    for ch in body:
        if ch in '(<': d+=1
        if ch in ')>': d-=1
        if ch==',' and d==0: out.append(cur); cur=''; continue
        cur+=ch
    out.append(cur); return head,out
h1,p1=split_top(F1); h2,p2=split_top(F2)
def pipe(q1,q2):
    return ('cgscc(function-attrs<skip-non-recursive-function-attrs>,argpromotion,'+h1+','.join(q1)+'),function-attrs),'
            'deadargelim,globalopt,globaldce,elim-avail-extern,rpo-function-attrs,'+h2+','.join(q2)+'),globaldce,constmerge')
vars_=[('base',p1,p2)]
for i,x in enumerate(p1): vars_.append(('F1-%02d-%s'%(i,re.sub(r'[^\w-]','',x.split('<')[0].split('(')[0])),p1[:i]+p1[i+1:],p2))
for i,x in enumerate(p2): vars_.append(('F2-%02d-%s'%(i,re.sub(r'[^\w-]','',x.split('<')[0].split('(')[0])),p1,p2[:i]+p2[i+1:]))
if '--list' in sys.argv:
    for n,_,_ in vars_: print(n)
    sys.exit()
def run(v):
    n,q1,q2=v; d=L+'/irexp/'+prefix+'-'+n; os.makedirs(d,exist_ok=True)
    r=subprocess.run([D+'/opt','-passes='+pipe(q1,q2),src,'-S','-o',d+'/in.ll'],capture_output=True,text=True)
    if r.returncode: return {'knob':n,'err':r.stderr[-200:]}
    p=subprocess.run(['python3',L+'/tools/oracle.py',d+'/in.ll',prefix+'-'+n],capture_output=True,text=True)
    try: res=json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: res={'err':(p.stdout+p.stderr)[-200:]}
    res['knob']=n
    for fn in ('in.ll','m.ll'):
        try: os.remove(d+'/'+fn)
        except OSError: pass
    return res
out=open(L+'/scan/'+prefix+'.jsonl','w')
with cf.ThreadPoolExecutor(j) as ex:
    for res in ex.map(run,vars_):
        out.write(json.dumps(res)+'\n'); out.flush()
        print('%.5f %6s %s %s'%(res.get('ratio',-1),res.get('bytes','-'),res['knob'],res.get('err','')[-80:]),flush=True)
