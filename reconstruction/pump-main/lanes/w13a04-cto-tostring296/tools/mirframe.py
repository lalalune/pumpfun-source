import sys,re
# mirframe.py <file.mir> : execute's stack objects (offset size align name), by offset
t=open(sys.argv[1]).read()
i=t.find('name:            _ZN14pump_recovered9admin_cto7execute17')
j=t.find('\nstack:',i); k=t.find('\ncallSites:',j)
rows=[]
for e in re.findall(r'\{ id: \d+,[^}]*\}',t[j:k]):
    e=' '.join(e.split())
    m=re.search(r"id: (\d+), name: ([^,]*), type: (\S+), offset: (-?\d+), size: (\d+), alignment: (\d+)",e)
    if m: rows.append((-int(m.group(4)),int(m.group(5)),int(m.group(6)),m.group(2).strip("'") or '#'+m.group(1)))
for o,s,a,n in sorted(rows): print(f'{o:#06x} {s:5d} {a} {n}')
