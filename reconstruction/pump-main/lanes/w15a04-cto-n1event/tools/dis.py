import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bdis import decode
raw=open(sys.argv[1],'rb').read(); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
for d in decode(raw):
    if lo<=d['off']<hi: print('%04x %s'%(d['off'],d['txt']))
