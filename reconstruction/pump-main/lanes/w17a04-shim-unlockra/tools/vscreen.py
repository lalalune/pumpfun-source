#!/usr/bin/env python3
"""vscreen.py <m.ll> <out.jsonl> <kinds> [jobs] [--base-edits f.py]
IR-level shim screen on the slimmed post-opt module: for each candidate instruction in admin_cto::execute apply ONE edit
  vl  : load -> load volatile           (read_volatile pin)
  vs  : store -> store volatile         (write_volatile pin)
  bl/bu: cond br gets branch_weights 2000:1 / 1:2000 (likely / unlikely on the true edge)
then SDK llc (fastbuild flags), extract the fn, score ratio/bytes/M vs the original window. Experiment only."""
import sys,os,re,subprocess,json,tempfile
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(__file__))
import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
LLC=os.environ.get('VLLC',SDK+'/llc')
ORIG=None
def init():
    global ORIG,OM
    ORIG=oracle.orig_window(); OM=oracle.mask(ORIG)
import difflib
def score(cand):
    c=oracle.mask(cand)
    sm=difflib.SequenceMatcher(None,OM,c,autojunk=False)
    M=sum(b.size for b in sm.get_matching_blocks())
    return round(2*M/(len(OM)+len(c)),5),M
def run(job):
    name,text=job
    fd,o=tempfile.mkstemp(suffix='.o',dir='/tmp/claude-501'); os.close(fd)
    try:
        r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections','-','-filetype=obj','-o',o],input=text,capture_output=True,text=True,env=dict(os.environ))
        if r.returncode: return {'name':name,'err':r.stderr[-300:]}
        cand=oracle.elf_fn(o,oracle.KEEP)
        ra,M=score(cand)
        return {'name':name,'ratio':ra,'M':M,'bytes':len(cand)}
    finally:
        os.remove(o)
def main():
    a=sys.argv[1:]; src,out,kinds=a[0],a[1],a[2].split(','); jobs=int(a[3]) if len(a)>3 and a[3].isdigit() else 4
    t=open(src).read()
    i=t.index('\ndefine '); j=t.index('\n}\n',i)
    pre,body,post=t[:i],t[i:j],t[j:]
    L=body.split('\n')
    md=max([int(x) for x in re.findall(r'^!(\d+) = ',t,re.M)]+[0])+1
    JOBS=[]
    for k,l in enumerate(L):
        if 'vl' in kinds and re.search(r'= load (?!volatile)',l):
            L2=L[:]; L2[k]=l.replace('= load ','= load volatile ',1); JOBS.append((f'vl:{k}',pre+'\n'.join(L2)+post))
        if 'vs' in kinds and re.match(r'\s+store (?!volatile)',l):
            L2=L[:]; L2[k]=l.replace('store ','store volatile ',1); JOBS.append((f'vs:{k}',pre+'\n'.join(L2)+post))
        if re.match(r'\s+br i1 %',l) and '!prof' not in l:
            for kd,w in (('bl','2000, i32 1'),('bu','1, i32 2000')):
                if kd in kinds:
                    L2=L[:]; L2[k]=l+f', !prof !{md}'; JOBS.append((f'{kd}:{k}',pre+'\n'.join(L2)+post+f'\n!{md} = !{{!"branch_weights", i32 {w}}}\n'))
    JOBS.insert(0,('base:0',t))
    print(len(JOBS),'jobs',file=sys.stderr)
    with Pool(jobs,initializer=init) as p, open(out,'a') as f:
        for r in p.imap_unordered(run,JOBS):
            k=int(r['name'].split(':')[1]); r['line']=L[k].strip()[:160]
            f.write(json.dumps(r)+'\n'); f.flush()
if __name__=='__main__': main()
