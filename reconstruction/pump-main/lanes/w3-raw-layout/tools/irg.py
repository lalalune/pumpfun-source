import re,sys
def load(path):
    ll=open(path).read().split('\n')
    gorder=[];gfull={}
    for l in ll:
        m=re.match(r'^(@[\w.$]+|@"[^"]+") = ',l)
        if m: gorder.append(m.group(1)); gfull[m.group(1)]=l
    ref=re.compile(r'@(alloc_[0-9a-f]+|vtable\.\d+|[\w.$]+|"[^"]+")')
    fnames=[];first={};cur=None
    for l in ll:
        if l.startswith('define '):
            m=re.search(r'@("[^"]+"|[\w.$]+)\(',l); cur=m.group(1).strip('"'); fnames.append(cur); continue
        if cur is None: continue
        if l=='}': cur=None; continue
        for r in ref.findall(l):
            g='@'+r
            if g in gfull and g not in first: first[g]=len(fnames)-1
    gref={g:['@'+r for r in ref.findall(gfull[g].split(' = ',1)[1])] for g in gorder}
    ch=True
    while ch:
        ch=False
        for h in gorder:
            if h in first:
                for g in gref[h]:
                    if g in gfull and (g not in first or first[g]>first[h]): first[g]=first[h]; ch=True
    return gorder,gfull,fnames,first
if __name__=='__main__':
    gorder,gfull,fnames,first=load(sys.argv[1])
    for pat in sys.argv[2:]:
        for i,g in enumerate(gorder):
            if pat in gfull[g]:
                f=first.get(g); print(f'[{pat}] g#{i} fn#{f} {fnames[f][:110] if f is not None else "-"}')
