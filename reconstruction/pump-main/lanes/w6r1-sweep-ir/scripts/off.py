import sys
def L(p):
    out=[];off=0
    for l in open(p):
        s=l.strip()
        if not s: continue
        out.append((off,s)); off+=16 if s.startswith('lddw') else 8
    return out
a,b=int(sys.argv[2],16),int(sys.argv[3],16)
for o,s in L(sys.argv[1]):
    if a<=o<b: print(f'{o:#6x} {s}')
