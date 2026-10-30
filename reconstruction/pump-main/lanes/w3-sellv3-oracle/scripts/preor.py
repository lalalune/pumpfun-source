#!/usr/bin/env python3
"""preor.py pre.ll edit.py|- [blockops]: edit sell fn in pre-opt module, opt O3, slim, llc-oracle vs original. Prints ret phi order."""
import sys,os,re,runpy,subprocess
B=os.path.expanduser('~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin')
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle')
SYM=os.environ.get('SYM','5trade4sell17h')
src,ed=sys.argv[1:3]; ops=sys.argv[3:]
t=open(src).read()
m=re.search(r'^define[^\n]*'+SYM+r'[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
f=m.group(0)
if ed!='-':
    f2=runpy.run_path(ed)['edit'](f); assert f2!=f,'edit changed nothing'
else: f2=f
tag=os.environ.get('TAG','pre')
p=f'{D}/oracle/{tag}.pre.ll'; open(p,'w').write(t[:m.start()]+f2+t[m.end():])
r=subprocess.run([B+'/opt','-passes=default<O3>',p,'-S','-o',f'{D}/oracle/{tag}.opt.ll'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
subprocess.run(['python3',D+'/tools/slim.py',f'{D}/oracle/{tag}.opt.ll',SYM,f'{D}/oracle/{tag}.slim.ll'],check=True)
os.remove(f'{D}/oracle/{tag}.opt.ll')
s=open(f'{D}/oracle/{tag}.slim.ll').read()
fm=re.search(r'^define[^\n]*'+SYM+r'[^\n]*\{\n.*?^\}\n',s,re.M|re.S).group(0)
rb=re.search(r'\n((?:  %[^\n]*= phi [^\n]*\n)+)(?:  [^\n]*\n)*?  ret \{ i64, ptr \}',fm)
print('retphis',re.findall(r'= phi (\S+)',rb.group(1)) if rb else None)
env=dict(os.environ); env.setdefault('ORIG',D+'/oracle/orig.sell.txt'); env['TAG']=tag
sys.stdout.flush()
os.execvpe('python3',['python3',D+'/tools/oracle.py',f'{D}/oracle/{tag}.slim.ll',SYM]+ops,env)
