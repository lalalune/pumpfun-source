#!/usr/bin/env python3
# batch.py <listfile>: lines "name genes[,..] [wts]"; runs fw.py 2 at a time (work0/work1)
import sys,subprocess,queue
from concurrent.futures import ThreadPoolExecutor
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a18-cto-slotpin'
Q=queue.Queue(); Q.put('work0'); Q.put('work1')
jobs=[l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
def run(j):
    w=Q.get()
    try: subprocess.run(['python3',O+'/tools/fw.py',j[0],j[1],w]+j[2:3],capture_output=True)
    finally: Q.put(w)
with ThreadPoolExecutor(2) as ex: list(ex.map(run,jobs))
