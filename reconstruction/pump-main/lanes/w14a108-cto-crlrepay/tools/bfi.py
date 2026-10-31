#!/usr/bin/env python3
"""bfi.py <raw.ll> [fnregex]: light simplify pipeline + BFI; print freq of each block that calls to_string (with error code) in the fn."""
import sys,os,re,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
src=sys.argv[1]; fn=sys.argv[2] if len(sys.argv)>2 else r'admin_cto8validate'
d=os.path.dirname(os.path.abspath(src)); tmp=f'{d}/_bfi_{os.getpid()}.ll'
open(tmp,'w').write(oracle.slim(open(src).read(),keep=fn))
P=os.environ.get('BFIP','function(sroa,early-cse,simplifycfg,instcombine,simplifycfg)')
r=subprocess.run([OPT,f'-passes={P},print<block-freq>',tmp,'-S','-o',tmp+'.o.ll'],capture_output=True,text=True)
fr={}
for l in r.stderr.split('\n'):
    m=re.match(r' - (\S+): float = ([\d.e+-]+)',l)
    if m: fr[m.group(1)]=float(m.group(2))
ir=open(tmp+'.o.ll').read(); os.remove(tmp); os.remove(tmp+'.o.ll')
body=ir[ir.index('define',ir.index(re.search(r'define [^\n]*'+fn,ir).group(0))):]
body=body[:body.index('\n}\n')]
blk='start'
for l in body.split('\n'):
    m=re.match(r'^([\w.$-]+):',l)
    if m: blk=m.group(1); code=None
    m=re.search(r'for\$u20\$u32\$GT\$4from\S*\(i32 noundef (\d+)\)',l)
    if m: code=int(m.group(1))
    if '9to_string' in l and 'call' in l:
        print(f'{blk:24s} freq {fr.get(blk,-1):.5f} code {code} {"COLD" if fr.get(blk,1)<0.02 else ""}')
