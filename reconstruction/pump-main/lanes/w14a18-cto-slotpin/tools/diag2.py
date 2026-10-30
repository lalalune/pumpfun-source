import sys,json,collections,difflib,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import slotpin as S
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tag=sys.argv[1]; d=f'{O}/q/{tag}'
ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}; mp={int(k):v for k,v in json.load(open(d+'/i_orig.json')).items()}
a,ta=S._rd(d+'/direct.txt'); b,tb=S._rd(O+'/orig_fn.txt'); oa=S._offs(a); obb=S._offs(b)
V=collections.defaultdict(collections.Counter); nobj=0
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1):
        x,y=oa[i1+k],obb[j1+k]
        if x is None or y is None: continue
        f=[i for i,o in ob.items() if o['off']<=x<o['off']+o['size']]
        if not f: nobj+=1; continue
        i=f[0]; V[i][y-(x-ob[i]['off'])]+=1
tot=sum(sum(c.values()) for c in V.values()); got=sum(c[mp[i]] for i,c in V.items() if i in mp)
best=sum(c.most_common(1)[0][1] for c in V.values())
print(tag,'aligned frame accesses',tot,'no-obj',nobj,'| pinned-consistent',got,'| per-object best (no conflicts)',best,'| inherent split loss',tot-best,'| conflict loss',best-got)
sp=[(sum(c.values())-c.most_common(1)[0][1],i) for i,c in V.items()]
for l,i in sorted(sp,reverse=True)[:8]: print('  split',i,ob[i]['type'],ob[i]['size'],ob[i]['name'],l,{hex(-k):v for k,v in V[i].most_common(4)})
