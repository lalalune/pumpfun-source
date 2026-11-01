#!/usr/bin/env python3
"""preord.py <name|path.ll> [--post]: compact block-order signature of the sweep region (experiment only).
pre-opt (default): the sweep fn (+ nested tok/nat fns) in fx/<name>/in.ll; --post: execute in fx/<name>/m.ll.
Letters: T=token_frozen/raw (quote acct arm), R=Rent::get, r=Rent Err (From<ProgramError>), m=minimum_balance,
E=ensure_rent_exempt, N=collect_transfer_native, V=collect_transfer_vault_tokens, C=create_idempotent,
J=vsigner-scope Err join (lifetime.end vsigner, not the Ok exit), O=Ok exit (lifetime.end vsigner + dest), X=sweep.exit, .=other"""
import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import irf
OUT=os.path.dirname(T)
def classify(B,n,P):
    b=B[n]; s=' '.join(b)
    tags=[]
    if 'Rent$GT$3get' in s: tags.append('R')
    if 'ProgramError$GT$$GT$4from' in s: tags.append('r')
    if 'minimum_balance' in s: tags.append('m')
    if 'ensure_rent_exempt' in s: tags.append('E')
    if 'collect_transfer_native' in s or 'transfer_native17' in s: tags.append('N')
    if 'transfer_vault_tokens' in s: tags.append('V')
    if 'create_idempotent' in s: tags.append('C')
    if 'token_frozen' in s or 'token_raw_amount' in s: tags.append('T')
    if re.search(r'lifetime\.end\.p0\(i64 \d+, ptr (?:nonnull )?%vsigner[\w.]*\)',s):
        tags.append('O' if re.search(r'ptr (?:nonnull )?%dest[\w.]*\)',s) else 'J')
    if n.endswith('.exit') and 'sweep' in n: tags.append('X')
    return ''.join(tags) or '.'
def sig(path,fnpat):
    t=open(path).read()
    out=[]
    for m in re.finditer(r'^define [^\n]*@"?([^"(\s]*'+fnpat+r'[^"(\s]*)"?\(',t,re.M):
        fn=m.group(1)
        try: i,j,h,B,order=irf.parse(t,fn=re.escape(fn))
        except Exception as e: continue
        P=irf.preds(B)
        out.append((fn[-60:],[(n,classify(B,n,P),len(P[n])) for n in order]))
    return out
if __name__=='__main__':
    a=sys.argv[1:]; post='--post' in a; a=[x for x in a if x!='--post']
    p=a[0]
    if not p.endswith('.ll'): p=OUT+'/fx/%s/%s'%(p,'m.ll' if post else 'in.ll')
    pats=[r'admin_cto7execute17h'] if post else [r'admin_cto7execute5sweep17h',r'sweep3tok17h',r'sweep3nat17h']
    for pat in pats:
        for fn,L in sig(p,pat):
            s=''.join(c if len(c)==1 else '['+c+']' for _,c,_ in L)
            if post:
                # trim to the sweep region: from first 'T' or 'R' minus 10 to the last X plus 3
                ks=[k for k,(_,c,_) in enumerate(L) if any(x in c for x in 'RTXJ')]
                if ks: s=''.join(c if len(c)==1 else '['+c+']' for _,c,_ in L[max(0,ks[0]-3):ks[-1]+3])
            print(fn, len(L), s)
            if '-v' in sys.argv:
                for n,c,np in L:
                    if c!='.': print('   ',n[:50],c,np)
