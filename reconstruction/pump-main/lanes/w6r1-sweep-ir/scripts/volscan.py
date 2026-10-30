import re,sys,subprocess,os
t=open(sys.argv[1]).read()
m=re.search(r'^define[^\n]*5sweep7execute17h[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
f=m.group(0)
i=f.find('Rent$GT$3get'); s=f.rfind('\n\n',0,i); e=f.find('ensure_rent_exempt17h',i); e=f.find('\n\n',e)
lines=[(k.start(),k.end()) for k in re.finditer(r'call void @llvm\.memcpy[^\n]*i1 false\)',f[s:e])]
for a,b in lines:
    ln=f[s+a:s+b]
    f2=f[:s+a]+ln.replace('i1 false)','i1 true)')+f[s+b:]
    open('/tmp/x_ed.py','w').write('')
    t2=t[:m.start()]+f2+t[m.end():]
    open(os.path.dirname(sys.argv[1])+'/vs.ll','w').write(t2)
    r=subprocess.run(['python3',os.path.dirname(__file__)+'/mco.py',os.path.dirname(sys.argv[1])+'/vs.ll'],capture_output=True,text=True).stdout.strip()
    print(r, '<-', re.sub(r'ptr noundef nonnull align 8 dereferenceable\(24\) ','',ln)[40:140])
