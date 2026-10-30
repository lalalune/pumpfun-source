import sys
# padalloca.py in out defline size [pos: first|last]
src,dst,n,size=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); pos=sys.argv[5] if len(sys.argv)>5 else 'first'
L=open(src).read().split('\n')
assert L[n-1].startswith('define')
# find start: label line
i=n
while not L[i].startswith('start:'): i+=1
j=i+1
if pos=='last':
    while L[j].lstrip().startswith('%') and ' = alloca ' in L[j]: j+=1
ins=[f'  %zzpad = alloca [{size} x i8], align 8']
# keep alive: volatile store at entry after allocas
k=j
while L[k].lstrip().startswith('%') and ' = alloca ' in L[k]: k+=1
L=L[:j]+ins+L[j:k]+['  call void asm sideeffect "", "r"(ptr %zzpad)']+L[k:]
open(dst,'w').write('\n'.join(L))
