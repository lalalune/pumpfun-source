#!/usr/bin/env python3
"""rowsum.py <rx> [suffix]: one joint-ceiling row for an lpipe.sh run (experiment only).
unforced: bytes/M/Mperm/Mhc/lcs from rx/mp_<rx>/mp.json (scr.py) or rx/<rx>/res.json; climb: final forces, ratio, bytes;
forced: M, Mperm, joint Mhc (permhc), true LCS deltas vs main (evall), window rotation (winrot) unforced and forced."""
import sys,os,json,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); O=os.path.dirname(T)
n=sys.argv[1]; t=sys.argv[2] if len(sys.argv)>2 else ''
r={'rx':n,'pass':t or 'p1'}
try:
    mp=json.load(open(f'{O}/rx/mp_{n}/mp.json')); r.update(bytes=mp['bytes'],M=mp['M'],Mperm=mp['Mperm'],Mhc=mp['Mhc'],lcs=mp.get('lcs'),lcs_f=mp.get('lcs_f'))
except Exception: pass
try: r['ratio']=json.load(open(f'{O}/rx/{n}/res.json'))['ratio']
except Exception: pass
cl=[json.loads(l) for l in open(f'{O}/cm/{n}{t}.climb.log') if l.startswith('{')]
if cl:
    x=cl[-1]; r.update(climb_ratio=x['ratio'],climb_bytes=x['bytes'],climb_L2=x.get('L2'),forces=x.get('force',''),nforces=len([f for f in x.get('force','').split(',') if f]))
    r['climb_traj']=[(y['round'],y['ratio'],y['bytes']) for y in cl]
try:
    p=json.load(open(f'{O}/rx/{n}{t}ra/permhc.json')); r.update(fM=p['M'],fMperm=p['Mperm'],joint=p['Mhc'])
except Exception as e: r['perr']=repr(e)[:80]
try:
    ev=open(f'{O}/rx/{n}{t}ra/evall.out').read()
    m=re.search(r'L---=([+-]\d+) Lrfj=([+-]\d+)',ev); r.update(fLCS=int(m.group(1)),fLCSrfj=int(m.group(2)))
except Exception: pass
import winrot
try: r['rot']=winrot.rot(open(f'{O}/rx/{n}/fn.bin','rb').read())[0]
except Exception: pass
try: r['frot']=winrot.rot(open(f'{O}/rx/{n}{t}ra/fn.bin','rb').read())[0]
except Exception: pass
print(json.dumps(r),flush=True)
