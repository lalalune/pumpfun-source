#!/usr/bin/env python3
"""bfi.py <module.ll|.bc> [fnregex=admin_cto8validate] : Inliner cold-call-site oracle. Dumps the function right
before its CGSCC inliner (module scope), computes BFI there and prints, for every error! site (to_string call
followed by a `store i32 LINE`), its block frequency relative to entry and whether the inliner treats it as cold
(< 2% => to_string kept as a call, threshold 45) or hot (inlined at threshold 325)."""
import sys,os,re,subprocess
D=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin')
src=sys.argv[1]; fre=sys.argv[2] if len(sys.argv)>2 else r'admin_cto8validate17h'
t=open(src,errors='ignore').read() if src.endswith('.ll') else subprocess.run([D+'/opt','-S',src,'-o','-'],capture_output=True,text=True).stdout
m=re.search(r'\ndefine [^\n]*@("?[^\n(]*'+fre+r'[^\n(]*"?)\(',t); F=m.group(1).strip('"')
d=os.path.dirname(os.path.abspath(src))
dump=d+'/pre_inline_'+re.sub(r'\W','',fre)[:20]+'.ll'
r=subprocess.run([D+'/opt','-O3','-print-before=inline','-print-module-scope','-filter-print-funcs='+F,src,'-o','/dev/null'],capture_output=True,text=True)
txt=r.stderr; txt=txt[txt.index('\n')+1:]
k=txt.find('\n; *** IR Dump')
if k>0: txt=txt[:k]
open(dump,'w').write(txt)
b=subprocess.run([D+'/opt','-passes=function(print<block-freq>)',dump,'-o','/dev/null'],capture_output=True,text=True).stderr
k=b.index('block-frequency-info: '+F); seg=b[k:b.find('Printing analysis',k)]
freq={mm.group(1):float(mm.group(2)) for mm in re.finditer(r' - ([^:]+): float = ([0-9.e-]+)',seg)}
m=re.search(r'\ndefine [^\n]*@"?'+re.escape(F)+r'"?\(',txt); s=m.start()+1; e=txt.index('\n}\n',s)
lines=txt[s:e].split('\n'); blk='start'; rows=[]
for i,l in enumerate(lines):
    mm=re.match(r'^([\w.\-$"]+):',l)
    if mm: blk=mm.group(1).strip('"')
    if 'to_string17h' in l and l.strip().startswith('call'):
        for kk in range(i+1,min(i+15,len(lines))):
            m2=re.search(r'store i32 (\d+),',lines[kk])
            if m2: rows.append((int(m2.group(1)),blk,freq.get(blk,-1))); break
for ln,bk,fq in sorted(rows):
    print('line %d  block %-12s freq %.5f  %s'%(ln,bk,fq,'COLD (call kept)' if fq<0.02 else 'hot (inlined)'))
