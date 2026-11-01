#!/usr/bin/env python3
"""llcw.py <llc args...>: the patched (RAPRIO) llc with the automatic join-restore (ares.py) between register allocation and
branch-folder. Experiment only. Same CLI as llc for '<m.ll> -filetype=obj -o <out>' calls (screen.py / sclimb.py)."""
import sys,os,subprocess,tempfile
REAL=os.environ.get('LLCW_REAL',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound/llvmb/bin/llc'))
T=os.path.dirname(os.path.abspath(__file__))
a=sys.argv[1:]
if os.environ.get('LLCW_OFF')=='1' or not any(x=='-filetype=obj' for x in a):
    sys.exit(subprocess.run([REAL,*a]).returncode)
o=a[a.index('-o')+1]; rest=[x for i,x in enumerate(a) if x!='-filetype=obj' and x!='-o' and (i==0 or a[i-1]!='-o')]
fd,m1=tempfile.mkstemp(suffix='.mir'); os.close(fd); m2=m1[:-4]+'.r.mir'
try:
    r=subprocess.run([REAL,*rest,'-stop-before=branch-folder','-o',m1],capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-2000:]); sys.exit(r.returncode)
    r=subprocess.run([sys.executable,T+'/ares.py',m1,m2],capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-2000:]); sys.exit(r.returncode)
    if os.environ.get('LLCW_LOG'): open(os.environ['LLCW_LOG'],'a').write(r.stdout)
    base=[x for x in rest if not x.endswith('.ll')]
    r=subprocess.run([REAL,*base,m2,'-start-before=branch-folder','-filetype=obj','-o',o],capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-2000:]); sys.exit(r.returncode)
finally:
    for f in (m1,m2):
        if os.path.exists(f): os.remove(f)
