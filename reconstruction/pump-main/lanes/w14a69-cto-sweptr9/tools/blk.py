import re,sys
L=open(sys.argv[1]).read().split('\n'); pat=sys.argv[2]
blk=None;info={}
for i,l in enumerate(L):
    m=re.match(r'^(\d+)B\tbb\.(\d+)(\.\S*)?:',l)
    if m:
        blk=int(m.group(2)),m.group(3); np=ns=0
        for k in (1,2):
            q=L[i+k]
            if 'predecessors' in q: np=len(re.findall(r'%bb\.\d+',q))
            if 'successors' in q: ns=len(set(re.findall(r'%bb\.\d+',q.split(';')[0])))
        info[blk]=(np,ns)
    if re.search(pat,l) and not m: print(l.strip()[:90],blk,info.get(blk),sum(info.get(blk,(0,0))))
