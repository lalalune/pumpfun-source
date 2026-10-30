import sys,re
log,stop,reg=sys.argv[1],int(sys.argv[2]),sys.argv[3]
cur={}
for i,l in enumerate(open(log)):
    if i+1>=stop: break
    m=re.match(r'assigning (%\d+) to \$(r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=(m.group(2),m.group(3)[:150])
    m=re.match(r'unassigning (%\d+) from \$(r\d+)',l)
    if m: cur.pop(m.group(1),None)
for v,(r,iv) in cur.items():
    if r==reg: print(v,iv)
