import sys
L=open(sys.argv[1]).read().split('\n')
for i in [int(x) for x in sys.argv[2:]]:
    print('#### idx',i)
    for j in range(max(0,i-9),i+4): print(('>> ' if j==i else '   ')+L[j][:170])
