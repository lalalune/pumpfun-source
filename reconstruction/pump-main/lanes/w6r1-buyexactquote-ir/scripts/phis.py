import re,sys
t=open(sys.argv[1]).read().split('\n')
s=next(i for i,l in enumerate(t) if l.startswith('define') and 'trade15buy_exact_quote17h' in l)
e=next(i for i in range(s,len(t)) if t[i]=='}')
b=None
for i in range(s,e):
    m=re.match(r'^([\w.$"]+):',t[i])
    if m: b=m.group(1)
    if '%_0.sroa' in t[i] and ' = phi ' in t[i]: print(b[:60], t[i].split('=')[0].strip(), t[i].split()[3], t[i].count('['))
