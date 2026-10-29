import re,sys
ll=open(sys.argv[1]).read().split('\n')
gorder=[];gdef={};gdef_full={}
for i,l in enumerate(ll):
    m=re.match(r'^(@[\w.$"]+|@"[^"]+") = ',l)
    if m: gorder.append(m.group(1)); gdef[m.group(1)]=l[:160]; gdef_full[m.group(1)]=l
fnames=[];first={}
cur=None;fi=-1
ref=re.compile(r'@(alloc_[0-9a-f]+|vtable\.\d+|[\w.$]+|"[^"]+")')
for l in ll:
    if l.startswith('define '):
        m=re.search(r'@("[^"]+"|[\w.$]+)\(',l); cur=m.group(1).strip('"'); fnames.append(cur); fi=len(fnames)-1; continue
    if cur is None: continue
    if l=='}': cur=None; continue
    for r in ref.findall(l):
        g='@'+r
        if g in gdef and g not in first: first[g]=fi
# nested: globals referenced by globals inherit
gref={g:[ '@'+r for r in ref.findall(gdef_full[g].split(' = ',1)[1])] for g in gorder}
ch=True
while ch:
    ch=False
    for h in gorder:
        if h in first:
            for g in gref[h]:
                if g in gdef and (g not in first or first[g]>first[h]): first[g]=first[h]; ch=True
seq=[(g,first.get(g)) for g in gorder]
nm=sum(1 for g,f in seq if f is None)
inv=0;last=-1
for g,f in seq:
    if f is None: continue
    if f<last: inv+=1
    last=max(last,f)
print('globals',len(seq),'unreferenced-by-fn',nm,'inversions',inv)
if len(sys.argv)>2:
    for g,f in seq[:int(sys.argv[2])]: print(f, fnames[f][:70] if f is not None else '-', gdef[g][:110])
