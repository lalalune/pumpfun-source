#!/usr/bin/env python3
"""po.py: post-opt IR helpers (llc only) on fx/<base>/m.ll: apply text edits, score with llc + M + per-region diff."""
import sys,os,re,json,subprocess,hashlib,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
os.environ['LANE_OUT']=OUT
import fx,oracle
def score(text,name,ref='m0',rg=True,keepll=False):
    d=f'{OUT}/fx/{name}'; os.makedirs(d,exist_ok=True); t0=time.time()
    open(d+'/m.ll','w').write(text)
    r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':'llc:'+r.stderr[-800:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b); os.remove(d+'/m.o')
    if not keepll: os.remove(d+'/m.ll')
    M,ratio=fx.Mof(b)
    res={'name':name,'M':M,'ratio':round(ratio,5),'bytes':len(b),'secs':round(time.time()-t0,1),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]}
    if rg:
        q=subprocess.run(['python3',T+'/rg.py',f'{d}/fn.bin',f'{OUT}/fx/{ref}/fn.bin'],capture_output=True,text=True)
        res['rg']=q.stdout.strip()
    return res
def rep(t,a,b,n=1):
    c=t.count(a); assert c==n,(c,a[:150]); return t.replace(a,b)
def rename(t):
    # rename numbered SSA values in execute to named ones so that edits don't break numbering
    import re
    m=re.search(r'^define [^\n]*admin_cto7execute[^\n]*\{\n',t,re.M); e=t.index('\n}\n',m.end())+3
    body=t[m.start():e]
    body=re.sub(r'%(\d+)(?=[\s,\)\]:])',r'%v\1',body)
    return t[:m.start()]+body+t[e:]
class Fn:
    """function-level block editing on post-opt text"""
    def __init__(s,t,name='admin_cto7execute'):
        import re
        s.t=t
        m=re.search(r'^define [^\n]*'+name+r'[^\n]*\{\n',t,re.M); s.a=m.start(); s.b=t.index('\n}\n',m.end())+3
        lines=t[s.a:s.b].split('\n')
        s.head=lines[0]; s.blocks=[];cur=None
        for l in lines[1:]:
            if l=='}':break
            m2=re.match(r'^("[^"]+"|[\w.$-]+):',l)
            if m2: cur=[m2.group(1),[l]]; s.blocks.append(cur)
            else:
                if cur is None: raise Exception('no block '+l)
                cur[1].append(l)
    def idx(s,n):
        for i,b in enumerate(s.blocks):
            if b[0]==n: return i
        raise KeyError(n)
    def blk(s,n): return s.blocks[s.idx(n)]
    def move_after(s,a,after):
        x=s.blocks.pop(s.idx(a)); s.blocks.insert(s.idx(after)+1,x)
    def move_before(s,a,before):
        x=s.blocks.pop(s.idx(a)); s.blocks.insert(s.idx(before),x)
    def text(s):
        return s.t[:s.a]+s.head+'\n'+'\n'.join('\n'.join(b[1]) for b in s.blocks)+'\n}\n'+s.t[s.b:]
