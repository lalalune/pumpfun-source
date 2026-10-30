#!/usr/bin/env python3
"""noinl.py <in.ll> <out.ll> <fnregex> <line,line,...> : add a noinline call-site attribute to the
to_string calls whose error! site stores one of the given Source line numbers (IR oracle only)."""
import re,sys
t=open(sys.argv[1]).read(); fnre=sys.argv[3]; targets=set(int(x) for x in sys.argv[4].split(','))
m=re.search(r'\ndefine [^\n]*@"?[^\n(]*'+fnre+r'[^\n(]*"?\(',t)
s=m.start()+1; e=t.index('\n}\n',s)
lines=t[s:e].split('\n'); cnt=0
for i,l in enumerate(lines):
    if 'to_string17h' in l and l.strip().startswith('call'):
        for k in range(i+1,min(i+15,len(lines))):
            mm=re.search(r'store i32 (\d+),',lines[k])
            if mm:
                if int(mm.group(1)) in targets:
                    lines[i]=re.sub(r'\)( #\d+)?$',') #9999',l); cnt+=1
                break
t2=t[:s]+'\n'.join(lines)+t[e:]+'\nattributes #9999 = { noinline }\n'
open(sys.argv[2],'w').write(t2); print('patched',cnt)
