import re,sys
def asg(p):
    d={}
    for l in open(p):
        m=re.match(r'^assigning (%\d+) to \$(r\d+): W\d+ (.*)',l)
        if m:
            segs=re.findall(r'\[(\d+)[rBed],(\d+)[rBed]',m.group(3)); sz=sum(int(b)-int(a) for a,b in segs)
            d[m.group(1)]=(m.group(2),sz,segs[0][0] if segs else None, segs[-1][1] if segs else None)
        m=re.match(r'^unassigning (%\d+) from',l)
        if m: d.pop(m.group(1),None)
    return d
a=asg(sys.argv[1])
for k,v in sorted(a.items(),key=lambda x:-x[1][1])[:int(sys.argv[2]) if len(sys.argv)>2 else 30]: print(k,v)
