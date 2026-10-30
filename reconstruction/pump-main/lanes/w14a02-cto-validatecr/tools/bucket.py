#!/usr/bin/env python3
"""bucket.py name1 name2..: local (validate-window) rm alignment per 0x100 orig bucket."""
import sys,os,subprocess
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cols=[]
for n in sys.argv[1:]:
    out=subprocess.run(['python3',O+'/tools/aln.py',O+'/rx/%s/m.o'%n,'0','0x1a88']+([] if os.environ.get('G') else ['L']),capture_output=True,text=True).stdout
    r={}
    for l in out.splitlines(): r[int(l.split()[0],16)]=('--' not in l[48:])
    cols.append(r)
print('bucket n   '+' '.join('%8s'%n[:8] for n in sys.argv[1:]))
for b in range(0,0x1a88,0x100):
    ks=[a for a in cols[0] if b<=a<b+0x100]
    print('%5x %3d '%(b,len(ks))+' '.join('%8d'%sum(c.get(a,0) for a in ks) for c in cols))
print('total     '+' '.join('%8d'%sum(c.values()) for c in cols))
