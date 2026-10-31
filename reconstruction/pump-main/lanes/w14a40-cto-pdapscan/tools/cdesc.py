#!/usr/bin/env python3
"""cdesc.py <start.ll> <dir> <rounds> <lo> <hi> clones...: pscan coordinate descent (place -> pp on top-4 -> accept best) per clone,
accepting a change only if ratio improves with bytes in [lo,hi]. Writes <dir>/log.jsonl and <dir>/cur.ll."""
import sys,os,json,subprocess,shutil
T=os.path.dirname(os.path.abspath(__file__))
st,D,R,lo,hi=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]); C=sys.argv[6:]
NT=os.environ.get('NT','6'); os.makedirs(D,exist_ok=True); cur=D+'/cur.ll'; shutil.copy(st,cur)
log=open(D+'/log.jsonl','a')
def scan(mode,x,out,place=None):
    e=dict(os.environ,MODE=mode,XVAL=x)
    if place: e['PLACE']=place
    subprocess.run(['python3',T+'/pscan.py',cur,'x',out,NT],env=e,capture_output=True)
    return [json.loads(l) for l in open(out)] if os.path.exists(out) else []
def ok(r): return 'ratio' in r and lo<=r['bytes']<=hi
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g); O=g['orig_window']()
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def score(p):
    subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',D+'/s.o'],check=True)
    c=g['elf_fn'](D+'/s.o',g['KEEP']); r,sd=g['metric'](c,O); return round(r,5),len(c),sd
best=score(cur); print('start',best,flush=True); log.write(json.dumps({'start':best})+'\n')
for rd in range(R):
    moved=False
    for x in C:
        n=x.strip('%').replace('.','')
        P=scan('place',x,D+'/%d_%s_place.jsonl'%(rd,n))
        cands=[r for r in P if ok(r)]
        cands.sort(key=lambda r:-r['ratio']); tops=[]
        for r in cands:
            p=r['lab'].split(':')[0]
            if p not in tops: tops.append(p)
            if len(tops)==4: break
        A=list(cands)
        for p in tops: A+= [r for r in scan('pp',x,D+'/%d_%s_pp_%s.jsonl'%(rd,n,p),p) if ok(r)]
        A+= [r for r in scan('pp',x,D+'/%d_%s_pp_cur.jsonl'%(rd,n)) if ok(r)]
        if not A: print(rd,x,'no valid',flush=True); continue
        b=max(A,key=lambda r:r['ratio'])
        rec={'round':rd,'clone':x,'best':b,'cur':best,'n':len(A)}
        if b['ratio']>best[0]+1e-6:
            e=dict(os.environ,MODE='dump',XVAL=x,JOB=b['lab'])
            subprocess.run(['python3',T+'/pscan.py',cur,'x',D+'/new.ll'],env=e,check=True)
            s=score(D+'/new.ll'); rec['rescore']=s
            if s[0]>best[0]+1e-6 and lo<=s[1]<=hi:
                shutil.copy(D+'/new.ll',cur); shutil.copy(D+'/new.ll',D+'/r%d_%s.ll'%(rd,n)); best=s; moved=True; rec['accepted']=True
        print(json.dumps(rec),flush=True); log.write(json.dumps(rec)+'\n'); log.flush()
    if not moved: break
print('final',best,flush=True)
