# movefn.py <src file> <fn name> <reexport line or ''> [nth]  -> prints block to stdout, replaces lines with pads (first line = reexport if given)
import sys,re
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from fnloc import locate
def move(path,name,reexp,nth=0,pad='// layout-pad'):
    i,j,L=locate(path,name,nth)
    s=i
    while s>0 and (L[s-1].strip().startswith('#[') or L[s-1].strip().startswith('///')): s-=1
    # the fn line must start at col 0 with only attrs before it on same line
    pre=L[s][:L[s].find('fn '+name)] if s==i else ''
    blk=L[s:j+1]
    tail=L[j][L[j].rfind('}')+1:]
    assert tail.strip()=='', ('trailing code after fn end',tail)
    for x in range(s,j+1): L[x]=pad
    if reexp: L[s]=reexp
    open(path,'w').write('\n'.join(L))
    return blk
if __name__=='__main__':
    b=move(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else 0)
    print('\n'.join(b))
