#!/usr/bin/env python3
"""bficall.py <module.ll> <fnregex> <callee-regex...>: pre-inliner BFI of call sites (relative to entry); <0.02 = cold."""
import sys,os,re,subprocess
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin')
src=sys.argv[1]; fre=sys.argv[2]; pats=sys.argv[3:]
t=open(src,errors='ignore').read()
m=re.search(r'\ndefine [^\n]*@("?[^\n(]*'+fre+r'[^\n(]*"?)\(',t); F=m.group(1).strip('"')
dump=src+'.preinl.ll'
r=subprocess.run([D+'/opt','-O3','-print-before=inline','-print-module-scope','-filter-print-funcs='+F,src,'-o','/dev/null'],capture_output=True,text=True)
txt=r.stderr; txt=txt[txt.index('\n')+1:]
k=txt.find('\n; *** IR Dump')
if k>0: txt=txt[:k]
open(dump,'w').write(txt)
b=subprocess.run([D+'/opt','-passes=function(print<block-freq>)',dump,'-o','/dev/null'],capture_output=True,text=True).stderr
k=b.index('block-frequency-info: '+F); seg=b[k:b.find('Printing analysis',k)]
freq={mm.group(1):float(mm.group(2)) for mm in re.finditer(r' - ([^:]+): float = ([0-9.e-]+)',seg)}
m=re.search(r'\ndefine [^\n]*@"?'+re.escape(F)+r'"?\(',txt); s=m.start()+1; e=txt.index('\n}\n',s)
blk='start'
for l in txt[s:e].split('\n'):
    mm=re.match(r'^([\w.\-$"]+):',l)
    if mm: blk=mm.group(1).strip('"')
    if l.strip().startswith(('call','%')) and ' call ' in ' '+l:
        for p in pats:
            if re.search(p,l):
                fq=freq.get(blk,-1); print('%-14s %-20s %.5f %s'%(p[:14],blk,fq,'COLD' if fq<0.02 else ''))
os.remove(dump)
