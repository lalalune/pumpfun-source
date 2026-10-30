#!/usr/bin/env python3
"""bwscan.py <m.ll> <outdir> [jobs]: for every conditional br in execute, llc with branch weights 1:2000 and 2000:1;
prints JSON lines (llcb objectives + payload reg) sorted by clonefeat then ratio."""
import sys,os,re,subprocess,json,concurrent.futures as cf
T=os.path.dirname(os.path.abspath(__file__))
m,od=sys.argv[1],sys.argv[2]; jobs=int(sys.argv[3]) if len(sys.argv)>3 else 4
os.makedirs(od,exist_ok=True)
t=open(m).read()
s=t.index('admin_cto7execute'); s=t.rindex('\ndefine ',0,s); e=t.index('\n}\n',s)
body=t[s:e]
brs=[mm for mm in re.finditer(r'\n(  br i1 [^\n]*?)(, !prof ![0-9]+)?(?=\n)',body)]
def run(k):
    i,w=k; mm=brs[i]
    nb=body[:mm.start()]+'\n'+mm.group(1)+', !prof !999999'+body[mm.end():]
    tt=t[:s]+nb+t[e:]+'\n!999999 = !{!"branch_weights", i32 %d, i32 %d}\n'%w
    d=os.path.join(od,'b%d_%d'%(i,w[0])); os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(tt)
    r=subprocess.run([sys.executable,T+'/llcb.py',d+'/m.ll'],capture_output=True,text=True).stdout.strip().split('\n')[-1]
    os.remove(d+'/m.ll'); os.rmdir(d)
    try: j=json.loads(r)
    except Exception: j={'err':r[-200:]}
    j['br']=i; j['w']='%d:%d'%w; j['src']=mm.group(1).strip()[:80]
    return j
ks=[(i,w) for i in range(len(brs)) for w in ((1,2000),(2000,1))]
with cf.ThreadPoolExecutor(jobs) as ex: res=list(ex.map(run,ks))
for j in res: print(json.dumps(j))
