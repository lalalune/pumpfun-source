import re,sys,subprocess,os
t=open(sys.argv[1]).read()
t=t.replace('\ndefine ','\ndeclare void @cap_probe(ptr)\n\ndefine ',1)
m=re.search(r'^define[^\n]*5sweep7execute17h[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
f=m.group(0)
for a in sys.argv[2].split(','):
    ln=re.search(r'  call void @llvm.lifetime.start.p0\(i64 \d+, ptr nonnull %'+re.escape(a)+r'\)[^\n]*\n',f)
    f=f[:ln.end()]+f'  call void @cap_probe(ptr %{a})\n'+f[ln.end():]
p=os.path.dirname(sys.argv[1])+'/cs.ll'
open(p,'w').write(t[:m.start()]+f+t[m.end():])
r=subprocess.run(['python3',os.path.dirname(__file__)+'/mco.py',p],capture_output=True,text=True,env=dict(os.environ))
print(sys.argv[2], r.stdout.strip()[:3000], r.stderr[-300:])
