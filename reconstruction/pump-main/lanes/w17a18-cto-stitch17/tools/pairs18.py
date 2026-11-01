#!/usr/bin/env python3
"""pairs18.py <tag> <m0 capture name> [maxabs=160]: splice screen on the CURRENT baseline (linked basis).
items = w16a17 library translations (5998913 basis -> current main) + this lane's captures (from the <m0> oracle basis
-> current main). Vars are cached, so pairs/triples need no difflib. Ranks composites at 27,400 B by (M desc, slots asc)."""
import sys,os,json,itertools
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T); sys.path.insert(0,T)
import splice, oracle
S=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a17-cto-stitch16')
tag=sys.argv[1]; m0n=sys.argv[2]; MAXABS=int(sys.argv[3]) if len(sys.argv)>3 else 160
so=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
NEW=oracle.elf_fn(so,oracle.KEEP); orig=oracle.orig_window()
NB=splice.parse(NEW); NBT=splice.targets(NB)
OLD=open(S+'/rx/main/fn.bin','rb').read(); OB=splice.parse(OLD); OBT=splice.targets(OB); NV=splice.Var(OB,NEW)
M0=open(f'{OUT}/fx/{m0n}/fn.bin','rb').read(); MB=splice.parse(M0); MBT=splice.targets(MB); MV=splice.Var(MB,NEW)
mn=b''.join(oracle.mask(NEW)); m_main=splice.M(NEW); r0,s0=oracle.metric(NEW,orig)
print('main',m_main,s0,flush=True)
os.makedirs(f'{OUT}/tx_{tag}',exist_ok=True)
items={}
def add(name,raw,src):
    if raw is None or b''.join(oracle.mask(raw))==mn: return
    items[name]={'raw':raw,'src':src,'dB':len(raw)-27400}
lib=json.load(open(f'{OUT}/data/tnew3_bf01b5f.json'))
for x in lib:
    p=f"{OUT}/tx_{tag}/{x['name']}.bin"
    if os.path.exists(p): raw=open(p,'rb').read()
    else:
        raw=splice.splice(OLD,[NV,open(x['tpath'],'rb').read()],OB,OBT)
        if raw is None: continue
        open(p,'wb').write(raw)
    add('L:'+x['name'],raw,x['lane'])
caps=[json.loads(l) for l in open(OUT+'/res/cap.jsonl')]
mine=[r for r in caps if 'err' not in r and r['name'].endswith(sys.argv[4] if len(sys.argv)>4 else '') and r['name']!=m0n]
for r in mine:
    b=open(f"{OUT}/fx/{r['name']}/fn.bin",'rb').read()
    add('C:'+r['name'],splice.splice(M0,[MV,b],MB,MBT),'cap')
print('items',len(items),flush=True)
V={n:splice.Var(NB,items[n]['raw']) for n in items}
def price(ns):
    s=splice.splice(NEW,[V[n] for n in ns],NB,NBT)
    if s is None: return None
    rr,sd=oracle.metric(s,orig); return {'bytes':len(s),'M':splice.M(s),'slots':sd,'set':list(ns)}
res=[]
for n in items:
    p=price([n])
    if p: res.append(p)
sing={r['set'][0]:r for r in res}
small=[n for n in items if abs(items[n]['dB'])<=MAXABS and n in sing and sing[n]['M']>=m_main-6]
for a,b in itertools.combinations(small,2):
    if items[a]['dB']+items[b]['dB']!=0: continue
    p=price([a,b])
    if p: res.append(p)
good=[n for n in small if sing[n]['M']>=m_main-3 and items[n]['dB']!=0]
for a,b,c in itertools.combinations(good,3):
    if items[a]['dB']+items[b]['dB']+items[c]['dB']!=0: continue
    p=price([a,b,c])
    if p: res.append(p)
json.dump({'main':[m_main,s0],'singles':{n:{k:sing[n][k] for k in ('bytes','M','slots')} for n in sing},'res':res},open(f'{OUT}/data/pairs18_{tag}.json','w'))
at=[r for r in res if r['bytes']==27400]
at.sort(key=lambda r:(-r['M'],r['slots'] if r['slots'] is not None else 9999))
print('composites at 27400:',len(at))
for r in at[:40]: print(r['M']-m_main, r['M'], r['slots'], '+'.join(r['set']))
