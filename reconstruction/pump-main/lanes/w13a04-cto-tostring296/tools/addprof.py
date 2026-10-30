import sys
# addprof.py in.ll out.ll lineno w1 w2
src,dst,n,w1,w2=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4],sys.argv[5]
L=open(src).read().split('\n')
assert L[n-1].lstrip().startswith('br i1'), L[n-1]
L[n-1]=L[n-1]+', !prof !99999'
L.append(f'!99999 = !{{!"branch_weights", i32 {w1}, i32 {w2}}}')
open(dst,'w').write('\n'.join(L))
