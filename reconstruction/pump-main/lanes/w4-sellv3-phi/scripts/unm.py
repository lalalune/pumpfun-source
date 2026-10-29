import re,sys
t=open(sys.argv[1]).read(); m=re.search(r'^define[^\n]*@_ZN14pump_recovered'+sys.argv[2],t,re.M); i=m.start(); j=t.index('\n}',i); f=t[i:j]
open(sys.argv[1]+'.fn','w').write(f)
print('unmarked:',' '.join(a for a,ty in re.findall(r'^\s+(%[\w.]+) = alloca (\[\d+ x i8\])',f,re.M) if not re.search(r'lifetime\.start\.p0\(i64 \d+, ptr '+re.escape(a)+r'\)',f)))
