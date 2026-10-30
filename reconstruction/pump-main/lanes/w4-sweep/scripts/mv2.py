import re,sys
# mv2.py in.ll out.ll i:j[:k] ... : move block range [i..j] (indices) to after block k  (renames numbered values)
t=open(sys.argv[1]).read()
m=re.search(r'^define[^\n]*5sweep7execute17h[^\n]*\{\n(.*?)^\}\n',t,re.M|re.S)
body=re.sub(r'%(\d+)\b',r'%__n\1',m.group(1))
body=re.sub(r'^(\d+):',r'__n\1:',body,flags=re.M)
bl=re.split(r'\n\n',body.strip('\n'))
for spec in sys.argv[3:]:
    i,j,k=map(int,spec.split(':'))
    seg=bl[i:j+1]; ids=[id(x) for x in seg]
    anchor=bl[k]
    rest=[x for x in bl if id(x) not in ids]
    p=rest.index(anchor); bl=rest[:p+1]+seg+rest[p+1:]
hdr=m.group(0)[:m.start(1)-m.start(0)]
hdr=re.sub(r'%(\d+)\b',r'%__n\1',hdr)
f=hdr+'\n\n'.join(bl)+'\n}\n'
open(sys.argv[2],'w').write(t[:m.start()]+f+t[m.end():])
