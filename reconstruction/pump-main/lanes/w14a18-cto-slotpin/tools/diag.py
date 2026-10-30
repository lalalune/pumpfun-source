import sys,json,collections,difflib,re
sys.path.insert(0,__file__.rsplit('/',1)[0]); import slotpin as S
d=sys.argv[1]; ref=sys.argv[2]; mpf=sys.argv[3]
ob={int(k):v for k,v in json.load(open(d+'/objs.json')).items()}
a,ta=S._rd(d+'/direct.txt'); b,tb=S._rd(ref); oa=S._offs(a); obb=S._offs(b)
V=collections.defaultdict(collections.Counter)
def find(x):
    for i,o in ob.items():
        if o['off']<=x<o['off']+o['size']: return i
tot=0;nf=collections.Counter()
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1):
        x,y=oa[i1+k],obb[j1+k]
        if x is None or y is None: continue
        i=find(x); tot+=1
        if i is None: nf[x]+=1; continue
        V[i][y-(x-ob[i]['off'])]+=1
mp=json.load(open(mpf))
ok=sum(c[mp[str(i)]] for i,c in V.items() if str(i) in mp)
print('aligned r10 pairs',tot,'not-in-obj',sum(nf.values()),'consistent after pin',ok,'identity-consistent',sum(c[ob[i]['off']] for i,c in V.items()))
lost=0
for i,c in sorted(V.items(),key=lambda z:-sum(z[1].values())):
    got=c[mp[str(i)]] if str(i) in mp else 0; l=sum(c.values())-got; lost+=l
    if l>=3: print(f"id{i} off={ob[i]['off']:#x} {ob[i]['type']} sz{ob[i]['size']} pin={mp.get(str(i),'-') if str(i) not in mp else hex(mp[str(i)])} lost {l}:",{hex(k):v for k,v in c.most_common(5)})
print('lost',lost)
