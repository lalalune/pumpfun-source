#!/usr/bin/env python3
"""mk.py <name> comp1 comp2 ...: write e/<name>.py with the concatenated component edits"""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/comp.py').read(),g); C=g['C']
n=sys.argv[1]; E=[]
for c in sys.argv[2:]: E+=C[c]
open(os.path.join(os.path.dirname(T),'e',n+'.py'),'w').write('E='+repr(E)+'\n')
print(n,len(E))
