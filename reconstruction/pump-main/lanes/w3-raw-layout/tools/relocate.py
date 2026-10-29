# relocate.py file fnname dest_line(1-based, first pad line) [nth]: move fn block (with attrs) into pad lines starting at dest
import sys,re
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from fnloc import locate
def ispad(l): return l.strip()=='' or l.strip().startswith('// layout-pad')
def relocate(path,name,dest,nth=0):
    i,j,L=locate(path,name,nth)
    s=i
    while s>0 and (L[s-1].strip().startswith('#[') or L[s-1].strip().startswith('///')): s-=1
    tail=L[j][L[j].rfind('}')+1:]; assert tail.strip()=='',tail
    blk=L[s:j+1]; d=dest-1
    for k in range(len(blk)): assert ispad(L[d+k]) or s<=d+k<=j, ('not pad',d+k+1,L[d+k])
    for x in range(s,j+1): L[x]='// layout-pad'
    for k,l in enumerate(blk): L[d+k]=l
    open(path,'w').write('\n'.join(L))
    print(f'{path}: moved {name} {s+1}-{j+1} -> {dest}-{dest+len(blk)-1}')
if __name__=='__main__':
    relocate(sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]) if len(sys.argv)>4 else 0)
