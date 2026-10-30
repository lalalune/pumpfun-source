import sys,struct,json,collections
sys.argv_saved=list(sys.argv)
exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w6r2-layout-rodata/scripts/shiftraw.py').read().split("by={}")[0])
by={}
for st,l,n in candidate_functions(sys.argv[1]):
    raw=body(cand,cs,st,l); by.setdefault((l,hashlib.sha256(normalize(raw,st,cs)).digest()),[]).append((st,n,raw))
cls=collections.Counter(); ex=collections.defaultdict(list)
for w in original_windows():
    ms=by.get((w['bytes'],hashlib.sha256(w['norm']).digest()),[])
    if not ms: continue
    best=None
    for st,n,raw in ms:
        rb=rebase(raw); o=w['raw']; calls=0; data=0; other=0; i=0
        while i<len(o):
            if o[i]==0x18:
                if rb[i:i+16]!=o[i:i+16]: data+=1
                i+=16
            else:
                if rb[i:i+8]!=o[i:i+8]:
                    if o[i]==0x85: calls+=1
                    else: other+=1
                i+=8
        k=(calls>0,data>0,other>0)
        if best is None or sum(k)<sum(best): best=k
    cls[best]+=1; ex[best].append(hex(w['start']))
for k,v in cls.items(): print('calls,data,other',k,v, ex[k][:8])
# section of data diffs
sec=collections.Counter(); det=collections.defaultdict(list)
def secof(v,S):
    for n,s in S.items():
        if n and s['addr']>0 and s['addr']<=v<s['addr']+s['size']: return n
for w in original_windows():
    ms=by.get((w['bytes'],hashlib.sha256(w['norm']).digest()),[])
    if not ms: continue
    st,n,raw=ms[0]; rb=rebase(raw); o=w['raw']; i=0
    while i<len(o):
        if o[i]==0x18:
            if rb[i:i+16]!=o[i:i+16]:
                ov=struct.unpack_from('<I',o,i+4)[0]|struct.unpack_from('<I',o,i+12)[0]<<32
                cv=struct.unpack_from('<I',raw,i+4)[0]|struct.unpack_from('<I',raw,i+12)[0]<<32
                sec[secof(ov,os_)]+=1; det[secof(ov,os_)].append((hex(w['start']),hex(ov),hex(cv),n[:60]))
            i+=16
        else: i+=8
print(sec)
for k,v in det.items():
    for x in v[:12]: print(k,x)
