#!/usr/bin/env python3
"""vbfi.py <raw.ll>: REAL-pipeline BFI of validate's to_string call sites. Runs opt -O3 -print-after-all on validate, takes
validate's last full dump (fully simplified, i.e. the body that gets inlined into execute, where the inliner re-decides the
call sites it refused in validate), splices it into the raw module and prints each to_string call's block frequency
(relative to validate entry) with its error line. < 0.02 => cold in execute too (execute calls validate at freq ~1)."""
import sys,os,re,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
src=sys.argv[1]; t=open(src).read()
V=re.search(r'define[^\n]*@(_ZN14pump_recovered9admin_cto8validate17h[0-9a-f]+E)',t).group(1)
tmp=f'{src}.vbfi{os.getpid()}'
r=subprocess.run([OPT,'-O3',src,'-o','/dev/null','-print-after-all',f'-filter-print-funcs={V}'],capture_output=True,text=True)
secs=r.stderr.split('; *** IR Dump After ')
which=os.environ.get('VB_AT','last')
cands=[s for s in secs if '\ndefine ' in s]
if which!='last': cands=[s for s in cands if s.startswith(which)]
s=cands[-1 if which=='last' or os.environ.get('VB_N') is None else int(os.environ['VB_N'])]
hdr=s.split('\n',1)[0]
f=s[s.index('\ndefine ')+1:]; f=f[:f.index('\n}\n')+3]
f=re.sub(r', !(?:noalias|alias\.scope|noundef|range|nonnull|align|dereferenceable|prof|llvm\.loop|tbaa) !\d+','',f)
f=re.sub(r' !(?:range|noundef|nonnull|align|prof) !\d+','',f)
m=re.search(r'\ndefine[^\n]*@'+V+r'\(',t); a=m.start()+1; b=t.index('\n}\n',a)+3
mod=t[:a]+f+t[b:]
open(tmp,'w').write(oracle.slim(mod,keep=V))
r=subprocess.run([OPT,'-passes=function(verify),print<block-freq>',tmp,'-S','-o','/dev/null'],capture_output=True,text=True)
os.remove(tmp)
fr={}
for l in r.stderr.split('\n'):
    mm=re.match(r' - (\S+): float = ([\d.e+-]+)',l)
    if mm: fr[mm.group(1)]=float(mm.group(2))
if not fr: print(r.stderr[-2000:]); sys.exit(1)
print('# validate after:',hdr[:80])
blk='entry'; pend=[]; out=[]
for l in f.split('\n'):
    mm=re.match(r'^("?[\w.$-]+"?):',l)
    if mm: blk=mm.group(1).strip('"')
    if ('call' in l and '9to_string' in l) or ('call' in l and '4name17' in l): pend.append(blk)
    mm=re.search(r'store i32 (\d{3}), ptr',l)
    if mm and pend: out.append((int(mm.group(1)),pend[0])); pend=[]
for line,b in sorted(out): print(f'{line} {b:20s} {fr.get(b,-1):.5f} {"COLD" if fr.get(b,1)<0.02 else ""}')
