import sys,re
src,out,arg=sys.argv[1],sys.argv[2],sys.argv[3]
t=open(src).read().split('\n')
s=next(i for i,l in enumerate(t) if l.startswith('define') and 'buy_exact_quote_body17h' in l)
e=next(i for i in range(s,len(t)) if t[i]=='}')
j=next(i for i in range(s,s+400) if t[i].strip().startswith('%_0 = alloca'))
# last alloca line index
la=max(i for i in range(s,s+400) if ' = alloca' in t[i])
body=t[la+1:e]
n=0
for k,l in enumerate(body):
    if re.search(r'%'+arg+r'\b',l) and not l.strip().startswith(';'):
        n+=1; body[k]=f'  %{arg}.ld{n} = load i64, ptr %{arg}.addr, align 8\n'+re.sub(r'%'+arg+r'\b',f'%{arg}.ld{n}',l)
t=t[:la+1]+[f'  store i64 %{arg}, ptr %{arg}.addr, align 8']+body+t[e:]
t.insert(j+1,f'  %{arg}.addr = alloca [8 x i8], align 8')
open(out,'w').write('\n'.join(t))
print('uses',n)
