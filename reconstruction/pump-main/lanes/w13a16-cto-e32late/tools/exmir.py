import sys,re
t=open(sys.argv[1]).read()
i=t.index('fn admin_cto::execute(')
j=t.index('\n}\n',i)
open(sys.argv[2],'w').write(t[i:j+3])
