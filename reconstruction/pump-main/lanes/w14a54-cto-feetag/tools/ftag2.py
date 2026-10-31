#!/usr/bin/env python3
"""ftag2.py in.ll out.ll : ftag.py plus the admin_cto_pool CPI fee-tag argument taken from the phi (fee arg tag dies in validate)."""
import sys,subprocess,os
src,dst=sys.argv[1:3]
subprocess.run([sys.executable,os.path.dirname(os.path.abspath(__file__))+'/ftag.py',src,dst],check=True)
t=open(dst).read(); L=t.split('\n')
k=[i for i,l in enumerate(L) if 'admin_cto_pool17h' in l and 'call' in l and 'i64 noundef %0' in l]; assert len(k)==1
L[k[0]]=L[k[0]].replace('i64 noundef %0','i64 noundef %ftag'); open(dst,'w').write('\n'.join(L))
