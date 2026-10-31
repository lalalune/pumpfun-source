import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,T+'/../s12/tools'); import oracle, dis as D
for p in sys.argv[1:]:
    raw=oracle.orig_window() if p=='orig' else open(f'{T}/../rx/{p}/fn.bin','rb').read()
    L=D.d(raw); s=[f"{int(m.group(1))}@{o:x}" for o,x in L for m in [re.match(r'stw \[r10-0x2b8\], (\d+)',x)] if m]
    print(f"{p:10s} {len(raw)} "+' '.join(s[:12]))
