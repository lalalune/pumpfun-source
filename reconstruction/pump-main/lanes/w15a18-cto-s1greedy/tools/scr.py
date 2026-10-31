#!/usr/bin/env python3
"""scr.py <m.ll> <jobs.jsonl> <out.jsonl> [nproc]: per job (prio/force/hint/casc/weight/nohint env for the private llc)
run cell.sh in a temp dir and record free / pinV / pinA (ratio, M, bytes)."""
import sys,os,json,subprocess,tempfile,re,shutil,multiprocessing as mp
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy')
def parse(s):
    r={}
    m=re.search(r'free: ratio (\S+) M (\d+) bytes (\d+)',s)
    if m: r['ratio']=float(m.group(1)); r['M']=int(m.group(2)); r['bytes']=int(m.group(3))
    for k in ('pinV','pinA'):
        m=re.search(k+r': (\{.*?\})',s)
        if m:
            d=json.loads(m.group(1)); r[k]=d.get('M'); r[k+'r']=d.get('ratio')
    return r
def run(a):
    m,job=a; env=dict(os.environ)
    for k in list(env):
        if k.startswith('RAPRIO_'): env.pop(k)
    for k in ('prio','force','hint','casc','weight','nohint'):
        if job.get(k): env['RAPRIO_'+k.upper()]=job[k]
    d=tempfile.mkdtemp(dir=O+'/tmp')
    p=subprocess.run(['bash',O+'/w6/tools/cell.sh',m,d],env=env,capture_output=True,text=True)
    res=dict(job); res.update(parse(p.stdout))
    if 'M' not in res: res['error']=(p.stderr or p.stdout)[-300:]
    if job.get('keep'): shutil.copytree(d,job['keep'],dirs_exist_ok=True)
    shutil.rmtree(d,ignore_errors=True)
    return res
if __name__=='__main__':
    m,jf,of=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 4
    os.makedirs(O+'/tmp',exist_ok=True)
    jobs=[json.loads(l) for l in open(jf) if l.strip()]
    with mp.Pool(n) as p, open(of,'a') as f:
        for res in p.imap_unordered(run,[(m,j) for j in jobs]):
            f.write(json.dumps(res)+'\n'); f.flush()
