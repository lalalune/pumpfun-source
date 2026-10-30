import sys,re
def fn(path,pat):
    out=[];on=False
    for l in open(path):
        if l.startswith('define') and re.search(pat,l): on=True
        if on: out.append(l)
        if on and l.startswith('}'): break
    return out
a=fn(sys.argv[1],sys.argv[2]); b=fn(sys.argv[3],sys.argv[4])
print(len(a),len(b)); print(a[0][:400]); print(b[0][:400])
