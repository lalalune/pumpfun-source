#!/usr/bin/env python3
"""catalog.py <out.json> [NP]: size-knob catalog for admin_cto on the current admin_cto source (86e2a6b == 9120883 ==
9bd38c7; main's raw-IR capture is byte-identical in w15a03 n0, w15a13 m0 and this lane's main). Walks cached raw-IR
oracle captures (fn.bin) of this lane, w15a03 (stitch15 res-86e2a6b/res-9120883) and w15a13 (res.txt), re-derives bytes
and M from each fn.bin, tags where the byte delta lands (call-anchor alignment vs main, region.py) and adds the
w16-strategy drift metrics (drift.py: jump-displacement mismatches, region drift, rfj true LCS). Experiment only."""
import sys,os,json,re,difflib,subprocess
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window
import region
C=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
OT=mask(orig_window())
MAINFB=C+'/w16a02-cto-faithknobs/rx/main/fn.bin'; MAIN=open(MAINFB,'rb').read()
def rows():
    out=[]
    for f in ('res-86e2a6b.jsonl','res-9120883.jsonl'):
        for l in open(f'{C}/w15a03-cto-stitch15/{f}'):
            r=json.loads(l)
            if 'error' in r: continue
            out.append(('w15a03-cto-stitch15',r['name'],r.get('genes',''),f'{C}/w15a03-cto-stitch15/rx/{r["name"]}/fn.bin'))
    for l in open(f'{C}/w15a13-cto-jointraceback/res.txt'):
        n=l.split('|')[0].strip()
        if n: out.append(('w15a13-cto-jointraceback',n,'e/'+n.split('_')[0]+'.py (+ knob '+'_'.join(n.split('_')[1:])+')' if '_' in n else 'e/'+n+'.py',f'{C}/w15a13-cto-jointraceback/rx/{n}/fn.bin'))
    for lane,fs in (('w15a01-cto-devolfill',('res-86e2a6b.jsonl',)),('w15a16-cto-mpermrank',('res-86e2a6b.jsonl','res-9120883.jsonl')),
                    ('w15a30-cto-litfamily',('res-9120883.jsonl','res-1cc4879.jsonl','res-9bd38c7.jsonl')),('w15a32-cto-lbasinweight',('res-9120883.jsonl','res-1cc4879.jsonl','res-9bd38c7.jsonl')),
                    ('w15a35-cto-pdafceiling',('res-9120883.jsonl',)),('w16a04-cto-lanchorceil',('res-9bd38c7.jsonl',)),('w16a05-cto-skelsplice',('res-9bd38c7.jsonl',))):
        for f in fs:
            fp=f'{C}/{lane}/{f}'
            if not os.path.exists(fp): continue
            for l in open(fp):
                try: r=json.loads(l)
                except Exception: continue
                if 'error' in r or 'name' not in r: continue
                out.append((lane,r['name'],r.get('genes',''),f'{C}/{lane}/rx/{r["name"]}/fn.bin',r.get('M'),r.get('bytes')))
    for l in open(f'{C}/w16a02-cto-faithknobs/res-9bd38c7.jsonl'):
        r=json.loads(l)
        if 'error' in r: continue
        out.append(('w16a02-cto-faithknobs',r['name'],r.get('genes',''),f'{C}/w16a02-cto-faithknobs/rx/{r["name"]}/fn.bin'))
    seen=set(); res=[]
    for x in out:
        if not os.path.exists(x[3]): continue
        k=open(x[3],'rb').read()
        if k in seen: continue   # identical captures listed once (first source wins)
        if len(x)>4 and x[5] is not None and x[5]!=len(k): continue   # rx dir overwritten by a later run: drop
        seen.add(k); res.append(x[:4]+((x[4],) if len(x)>4 else (None,)))
    return res
def ev(x):
    lane,name,genes,fb,expM=x; raw=open(fb,'rb').read()
    M=sum(b.size for b in difflib.SequenceMatcher(None,OT,mask(raw),autojunk=False).get_matching_blocks())
    if expM is not None and expM!=M: return None
    rg=region.regions(fb,MAINFB)
    d={'name':name,'lane':lane,'genes':genes,'bytes':len(raw),'delta_bytes':len(raw)-27400,'M':M,'dM':M-2249,
       'ratio':round(2*M/(6676+(len(raw)-27400)/8),5),'identical_to_main':mask(raw)==mask(MAIN),
       'changes':rg.get('changes'),'by_region':rg.get('by_region'),'call_note':rg.get('error')}
    if abs(len(raw)-27400)<=200 and M>=2150:
        p=subprocess.run(['python3',T+'/drift.py',fb],capture_output=True,text=True)
        try: d.update({k:v for k,v in json.loads(p.stdout.strip().splitlines()[-1]).items() if k in ('rfj_lcs','jumps_bad','jumps_aligned','drift_med')})
        except Exception: pass
    return d
if __name__=='__main__':
    R=rows(); print(len(R),'unique captures',flush=True)
    with Pool(int(sys.argv[2]) if len(sys.argv)>2 else 4) as P: out=[d for d in P.map(ev,R,chunksize=4) if d is not None]
    out.sort(key=lambda d:(-d['dM'],d['delta_bytes']))
    json.dump(out,open(sys.argv[1],'w'),indent=0)
    print('done',len(out))
