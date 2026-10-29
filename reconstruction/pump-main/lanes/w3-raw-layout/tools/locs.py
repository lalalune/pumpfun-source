# locs.py cand.so refined.json 0xORIG... : print panic Locations (file,line,col) referenced by original window and by paired cand fn
import sys,struct; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
M=model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read(); orig=(C.BASE/'original.so').read_bytes()
def rd(blob,secs,va,n):
    for nm,s in secs.items():
        if s['addr'] and s['addr']<=va<s['addr']+s['size']: o=va-s['addr']+s['offset']; return blob[o:o+n]
def locs(blob,secs,raw,addr):
    out=[]
    for o,k,v,*r in C.operands(raw,addr,secs):
        if k=='lddw' and r and r[0]=='.data.rel.ro':
            b=rd(blob,secs,v,24)
            lo,hi,l,line,col=struct.unpack('<IIQII',b); p=hi if lo==0 else lo|(hi<<32)
            s=rd(blob,secs,p,l) if 0<l<200 else None
            if s and s.startswith(b'programs'): out.append((s.decode()[18:],line,col))
    return out
for x in sys.argv[3:]:
    st=int(x,16); w=M.wins[st]; a=M.pair[st]
    print(hex(st),'orig',locs(orig,M.osec,w['raw'],st))
    print('       cand',locs(cand,M.csec,C.body(cand,M.csec,a,M.units[a][0]),a))
