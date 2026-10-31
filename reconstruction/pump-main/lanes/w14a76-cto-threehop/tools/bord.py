import sys,re
# block order with cumulative instruction slot index (lddw=2)
def order(f):
    out=[]; slot=0; cur=None
    for l in open(f):
        m=re.match(r'^(?:# %bb\.\d+:|LBB\d+_\d+:)\s*#\s*(\S.*)$',l)
        if m: cur=m.group(1).strip(); out.append((slot,cur)); continue
        s=l.strip()
        if not s or s.startswith(('#','.')) or s.endswith(':'): continue
        if cur is None: continue
        slot+=2 if s.startswith('lddw') else 1
    return out
o=order(sys.argv[1]); a,b=int(sys.argv[2]),int(sys.argv[3])
for s,n in o:
    if a<=s<=b: print(s,n[:90])
