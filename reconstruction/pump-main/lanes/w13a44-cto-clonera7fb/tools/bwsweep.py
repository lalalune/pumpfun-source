#!/usr/bin/env python3
"""bwsweep.py <m.ll> <br text> <a:b>...: llcb for each weight on one branch (parallel)."""
import sys,os,subprocess,tempfile,json,concurrent.futures as cf
T=os.path.dirname(os.path.abspath(__file__))
m,br=sys.argv[1],sys.argv[2]; ws=sys.argv[3:]
t=open(m).read(); line='  '+br.strip()+'\n'; assert t.count(line)==1,t.count(line)
def run(w):
    a,b=w.split(':'); d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(m)))
    open(d+'/m.ll','w').write(t.replace(line,'  '+br.strip()+', !prof !999991\n')+'\n!999991 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b))
    r=subprocess.run([sys.executable,T+'/llcb.py',d+'/m.ll'],capture_output=True,text=True).stdout.strip().split('\n')[-1]
    subprocess.run(['rm','-rf',d]); return w+' '+r
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(run,ws): print(r)
