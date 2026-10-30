import sys,re
log,vr,reg=sys.argv[1],sys.argv[2],sys.argv[3]
L=open(log).read().split('\n')
stop=next(i for i,l in enumerate(L) if l.startswith('selectOrSplit GPR:%s '%vr))
segs=lambda s:[(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[rBed],(\d+)[rBed]',s)]
P=segs(L[stop].split(' ',2)[2])
cur={}
for l in L[:stop]:
    m=re.match(r'assigning (%\d+) to \$(r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=(m.group(2),segs(m.group(3)))
    m=re.match(r'unassigning (%\d+) from',l)
    if m: cur.pop(m.group(1),None)
for v,(r,S) in cur.items():
    if r!=reg: continue
    ov=[(max(a,c),min(b,d)) for a,b in P for c,d in S if max(a,c)<min(b,d)]
    if ov: print(v,r,'overlaps',ov[:6],'span',S[0][0],S[-1][1])
