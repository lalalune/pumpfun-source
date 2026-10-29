import re,sys
dis,target=sys.argv[1],int(sys.argv[2],16); n=int(sys.argv[3]) if len(sys.argv)>3 else 12
buf=[]; fn='?'
for l in open(dis):
    m=re.match(r'^([0-9a-f]+) <(.*)>:',l)
    if m: fn=m.group(2); buf=[]; continue
    m=re.match(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s){8}\s*(.*)',l)
    if not m: continue
    a=int(m.group(1))*8; ins=re.sub(r'\s*<.*','',m.group(2).strip()); buf.append((a,ins))
    c=re.match(r'call (-?0x[0-9a-f]+)',ins)
    if c and a+8+int(c.group(1),16)*8==target:
        print('==',hex(a),fn[:90]); print('\n'.join('   %x %s'%x for x in buf[-n:]))
