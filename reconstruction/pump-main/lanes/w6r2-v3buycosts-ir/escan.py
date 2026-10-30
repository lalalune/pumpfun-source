#!/usr/bin/env python3
"""Diagnostic: split CFG edges with a block holding only a ZST lifetime marker (code-neutral, survives to RA)."""
import re,subprocess,os,sys,itertools
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w6r2-v3buycosts-ir')
BASE=os.environ.get('FNBASE',OUT+'/irexp/base/fn.ll')
src=open(BASE).read()
def blocks(f):
    # returns list of (name, text)
    parts=re.split(r'\n(?=(?:"[^"]+"|[\w.$]+):)',f)
    return parts
def edges(f):
    E=[]
    for part in blocks(f)[1:]:
        name=re.match(r'("[^"]+"|[\w.$]+):',part).group(1)
        term=[l for l in part.split('\n') if l.strip().startswith(('br ','switch'))]
        if not term: continue
        for s in re.findall(r'label %("[^"]+"|[\w.$]+)',term[-1]): E.append((name,s))
    return E
MARK=os.environ.get('MARK','  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i.i29)')
def split(f,e,k):
    p,s=e; nb='esplit%d'%k
    parts=blocks(f)
    out=[]
    for part in parts:
        m=re.match(r'("[^"]+"|[\w.$]+):',part)
        name=m.group(1) if m else None
        if name==p:
            lines=part.split('\n')
            ti=max(i for i,l in enumerate(lines) if l.strip().startswith('br '))
            lines[ti]=re.sub(r'label %'+re.escape(s)+r'(?=[,\s]|$)','label %'+nb,lines[ti],count=1)
            part='\n'.join(lines)
        if name==s:
            part=re.sub(r'(phi [^\n]*?)\[ ([^\]]+?), %'+re.escape(p)+r' \]',lambda mm: mm.group(1)+'[ '+mm.group(2)+', %'+nb+' ]',part)
        out.append(part)
    f='\n'.join(out)
    f=f.rstrip('\n'); assert f.endswith('}')
    return f[:-1]+'\n'+nb+':\n'+MARK+'\n  br label %'+s+'\n}\n'
def run(name,f):
    p=OUT+'/scan/'+name+'.py'; open(OUT+'/scan/'+name+'.fn','w').write(f)
    open(p,'w').write("def edit(f):\n    return open(%r).read()\n"%(OUT+'/scan/'+name+'.fn'))
    r=subprocess.run(['python3',OUT+'/bin/irexp.py','scan_'+name,p],capture_output=True,text=True)
    return (r.stdout+r.stderr).strip().split('\n')[-1]
E=edges(src)
mode=sys.argv[1]
if mode=='list':
    for i,e in enumerate(E): print(i,e)
def score(r):
    m=re.search(r'bytes=(\d+).*-(\d+) \+(\d+)',r); return (int(m.group(2))+int(m.group(3))) if m else 999
if mode=='single':
    def job(i):
        return i,run('e%d'%i,split(src,E[i],i))
    with ThreadPoolExecutor(6) as ex:
        for i,r in ex.map(job,range(len(E))): print(i,E[i],r,flush=True)
if mode=='pairs':
    cand=[int(x) for x in sys.argv[2].split(',')] if len(sys.argv)>2 else range(len(E))
    def job(pq):
        a,b=pq; f=split(split(src,E[a],a),E[b],b) if E[a]!=E[b] else None
        return pq,(run('ep%d_%d'%pq,f) if f else 'same')
    with ThreadPoolExecutor(6) as ex:
        for pq,r in ex.map(job,itertools.combinations(cand,2)):
            if score(r)<20 or '2120' in r: print(pq,r,flush=True)
