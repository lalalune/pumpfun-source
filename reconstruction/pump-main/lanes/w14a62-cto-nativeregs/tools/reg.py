#!/usr/bin/env python3
# reg.py <o|so> [lo hi]: count raw-identical aligned lines in orig native region
import sys,subprocess
lo=sys.argv[2] if len(sys.argv)>2 else '0x5950'; hi=sys.argv[3] if len(sys.argv)>3 else '0x5c40'
t=subprocess.run(['python3',__file__.replace('reg.py','sbs.py'),sys.argv[1],lo,hi],capture_output=True,text=True).stdout.split('\n')
same=sum(1 for l in t if l.startswith('  ')); tot=sum(1 for l in t if l[2:6].strip())
print(f"region {lo}-{hi}: raw-same {same}/{tot}")
