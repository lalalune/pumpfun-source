#!/usr/bin/env python3
"""tab4.py: markdown screen table of res.txt with true LCS (---, rfj) and Mperm (relab binspills)"""
import sys,os,re,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T); sys.path.insert(0,T); import tg
rows=[]
for l in open(OUT+'/res.txt'):
    n,g=l.split()[:2]
    if 'COMPILE FAIL' in l: rows.append((n,g,'fail','','','','','')); continue
    m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); j=json.loads(l.split(' | ')[2])
    lc=subprocess.run(['python3',T+'/lcs.py',n,'--masks','---,rfj'],capture_output=True,text=True,cwd=OUT).stdout.split()
    rp=json.loads(subprocess.run(['python3',T+'/relab.py','bin',n],capture_output=True,text=True,cwd=OUT).stdout)
    rows.append((n,g,m[1],m[2],m[6],lc[2].split(':')[1],lc[3].split(':')[1],rp['Mperm'],j['eq_main']))
print('| variant | genes | bytes | M | rfjM | LCS --- | LCS rfj | Mperm | eq main |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for r in rows: print('| '+' | '.join(str(x) for x in r)+' |')
