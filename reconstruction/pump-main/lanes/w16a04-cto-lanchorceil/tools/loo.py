#!/usr/bin/env python3
"""loo.py <rx> <forces> <tag> [procs]: leave-one-out joint value of each sticky force (experiment only).
For the full set and for each set minus one force: sticky-forced llc (obj + PEI MIR), M, Mperm, joint Mhc (permhc), bytes.
Writes data/loo-<tag>.jsonl."""
import sys,os,json,subprocess,shutil,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
LLC=O+'/llvmb/bin/llc'; A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
def run(job):
    name,rx,F=job; d=f'{O}/rx/loo_{name}'; os.makedirs(d,exist_ok=True)
    env=dict(os.environ,RAPRIO_STICKY='1',RAPRIO_FORCE=F)
    subprocess.run([LLC,*A,f'{O}/rx/{rx}/m.ll','-stop-after=prologepilog','-o',d+'/pei.mir'],env=env,check=True,capture_output=True)
    subprocess.run([LLC,*A,f'{O}/rx/{rx}/m.ll','-filetype=obj','-o',d+'/f.o'],env=env,check=True,capture_output=True)
    import oracle; b=oracle.elf_fn(d+'/f.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b)
    p=subprocess.run(['python3',T+'/permhc.py',d],capture_output=True,text=True)
    r=json.loads(p.stdout.strip().splitlines()[-1]); shutil.rmtree(d,ignore_errors=True)
    return {'name':name,'force':F,'bytes':len(b),'M':r['M'],'Mperm':r['Mperm'],'joint':r['Mhc']}
if __name__=='__main__':
    rx,F,tag=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 2
    fs=[x for x in F.split(',') if x]
    jobs=[(f'{tag}_all',rx,F)]+[(f'{tag}_no{f.replace("=","_")}',rx,','.join(y for y in fs if y!=f)) for f in fs]
    out=open(f'{O}/data/loo-{tag}.jsonl','a')
    with mp.Pool(n) as p:
        for r in p.imap_unordered(run,jobs):
            out.write(json.dumps(r)+'\n'); out.flush(); print(json.dumps(r),flush=True)
