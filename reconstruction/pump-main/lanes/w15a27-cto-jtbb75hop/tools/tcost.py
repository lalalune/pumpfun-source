#!/usr/bin/env python3
"""tcost.py <name>: dbg opt -O3 on ir/<name>.ll, dump execute before each JumpThreading; in dump #2 find the block that
branches on the shared flag (tree test) and print its JT duplication cost and memcpy count, plus JT2 trace lines for it."""
import sys,os,re,subprocess
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop')
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/opt')
F='_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'
n=sys.argv[1]
r=subprocess.run([DBG,'-O3','-print-before=jump-threading','-filter-print-funcs='+F,OUT+'/ir/'+n+'.ll','-o','/dev/null'],capture_output=True,text=True)
d=re.split(r'^; \*\*\* IR Dump.*$',r.stderr,flags=re.M)
print(n,'dumps',len(d)-1)
for k in (1,2):
    if k>=len(d): break
    blocks=re.split(r'\n(?=[\w.$"-]+:)',d[k])
    for b in blocks:
        L=b.strip().split('\n'); 
        if not L or not re.search(r'br i1 %shared[\w.]*, label',L[-1]): continue
        name=L[0].split(':')[0]; c=0; mc=0
        for l in L[1:]:
            s=l.strip()
            if not s or s.startswith(';') or ' = phi ' in s or 'lifetime' in s: continue
            if s.startswith('br ') or s.startswith('switch'): continue
            free=(' getelementptr inbounds' in s and re.search(r'i64 \d+$|i64 \d+, !',s)) or ' bitcast ' in s
            c+=0 if free else (2 if ('call ' in s and '@llvm.' in s) else 4 if 'call ' in s else 1)
            mc+='llvm.memcpy' in s
        print(f'  JT{k} block {name}: cost {c} memcpys {mc} insts {len(L)-1} term {L[-1].strip()[:80]}')
