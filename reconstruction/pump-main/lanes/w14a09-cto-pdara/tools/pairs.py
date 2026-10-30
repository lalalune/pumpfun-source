import sys,difflib,re
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/tools')
from slots import orig_dis,cand_dis
from abs import n2
from collections import Counter
o=orig_dis(); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
c=cand_dis(sys.argv[1])
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
pairs=Counter(); n=0; eq=0
for a,b,k in sm.get_matching_blocks():
    for j in range(k):
        oa,ot=o[a+j]
        if lo<=oa<hi:
            n+=1; ct=c[b+j][1]; eq+= (ct==ot)
            for x,y in zip(re.findall(r'\br\d\b',ot),re.findall(r'\br\d\b',ct)):
                if x!=y: pairs[(x,y)]+=1
print(sys.argv[1].split('/')[-2],'aligned',n,'exact',eq,pairs.most_common(10))
