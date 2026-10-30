import re,sys,collections
# scg.py sc.log [name...]: StackColoring groups (representative <- members) for the execute function trace
t=open(sys.argv[1]).read()
i=t.find('Function: _ZN14pump_recovered9admin_cto7execute'); j=t.find('********** Stack Coloring',i); t=t[i:j if j>0 else None]
names={int(a):b for a,b in re.findall(r'slot #(\d+) with allocation: (\S+)',t)}
sizes={int(a):int(b) for a,b in re.findall(r'^Slot #(\d+) - (\d+) bytes\.',t,re.M)}
par={k:k for k in names}
def r(x):
    while par[x]!=x: x=par[x]
    return x
for a,b in re.findall(r'Merging #(\d+) and slots #(\d+) together',t):
    a,b=r(int(a)),r(int(b))
    if a!=b: par[b]=a
g=collections.defaultdict(list)
for k in names: g[r(k)].append(k)
want=sys.argv[2:]
for rep,m in sorted(g.items()):
    ns=[names[x] for x in sorted(m)]
    if not want or any(w in ns for w in want): print(sizes.get(rep),names[rep],'<-',' '.join(n for n in ns if n!=names[rep]))
