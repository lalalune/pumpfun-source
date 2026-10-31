import re,sys
def blocks(f):
    out=[];cur=None;n=0;infn=False
    for l in open(f):
        if 'admin_cto7execute' in l and l.split(':')[0].startswith('_ZN') and not l.startswith('\t'): infn=True; cur=('bb.0','%start');n=0; continue
        if not infn: continue
        if l.startswith('.Lfunc_end') or l.startswith('Lfunc_end'): out.append((cur,n)); break
        m=re.match(r'^(LBB\S+|# %bb\.\d+):\s*(#\s*(\S+))?',l)
        if m:
            if cur: out.append((cur,n))
            cur=(m.group(1).replace('# ',''), m.group(3) or ''); n=0; continue
        s=l.strip()
        if s and not s.startswith(('#','.')): n+= 2 if s.startswith('lddw') else 1
    return out
for f in sys.argv[1:]:
    b=blocks(f); pos=0; L=[]
    for (lab,ir),n in b: L.append(f'{pos*8:6x} {n:4d} {ir:28s} {lab}'); pos+=n
    open(f.replace('.s','.lay'),'w').write('\n'.join(L)+'\n'); print(f,len(b),pos*8)
