#!/usr/bin/env python3
"""one.py <tag-substring> <classes> : rerun the named mutation and print diff"""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
import mut
f=mut.F0
if os.environ.get('EDIT'):
    import runpy
    for e in os.environ['EDIT'].split(':'): f=runpy.run_path(e)['edit'](f)
jobs=[j for j in mut.muts_single(f,sys.argv[2].split(',')) if sys.argv[1] in j[0]]
tag,f=jobs[0]; print(tag)
c,_=mut.llc(f,keep=mut.OUT+'/irexp/one')
open(mut.OUT+'/irexp/one/fn.txt','w').write('\n'.join(c)+'\n')
print(mut.score(c))
for l in difflib.unified_diff(mut.ORIG,c,n=0,lineterm=''): print(l)
