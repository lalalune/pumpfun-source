#!/usr/bin/env python3
"""scan.py ll BLOCK [preops...]: try moving BLOCK after every other block (on top of preops)."""
import sys,subprocess,os,re
from concurrent.futures import ThreadPoolExecutor
O=os.path.dirname(os.path.abspath(__file__))+'/oracle2.py'
ll,blk=sys.argv[1],sys.argv[2]; pre=sys.argv[3:]
names=[l.split()[0] for l in subprocess.run(['python3',O,ll,'5trade3buy17h','list'],capture_output=True,text=True).stdout.splitlines()][1:]
def run(i,y):
    r=subprocess.run(['python3',O,ll,'5trade3buy17h']+pre+[f'{blk}>{y}'],capture_output=True,text=True,env=dict(os.environ,TAG=f'sc{i}'))
    m=re.search(r'cand (\d+) diffslots (\d+) ratio ([\d.]+)',r.stdout)
    return (int(m.group(2)),int(m.group(1)),float(m.group(3)),y) if m else (9999,0,0,y)
with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda p:run(*p),enumerate(n for n in names if n!=blk)))
for r in sorted(res)[:int(os.environ.get('N','8'))]: print(r)
