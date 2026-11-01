import json,os,sys
f=sys.argv[1]; bsig=sys.argv[2]; M0=int(sys.argv[3]); B0=int(sys.argv[4]); n=int(sys.argv[5]) if len(sys.argv)>5 else 25
R=[json.loads(l) for l in open(f)]
tot=len(R); R=[r for r in R if r.get('M') and r['sig']!=bsig]
print('done',tot,'changed',len(R))
R.sort(key=lambda r:-(r['M']-M0))
for r in R[:n]: print('%-28s M %d (%+d) B %d (%+d)'%(r['id'],r['M'],r['M']-M0,r['bytes'],r['bytes']-B0))
print('-- best with dB<0:')
for r in sorted([r for r in R if r['bytes']<B0],key=lambda r:-(r['M']-M0))[:12]: print('%-28s M %d (%+d) B %d (%+d)'%(r['id'],r['M'],r['M']-M0,r['bytes'],r['bytes']-B0))
