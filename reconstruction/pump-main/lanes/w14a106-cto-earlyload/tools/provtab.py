import json,sys
a=json.load(open(sys.argv[1]));b=json.load(open(sys.argv[2])); th=int(sys.argv[3],16) if len(sys.argv)>3 else 0
rows=[]
for k in set(a)|set(b):
    oa=a.get(k,[]);ob=b.get(k,[])
    rows.append((oa[0] if oa else 0x7fff, ob[0] if ob else 0x7fff, k, oa, ob))
rows.sort()
for fa,fb,k,oa,ob in rows:
    if abs(fa-fb)<th: continue
    fl='' if abs(fa-fb)<0x100 else ('EARLY' if fa<fb else 'late')
    print('%05x %05x %6d %-34s %2d %2d %-5s o:%s m:%s'%(fa,fb,fb-fa,k,len(oa),len(ob),fl,','.join('%x'%x for x in oa[:6]),','.join('%x'%x for x in ob[:6])))
