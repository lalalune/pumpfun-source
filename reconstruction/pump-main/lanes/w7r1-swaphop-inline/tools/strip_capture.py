import sys
p=sys.argv[1]; t=open(p).read().split('\n'); t=[l for l in t if '@w7_capture(ptr' not in l or l.startswith('declare')]; open(p,'w').write('\n'.join(t))
