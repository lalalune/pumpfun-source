import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
def offs(raw):
    t,_=xled.toks(raw); s=set()
    for x in t:
        op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): s.add(-struct.unpack('<h',x[2:4])[0])
    return s
O=offs(oracle.orig_window())
for p in sys.argv[1:]:
    s=offs(open(p,'rb').read())
    print(os.path.basename(p),'n',len(s),'max',max(s),'spill-area (>=2264) n',len([x for x in s if x>=2264]),sorted(x for x in s if x>=2264)[:40])
print('orig n',len(O),'max',max(O),len([x for x in O if x>=2264]),sorted(x for x in O if x>=2264)[:40])
