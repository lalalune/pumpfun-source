#!/usr/bin/env python3
"""rank.py [jsonl...]: Mperm/Mhc/LCS ranking table. Base per row = 90300f9 (main M 2248/Mperm 2292/Mhc 2299/lcs 2253)
unless the m.ll is newer than the 86e2a6b baseline switch (07:36:22 local), then 86e2a6b (2249/2293/2300/2255)."""
import json,sys,os,glob
B={'90300f9':(2248,2292,2299,2253,2484),'86e2a6b':(2249,2293,2300,2255,2488)}
C=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
genes={}
for f in glob.glob(C+'/w15a*/res-*.jsonl')+glob.glob(C+'/w15a*/*.jsonl'):
    try:
        for l in open(f):
            try: r=json.loads(l)
            except Exception: continue
            if isinstance(r,dict) and 'name' in r: genes[(os.path.basename(os.path.dirname(f)).split('-')[0][3:],r['name'])]=genes[(os.path.basename(os.path.dirname(f)).split('-')[0],r['name'])]=r.get('genes') or r.get('edits') or ''
    except Exception: pass
rows=[]
for f in sys.argv[1:]:
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        if 'Mperm' not in r: continue
        rows.append(r) if r['n'] not in {x['n'] for x in rows} else None
def base(r):
    return r.get('base') or ('86e2a6b' if r.get('mt',0)>0 else '90300f9')
SW=os.stat(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).st_mtime
LD={p.split('/')[-1].split('-')[0]:p for p in glob.glob(C+'/w15a*')}; LD.update({k[3:]:v for k,v in list(LD.items())})
N86={}
for k,v in LD.items():
    try: N86[k]={json.loads(l).get('name') for l in open(v+'/res-86e2a6b.jsonl')}
    except Exception: pass
out=[]
for r in rows:
    lane,_,nm=r['n'].partition('_')
    if lane=='mp': bs='86e2a6b'
    else:
        p=f'{LD.get(lane,"")}/rx/{nm}/m.ll'
        if nm in N86.get(lane,set()) or 'lf_fee_configurable' in genes.get((lane,nm),'') or genes.get((lane,nm),'').startswith('l2'): bs='86e2a6b'; b=B[bs]; out.append((r['Mhc']-b[2],r['Mperm']-b[1],r['M']-b[0],r['lcs_hc']-b[2],r['lcs_f']-b[4],r['bytes']-27400,r['n'],bs,genes.get((lane,nm),''))); continue
        try: bs='86e2a6b' if os.stat(p).st_mtime>SW+60 else '90300f9'
        except OSError: bs='?'
    b=B.get(bs,B['90300f9'])
    out.append((r['Mhc']-b[2],r['Mperm']-b[1],r['M']-b[0],r['lcs_hc']-b[2] if 'lcs_hc' in r else 0,r['lcs_f']-b[4],r['bytes']-27400,r['n'],bs,genes.get((lane,nm),'')))
key=os.environ.get('KEY','hc')
out.sort(key=lambda x:(-x[0],-x[1]) if key=='hc' else ((-x[1],-x[0]) if key=='perm' else (-x[4],-x[0])))
print('dMhc dMperm dM dLCShc dLCSf dB name base genes')
for x in out[:int(os.environ.get('N','60'))]: print(*x)
