import sys,re,collections
for f in sys.argv[1:]:
    c=collections.Counter(int(m,16) for m in re.findall(r'r10 - (0x[0-9a-f]+)',open(f).read()))
    print('==',f,len(c),'distinct')
    print(' '.join(f'{k:x}:{c[k]}' for k in sorted(c)))
