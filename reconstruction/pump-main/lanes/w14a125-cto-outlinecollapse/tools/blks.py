import sys,re,importlib.util,os
os.chdir(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a125-cto-outlinecollapse/jt'))
sv=sys.argv; sys.argv=['x']
sp=importlib.util.spec_from_file_location('relay','relay.py'); R=importlib.util.module_from_spec(sp); sp.loader.exec_module(R); sys.argv=sv
pre,bl,post=R.parse(sv[1])
off=0
for i,(n,b) in enumerate(bl):
    m=re.search(r'#\s*(%\S+)',b[0]); ir=m.group(1) if m else ''
    ni=sum(1 for l in b[1:] if l.strip() and not l.strip().startswith(('#','.')) and not l.strip().endswith(':'))
    print(i,n,ir,ni)
