#!/usr/bin/env python3
"""mirren.py <in.mir> <out.mir> <target vreg> <vreg>...: rename vregs to target in the function body (pre-coalescing MIR oracle)."""
import sys,re
i,o,t=sys.argv[1:4]; vs=set(sys.argv[4:])
s=open(i).read(); b=s.index('body:')
body=re.sub(r'%(\d+)(?![0-9])',lambda m: t if '%'+m.group(1) in vs else m.group(0),s[b:])
body=re.sub(r'^\s*'+re.escape(t)+r':gpr = COPY '+re.escape(t)+r'\n','',body,flags=re.M)
open(o,'w').write(s[:b]+body)
