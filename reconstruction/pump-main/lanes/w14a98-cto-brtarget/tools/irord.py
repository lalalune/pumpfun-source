#!/usr/bin/env python3
"""irord.py <m.ll> <out_prefix> <spec> [--prof blk=T:F,...] : reorder execute's post-opt IR blocks (spec = comma list of
short names placed in that order at the first listed block's position; to_string exits as exitNN.i), optional !prof on
a block's conditional br, llc, score with sc. Experiment only."""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sc
def split(t):
    m=re.search(r'define [^\n]*admin_cto7execute[^\n]*\{\n',t); s=m.end(); e=t.index('\n}\n',s)
    body=t[s:e]; parts=re.split(r'\n\n(?=[\w.$"-]+:)',body)
    blocks=[]
    for k,p in enumerate(parts):
        nm=p.split(':')[0] if k else 'start'
        if k==0 and not re.match(r'^[\w.$"-]+:',p): nm='__entry'
        blocks.append([nm,p])
    return t[:s],blocks,t[e:]
def short(n):
    n=n.strip('"')
    if 'to_string' in n: return n.split('E.')[-1]
    return n
def run(ll,outp,spec,prof=None,score=True):
    t=open(ll).read(); pre,bl,post=split(t); nm=[short(b[0]) for b in bl]
    if spec and spec.startswith('mv:'):
        for it in spec[3:].split(';'):
            a,b=it.split('@'); nm=[short(x[0]) for x in bl]; blk=bl[nm.index(a)]; bl=[x for x in bl if x is not blk]
            nm=[short(x[0]) for x in bl]; j=nm.index(b)+1; bl=bl[:j]+[blk]+bl[j:]
    elif spec:
        sp=spec.split(','); idx=[nm.index(x) for x in sp]; lo=min(idx)
        ent=[bl[i] for i in idx]; rest=[b for i,b in enumerate(bl) if i not in idx]
        restn=[short(b[0]) for b in rest]; anchor=nm[lo]
        # insert at original position of first-in-file listed block
        k=sum(1 for i in range(lo) if i not in idx)
        bl=rest[:k]+ent+rest[k:]
    md=''
    if prof:
        for kv in prof.split(','):
            b,w=kv.split('='); a,c=w.split(':'); i=[short(x[0]) for x in bl].index(b)
            p=bl[i][1]; lines=p.rstrip().split('\n'); L=lines[-1]
            assert L.strip().startswith('br i1'),L
            tag=f'!{990000+i}'; lines[-1]=re.sub(r',\s*!prof\s*!\d+','',L)+f', !prof {tag}'; bl[i][1]='\n'.join(lines)
            md+=f'\n{tag} = !{{!"branch_weights", i32 {a}, i32 {c}}}'
    out=pre+'\n\n'.join(b[1] for b in bl)+post+md+'\n'
    open(outp+'.ll','w').write(out)
    SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',outp+'.ll','-filetype=asm','-o',outp+'.s'],capture_output=True,text=True)
    if r.returncode: return {'err':r.stderr[-800:]}
    if not score: return {}
    s=sc.score(outp+'.s'); s.pop('ch',None); return s
if __name__=='__main__':
    a=sys.argv[1:]; prof=None
    if '--prof' in a: i=a.index('--prof'); prof=a[i+1]; del a[i:i+2]
    print(json.dumps(run(a[0],a[1],a[2] if len(a)>2 else '',prof)))
