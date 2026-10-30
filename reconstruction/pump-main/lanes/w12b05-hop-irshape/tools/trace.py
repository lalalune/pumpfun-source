import re,sys
# trace.py build.log regex : for each IR dump print blocks containing lines matching regex (only when changed)
t=open(sys.argv[1]).read(); rx=re.compile(sys.argv[2])
dumps=re.split(r'\n(?=\*\*\* IR Dump After )', t)
prev=None
for i,d in enumerate(dumps):
    if not d.startswith('*** IR Dump After'): continue
    hdr=d.split('\n',1)[0][18:90]
    if 'ISel' in hdr or '(' in hdr.split(' on ')[0] and 'Pass' not in hdr: pass
    cur=[]; lab='ENTRY'
    for l in d.split('\n')[1:]:
        m=re.match(r'^([\w.$"-]+):',l)
        if m: lab=m.group(1)
        if rx.search(l): cur.append(f'{lab}: {l.strip()[:110]}')
    s='\n'.join(cur)
    if s!=prev:
        print(f'[{i}] {hdr}'); print('   '+s.replace('\n','\n   ')); prev=s
