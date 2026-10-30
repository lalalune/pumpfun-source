import re,sys
def groups(path):
    t=open(path).read(); name={}
    for m in re.finditer(r'slot #(\d+) .*?with allocation: (\S+)',t): name[int(m.group(1))]=m.group(2)
    g={}
    for m in re.finditer(r'Merging #(\d+) and slots #(\d+) together',t):
        g.setdefault(int(m.group(1)),[]).append(int(m.group(2)))
    return name,g
name,g=groups(sys.argv[1])
want=sys.argv[2:]
for h,ms in g.items():
    ns=[name.get(h,'#%d'%h)]+[name.get(x,'#%d'%x) for x in ms]
    if not want or any(w in ns for w in want): print(' '.join(ns))
