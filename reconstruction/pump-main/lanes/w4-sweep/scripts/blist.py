import re,sys
t=open(sys.argv[1]).read()
m=re.search(r'^define[^\n]*5sweep7execute17h[^\n]*\{\n(.*?)^\}\n',t,re.M|re.S)
bl=re.split(r'\n\n',m.group(1).strip('\n'))
for i,b in enumerate(bl):
    name=b.split(':')[0] if not b.startswith('start') else 'start'
    name=re.sub(r'17h[0-9a-f]{16}E','',name); name=re.sub(r'\$LT\$|\$GT\$|\$u20\$|_ZN\d+|\$RF\$','',name)[-45:]
    calls=[re.sub(r'_ZN\d+|17h[0-9a-f]+E|\$LT\$|\$GT\$|\$u20\$','',c)[-30:] for c in re.findall(r'call [^@]*@([\w.$"]+)\(',b) if not c.startswith('llvm.')]
    print(i,name,len(b.splitlines()),','.join(calls)[:90])
