import re,difflib,sys
o,c=[],[]
for ln in open(sys.argv[1]).read().splitlines()[1:]:
    m=re.match(r'^([-+ ]) (0x[0-9a-f]+)? +(0x[0-9a-f]+)? +(.*)$',ln)
    if not m: continue
    tag,oa,ca,ins=m.groups()
    if tag in ' -': o.append((int(oa,16)-0x5b3b0,ins))
    if tag in ' +': c.append((int(ca,16),ins))
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
cum=0; allh='--all' in sys.argv
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal': continue
    ob=sum(16 if o[k][1].startswith('lddw') else 8 for k in range(i1,i2)); cb=sum(16 if c[k][1].startswith('lddw') else 8 for k in range(j1,j2))
    cum+=cb-ob
    oo=o[i1][0] if i1<len(o) else -1
    if cb!=ob or allh:
        print(f'{oo:#6x} -{i2-i1} +{j2-j1} delta {cb-ob:+4d} cum {cum:+5d} | {" ; ".join(x[1] for x in o[i1:i2])[:110]} || {" ; ".join(x[1] for x in c[j1:j2])[:110]}')
