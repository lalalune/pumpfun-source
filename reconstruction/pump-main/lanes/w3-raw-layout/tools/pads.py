import sys
L=open(sys.argv[1]).read().split('\n'); lo=int(sys.argv[2]) if len(sys.argv)>2 else 1; hi=int(sys.argv[3]) if len(sys.argv)>3 else len(L)
ispad=lambda l: l.strip()=='' or l.strip().startswith('// layout-pad')
i=lo-1
while i<hi:
    if ispad(L[i]):
        j=i
        while j<hi and ispad(L[j]): j+=1
        if j-i>=3: print(f'pads {i+1}-{j} ({j-i})')
        i=j
    else: i+=1
