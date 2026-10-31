import sys,re
p,ph=sys.argv[1],sys.argv[2]; names=sys.argv[3:]
t=open(p).read(); parts=re.split(r'^# \*\*\* IR Dump (Before|After) .*$',t,flags=re.M)
body=parts[parts.index(ph)+1]
chunks=re.split(r'^(?=bb\.\d+)',body,flags=re.M)[1:]
bbname={}
for c in chunks:
    m=re.match(r'bb\.(\d+)(?:\.([^\s:(]+))?',c); bbname[m.group(1)]=m.group(2) or ''
for c in chunks:
    m=re.match(r'bb\.(\d+)(?:\.([^\s:(]+))?',c); n=m.group(2) or ''
    if any(n==x or re.fullmatch(x,n) for x in names):
        s=re.search(r'successors: ([^\n;]*)(?:; ([^\n]*))?',c)
        ss=(s.group(2) or s.group(1)) if s else ''
        ss=re.sub(r'%bb\.(\d+)',lambda q:'bb.'+q.group(1)+'.'+bbname.get(q.group(1),'')[:22],ss)
        pr=re.search(r'; predecessors: ([^\n]*)',c); pp=re.sub(r'%bb\.(\d+)',lambda q:bbname.get(q.group(1),'')[:16],pr.group(1)) if pr else ''
        print('bb.'+m.group(1),n,'->',ss[:260],' <-',pp[:120])
