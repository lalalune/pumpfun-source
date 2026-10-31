import re,sys
# pjt.py <pbjt.txt> <dump idx> <block>: print block w/o lifetime, count JT-relevant cost
t=open(sys.argv[1]).read(); k=int(sys.argv[2]); n=sys.argv[3]
d=re.split(r'^; \*\*\* IR Dump.*$',t,flags=re.M)[k]
blocks=re.split(r'\n(?=[\w.$"-]+:)',d); B={}
for b in blocks:
    m=re.match(r'([\w.$"-]+):',b)
    if m: B[m.group(1)]=b
b=B[n]; c=0
for l in b.split('\n'):
    s=l.strip()
    if not s or s.startswith(';') or ' = phi ' in s or 'lifetime' in s or s.endswith(':') or re.match(r'[\w.$"-]+:',s): continue
    free = (' getelementptr inbounds' in s and re.search(r'i64 \d+$|i64 \d+, !',s)) or ' bitcast ' in s
    cost=0 if free else (2 if 'call ' in s and '@llvm.' in s else 4 if 'call ' in s else 1)
    if s.startswith('br ') or s.startswith('switch'): cost=0
    c+=cost; print(f'{cost} {re.sub(r"_ZN[\w$.]*E","F",s)[:150]}')
print('TOTAL',c)
