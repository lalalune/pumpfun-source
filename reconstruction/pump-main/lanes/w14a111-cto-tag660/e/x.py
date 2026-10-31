import os,runpy
R=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a111-cto-tag660/e/r4d.py')['EDITS']
H=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a111-cto-tag660/e/h1.py')['EDITS']
C=('  %i684 = icmp ne i8 %i683, 0\n','  %i684 = icmp ne i8 %hflag, 0\n')
M=os.environ.get('MODE','rhc')
E=[]
if 'r' in M: E+=R
E+=H[:2]
if 'h' in M: E+=[H[2]]
if 'c' in M: E+=[C]
EDITS=E
