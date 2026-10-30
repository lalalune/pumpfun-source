import re,sys
L=open(sys.argv[1]).read().split('\n')
end=int(sys.argv[2]); xs=[int(x) for x in sys.argv[3].split(',')]
cur={}
pat_a=re.compile(r'^assigning (%\d+) to \$(r\d+): \S+ (.*)$')
pat_u=re.compile(r'^unassigning (%\d+) from \$(r\d+)')
for k,l in enumerate(L[:end]):
    m=pat_a.match(l)
    if m: cur[m.group(1)]=(m.group(2),m.group(3)); continue
    m=pat_u.match(l)
    if m: cur.pop(m.group(1),None)
def covers(rng,x):
    for a,b in re.findall(r'\[(\d+)[rBde],(\d+)[rBde]',rng):
        if int(a)<=x<int(b): return True
    return False
for v,(r,rng) in sorted(cur.items(),key=lambda t:t[1][0]):
    if any(covers(rng,x) for x in xs):
        segs=re.findall(r'\[(\d+)[rBde],(\d+)[rBde]',rng)
        print(v,r,segs[0],segs[-1],len(segs))
