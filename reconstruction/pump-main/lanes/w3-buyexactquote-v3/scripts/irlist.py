import sys,re,runpy,os
t=open(sys.argv[1]).read(); os.environ.setdefault('SYM',sys.argv[2] if len(sys.argv)>2 else 'trade15buy_exact_quote17h')
ns=runpy.run_path(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-buyexactquote-v3/iredits/reorder.py'))
L,s,e,bl=ns['blocks_of'](t)
for n,b in bl:
    calls=[re.search(r'@"?([^"( ]+)',x).group(1) for x in b if ' call ' in x and 'lifetime' not in x and 'llvm.' not in x and '@' in x]
    calls=[re.sub(r'17h[0-9a-f]{16}E$','',c)[-30:] for c in calls]
    lines=[x for x in b if 'stw' in x or 'store i32 ' in x]
    ln=[re.search(r'store i32 (\d+)',x).group(1) for x in b if re.search(r'store i32 (\d{3,4}),',x)]
    term=[x.strip()[:60] for x in b if x.strip().startswith(('br ','switch','ret','unreachable'))]
    print(f'{n:28s} {len(b):3d} {" ".join(calls)[:70]} L{",".join(ln)} | {term[0] if term else ""}')
