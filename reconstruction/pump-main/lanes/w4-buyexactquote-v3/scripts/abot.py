import sys
# abot.py src out names... : move named allocas to after %_0 (bottom of alloca list)
src,out=sys.argv[1],sys.argv[2]; names=sys.argv[3:]
t=open(src).read().split('\n')
s=next(i for i,l in enumerate(t) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
lines=[]
for nm in names:
    j=next(i for i in range(s,s+400) if t[i].strip().startswith(nm+' = alloca'))
    lines.append(t.pop(j))
j=next(i for i in range(s,s+400) if t[i].strip().startswith('%_0 = alloca'))
for l in lines[::-1]: t.insert(j+1,l)
open(out,'w').write('\n'.join(t))
