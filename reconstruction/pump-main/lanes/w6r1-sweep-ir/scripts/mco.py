#!/usr/bin/env python3
"""mco.py pre.ll [edit.py] : apply edit to execute fn in pre-memcpyopt module, run LLVM18 memcpyopt, report sroa.5 markers + region."""
import sys,re,subprocess,runpy,os
OPT=os.path.expanduser('~/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt')
t=open(sys.argv[1]).read()
if len(sys.argv)>2:
    t2=runpy.run_path(sys.argv[2])['edit'](t); assert t2!=t; t=t2
open('/tmp/mco_in.ll','w').write(t) if False else None
d=os.path.dirname(os.path.abspath(sys.argv[1]))
open(d+'/mco_in.ll','w').write(t)
r=subprocess.run([OPT,'-passes='+os.environ.get('PASSES','memcpyopt'),d+'/mco_in.ll','-S','-o',d+'/mco_out.ll'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
o=open(d+'/mco_out.ll').read()
m=re.search(r'^define[^\n]*5sweep7execute17h[^\n]*\{\n.*?^\}\n',o,re.M|re.S); f=m.group(0)
pat=os.environ.get('PAT','_5.sroa.5.i')
print('markers on',pat,':',len(re.findall(r'lifetime\.(start|end)[^\n]*%'+re.escape(pat)+r'\)',f)))
i=f.find('Rent$GT$3get'); s=f.rfind('\n\n',0,i); e=f.find('ensure_rent_exempt17h',i); e=f.find('\n\n',e)
if os.environ.get('V'): print(re.sub(r', !(noalias|alias.scope) ![0-9]+','',f[s:e]))
