import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'s12','tools'))
import dis as D, oracle
for p in sys.argv[1:]:
    raw=oracle.orig_window() if p=='orig' else open(f'{os.path.dirname(T)}/rx/{p}/fn.bin','rb').read()
    L=D.d(raw); s=[f"{int(m.group(1))}@{o:x}" for o,x in L for m in [re.match(r'stw \[r10-0x2b8\], (\d+)',x)] if m]
    nc=sum(1 for o,x in L if x.startswith('call'))
    print(f'{p:10s} calls {nc} | '+' '.join(s[:14]))
