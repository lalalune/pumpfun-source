#!/usr/bin/env python3
"""wck.py <fn.bin>...: wallet colour check vs the original: cand instruction aligned at orig 0x5c30/0x5ca0/0x5cb8 (do_coin defs),
0x6100, 0x5cc0 (accounts piece), 0x5cf0 (ATA buffer), 0x5e50/0x6858 (coin gate); plus mismatch counts over orig [0x5b40,0x6b08)."""
import sys,subprocess,os,re
T=os.path.dirname(os.path.abspath(__file__))
KEYS={'5c30':'dc0','5ca0':'dc1','5cb8':'dc2','6100':'dc3','5cc0':'acc','5cf0':'buf','5e50':'g1','6858':'g2'}
for f in sys.argv[1:]:
    out=subprocess.run(['python3',T+'/side.py',f,'0x5b40','0x6b08'],capture_output=True,text=True).stdout.splitlines()
    got={}; cnt={' ':0,'r':0,'s':0,'-':0,'+':0,'x':0}; prev=None
    for i,l in enumerate(out):
        m=l[0]; cnt[m]=cnt.get(m,0)+1
        a=l[2:7].strip().lstrip('0')
        if a in KEYS:
            right=l.split('|',1)[1].strip() if '|' in l else ''
            nxt=out[i+1] if i+1<len(out) else ''
            sp=' +stx' if nxt.startswith('+') and 'stx' in nxt else ''
            got[KEYS[a]]=(m+':'+re.sub(r'^[0-9a-f]+ ','',right)+sp)
    print(os.path.basename(os.path.dirname(f)) or f, ' '.join(f"{k}={got.get(k,'?')}" for k in KEYS.values()), 'counts', cnt)
