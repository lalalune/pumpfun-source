#!/usr/bin/env python3
"""irpat.py <variant>: pre-opt and post-opt IR diff of a calibration variant against m0 (admin_cto fns only)."""
import sys,os,re,difflib
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T); sys.path.insert(0,T); import modparse
FN=[('validate',r'admin_cto8validate17h'),('execute',r'admin_cto7execute17h'),('wallet',r'admin_cto7execute6wallet17h'),('sweep',r'admin_cto7execute5sweep17h')]
def norm(l):
    l=re.sub(r'%[\w.$-]+|%"[^"]+"','%v',l); l=re.sub(r'![\w.]+','!m',l); l=re.sub(r'#\d+','#a',l); l=re.sub(r'@alloc_\w+','@G',l)
    l=re.sub(r'^"?[\w.$-]+"?:.*','LABEL',l); return l.rstrip()
def bodies(p,post=False):
    E=modparse.parse(open(p).read()); D={n:l for k,n,l in E if k=='define'}; out={}
    for k,pat in FN:
        c=[n for n in D if re.search(pat,n)]
        if c: out[k]=[norm(x) for x in D[c[0]] if x.strip() and not x.startswith(';') and not x.strip().startswith('; ')]
    return out
def diff(a,b,lim=14):
    res=[]
    for k in a:
        if k not in b: res.append(f'  [{k}] missing'); continue
        d=[x for x in difflib.unified_diff(a[k],b[k],lineterm='',n=0) if x[:1] in '+-' and not x.startswith(('+++','---'))]
        if d: res.append(f'  [{k}] {len(d)} changed lines'); res+=['    '+x[:170] for x in d[:lim]]
    return res
if __name__=='__main__':
    v=sys.argv[1]; lim=int(sys.argv[2]) if len(sys.argv)>2 else 14
    print('== pre-opt'); print('\n'.join(diff(bodies(OUT+'/ir/m0.ll'),bodies(OUT+f'/ir/{v}.ll'),lim)))
    if os.path.exists(OUT+f'/rx/{v}/m.ll'):
        print('== post-opt execute'); print('\n'.join(diff(bodies(OUT+'/rx/m0/m.ll'),bodies(OUT+f'/rx/{v}/m.ll'),lim)))
