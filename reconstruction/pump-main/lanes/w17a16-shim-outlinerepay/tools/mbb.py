#!/usr/bin/env python3
"""mbb.py <m.ll>: final MBB layout order (IR block names) of admin_cto::execute after block placement (debug llc)."""
import sys,os,re,subprocess
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
m=sys.argv[1]
r=subprocess.run([DBG,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o',os.devnull,'-print-after=block-placement','-filter-print-funcs=_ZN14pump_recovered9admin_cto7execute17h'+re.search(r'admin_cto7execute17h([0-9a-f]+)E',open(m).read()).group(1)+'E'],capture_output=True,text=True)
names=re.findall(r'^bb\.(\d+)(?:\.([\w.]+))?:',r.stderr,re.M)
print(' '.join((n or '#'+i) for i,n in names))
