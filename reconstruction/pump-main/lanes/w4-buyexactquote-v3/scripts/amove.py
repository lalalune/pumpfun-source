import sys
src,out,k=sys.argv[1],sys.argv[2],int(sys.argv[3])
t=open(src).read().split('\n')
s=next(i for i,l in enumerate(t) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
idx=[i for i in range(s,s+400) if ' = alloca' in t[i]]
j=next(i for i in idx if t[i].strip().startswith('%_0 = alloca'))
line=t.pop(j); pos=idx[len(idx)-1-k]; t.insert(pos,line)
open(out,'w').write('\n'.join(t))
