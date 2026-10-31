#!/usr/bin/env python3
"""inl.py <rxname|m.ll>...: REAL -O3 to_string outline map of admin_cto::execute (post-opt IR): for every error! line
site, I = to_string inlined, O = outlined call. (bfi.py's light-pipeline COLD prediction is NOT reliable: see NOTES.)"""
import sys,re,os
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG={'O':[307,312,330,334,338,660,719],'I':[284,289,296,298,306,326]}
for p in sys.argv[1:]:
    f=p if p.endswith('.ll') else f'{D}/rx/{p}/m.ll'
    t=open(f).read(); i=t.index('define',t.index('admin_cto7execute')-300); body=t[i:t.index('\n}\n',i)]
    last=None; res={}
    for l in body.split('\n'):
        if 'call' in l and '9to_string' in l and 'define' not in l: last='O'
        elif re.match(r'^"?\S*9to_string\S*\.exit\S*:',l): last='I'
        m=re.search(r'store i32 (\d{3}), ptr %\S*sroa_idx',l)
        if m and last: res.setdefault(int(m.group(1)),last); last=None
    s=' '.join(f'{k}{v}' for k,v in sorted(res.items()))
    ok=all(res.get(k)==v for v in 'OI' for k in ORIG[v] if k in res)
    print(f'{os.path.basename(p):12s} {s}  orig-pattern={ok}')
