import sys,re
def asg(p):
    d={}
    for l in open(p):
        m=re.match(r'^assigning (%\d+) to \$(r\d+): W\d+ (.*)',l)
        if m:
            segs=[(int(a),int(b)) for a,b in re.findall(r'\[(\d+)[rBed],(\d+)[rBed]',m.group(3))]
            d[m.group(1)]=(m.group(2),segs)
        m=re.match(r'^unassigning (%\d+) from',l)
        if m: d.pop(m.group(1),None)
    return d
a=asg(sys.argv[1]); lo,hi=int(sys.argv[2]),int(sys.argv[3])
out=[]
for v,(r,segs) in a.items():
    ov=sum(max(0,min(b,hi)-max(a_,lo)) for a_,b in segs)
    if ov>(hi-lo)*float(sys.argv[4] if len(sys.argv)>4 else 0.3): out.append((r,v,ov,segs[0][0],segs[-1][1]))
for x in sorted(out): print(*x)
