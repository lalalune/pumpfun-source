import sys,re,json
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from fnloc import locate
def find_nth(path,name,after):
    L=open(path).read().split('\n')
    hits=[i for i,l in enumerate(L) if re.search(r'\bfn\s+'+re.escape(name)+r'\b\s*[<(]',l)]
    hits2=[k for k,i in enumerate(hits) if i+1>=after]
    return hits2[0]
def move(path,name,newname,dest_mod,after=0,pad='// layout-pad'):
    nth=find_nth(path,name,after)
    i,j,L=locate(path,name,nth)
    s=i
    while s>0 and (L[s-1].strip().startswith('#[') or L[s-1].strip().startswith('///')): s-=1
    blk=L[s:j+1]
    tail=L[j][L[j].rfind('}')+1:]
    assert tail.strip()=='', ('trailing',path,name,tail)
    head=L[s][:L[s].find('fn '+name)] if s==i else None
    if s==i: assert re.fullmatch(r'\s*(#\[[^\]]*\]\s*)*(pub(\([a-z]+\))?\s+)?',head), ('lead',path,name,head)
    vis=re.compile(r'(^|\s|\])(pub(\((crate|super)\))?\s+)?fn\s+'+re.escape(name)+r'\b')
    # rewrite the fn line: make pub, rename
    k=i-s
    mm=vis.search(blk[k]); v=(mm.group(2) or '').strip()
    nv='pub' if v=='pub' else 'pub(crate)'
    blk[k]=vis.sub(lambda m: m.group(1)+nv+' fn '+newname, blk[k],count=1)
    for x in range(s,j+1): L[x]=pad
    L[s]=f'{nv} use crate::{dest_mod}::{newname} as {name};'
    open(path,'w').write('\n'.join(L))
    return blk
if __name__=='__main__':
    spec=json.load(open(sys.argv[1])); dest=sys.argv[2]; dmod=sys.argv[3]
    out=[]
    for path,name,new,after in spec:
        out+=move(path,name,new,dmod,after)
    D=open(dest).read().rstrip('\n').split('\n')
    open(dest,'w').write('\n'.join(D+out)+'\n')
