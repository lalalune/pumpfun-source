#!/usr/bin/env python3
"""hw.py <name> [prof]: post-opt head weights on rx/<name>/m.ll (instnamer first), llc, score."""
import sys,os,json,subprocess,glob; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T); import irord
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
n=sys.argv[1]; pr=sys.argv[2] if len(sys.argv)>2 else 'bb7.i=1:1,bb14.i=1:1'
d=f'{O}/rx/{n}'
if not os.path.exists(d+'/mn.ll'): subprocess.run([OPT,'-passes=instnamer',d+'/m.ll','-S','-o',d+'/mn.ll'],check=True)
out={'name':n,'prof':pr}
for k,p in (('hw',pr),):
    try: r=irord.run(d+'/mn.ll',d+'/hw',"",p); out.update({x:r.get(x) for x in ('M','bytes','jM','fM','err')})
    except Exception as e: out['err']=repr(e)[:150]
print(json.dumps(out))
