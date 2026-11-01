#!/usr/bin/env python3
"""irw.py: helpers to apply IR edits inside admin_cto execute/validate/wallet/sweep pre-opt bodies of a slim module."""
import re,os,sys
FN={'validate':r'admin_cto8validate17h','execute':r'admin_cto7execute17h','wallet':r'admin_cto7execute6wallet17h','sweep':r'admin_cto7execute5sweep17h'}
def rng(L,fn):
    for i,l in enumerate(L):
        if l.startswith('define ') and re.search(FN[fn],l.split('(')[0]):
            j=i
            while L[j]!='}': j+=1
            return i,j
def find(L,fn,text):
    a,b=rng(L,fn); hits=[i for i in range(a,b) if L[i]==text]
    assert len(hits)==1,(fn,text,len(hits)); return hits[0]
EXTRA=['!990001 = !{!"branch_weights", i32 2000, i32 1}','!990002 = !{!"branch_weights", i32 1, i32 2000}']
