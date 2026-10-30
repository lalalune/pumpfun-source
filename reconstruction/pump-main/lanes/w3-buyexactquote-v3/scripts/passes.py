#!/usr/bin/env python3
"""passes.py changes.txt SYM out_dir: split per-pass dumps of SYM into numbered files"""
import sys,re,os
f,sym,od=sys.argv[1:4]; os.makedirs(od,exist_ok=True)
cur=None;k=0;buf=[]
def flush():
    global buf,cur
    if cur: open(f'{od}/{cur}','w').write(''.join(buf))
    buf=[]
for line in open(f,errors='replace'):
    if line.startswith('*** IR Dump'):
        flush(); cur=None
        if sym in line and 'omitted' not in line and 'filtered' not in line:
            k+=1; p=re.search(r'(After|At) (\S+)',line).group(2); cur=f'{k:02d}_{p}.ll'
        continue
    if cur: buf.append(line)
flush()
