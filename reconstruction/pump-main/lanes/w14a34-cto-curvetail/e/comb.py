#!/usr/bin/env python3
"""comb.py <name> <part...>: e/<name>.py = concatenated EDITS of e/<part>.py"""
import sys,runpy,os
D=os.path.dirname(os.path.abspath(__file__))+'/e'
n=sys.argv[1]; E=[]
for p in sys.argv[2:]: E+=runpy.run_path(f'{D}/{p}.py')['EDITS']
open(f'{D}/{n}.py','w').write('EDITS='+repr(E)+'\n')
