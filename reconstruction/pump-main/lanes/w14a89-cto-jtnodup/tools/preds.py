import sys,re
# preds.py dis.txt addr... : list branch sources (and fallthrough) into each addr
L=[]
for l in open(sys.argv[1]):
    m=re.match(r'^[-+ ]?\s*(0x[0-9a-f]+)\s+(.*)$',l.rstrip())
    if m: L.append((int(m.group(1),16),m.group(2)))
addrs=[a for a,_ in L]; nxt={addrs[i]:addrs[i+1] for i in range(len(addrs)-1)}
T={}
for a,ins in L:
    m=re.match(r'(j\w+)\s.*?([+-]0x[0-9a-f]+)$',ins)
    if m and not ins.startswith('call'):
        t=nxt.get(a,a+8)+int(m.group(2),16)*8 if False else a+8+int(m.group(2),16)*8
        T.setdefault(t,[]).append((a,ins))
for x in sys.argv[2:]:
    x=int(x,16); prev=[(a,i) for a,i in L if nxt.get(a)==x]
    ft=prev and not re.match(r'(ja|exit)\b',prev[0][1])
    print(hex(x),'fallthrough' if ft else '', [(hex(a),i) for a,i in T.get(x,[])])
